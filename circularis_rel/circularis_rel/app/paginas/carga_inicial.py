"""Carga de planillas (importador): simular primero, después importar. Todo o nada."""

import hashlib
import tempfile
from pathlib import Path

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.config import RAIZ_PROYECTO
from circularis_rel.servicios.importador.aplicar import importar
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.CONFIGURAR)
st.header("Carga de planillas")
st.caption("Primero **Simular**: valida todo y muestra los errores fila por fila sin grabar. "
           "**Importar** se habilita cuando la simulación del mismo archivo no tiene errores. "
           "Re-importar el mismo libro no duplica nada.")

with st.expander("Plantillas y formato"):
    plantillas = RAIZ_PROYECTO / "docs" / "plantillas"
    for archivo in ("carga_inicial.xlsx", "historico.xlsx", "carga_inicial_borrador_TP1.xlsx"):
        if (plantillas / archivo).exists():
            st.download_button(archivo, (plantillas / archivo).read_bytes(), file_name=archivo)
    if (plantillas / "FORMATO.md").exists():
        st.markdown((plantillas / "FORMATO.md").read_text(encoding="utf-8"))

tipo = st.radio("Tipo de planilla", ["Carga inicial", "Histórico (triage A/B/C)"], horizontal=True)
archivo = st.file_uploader("Planilla Excel", type=["xlsx"])
if archivo is None:
    st.stop()

contenido = archivo.getvalue()
huella = hashlib.sha256(contenido + tipo.encode()).hexdigest()
historico = tipo.startswith("Histórico")


def correr(simular: bool):
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / archivo.name
        ruta.write_bytes(contenido)
        return importar(contexto.db(), ruta, simular=simular, usuario_id=contexto.id_usuario(), historico=historico)


c1, c2 = st.columns(2)
reporte = None
if c1.button("Simular", width="stretch", type="primary"):
    reporte = correr(True)
    st.session_state["simulacion_ok"] = huella if reporte.ok else None
puede_importar = st.session_state.get("simulacion_ok") == huella
if c2.button("Importar", width="stretch", disabled=not puede_importar,
             help=None if puede_importar else "Primero simulá este archivo sin errores"):
    reporte = correr(False)
    st.session_state["simulacion_ok"] = None

if reporte is not None:
    if reporte.aplicado:
        st.success("Importación aplicada.")
    elif reporte.simulado and reporte.ok:
        st.success("Simulación sin errores. Ya podés importar.")
    else:
        st.error(f"Hay {len(reporte.errores)} errores: no se grabó nada.")
    st.dataframe([{"Hoja": h, "Nuevos": r.creados, "Actualizados": r.actualizados, "Sin cambios": r.sin_cambios}
                  for h, r in reporte.hojas.items()], hide_index=True, width="stretch")
    if reporte.errores:
        st.subheader("Errores")
        for e in reporte.errores[:300]:
            st.markdown(f"- {e}")
    if reporte.advertencias:
        st.subheader("Advertencias")
        for a in reporte.advertencias[:300]:
            st.markdown(f"- {a}")
