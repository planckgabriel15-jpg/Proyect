"""Panel (fase 1c) sobre la historia DEMO: semáforos, ranking, Pareto, tendencia, sugerencias y borrado."""

from datetime import date, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select

from circularis_rel.asistente import rca
from circularis_rel.datos.db import BaseDatos
from circularis_rel.datos.enums import OrigenAnalisis
from circularis_rel.datos.modelos import (
    Activo,
    EventoFalla,
    ParteTurno,
    PosicionComponente,
    ResultadoWeibull,
    TipoComponente,
    Usuario,
)
from circularis_rel.datos.semillas import sembrar
from circularis_rel.servicios import panel, recalculo
from circularis_rel.servicios.demo import borrar_demo, cargar_demo, hay_demo

TZ = ZoneInfo("America/Argentina/Cordoba")


@pytest.fixture(scope="module")
def demo() -> BaseDatos:
    db = BaseDatos("sqlite://")
    db.crear_esquema()
    with db.escritura() as s:
        sembrar(s)
    assert cargar_demo(db, tz=TZ).aplicado
    return db


def _hoy() -> date:
    from circularis_rel.datos.db import ahora

    return ahora().astimezone(TZ).date()


def test_estado_de_las_maquinas(demo):
    with demo.lectura() as s:
        maquinas = {m.codigo: m for m in panel.estado_maquinas(s)}
    assert list(maquinas) == ["DEMO-AGR-001", "DEMO-LAV-001", "DEMO-EXT-001"]  # orden de proceso
    agr = maquinas["DEMO-AGR-001"]
    cuchillas = next(c for c in agr.componentes if c.codigo == "CUCHILLAS")
    assert cuchillas.color == "ROJO" and agr.color == "ROJO"  # la máquina toma el peor de sus críticos
    assert cuchillas.p is not None and cuchillas.p_inf <= cuchillas.p <= cuchillas.p_sup
    valvula = next(c for c in maquinas["DEMO-EXT-001"].componentes if c.codigo == "VALV-SEG")
    assert valvula.color == "GRIS" and any("Edad desconocida" in m for m in valvula.motivos)


def test_aviso_abierto_pone_la_maquina_en_rojo(demo):
    with demo.escritura() as s:
        lav = s.scalar(select(Activo).where(Activo.codigo == "DEMO-LAV-001"))
        s.add(EventoFalla(id_activo=lav.id, fecha_hora_falla=panel._rango(_hoy(), _hoy(), TZ)[0]))
        s.flush()
        m = panel.estado_maquina(s, lav)
        assert m.color == "ROJO" and m.avisos_abiertos == 1 and "aviso" in m.motivos[0]
        s.rollback()


def test_ranking_de_riesgo_ordenado(demo):
    with demo.lectura() as s:
        filas = panel.ranking_riesgo(s, _hoy())
    assert filas and all(f.riesgo is not None for f in filas)  # la demo trae costos ficticios
    riesgos = [f.riesgo for f in filas]
    assert riesgos == sorted(riesgos, reverse=True)
    assert all(f.riesgo == pytest.approx(f.p * f.cf) for f in filas)


@pytest.mark.parametrize("criterio", ["frecuencia", "horas", "costo"])
def test_pareto(demo, criterio):
    hoy = _hoy()
    with demo.lectura() as s:
        filas = panel.pareto(s, hoy - timedelta(days=1000), hoy, TZ, criterio)
        total_eventos = s.scalar(select(func.count()).select_from(EventoFalla))
    assert sum(f.n for f in filas) == total_eventos
    valores = [f.valor for f in filas]
    assert valores == sorted(valores, reverse=True)
    assert filas[-1].acumulado == pytest.approx(1.0)
    assert filas[0].dentro_corte
    # Cada barra "a atacar" empieza antes del corte (80 %).
    anterior = 0.0
    for f in filas:
        assert f.dentro_corte == (anterior < 0.80)
        anterior = f.acumulado


def test_pareto_criterio_invalido(demo):
    with demo.lectura() as s, pytest.raises(ValueError):
        panel.pareto(s, _hoy(), _hoy(), TZ, "otro")


def test_tendencia_mensual(demo):
    hoy = _hoy()
    with demo.lectura() as s:
        filas = panel.tendencia_mensual(s, hoy - timedelta(days=1000), hoy, TZ)
        total_eventos = s.scalar(select(func.count()).select_from(EventoFalla))
        operadas = s.scalar(select(func.sum(ParteTurno.horas_operadas)))
    assert sum(f["fallas"] for f in filas) == total_eventos
    assert sum(f["horas_operadas"] for f in filas) == pytest.approx(operadas)
    for f in filas:
        if f["ao"] is not None:
            assert 0 <= f["ao"] <= 1
        if f["fallas"]:
            assert f["mtbf"] == pytest.approx(f["horas_operadas"] / f["fallas"])
            assert f["costo"] is not None and f["costo"] > 0


