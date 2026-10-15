"""Exportación total a Excel: la empresa nunca queda atada al software."""

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.servicios.exportacion import exportar_todo
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.EXPORTAR)
st.header("📤 Exportar")
st.caption("Un libro de Excel con una hoja por tabla, con todos los datos del sistema (sin contraseñas).")
if st.button("Preparar exportación", width="stretch"):
    with contexto.db().lectura() as s:
        st.session_state["exportacion"] = exportar_todo(s)
if "exportacion" in st.session_state:
    st.download_button("Descargar Excel", st.session_state["exportacion"],
                       file_name=f"circularis_{F.hoy():%Y%m%d}.xlsx", type="primary", width="stretch")
