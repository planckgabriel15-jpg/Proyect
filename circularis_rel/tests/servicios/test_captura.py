"""Fase 1a: captura de punta a punta (parte, aviso, tarjeta, OT, vidas, validación, faltantes, backup)."""

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select

from circularis_rel.datos.enums import (
    AccionOT,
    ColorTarjeta,
    EstadoEvento,
    EstadoOT,
    EstadoParte,
    EstadoTarjeta,
    NivelHora,
    OrigenParte,
    TipoFin,
    TipoReparacion,
)
from circularis_rel.datos.modelos import (
    ActivoTurno,
    EventoFalla,
    MotivoParada,
    OrdenTrabajo,
    ParteTurno,
    RecalculoPendiente,
    Repuesto,
    VidaComponente,
)
from circularis_rel.servicios import auth, faltantes, ot, registro, validacion, vidas
from circularis_rel.servicios.permisos import PermisoDenegado

TZ = ZoneInfo("America/Argentina/Cordoba")


def local(*a) -> datetime:
    return datetime(*a, tzinfo=TZ)


@dataclass
class Gente:
    operario: int
    encargado: int
    jefe: int


@pytest.fixture
def gente(db, planta) -> Gente:
    with db.escritura() as s:
        s.add(ActivoTurno(id_activo=planta.activo, id_turno=planta.turno, dias="1,2,3,4,5,6,7"))
        op = auth.crear_usuario(s, "op", "Operario", "OPERARIO", "1234", maquinas=["DEMO-AGR-001"])
        enc = auth.crear_usuario(s, "enc", "Encargado", "ENCARGADO", "clave-encargado")
        jefe = auth.crear_usuario(s, "jefe2", "Jefe", "JEFE", "clave-del-jefe")
        return Gente(op.id, enc.id, jefe.id)


def motivo(db, codigo):
    with db.lectura() as s:
        return s.scalar(select(MotivoParada.id).where(MotivoParada.codigo == codigo))


def parte(db, g, planta, fecha, estado="TODO", horas=0.0, mot=None, usuario=None):
    with db.escritura(usuario_id=usuario or g.operario) as s:
        return registro.registrar_parte(s, usuario or g.operario, planta.activo, fecha, planta.turno, estado, horas, mot,
                                        tz=TZ, hoy=date(2026, 12, 31)).id


# --- Parte de turno -------------------------------------------------------------------
def test_parte_todo_parcial_no_opero(db, planta, gente):
    parte(db, gente, planta, date(2026, 9, 19))
    parte(db, gente, planta, date(2026, 9, 20), "PARCIAL", 1.5, motivo(db, "LIMPIEZA"))
    parte(db, gente, planta, date(2026, 9, 21), "NO_OPERO", 0, motivo(db, "SIN_DEMANDA"))
    with db.lectura() as s:
        horas = {p.fecha: p.horas_operadas for p in s.scalars(select(ParteTurno))}
    assert horas == {date(2026, 9, 19): 8, date(2026, 9, 20): 6.5, date(2026, 9, 21): 0}


@pytest.mark.parametrize("estado,horas,mot,mensaje", [
    ("PARCIAL", 1.25, "LIMPIEZA", "media hora"),
    ("PARCIAL", 9, "LIMPIEZA", "van de 0 a 8"),
    ("PARCIAL", 2, None, "motivo"),
    ("PARCIAL", 0, "LIMPIEZA", "más de 0"),
])
def test_parte_invalido(db, planta, gente, estado, horas, mot, mensaje):
    with pytest.raises(registro.ErrorRegistro, match=mensaje):
        parte(db, gente, planta, date(2026, 9, 19), estado, horas, motivo(db, mot) if mot else None)


def test_parte_duplicado_y_token(db, planta, gente):
    with db.escritura() as s:
        a = registro.registrar_parte(s, gente.operario, planta.activo, date(2026, 9, 19), planta.turno, "TODO",
                                     token="t1", tz=TZ, hoy=date(2026, 12, 31))
        b = registro.registrar_parte(s, gente.operario, planta.activo, date(2026, 9, 19), planta.turno, "TODO",
                                     token="t1", tz=TZ, hoy=date(2026, 12, 31))
        assert a.id == b.id  # doble toque: el mismo parte
    with pytest.raises(registro.ErrorRegistro, match="Ya hay un parte"):
        parte(db, gente, planta, date(2026, 9, 19))


