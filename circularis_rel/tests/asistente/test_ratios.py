"""Ratios del tablero [12.E] (prueba 11 del PLAN_TECNICO): un caso numérico por indicador."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from circularis_rel.asistente import tablero as T
from circularis_rel.datos.enums import EstadoEvento, EstadoOT, EstadoParte, TipoOT
from circularis_rel.datos.modelos import EventoFalla, OrdenTrabajo, ParteTurno
from circularis_rel.servicios import parametros as P

TZ = ZoneInfo("America/Argentina/Cordoba")
MES = "2026-03"


@pytest.fixture
def mes(db, planta):
    """Marzo 2026: 400 h operadas, 1 falla con 5 h de parada, OT preventiva de 10 HH y correctiva de 40 HH
    más $100.000 de servicio externo. Tarifa $10.000/h."""
    with db.escritura() as s:
        P.fijar(s, "costos.tarifa_mo_ars_h", 10_000, date(2026, 1, 1))
        for activo in (planta.activo, planta.activo2):
            for d in range(1, 26):
                s.add(ParteTurno(id_activo=activo, fecha=date(2026, 3, d), id_turno=planta.turno, horas_turno=8,
                                 estado=EstadoParte.TODO, horas_no_operadas=0, horas_operadas=8))
        falla = datetime(2026, 3, 10, 8, tzinfo=TZ)
        ev = EventoFalla(id_activo=planta.activo, id_posicion=planta.posicion, fecha_hora_falla=falla, id_modo=planta.modo,
                         id_causa=planta.causa, inicio_reparacion=falla, fin_reparacion=falla + timedelta(hours=4),
                         tiempo_reparacion_h=4, horas_parada=5, estado=EstadoEvento.VALIDADO)
        s.add(ev)
        s.flush()
        s.add(OrdenTrabajo(numero="OT-T-1", tipo=TipoOT.CORRECTIVA, id_activo=planta.activo, id_evento=ev.id,
                           estado=EstadoOT.VALIDADA, inicio_real=falla, fin_real=falla + timedelta(hours=4),
                           hh_propias=40, costo_externo_ars=100_000))
        s.add(OrdenTrabajo(numero="OT-T-2", tipo=TipoOT.PREVENTIVA, id_activo=planta.activo, estado=EstadoOT.CERRADA,
                           inicio_real=datetime(2026, 3, 20, 8, tzinfo=TZ), fin_real=datetime(2026, 3, 20, 10, tzinfo=TZ),
                           hh_propias=10))
        # Fuera del mes: no cuenta
        s.add(OrdenTrabajo(numero="OT-T-3", tipo=TipoOT.PREVENTIVA, id_activo=planta.activo, estado=EstadoOT.CERRADA,
                           inicio_real=datetime(2026, 4, 1, 8, tzinfo=TZ), fin_real=datetime(2026, 4, 1, 10, tzinfo=TZ),
                           hh_propias=99))
    return db


def _valores(db) -> dict[str, T.ValorIndicador]:
    with db.lectura() as s:
        return {v.codigo: v for v in T.tablero(s, MES, TZ)}


def test_variables_del_sistema(mes):
    with mes.lectura() as s:
        v, faltan = T.variables_sistema(s, MES, TZ)
    basicas = {k: v[k] for k in ("CPREV", "CCORR", "CTMN", "HHMP", "HHMC", "HHTM", "HPM", "HPR")}
    assert basicas == pytest.approx({"CPREV": 100_000, "CCORR": 500_000, "CTMN": 600_000, "HHMP": 10, "HHMC": 40,
                                     "HHTM": 50, "HPM": 5, "HPR": 400})
    # Tablero completo: MO contratada (externos) y propia (HH × tarifa), y CIT con fijos ≈ preventivo, variables ≈ correctivo.
    assert v["CMOC"] == 100_000 and v["CMOP"] == pytest.approx(500_000)
    assert v["CFJ"] == 100_000 and v["CV"] == 500_000
    assert "CFA" not in v  # sin margen de la línea no se puede valorizar la producción perdida
    assert faltan == []


def test_sin_datos_cargados_falta_dato(mes):
    v = _valores(mes)
    assert v["CPCT"].valor == pytest.approx(100_000 / 600_000)
    assert v["HPHP"].valor == pytest.approx(5 / 400)
    for codigo in ("CMFT", "TBMP", "TBMC", "OCPM"):  # necesitan facturación u horas-hombre disponibles
        assert v[codigo].valor is None and v[codigo].faltan
        assert v[codigo].color == "GRIS"


def test_un_caso_por_indicador(mes):
    with mes.escritura() as s:
        T.cargar_dato(s, MES, "FETP", 30_000_000)
        T.cargar_dato(s, MES, "HHDP", 160)
    v = _valores(mes)
    assert v["CMFT"].valor == pytest.approx(600_000 / 30_000_000)  # 2 %
    assert v["CMFT"].variables["CTMN"] == (600_000, "sistema") and v["CMFT"].notas
    assert v["CPCT"].valor == pytest.approx(1 / 6)
    assert v["HPHP"].valor == pytest.approx(0.0125)
    assert v["TBMP"].valor == pytest.approx(10 / 160)
    assert v["TBMC"].valor == pytest.approx(40 / 160)
    assert v["OCPM"].valor == pytest.approx((160 - 50) / 160)


def test_lo_cargado_manda_sobre_lo_calculado(mes):
    with mes.escritura() as s:
        T.cargar_dato(s, MES, "FETP", 30_000_000)
        T.cargar_dato(s, MES, "CTMN", 900_000)
    v = _valores(mes)
    assert v["CMFT"].valor == pytest.approx(0.03)
    assert v["CMFT"].variables["CTMN"] == (900_000, "cargado") and not v["CMFT"].notas
    with mes.escritura() as s:
        T.cargar_dato(s, MES, "CTMN", None)  # borrar vuelve al valor del sistema
    assert _valores(mes)["CMFT"].valor == pytest.approx(0.02)


def test_ociosidad_negativa_son_horas_extra(mes):
    with mes.escritura() as s:
        T.cargar_dato(s, MES, "HHDP", 40)
    v = _valores(mes)["OCPM"]
    assert v.valor == pytest.approx(-0.25) and "horas extra" in v.notas[0]


def test_dato_invalido(mes):
    with mes.escritura() as s:
        with pytest.raises(ValueError):
            T.cargar_dato(s, MES, "INVENTADO", 1)
        with pytest.raises(ValueError):
            T.cargar_dato(s, MES, "FETP", -1)


def test_sin_tarifa_los_costos_faltan(db, planta):
    with db.lectura() as s:
        v = {x.codigo: x for x in T.tablero(s, MES, TZ)}
    assert v["CPCT"].valor is None  # sin OT en el mes: denominador cero, no un 0 %


@pytest.mark.parametrize("valor,obj,li,ls,mayor,esperado", [
    (None, 0.2, None, None, True, "GRIS"),
    (0.25, None, None, None, True, "GRIS"),
    (0.25, 0.20, 0.10, None, True, "VERDE"),
    (0.15, 0.20, 0.10, None, True, "AMARILLO"),
    (0.05, 0.20, 0.10, None, True, "ROJO"),
    (0.02, 0.03, None, 0.05, False, "VERDE"),
    (0.04, 0.03, None, 0.05, False, "AMARILLO"),
    (0.06, 0.03, None, 0.05, False, "ROJO"),
])
def test_color(valor, obj, li, ls, mayor, esperado):
    assert T.color(valor, obj, li, ls, mayor) == esperado


def test_objetivos(mes):
    with mes.escritura() as s:
        T.cargar_dato(s, MES, "HHDP", 160)
        T.fijar_objetivo(s, "TBMC", 0.20, None, 0.30)
        with pytest.raises(ValueError):
            T.fijar_objetivo(s, "TBMC", 0.2, 0.5, 0.1)
    assert _valores(mes)["TBMC"].color == "AMARILLO"  # 25 %: dentro del límite pero peor que el objetivo


def test_cit(mes):
    with mes.escritura() as s:
        P.fijar(s, "costos.margen_linea_ars_h", 600_000, date(2026, 1, 1))
        c = T.cit(s, MES, TZ)
        assert c.total is None and c.faltan == [T.VARIABLES["CFN"][0]]  # los financieros se cargan a mano
        T.cargar_dato(s, MES, "CFN", 50_000)
        c = T.cit(s, MES, TZ)
    # CFJ = preventivo 100.000; CV = correctivo 500.000; CFA = 5 h de parada × $600.000 (sin pulmón).
    assert c.cfj == (100_000, "sistema") and c.cv == (500_000, "sistema") and c.cfa == (3_000_000, "sistema")
    assert c.total == pytest.approx(3_650_000)


def test_tablero_completo(mes):
    with mes.escritura() as s:
        for clave, valor in (("CPROD", 12_000_000), ("VIB", 150_000_000), ("HHDP", 160), ("HHEI", 8), ("EMMM", 4),
                             ("NOTR", 0), ("NODV", 1), ("HHEF", 640), ("HHAF", 64)):
            T.cargar_dato(s, MES, clave, valor)
        v = {x.codigo: x for x in T.tablero(s, MES, TZ, completo=True)}
    assert v["CMOE"].valor == pytest.approx(100_000 / 600_000)
    assert v["CMPP"].valor == pytest.approx(600_000 / 12_000_000)
    assert v["CMPV"].valor == pytest.approx(600_000 / 150_000_000)
    assert v["TBML"].valor == 0  # sin OT de mantenimiento autónomo
    assert v["PETI"].valor == pytest.approx(8 / 160)
    assert v["CSMP"].valor == pytest.approx(4 / 5)
    assert v["EFMD"].valor == pytest.approx(0.9) and "Ausentismo" in v["EFMD"].notas[0]
    assert "CMOE" not in {x.codigo for x in _valores(mes).values()}  # el básico no los muestra


def test_disponibilidad_mensual(mes):
    with mes.lectura() as s:
        serie = T.serie(s, "DISP", ["2026-02", MES], TZ)
    assert serie[0][1] is None and serie[1][1] == pytest.approx(1.0)  # todos los partes sin paradas
