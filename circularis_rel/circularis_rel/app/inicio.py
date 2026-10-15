"""Punto de entrada de la app web: login y navegación por rol.

    streamlit run circularis_rel/app/inicio.py      (o:  circularis app)

Cada rol ve solo sus páginas; además cada servicio verifica el permiso.
El QR de la máquina abre esta app con `?maq=AGR-001`: se guarda para preseleccionarla.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from circularis_rel.app import contexto, sesion
from circularis_rel.app.componentes import estilos
from circularis_rel.datos.enums import Rol
from circularis_rel.servicios.demo import hay_demo

PAGINAS = Path(__file__).parent / "paginas"

st.set_page_config(page_title="Circularis", page_icon="🔧", layout="wide")
estilos.aplicar()

maquina_qr = st.query_params.get("maq")
if maquina_qr:
    st.session_state["maquina_qr"] = maquina_qr

usuario = sesion.asegurar_login()
if usuario is None:
    st.stop()

with contexto.db().lectura() as s:
    if hay_demo(s):
        estilos.cartel_demo()

rol = Rol(usuario["rol"])


def pagina(archivo: str, titulo: str, icono: str) -> st.Page:
    return st.Page(str(PAGINAS / archivo), title=titulo, icon=icono)


comunes = [pagina("ayuda.py", "Ayuda", "❓")]
if rol == Rol.JEFE:
    paginas = {
        "Puesta en marcha": [
            pagina("puesta_en_marcha.py", "Puesta en marcha", "🧭"),
            pagina("carga_inicial.py", "Carga de planillas", "📥"),
            pagina("maquinas.py", "Máquinas y revisión", "🏭"),
            pagina("historico.py", "Histórico (triage)", "🗂️"),
        ],
        "Configuración": [
            pagina("usuarios.py", "Usuarios", "👥"),
            pagina("parametros.py", "Parámetros", "⚙️"),
            pagina("datos_demo.py", "Datos DEMO", "🧪"),
        ],
        "Ayuda": comunes,
    }
else:
    paginas = {"Inicio": [pagina("inicio_rol.py", "Inicio", "🏠"), *comunes]}

with st.sidebar:
    st.markdown(f"**{usuario['nombre']}**  \n{rol.value.capitalize()}")
    if st.button("Salir", use_container_width=True):
        sesion.salir()
        st.rerun()

st.navigation(paginas).run()
