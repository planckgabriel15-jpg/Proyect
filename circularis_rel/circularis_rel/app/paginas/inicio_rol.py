"""Inicio de operario, encargado y gerencia. Las pantallas de carga llegan en la fase 1a."""

import streamlit as st

from circularis_rel.app import contexto

u = contexto.usuario()
st.header(f"Hola, {u['nombre']}")
maq = st.session_state.get("maquina_qr")
if maq:
    st.info(f"Máquina del QR: **{maq}**")
st.info("El **panel de planta** (disponibilidad, MTBF, MTTR, costos y semáforos) se habilita en la fase 1c. "
        "Mientras tanto podés exportar todos los datos a Excel.")
