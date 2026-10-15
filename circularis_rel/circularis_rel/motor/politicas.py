"""Políticas de mantenimiento (Plan §8) e inventarios (UNIDAD 5).

- Intervalo óptimo por costo (reemplazo por edad): C(T) = [Cp·R(T) + Cf·F(T)] / ∫₀ᵀ R(t) dt.
  "Hasta la falla" cuesta Cf / MTTF por hora. La curva suele ser plana cerca del óptimo, así que se
  redondea el intervalo a un paso cómodo (alineado con paradas).
- Intervalo por confiabilidad objetivo: T = η·(−ln R*)^(1/β) (con R* = 90 %, T = B10).
- Falla con intervalo P-F conocido: inspección cada P-F/2.
- Stock mínimo por Poisson para un nivel de servicio; lote económico y stock de protección de la cátedra.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy import integrate, optimize, stats

from circularis_rel.motor import kpis


def costo_por_hora(T: float, cp: float, cf: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    r = kpis.confiabilidad(T, beta, eta, gamma)
    integral, _ = integrate.quad(lambda t: kpis.confiabilidad(t, beta, eta, gamma), 0, T, limit=200)
    return (cp * r + cf * (1 - r)) / integral


def costo_hasta_falla(cf: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    return cf / kpis.mttf(beta, eta, gamma)


def intervalo_optimo(cp: float, cf: float, beta: float, eta: float, gamma: float = 0.0) -> tuple[float, float] | None:
    """(T*, C(T*)). None si no hay óptimo finito (β ≤ 1 o Cf ≤ Cp): conviene correr hasta la falla."""
    if beta <= 1 or cf <= cp:
        return None
    superior = eta * 5 + gamma
    r = optimize.minimize_scalar(lambda T: costo_por_hora(T, cp, cf, beta, eta, gamma),
                                 bounds=(max(eta * 0.01, gamma + 1e-6), superior), method="bounded",
                                 options={"xatol": 1e-3})
    if r.x >= superior * 0.999 or r.fun >= costo_hasta_falla(cf, beta, eta, gamma):
        return None
    return float(r.x), float(r.fun)


def curva_costo(cp: float, cf: float, beta: float, eta: float, gamma: float = 0.0, puntos: int = 60,
                hasta: float | None = None) -> list[tuple[float, float, float]]:
    """[(T, C(T), F(T))] para graficar la curva completa."""
    hasta = hasta or 2.5 * eta
    salida = []
    for i in range(1, puntos + 1):
        T = hasta * i / puntos
        salida.append((T, costo_por_hora(T, cp, cf, beta, eta, gamma), kpis.infiabilidad(T, beta, eta, gamma)))
    return salida


def redondear_intervalo(T: float, paso: float) -> float:
    """Intervalo redondo más cercano (Plan §15: 369 h con paso 25 h → 375 h)."""
    return max(paso, round(T / paso) * paso) if paso > 0 else T


def intervalo_confiabilidad(r_objetivo: float, beta: float, eta: float, gamma: float = 0.0) -> float:
    return kpis.vida_para_confiabilidad(r_objetivo, beta, eta, gamma)


def intervalo_inspeccion_pf(pf: float) -> float:
    return pf / 2


@dataclass
class Recomendacion:
    regla: str  # NINGUNO | OPTIMO_COSTO | CONFIABILIDAD_OBJETIVO | PF
    intervalo: float | None
    texto: str
    t_optimo: float | None = None
    costo_optimo: float | None = None
    costo_falla_por_hora: float | None = None
    ahorro: float | None = None  # fracción de ahorro frente a correr hasta la falla


def recomendar(beta: float | None, eta: float | None, *, cp: float | None, cf: float | None, critico: bool,
               seguridad: bool, intervalo_pf: float | None, r_objetivo: float, cf_cp_minimo: float,
               paso_redondeo: float, interpretacion: str | None = None, gamma: float = 0.0) -> Recomendacion:
    """Reglas del Plan §8, en este orden: P-F conocido, β ≤ 1 (o aleatoria), seguridad o clase A, costo."""
    if intervalo_pf:
        return Recomendacion("PF", intervalo_inspeccion_pf(intervalo_pf),
                             f"Inspección cada P-F/2 = {intervalo_inspeccion_pf(intervalo_pf):g}")
    if beta is None or eta is None:
        return Recomendacion("NINGUNO", None, "Sin Weibull todavía: usar la recomendación del fabricante")
    if beta <= 1 or interpretacion in ("ALEATORIA", "MORTALIDAD_INFANTIL"):
        return Recomendacion("NINGUNO", None, "β ≤ 1 o fallas al azar: sin preventivo por tiempo. Inspección, "
                                              "mantenimiento por condición o análisis de causa raíz")
    if seguridad or critico:
        t = intervalo_confiabilidad(r_objetivo, beta, eta, gamma)
        return Recomendacion("CONFIABILIDAD_OBJETIVO", redondear_intervalo(t, paso_redondeo),
                             f"Componente crítico: cambio a R* = {r_objetivo:.0%} (T = {t:.0f})", t_optimo=t)
    if cp and cf and cf / cp >= cf_cp_minimo:
        opt = intervalo_optimo(cp, cf, beta, eta, gamma)
        if opt is not None:
            hasta_falla = costo_hasta_falla(cf, beta, eta, gamma)
            return Recomendacion("OPTIMO_COSTO", redondear_intervalo(opt[0], paso_redondeo),
                                 f"Intervalo óptimo por costo ≈ {opt[0]:.0f}", t_optimo=opt[0], costo_optimo=opt[1],
                                 costo_falla_por_hora=hasta_falla, ahorro=1 - opt[1] / hasta_falla)
    if not cp or not cf:
        return Recomendacion("NINGUNO", None, "Falta cargar costos (precio, tarifa o margen) para calcular el intervalo")
    return Recomendacion("NINGUNO", None, f"Cf/Cp = {cf / cp:.1f} < {cf_cp_minimo:g}: el preventivo por tiempo no se justifica")


# ---------------------------------------------------------------------------
# Repuestos e inventarios
# ---------------------------------------------------------------------------


def stock_minimo_poisson(demanda_lead_time: float, nivel_servicio: float) -> int:
    """Menor s tal que P(demanda ≤ s) ≥ nivel de servicio, con demanda Poisson (Plan §8)."""
    if demanda_lead_time <= 0:
        return 0
    return int(stats.poisson.ppf(nivel_servicio, demanda_lead_time))


def lote_economico(K: float, D: float, b: float, p: float) -> float:
    """q_e = √(2·K·D / (b·p)) (UNIDAD 5, diap. 62)."""
    return math.sqrt(2 * K * D / (b * p))


def costo_total_inventario(q: float, K: float, D: float, b: float, p: float) -> float:
    """CTE = K·D/q + ½·q·b·p (UNIDAD 5, diap. 56–59)."""
    return K * D / q + 0.5 * q * b * p


def factor_h(riesgo: float) -> float:
    """H = Φ⁻¹(1 − riesgo). La tabla de la cátedra redondea estos valores (B-007)."""
    return float(stats.norm.ppf(1 - riesgo))


def stock_proteccion(riesgo: float, consumo_diario: float, demora_dias: float) -> float:
    """Sp = H·√(c·d) (UNIDAD 5, diap. 67)."""
    return factor_h(riesgo) * math.sqrt(consumo_diario * demora_dias)
