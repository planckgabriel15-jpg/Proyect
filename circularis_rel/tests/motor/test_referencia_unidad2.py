"""Sección 13, casos 3 a 5: ejemplos de la UNIDAD 2 (Mgter. L. D. Torres)."""

import pytest

from circularis_rel.motor import kpis
from circularis_rel.motor import weibull as W
from tests.motor.conftest import U2

pytestmark = pytest.mark.referencia


def test_weibull_unidad2():
    """16, 34, 53, 75, 93, 120 h. Ajuste gráfico de la fuente: ±10 % en β y η, ±2 puntos en R(15)."""
    # La tabla de la diapositiva 34 son rangos medianos EXACTOS (beta); Benard los aproxima (B-015).
    publicados = [10.9, 26.4, 42.1, 57.9, 73.6, 89.1]
    assert [round(100 * W.rango_mediano_exacto(i, 6), 1) for i in range(1, 7)] == publicados
    rangos = W.rangos_johnson(U2)
    assert all(abs(100 * r[2] - p) < 0.25 for r, p in zip(rangos, publicados, strict=True))
    beta, eta, _r2, _ = W.rrx(U2)
    assert beta == pytest.approx(1.4, rel=0.10)
    assert eta == pytest.approx(76, rel=0.10)
    assert kpis.confiabilidad(15, beta, eta) == pytest.approx(0.902, abs=0.02)
    assert kpis.confiabilidad(15, 1.4, 76) == pytest.approx(0.902, abs=0.001)  # con los valores de la diapositiva
    assert kpis.confiabilidad(76, 1.4, 76) == pytest.approx(0.368, abs=0.001)  # en t = η queda el 36,8 %


def test_exponencial_valvulas():
    lam = kpis.tasa_exponencial(2, 50)
    assert lam == pytest.approx(0.04)
    assert 1 - kpis.confiabilidad_exponencial(1 / 3, lam) == pytest.approx(0.0132, abs=0.00005)
    assert kpis.confiabilidad_exponencial(1 / 2, lam) == pytest.approx(0.98, abs=0.0005)


def test_tabla_de_mortalidad_motores():
    filas, vida_media = kpis.tabla_mortalidad([7, 8, 9, 10, 11, 12], [18, 63, 53, 28, 12, 6], 180)
    assert vida_media == pytest.approx(8.84, abs=0.02)  # la diapositiva trunca a 8,83 (B-001)
    assert [round(f.F, 3) for f in filas] == [0.100, 0.450, 0.744, 0.900, 0.967, 1.000]
    assert [round(f.lam, 3) for f in filas] == [0.100, 0.389, 0.535, 0.609, 0.667, 1.000]
