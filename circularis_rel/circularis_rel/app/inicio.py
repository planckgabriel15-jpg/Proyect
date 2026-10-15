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
from circularis_rel.servicios import modulos
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
    mod_12g, mod_12h, mod_12f = (modulos.habilitado(s, c) for c in ("12G", "12H", "12F"))

rol = Rol(usuario["rol"])


def pagina(archivo: str, titulo: str, icono: str) -> st.Page:
    return st.Page(str(PAGINAS / archivo), title=titulo, icon=icono)


ayuda = pagina("ayuda.py", "Ayuda", "❓")
planta = [pagina("planta.py", "Inicio", "🏠"), pagina("reportar_falla.py", "Reportar falla", "🛠️"),
          pagina("parte_turno.py", "Parte de turno", "📝"), pagina("tarjeta.py", "Tarjeta", "🏷️")]
mantenimiento = [pagina("bandeja_encargado.py", "Bandeja del encargado", "📋"), pagina("cerrar_ot.py", "Cerrar OT", "🔧"),
                 pagina("cambio_preventivo.py", "Cambio preventivo", "🔁")]
exportar = pagina("exportar.py", "Exportar", "📤")
panel_planta = pagina("panel_planta.py", "Panel de planta", "📊")
ficha = pagina("ficha_maquina.py", "Ficha de máquina", "🏭")
weibull = pagina("analisis_weibull.py", "Análisis Weibull", "📈")
papel = pagina("papel_weibull.py", "Papel de Weibull", "📐")
problemas = pagina("analisis_problemas.py", "Análisis de problemas", "🔍")
tablero = pagina("tablero.py", "Tablero de comando", "🎯")
plan = pagina("plan_preventivo.py", "Plan preventivo", "🗓️")
repuestos = pagina("repuestos.py", "Repuestos", "📦")
predictivo = [pagina("predictivo.py", "Predictivo", "📡")] if mod_12g else []
herramientas = [pagina("herramientas.py", "Herramientas de fiabilidad", "🧮")] if mod_12h else []
reportes = pagina("reportes.py", "Reportes", "🧾")
tpm = [pagina("tpm.py", "TPM y OEE", "⚙️")] if mod_12f else []

if rol == Rol.OPERARIO:
    paginas = {"": [*planta, ficha, ayuda]}
elif rol == Rol.ENCARGADO:
    paginas = {"Mantenimiento": [*mantenimiento, plan, repuestos, *predictivo, problemas, ficha], "Planta": planta,
               "Otros": [exportar, ayuda]}
elif rol == Rol.GERENCIA:
    paginas = {"": [panel_planta, tablero, ficha, reportes, *tpm, papel, *herramientas, exportar, ayuda]}
else:  # JEFE
    paginas = {
        "Panel": [panel_planta, ficha, weibull, papel, problemas, tablero, reportes, *tpm, *herramientas],
        "Gestión": [pagina("bandeja_validacion.py", "Bandeja de validación", "✅"), *mantenimiento, plan, repuestos,
                    *predictivo],
        "Planta": planta,
        "Puesta en marcha": [
            pagina("puesta_en_marcha.py", "Puesta en marcha", "🧭"),
            pagina("piloto.py", "Piloto", "🧪"),
            pagina("carga_inicial.py", "Carga de planillas", "📥"),
            pagina("maquinas.py", "Máquinas y revisión", "🏗️"),
            pagina("criticidad.py", "Criticidad", "⚖️"),
            pagina("amfe.py", "AMFE", "🧯"),
            pagina("catalogos.py", "Catálogos", "📚"),
            pagina("historico.py", "Histórico (triage)", "🗂️"),
        ],
        "Configuración": [
            pagina("usuarios.py", "Usuarios", "👥"),
            pagina("parametros.py", "Parámetros", "⚙️"),
            pagina("datos_demo.py", "Datos DEMO", "🧪"),
            exportar,
        ],
        "Ayuda": [ayuda],
    }

with st.sidebar:
    st.markdown(f"**{usuario['nombre']}**  \n{rol.value.capitalize()}")
    if st.button("Salir", width="stretch"):
        sesion.salir()
        st.rerun()

st.navigation(paginas, expanded=True).run()
