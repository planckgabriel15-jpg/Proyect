"""Datos DEMO: ficticios, para probar y capacitar. Se borran antes de usar el sistema en serio."""

import streamlit as st

from circularis_rel.app import contexto, sesion
from circularis_rel.servicios.demo import USUARIOS_DEMO, borrar_demo, cargar_demo, hay_demo
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.CONFIGURAR)
db = contexto.db()
st.header("Datos DEMO")
st.caption("Máquinas, componentes y usuarios ficticios (todo empieza con DEMO- o demo.). Mientras estén cargados se ve el cartel rojo.")
with db.lectura() as s:
    cargados = hay_demo(s)
if cargados:
    st.warning("Hay datos DEMO cargados.")
    st.table([{"Usuario": u, "Rol": r.capitalize(), "Clave": c} for u, _n, r, c, _m in USUARIOS_DEMO])
    if st.button("Borrar todos los datos DEMO", type="primary", use_container_width=True):
        borrar_demo(db, contexto.id_usuario())
        sesion.refrescar_credenciales()
        st.rerun()
else:
    st.info("No hay datos DEMO.")
    if st.button("Cargar datos DEMO", use_container_width=True):
        reporte = cargar_demo(db, contexto.id_usuario())
        sesion.refrescar_credenciales()
        if reporte.aplicado:
            st.rerun()
        st.error(reporte.texto())
