"""Herramientas de fiabilidad [12.H]: tabla de mortalidad, modelo exponencial y bloques serie/paralelo (UNIDAD 2).
Sirven para poblaciones numerosas de ítems iguales (motores, válvulas) y para enseñar con números propios."""

import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.datos.modelos import Activo
from circularis_rel.motor import kpis
from circularis_rel.servicios import panel
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.VER_PANEL_GERENCIAL)
st.header("🧮 Herramientas de fiabilidad")
st.caption("El papel de Weibull para practicar con datos propios está en **Papel de Weibull**.")
tab_mort, tab_exp, tab_bloques = st.tabs(["Tabla de mortalidad", "Modelo exponencial", "Bloques serie y paralelo"])

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

with tab_bloques:
    st.caption("Confiabilidad de un conjunto (UNIDAD 2, diap. 7–10). En **serie** todos tienen que andar: Rs = Π Rj. En "
               "**paralelo** alcanza con uno: Rp = 1 − Π(1 − Rj). Cada grupo es un bloque o varios en paralelo, y los "
               "grupos van en serie. Declarar paralelo solo lo que de verdad se reemplaza entre sí (no se supone).")
    db = contexto.db()
    tz = contexto.config().zona_horaria
    with db.lectura() as s:
        activos = list(s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo)))
    codigo = st.selectbox("Precargar con los componentes críticos de", ["(ninguna)", *[a.codigo for a in activos]])
    filas_bloques = [{"grupo": 1, "bloque": "A", "R": 0.95}, {"grupo": 2, "bloque": "B", "R": 0.90},
                     {"grupo": 2, "bloque": "C", "R": 0.90}]
    if codigo != "(ninguna)":
        with db.lectura() as s:
            a = next(x for x in activos if x.codigo == codigo)
            comps = [c for c in panel.componentes(s, a.id) if c.critica and c.p is not None]
        filas_bloques = [{"grupo": i + 1, "bloque": c.codigo, "R": round(1 - c.p, 4)} for i, c in enumerate(comps)] or filas_bloques
        if comps:
            st.caption("R de cada componente = 1 − P(falla hasta la próxima parada), del semáforo de hoy.")
    datos_b = st.data_editor(filas_bloques, num_rows="dynamic", width="stretch", key=f"bloques_{codigo}",
                             column_config={"grupo": "Grupo (en serie)", "bloque": "Bloque",
                                            "R": st.column_config.NumberColumn("Confiabilidad R", min_value=0.0, max_value=1.0)})
    grupos: dict = {}
    for f in datos_b:
        if f.get("grupo") is not None and f.get("R") is not None:
            grupos.setdefault(f["grupo"], []).append(float(f["R"]))
    if grupos:
        arbol = ("serie", [("paralelo", rs) if len(rs) > 1 else rs[0] for _g, rs in sorted(grupos.items())])
        st.metric("Confiabilidad del conjunto", A.porcentaje(kpis.mixta(arbol), 2))
        st.caption(" · ".join(f"Grupo {g}: " + (f"paralelo de {len(rs)} → {A.porcentaje(kpis.paralelo(rs), 2)}" if len(rs) > 1
                                                  else A.porcentaje(rs[0], 2)) for g, rs in sorted(grupos.items())))
