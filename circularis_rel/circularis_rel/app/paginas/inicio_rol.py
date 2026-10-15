"""Inicio de operario, encargado y gerencia. Las pantallas de carga llegan en la fase 1a."""

import streamlit as st

from circularis_rel.app import contexto

u = contexto.usuario()
st.header(f"Hola, {u['nombre']}")
maq = st.session_state.get("maquina_qr")
if maq:
    st.info(f"Máquina del QR: **{maq}**")
st.info("Las pantallas de **parte de turno**, **aviso de falla** y **tarjetas** se habilitan en la fase 1a "
        "(captura). Por ahora el sistema está en preparación.")
