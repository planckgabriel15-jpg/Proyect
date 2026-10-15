"""Login (P-02): `streamlit-authenticator` solo para el formulario y la cookie firmada.
Usuarios, roles y contraseñas viven en la base (`servicios/auth.py`)."""

from __future__ import annotations

import streamlit as st
import streamlit_authenticator as stauth
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.datos.modelos import Usuario
from circularis_rel.servicios import auth


def _autenticador() -> stauth.Authenticate:
    if "autenticador" not in st.session_state:
        cfg = contexto.config()
        with contexto.db().lectura() as s:
            credenciales = auth.credenciales(s)
        st.session_state["autenticador"] = stauth.Authenticate(
            credenciales, cfg.nombre_cookie, cfg.clave_cookie, cfg.dias_cookie, auto_hash=False)
    return st.session_state["autenticador"]


def asegurar_login() -> dict | None:
    """Devuelve el usuario logueado o muestra el formulario y devuelve None."""
    if contexto.usuario():
        return contexto.usuario()
    with contexto.db().lectura() as s:
        hay_usuarios = s.scalar(select(Usuario.id).limit(1)) is not None
    if not hay_usuarios:
        st.title("Circularis · Sistema de confiabilidad")
        st.warning("Todavía no hay usuarios. Crear el primero desde la PC del servidor con:\n\n"
                   "`circularis crear-usuario jefe \"Nombre del jefe\" JEFE`")
        return None
    # Nota: no envolver el login en un contenedor que se vacíe ni hacer st.rerun() al entrar: el componente
    # que escribe la cookie se dibuja en esta corrida y, si se borra, la sesión no sobrevive a una recarga.
    autenticador = _autenticador()
    if st.session_state.get("authentication_status") is None:
        st.title("Circularis · Sistema de confiabilidad")
    try:
        autenticador.login(location="main", fields={
            "Form name": "Ingresar", "Username": "Usuario", "Password": "Contraseña o PIN", "Login": "Entrar"})
    except Exception as e:  # la librería lanza errores propios ante datos inválidos
        st.error(f"No se pudo ingresar: {e}")
        return None
    estado = st.session_state.get("authentication_status")
    if estado is False:
        st.error("Usuario o contraseña incorrectos.")
        return None
    if not estado:
        return None
    with contexto.db().lectura() as s:
        u = s.scalar(select(Usuario).where(Usuario.usuario == st.session_state["username"], Usuario.activo.is_(True)))
    if u is None:
        st.error("El usuario está dado de baja.")
        return None
    st.session_state["usuario"] = {"id": u.id, "usuario": u.usuario, "nombre": u.nombre, "rol": u.rol.value}
    return st.session_state["usuario"]


def salir() -> None:
    autenticador = st.session_state.get("autenticador")
    if autenticador is not None:
        autenticador.logout("Salir", location="unrendered")
    for clave in ("usuario", "autenticador"):
        st.session_state.pop(clave, None)


def refrescar_credenciales() -> None:
    """Después de crear o cambiar usuarios, el formulario de login tiene que ver los datos nuevos."""
    st.session_state.pop("autenticador", None)
