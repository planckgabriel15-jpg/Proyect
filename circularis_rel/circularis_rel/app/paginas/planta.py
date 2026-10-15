"""Inicio de planta: dos botones grandes y el estado de las máquinas del usuario (sin costos)."""

import streamlit as st
from sqlalchemy import func, select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.enums import EstadoEvento
from circularis_rel.datos.modelos import EventoFalla, ParteTurno
from circularis_rel.servicios import registro

u = contexto.usuario()
st.header(f"Hola, {u['nombre'].split()[0]}")
F.mensaje_ok("planta")
c1, c2 = st.columns(2)
if c1.button("🛠️  Reportar falla", type="primary", width="stretch"):
    st.switch_page("paginas/reportar_falla.py")
if c2.button("📝  Parte de turno", type="primary", width="stretch"):
    st.switch_page("paginas/parte_turno.py")
if st.button("🏷️  Tarjeta (azul, roja o verde)", width="stretch"):
    st.switch_page("paginas/tarjeta.py")

with contexto.db().lectura() as s:
    maquinas = registro.maquinas_permitidas(s, u["id"])
    hoy = F.hoy()
    filas = []
    for a in maquinas:
        abiertos = s.scalar(select(func.count()).select_from(EventoFalla).where(
            EventoFalla.id_activo == a.id,
            EventoFalla.estado.in_([EstadoEvento.AVISADO, EstadoEvento.EN_REPARACION, EstadoEvento.DEVUELTO])))
        partes_hoy = s.scalar(select(func.count()).select_from(ParteTurno).where(ParteTurno.id_activo == a.id,
                                                                                 ParteTurno.fecha == hoy))
        filas.append({"Máquina": f"{a.codigo} · {a.nombre}", "Avisos abiertos": abiertos, "Partes de hoy": partes_hoy})
st.subheader("Mis máquinas" if u["rol"] == "OPERARIO" else "Máquinas")
st.dataframe(filas, hide_index=True, width="stretch")
