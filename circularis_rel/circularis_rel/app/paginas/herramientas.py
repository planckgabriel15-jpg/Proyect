"""Herramientas de fiabilidad [12.H]: tabla de mortalidad y modelo exponencial (UNIDAD 2). Sirven para poblaciones
numerosas de ítems iguales (motores, válvulas) y para enseñar los conceptos con números propios."""

import plotly.graph_objects as go
import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.motor import kpis
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.VER_PANEL_GERENCIAL)
st.header("🧮 Herramientas de fiabilidad")
tab_mort, tab_exp = st.tabs(["Tabla de mortalidad", "Modelo exponencial"])

with tab_mort:
    st.caption("Población de ítems idénticos que arrancan juntos: cuántos fallan en cada período. Da f(t), F(t), R(t), "
               "λ(t) y la vida media (MTTF = Σ t·n(t) / N). UNIDAD 2, diap. 11–13.")
    poblacion = st.number_input("Ítems al inicio (N)", min_value=1, value=180, step=1)
    st.caption("Ejemplo de la UNIDAD 2 (diap. 13): 180 motores; vida media 8,84 períodos. Editá la tabla con tus datos.")
    datos = st.data_editor([{"t": t, "fallados": n} for t, n in zip([7, 8, 9, 10, 11, 12], [18, 63, 53, 28, 12, 6], strict=True)],
                           num_rows="dynamic", column_config={"t": "Período t", "fallados": "Fallados en el período n(t)"},
                           width="stretch", key="mortalidad")
    filas_ok = [d for d in datos if d.get("t") is not None and d.get("fallados") is not None]
    total = sum(int(d["fallados"]) for d in filas_ok)
    if total > poblacion:
        st.error(f"Fallaron {total} ítems y la población es de {poblacion}")
    elif filas_ok:
        filas, mttf = kpis.tabla_mortalidad([float(d["t"]) for d in filas_ok], [int(d["fallados"]) for d in filas_ok], int(poblacion))
        st.dataframe([{"t": f.t, "n(t)": f.fallados, "N(t)": f.funcionando, "f(t)": round(f.f, 4), "F(t)": round(f.F, 4),
                       "R(t)": round(f.R, 4), "λ(t)": round(f.lam, 4) if f.lam is not None else None} for f in filas],
                     hide_index=True, width="stretch")
        st.metric("Vida media (MTTF)", A.numero(mttf, 2, "períodos"))
        if total < poblacion:
            st.caption(f"Quedan {poblacion - total} ítems sin fallar: la vida media calculada así los ignora (subestima).")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[f.t for f in filas], y=[f.R for f in filas], name="R(t)", line=dict(color="#1e8e3e")))
        fig.add_trace(go.Bar(x=[f.t for f in filas], y=[f.lam for f in filas], name="λ(t)", yaxis="y2", marker_color="#f28b82",
                             opacity=0.6))
        fig.update_layout(height=340, yaxis=dict(title="R(t)", tickformat=".0%"),
                          yaxis2=dict(title="λ(t)", overlaying="y", side="right", showgrid=False),
                          margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        st.caption("Si λ(t) crece con el tiempo hay desgaste; si es pareja, fallas al azar; si baja, fallas de juventud.")

with tab_exp:
    st.caption("Cuando la tasa de falla es constante (fallas al azar, β = 1): λ = fallas / (ítems × período) y R(t) = e^(−λt). "
               "UNIDAD 2: 2 válvulas falladas de 50 en un año dan λ = 0,04 por año.")
    c1, c2, c3 = st.columns(3)
    fallas = c1.number_input("Fallas en el período", min_value=0, value=2, step=1)
    unidades = c2.number_input("Ítems en servicio", min_value=1, value=50, step=1)
    t = c3.number_input("Tiempo a evaluar (en períodos)", min_value=0.0, value=0.5, step=0.25)
    lam = kpis.tasa_exponencial(int(fallas), int(unidades))
    r = kpis.confiabilidad_exponencial(t, lam)
    m = st.columns(3)
    m[0].metric("λ (por período)", A.numero(lam, 4))
    m[1].metric(f"R({t:g})", A.porcentaje(r, 2))
    m[2].metric("MTBF = 1/λ", A.numero(1 / lam, 1, "períodos") if lam else "sin fallas")
