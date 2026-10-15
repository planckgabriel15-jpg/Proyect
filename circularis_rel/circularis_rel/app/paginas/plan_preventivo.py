"""Plan preventivo y calendario (jefe) [12.G; Plan §8]: intervalos, calendario de 52 semanas, OT preventivas
imprimibles, pruebas funcionales de fallas ocultas y diagnóstico de sobre y sub-mantenimiento."""

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.enums import ReglaPlan, TipoOT
from circularis_rel.datos.modelos import Activo, OrdenTrabajo, PosicionComponente
from circularis_rel.servicios import formatos_catedra as FC
from circularis_rel.servicios import plan_preventivo as PP
from circularis_rel.servicios import recalculo
from circularis_rel.servicios.permisos import Accion, puede, requerir
from circularis_rel.servicios.registro import ErrorRegistro

u = contexto.usuario()
requerir(u["rol"], Accion.CERRAR_OT)
es_jefe = puede(u["rol"], Accion.CONFIGURAR)
db = contexto.db()
tz = contexto.config().zona_horaria
hoy = F.hoy()
st.header("🗓️ Plan preventivo")
F.mensaje_ok("plan")

tabs = st.tabs(["Intervalos", "Calendario de 52 semanas", "Órdenes de trabajo", "Sobre y sub-mantenimiento"])

with db.lectura() as s:
    propuestas = PP.propuestas(s, hoy, tz)

with tabs[0]:
    st.caption("Mientras no hay datos se usa el intervalo del fabricante; cuando el componente tiene un Weibull de desgaste "
               "con confianza suficiente, el sistema propone el calculado. El plan aprobado manda sobre los dos.")
    A.boton("intervalo")
    st.dataframe([{"Máquina": p.maquina, "Componente": p.componente, "Tipo": p.tipo,
                   "Vigente": (f"{p.plan.intervalo:g} ({p.plan.regla.value.lower().replace('_', ' ')})"
                               if p.plan and p.plan.intervalo else "—"),
                   "Fabricante": f"{p.fabricante:g}" if p.fabricante else "—",
                   "Calculado": f"{p.calculado:g}" if p.calculado else "—", "Confianza": p.confianza.capitalize(),
                   "Ahorro vs. hasta la falla": A.porcentaje(p.ahorro, 0) if p.ahorro is not None else "—",
                   "Sugerencia": p.sugerencia} for p in propuestas], hide_index=True, width="stretch")
    if es_jefe and propuestas:
        st.subheader("Aprobar un intervalo")
        etiquetas = {f"{p.maquina} · {p.componente} ({p.tipo})": p for p in propuestas}
        elegida = etiquetas[st.selectbox("Componente", list(etiquetas))]
        st.caption(elegida.texto_calculado)
        if elegida.falla_oculta:
            opciones = {"Prueba funcional periódica": ReglaPlan.PRUEBA_FUNCIONAL, "Sin plan": ReglaPlan.NINGUNO}
        else:
            opciones = {}
            if elegida.calculado:
                opciones[f"Calculado: {elegida.calculado:g} h"] = ReglaPlan(elegida.regla_calculada)
            if elegida.fabricante:
                opciones[f"Fabricante: {elegida.fabricante:g} h"] = ReglaPlan.FABRICANTE
            opciones["Otro valor (criterio del jefe)"] = ReglaPlan.FABRICANTE
            opciones["Sin preventivo por tiempo"] = ReglaPlan.NINGUNO
        with st.form("aprobar"):
            texto = st.radio("Regla", list(opciones))
            regla = opciones[texto]
            if regla == ReglaPlan.PRUEBA_FUNCIONAL:
                dias = st.number_input("Cada cuántos días se prueba", min_value=1, value=30, step=1)
                intervalo = dias * 24.0
            elif texto.startswith("Calculado"):
                intervalo = elegida.calculado
            elif texto.startswith("Fabricante"):
                intervalo = elegida.fabricante
            elif regla == ReglaPlan.NINGUNO:
                intervalo = None
            else:
                intervalo = st.number_input("Intervalo (h de uso)", min_value=1.0, value=elegida.fabricante or 500.0, step=25.0)
            if st.form_submit_button("Aprobar y reprogramar", type="primary", width="stretch"):
                try:
                    with db.escritura(usuario_id=u["id"], motivo=f"Plan preventivo: {texto}") as s:
                        PP.aprobar(s, u["id"], elegida.id_posicion, regla, intervalo, t_optimo=elegida.t_optimo,
                                   id_resultado=elegida.id_resultado if texto.startswith("Calculado") else None, desde=hoy)
                        PP.programar(s, hoy, tz)
                        recalculo.actualizar_estado(s, s.get(PosicionComponente, elegida.id_posicion), tz)
                    F.guardar_mensaje_ok("plan", "Plan aprobado y calendario reprogramado.")
                    st.rerun()
                except ErrorRegistro as e:
                    st.error(str(e))

