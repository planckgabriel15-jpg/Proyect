"""Fase 2: alertas firmes, piloto, histórico A/B, flota, criticidad guiada y catálogos."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from circularis_rel.asistente import etapas
from circularis_rel.datos.enums import (
    AparicionFalla,
    CapacidadFalla,
    ClaseTriage,
    ConjuntoDatos,
    EstadoEvento,
    EstadoParte,
    MetodoCriticidad,
    OrigenParte,
    Rol,
    TipoCatalogo,
    TipoFin,
)
from circularis_rel.datos.modelos import (
    ActivoTurno,
    Alerta,
    EventoFalla,
    ParteTurno,
    PosicionComponente,
    ResultadoWeibull,
    Usuario,
    VidaComponente,
    VidaHistorica,
)
from circularis_rel.servicios import alertas, catalogos, criticidad, flota, panel, piloto, recalculo
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.permisos import PermisoDenegado
from circularis_rel.servicios.registro import ErrorRegistro

TZ = ZoneInfo("America/Argentina/Cordoba")
INICIO = datetime(2025, 1, 6, tzinfo=TZ)


def _vidas(s, id_posicion: int, id_modo: int, edades: list[tuple[float, str]]) -> datetime:
    """Vidas cerradas consecutivas (24 h por día, como el Plan §15); deja una vida en servicio al final."""
    momento = INICIO
    for edad, estado in edades:
        fin = momento + timedelta(hours=edad)
        s.add(VidaComponente(id_posicion=id_posicion, fecha_instalacion=momento, fecha_fin=fin,
                             tipo_fin=TipoFin.FALLA if estado == "F" else TipoFin.SUSPENSION_PREVENTIVA,
                             id_modo_falla=id_modo if estado == "F" else None, validado=True))
        momento = fin
    s.add(VidaComponente(id_posicion=id_posicion, fecha_instalacion=momento))
    return momento


@pytest.fixture
def continuo(db, planta):
    """Turno de 24 h todos los días en las dos máquinas, con partes desde INICIO hasta hoy."""
    from circularis_rel.datos.modelos import Turno

    with db.escritura() as s:
        t = Turno(codigo="DEMO-24", nombre="Continuo", hora_inicio=time(0), hora_fin=time(0), duracion_h=24)
        s.add(t)
        s.flush()
        hoy = date.today()
        for a in (planta.activo, planta.activo2):
            s.add(ActivoTurno(id_activo=a, id_turno=t.id, dias="1,2,3,4,5,6,7"))
            d = INICIO.date()
            while d <= hoy:
                s.add(ParteTurno(id_activo=a, fecha=d, id_turno=t.id, horas_turno=24, estado=EstadoParte.TODO,
                                 horas_no_operadas=0, horas_operadas=24))
                d += timedelta(days=1)
        return t.id


# ---------------------------------------------------------------------------
# Alertas firmes
# ---------------------------------------------------------------------------


def test_alertas_orientativas_hasta_confianza_media(db, planta, continuo):
    with db.escritura() as s:
        _vidas(s, planta.posicion, planta.modo, [(300, "S"), (410, "F"), (560, "F"), (650, "S"), (690, "F"), (780, "F"), (920, "F")])
        s.flush()
        recalculo.recalcular_todo(s, TZ)
        e = panel.ultimo_estado(s, planta.posicion)
        assert e.semaforo.value == "ROJO" and e.confianza.value == "BAJA"
        r = alertas.actualizar_riesgo(s, date.today())
        assert r["orientativas"] == 1 and r["firmes"] == 0
        a = s.scalar(select(Alerta).where(Alerta.resuelta_en.is_(None)))
        assert a.tipo == "RIESGO_ORIENTATIVO" and a.destinatarios is None  # no va por mail
        # Con el umbral en BAJA pasa a firme y la orientativa se resuelve.
        P.fijar(s, "alertas.confianza_firme", "BAJA", date(2000, 1, 2))
        alertas.actualizar_riesgo(s, date.today())
        abiertas = list(s.scalars(select(Alerta).where(Alerta.resuelta_en.is_(None))))
        assert [x.tipo for x in abiertas] == ["RIESGO"] and abiertas[0].destinatarios == "JEFE"
        # Repetir no duplica.
        alertas.actualizar_riesgo(s, date.today())
        assert len(list(s.scalars(select(Alerta).where(Alerta.resuelta_en.is_(None))))) == 1
        # Si sale del rojo, se resuelve sola.
        e.semaforo = type(e.semaforo)("VERDE")
        assert alertas.actualizar_riesgo(s, date.today())["resueltas"] == 1


# ---------------------------------------------------------------------------
# Piloto
# ---------------------------------------------------------------------------


def test_semanas_cerradas():
    semanas = piloto.semanas_cerradas(date(2026, 10, 15), 2)  # jueves
    assert semanas == [(date(2026, 9, 28), date(2026, 10, 4)), (date(2026, 10, 5), date(2026, 10, 11))]


def test_criterio_del_piloto(db, planta):
    hoy = date(2026, 10, 15)
    with db.escritura() as s:
        s.add(ActivoTurno(id_activo=planta.activo, id_turno=planta.turno, dias="1,2,3,4,5"))
        s.add(ActivoTurno(id_activo=planta.activo2, id_turno=planta.turno, dias="1,2,3,4,5"))
        P.fijar(s, "piloto.maquinas", ["DEMO-AGR-001", "DEMO-AGR-002"], date(2000, 1, 2))
        for a in (planta.activo, planta.activo2):
            for inicio, fin in piloto.semanas_cerradas(hoy, 2):
                d = inicio
                while d <= fin:
                    if d.weekday() < 5:
                        estimado = a == planta.activo2 and d == fin - timedelta(days=2)  # un viernes estimado
                        s.add(ParteTurno(id_activo=a, fecha=d, id_turno=planta.turno, horas_turno=8, estado=EstadoParte.TODO,
                                         horas_no_operadas=0, horas_operadas=8,
                                         origen=OrigenParte.ESTIMADO_SISTEMA if estimado else OrigenParte.OPERARIO))
                    d += timedelta(days=1)
        e = piloto.estado(s, hoy, TZ)
    assert not e.sin_maquinas_definidas
    agr1, agr2 = e.maquinas
    assert agr1.cumple and all(w.fraccion == 1 for w in agr1.semanas[-2:])
    # 4 de 5 partes del operario = 80 %: no alcanza el 90 %.
    assert not agr2.cumple and agr2.semanas[-1].fraccion == pytest.approx(0.8)
    assert not e.cumple


def test_piloto_sin_maquinas_del_parametro_usa_todas(db, planta):
    with db.lectura() as s:
        e = piloto.estado(s, date(2026, 10, 15), TZ)
    assert e.sin_maquinas_definidas and e.faltan_codigos == ["EXT-001", "LAV-001", "ENF-001", "AGR-001"]
    assert {m.codigo for m in e.maquinas} == {"DEMO-AGR-001", "DEMO-AGR-002"}


def test_criterio_fase1_estable_en_puesta_en_marcha(db, planta):
    with db.lectura() as s:
        v = etapas.CRITERIOS["fase1_estable"](s)
    assert v.cumple is False and "Partes" in v.detalle


# ---------------------------------------------------------------------------
# Histórico A/B
# ---------------------------------------------------------------------------


def test_comparacion_con_historico(db, planta, continuo):
    with db.escritura() as s:
        _vidas(s, planta.posicion, planta.modo, [(410, "F"), (560, "F"), (690, "F"), (780, "F")])
        for edad in (500, 620, 700):
            s.add(VidaHistorica(id_activo=planta.activo, id_posicion=planta.posicion, tipo_fin=TipoFin.FALLA,
                                id_modo_falla=planta.modo, edad_horas=edad, clase_triage=ClaseTriage.A, fuente="Planilla",
                                respaldo="OT papel", fecha_fin=date(2024, 5, 1)))
        s.flush()
        recalculo.recalcular_todo(s, TZ)
        nuevos = s.scalar(select(ResultadoWeibull).where(ResultadoWeibull.vigente.is_(True),
                                                         ResultadoWeibull.conjunto_datos == ConjuntoDatos.NUEVOS))
        con = s.scalar(select(ResultadoWeibull).where(ResultadoWeibull.vigente.is_(True),
                                                      ResultadoWeibull.conjunto_datos == ConjuntoDatos.NUEVOS_MAS_HIST_AB))
        assert nuevos.n_fallas == 4 and con.n_fallas == 7
        pos = s.get(PosicionComponente, planta.posicion)
        assert [r.id for r in recalculo.ajustes_para_semaforo(s, planta.tipo, planta.activo, pos.id)] == [nuevos.id]
        P.fijar(s, "motor.semaforo_con_historico", True, date(2000, 1, 2))
        assert [r.id for r in recalculo.ajustes_para_semaforo(s, planta.tipo, planta.activo, pos.id)] == [con.id]


def test_pares_incluye_fallas_solo_historicas(db, planta):
    with db.escritura() as s:
        s.add(VidaHistorica(id_activo=planta.activo, id_posicion=planta.posicion, tipo_fin=TipoFin.FALLA,
                            id_modo_falla=planta.modo, edad_horas=500, clase_triage=ClaseTriage.A, fuente="x", respaldo="y",
                            fecha_fin=date(2024, 5, 1)))
        s.add(VidaHistorica(id_activo=planta.activo, id_posicion=planta.posicion2, tipo_fin=TipoFin.FALLA,
                            id_modo_falla=planta.modo_otro_tipo, edad_horas=500, clase_triage=ClaseTriage.C, fuente="x"))
        s.flush()
        assert recalculo.pares_con_fallas(s) == {(planta.tipo, planta.modo, planta.activo)}  # la C no entra


# ---------------------------------------------------------------------------
# Flota
# ---------------------------------------------------------------------------


def test_flota_por_tipo_y_uso_en_el_semaforo(db, planta, continuo):
    with db.escritura() as s:
        pos2 = PosicionComponente(id_activo=planta.activo2, id_tipo_componente=planta.tipo, codigo="CUCH", critica=True)
        s.add(pos2)
        s.flush()
        _vidas(s, planta.posicion, planta.modo, [(410, "F"), (560, "F"), (690, "F"), (780, "F"), (650, "S")])
        _vidas(s, pos2.id, planta.modo, [(450, "F"), (720, "F"), (600, "S")])
        s.flush()
        recalculo.recalcular_todo(s, TZ)
        propio2 = s.scalar(select(ResultadoWeibull).where(ResultadoWeibull.id_activo == planta.activo2,
                                                          ResultadoWeibull.vigente.is_(True)))
        assert propio2.beta is None  # 2 fallas: sin ajuste propio
        grupo = next(g for g in flota.grupos(s) if g.clave == f"tipo:{planta.tipo}")
        assert set(grupo.posiciones) == {planta.posicion, pos2.id}
        prueba = flota.probar(s, grupo, planta.modo, TZ)
        assert prueba.p is not None and prueba.gl == 2 and prueba.agrupable
        assert prueba.por_maquina == {"DEMO-AGR-001": (4, 2), "DEMO-AGR-002": (2, 2)}
        r = flota.ajustar(s, grupo, planta.modo, TZ)
        assert r.alcance.value == "FLOTA" and r.n_fallas == 6 and r.ids_activos_flota == sorted([planta.activo, planta.activo2])
        r = flota.ajustar(s, grupo, planta.modo, TZ)  # la edad en servicio avanza: puede haber fila nueva, pero una sola vigente
        assert len([x for x in s.scalars(select(ResultadoWeibull).where(ResultadoWeibull.alcance == r.alcance,
                                                                        ResultadoWeibull.vigente.is_(True)))]) == 1
        usados = recalculo.ajustes_para_semaforo(s, planta.tipo, planta.activo2, pos2.id)
        assert [x.id for x in usados] == [r.id]
        # La máquina con ajuste propio usa el suyo.
        assert all(x.alcance.value == "MAQUINA" for x in recalculo.ajustes_para_semaforo(s, planta.tipo, planta.activo,
                                                                                            planta.posicion))
        assert recalculo.recalcular_todo(s, TZ)["flotas"] == 1


def test_equivalencias(db, planta):
    with db.escritura() as s:
        with pytest.raises(ValueError):
            flota.declarar_equivalencia(s, "Correas", [planta.posicion2])
        flota.declarar_equivalencia(s, "Mixto", [planta.posicion, planta.posicion2])
        g = next(g for g in flota.grupos(s) if g.clave == "equiv:Mixto")
        assert set(g.posiciones) == {planta.posicion, planta.posicion2}
        with pytest.raises(ValueError, match="ya está"):
            flota.declarar_equivalencia(s, "Otro", [planta.posicion, planta.posicion2])
        flota.declarar_equivalencia(s, "Mixto", [planta.posicion, planta.posicion2])  # redeclarar el mismo grupo


# ---------------------------------------------------------------------------
# Criticidad guiada
# ---------------------------------------------------------------------------


TP_AGR = dict(uso=5, alternativa=2, influencia=4, calidad=4, ambiente=3, seguridad=5)  # TP N.º 1: 23 puntos, Media


def test_criticidad_tp_desde_la_pantalla(db, planta):
    with db.escritura() as s:
        ev = criticidad.guardar(s, planta.jefe, planta.activo, MetodoCriticidad.TP_6_CRITERIOS, TP_AGR)
        primera = ev
        assert ev.puntaje == 23 and ev.nivel == "Media" and ev.clase.value == "B"
        from circularis_rel.datos.modelos import Activo

        act = s.get(Activo, planta.activo)
        assert act.criticidad_clase.value == "B" and act.criticidad_puntaje == 23
        nueva = criticidad.guardar(s, planta.jefe, planta.activo, MetodoCriticidad.TP_6_CRITERIOS, TP_AGR, clase_manual="A")
        assert nueva.clase.value == "A" and nueva.criterios["clase_calculada"] == "B"
        assert not primera.vigente and [h.vigente for h in criticidad.historial(s, planta.activo)] == [True, False]


def test_criticidad_u1(db, planta):
    u1 = dict(uso=4, alternativa=5, influencia=4, calidad=4, ambiente=2, seguridad=5)
    with db.escritura() as s:
        with pytest.raises(ErrorRegistro, match="elegí la clase"):
            criticidad.guardar(s, planta.jefe, planta.activo, MetodoCriticidad.PONDERACION_U1, u1)
        with pytest.raises(ErrorRegistro):  # 3 no está en la escala U1 de uso (4/2/1)
            criticidad.guardar(s, planta.jefe, planta.activo, MetodoCriticidad.PONDERACION_U1, u1 | {"uso": 3}, "A")
        ev = criticidad.guardar(s, planta.jefe, planta.activo, MetodoCriticidad.PONDERACION_U1, u1, clase_manual="A")
        assert ev.puntaje == 24 and ev.clase.value == "A"
        P.fijar(s, "criticidad.u1_cortes", {"A": 25, "B": 18}, date(2000, 1, 2))
        ev = criticidad.guardar(s, planta.jefe, planta.activo, MetodoCriticidad.PONDERACION_U1, u1)
        assert ev.clase.value == "B"


def test_criticidad_solo_el_jefe(db, planta):
    with db.escritura() as s:
        enc = Usuario(usuario="enc", nombre="Encargado", rol=Rol.ENCARGADO, hash_password="x")
        s.add(enc)
        s.flush()
        with pytest.raises(PermisoDenegado):
            criticidad.guardar(s, enc.id, planta.activo, MetodoCriticidad.TP_6_CRITERIOS, TP_AGR)


def test_cuadrantes(db, planta):
    hoy = date.today()
    falla = datetime.combine(hoy - timedelta(days=3), time(8), tzinfo=TZ)
    with db.escritura() as s:
        for ap, cap in ((AparicionFalla.REPENTINA, CapacidadFalla.TOTAL), (AparicionFalla.REPENTINA, CapacidadFalla.TOTAL),
                        (AparicionFalla.PROGRESIVA, CapacidadFalla.PARCIAL), (None, None)):
            s.add(EventoFalla(id_activo=planta.activo, id_posicion=planta.posicion, fecha_hora_falla=falla, id_modo=planta.modo,
                              id_causa=planta.causa, inicio_reparacion=falla, fin_reparacion=falla + timedelta(hours=1),
                              estado=EstadoEvento.VALIDADO, aparicion=ap, capacidad=cap))
        s.flush()
        q = panel.cuadrantes(s, hoy - timedelta(days=30), hoy, TZ)
    assert q["conteo"][("REPENTINA", "TOTAL")] == 2 and q["conteo"][("PROGRESIVA", "PARCIAL")] == 1
    assert q["sin_clasificar"] == 1


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------


def test_catalogos(db, planta):
    with db.escritura() as s:
        with pytest.raises(catalogos.ErrorCatalogo, match="Código inválido"):
            catalogos.guardar_item(s, TipoCatalogo.SINTOMA, "ñ", "x")
        si = catalogos.guardar_item(s, TipoCatalogo.SINTOMA, "ruido metalico", "Ruido metálico")
        assert si.codigo == "RUIDO_METALICO"
        with pytest.raises(catalogos.ErrorCatalogo, match="al menos a un tipo"):
            catalogos.guardar_item(s, TipoCatalogo.MODO, "ROTURA", "Rotura")
        s.rollback()
    with db.escritura() as s:
        m = catalogos.guardar_item(s, TipoCatalogo.MODO, "ROTURA", "Rotura", tipos_aplica=[planta.tipo])
        m2 = catalogos.guardar_item(s, TipoCatalogo.MODO, "ROTURA", "Rotura total", activo=False, tipos_aplica=[])
        assert m2.id == m.id and m2.descripcion == "Rotura total" and not m2.activo  # desactivado puede quedar sin tipos
        mot = catalogos.guardar_motivo(s, "corte luz", "Corte de luz", cuenta_como_requerida=False)
        assert mot.codigo == "CORTE_LUZ" and not mot.cuenta_como_requerida
