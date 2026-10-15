"""Tendencia del predictivo y clasificación del ultrasonido (UNIDAD 3)."""

import pytest

from circularis_rel.motor import tendencia

TABLA = [{"desde_db": 8, "estado": "Pre-falla"}, {"desde_db": 10, "estado": "Primeros síntomas"},
         {"desde_db": 16, "estado": "Falla"}, {"desde_db": 35, "estado": "Catastrófica"}]


def test_recta_y_dias_hasta_el_limite():
    t = tendencia.ajustar([0, 10, 20, 30], [1.0, 2.0, 3.0, 4.0], limite=6.0)
    assert t.pendiente_por_dia == pytest.approx(0.1) and t.r2 == pytest.approx(1.0)
    assert t.dias_hasta_limite == pytest.approx(20.0)


def test_sin_tendencia_hacia_el_limite():
    assert tendencia.ajustar([0, 10, 20], [5.0, 4.0, 3.0], limite=6.0).dias_hasta_limite is None
    # Parámetro que empeora al bajar.
    assert tendencia.ajustar([0, 10, 20], [5.0, 4.0, 3.0], limite=1.0, creciente=False).dias_hasta_limite == pytest.approx(20.0)


def test_pocos_puntos():
    assert tendencia.ajustar([0, 1], [1, 2], 3) is None
    assert tendencia.ajustar([0, 0, 0], [1, 2, 3], 3) is None


@pytest.mark.parametrize("delta,estado", [(5, None), (8, "Pre-falla"), (11, "Primeros síntomas"), (16, "Falla"),
                                          (40, "Catastrófica")])
def test_ultrasonido(delta, estado):
    fila = tendencia.clasificar_ultrasonido(delta, TABLA)
    assert (fila["estado"] if fila else None) == estado
