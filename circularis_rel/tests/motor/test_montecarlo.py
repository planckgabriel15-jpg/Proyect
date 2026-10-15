"""Sección 13, caso 8: Monte Carlo. Cobertura del IC al 90 % y sesgo (RBA).

Réplicas configurables con la variable MC_REPLICAS (por defecto, rápido para CI). La versión exhaustiva
corre con `pytest -m lento`.
"""

import math
import os

import numpy as np
import pytest

from circularis_rel.motor import weibull as W
from circularis_rel.motor.tipos import Observacion as O

REPLICAS = int(os.environ.get("MC_REPLICAS", "150"))


def _muestra(rng, beta, eta, n, frac_censura):
    t = eta * rng.weibull(beta, n)
    if frac_censura == 0:
        return [O(float(x), "F") for x in t]
    # censura tipo I a la edad que deja aproximadamente esa fracción sin fallar
    corte = eta * (-math.log(frac_censura)) ** (1 / beta)
    return [O(float(min(x, corte)), "F" if x <= corte else "S") for x in t]


def _cobertura(beta, eta, n, frac, replicas, semilla):
    rng = np.random.default_rng(semilla)
    dentro = total = 0
    for _ in range(replicas):
        obs = _muestra(rng, beta, eta, n, frac)
        if sum(o.estado == "F" for o in obs) < 3:
            continue
        b, e, _ = W.mle(obs)
        (bi, bs), _eta_ic = W.ic_razon_verosimilitud(obs, b, e, 0.90)
        dentro += bi <= beta <= bs
        total += 1
    return dentro / total, total


def _tolerancia(total):
    # banda binomial de ±3 desvíos alrededor de 0,90 (con muchas réplicas queda en ~0,86–0,94)
    return 3 * math.sqrt(0.9 * 0.1 / total)


@pytest.mark.parametrize("beta,n,frac", [(2.0, 10, 0.0), (3.5, 15, 0.3)])
def test_cobertura_ic_razon_verosimilitud(beta, n, frac):
    cob, total = _cobertura(beta, 100.0, n, frac, REPLICAS, 123)
    assert abs(cob - 0.90) <= max(_tolerancia(total), 0.04), f"cobertura {cob:.3f} con {total} réplicas"


def test_rba_reduce_el_sesgo_de_beta():
    """Con muestras chicas el MLE sobreestima β; la corrección RBA la acerca al valor real."""
    rng = np.random.default_rng(5)
    beta_real, n = 2.5, 6
    mle_b, rba_b = [], []
    for _ in range(max(REPLICAS * 2, 300)):
        obs = _muestra(rng, beta_real, 100, n, 0.0)
        b, _e, _ = W.mle(obs)
        mle_b.append(b)
        rba_b.append(b * W.factor_rba(n))
    assert np.median(mle_b) > beta_real
    assert abs(np.median(rba_b) - beta_real) < abs(np.median(mle_b) - beta_real)


@pytest.mark.lento
@pytest.mark.parametrize("beta", [0.7, 1.0, 2.0, 3.5, 6.0])
@pytest.mark.parametrize("n", [5, 10, 20, 50])
@pytest.mark.parametrize("frac", [0.0, 0.3, 0.6])
def test_cobertura_exhaustiva(beta, n, frac):
    """Con ≥ 10 fallas la cobertura queda en 86–94 %. Con 5 fallas el IC por razón de verosimilitud
    (asintótico) cubre ~83–86 %: hallazgo documentado en D-034 (en ese rango el vigente es RRX y la
    etiqueta ya dice "confianza baja")."""
    cob, total = _cobertura(beta, 100.0, n, frac, max(REPLICAS, 2000), 99)
    if n < 10:
        assert cob >= 0.80, f"{cob:.3f} ({total})"
    else:
        assert 0.86 <= cob <= 0.94 or abs(cob - 0.9) <= _tolerancia(total), f"{cob:.3f} ({total})"
