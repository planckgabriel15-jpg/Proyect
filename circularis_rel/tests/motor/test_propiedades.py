"""Sección 13, caso 12: propiedades con hypothesis."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from circularis_rel.motor import kpis
from circularis_rel.motor import weibull as W
from circularis_rel.motor.tipos import Observacion as O

betas = st.floats(0.3, 8)
etas = st.floats(1, 1e5)
tiempos = st.floats(0, 1e5)


@given(betas, etas, tiempos, tiempos)
def test_F_monotona_y_R_mas_F_igual_1(beta, eta, t1, t2):
    a, b = sorted((t1, t2))
    assert kpis.infiabilidad(a, beta, eta) <= kpis.infiabilidad(b, beta, eta) + 1e-12
    assert kpis.confiabilidad(a, beta, eta) + kpis.infiabilidad(a, beta, eta) == pytest.approx(1)


@given(betas, etas, tiempos, st.floats(0, 1e5))
def test_probabilidad_condicional_entre_0_y_1(beta, eta, a, delta):
    p = kpis.prob_condicional(a, delta, beta, eta)
    assert 0 <= p <= 1


@settings(max_examples=40, deadline=None)
@given(st.lists(st.floats(1, 1000), min_size=4, max_size=12, unique=True), st.floats(0.01, 1000))
def test_escalado_beta_invariante_y_eta_escala(tiempos_falla, k):
    """Si todas las edades se multiplican por k, β no cambia y η se multiplica por k (Plan §4)."""
    obs = [O(t, "F") for t in tiempos_falla]
    b1, e1, _ = W.rrx(obs)[:3]
    b2, e2, _ = W.rrx([O(t * k, "F") for t in tiempos_falla])[:3]
    assert b2 == pytest.approx(b1, rel=1e-6) and e2 == pytest.approx(e1 * k, rel=1e-6)
    m1 = W.mle(obs)
    m2 = W.mle([O(t * k, "F") for t in tiempos_falla])
    assert m2[0] == pytest.approx(m1[0], rel=1e-4) and m2[1] == pytest.approx(m1[1] * k, rel=1e-4)


@settings(max_examples=30, deadline=None)
@given(st.lists(st.floats(10, 1000), min_size=4, max_size=10, unique=True), st.floats(10, 2000))
def test_agregar_una_suspension_no_reduce_eta(tiempos_falla, susp):
    obs = [O(t, "F") for t in tiempos_falla]
    assert W.mle(obs + [O(susp, "S")])[1] >= W.mle(obs)[1] * (1 - 1e-6)
