"""Weibull bayesiano: con previa débil se acerca a los datos; con previa fuerte y una falla, a Weibayes."""

import pytest

from circularis_rel.motor import bayes
from circularis_rel.motor import weibull as W
from circularis_rel.motor.tipos import Observacion as O

PLAN15 = [O(300, "S"), O(410, "F"), O(560, "F"), O(650, "S"), O(690, "F"), O(780, "F"), O(920, "F")]


def test_previa_debil_sigue_a_los_datos():
    b = bayes.ajustar(PLAN15, beta_previa=1.0, sd_log=5.0)
    beta_mle, eta_mle, _ll = W.mle(PLAN15)
    # La mediana posterior queda entre el MLE con corrección RBA (≈ 3,96) y el MLE (4,75), lejos de la previa (1).
    assert 3.0 < b.beta < beta_mle and b.eta == pytest.approx(eta_mle, rel=0.05)
    assert b.beta_ic[0] < b.beta < b.beta_ic[1] and b.eta_ic[0] < b.eta < b.eta_ic[1]


def test_previa_fuerte_con_una_falla_se_parece_a_weibayes():
    obs = [O(1200, "F"), O(800, "S")]
    b = bayes.ajustar(obs, beta_previa=2.5, sd_log=0.05)
    eta_wb, _ic = W.weibayes(obs, 2.5, 0.9)
    assert b.beta == pytest.approx(2.5, rel=0.03)
    assert b.eta == pytest.approx(eta_wb, rel=0.15)  # mediana posterior contra el estimador de Weibayes


def test_mas_datos_achican_el_intervalo():
    pocos = bayes.ajustar(PLAN15[:4], beta_previa=3.0, sd_log=0.5)
    todos = bayes.ajustar(PLAN15, beta_previa=3.0, sd_log=0.5)
    assert (todos.eta_ic[1] - todos.eta_ic[0]) < (pocos.eta_ic[1] - pocos.eta_ic[0])


def test_censura_por_intervalo_y_errores():
    b = bayes.ajustar([O(500, "I", edad_inf=400), O(700, "F"), O(300, "S")], 2.0, 0.35)
    assert b.n_fallas == 2 and b.n_suspensiones == 1
    with pytest.raises(ValueError):
        bayes.ajustar([O(300, "S")], 2.0, 0.35)
    with pytest.raises(ValueError):
        bayes.ajustar(PLAN15, 0, 0.35)
