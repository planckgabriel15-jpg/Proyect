"""Cerrar OT correctiva en dos pasos de hasta 6 campos (D-010)."""

from datetime import timedelta

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.enums import (
    AccionOT,
    AparicionFalla,
    CapacidadFalla,
    EfectoFalla,
    EstadoEvento,
)
from circularis_rel.datos.modelos import (
    Activo,
    EventoFalla,
    PosicionComponente,
    Repuesto,
    TipoComponente,
)
from circularis_rel.servicios import ot, registro
from circularis_rel.servicios.permisos import Accion, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.CERRAR_OT)
db = contexto.db()
tz = contexto.config().zona_horaria
st.header("🔧 Cerrar OT")
F.mensaje_ok("cierre")

with db.lectura() as s:
    abiertos = s.execute(select(EventoFalla, Activo).join(Activo, Activo.id == EventoFalla.id_activo).where(
        EventoFalla.estado.in_([EstadoEvento.AVISADO, EstadoEvento.EN_REPARACION, EstadoEvento.DEVUELTO]))
        .order_by(EventoFalla.fecha_hora_falla)).all()
if not abiertos:
    st.info("No hay avisos abiertos para cerrar.")
    st.stop()
ids = [ev.id for ev, _ in abiertos]
pre = st.session_state.get("evento_a_cerrar")
eid = st.selectbox("Aviso", ids, index=ids.index(pre) if pre in ids else 0,
                   format_func=lambda i: next(f"n.º {e.id} · {a.codigo} · {e.fecha_hora_falla.astimezone(tz):%d/%m %H:%M}"
                                              for e, a in abiertos if e.id == i))
ev, activo = next((e, a) for e, a in abiertos if e.id == eid)
falla_local = ev.fecha_hora_falla.astimezone(tz)
paso = st.session_state.get(f"paso_{eid}", 1)
st.progress(0.5 if paso == 1 else 1.0, text=f"Paso {paso} de 2")

if paso == 1:
    with db.lectura() as s:
        posiciones = {f"{p.codigo} · {t.nombre}": p.id for p, t in s.execute(
            select(PosicionComponente, TipoComponente).join(TipoComponente, TipoComponente.id == PosicionComponente.id_tipo_componente)
            .where(PosicionComponente.id_activo == activo.id, PosicionComponente.activa.is_(True)).order_by(PosicionComponente.codigo))}
    if not posiciones:
        st.error("La máquina no tiene componentes cargados.")
        st.stop()
    pos_txt = st.selectbox("Componente que falló", list(posiciones))
    id_pos = posiciones[pos_txt]
    with db.lectura() as s:
        modos = {m.descripcion: m.id for m in ot.modos_de_posicion(s, id_pos)}
        causas = {c.descripcion: c.id for c in ot.causas_de_posicion(s, id_pos)}
    if not modos:
        st.error("Ese componente no tiene modos de falla en el catálogo. El jefe los carga en la planilla (hoja 'modos').")
        st.stop()
    modo = st.selectbox("Modo de falla", list(modos))
    causa = st.selectbox("Causa", list(causas))
    ACCIONES = {"Reemplazo": AccionOT.REEMPLAZO, "Reparación": AccionOT.REPARACION_MINIMA, "Ajuste": AccionOT.AJUSTE}
    accion = st.segmented_control("Qué se hizo", list(ACCIONES), default="Reemplazo")
    c1, c2 = st.columns(2)
    ini_f = c1.date_input("Inicio de la reparación", falla_local.date(), format="DD/MM/YYYY")
    ini_h = c2.time_input("Hora de inicio", falla_local.time().replace(second=0, microsecond=0), step=300)
    ahora = F.ahora_local()
    c3, c4 = st.columns(2)
    fin_f = c3.date_input("Fin de la reparación", ahora.date(), format="DD/MM/YYYY")
    fin_h = c4.time_input("Hora de fin", ahora.time().replace(second=0, microsecond=0), step=300)
    if st.button("Siguiente", type="primary", width="stretch"):
        st.session_state[f"paso1_{eid}"] = dict(id_posicion=id_pos, id_modo=modos[modo], id_causa=causas[causa],
                                                accion=ACCIONES[accion or "Reemplazo"], inicio=F.combinar(ini_f, ini_h),
                                                fin=F.combinar(fin_f, fin_h))
        st.session_state[f"paso_{eid}"] = 2
        st.rerun()
else:
    p1 = st.session_state[f"paso1_{eid}"]
    st.caption(f"Reparación: {p1['inicio']:%d/%m %H:%M} → {p1['fin']:%d/%m %H:%M} "
               f"({(p1['fin'] - p1['inicio']) / timedelta(hours=1):.1f} h)")
    with db.lectura() as s:
        repuestos = {f"{r.codigo} · {r.descripcion}": r.id for r in s.scalars(select(Repuesto).order_by(Repuesto.codigo))}
    usados = st.multiselect("Repuestos usados", list(repuestos))
    cantidades = [(repuestos[r], st.number_input(f"Cantidad de {r}", min_value=0.0, value=1.0, step=1.0, key=f"c_{eid}_{r}"))
                  for r in usados]
    EFECTOS = {"Producción": EfectoFalla.PRODUCCION, "Calidad": EfectoFalla.CALIDAD, "Seguridad": EfectoFalla.SEGURIDAD,
               "Ambiente": EfectoFalla.AMBIENTE}
    efecto = st.segmented_control("Efecto de la falla", list(EFECTOS), default="Producción")
    capacidad = st.segmented_control("Pérdida de capacidad", ["Total", "Parcial"],
                                     default="Total" if ev.parada_total is not False else "Parcial")
    aparicion = st.segmented_control("Cómo apareció", ["Repentina", "Progresiva"], default="Repentina")
    hh = st.number_input("Horas-hombre", min_value=0.0, value=round((p1["fin"] - p1["inicio"]) / timedelta(hours=1), 1), step=0.5)
    c1, c2 = st.columns(2)
    if c1.button("Volver", width="stretch"):
        st.session_state[f"paso_{eid}"] = 1
        st.rerun()
    if c2.button("Cerrar OT", type="primary", width="stretch"):
        try:
            datos = ot.CierreOT(**p1, repuestos=cantidades, efecto=EFECTOS.get(efecto),
                                capacidad=CapacidadFalla.TOTAL if capacidad == "Total" else CapacidadFalla.PARCIAL,
                                aparicion=AparicionFalla.REPENTINA if aparicion == "Repentina" else AparicionFalla.PROGRESIVA,
                                hh=hh)
            with db.escritura(usuario_id=u["id"]) as s:
                ot.cerrar_correctiva(s, u["id"], eid, datos)
            for k in (f"paso_{eid}", f"paso1_{eid}", "evento_a_cerrar"):
                st.session_state.pop(k, None)
            F.guardar_mensaje_ok("cierre", f"OT del aviso n.º {eid} cerrada. Queda para validar por el jefe.")
            st.rerun()
        except (registro.ErrorRegistro, PermissionError) as e:
            st.error(str(e))
