"""Fase 4: TPM y OEE, horómetro, Crow-AMSAA y Laplace por máquina, AMFE con O calculada y revisión en t = η."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from circularis_rel.datos.enums import EstadoEvento, EstadoParte, NivelHora, OrigenDato, Rol
from circularis_rel.datos.modelos import (
    Activo,
    ActivoTurno,
    Alerta,
    AmfeItem,
    EventoFalla,
    MotivoParada,
    ParteTurno,
    ResultadoSistema,
    ResultadoWeibull,
    Turno,
    Usuario,
)
from circularis_rel.servicios import amfe, kpis_planta, registro, sistemas, tpm
from circularis_rel.servicios.registro import ErrorRegistro

TZ = ZoneInfo("America/Argentina/Cordoba")


def _motivo(s, codigo):
    return s.scalar(select(MotivoParada.id).where(MotivoParada.codigo == codigo))


# ---------------------------------------------------------------------------
# TPM: RO = Dp · Di · Rv · Tq y seis grandes pérdidas
# ---------------------------------------------------------------------------


def test_rendimiento_operacional(db, planta):
    d = date(2026, 3, 2)
    with db.escritura() as s:
        s.get(Activo, planta.activo).ciclo_teorico_s = 60  # 60 piezas por hora en teoría
        partes = [  # (horas no operadas, motivo, cantidad, rechazadas)
            (0.0, None, 420, 21),          # 8 h operadas
            (2.0, "PREPARACION", 300, 0),  # 6 h operadas, 2 h de preparación
            (1.0, "FALLA", 360, 18),       # 7 h operadas, 1 h de avería
            (8.0, "SIN_DEMANDA", None, None),  # no cuenta como requerido
        ]
        for i, (no_op, motivo, cant, rech) in enumerate(partes):
            estado = EstadoParte.TODO if no_op == 0 else EstadoParte.NO_OPERO if no_op == 8 else EstadoParte.PARCIAL
            s.add(ParteTurno(id_activo=planta.activo, fecha=d + timedelta(days=i), id_turno=planta.turno, horas_turno=8,
                             estado=estado, horas_no_operadas=no_op, horas_operadas=8 - no_op,
                             id_motivo=_motivo(s, motivo) if motivo else None, cantidad_procesada=cant, cantidad_rechazada=rech))
        s.flush()
        r = tpm.calcular(s, planta.activo, d, d + timedelta(days=5))
    assert (r.tt, r.tap, r.tai, r.horas_operadas) == (24, 2, 1, 21)
    assert r.dp == pytest.approx(22 / 24) and r.di == pytest.approx(21 / 22)
    assert r.rv == pytest.approx(1080 * 60 / 3600 / 21)  # 18 h teóricas en 21 h operadas
    assert r.tq == pytest.approx((1080 - 39) / 1080)
    assert r.ro == pytest.approx(r.dp * r.di * r.rv * r.tq)
    assert r.perdidas_h["Averías"] == 1 and r.perdidas_h["Preparación y ajuste"] == 2
    assert r.perdidas_h["Velocidad reducida"] == pytest.approx(21 * (1 - r.rv))
    assert r.perdidas_h["Defectos de calidad y reproceso"] == pytest.approx(21 * r.rv * (1 - r.tq))


def test_rendimiento_sin_datos_de_produccion(db, planta):
    with db.escritura() as s:
        s.add(ParteTurno(id_activo=planta.activo, fecha=date(2026, 3, 2), id_turno=planta.turno, horas_turno=8,
                         estado=EstadoParte.TODO, horas_no_operadas=0, horas_operadas=8))
        s.flush()
        r = tpm.calcular(s, planta.activo, date(2026, 3, 1), date(2026, 3, 31))
    assert r.dp == 1 and r.di == 1 and r.rv is None and r.tq is None and r.ro is None
    assert "cantidad procesada en los partes" in r.faltan


def test_oee_con_calidad(db, planta):
    with db.escritura() as s:
        s.get(Activo, planta.activo).ciclo_teorico_s = 60
        s.add(ParteTurno(id_activo=planta.activo, fecha=date(2026, 3, 2), id_turno=planta.turno, horas_turno=8,
                         estado=EstadoParte.TODO, horas_no_operadas=0, horas_operadas=8, cantidad_procesada=400,
                         cantidad_rechazada=20))
        s.flush()
        k = kpis_planta.kpis_maquina(s, planta.activo, date(2026, 3, 1), date(2026, 3, 31), TZ)
    assert k.oee == pytest.approx(1.0 * (400 / 480) * (380 / 400))


# ---------------------------------------------------------------------------
# Parte de turno: rechazadas y horómetro
# ---------------------------------------------------------------------------


def test_parte_con_rechazadas_y_horometro(db, planta):
    hoy = date(2026, 3, 10)
    with db.escritura() as s:
        op = Usuario(usuario="op", nombre="Operario", rol=Rol.OPERARIO, hash_password="x")
        s.add(op)
        s.flush()
        from circularis_rel.datos.modelos import UsuarioActivo

        s.add(UsuarioActivo(id_usuario=op.id, id_activo=planta.activo))
        s.add(ActivoTurno(id_activo=planta.activo, id_turno=planta.turno))
        s.flush()
        with pytest.raises(ErrorRegistro, match="rechazadas"):
            registro.registrar_parte(s, op.id, planta.activo, hoy, planta.turno, "TODO", cantidad=10, rechazada=11, tz=TZ, hoy=hoy)
        p1 = registro.registrar_parte(s, op.id, planta.activo, hoy - timedelta(days=1), planta.turno, "TODO",
                                      lectura_horometro=1000, tz=TZ, hoy=hoy)
        assert p1.nivel_hora == NivelHora.D  # primera lectura: no hay contra qué comparar
        p2 = registro.registrar_parte(s, op.id, planta.activo, hoy, planta.turno, "TODO", lectura_horometro=1008.2,
                                      cantidad=100, rechazada=3, tz=TZ, hoy=hoy)
        assert p2.nivel_hora == NivelHora.M and p2.cantidad_rechazada == 3  # 8,2 h medidas contra 8 h del parte
        with pytest.raises(ErrorRegistro, match="menor que la anterior"):
            registro.registrar_parte(s, op.id, planta.activo, hoy + timedelta(days=1), planta.turno, "TODO",
                                     lectura_horometro=1000, tz=TZ, hoy=hoy + timedelta(days=1))


# ---------------------------------------------------------------------------
# La máquina como sistema reparable
# ---------------------------------------------------------------------------


@pytest.fixture
def continuo(db, planta):
    with db.escritura() as s:
        t = Turno(codigo="DEMO-24", nombre="Continuo", hora_inicio=time(0), hora_fin=time(0), duracion_h=24)
        s.add(t)
        s.flush()
        s.add(ActivoTurno(id_activo=planta.activo, id_turno=t.id, dias="1,2,3,4,5,6,7"))
        for k in range(200):
            s.add(ParteTurno(id_activo=planta.activo, fecha=date(2026, 1, 1) + timedelta(days=k), id_turno=t.id,
                             horas_turno=24, estado=EstadoParte.TODO, horas_no_operadas=0, horas_operadas=24))
    return db


def _falla(s, planta, cuando: datetime):
    s.add(EventoFalla(id_activo=planta.activo, id_posicion=planta.posicion, fecha_hora_falla=cuando, id_modo=planta.modo,
                      id_causa=planta.causa, inicio_reparacion=cuando, fin_reparacion=cuando + timedelta(hours=1),
                      estado=EstadoEvento.VALIDADO))


def test_tendencia_de_degradacion(continuo, planta):
    inicio = datetime(2026, 1, 1, 12, tzinfo=TZ)
    # Fallas cada vez más seguidas: días 100, 140, 165, 180, 190, 196.
    with continuo.escritura() as s:
        for dia in (100, 140, 165, 180, 190, 196):
            _falla(s, planta, inicio + timedelta(days=dia))
        s.flush()
        tiempos, T = sistemas.tiempos_de_falla(s, planta.activo, date(2026, 1, 1), date(2026, 7, 19), TZ)
        assert T == 200 * 24 and tiempos[0] == pytest.approx(100 * 24 + 12)  # días previos + medio día
        t = sistemas.analizar(s, planta.activo, date(2026, 1, 1), date(2026, 7, 19), TZ)
        assert t.crow.beta > 1 and t.laplace_u > 0 and t.degradacion and "degrada" in t.texto
        sistemas.recalcular(s, date(2026, 1, 1), date(2026, 7, 19), TZ)
        assert s.scalar(select(Alerta).where(Alerta.tipo == "DEGRADACION")).resuelta_en is None
        assert s.scalar(select(ResultadoSistema).where(ResultadoSistema.id_activo == planta.activo)).n_fallas == 6


def test_pocas_fallas_no_hay_tendencia(continuo, planta):
    with continuo.escritura() as s:
        _falla(s, planta, datetime(2026, 2, 1, 12, tzinfo=TZ))
        s.flush()
        t = sistemas.analizar(s, planta.activo, date(2026, 1, 1), date(2026, 7, 19), TZ)
    assert t.crow is None and "al menos" in t.texto


# ---------------------------------------------------------------------------
# AMFE
# ---------------------------------------------------------------------------


ESCALA = [[0.95, 10], [0.85, 9], [0.70, 8], [0.50, 7], [0.30, 6], [0.15, 5], [0.07, 4], [0.03, 3]]


@pytest.mark.parametrize("f,o", [(0.99, 10), (0.9, 9), (0.6, 7), (0.2, 5), (0.05, 3), (0.001, 2)])
def test_escala_de_ocurrencia(f, o):
    assert amfe.ocurrencia_por_f(f, ESCALA) == o


def test_o_calculada_con_weibull(continuo, planta):
    from circularis_rel.motor import kpis

    hoy = date(2026, 7, 19)
    with continuo.escritura() as s:
        item = AmfeItem(id_activo=planta.activo, id_tipo_componente=planta.tipo, id_modo=planta.modo, g=6, o=5, d=4,
                        origen=OrigenDato.TP1_ILUSTRATIVO)
        s.add(item)
        s.add(ResultadoWeibull(id_tipo_componente=planta.tipo, id_modo=planta.modo, alcance="MAQUINA", id_activo=planta.activo,
                               n_fallas=5, n_suspensiones=2, beta=3.42, eta=774, confianza="BAJA", version_motor="1",
                               hash_datos="x", vigente=True))
        s.flush()
        f, texto = amfe.f_un_anio(s, item, hoy)
        assert f == pytest.approx(kpis.infiabilidad(24 * 365, 3.42, 774)) and "β = 3.42" in texto
        assert amfe.actualizar_ocurrencias(s, hoy) == 1 and item.o_calculada == 10  # 8760 h ≫ η: falla seguro en el año
        assert item.o == 5  # la O del TP no se pisa
        amfe.editar(s, item.id, g=6, o=10, d=4, ap="H", acciones="Cambio cada 375 h", responsable="Jefe", fecha=None)
        assert item.origen == OrigenDato.JEFE and item.npr == 240
        with pytest.raises(ValueError):
            amfe.editar(s, item.id, g=11, o=1, d=1, ap=None, acciones=None, responsable=None, fecha=None)
        with pytest.raises(ValueError):
            amfe.editar(s, item.id, g=1, o=1, d=1, ap="X", acciones=None, responsable=None, fecha=None)


def test_amfe_sin_weibull(db, planta):
    with db.escritura() as s:
        item = AmfeItem(id_tipo_componente=planta.tipo, id_modo=planta.modo, g=5, o=5, d=5)
        s.add(item)
        s.flush()
        assert amfe.f_un_anio(s, item, date(2026, 7, 1))[0] is None
        amfe.actualizar_ocurrencias(s, date(2026, 7, 1))
        assert item.o_calculada is None
