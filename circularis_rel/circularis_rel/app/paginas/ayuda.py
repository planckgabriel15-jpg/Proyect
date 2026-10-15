"""Ayuda: definiciones en lenguaje simple [12.H]."""

import streamlit as st

from circularis_rel.asistente.ayudas import AYUDAS

st.header("Ayuda: qué significa cada indicador")
st.caption("Definiciones simples, con la fuente de cada una. También aparecen con el botón \"?\" junto a cada indicador.")
for a in AYUDAS.values():
    with st.expander(a["titulo"]):
        st.write(a["texto"])
        st.caption(f"Fuente: {a['fuente']}")