with tabs[1]:
    c1, c2, c3 = st.columns(3)
    if es_jefe and c1.button("Reprogramar ahora", width="stretch"):
        with db.escritura(usuario_id=u["id"], motivo="Reprogramación del calendario") as s:
            r = PP.programar(s, hoy, tz)
        F.guardar_mensaje_ok("plan", f"{r['intervenciones']} intervenciones de {r['planes']} planes.")
        st.rerun()
    with db.lectura() as s:
        filas = PP.calendario(s, hoy)
    c2.download_button("Calendario en PDF (1CMP001 y 2CMP001)", FC.pdf_calendario(filas, hoy), "calendario_preventivo.pdf",
                       "application/pdf", width="stretch")
    c3.download_button("Calendario en Excel", FC.excel_calendario(filas, hoy), "calendario_preventivo.xlsx", width="stretch")
    st.caption(f"Semana 1 = lunes {PP.lunes(hoy):%d/%m/%Y}. Se reprograma cada noche con la edad y el ritmo real de cada máquina.")
    if filas:
        st.dataframe([{"Máquina": f.maquina, "Tarea": f.tarea, "Tiempo (h)": f.tiempo_h,
                       **{str(n): ("X" if n in f.semanas else "") for n in range(1, 53)}} for f in filas],
                     hide_index=True, width="stretch")
    else:
        st.info("Sin intervenciones programadas: aprobá intervalos en la primera pestaña.")

with tabs[2]:
    st.caption("Las OT preventivas se generan solas con la anticipación del parámetro politicas.anticipacion_ot_dias. "
               "Al registrar el cambio en \"Cambio preventivo\", la OT planificada de ese componente se cierra.")
    if es_jefe and st.button("Generar las OT que corresponden ahora"):
        with db.escritura(usuario_id=u["id"], motivo="Generación de OT preventivas") as s:
            nuevas = PP.generar_ot(s, hoy)
        F.guardar_mensaje_ok("plan", f"{len(nuevas)} OT generadas.")
        st.rerun()
    with db.lectura() as s:
        abiertas = [(o, s.get(Activo, o.id_activo).codigo, s.get(PosicionComponente, o.id_posicion).codigo if o.id_posicion else "—")
                    for o in s.scalars(select(OrdenTrabajo).where(OrdenTrabajo.tipo.in_([TipoOT.PREVENTIVA, TipoOT.PRUEBA_FUNCIONAL]),
                                                                  OrdenTrabajo.estado.in_(PP.ABIERTAS))
                                       .order_by(OrdenTrabajo.fecha_programada))]
    if not abiertas:
        st.info("No hay OT preventivas abiertas.")
    for o, maquina, componente in abiertas:
        with st.container(border=True):
            vencida = o.fecha_programada and o.fecha_programada < hoy
            st.markdown(f"**{o.numero}** · {maquina} · {componente} · {o.tipo.value.replace('_', ' ').lower()} · "
                        f"{'⚠️ vencida ' if vencida else ''}para el {o.fecha_programada:%d/%m/%Y}")
            c1, c2 = st.columns(2)
            with db.lectura() as s:
                c1.download_button("Imprimir OT (MANT/MPV001)", FC.pdf_ot_preventiva(s, o.id, tz), f"{o.numero}.pdf",
                                   "application/pdf", key=f"pdf_{o.id}", width="stretch")
            if o.tipo == TipoOT.PRUEBA_FUNCIONAL:
                with c2.popover("Registrar resultado", width="stretch"):
                    actuo = st.radio("¿Actuó?", ["Sí, actuó bien", "No actuó"], key=f"actuo_{o.id}")
                    hh = st.number_input("Horas-hombre", min_value=0.0, value=None, step=0.5, key=f"hh_{o.id}")
                    obs = st.text_input("Observaciones", key=f"obs_{o.id}")
                    if st.button("Cerrar prueba", key=f"cerrar_{o.id}", type="primary"):
                        try:
                            with db.escritura(usuario_id=u["id"]) as s:
                                PP.cerrar_prueba_funcional(s, u["id"], o.id, F.ahora_local(), actuo.startswith("Sí"), hh, obs)
                            F.guardar_mensaje_ok("plan", "Prueba registrada." + ("" if actuo.startswith("Sí") else
                                                 " Quedó el aviso de falla para el encargado."))
                            st.rerun()
                        except ErrorRegistro as e:
                            st.error(str(e))

with tabs[3]:
    st.caption("UNIDAD 3: **sobre-mantenimiento** = el preventivo corta la vida útil sin causa (o se cambia por tiempo algo "
               "que falla al azar); **sub-mantenimiento** = el intervalo es largo y el correctivo le gana al preventivo.")
    con = [p for p in propuestas if p.diagnostico]
    if not con:
        st.success("Sin indicios de sobre ni de sub-mantenimiento con los datos actuales.")
    for p in con:
        with st.container(border=True):
            st.markdown(f"**{p.maquina} · {p.componente}** ({p.tipo})")
            for d in p.diagnostico:
                st.warning(d)
    A.boton("costo_t")
