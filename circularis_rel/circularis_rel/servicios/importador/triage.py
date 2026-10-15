"""Triage del histórico (Plan §11): nunca se importa directo.

- A, confiable: fecha real, componente identificado (y modo si es falla), con respaldo
  (OT, factura, parte). Entra como vida con horas de nivel E.
- B, parcial: componente claro, fecha o edad aproximada (rango). Censura por intervalo, solo MLE.
- C, no usable: sin fecha, sin componente o claramente reconstruido. Fuera del ajuste; solo
  Pareto cualitativo.
"""

from __future__ import annotations

from datetime import date

from circularis_rel.datos.enums import ClaseTriage, TipoFin


def _hay_rango(v: dict) -> bool:
    return (v.get("fecha_fin_desde") is not None and v.get("fecha_fin_hasta") is not None) or (
        v.get("edad_desde_h") is not None and v.get("edad_hasta_h") is not None
    )


def requisitos_faltantes(clase: ClaseTriage, v: dict, hay_posicion: bool, hay_modo: bool) -> list[str]:
    faltan: list[str] = []
    if clase == ClaseTriage.A:
        if not hay_posicion:
            faltan.append("componente (posición)")
        if v.get("fecha_fin") is None:
            faltan.append("fecha real del cambio (fecha_fin)")
        if not v.get("respaldo"):
            faltan.append("respaldo (OT, factura o parte)")
        if v.get("tipo_fin") == TipoFin.FALLA and not hay_modo:
            faltan.append("modo de falla")
    elif clase == ClaseTriage.B:
        if not hay_posicion:
            faltan.append("componente (posición)")
        if not _hay_rango(v):
            faltan.append("rango de fecha (desde/hasta) o de edad (desde/hasta)")
    return faltan


def sugerir_clase(v: dict, hay_posicion: bool, hay_modo: bool) -> tuple[ClaseTriage, str]:
    if not requisitos_faltantes(ClaseTriage.A, v, hay_posicion, hay_modo):
        return ClaseTriage.A, "Fecha real, componente identificado y respaldo"
    if not requisitos_faltantes(ClaseTriage.B, v, hay_posicion, hay_modo):
        return ClaseTriage.B, "Componente claro con fecha o edad aproximada: censura por intervalo"
    faltan_a = requisitos_faltantes(ClaseTriage.A, v, hay_posicion, hay_modo)
    faltan_b = requisitos_faltantes(ClaseTriage.B, v, hay_posicion, hay_modo)
    return ClaseTriage.C, (
        "No usable para el ajuste. Para A falta: " + ", ".join(faltan_a)
        + ". Para B falta: " + ", ".join(faltan_b)
    )


def parece_reconstruido(fechas: list[date], minimo: int = 4) -> bool:
    """Espaciado regular (90, 120, 150… días) típico de valores reconstruidos (Plan §11, punto 3)."""
    fechas = sorted(f for f in fechas if f is not None)
    if len(fechas) < minimo:
        return False
    saltos = [(b - a).days for a, b in zip(fechas, fechas[1:], strict=False)]
    if any(s <= 0 for s in saltos):
        return False
    return len(set(saltos)) == 1 or all(s % 30 == 0 for s in saltos)
