"""Criticidad guiada [12.C]: seis preguntas por máquina, con el método del TP o la ponderación U1."""

from datetime import timedelta

import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.asistente import criticidad as AC
from circularis_rel.datos.enums import MetodoCriticidad
from circularis_rel.datos.modelos import Activo
from circularis_rel.servicios import criticidad as SC
from circularis_rel.servicios import panel
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.permisos import Accion, requerir
from circularis_rel.servicios.registro import ErrorRegistro

u = contexto.usuario()
requerir(u["rol"], Accion.CONFIGURAR)
db = contexto.db()
tz = contexto.config().zona_horaria
hoy = F.hoy()
st.header("⚖️ Criticidad de equipos")
st.caption("La clase A/B/C ordena dónde poner el esfuerzo primero: umbrales más exigentes del semáforo, "
           "preventivo por confiabilidad objetivo y stock de repuestos.")
F.mensaje_ok("criticidad")

with db.lectura() as s:
    activos = list(s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo)))
    escalas_u1 = P.obtener(s, "criticidad.u1_escalas")
    cortes_u1 = P.obtener(s, "criticidad.u1_cortes")
    cortes_tp = P.obtener(s, "criticidad.tp_cortes")

st.dataframe([{"Máquina": a.codigo, "Nombre": a.nombre, "Clase": a.criticidad_clase.value if a.criticidad_clase else "—",
               "Nivel": a.criticidad_nivel or "—", "Puntaje": a.criticidad_puntaje,
               "Método": "TP" if a.criticidad_metodo == MetodoCriticidad.TP_6_CRITERIOS else
               "U1" if a.criticidad_metodo else "—"} for a in activos], hide_index=True, width="stretch")
if not activos:
    st.stop()

st.subheader("Evaluar una máquina")
codigos = [a.codigo for a in activos]
codigo = st.selectbox("Máquina", codigos, index=F.indice_maquina(codigos))
activo = next(a for a in activos if a.codigo == codigo)
metodo = st.segmented_control(
    "Método", [MetodoCriticidad.TP_6_CRITERIOS, MetodoCriticidad.PONDERACION_U1], default=MetodoCriticidad.TP_6_CRITERIOS,
    format_func=lambda m: "TP N.º 1 (predeterminado)" if m == MetodoCriticidad.TP_6_CRITERIOS else "Ponderación UNIDAD 1",
    key="crit_metodo") or MetodoCriticidad.TP_6_CRITERIOS
if metodo == MetodoCriticidad.PONDERACION_U1:
    st.warning("Escalas de la UNIDAD 1 citadas en el pedido, **a verificar** contra las diapositivas (no se recibió la "
               "UNIDAD 1). Se editan en Parámetros (criticidad.u1_escalas)."
               + ("" if cortes_u1 else " Sin cortes cargados (criticidad.u1_cortes): la clase la elegís vos."))
else:
    st.caption(f"Suma de los seis criterios. Cortes del TP: ≥ {cortes_tp['Alta']} Alta; ≥ {cortes_tp['Media']} Media; "
               f"≥ {cortes_tp['Baja']} Baja; menos, Muy baja.")
try:
    ops = AC.opciones(metodo.value, escalas_u1)
except ValueError as e:
    st.error(f"Las escalas cargadas no coinciden con las opciones: {e}")
    st.stop()
anteriores = {}
with db.lectura() as s:
    hist = SC.historial(s, activo.id)
    if hist and hist[0].metodo == metodo:
        anteriores = hist[0].criterios
valores = {}
for c in AC.CRITERIOS:
    opciones = ops[c]
    previo = anteriores.get(c)
    indice = next((i for i, (v, _t) in enumerate(opciones) if v == previo), None)
    elegido = st.radio(f"**{AC.PREGUNTAS[c]}**", range(len(opciones)), index=indice,
                       format_func=lambda i, o=opciones: f"{o[i][1]} ({o[i][0]})", horizontal=True, key=f"crit_{c}_{metodo}")
    if elegido is not None:
        valores[c] = opciones[elegido][0]

if len(valores) == len(AC.CRITERIOS):
    with db.lectura() as s:
        r = SC.calcular(s, metodo, valores)
    c1, c2, c3 = st.columns(3)
    c1.metric("Puntaje", f"{r.puntaje:.0f}")
    c2.metric("Nivel", r.nivel or "—")
    c3.metric("Clase calculada", r.clase or "elegir")
    manual = None
    if not r.clase:
        manual = st.radio("Clase", ["A", "B", "C"], horizontal=True, index=None)
    elif st.checkbox("Cambiar la clase a mano"):
        manual = st.radio("Clase", ["A", "B", "C"], horizontal=True, index=["A", "B", "C"].index(r.clase))
    if st.button("Guardar evaluación", type="primary", width="stretch"):
        try:
            with db.escritura(usuario_id=u["id"], motivo="Evaluación de criticidad") as s:
                SC.guardar(s, u["id"], activo.id, metodo, valores, manual if manual != r.clase else None)
            F.guardar_mensaje_ok("criticidad", f"{codigo}: criticidad guardada.")
            st.rerun()
        except ErrorRegistro as e:
            st.error(str(e))
else:
    st.caption("Respondé las seis preguntas.")

if hist:
    with st.expander("Evaluaciones anteriores"):
        st.dataframe([{"Fecha": f"{h.fecha:%d/%m/%Y}", "Método": "TP" if h.metodo == MetodoCriticidad.TP_6_CRITERIOS else "U1",
                       "Puntaje": h.puntaje, "Clase": h.clase.value, "Vigente": "Sí" if h.vigente else ""} for h in hist],
                     hide_index=True, width="stretch")

st.subheader("Clasificación de las fallas (último año)")
st.caption("Por forma de aparición y capacidad. Las progresivas se pueden anticipar con inspección o predictivo; "
           "las repentinas y totales son las que más cuestan. Se cargan al cerrar la OT.")
with db.lectura() as s:
    q = panel.cuadrantes(s, hoy - timedelta(days=365), hoy, tz)
z = [[q["conteo"][("REPENTINA", "TOTAL")], q["conteo"][("PROGRESIVA", "TOTAL")]],
     [q["conteo"][("REPENTINA", "PARCIAL")], q["conteo"][("PROGRESIVA", "PARCIAL")]]]
fig = go.Figure(go.Heatmap(z=z, x=["Repentina", "Progresiva"], y=["Total", "Parcial"], text=z, texttemplate="%{text}",
                           colorscale="Reds", showscale=False))
fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, width="stretch")
if q["sin_clasificar"]:
    st.caption(f"{q['sin_clasificar']} falla(s) validada(s) sin clasificar.")
