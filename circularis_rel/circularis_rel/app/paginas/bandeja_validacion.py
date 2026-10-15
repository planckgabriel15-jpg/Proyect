"""Bandeja de validación del jefe: aprobar, devolver o anular, con las advertencias del sistema resaltadas.
Solo lo validado alimenta el cálculo."""

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.enums import EstadoEvento
from circularis_rel.datos.modelos import (
    Activo,
    Catalogo,
    EventoFalla,
    OrdenTrabajo,
    PosicionComponente,
    Usuario,
)
from circularis_rel.servicios import ot, registro, validacion
from circularis_rel.servicios.permisos import Accion, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.VALIDAR_EVENTO)
db = contexto.db()
tz = contexto.config().zona_horaria
st.header("✅ Bandeja de validación")
F.mensaje_ok("validacion")

with db.lectura() as s:
    items = validacion.bandeja(s, tz)
    detalles = {}
    for it in items:
        if it.tipo == "evento":
            ev = s.get(EventoFalla, it.id)
            nombre = lambda i: s.get(Catalogo, i).descripcion if i else "—"  # noqa: E731
            pos = s.get(PosicionComponente, ev.id_posicion)
            detalles[(it.tipo, it.id)] = {
                "Máquina": s.get(Activo, ev.id_activo).codigo, "Componente": pos.codigo if pos else "—",
                "Modo": nombre(ev.id_modo), "Causa": nombre(ev.id_causa), "Síntoma": nombre(ev.id_sintoma),
                "Falla": f"{ev.fecha_hora_falla.astimezone(tz):%d/%m %H:%M}",
                "Reparación (h)": ev.tiempo_reparacion_h, "Espera (h)": ev.tiempo_espera_h, "Parada (h)": ev.horas_parada,
                "Cerró": (s.get(Usuario, ev.id_usuario_cierre).nombre if ev.id_usuario_cierre else "—"),
            }
        else:
            o = s.get(OrdenTrabajo, it.id)
            pos = s.get(PosicionComponente, o.id_posicion) if o.id_posicion else None
            detalles[(it.tipo, it.id)] = {"OT": o.numero, "Tipo": o.tipo.value.capitalize(),
                                          "Máquina": s.get(Activo, o.id_activo).codigo,
                                          "Componente": pos.codigo if pos else "—",
                                          "Fecha": f"{(o.fin_real or o.creado_en).astimezone(tz):%d/%m %H:%M}", "HH": o.hh_propias}

st.caption(f"{len(items)} pendientes. Las advertencias no bloquean: son para mirar con atención antes de aprobar.")
for it in items:
    d = detalles[(it.tipo, it.id)]
    titulo = f"Aviso n.º {it.id}" if it.tipo == "evento" else d["OT"]
    with st.container(border=True):
        st.markdown(f"**{titulo} · {d['Máquina']}** · esperando {it.horas_espera:.0f} h")
        st.dataframe([d], hide_index=True, width="stretch")
        for a in it.advertencias:
            st.warning(a)
        c1, c2, c3 = st.columns(3)
        if c1.button("Aprobar", key=f"ok_{it.tipo}_{it.id}", type="primary", width="stretch"):
            with db.escritura(usuario_id=u["id"]) as s:
                if it.tipo == "evento":
                    validacion.validar_evento(s, u["id"], it.id)
                else:
                    validacion.validar_ot(s, u["id"], it.id)
            F.guardar_mensaje_ok("validacion", f"{titulo} validado: entra al cálculo.")
            st.rerun()
        if it.tipo == "evento":
            motivo = c2.text_input("Motivo", key=f"mot_{it.id}", label_visibility="collapsed", placeholder="Motivo para devolver o anular")
            if c2.button("Devolver", key=f"dev_{it.id}", width="stretch"):
                try:
                    with db.escritura(usuario_id=u["id"]) as s:
                        validacion.devolver_evento(s, u["id"], it.id, motivo)
                    st.rerun()
                except registro.ErrorRegistro as e:
                    st.error(str(e))
            if c3.button("Anular", key=f"anu_{it.id}", width="stretch"):
                try:
                    with db.escritura(usuario_id=u["id"], motivo=motivo) as s:
                        validacion.anular_evento(s, u["id"], it.id, motivo)
                    st.rerun()
                except registro.ErrorRegistro as e:
                    st.error(str(e))

with st.expander("Corregir un aviso ya validado (exige motivo)"):
    with db.lectura() as s:
        validados = s.execute(select(EventoFalla, Activo.codigo).join(Activo, Activo.id == EventoFalla.id_activo)
                              .where(EventoFalla.estado == EstadoEvento.VALIDADO)
                              .order_by(EventoFalla.fecha_hora_falla.desc()).limit(100)).all()
    if not validados:
        st.caption("No hay avisos validados.")
    else:
        eid = st.selectbox("Aviso", [e.id for e, _ in validados],
                           format_func=lambda i: next(f"n.º {e.id} · {c} · {e.fecha_hora_falla.astimezone(tz):%d/%m/%Y %H:%M}"
                                                      for e, c in validados if e.id == i))
        ev = next(e for e, _ in validados if e.id == eid)
        with db.lectura() as s:
            modos = {m.descripcion: m.id for m in ot.modos_de_posicion(s, ev.id_posicion)}
            causas = {c.descripcion: c.id for c in ot.causas_de_posicion(s, ev.id_posicion)}
        with st.form("corregir"):
            modo = st.selectbox("Modo", list(modos), index=list(modos.values()).index(ev.id_modo) if ev.id_modo in modos.values() else 0)
            causa = st.selectbox("Causa", list(causas), index=list(causas.values()).index(ev.id_causa) if ev.id_causa in causas.values() else 0)
            ini = ev.inicio_reparacion.astimezone(tz)
            fin = ev.fin_reparacion.astimezone(tz)
            c1, c2 = st.columns(2)
            ini_h = c1.time_input("Inicio de reparación", ini.time())
            fin_h = c2.time_input("Fin de reparación", fin.time())
            motivo = st.text_input("Motivo de la corrección (obligatorio)")
            if st.form_submit_button("Guardar corrección", width="stretch"):
                cambios = {"id_modo": modos[modo], "id_causa": causas[causa],
                           "inicio_reparacion": F.combinar(ini.date(), ini_h), "fin_reparacion": F.combinar(fin.date(), fin_h)}
                cambios = {k: v for k, v in cambios.items() if getattr(ev, k) != v}
                try:
                    with db.escritura(usuario_id=u["id"], motivo=motivo) as s:
                        validacion.corregir_evento(s, u["id"], eid, cambios, motivo)
                    F.guardar_mensaje_ok("validacion", f"Aviso n.º {eid} corregido.")
                    st.rerun()
                except registro.ErrorRegistro as e:
                    st.error(str(e))
