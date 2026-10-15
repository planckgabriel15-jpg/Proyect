"""Puesta en marcha guiada [12.A]: las 14 etapas de la UNIDAD 6 en tres fases."""

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.asistente import etapas
from circularis_rel.config import RAIZ_PROYECTO
from circularis_rel.datos.enums import EstadoEtapa
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.PUESTA_EN_MARCHA)
db = contexto.db()

st.header("Puesta en marcha del mantenimiento")
st.caption("Secuencia de etapas de la UNIDAD 6 (Mgter. L. D. Torres): primero el sistema semiautomático con los "
           "equipos prioritarios, después los correctivos y el histórico, y recién con datos confiables el "
           "control predictivo y las alertas.")

with db.lectura() as s:
    lista = etapas.listar(s)
st.progress(etapas.progreso(lista), text=f"Avance: {etapas.progreso(lista):.0%}")

with st.expander("Antes de empezar: lo que cuesta informatizar (UNIDAD 6)"):
    for d in etapas.desventajas():
        st.markdown(f"- {d}")

plantillas = RAIZ_PROYECTO / "docs" / "plantillas"
c1, c2, c3 = st.columns(3)
for col, archivo, etiqueta in ((c1, "carga_inicial.xlsx", "Plantilla de carga inicial"),
                               (c2, "historico.xlsx", "Plantilla de histórico"),
                               (c3, "carga_inicial_borrador_TP1.xlsx", "Borrador con datos del TP N.º 1")):
    ruta = plantillas / archivo
    if ruta.exists():
        col.download_button(etiqueta, ruta.read_bytes(), file_name=archivo, width="stretch")

NOMBRES_FASE = {1: "Fase 1 · Sistema semiautomático con los equipos prioritarios",
                2: "Fase 2 · Correctivos e histórico (con la fase 1 estable)",
                3: "Fase 3 · Control predictivo y alertas (con datos suficientes y confiables)"}
ETIQUETAS = {EstadoEtapa.PENDIENTE: "Pendiente", EstadoEtapa.EN_CURSO: "En curso", EstadoEtapa.HECHA: "Hecha"}

for fase in (1, 2, 3):
    st.subheader(NOMBRES_FASE[fase])
    for e in (x for x in lista if x.fase == fase):
        icono = {True: "✅", False: "⚠️", None: "ℹ️"}[e.verificacion.cumple]
        with st.container(border=True):
            st.markdown(f"**{e.numero}. {e.titulo}**")
            st.write(e.que_es)
            st.caption(f"Por qué importa: {e.por_que}  ·  Dónde: {e.pantalla or '—'}")
            st.markdown(f"{icono} Control del sistema: {e.verificacion.detalle}")
            nuevo = st.radio("Estado", list(ETIQUETAS), index=list(ETIQUETAS).index(e.estado),
                             format_func=ETIQUETAS.get, horizontal=True, key=f"etapa_{e.numero}")
            if nuevo != e.estado:
                with db.escritura(usuario_id=contexto.id_usuario()) as s:
                    etapas.marcar(s, e.numero, nuevo, contexto.id_usuario())
                st.rerun()
