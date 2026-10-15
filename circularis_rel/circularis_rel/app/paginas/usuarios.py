"""Usuarios: alta, máquinas asignadas, clave y baja."""

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto, sesion
from circularis_rel.datos.enums import Rol
from circularis_rel.datos.modelos import Activo, Usuario
from circularis_rel.servicios import auth
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.CONFIGURAR)
db = contexto.db()
st.header("Usuarios")
st.caption("Operarios: usuario + PIN de 4 a 6 números. Encargado, jefe y gerencia: contraseña de 8 caracteres o más.")

with db.lectura() as s:
    usuarios = list(s.scalars(select(Usuario).order_by(Usuario.rol, Usuario.usuario)))
    maquinas_por_usuario = {u.id: auth.maquinas_de(s, u.id) for u in usuarios}
    codigos = list(s.scalars(select(Activo.codigo).where(Activo.activo.is_(True)).order_by(Activo.codigo)))

st.dataframe([{"Usuario": u.usuario, "Nombre": u.nombre, "Rol": u.rol.value.capitalize(),
               "Máquinas": ", ".join(maquinas_por_usuario[u.id]), "Activo": "Sí" if u.activo else "No"}
              for u in usuarios], hide_index=True, width="stretch")

t_alta, t_editar = st.tabs(["Nuevo usuario", "Modificar"])
with t_alta, st.form("alta", clear_on_submit=True):
    usuario = st.text_input("Usuario (sin espacios)")
    nombre = st.text_input("Nombre y apellido")
    rol = st.selectbox("Rol", [r.value for r in Rol], format_func=str.capitalize)
    clave = st.text_input("Contraseña o PIN", type="password")
    email = st.text_input("Email (para alertas, opcional)")
    maquinas = st.multiselect("Máquinas a cargo (operarios)", codigos)
    if st.form_submit_button("Crear usuario", width="stretch"):
        try:
            with db.escritura(usuario_id=contexto.id_usuario()) as s:
                auth.crear_usuario(s, usuario, nombre, rol, clave, email or None, maquinas)
            sesion.refrescar_credenciales()
            st.success(f"Usuario '{usuario}' creado.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))

with t_editar:
    if not usuarios:
        st.stop()
    elegido = st.selectbox("Usuario", usuarios, format_func=lambda u: f"{u.usuario} · {u.nombre}")
    with st.form("editar"):
        maquinas = st.multiselect("Máquinas a cargo", codigos, default=maquinas_por_usuario[elegido.id])
        nueva = st.text_input("Nueva contraseña o PIN (vacío = no cambiar)", type="password")
        activo = st.checkbox("Usuario activo", value=elegido.activo)
        if st.form_submit_button("Guardar cambios", width="stretch"):
            try:
                with db.escritura(usuario_id=contexto.id_usuario()) as s:
                    u = s.get(Usuario, elegido.id)
                    auth.asignar_maquinas(s, u, maquinas)
                    if nueva:
                        auth.cambiar_clave(s, u, nueva)
                    if activo != u.activo:
                        auth.fijar_activo(s, u.id, activo, contexto.id_usuario())
                sesion.refrescar_credenciales()
                st.success("Cambios guardados.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