def test_linea_de_tiempo(demo):
    with demo.lectura() as s:
        agr = s.scalar(select(Activo.id).where(Activo.codigo == "DEMO-AGR-001"))
        historia = panel.linea_tiempo(s, agr, TZ)
    fechas = [h["fecha"] for h in historia]
    assert fechas == sorted(fechas, reverse=True)
    assert {h["tipo"] for h in historia} >= {"Falla", "Preventiva"}


def test_sugerencias_de_analisis(demo):
    hoy = _hoy()
    with demo.lectura() as s:
        sugerencias = panel.sugerencias_rca(s, hoy, TZ)
    origenes = {sg.origen for sg in sugerencias}
    assert OrigenAnalisis.SUGERIDO_PARETO in origenes
    # Los rulemanes de la agrumadora fallan al azar (β ≈ 1) con confianza media: análisis de causa raíz.
    beta = [sg for sg in sugerencias if any("azar" in m for m in sg.motivos)]
    assert [sg.etiqueta for sg in beta] == ["DEMO-AGR-001 · RULEMANES · Ruido y desgaste (DEMO)"]
    # Con un análisis abierto del par, deja de sugerirse.
    sg = beta[0]
    with demo.escritura() as s:
        jefe = s.scalar(select(Usuario.id).where(Usuario.usuario == "demo.jefe"))
        a = rca.crear(s, jefe, "Rulemanes", id_activo=sg.id_activo, id_tipo=sg.id_tipo, id_modo=sg.id_modo,
                      origen=sg.origen)
        assert all((x.id_activo, x.id_tipo, x.id_modo) != (sg.id_activo, sg.id_tipo, sg.id_modo)
                   for x in panel.sugerencias_rca(s, hoy, TZ))
        s.delete(a)


def test_rangos_para_el_grafico(demo):
    with demo.lectura() as s:
        r = s.scalar(select(ResultadoWeibull).join(TipoComponente, TipoComponente.id == ResultadoWeibull.id_tipo_componente)
                     .where(TipoComponente.codigo == "DEMO-CUCHILLAS", ResultadoWeibull.vigente.is_(True)))
        rangos = panel.rangos_par(s, r, TZ)
        assert len(rangos) == r.n_fallas
        assert not s.dirty  # leer no deja cambios pendientes
        costo = panel.analisis_costo(s, r, _hoy())
    assert costo.curva and costo.t_optimo and 0 < costo.ahorro < 1


def test_forzar_y_volver_a_automatico(demo):
    with demo.escritura(motivo="prueba") as s:
        r = s.scalar(select(ResultadoWeibull).join(TipoComponente, TipoComponente.id == ResultadoWeibull.id_tipo_componente)
                     .where(TipoComponente.codigo == "DEMO-CUCHILLAS", ResultadoWeibull.vigente.is_(True)))
        clave = (r.id_tipo_componente, r.id_modo, r.id_activo)
        f = recalculo.recalcular_par(s, *clave, TZ, forzar="MLE", justificacion="Prueba")
        assert f.forzado and f.metodo.value.startswith("MLE")  # con pocas fallas, MLE lleva RBA
        assert recalculo.recalcular_par(s, *clave, TZ).metodo == f.metodo  # el forzado se mantiene
        auto = recalculo.quitar_forzado(s, *clave, TZ)
        assert not auto.forzado and auto.metodo.value == "RRX"
        assert recalculo.recalcular_par(s, *clave, TZ).id == auto.id


def test_borrar_demo_con_historia():
    db = BaseDatos("sqlite://")
    db.crear_esquema()
    with db.escritura() as s:
        sembrar(s)
    assert cargar_demo(db, tz=TZ).aplicado
    with db.escritura() as s:
        jefe = s.scalar(select(Usuario.id).where(Usuario.usuario == "demo.jefe"))
        agr = s.scalar(select(Activo.id).where(Activo.codigo == "DEMO-AGR-001"))
        a = rca.crear(s, jefe, "Prueba", id_activo=agr)
        rca.guardar_porques(s, jefe, a.id, ["uno"], accion="Cambiar", responsable="Jefe")
        rca.convertir_en_ot(s, jefe, a.id)
    borrar_demo(db)
    with db.lectura() as s:
        assert not hay_demo(s)
        for modelo in (ParteTurno, EventoFalla, ResultadoWeibull, PosicionComponente):
            assert s.scalar(select(func.count()).select_from(modelo)) == 0
