"""Predictivo [12.G] (MANT/PMRED001): parámetros por máquina, mediciones, límites y tendencia. Es la herramienta
para los componentes que fallan al azar (β ≈ 1), donde el cambio por tiempo no sirve."""

from datetime import timedelta

import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.modelos import Activo, PredictivoParametro
from circularis_rel.servicios import formatos_catedra as FC
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios import predictivo as PR
from circularis_rel.servicios.permisos import Accion, puede, requerir
from circularis_rel.servicios.registro import ErrorRegistro

u = contexto.usuario()
requerir(u["rol"], Accion.CERRAR_OT)
es_jefe = puede(u["rol"], Accion.CONFIGURAR)
db = contexto.db()
tz = contexto.config().zona_horaria
st.header("📡 Mantenimiento predictivo")
st.caption("Medir la condición (vibración, temperatura, ultrasonido, corriente…) y actuar antes de la falla. Cada "
           "parámetro tiene límite de alerta y de acción; la tendencia estima cuánto falta para el límite.")
F.mensaje_ok("predictivo")

with db.lectura() as s:
    activos = list(s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo)))
    tabla_us = P.obtener(s, "predictivo.ultrasonido_rodamientos_db")
if not activos:
    st.info("No hay máquinas cargadas.")
    st.stop()
codigos = [a.codigo for a in activos]
codigo = st.selectbox("Máquina", codigos, index=F.indice_maquina(codigos))
activo = next(a for a in activos if a.codigo == codigo)
with db.lectura() as s:
    parametros = list(s.scalars(select(PredictivoParametro).where(PredictivoParametro.id_activo == activo.id,
                                                                  PredictivoParametro.activo.is_(True))
                                .order_by(PredictivoParametro.especialidad, PredictivoParametro.id)))
    datos = {p.id: (PR.historia(s, p.id), PR.tendencia_parametro(s, p)) for p in parametros}

if not parametros:
    st.info("Esta máquina no tiene parámetros predictivos." + (" Agregalos abajo." if es_jefe else " Los define el jefe."))

for p in parametros:
    medidas, tend = datos[p.id]
    with st.container(border=True):
        st.markdown(f"**{p.nombre}** ({p.unidad}) · {p.especialidad}"
                    + (" · plantilla ultrasonido" if p.plantilla == PR.PLANTILLA_ULTRASONIDO else ""))
        if medidas:
            ultima = medidas[-1]
            with db.lectura() as s:
                nivel, texto = PR.evaluar(s, p, ultima.valor)
            (st.error if nivel == "ACCION" else st.warning if nivel == "ALERTA" else st.success)(
                f"Última: {ultima.valor:g} {p.unidad} el {ultima.fecha.astimezone(tz):%d/%m/%Y}. {texto}")
            fig = go.Figure(go.Scatter(x=[m.fecha.astimezone(tz) for m in medidas], y=[m.valor for m in medidas],
                                       mode="lines+markers", name=p.nombre))
            for valor, nombre, color in ((p.linea_base, "Base", "#80868b"), (p.limite_alerta, "Alerta", "#f9ab00"),
                                         (p.limite_accion, "Acción", "#d93025")):
                if valor is not None:
                    fig.add_hline(y=valor, line_dash="dot", line_color=color, annotation_text=nombre)
            if tend is not None and tend.dias_hasta_limite not in (None, 0.0):
                fin = ultima.fecha + timedelta(days=tend.dias_hasta_limite)
                xs = [ultima.fecha, fin]
                ys = [tend.valor_actual_estimado, p.limite_accion]
                fig.add_trace(go.Scatter(x=[x.astimezone(tz) for x in xs], y=ys, mode="lines", name="Tendencia",
                                         line=dict(dash="dash", color="#d93025")))
                st.caption(f"Al ritmo actual ({tend.pendiente_por_dia:+.3g} {p.unidad}/día) llega al límite de acción en "
                           f"unos {tend.dias_hasta_limite:.0f} días (alrededor del {fin.astimezone(tz):%d/%m/%Y}). "
                           "Es una extrapolación: vale si la degradación sigue igual.")
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            st.plotly_chart(fig, width="stretch", key=f"g_{p.id}")
        with st.form(f"med_{p.id}"):
            c1, c2, c3 = st.columns(3)
            valor = c1.number_input(f"Medición ({p.unidad})", value=None, step=0.1, key=f"v_{p.id}")
            equipo = c2.text_input("Equipo de medición", key=f"e_{p.id}")
            ahora = F.ahora_local()
            fecha = c3.date_input("Fecha", ahora.date(), format="DD/MM/YYYY", key=f"f_{p.id}")
            if st.form_submit_button("Registrar medición", width="stretch"):
                if valor is None:
                    st.error("Cargá el valor medido")
                else:
                    try:
                        with db.escritura(usuario_id=u["id"]) as s:
                            ev = PR.registrar(s, u["id"], p.id, F.combinar(fecha, ahora.time()), valor, equipo)
                            ot_num = ev.ot.numero if ev.ot else None
                        F.guardar_mensaje_ok("predictivo", f"Medición registrada: {ev.texto}"
                                             + (f" Se generó la OT {ot_num}." if ot_num else ""))
                        st.rerun()
                    except ErrorRegistro as e:
                        st.error(str(e))

