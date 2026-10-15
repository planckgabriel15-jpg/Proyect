"""Repuestos (jefe y encargado; Plan §8, UNIDAD 5): stock frente a la demanda esperada en el lead time, stock
mínimo por Poisson, lote económico y stock de protección."""

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.modelos import Repuesto
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios import repuestos as R
from circularis_rel.servicios.permisos import Accion, puede, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.GESTIONAR_REPUESTOS)
es_jefe = puede(u["rol"], Accion.CONFIGURAR)
db = contexto.db()
tz = contexto.config().zona_horaria
hoy = F.hoy()
st.header("📦 Repuestos")
F.mensaje_ok("repuestos")
with db.lectura() as s:
    lista = R.estado(s, hoy, tz)
    nivel = P.obtener(s, "politicas.nivel_servicio_stock")
st.caption(f"Demanda esperada en el lead time = probabilidad de falla de cada componente que usa el repuesto + preventivos "
           f"programados. Stock mínimo para un nivel de servicio del {A.porcentaje(nivel, 0)} (Poisson). Lote económico y "
           "stock de protección según la UNIDAD 5.")
bajos = [e for e in lista if e.bajo_minimo]
if bajos:
    st.error("Stock por debajo del mínimo: " + ", ".join(f"{e.codigo} ({e.stock:g} de {e.minimo_vigente:g})" for e in bajos))
st.dataframe([{"": "🔴" if e.bajo_minimo else "", "Código": e.codigo, "Descripción": e.descripcion,
               "Uso": (e.uso or "—").capitalize(), "Stock": e.stock, "Lead time (días)": e.lead_time_dias,
               "Demanda en el lead time": A.numero(e.demanda_lead, 2) if e.demanda_lead is not None else "—",
               "Mínimo calculado": e.stock_minimo, "Mínimo manual": e.stock_minimo_manual,
               "Demanda anual": A.numero(e.demanda_anual, 1) if e.demanda_anual else "—",
               "Lote económico": A.numero(e.lote_economico, 1) if e.lote_economico else "—",
               "Stock de protección": A.numero(e.stock_proteccion, 1) if e.stock_proteccion else "—",
               "Falta": ", ".join(e.faltan)} for e in lista], hide_index=True, width="stretch")

for e in lista:
    with st.expander(f"{e.codigo} · {e.descripcion}"):
        for d in e.detalle or ["Sin componentes asociados"]:
            st.write("• " + d)

if lista:
    st.subheader("Ajustar stock (conteo físico)")
    codigos = {f"{e.codigo} · {e.descripcion}": e for e in lista}
    with st.form("ajuste"):
        elegido = codigos[st.selectbox("Repuesto", list(codigos))]
        nuevo = st.number_input("Stock contado", min_value=0.0, value=float(elegido.stock or 0), step=1.0)
        manual = None
        if es_jefe:
            manual = st.number_input("Stock mínimo manual (vacío = usar el calculado)", min_value=0.0,
                                     value=elegido.stock_minimo_manual, step=1.0)
        motivo = st.text_input("Motivo", placeholder="Ej.: conteo mensual del depósito")
        if st.form_submit_button("Guardar", width="stretch"):
            try:
                with db.escritura(usuario_id=u["id"], motivo=motivo) as s:
                    R.ajustar_stock(s, elegido.id, nuevo, motivo)
                    if es_jefe:
                        s.get(Repuesto, elegido.id).stock_minimo_manual = manual
                F.guardar_mensaje_ok("repuestos", f"{elegido.codigo}: stock {nuevo:g}.")
                st.rerun()
            except ValueError as ex:
                st.error(str(ex))
