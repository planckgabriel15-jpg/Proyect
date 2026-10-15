"""Estilo de planta: botones de al menos 48 px, letra grande, alto contraste (uso con guantes)."""

from __future__ import annotations

import streamlit as st

CSS = """
<style>
html, body, [class*="css"] { font-size: 18px; }
div.stButton > button, div.stDownloadButton > button, div.stFormSubmitButton > button {
    min-height: 48px; font-size: 1.05rem; font-weight: 600;
}
div[role="radiogroup"] label { min-height: 44px; padding: 6px 10px; }
.demo-banner {
    background: #b00020; color: #fff; padding: 10px 16px; border-radius: 6px;
    font-weight: 700; text-align: center; margin-bottom: 12px; font-size: 1.05rem;
}
</style>
"""


def aplicar() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def cartel_demo() -> None:
    st.markdown('<div class="demo-banner">⚠ DATOS FICTICIOS DE DEMOSTRACIÓN cargados. '
                'Borrarlos en Configuración › Datos DEMO antes de usar el sistema en serio.</div>',
                unsafe_allow_html=True)
