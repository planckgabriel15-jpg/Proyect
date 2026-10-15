"""Botón "?" con la definición de un indicador [12.H]."""

from __future__ import annotations

import streamlit as st

from circularis_rel.asistente.ayudas import AYUDAS

ETAPAS = {"PREPROCESADO": "Preprocesado", "LAVADO": "Lavado", "SECADO": "Secado", "FORMULACION": "Formulación",
          "EXTRUSION": "Extrusión", "ACONDICIONAMIENTO": "Acondicionamiento"}


def texto(clave: str) -> str:
    a = AYUDAS[clave]
    return f"**{a['titulo']}**\n\n{a['texto']}\n\n*Fuente: {a['fuente']}*"


def etiqueta_corta(clave: str) -> str:
    """Texto del botón: el "corto" de la definición o, si el título empieza con una sigla ("MTBF: …"), "¿Qué es MTBF?"."""
    a = AYUDAS[clave]
    if "corto" in a:
        return a["corto"]
    sigla = a["titulo"].split(":")[0] if ":" in a["titulo"] else ""
    return f"¿Qué es {sigla}?" if 0 < len(sigla) <= 8 else "¿Qué es?"


def boton(clave: str, contenedor=None, etiqueta: str | None = None) -> None:
    """Burbuja de ayuda: botón con el tema ("¿Qué es β?") que abre la definición, con su fuente (si la hay)."""
    a = AYUDAS.get(clave)
    if a is None:
        return
    with (contenedor or st).popover(etiqueta or etiqueta_corta(clave), icon=":material/help:", help=a["titulo"]):
        st.markdown(f"**{a['titulo']}**")
        st.write(a["texto"])
        st.caption(f"Fuente: {a['fuente']}")


def metrica(contenedor, etiqueta: str, valor: str, clave: str | None = None, ayuda_texto: str | None = None) -> None:
    """Métrica con la definición en el "?" del encabezado."""
    partes = [x for x in (texto(clave) if clave else None, ayuda_texto) if x]
    contenedor.metric(etiqueta, valor, help="\n\n".join(partes) or None, border=True)


def porcentaje(x: float | None, decimales: int = 1) -> str:
    return "falta dato" if x is None else f"{x:.{decimales}%}".replace(".", ",")


def numero(x: float | None, decimales: int = 0, unidad: str = "") -> str:
    if x is None:
        return "falta dato"
    texto = f"{x:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto} {unidad}".strip()


def pesos(x: float | None) -> str:
    return "falta dato" if x is None else "$ " + numero(x)
