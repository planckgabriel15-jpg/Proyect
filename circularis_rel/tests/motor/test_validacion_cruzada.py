"""Sección 13, casos 6 y 7: casos publicados y validación cruzada contra otras implementaciones."""

import warnings

import numpy as np
import pytest

from circularis_rel.motor import weibull as W
from circularis_rel.motor.tipos import Observacion as O
from tests.motor.conftest import PLAN15, U2

warnings.filterwarnings("ignore")


def _dataset_censurado():
    rng = np.random.default_rng(7)
    t = 500 * rng.weibull(2.2, 25)
    c = rng.uniform(200, 900, 25)
    return [O(float(min(a, b)), "F" if a <= b else "S") for a, b in zip(t, c, strict=True)]


DATASETS = {"plan15": PLAN15, "unidad2": U2, "censurado": _dataset_censurado()}


@pytest.mark.parametrize("nombre", list(DATASETS))
def test_mle_igual_a_reliability_surpyval_y_lifelines(nombre):
    import matplotlib

    matplotlib.use("Agg")
    import surpyval
    from lifelines import WeibullFitter
    from reliability.Fitters import Fit_Weibull_2P

    obs = DATASETS[nombre]
    beta, eta, _ = W.mle(obs)
    f = [o.edad for o in obs if o.estado == "F"]
    s = [o.edad for o in obs if o.estado == "S"] or None
    rel = Fit_Weibull_2P(failures=f, right_censored=s, method="MLE", show_probability_plot=False, print_results=False)
    assert rel.beta == pytest.approx(beta, rel=1e-3) and rel.alpha == pytest.approx(eta, rel=1e-3)
    x = np.array([o.edad for o in obs])
    c = np.array([0 if o.estado == "F" else 1 for o in obs])
    sp = surpyval.Weibull.fit(x, c)
    assert sp.params[1] == pytest.approx(beta, rel=1e-3) and sp.params[0] == pytest.approx(eta, rel=1e-3)
    lf = WeibullFitter().fit(x, event_observed=1 - c)
    assert lf.rho_ == pytest.approx(beta, rel=2e-3) and lf.lambda_ == pytest.approx(eta, rel=2e-3)


@pytest.mark.parametrize("nombre", list(DATASETS))
def test_rrx_igual_a_reliability(nombre):
    """RRX con rangos de Johnson y Benard: misma convención que `reliability` (method='RRX')."""
    import matplotlib

    matplotlib.use("Agg")
    from reliability.Fitters import Fit_Weibull_2P

    obs = DATASETS[nombre]
    beta, eta, _r2, _ = W.rrx(obs)
    f = [o.edad for o in obs if o.estado == "F"]
    s = [o.edad for o in obs if o.estado == "S"] or None
    rel = Fit_Weibull_2P(failures=f, right_censored=s, method="RRX", show_probability_plot=False, print_results=False)
    assert rel.beta == pytest.approx(beta, rel=1e-3) and rel.alpha == pytest.approx(eta, rel=1e-3)


def test_fisher_igual_a_reliability():
    import matplotlib

    matplotlib.use("Agg")
    from reliability.Fitters import Fit_Weibull_2P

    beta, eta, _ = W.mle(PLAN15)
    (bi, bs), (ei, es) = W.ic_fisher(PLAN15, beta, eta, 0.90)
    rel = Fit_Weibull_2P(failures=[410, 560, 690, 780, 920], right_censored=[300, 650], CI=0.9, method="MLE",
                         show_probability_plot=False, print_results=False)
    assert (bi, bs) == pytest.approx((rel.beta_lower, rel.beta_upper), rel=5e-3)
    assert (ei, es) == pytest.approx((rel.alpha_lower, rel.alpha_upper), rel=5e-3)


def test_censura_por_intervalo_igual_a_surpyval():
    import surpyval

    rng = np.random.default_rng(11)
    t = 300 * rng.weibull(2.0, 30)
    obs, xs, cs = [], [], []
    for v in t:
        if v < 150:
            obs.append(O(float(v), "F"))
            xs.append([float(v), float(v)])
            cs.append(0)
        else:
            a, b = float(np.floor(v / 50) * 50), float(np.floor(v / 50) * 50 + 50)
            obs.append(O(b, "I", edad_inf=a))
            xs.append([a, b])
            cs.append(2)
    beta, eta, _ = W.mle(obs)
    sp = surpyval.Weibull.fit(xl=[x[0] for x in xs], xr=[x[1] for x in xs])
    assert sp.params[1] == pytest.approx(beta, rel=5e-3) and sp.params[0] == pytest.approx(eta, rel=5e-3)


@pytest.mark.xfail(reason="Ejemplos resueltos de Abernethy (2006) e IEC 61649:2008: los textos no están disponibles "
                          "en el proyecto. No se inventan datos (pedido §13.6).", strict=True)
def test_casos_publicados_abernethy_iec():
    raise NotImplementedError("Cargar aquí los ejemplos cuando se consigan los textos")
