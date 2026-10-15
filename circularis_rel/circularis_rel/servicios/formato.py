"""Formato de números y fechas para pantalla y reportes (es-AR: 1.495,50)."""

from __future__ import annotations

from datetime import date, datetime


def numero(valor: float | int | None, decimales: int = 2, vacio: str = "—") -> str:
    if valor is None:
        return vacio
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def cantidad(valor: float | int | None, vacio: str = "") -> str:
    """Cantidades: sin decimales si es entera (2 y no 2,00)."""
    if valor is None:
        return vacio
    return numero(valor, 0 if float(valor).is_integer() else 2)


def fecha(valor: date | datetime | None, vacio: str = "") -> str:
    return valor.strftime("%d/%m/%Y") if valor else vacio
