"""AMFE (jefe): matriz con NPR = G × O × D y ocurrencia O calculada con el Weibull (F de un año de uso)."""

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.servicios import amfe
from circularis_rel.servicios.permisos import Accion, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.CONFIGURAR)
db = contexto.db()
hoy = F.hoy()
st.header("🧯 AMFE")
st.caption("Gravedad (G), ocurrencia (O) y no detección (D) con las escalas del TP N.º 1; NPR = G × O × D. La **O calculada** "
           "sale del Weibull de cada componente: probabilidad de fallar en un año de uso, pasada a la escala con los cortes "
           "de Parámetros (amfe.escala_ocurrencia, propuesta a revisar). La O del TP es ilustrativa: adoptá la calculada "
           "cuando el componente tenga datos.")
F.mensaje_ok("amfe")
if st.button("Recalcular las O ahora"):
    with db.escritura(usuario_id=u["id"], motivo="Ocurrencia del AMFE") as s:
        n = amfe.actualizar_ocurrencias(s, hoy)
    F.guardar_mensaje_ok("amfe", f"{n} ocurrencias actualizadas.")
    st.rerun()
with db.lectura() as s:
    filas = amfe.filas(s, hoy)
if not filas:
    st.info("Sin ítems de AMFE: se cargan con la planilla (hoja amfe).")
    st.stop()
st.dataframe([{"Máquina": f.maquina, "Componente": f.componente, "Modo": f.modo, "G": f.g, "O": f.o, "D": f.d, "NPR": f.npr,
               "O calculada": f.o_calculada or "—", "NPR con O calculada": f.npr_calculado or "—", "AP": f.ap or "—",
               "Origen": f.origen.replace("_", " ").capitalize(), "Acciones": f.acciones or ""} for f in filas],
             hide_index=True, width="stretch")

st.subheader("Editar un ítem")
etiquetas = {f"{f.maquina} · {f.componente} · {f.modo}": f for f in filas}
f = etiquetas[st.selectbox("Ítem", list(etiquetas))]
st.caption(f.explicacion)
with st.form("amfe_item"):
    c1, c2, c3, c4 = st.columns(4)
    g = c1.number_input("G", 1, 10, f.g)
    o = c2.number_input("O", 1, 10, f.o_calculada if st.session_state.get("usar_calc") and f.o_calculada else f.o)
    d = c3.number_input("D", 1, 10, f.d)
    ap = c4.selectbox("AP (AIAG-VDA, a mano)", ["", "H", "M", "L"], index=["", "H", "M", "L"].index(f.ap or ""),
                      format_func=lambda x: x or "—")
    acciones = st.text_area("Acciones recomendadas", f.acciones or "")
    c1, c2 = st.columns(2)
    responsable = c1.text_input("Responsable")
    fecha = c2.date_input("Fecha", None, format="DD/MM/YYYY")
    if st.form_submit_button("Guardar", width="stretch"):
        try:
            with db.escritura(usuario_id=u["id"], motivo="Edición del AMFE") as s:
                amfe.editar(s, f.id, g=int(g), o=int(o), d=int(d), ap=ap, acciones=acciones, responsable=responsable,
                            fecha=fecha)
            F.guardar_mensaje_ok("amfe", "Ítem guardado.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
if f.o_calculada and f.o_calculada != f.o:
    st.checkbox(f"Usar la O calculada ({f.o_calculada}) en el formulario", key="usar_calc")