def test_parte_futuro_y_maquina_ajena(db, planta, gente):
    with pytest.raises(registro.ErrorRegistro, match="futura"), db.escritura() as s:
        registro.registrar_parte(s, gente.operario, planta.activo, date(2027, 1, 5), planta.turno, "TODO",
                                 tz=TZ, hoy=date(2026, 12, 31))
    with pytest.raises(PermisoDenegado), db.escritura() as s:
        registro.registrar_parte(s, gente.operario, planta.activo2, date(2026, 9, 19), planta.turno, "TODO",
                                 tz=TZ, hoy=date(2026, 12, 31))


def test_el_parte_del_operario_reemplaza_al_estimado(db, planta, gente):
    with db.escritura() as s:
        assert faltantes.completar_estimados(s, date(2026, 9, 22), TZ, dias_atras=1) == 2  # 19 y 20/09
        est = s.scalar(select(ParteTurno).where(ParteTurno.fecha == date(2026, 9, 20)))
        assert est.origen == OrigenParte.ESTIMADO_SISTEMA and est.nivel_hora == NivelHora.E
    parte(db, gente, planta, date(2026, 9, 20), "PARCIAL", 2, motivo(db, "LIMPIEZA"))
    with db.lectura() as s:
        p = s.scalar(select(ParteTurno).where(ParteTurno.fecha == date(2026, 9, 20)))
        assert p.origen == OrigenParte.OPERARIO and p.horas_operadas == 6 and p.nivel_hora == NivelHora.D


def test_faltantes_y_estimados(db, planta, gente):
    parte(db, gente, planta, date(2026, 9, 19))
    with db.lectura() as s:
        f = faltantes.faltantes(s, date(2026, 9, 19), date(2026, 9, 21))
    assert [x.fecha for x in f] == [date(2026, 9, 20), date(2026, 9, 21)]
    with db.escritura() as s:
        n = faltantes.completar_estimados(s, date(2026, 9, 23), TZ, dias_atras=5)
        p = s.scalar(select(ParteTurno).where(ParteTurno.fecha == date(2026, 9, 20)))
    assert n == 5  # del 16 al 21 (hoy 23 menos 2 días de espera) = 6 días, menos el 19 que ya tenía parte
    assert p.horas_operadas == 8  # 8 h/día del listado en un solo turno


# --- Aviso, tarjetas y OT ---------------------------------------------------------------
def aviso(db, g, planta, momento, paro=True):
    with db.escritura(usuario_id=g.operario) as s:
        return registro.crear_aviso(s, g.operario, planta.activo, planta.sintoma, momento, paro).id


def cerrar(db, g, planta, eid, ini, fin, accion=AccionOT.REEMPLAZO, repuestos=()):
    with db.escritura(usuario_id=g.encargado) as s:
        ot.cerrar_correctiva(s, g.encargado, eid, ot.CierreOT(planta.posicion, planta.modo, planta.causa, accion, ini, fin,
                                                              list(repuestos)))


def test_aviso_duplicado_se_detecta(db, planta, gente):
    aviso(db, gente, planta, local(2026, 9, 20, 9, 0))
    with db.lectura() as s:
        assert len(registro.avisos_recientes(s, planta.activo, local(2026, 9, 20, 9, 20))) == 1
        assert len(registro.avisos_recientes(s, planta.activo, local(2026, 9, 20, 10, 0))) == 0


def test_tarjeta_roja_genera_aviso_y_azul_se_resuelve(db, planta, gente):
    with db.escritura() as s:
        roja = registro.crear_tarjeta(s, gente.operario, ColorTarjeta.ROJA, planta.activo, "Pieza desgastada o rota")
        azul = registro.crear_tarjeta(s, gente.operario, "AZUL", planta.activo, "Tornillo flojo")
        assert roja.estado == EstadoTarjeta.DERIVADA and roja.id_evento_generado is not None
        assert s.get(EventoFalla, roja.id_evento_generado).origen == "TARJETA_ROJA"
        registro.cerrar_tarjeta(s, gente.operario, azul.id)
        assert azul.estado == EstadoTarjeta.RESUELTA
        with pytest.raises(registro.ErrorRegistro):
            registro.crear_tarjeta(s, gente.operario, "VERDE", planta.activo, "Tornillo flojo")


