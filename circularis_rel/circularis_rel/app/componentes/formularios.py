"""Ayudas comunes de los formularios de planta: idempotencia, máquina por defecto, fecha y hora local."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.datos.db import ahora


def token(clave: str) -> str:
    """Token de envío único por formulario: evita duplicados por doble toque o mala señal."""
    k = f"token_{clave}"
    if k not in st.session_state:
        st.session_state[k] = uuid.uuid4().hex
    return st.session_state[k]


def renovar_token(clave: str) -> None:
    st.session_state.pop(f"token_{clave}", None)


def ahora_local() -> datetime:
    return ahora().astimezone(contexto.config().zona_horaria)


def hoy() -> date:
    return ahora_local().date()


def combinar(fecha: date, hora: time) -> datetime:
    return datetime.combine(fecha, hora, tzinfo=contexto.config().zona_horaria)


def indice_maquina(codigos: list[str]) -> int:
    """QR > última usada > primera."""
    for clave in ("maquina_qr", "ultima_maquina"):
        c = st.session_state.get(clave)
        if c in codigos:
            return codigos.index(c)
    return 0


def recordar_maquina(codigo: str) -> None:
    st.session_state["ultima_maquina"] = codigo


def mensaje_ok(clave: str) -> None:
    """Muestra (una vez) el mensaje de éxito guardado antes de un rerun."""
    texto = st.session_state.pop(f"ok_{clave}", None)
    if texto:
        st.success(texto)


def guardar_mensaje_ok(clave: str, texto: str) -> None:
    st.session_state[f"ok_{clave}"] = texto
