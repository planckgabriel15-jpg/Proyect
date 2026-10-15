"""Integración base ↔ motor: el caso del Plan §15 armado con vidas y partes reales."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from circularis_rel.datos.enums import EstadoParte, MetodoWeibull, Semaforo, TipoFin
from circularis_rel.datos.modelos import (
    Activo,
    ActivoTurno,
    EstadoComponente,
    ParteTurno,
    PosicionComponente,
    PrecioRepuesto,
    RecalculoPendiente,
    Repuesto,
    ResultadoWeibull,
    TipoCambio,
    TipoComponente,
    Turno,
    VidaComponente,
)
from circularis_rel.motor import kpis
from circularis_rel.servicios import costos, kpis_planta, recalculo
from circularis_rel.servicios import parametros as P

TZ = ZoneInfo("America/Argentina/Cordoba")
INICIO = datetime(2025, 1, 1, tzinfo=TZ)
EDADES = [(300, "S"), (410, "F"), (560, "F"), (650, "S"), (690, "F"), (780, "F"), (920, "F")]


@pytest.fixture
def plan15(db, planta):
    """Turno de 24 h todos los días: la edad en horas es el tiempo transcurrido."""
    with db.escritura() as s:
        t24 = Turno(codigo="DEMO-24", nombre="Continuo", hora_inicio=time(0), hora_fin=time(0), duracion_h=24)
        s.add(t24)
        s.flush()
        s.add(ActivoTurno(id_activo=planta.activo, id_turno=t24.id, dias="1,2,3,4,5,6,7"))
        momento = INICIO
        for edad, estado in EDADES:
            fin = momento + timedelta(hours=edad)
            s.add(VidaComponente(id_posicion=planta.posicion, fecha_instalacion=momento, fecha_fin=fin,
                                 tipo_fin=TipoFin.FALLA if estado == "F" else TipoFin.SUSPENSION_PREVENTIVA,
                                 id_modo_falla=planta.modo if estado == "F" else None, validado=True))
            momento = fin
        actual = momento
        s.add(VidaComponente(id_posicion=planta.posicion, fecha_instalacion=actual))
        hoy = (actual + timedelta(hours=520)).date()
        d = INICIO.date()
        while d <= hoy + timedelta(days=1):
            s.add(ParteTurno(id_activo=planta.activo, fecha=d, id_turno=t24.id, horas_turno=24, estado=EstadoParte.TODO,
                             horas_no_operadas=0, horas_operadas=24))
            d += timedelta(days=1)
        corte = actual + timedelta(hours=520)
    return {"actual": actual, "corte": corte, "turno": t24}


def test_recalculo_del_par_reproduce_el_caso_2(db, planta, plan15, monkeypatch):
    monkeypatch.setattr(recalculo, "ahora", lambda: plan15["corte"].astimezone(UTC))
    monkeypatch.setattr("circularis_rel.servicios.vidas.ahora", lambda: plan15["corte"].astimezone(UTC))
    with db.escritura() as s:
        r = recalculo.recalcular_par(s, planta.tipo, planta.modo, planta.activo, TZ)
        rid = r.id
    with db.lectura() as s:
        r = s.get(ResultadoWeibull, rid)
        # La vida en servicio (520 h) entra como suspensión (D-002): caso 2
        assert r.metodo == MetodoWeibull.RRX and r.vigente
        assert (r.n_fallas, r.n_suspensiones) == (5, 3)
        assert r.beta == pytest.approx(3.582, abs=0.003) and r.eta == pytest.approx(781.3, abs=0.3)
        assert r.version_motor and len(r.hash_datos) == 64 and r.metodo_ic == "BOOTSTRAP"
        alternativa = s.scalar(select(ResultadoWeibull).where(ResultadoWeibull.vigente.is_(False)))
        assert alternativa.metodo == MetodoWeibull.MLE_RBA
    with db.escritura() as s:  # recalcular sin cambios no duplica filas
        recalculo.recalcular_par(s, planta.tipo, planta.modo, planta.activo, TZ)
    with db.lectura() as s:
        assert len(s.scalars(select(ResultadoWeibull)).all()) == 2


def test_estado_del_componente(db, planta, plan15, monkeypatch):
    monkeypatch.setattr(recalculo, "ahora", lambda: plan15["corte"].astimezone(UTC))
    monkeypatch.setattr("circularis_rel.servicios.vidas.ahora", lambda: plan15["corte"].astimezone(UTC))
    hoy = plan15["corte"].date()
    with db.escritura() as s:
        P.fijar(s, "semaforo.horizonte_dias_defecto", 7, date.today())
        r = recalculo.recalcular_par(s, planta.tipo, planta.modo, planta.activo, TZ)
        pos = s.get(PosicionComponente, planta.posicion)
        est = recalculo.actualizar_estado(s, pos, TZ, hoy)
        assert est.edad == pytest.approx(520, abs=0.01)
        assert est.delta == pytest.approx(7 * 24)  # ritmo real 24 h/día × 7 días
        assert est.p_falla_delta == pytest.approx(kpis.prob_condicional(520, 168, r.beta, r.eta), rel=1e-9)
        assert est.p_falla_delta_inf <= est.p_falla_delta <= est.p_falla_delta_sup
        assert est.semaforo == Semaforo.ROJO and est.confianza == "BAJA"
        assert est.vida_rem_mediana == pytest.approx(kpis.vida_remanente(520, 0.5, r.beta, r.eta), rel=1e-4)


def test_cola_de_recalculo(db, planta, plan15):
    with db.escritura() as s:
        s.add(RecalculoPendiente(id_tipo_componente=planta.tipo, id_modo=planta.modo, id_activo=planta.activo))
    with db.escritura() as s:
        assert recalculo.procesar_cola(s, TZ) == 1
    with db.lectura() as s:
        item = s.scalar(select(RecalculoPendiente))
        assert item.terminado_en is not None and item.error is None
        assert s.scalar(select(EstadoComponente).where(EstadoComponente.id_posicion == planta.posicion)) is not None


def test_forzar_metodo_exige_justificacion(db, planta, plan15):
    with pytest.raises(ValueError, match="justificación"), db.escritura() as s:
        recalculo.recalcular_par(s, planta.tipo, planta.modo, planta.activo, TZ, forzar="MLE", justificacion="")
    with db.escritura() as s:
        r = recalculo.recalcular_par(s, planta.tipo, planta.modo, planta.activo, TZ, forzar="MLE",
                                     justificacion="Comparar con el control")
        assert r.forzado and r.metodo == MetodoWeibull.MLE_RBA
    with db.escritura() as s:  # el forzado se respeta en los recálculos siguientes
        assert recalculo.recalcular_par(s, planta.tipo, planta.modo, planta.activo, TZ).metodo == MetodoWeibull.MLE_RBA


def test_costos_de_decision(db, planta):
    with db.escritura() as s:
        tipo = s.get(TipoComponente, planta.tipo)
        tipo.hh_preventiva, tipo.hh_correctiva = 2, 4
        s.get(Activo, planta.activo).autonomia_pulmon_h = 1
        rep = Repuesto(codigo="DEMO-RC", descripcion="Cuchillas", id_tipo_componente=planta.tipo)
        s.add(rep)
        s.flush()
        s.add(PrecioRepuesto(id_repuesto=rep.id, fecha=date(2026, 1, 1), precio=100, moneda="USD"))
        s.add(TipoCambio(fecha=date(2026, 1, 1), ars_por_usd=1000))
        c = costos.costos_decision(s, planta.tipo, planta.modo, planta.activo, date(2026, 2, 1))
        assert not c.completo and "tarifa de mano de obra" in c.faltan
        P.fijar(s, "costos.tarifa_mo_ars_h", 10000, date(2026, 1, 1))
        P.fijar(s, "costos.margen_linea_ars_h", 50000, date(2026, 1, 1))
        P.fijar(s, "costos.horas_parada_defecto_h", 5, date(2026, 1, 1))
        c = costos.costos_decision(s, planta.tipo, planta.modo, planta.activo, date(2026, 2, 1))
    assert c.cp == 100_000 + 2 * 10_000
    assert c.cf == 100_000 + 4 * 10_000 + (5 - 1) * 50_000


def test_kpis_de_planta(db, planta, plan15):
    with db.lectura() as s:
        k = kpis_planta.kpis_maquina(s, planta.activo, INICIO.date(), INICIO.date() + timedelta(days=9), TZ)
    assert k.horas_turno == 240 and k.horas_operadas == 240 and k.ao == 1.0 and k.n_fallas == 0 and k.mtbf is None
