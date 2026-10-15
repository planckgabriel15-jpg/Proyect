"""Sección 13, casos 1 y 2: ejemplo del Plan §15 (cuchillas AGR-001). Valores publicados; no se ajustan."""

import pytest

from circularis_rel.motor import kpis, politicas, semaforo
from circularis_rel.motor import weibull as W
from circularis_rel.motor.tipos import Observacion as O
from tests.motor.conftest import PLAN15

pytestmark = pytest.mark.referencia


@pytest.fixture(scope="module")
def ajuste():
    return W.ajustar(PLAN15 + [O(520, "S", solo_pronostico=True)])


def test_metodo_rrx_y_rangos(ajuste):
    v = ajuste.vigente
    assert v.metodo == "RRX"
    assert [round(r[1], 2) for r in v.rangos] == [1.14, 2.29, 3.71, 5.14, 6.57]
    assert [round(100 * r[2], 1) for r in v.rangos] == [11.4, 26.8, 46.1, 65.4, 84.7]


def test_beta_eta_r2(ajuste):
    v = ajuste.vigente
    assert v.beta == pytest.approx(3.42, rel=0.01)
    assert v.eta == pytest.approx(774, rel=0.01)
    assert v.r2 == pytest.approx(0.996, abs=0.0005)
    assert v.r2 > v.r2_critico  # "muy por encima del valor crítico para 5 fallas"
    assert (v.n_fallas, v.n_suspensiones) == (5, 2)


def test_mle_de_control(ajuste):
    a = ajuste.alternativa
    assert a.beta_mle_sin_corregir == pytest.approx(4.75, rel=0.01)
    import circularis_rel.motor.weibull as w
    beta, eta, _ = w.mle(PLAN15)
    assert eta == pytest.approx(761, rel=0.01)


def test_ic_publicado_es_fisher_y_el_sistema_usa_razon_de_verosimilitud(ajuste):
    """D-004: el IC del §15 (2,7–8,4; 650–890) es de matriz de Fisher. El sistema usa LR."""
    beta, eta, _ = W.mle(PLAN15)
    (bf, bF), (ef, eF) = W.ic_fisher(PLAN15, beta, eta, 0.90)
    assert (round(bf, 1), round(bF, 1)) == (2.7, 8.4)
    assert (round(ef, -1), round(eF, -1)) == (650, 890)
    a = ajuste.alternativa
    assert a.metodo_ic == "LR"
    assert a.beta_ic == pytest.approx((2.47, 7.89), rel=0.01)
    assert a.eta_ic == pytest.approx((638, 924), rel=0.01)


def test_kpis_del_componente(ajuste):
    b, e = ajuste.vigente.beta, ajuste.vigente.eta
    assert kpis.mttf(b, e) == pytest.approx(696, rel=0.005)
    assert kpis.vida_b(0.10, b, e) == pytest.approx(401, rel=0.005)
    assert kpis.confiabilidad(520, b, e) == pytest.approx(0.774, abs=0.001)
    for delta, p in ((80, 0.149), (160, 0.320), (240, 0.494)):
        assert kpis.prob_condicional(520, delta, b, e) == pytest.approx(p, abs=0.001)
    assert kpis.vida_remanente(520, 0.5, b, e) == pytest.approx(243, abs=1)
    assert kpis.vida_remanente(520, 0.9, b, e) == pytest.approx(55, abs=1)


def test_politica_de_costos(ajuste):
    b, e = ajuste.vigente.beta, ajuste.vigente.eta
    cp, cf = 400, 2500
    for T, c in ((300, 1.62), (350, 1.55), (400, 1.56), (450, 1.62), (500, 1.73)):
        assert politicas.costo_por_hora(T, cp, cf, b, e) == pytest.approx(c, abs=0.006)
    t_opt, c_opt = politicas.intervalo_optimo(cp, cf, b, e)
    assert t_opt == pytest.approx(370, rel=0.01) and c_opt == pytest.approx(1.54, abs=0.005)
    assert politicas.costo_hasta_falla(cf, b, e) == pytest.approx(3.59, abs=0.005)
    # curva plana entre 350 y 400 h: menos de 1 % por encima del óptimo
    assert politicas.costo_por_hora(350, cp, cf, b, e) / c_opt < 1.01
    assert politicas.costo_por_hora(400, cp, cf, b, e) / c_opt < 1.01
    rec = politicas.recomendar(b, e, cp=cp, cf=cf, critico=False, seguridad=False, intervalo_pf=None, r_objetivo=0.9,
                               cf_cp_minimo=2, paso_redondeo=25, interpretacion="DESGASTE")
    assert rec.regla == "OPTIMO_COSTO" and rec.intervalo == 375
    assert rec.ahorro == pytest.approx(0.57, abs=0.01)  # "ahorro de ~57 % del costo por hora"


def test_semaforo_rojo_con_confianza_baja(ajuste):
    """P(160 h) = 32 % ≥ 30 % y edad 520 h > 375 h → rojo. Confianza BAJA con 5 fallas (P-08)."""
    v = ajuste.vigente
    p = kpis.prob_condicional(520, 160, v.beta, v.eta)
    c = semaforo.color_componente(p, 520, 375, False, v.confianza, "B", delta=160)
    assert c.color == "ROJO" and len(c.motivos) == 2
    assert v.confianza == "BAJA" and not c.duro
    assert ajuste.vigente.interpretacion == "DESGASTE"


def test_kpis_de_la_maquina():
    """4.310 h operadas, 8 fallas, 36 h de reparación."""
    m = kpis.mtbf(4310, 8)
    r = kpis.mttr([4.5] * 8)
    assert m == pytest.approx(538.75) and r == 4.5
    assert kpis.disponibilidad_inherente(m, r) == pytest.approx(0.992, abs=0.0005)
    assert pytest.approx(800) == 0.32 * 2500  # costo esperado en el horizonte (ranking)


def test_caso2_vida_en_servicio_como_suspension():
    """D-002: incluir la suspensión de 520 h no puede bajar η."""
    sin = W.ajustar(PLAN15, W.sin_ic(W.Configuracion())).vigente
    con = W.ajustar(PLAN15 + [O(520, "S")], W.sin_ic(W.Configuracion())).vigente
    assert con.eta >= sin.eta
    assert con.beta == pytest.approx(3.582, abs=0.002) and con.eta == pytest.approx(781.3, abs=0.2)
    assert W.mle(PLAN15 + [O(520, "S")])[1] >= W.mle(PLAN15)[1]
