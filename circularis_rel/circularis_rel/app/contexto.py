"""Recursos compartidos de la app: base de datos y configuración (uno por proceso)."""

from __future__ import annotations

import streamlit as st

from circularis_rel.config import Config, cargar_config
from circularis_rel.datos.db import BaseDatos


@st.cache_resource
def config() -> Config:
    return cargar_config()


@st.cache_resource
def db() -> BaseDatos:
    return BaseDatos(config().url_db)


def usuario() -> dict | None:
    """Usuario logueado: {'id', 'usuario', 'nombre', 'rol'}."""
    return st.session_state.get("usuario")


def id_usuario() -> int | None:
    u = usuario()
    return u["id"] if u else None
