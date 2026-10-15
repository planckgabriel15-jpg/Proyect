"""Reportes (jefe y gerencia; Plan §10, pantalla 13): PDF del mes o de un período, y los reportes mensuales guardados."""

from datetime import date, timedelta

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.servicios import panel, reporte
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.VER_PANEL_GERENCIAL)
db = contexto.db()
cfg = contexto.config()
hoy = F.hoy()
st.header("🧾 Reportes")
st.caption("El reporte resume el panel: KPIs de la línea, estado de las máquinas, ranking de riesgo, Pareto, tablero de "
           "comando, alertas y calidad de los datos. El del mes se genera solo el día 1 y, si hay correo configurado, "
           "se manda al jefe y a la gerencia.")

periodos = list(reversed(panel.meses(date(hoy.year - 1, hoy.month, 1), hoy)))
c1, c2 = st.columns(2)
periodo = c1.selectbox("Mes", periodos, index=1 if len(periodos) > 1 else 0)
anio, mes = (int(x) for x in periodo.split("-"))
desde = date(anio, mes, 1)
hasta = min(hoy, date(anio + (mes == 12), mes % 12 + 1, 1) - timedelta(days=1))
if c2.button("Generar el PDF del mes", width="stretch", type="primary"):
    with st.spinner("Armando el reporte..."), db.lectura() as s:
        st.session_state["reporte_pdf"] = (periodo, reporte.pdf(s, desde, hasta, cfg.zona_horaria, "Reporte de mantenimiento"))
if st.session_state.get("reporte_pdf", (None,))[0] == periodo:
    st.download_button(f"Descargar el reporte de {periodo}", st.session_state["reporte_pdf"][1], f"reporte_{periodo}.pdf",
                       "application/pdf", width="stretch")

guardados = sorted(cfg.dir_reportes.glob("reporte_*.pdf"), reverse=True) if cfg.dir_reportes.exists() else []
if guardados:
    st.subheader("Reportes mensuales guardados")
    for archivo in guardados[:24]:
        st.download_button(archivo.stem.replace("_", " ").capitalize(), archivo.read_bytes(), archivo.name, "application/pdf",
                           key=archivo.name)
st.caption("La ficha de cada máquina (MANT/RHM001) está en Máquinas y revisión; la exportación total a Excel, en Exportar.")
