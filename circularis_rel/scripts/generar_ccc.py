"""Genera `circularis_rel/motor/tablas/ccc_p10.csv`: valor crítico de r² (percentil 10) de la recta de
Weibull por RRX con rangos de Benard, para n = 3…100 fallas (Plan §5, bondad de ajuste 1).

Método (D-005/P-03): Monte Carlo con semilla fija. Para cada n se simulan muestras completas de una
Weibull (el r² no depende de β ni η: ln t es una transformación afín de una Gumbel de mínimos), se ordena,
se calcula r² entre x = ln t e y = ln(−ln(1 − F_Benard)) y se toma el percentil 10. Con suspensiones se
usa n = número de fallas, como en Abernethy.

Uso:  python scripts/generar_ccc.py [réplicas]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

SALIDA = Path(__file__).resolve().parent.parent / "circularis_rel" / "motor" / "tablas" / "ccc_p10.csv"


def ccc(n: int, replicas: int, rng: np.random.Generator) -> float:
    i = np.arange(1, n + 1)
    y = np.log(-np.log(1 - (i - 0.3) / (n + 0.4)))
    x = np.sort(np.log(rng.weibull(1.0, (replicas, n))), axis=1)
    xm = x - x.mean(axis=1, keepdims=True)
    ym = y - y.mean()
    r = (xm * ym).sum(axis=1) / np.sqrt((xm**2).sum(axis=1) * (ym**2).sum())
    return float(np.percentile(r**2, 10))


def main() -> None:
    replicas = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
    rng = np.random.default_rng(20261015)
    filas = ["n,r2_critico_p10"]
    for n in range(3, 101):
        filas.append(f"{n},{ccc(n, replicas, rng):.5f}")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(filas) + "\n", encoding="utf-8")
    print(f"Tabla generada con {replicas} réplicas por n: {SALIDA}")


if __name__ == "__main__":
    main()