especialidades = sorted({p.especialidad for p in parametros if p.especialidad})
if especialidades:
    esp = st.selectbox("Imprimir la plantilla MANT/PMRED001 de", especialidades)
    with db.lectura() as s:
        st.download_button("Plantilla MANT/PMRED001 (PDF)", FC.pdf_predictivo(s, activo.id, esp, tz),
                           f"PMRED001_{activo.codigo}_{esp}.pdf", "application/pdf")

if es_jefe:
    st.subheader("Agregar un parámetro")
    with st.form("nuevo_param"):
        plantilla = st.radio("Tipo", ["Libre", "Ultrasonido en rodamientos (UNIDAD 3)"], horizontal=True)
        c1, c2, c3 = st.columns(3)
        especialidad = c1.text_input("Especialidad", "Ultrasonido" if plantilla.startswith("Ultra") else "",
                                     placeholder="Vibraciones, termografía, ultrasonido…")
        nombre = c2.text_input("Parámetro", placeholder="Ej.: vibración del rodamiento lado acople")
        unidad = c3.text_input("Unidad", "dB" if plantilla.startswith("Ultra") else "", placeholder="mm/s, °C, dB, A")
        c1, c2, c3 = st.columns(3)
        base = c1.number_input("Línea base (funcionamiento normal)", value=None, step=0.1)
        alerta = c2.number_input("Límite de alerta", value=None, step=0.1,
                                 help="Vacío en ultrasonido: base + primer umbral de la tabla")
        accion = c3.number_input("Límite de acción", value=None, step=0.1,
                                 help="Vacío en ultrasonido: base + umbral de 'falla'")
        if st.form_submit_button("Agregar", width="stretch"):
            try:
                with db.escritura(usuario_id=u["id"], motivo="Parámetro predictivo") as s:
                    PR.crear_parametro(s, u["id"], activo.id, especialidad, nombre, unidad, linea_base=base,
                                       limite_alerta=alerta, limite_accion=accion,
                                       plantilla=PR.PLANTILLA_ULTRASONIDO if plantilla.startswith("Ultra") else None)
                F.guardar_mensaje_ok("predictivo", "Parámetro agregado.")
                st.rerun()
            except ErrorRegistro as e:
                st.error(str(e))
    with st.expander("Tabla de referencia del ultrasonido en rodamientos (UNIDAD 3; no es norma)"):
        st.dataframe([{"Desde (dB sobre la base)": f["desde_db"], "Hasta": f["hasta_db"] or "—", "Estado": f["estado"],
                       "Acción": f["accion"]} for f in tabla_us], hide_index=True, width="stretch")
        st.caption("Se edita en Parámetros › predictivo.ultrasonido_rodamientos_db.")
