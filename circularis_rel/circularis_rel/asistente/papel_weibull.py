"""Calculadora del papel de Weibull [12.H]: el procedimiento de la cátedra (UNIDAD 2, diap. 31–38) con datos propios.

1. Ordenar los tiempos de falla de menor a mayor y numerarlos (i).
2. F(i) por rango de Benard: (i − 0,3) / (N + 0,4). Con suspensiones, i es el rango ajustado de Johnson.
3. Llevar los puntos al papel y trazar la recta (acá, regresión X sobre Y: RRX).
4. β = pendiente (paralela por el polo); η = donde la recta corta el 63,2 %.
5. R(t) = e^−(t/η)^β para el tiempo de misión.

Además del papel se corre el ajuste completo del sistema (mismo motor que el semáforo), con su intervalo de
confianza, para comparar.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from circularis_rel.motor import kpis
from circularis_rel.motor import weibull as W
from circularis_rel.motor.tipos import Configuracion, Observacion, ResultadoPar

# Ejemplo resuelto de la cátedra: tiempos de falla en horas (UNIDAD 2, diap. 33–38).
EJEMPLO_UNIDAD2 = {"fuente": "UNIDAD 2, diap. 33–38 (Mgter. L. D. Torres)", "tiempos": [93, 34, 16, 120, 53, 75],
                   "mision": 15.0}

ESTADO = {
    "MORTALIDAD_INFANTIL": "Juventud (β < 1)",
    "ALEATORIA": "Estable: fallas al azar (β ≈ 1)",
    "DESGASTE": "Desgaste (β > 1)",
    "DESGASTE_RAPIDO": "Desgaste rápido (β alto)",
}


@dataclass
class FilaPapel:
    orden: int
    tiempo: float
    falla: bool
    rango: float | None = None  # rango ajustado de Johnson (= i sin suspensiones)
    f_benard: float | None = None


@dataclass
class ResultadoPapel:
    filas: list[FilaPapel]
    rangos: list[tuple[float, float, float]]
    n_fallas: int
    n_suspensiones: int
    beta: float | None = None
    eta: float | None = None
    r2: float | None = None
    r2_critico: float | None = None
    mttf: float | None = None
    estado: str | None = None
    r_mision: float | None = None
    ajuste: ResultadoPar | None = None
    avisos: list[str] = field(default_factory=list)


def a_horas(valores: list[float], unidad: str, horas_por_dia: float | None) -> list[float]:
    """El TP N.º 1 carga los TBF en días y los pasa a horas con las horas de trabajo por día."""
    if unidad == "h":
        return [float(v) for v in valores]
    if not horas_por_dia or horas_por_dia <= 0:
        raise ValueError("Indicá cuántas horas por día trabaja la máquina para pasar los días a horas")
    return [float(v) * horas_por_dia for v in valores]


def calcular(datos: list[tuple[float, bool]], t_mision: float | None = None, cfg: Configuracion | None = None,
             con_ajuste: bool = True) -> ResultadoPapel:
    """datos = [(tiempo, falló)]; falló = False es una suspensión (se retiró o sigue andando sin fallar)."""
    cfg = cfg or Configuracion()
    validos = [(float(t), bool(f)) for t, f in datos if t is not None]
    if any(t <= 0 for t, _ in validos):
        raise ValueError("Los tiempos tienen que ser mayores que cero")
    obs = [Observacion(t, "F" if f else "S") for t, f in validos]
    rangos = W.rangos_johnson(obs)
    por_tiempo = {}
    for edad, rango, f in rangos:
        por_tiempo.setdefault(edad, []).append((rango, f))
    ordenados = sorted(validos, key=lambda x: (x[0], not x[1]))
    filas = []
    for k, (t, falla) in enumerate(ordenados, start=1):
        fila = FilaPapel(k, t, falla)
        if falla and por_tiempo.get(t):
            fila.rango, fila.f_benard = por_tiempo[t].pop(0)
        filas.append(fila)
    nf = sum(1 for _, f in validos if f)
    res = ResultadoPapel(filas=filas, rangos=rangos, n_fallas=nf, n_suspensiones=len(validos) - nf)
    if nf < 2:
        res.avisos.append("Hacen falta al menos 2 fallas para trazar la recta (3 o más para que el resultado sirva)")
        return res
    res.beta, res.eta, res.r2, _ = W.rrx(obs)
    res.r2_critico = W.r2_critico(nf)
    res.mttf = kpis.mttf(res.beta, res.eta)
    res.estado = ESTADO[W.interpretar(res.beta, None, cfg)]
    if t_mision and t_mision > 0:
        res.r_mision = kpis.confiabilidad(t_mision, res.beta, res.eta)
    if nf < cfg.min_fallas_rrx:
        res.avisos.append(f"Con {nf} fallas la recta es muy incierta: tomala como orientativa")
    if res.r2 is not None and res.r2_critico is not None and res.r2 < res.r2_critico:
        res.avisos.append("Los puntos no siguen bien una recta (r² menor que el crítico): puede haber modos de falla "
                          "mezclados o una vida mínima (γ). Separá los datos por componente y modo de falla.")
    if con_ajuste and nf >= cfg.min_fallas_rrx:
        res.ajuste = W.ajustar(obs, cfg)
    return res


def r_en_eta() -> float:
    """R(η) = e^−1 = 36,8 % para cualquier β (UNIDAD 2, diap. 37)."""
    return math.exp(-1)
