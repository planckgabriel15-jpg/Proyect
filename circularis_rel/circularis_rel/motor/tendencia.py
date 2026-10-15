"""Tendencia de un parámetro predictivo [12.G]: recta por mínimos cuadrados y extrapolación hasta el límite.

Sirve para estimar cuánto falta para que una medición (vibración, temperatura, dB de ultrasonido) llegue al
límite de acción. Es una extrapolación simple: vale mientras la degradación siga el mismo ritmo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Tendencia:
    pendiente_por_dia: float
    ordenada: float  # valor estimado en el día 0 (primera medición)
    r2: float | None
    dias_hasta_limite: float | None  # desde la última medición; None si no se acerca al límite
    valor_actual_estimado: float


def ajustar(dias: list[float], valores: list[float], limite: float | None, creciente: bool = True) -> Tendencia | None:
    """`dias` desde la primera medición. `creciente`: el parámetro empeora cuando sube (lo habitual)."""
    if len(dias) < 3 or len(set(dias)) < 2:
        return None
    x, y = np.asarray(dias, float), np.asarray(valores, float)
    pendiente, ordenada = np.polyfit(x, y, 1)
    ajuste = pendiente * x + ordenada
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(((y - ajuste) ** 2).sum()) / ss_tot if ss_tot > 0 else None
    actual = float(pendiente * x[-1] + ordenada)
    faltan = None
    if limite is not None:
        se_acerca = pendiente > 0 if creciente else pendiente < 0
        if (creciente and actual >= limite) or (not creciente and actual <= limite):
            faltan = 0.0
        elif se_acerca:
            faltan = float((limite - actual) / pendiente)
    return Tendencia(float(pendiente), float(ordenada), r2, faltan, actual)


def clasificar_ultrasonido(delta_db: float, tabla: list[dict]) -> dict | None:
    """Fila de la tabla de referencia (UNIDAD 3) para un aumento de `delta_db` sobre la línea base: la de mayor
    umbral alcanzado. La tabla es editable y no es una norma."""
    alcanzadas = [f for f in tabla if delta_db >= f["desde_db"]]
    return max(alcanzadas, key=lambda f: f["desde_db"]) if alcanzadas else None
