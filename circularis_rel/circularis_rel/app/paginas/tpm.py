"""TPM y OEE [12.F]: rendimiento operacional RO = Dp · Di · Rv · Tq y las seis grandes pérdidas (UNIDAD 4)."""

from datetime import timedelta

import plotly.graph_objects as go
import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import formularios as F
from circularis_rel.servicios import tpm
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.VER_PANEL_GERENCIAL)
db = contexto.db()
hoy = F.hoy()
st.header("⚙️ TPM: rendimiento operacional y seis grandes pérdidas")
with st.expander("Cómo se calcula (UNIDAD 4, con las correcciones B-003 a B-005)"):
    st.markdown("- **Dp** (disponibilidad propia) = TR / TT, con TT = tiempo requerido y TR = TT − preparación y ajuste.\n"
                "- **Di** (disponibilidad intrínseca) = (TR − paradas imprevistas) / TR.\n"
                "- **Rv** (relación de velocidad) = ciclo teórico / ciclo real (≤ 1).\n"
                "- **Tq** (tasa de calidad) = (piezas realizadas − rechazadas) / realizadas.\n"
                "- **RO** = Dp · Di · Rv · Tq. Hace falta cargar la cantidad y las rechazadas en el parte y el ciclo "
                "teórico de la máquina; si no, queda \"falta dato\".")
dias = st.segmented_control("Período", [30, 90, 365], default=30, format_func=lambda d: f"Últimos {d} días", key="tpm_dias") or 30
with db.lectura() as s:
    filas = tpm.linea(s, hoy - timedelta(days=dias), hoy)
st.dataframe([{"Máquina": r.codigo, "Dp": A.porcentaje(r.dp), "Di": A.porcentaje(r.di), "Rv": A.porcentaje(r.rv),
               "Tq": A.porcentaje(r.tq), "RO": A.porcentaje(r.ro), "Falta": ", ".join(r.faltan)} for r in filas],
             hide_index=True, width="stretch")
perdidas: dict[str, float] = {}
for r in filas:
    for k, v in r.perdidas_h.items():
        perdidas[k] = perdidas.get(k, 0.0) + v
orden = sorted(((k, v) for k, v in perdidas.items() if v > 0), key=lambda kv: -kv[1])
if orden:
    fig = go.Figure(go.Bar(x=[k for k, _ in orden], y=[v for _, v in orden], marker_color="#d93025"))
    fig.update_layout(title="Seis grandes pérdidas de la línea (horas)", yaxis_title="h", height=380,
                      margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Velocidad reducida y calidad se estiman con Rv y Tq; si faltan, esas pérdidas no aparecen. Las paradas "
               "con un motivo sin categoría van a \"sin clasificar\" (se asigna en Catálogos › Motivos de parada).")
else:
    st.info("Sin pérdidas registradas en el período.")
