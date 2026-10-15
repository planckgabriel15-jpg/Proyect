"""Sección 13, caso 10: KPIs contra un escenario calculado a mano (igualdad exacta)."""

import pytest

from circularis_rel.motor import kpis

# Escenario a mano (planilla): una máquina en un mes.
#   Partes: 22 turnos de 8 h = 176 h de turno; 8 h sin demanda (no requeridas) → 168 h requeridas.
#   Paradas: 6 h por falla + 2 h de limpieza = 8 h paradas → 160 h operadas.
#   Fallas: 2, con reparación activa 2 h y 3 h, y paradas (con espera) 2,5 h y 3,5 h.
#   Costo de fallas: repuestos 100 + 50, MO 5 h × 20 = 100, lucro cesante 6 h × 30 = 180 → 430.


def test_escenario_a_mano():
    assert kpis.mtbf(160, 2) == 80
    assert kpis.mttr([2, 3]) == 2.5
    assert kpis.mttr_total([2.5, 3.5], 2) == 3.0
    assert kpis.disponibilidad_inherente(80, 2.5) == 80 / 82.5
    assert kpis.disponibilidad_operacional(168, 8) == 160 / 168
    assert 100 + 50 + 5 * 20 + 6 * 30 == 430


def test_sin_datos_no_inventa_ceros():
    assert kpis.mtbf(160, 0) is None
    assert kpis.mttr([]) is None
    assert kpis.disponibilidad_inherente(None, 2) is None
    assert kpis.disponibilidad_operacional(0, 0) is None
    assert kpis.oee(0.9, None, 0.99) is None


def test_sistemas_serie_paralelo_mixta():
    assert kpis.serie([0.9, 0.8]) == pytest.approx(0.72)
    assert kpis.paralelo([0.9, 0.8]) == pytest.approx(0.98)
    assert kpis.mixta(("serie", [0.95, ("paralelo", [0.9, 0.9])])) == pytest.approx(0.95 * 0.99)


def test_modos_combinados():
    p1 = kpis.prob_condicional(100, 50, 2, 300)
    p2 = kpis.prob_condicional(100, 50, 1, 1000)
    assert kpis.prob_condicional_combinada(100, 50, [(2, 300, 0), (1, 1000, 0)]) == pytest.approx(1 - (1 - p1) * (1 - p2))