def test_flujo_completo_falla_cierre_validacion(db, planta, gente):
    """Plan §10, flujo de una falla de punta a punta."""
    with db.escritura() as s:
        vidas.iniciar_vidas(s, local(2026, 9, 1, 6))
    for d in range(1, 21):
        parte(db, gente, planta, date(2026, 9, d))
    eid = aviso(db, gente, planta, local(2026, 9, 20, 10, 0))
    with db.lectura() as s:
        rep = s.scalar(select(Repuesto))
    with db.escritura() as s:
        s.add(Repuesto(codigo="DEMO-R", descripcion="Cuchillas", stock_actual=3))
    with db.lectura() as s:
        rep = s.scalar(select(Repuesto).where(Repuesto.codigo == "DEMO-R"))
    cerrar(db, gente, planta, eid, local(2026, 9, 20, 10, 30), local(2026, 9, 20, 12, 0), repuestos=[(rep.id, 1)])
    with db.lectura() as s:
        ev = s.get(EventoFalla, eid)
        assert ev.estado == EstadoEvento.CERRADO
        assert ev.tiempo_reparacion_h == 1.5 and ev.tiempo_espera_h == 0.5 and ev.horas_parada == 2
        cerrada = s.scalar(select(VidaComponente).where(VidaComponente.id_evento_cierre == eid))
        nueva = vidas.vida_abierta(s, planta.posicion)
        assert cerrada.tipo_fin == TipoFin.FALLA and not cerrada.validado and not cerrada.edad_conocida
        assert nueva.fecha_instalacion == local(2026, 9, 20, 12, 0) and nueva.tipo_reparacion == TipoReparacion.REEMPLAZO
        assert s.get(Repuesto, rep.id).stock_actual == 2
        items = validacion.bandeja(s, TZ)
        assert [i.id for i in items] == [eid]
        assert any("edad desconocida" in a for a in items[0].advertencias)
    with db.escritura(usuario_id=gente.jefe) as s:
        validacion.validar_evento(s, gente.jefe, eid)
    with db.lectura() as s:
        assert s.get(EventoFalla, eid).estado == EstadoEvento.VALIDADO
        assert s.scalar(select(VidaComponente).where(VidaComponente.id_evento_cierre == eid)).validado
        assert s.scalar(select(OrdenTrabajo).where(OrdenTrabajo.id_evento == eid)).estado == EstadoOT.VALIDADA
        assert s.scalar(select(func.count()).select_from(RecalculoPendiente)) == 1


def test_segunda_falla_tiene_edad_conocida_con_prorrateo(db, planta, gente):
    """La vida nueva empieza a las 12:00 del 20/09 (mitad del turno 6–14): cuenta 2 de las 8 h de ese turno."""
    for d in range(20, 24):
        parte(db, gente, planta, date(2026, 9, d))
    e1 = aviso(db, gente, planta, local(2026, 9, 20, 10, 0))
    cerrar(db, gente, planta, e1, local(2026, 9, 20, 10, 0), local(2026, 9, 20, 12, 0))
    e2 = aviso(db, gente, planta, local(2026, 9, 23, 8, 0))
    cerrar(db, gente, planta, e2, local(2026, 9, 23, 8, 0), local(2026, 9, 23, 9, 0))
    with db.escritura() as s:
        v = s.scalar(select(VidaComponente).where(VidaComponente.id_evento_cierre == e2))
        vidas.actualizar_edad(s, v, TZ)
        # 20/09: 12–14 = 2 h; 21 y 22: 8 + 8; 23/10: 6–8 = 2 h  → 20 h
        assert v.edad_conocida and v.edad_horas == pytest.approx(20) and v.nivel_hora == NivelHora.D


def test_falla_de_otro_modo_no_valida_contra_la_posicion(db, planta, gente):
    eid = aviso(db, gente, planta, local(2026, 9, 20, 10, 0))
    with pytest.raises(registro.ErrorRegistro, match="modo"), db.escritura() as s:
        ot.cerrar_correctiva(s, gente.encargado, eid, ot.CierreOT(planta.posicion, planta.modo_otro_tipo, planta.causa,
                                                                  AccionOT.REEMPLAZO, local(2026, 9, 20, 10),
                                                                  local(2026, 9, 20, 11)))


def test_operario_no_puede_cerrar_ot(db, planta, gente):
    eid = aviso(db, gente, planta, local(2026, 9, 20, 10, 0))
    with pytest.raises(PermisoDenegado), db.escritura() as s:
        ot.cerrar_correctiva(s, gente.operario, eid, ot.CierreOT(planta.posicion, planta.modo, planta.causa,
                                                                 AccionOT.REEMPLAZO, local(2026, 9, 20, 10),
                                                                 local(2026, 9, 20, 11)))


