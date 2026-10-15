import pytest

from circularis_rel.motor.tipos import Observacion as O

# Plan §15 (datos ficticios): vida 1 a 7; la vida 8 (520 h, en servicio) es solo para el pronóstico.
PLAN15 = [O(300, "S"), O(410, "F"), O(560, "F"), O(650, "S"), O(690, "F"), O(780, "F"), O(920, "F")]
U2 = [O(t, "F") for t in (93, 34, 16, 120, 53, 75)]


@pytest.fixture
def plan15():
    return list(PLAN15)
