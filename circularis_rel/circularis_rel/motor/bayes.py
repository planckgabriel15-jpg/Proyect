"""Weibull bayesiano (Plan §5, mejora de la fase 4): combina un β de referencia con los datos propios.

Sirve cuando hay pocas fallas: en lugar de fijar β (Weibayes), el β de referencia entra como **creencia previa** con
una incertidumbre, y los datos la corrigen. Con muchos datos el resultado se acerca al de máxima verosimilitud.

- Previa de β: lognormal con mediana en el β de referencia y desvío `sd_log` en escala logarítmica
  (sd_log = ln 2 / 1,96 ≈ 0,35 quiere decir "95 % de que β esté entre la mitad y el doble").
- Previa de η: uniforme en log(η) dentro de un rango amplio alrededor de los datos (no informativa).
- Verosimilitud con fallas exactas, suspensiones por derecha y censura por intervalo.
- Posterior por grilla (sin muestreo aleatorio: el resultado es reproducible). Se informan medianas e intervalos
  de credibilidad de las marginales.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from circularis_rel.motor.tipos import Observacion


@dataclass(frozen=True)
class AjusteBayes:
    beta: float  # mediana posterior
    eta: float
    beta_ic: tuple[float, float]  # intervalo de credibilidad
    eta_ic: tuple[float, float]
    nivel: float
    beta_previa: float
    sd_log: float
    n_fallas: int
    n_suspensiones: int


def _cuantiles(grilla: np.ndarray, pesos: np.ndarray, qs: list[float]) -> list[float]:
    acum = np.cumsum(pesos)
    acum = acum / acum[-1]
    return [float(np.interp(q, acum, grilla)) for q in qs]


def ajustar(obs: list[Observacion], beta_previa: float, sd_log: float, nivel: float = 0.90,
            puntos_beta: int = 241, puntos_eta: int = 301) -> AjusteBayes:
    datos = [o for o in obs if not o.solo_pronostico]
    fallas = np.array([o.edad for o in datos if o.estado == "F"], float)
    susp = np.array([o.edad for o in datos if o.estado == "S"], float)
    inter = [(o.edad_inf, o.edad) for o in datos if o.estado == "I"]
    if len(fallas) + len(inter) < 1:
        raise ValueError("El Weibull bayesiano necesita al menos una falla")
    if beta_previa <= 0 or sd_log <= 0:
        raise ValueError("La previa necesita β > 0 y un desvío positivo")
    edades = np.concatenate([fallas, susp, np.array([b for _a, b in inter], float)])
    # Rango de β: ±4 desvíos de la previa, sin salir de 0,05–50 (fuera de eso no hay componentes reales).
    lb = np.linspace(max(math.log(beta_previa) - 4 * sd_log, math.log(0.05)),
                     min(math.log(beta_previa) + 4 * sd_log, math.log(50)), puntos_beta)
    le = np.linspace(math.log(edades.min()) - 1.5, math.log(edades.max()) + 3.0, puntos_eta)
    B, E = np.meshgrid(np.exp(lb), np.exp(le), indexing="ij")
    loglik = np.zeros_like(B)
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):  # (t/η)^β enorme = verosimilitud cero
        if len(fallas):
            lf = np.log(fallas)
            # Σ [ln β − ln η + (β−1)(ln t − ln η) − (t/η)^β]
            loglik += len(fallas) * (np.log(B) - np.log(E)) + (B - 1) * (lf.sum() - len(fallas) * np.log(E))
            loglik -= sum((t / E) ** B for t in fallas)
        for t in susp:
            loglik -= (t / E) ** B
        for a, b in inter:
            fa = 1 - np.exp(-((a / E) ** B)) if a > 0 else 0.0
            fb = 1 - np.exp(-((b / E) ** B))
            loglik += np.log(np.clip(fb - fa, 1e-300, None))
    # Previa: lognormal en β (en la variable ln β es normal) y plana en ln η (la grilla ya es en logaritmos).
    logprevia = -0.5 * ((lb[:, None] - math.log(beta_previa)) / sd_log) ** 2
    logpost = np.nan_to_num(loglik, nan=-np.inf, posinf=-np.inf) + logprevia
    post = np.exp(logpost - logpost.max())
    a = (1 - nivel) / 2
    mb = post.sum(axis=1)
    me = post.sum(axis=0)
    b_inf, b_med, b_sup = _cuantiles(lb, mb, [a, 0.5, 1 - a])
    e_inf, e_med, e_sup = _cuantiles(le, me, [a, 0.5, 1 - a])
    return AjusteBayes(math.exp(b_med), math.exp(e_med), (math.exp(b_inf), math.exp(b_sup)), (math.exp(e_inf), math.exp(e_sup)),
                       nivel, beta_previa, sd_log, len(fallas) + len(inter), len(susp))
