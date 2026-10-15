"""Parámetros: todo número configurable del sistema, con historia (vigente desde)."""

import json
from datetime import date

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.datos.enums import TipoParametro
from circularis_rel.datos.modelos import Parametro
from circularis_rel.servicios import modulos
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.CONFIGURAR)
db = contexto.db()
st.header("Parámetros")
st.caption("Umbrales, métodos, costos y plazos. Un valor vacío es **falta dato**: el sistema no lo reemplaza por cero. "
           "Cada cambio guarda la fecha desde la que vale y queda en la auditoría.")

with db.lectura() as s:
    claves = sorted(set(s.scalars(select(Parametro.clave))))
    vigentes = [P.registro_vigente(s, c) for c in claves]
grupos = sorted({p.grupo for p in vigentes})
grupo = st.radio("Grupo", grupos, horizontal=True)
del_grupo = [p for p in vigentes if p.grupo == grupo]
st.dataframe([{"Parámetro": p.clave, "Valor": p.valor if p.valor is not None else "falta dato", "Unidad": p.unidad or "",
               "Descripción": p.descripcion, "Fuente": p.fuente or "", "Desde": p.vigente_desde.strftime("%d/%m/%Y")}
              for p in del_grupo], hide_index=True, width="stretch")

elegido = st.selectbox("Modificar", del_grupo, format_func=lambda p: p.clave)
with st.form("param"):
    st.caption(elegido.descripcion)
    if elegido.tipo == TipoParametro.BOOL:
        valor = st.checkbox("Valor", value=elegido.valor == "1")
    elif elegido.tipo in (TipoParametro.ENTERO, TipoParametro.REAL):
        actual = float(elegido.valor) if elegido.valor is not None else None
        valor = st.number_input(f"Valor ({elegido.unidad or ''})", value=actual,
                                step=1.0 if elegido.tipo == TipoParametro.ENTERO else 0.01, format="%g")
        if valor is not None and elegido.tipo == TipoParametro.ENTERO:
            valor = int(valor)
    elif elegido.tipo == TipoParametro.JSON:
        texto = st.text_area("Valor (JSON)", json.dumps(json.loads(elegido.valor), ensure_ascii=False, indent=1)
                             if elegido.valor else "")
        valor = texto
    else:
        valor = st.text_input("Valor", elegido.valor or "")
    desde = st.date_input("Vale desde", date.today(), format="DD/MM/YYYY")
    if st.form_submit_button("Guardar", width="stretch"):
        try:
            if elegido.tipo == TipoParametro.JSON:
                valor = json.loads(valor) if valor.strip() else None
            with db.escritura(usuario_id=contexto.id_usuario(), motivo=f"Cambio de parámetro {elegido.clave}") as s:
                P.fijar(s, elegido.clave, valor if valor != "" else None, desde)
            st.success("Guardado.")
            st.rerun()
        except (ValueError, json.JSONDecodeError) as e:
            st.error(f"Valor no válido: {e}")

st.subheader("Módulos")
st.caption("Se habilitan a medida que la planta los necesita (UNIDAD 6: informatizar de a poco). Deshabilitar un módulo "
           "oculta sus pantallas; no borra datos.")
with db.lectura() as s:
    lista_modulos = modulos.todos(s)
with st.form("modulos"):
    nuevos = {m.codigo: st.checkbox(f"{m.codigo} · {m.nombre}", value=m.habilitado) for m in lista_modulos}
    if st.form_submit_button("Guardar módulos", width="stretch"):
        with db.escritura(usuario_id=contexto.id_usuario(), motivo="Módulos habilitados") as s:
            for codigo, valor in nuevos.items():
                modulos.fijar(s, codigo, valor)
        st.rerun()
