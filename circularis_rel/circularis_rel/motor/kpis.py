"""Indicadores (Plan §6) y fiabilidad básica (UNIDAD 2).

Empíricos (desde el primer parte): MTBF, MTTR, MTTR total, Ai, Ao, OEE.
Con Weibull: R(t), F(t), h(t), MTTF, B10, probabilidad condicional, vida remanente.
También: tabla de mortalidad, modelo exponencial y configuraciones serie, paralelo y mixta.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Weibull
# ---------------------------------------------------------------------------


def confiabilidad(t: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    """R(t) = exp[−((t−γ)/η)^β]."""
    if t <= gamma:
        return 1.0
    return math.exp(-(((t - gamma) / eta) ** beta))


def infiabilidad(t: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    return -math.expm1(-(((t - gamma) / eta) ** beta)) if t > gamma else 0.0


def tasa_falla(t: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    """h(t) = (β/η)·((t−γ)/η)^(β−1)."""
    if t <= gamma:
        return 0.0 if beta > 1 else (math.inf if beta < 1 else 1 / eta)
    return (beta / eta) * ((t - gamma) / eta) ** (beta - 1)


def mttf(beta: float, eta: float, gamma: float = 0.0) -> float:
    """η·Γ(1 + 1/β) + γ."""
    return gamma + eta * math.gamma(1 + 1 / beta)


def vida_b(p: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    """Edad a la que falló la fracción p: B10 = η·(−ln 0,9)^(1/β) (UNIDAD 2, diap. 29)."""
    return gamma + eta * (-math.log(1 - p)) ** (1 / beta)


def vida_para_confiabilidad(r: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    """t = η·(ln(1/R))^(1/β) (UNIDAD 2, diap. 29)."""
    return vida_b(1 - r, beta, eta, gamma)


def prob_condicional(a: float, delta: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    """P(falla en Δ | edad a) = 1 − R(a+Δ)/R(a), calculada en escala log para no perder precisión."""
    if delta <= 0:
        return 0.0
    za = ((a - gamma) / eta) ** beta if a > gamma else 0.0
    zb = ((a + delta - gamma) / eta) ** beta if a + delta > gamma else 0.0
    return -math.expm1(-(zb - za))


def vida_remanente(a: float, q: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    """x tal que R(a+x)/R(a) = q (q = 0,5: mediana; q = 0,9: al 90 %)."""
    za = ((a - gamma) / eta) ** beta if a > gamma else 0.0
    return gamma + eta * (za - math.log(q)) ** (1 / beta) - a if a >= gamma else vida_b(1 - q, beta, eta, gamma)


def prob_condicional_combinada(a: float, delta: float, modos: list[tuple[float, float, float]]) -> float:
    """Varios modos (riesgos competitivos): el componente sobrevive si sobrevive a todos.
    modos = [(β, η, γ)]."""
    supervivencia = 1.0
    for beta, eta, gamma in modos:
        supervivencia *= 1 - prob_condicional(a, delta, beta, eta, gamma)
    return 1 - supervivencia


# ---------------------------------------------------------------------------
# Empíricos (Plan §6)
# ---------------------------------------------------------------------------


def mtbf(horas_operadas: float, n_fallas: int) -> float | None:
    return horas_operadas / n_fallas if n_fallas else None


def mttr(tiempos_reparacion: list[float]) -> float | None:
    return sum(tiempos_reparacion) / len(tiempos_reparacion) if tiempos_reparacion else None


def mttr_total(horas_parada: list[float], n_fallas: int) -> float | None:
    return sum(horas_parada) / n_fallas if n_fallas else None


def disponibilidad_inherente(mtbf_h: float | None, mttr_h: float | None) -> float | None:
    """Ai = MTBF / (MTBF + MTTR)."""
    if mtbf_h is None or mttr_h is None:
        return None
    return mtbf_h / (mtbf_h + mttr_h)


def disponibilidad_operacional(horas_requeridas: float, horas_paradas: float) -> float | None:
    """Ao = (requeridas − paradas) / requeridas (sin demanda y huelga no son requeridas: D-007)."""
    if horas_requeridas <= 0:
        return None
    return (horas_requeridas - horas_paradas) / horas_requeridas


def oee(disponibilidad: float | None, rendimiento: float | None, calidad: float | None) -> float | None:
    if None in (disponibilidad, rendimiento, calidad):
        return None
    return disponibilidad * rendimiento * calidad


# ---------------------------------------------------------------------------
# Exponencial y tabla de mortalidad (UNIDAD 2)
# ---------------------------------------------------------------------------


def tasa_exponencial(fallas: int, unidades: int) -> float:
    """λ = fallas / unidades en el período (UNIDAD 2, válvulas: 2/50 = 0,04 por año)."""
    return fallas / unidades


def confiabilidad_exponencial(t: float, lam: float) -> float:
    return math.exp(-lam * t)


@dataclass(frozen=True)
class FilaMortalidad:
    t: float
    fallados: int  # n(t)
    funcionando: int  # N(t)
    f: float  # proporción que falla en el período
    F: float  # acumulada
    R: float
    lam: float | None  # n(t) / N(t−1)


def tabla_mortalidad(tiempos: list[float], fallados: list[int], poblacion: int) -> tuple[list[FilaMortalidad], float]:
    """Tabla de mortalidad de una población de ítems idénticos y su MTTF = Σ t·n(t) / N (UNIDAD 2, diap. 13)."""
    filas = []
    vivos = poblacion
    acumulados = 0
    for t, n in zip(tiempos, fallados, strict=True):
        lam = n / vivos if vivos else None
        vivos -= n
        acumulados += n
        filas.append(FilaMortalidad(t, n, vivos, n / poblacion, acumulados / poblacion, vivos / poblacion, lam))
    vida_media = sum(t * n for t, n in zip(tiempos, fallados, strict=True)) / poblacion
    return filas, vida_media


# ---------------------------------------------------------------------------
# Sistemas: serie, paralelo y mixta (UNIDAD 2, diap. 7–10)
# ---------------------------------------------------------------------------


def serie(confiabilidades: list[float]) -> float:
    """Rs = Π Rj."""
    return math.prod(confiabilidades)


def paralelo(confiabilidades: list[float]) -> float:
    """Rp = 1 − Π (1 − Rj)."""
    return 1 - math.prod(1 - r for r in confiabilidades)


def mixta(arbol) -> float:
    """Árbol de bloques: un número es una confiabilidad; ("serie", [...]) o ("paralelo", [...])."""
    if isinstance(arbol, int | float):
        return float(arbol)
    tipo, hijos = arbol
    valores = [mixta(h) for h in hijos]
    if tipo == "serie":
        return serie(valores)
    if tipo == "paralelo":
        return paralelo(valores)
    raise ValueError(f"Tipo de bloque desconocido: {tipo}")
