"""Bandeja del encargado: avisos abiertos por prioridad, tarjetas, partes faltantes y alertas."""

from datetime import timedelta

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.enums import ColorTarjeta, EstadoEvento, EstadoTarjeta
from circularis_rel.datos.modelos import Activo, Catalogo, EventoFalla, TarjetaTPM, Usuario
from circularis_rel.servicios import alertas, faltantes, ot, registro
from circularis_rel.servicios.permisos import Accion, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.CERRAR_OT)
db = contexto.db()
tz = contexto.config().zona_horaria
st.header("📋 Bandeja del encargado")
F.mensaje_ok("bandeja")

ABIERTOS = [EstadoEvento.DEVUELTO, EstadoEvento.AVISADO, EstadoEvento.EN_REPARACION]
PRIORIDAD_CLASE = {"A": 0, "B": 1, "C": 2, None: 3}

with db.lectura() as s:
    filas = s.execute(select(EventoFalla, Activo, Catalogo.descripcion, Usuario.nombre)
                      .join(Activo, Activo.id == EventoFalla.id_activo)
                      .outerjoin(Catalogo, Catalogo.id == EventoFalla.id_sintoma)
                      .outerjoin(Usuario, Usuario.id == EventoFalla.id_usuario_alta)
                      .where(EventoFalla.estado.in_(ABIERTOS))).all()
filas.sort(key=lambda f: (f[0].estado != EstadoEvento.DEVUELTO,
                          PRIORIDAD_CLASE.get(f[1].criticidad_clase.value if f[1].criticidad_clase else None),
                          f[0].parada_total is False, f[0].fecha_hora_falla))

st.subheader(f"Avisos abiertos ({len(filas)})")
if not filas:
    st.success("No hay avisos abiertos.")
for ev, a, sintoma, quien in filas:
    with st.container(border=True):
        estado = {"DEVUELTO": "🔁 Devuelto por el jefe", "AVISADO": "🆕 Nuevo", "EN_REPARACION": "🔧 En reparación"}[ev.estado]
        st.markdown(f"**{a.codigo} · {a.nombre}** — {estado} — clase {a.criticidad_clase.value if a.criticidad_clase else '—'}")
        st.write(f"{sintoma or 'Sin síntoma'} · {'paró la máquina' if ev.parada_total is not False else 'sigue andando'} · "
                 f"{ev.fecha_hora_falla.astimezone(tz):%d/%m %H:%M} · avisó {quien or '—'} · aviso n.º {ev.id}")
        if ev.observaciones:
            st.caption(ev.observaciones)
        if ev.foto:
            ruta = contexto.config().dir_fotos / ev.foto
            if ruta.exists():
                st.image(str(ruta), width=220)
        c1, c2 = st.columns(2)
        if ev.estado == EstadoEvento.AVISADO and c1.button("Tomar", key=f"tomar_{ev.id}", width="stretch"):
            with db.escritura(usuario_id=u["id"]) as s:
                ot.tomar_aviso(s, u["id"], ev.id)
            st.rerun()
        if c2.button("Cerrar OT", key=f"cerrar_{ev.id}", type="primary", width="stretch"):
            st.session_state["evento_a_cerrar"] = ev.id
            st.switch_page("paginas/cerrar_ot.py")

with db.lectura() as s:
    tarjetas = s.execute(select(TarjetaTPM, Activo.codigo).join(Activo, Activo.id == TarjetaTPM.id_activo)
                         .where(TarjetaTPM.estado == EstadoTarjeta.ABIERTA).order_by(TarjetaTPM.creado_en)).all()
    ayer = F.hoy() - timedelta(days=1)
    falta = faltantes.faltantes(s, ayer, ayer)
    avisos_sistema = alertas.abiertas(s, "ENCARGADO")

st.subheader(f"Tarjetas abiertas ({len(tarjetas)})")
for t, cod in tarjetas:
    color = {"AZUL": "🟦", "VERDE": "🟩", "ROJA": "🟥"}[t.color]
    c1, c2, c3 = st.columns([4, 1, 1])
    c1.write(f"{color} {cod} · {t.anomalia}{' · ' + t.observaciones if t.observaciones else ''}")
    if c2.button("Hecha" if t.color != ColorTarjeta.VERDE else "Aceptar", key=f"res_{t.id}"):
        with db.escritura(usuario_id=u["id"]) as s:
            registro.cerrar_tarjeta(s, u["id"], t.id, True)
        st.rerun()
    if c3.button("Descartar", key=f"des_{t.id}"):
        with db.escritura(usuario_id=u["id"]) as s:
            registro.cerrar_tarjeta(s, u["id"], t.id, False)
        st.rerun()

st.subheader(f"Partes faltantes de ayer ({len(falta)})")
for f in falta:
    st.write(f"⚠️ {f.codigo} · {f.turno} del {f.fecha:%d/%m}")
if avisos_sistema:
    st.subheader("Alertas")
    for al in avisos_sistema:
        st.warning(al.mensaje)
