"""Piloto (fase 2, Plan §10): partes por semana en las máquinas del piloto, criterio para pasar de fase y uso
de los catálogos para ajustarlos con el jefe."""

from datetime import timedelta

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import formularios as F
from circularis_rel.config import RAIZ_PROYECTO
from circularis_rel.servicios import piloto
from circularis_rel.servicios.permisos import Accion, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.CONFIGURAR)
db = contexto.db()
tz = contexto.config().zona_horaria
hoy = F.hoy()
st.header("🧪 Piloto")
st.caption("Uso real en las máquinas del piloto. Para pasar a la fase siguiente, el Plan pide dos semanas seguidas "
           "con más del 90 % de los partes completos (cargados por el operario; los estimados por el sistema no cuentan).")

with db.lectura() as s:
    e = piloto.estado(s, hoy, tz)
    uso = piloto.uso_catalogos(s, hoy - timedelta(days=90), hoy, tz)

if e.sin_maquinas_definidas:
    st.warning("Ninguna máquina del parámetro piloto.maquinas existe todavía"
               + (f" ({', '.join(e.faltan_codigos)})" if e.faltan_codigos else "") + ": se muestran todas.")
elif e.faltan_codigos:
    st.info(f"Del piloto todavía no están cargadas: {', '.join(e.faltan_codigos)}.")

if e.cumple:
    st.success(f"✅ Criterio cumplido: {e.semanas_requeridas} semanas seguidas con más del {A.porcentaje(e.minimo, 0)} "
               "de partes completos en todas las máquinas del piloto. Se puede extender al resto de la planta.")
else:
    st.warning(f"Todavía no: hacen falta {e.semanas_requeridas} semanas seguidas con más del {A.porcentaje(e.minimo, 0)} "
               "de partes completos en cada máquina del piloto.")

if e.maquinas:
    filas = []
    for m in e.maquinas:
        fila = {"Máquina": m.codigo, "Cumple": "✅" if m.cumple else "—"}
        for w in m.semanas:
            fila[f"Semana {w.inicio:%d/%m}"] = (f"{A.porcentaje(w.fraccion, 0)} ({w.del_operario}/{w.esperados})"
                                               if w.esperados else "sin turnos")
        fila["Validados en 48 h (4 semanas)"] = A.porcentaje(m.validados_48h, 0) if m.validados_48h is not None else "—"
        fila["Cerrados sin validar"] = m.avisos_sin_validar
        filas.append(fila)
    st.dataframe(filas, hide_index=True, width="stretch")

st.subheader("Uso de los catálogos (últimos 90 días)")
st.caption("Lo que nunca se usa puede sobrar; si se carga mucho \"Otro\", falta una opción. Se ajustan en Catálogos.")
nombres = {"SINTOMA": "Síntomas", "MODO": "Modos de falla", "CAUSA": "Causas", "MOTIVO": "Motivos de parada"}
for col, (clave, titulo) in zip(st.columns(2) * 2, nombres.items(), strict=False):
    with col:
        st.markdown(f"**{titulo}**")
        st.dataframe([{"Código": x["codigo"], "Descripción": x["descripcion"], "Usos": x["usos"],
                       "Activo": "Sí" if x["activo"] else "No"} for x in uso[clave]], hide_index=True, width="stretch",
                     height=250)

guion = RAIZ_PROYECTO / "docs" / "guion_piloto.md"
if guion.exists():
    with st.expander("Guion del piloto"):
        st.markdown(guion.read_text(encoding="utf-8"))
