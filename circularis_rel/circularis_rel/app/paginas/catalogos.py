"""Catálogos (jefe): síntomas, modos de falla, causas y motivos de parada. Nada se borra: se desactiva."""

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import formularios as F
from circularis_rel.datos.enums import Categoria6P, TipoCatalogo
from circularis_rel.datos.modelos import Catalogo, CatalogoAplica, MotivoParada, TipoComponente
from circularis_rel.servicios import catalogos as C
from circularis_rel.servicios.permisos import Accion, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.CONFIGURAR)
db = contexto.db()
st.header("📚 Catálogos")
st.caption("Terminología única (UNIDAD 6): todos tienen que llamar igual a la misma falla. El código no cambia; la "
           "descripción sí. Lo que no se usa se desactiva (los registros viejos lo siguen mostrando). En "
           "**Piloto** se ve cuántas veces se usó cada opción.")
F.mensaje_ok("catalogos")

NOMBRES = {TipoCatalogo.SINTOMA: "Síntomas", TipoCatalogo.MODO: "Modos de falla", TipoCatalogo.CAUSA: "Causas"}
tabs = st.tabs([*NOMBRES.values(), "Motivos de parada"])

with db.lectura() as s:
    tipos = {t.id: f"{t.codigo} · {t.nombre}" for t in s.scalars(select(TipoComponente).order_by(TipoComponente.codigo))}
    aplica: dict[int, list[int]] = {}
    for c, t in s.execute(select(CatalogoAplica.id_catalogo, CatalogoAplica.id_tipo_componente)):
        aplica.setdefault(c, []).append(t)
    items = {tipo: list(s.scalars(select(Catalogo).where(Catalogo.tipo == tipo).order_by(Catalogo.codigo))) for tipo in NOMBRES}
    motivos = list(s.scalars(select(MotivoParada).order_by(MotivoParada.orden, MotivoParada.codigo)))

for tab, tipo in zip(tabs[:3], NOMBRES, strict=False):
    with tab:
        filas = [{"Código": i.codigo, "Descripción": i.descripcion, "Activo": i.activo, "Origen": i.origen.value,
                  **({"Aplica a": ", ".join(tipos[t].split(" · ")[0] for t in aplica.get(i.id, [])) or "—"}
                     if tipo == TipoCatalogo.MODO else {})} for i in items[tipo]]
        st.dataframe(filas, hide_index=True, width="stretch")
        with st.form(f"form_{tipo.value}"):
            st.markdown("**Agregar o editar**")
            existentes = {i.codigo: i for i in items[tipo]}
            elegido = st.selectbox("Elemento", ["(nuevo)", *existentes], key=f"sel_{tipo.value}")
            actual = existentes.get(elegido)
            codigo = st.text_input("Código", "" if actual is None else actual.codigo, disabled=actual is not None,
                                   help="Mayúsculas, sin espacios. Ej.: RUIDO_METALICO")
            descripcion = st.text_input("Descripción", "" if actual is None else actual.descripcion)
            activo = st.checkbox("Activo", True if actual is None else actual.activo)
            tipos_sel = None
            if tipo != TipoCatalogo.SINTOMA:
                ayuda = ("Obligatorio: a qué componentes aplica este modo" if tipo == TipoCatalogo.MODO
                         else "Vacío = aplica a todos los componentes")
                tipos_sel = st.multiselect("Tipos de componente", list(tipos), format_func=tipos.get, help=ayuda,
                                           default=aplica.get(actual.id, []) if actual else [])
            if st.form_submit_button("Guardar", width="stretch"):
                try:
                    with db.escritura(usuario_id=u["id"], motivo="Edición de catálogos") as s:
                        C.guardar_item(s, tipo, actual.codigo if actual else codigo, descripcion, activo=activo,
                                       tipos_aplica=tipos_sel)
                    F.guardar_mensaje_ok("catalogos", "Catálogo guardado.")
                    st.rerun()
                except C.ErrorCatalogo as e:
                    st.error(str(e))

with tabs[3]:
    st.caption("\"Cuenta como requerida\" = esas horas entran en la disponibilidad como paradas. Sin demanda, huelga "
               "y sin dato no cuentan (D-007, D-029). La categoría de pérdida alimenta el OEE (fase 4).")
    st.dataframe([{"Código": m.codigo, "Descripción": m.descripcion, "Requerida": m.cuenta_como_requerida,
                   "Falla": m.es_falla, "Preparación": m.es_setup, "Pérdida": m.categoria_6p.value if m.categoria_6p else "—",
                   "Activo": m.activo} for m in motivos], hide_index=True, width="stretch")
    with st.form("form_motivo"):
        existentes = {m.codigo: m for m in motivos}
        elegido = st.selectbox("Motivo", ["(nuevo)", *existentes])
        actual = existentes.get(elegido)
        codigo = st.text_input("Código", "" if actual is None else actual.codigo, disabled=actual is not None)
        descripcion = st.text_input("Descripción", "" if actual is None else actual.descripcion)
        c1, c2, c3, c4 = st.columns(4)
        requerida = c1.checkbox("Cuenta como requerida", True if actual is None else actual.cuenta_como_requerida)
        es_falla = c2.checkbox("Es falla", False if actual is None else actual.es_falla)
        es_setup = c3.checkbox("Es preparación", False if actual is None else actual.es_setup)
        activo = c4.checkbox("Activo", True if actual is None else actual.activo)
        cats = [None, *Categoria6P]
        categoria = st.selectbox("Categoría de pérdida (6 grandes pérdidas)", cats,
                                 index=cats.index(actual.categoria_6p) if actual and actual.categoria_6p in cats else 0,
                                 format_func=lambda c: "—" if c is None else c.value.replace("_", " ").capitalize())
        if st.form_submit_button("Guardar", width="stretch"):
            try:
                with db.escritura(usuario_id=u["id"], motivo="Edición de motivos de parada") as s:
                    C.guardar_motivo(s, actual.codigo if actual else codigo, descripcion, cuenta_como_requerida=requerida,
                                     es_falla=es_falla, es_setup=es_setup, categoria_6p=categoria, activo=activo)
                F.guardar_mensaje_ok("catalogos", "Motivo guardado.")
                st.rerun()
            except C.ErrorCatalogo as e:
                st.error(str(e))
