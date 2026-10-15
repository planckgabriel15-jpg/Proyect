"""Histórico: resultado del triage A/B/C (Plan §11). Nunca entra directo al cálculo."""

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.datos.modelos import Activo, Catalogo, PosicionComponente, VidaHistorica
from circularis_rel.servicios.formato import fecha, numero
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.CONFIGURAR)
st.header("Histórico de fallas y cambios")
st.caption("A = confiable (vida con horas nivel E) · B = parcial (censura por intervalo, solo MLE) · "
           "C = no usable (solo Pareto cualitativo). Se carga en **Carga de planillas** → Histórico.")

with contexto.db().lectura() as s:
    filas = s.execute(
        select(VidaHistorica, Activo.codigo, PosicionComponente.codigo, Catalogo.descripcion)
        .join(Activo, Activo.id == VidaHistorica.id_activo)
        .outerjoin(PosicionComponente, PosicionComponente.id == VidaHistorica.id_posicion)
        .outerjoin(Catalogo, Catalogo.id == VidaHistorica.id_modo_falla)
        .order_by(Activo.codigo, VidaHistorica.fecha_fin)).all()

if not filas:
    st.info("Todavía no se cargó histórico.")
    st.stop()

c1, c2, c3 = st.columns(3)
for col, clase in zip((c1, c2, c3), ("A", "B", "C"), strict=True):
    col.metric(f"Clase {clase}", sum(1 for v, *_ in filas if v.clase_triage == clase))

clases = st.multiselect("Clases", ["A", "B", "C"], default=["A", "B", "C"])
maquinas = sorted({m for _, m, _, _ in filas})
elegidas = st.multiselect("Máquinas", maquinas, default=maquinas)
st.dataframe([{
    "Máquina": m, "Posición": p or "—", "Fin": v.tipo_fin.value, "Modo": modo or "—",
    "Fecha": fecha(v.fecha_fin) or (f"{fecha(v.fecha_fin_inf)} a {fecha(v.fecha_fin_sup)}" if v.fecha_fin_inf else "—"),
    "Edad (h)": numero(v.edad_horas, 0) if v.edad_horas is not None else (
        f"{numero(v.edad_inf_h, 0)} a {numero(v.edad_sup_h, 0)}" if v.edad_inf_h is not None else "—"),
    "Clase": v.clase_triage.value, "Motivo": v.motivo_clase, "Fuente": v.fuente, "Respaldo": v.respaldo or "",
} for v, m, p, modo in filas if v.clase_triage in clases and m in elegidas], hide_index=True, use_container_width=True)