def test_devolver_y_volver_a_cerrar(db, planta, gente):
    eid = aviso(db, gente, planta, local(2026, 9, 20, 10, 0))
    cerrar(db, gente, planta, eid, local(2026, 9, 20, 10, 30), local(2026, 9, 20, 12, 0))
    with db.escritura(usuario_id=gente.jefe) as s:
        validacion.devolver_evento(s, gente.jefe, eid, "El fin de reparación está mal")
    cerrar(db, gente, planta, eid, local(2026, 9, 20, 10, 30), local(2026, 9, 20, 13, 0))
    with db.lectura() as s:
        assert s.scalar(select(func.count()).select_from(VidaComponente).where(
            VidaComponente.id_posicion == planta.posicion)) == 2  # una cerrada y la nueva, sin duplicar
        assert vidas.vida_abierta(s, planta.posicion).fecha_instalacion == local(2026, 9, 20, 13, 0)


def test_corregir_validado_exige_motivo_y_anular_reabre_la_vida(db, planta, gente):
    eid = aviso(db, gente, planta, local(2026, 9, 20, 10, 0))
    cerrar(db, gente, planta, eid, local(2026, 9, 20, 10, 30), local(2026, 9, 20, 12, 0))
    with db.escritura(usuario_id=gente.jefe) as s:
        validacion.validar_evento(s, gente.jefe, eid)
    with pytest.raises(registro.ErrorRegistro, match="motivo"), db.escritura(usuario_id=gente.jefe) as s:
        validacion.corregir_evento(s, gente.jefe, eid, {"fin_reparacion": local(2026, 9, 20, 13)}, "")
    with db.escritura(usuario_id=gente.jefe) as s:
        validacion.corregir_evento(s, gente.jefe, eid, {"fin_reparacion": local(2026, 9, 20, 13)}, "Hora mal cargada")
        assert s.get(EventoFalla, eid).tiempo_reparacion_h == 2.5
    with db.escritura(usuario_id=gente.jefe) as s:
        validacion.anular_evento(s, gente.jefe, eid, "Era un duplicado")
    with db.lectura() as s:
        assert s.get(EventoFalla, eid).estado == EstadoEvento.ANULADO
        abierta = vidas.vida_abierta(s, planta.posicion)
        assert abierta.id_evento_cierre is None
        assert s.scalar(select(func.count()).select_from(VidaComponente)) == 1


def test_cambio_preventivo_es_suspension(db, planta, gente):
    with db.escritura(usuario_id=gente.encargado) as s:
        o = ot.registrar_cambio(s, gente.encargado, planta.posicion, local(2026, 9, 20, 7))
        oid = o.id
    with db.lectura() as s:
        v = s.scalar(select(VidaComponente).where(VidaComponente.id_ot_cierre == oid))
        assert v.tipo_fin == TipoFin.SUSPENSION_PREVENTIVA
        assert [i.tipo for i in validacion.bandeja(s, TZ)] == ["ot"]
    with db.escritura(usuario_id=gente.jefe) as s:
        validacion.validar_ot(s, gente.jefe, oid)
    with db.lectura() as s:
        assert s.scalar(select(VidaComponente).where(VidaComponente.id_ot_cierre == oid)).validado


def test_sugerencia_de_parte_tras_aviso(db, planta, gente):
    eid = aviso(db, gente, planta, local(2026, 9, 20, 10, 0))
    cerrar(db, gente, planta, eid, local(2026, 9, 20, 10, 30), local(2026, 9, 20, 12, 0))
    from circularis_rel.datos.modelos import Turno
    with db.lectura() as s:
        sug = registro.sugerencia_parte(s, planta.activo, date(2026, 9, 20), s.get(Turno, planta.turno), TZ)
    assert sug["estado"] == EstadoParte.PARCIAL and sug["horas_no_operadas"] == 2


def test_falla_sin_parada_se_advierte(db, planta, gente):
    parte(db, gente, planta, date(2026, 9, 20))  # operó todo
    eid = aviso(db, gente, planta, local(2026, 9, 20, 10, 0))
    cerrar(db, gente, planta, eid, local(2026, 9, 20, 10, 30), local(2026, 9, 20, 12, 0))
    with db.lectura() as s:
        assert any("Falla sin parada" in a for a in validacion.bandeja(s, TZ)[0].advertencias)
