"""Máquina completa como sistema reparable (Plan §5): Crow-AMSAA y prueba de tendencia de Laplace.

Crow-AMSAA (modelo de potencia, terminación por tiempo T): β̂ = n / Σ ln(T/tᵢ), λ̂ = n / T^β̂.
β < 1: la máquina mejora; β > 1: se degrada. IEC 61710 (citada en el Plan §17).
Laplace: U = [Σtᵢ/n − T/2] / [T·√(1/(12n))] ~ N(0, 1) sin tendencia; U > 0 degradación.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy import stats


@dataclass(frozen=True)
class CrowAMSAA:
    beta: float
    lam: float
    beta_ic: tuple[float, float]
    n: int
    T: float

    def fallas_esperadas(self, t: float) -> float:
        return self.lam * t**self.beta

    def mtbf_instantaneo(self, t: float) -> float:
        return 1 / (self.lam * self.beta * t ** (self.beta - 1))


def crow_amsaa(tiempos_falla: list[float], T: float, nivel: float = 0.90) -> CrowAMSAA:
    """`tiempos_falla`: horas operadas acumuladas de la máquina en cada falla; `T`: horas al cierre."""
    t = sorted(x for x in tiempos_falla if x > 0)
    n = len(t)
    if n < 2:
        raise ValueError("Crow-AMSAA necesita al menos 2 fallas")
    if T < t[-1]:  # noqa: SIM300
        raise ValueError("T tiene que ser mayor o igual que la última falla")
    suma = sum(math.log(T / x) for x in t)
    if suma <= 0:
        raise ValueError("Todas las fallas coinciden con el final del período")
    beta = n / suma
    lam = n / T**beta
    a = (1 - nivel) / 2  # IC exacto con terminación por tiempo: 2nβ/β̂ ~ χ²(2n)
    ic = (beta * stats.chi2.ppf(a, 2 * n) / (2 * n), beta * stats.chi2.ppf(1 - a, 2 * n) / (2 * n))
    return CrowAMSAA(beta, lam, ic, n, T)


def laplace(tiempos_falla: list[float], T: float) -> tuple[float, float]:
    """(U, p-valor bilateral)."""
    n = len(tiempos_falla)
    if n < 1 or T <= 0:
        raise ValueError("Laplace necesita al menos una falla y T > 0")
    u = (sum(tiempos_falla) / n - T / 2) / (T * math.sqrt(1 / (12 * n)))
    return u, float(2 * stats.norm.sf(abs(u)))
