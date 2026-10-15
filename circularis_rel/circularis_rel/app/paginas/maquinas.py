"""Máquinas: revisión del jefe (criterio de salida de la fase 0), catastro [12.B], ficha y QR."""

from datetime import date

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.datos.enums import UnidadProduccion
from circularis_rel.datos.modelos import Activo, PosicionComponente, TipoComponente
from circularis_rel.servicios import catastro
from circularis_rel.servicios.formato import numero
from circularis_rel.servicios.permisos import Accion, requerir
from circularis_rel.servicios.qr import etiquetas_pdf

requerir(contexto.usuario()["rol"], Accion.REVISAR_CARGA)
db = contexto.db()
cfg = contexto.config()

st.header("Máquinas y revisión de la carga")
with db.lectura() as s:
    estados = catastro.estado_revision(s)
if not estados:
    st.info("No hay máquinas cargadas. Importá la planilla de carga inicial en **Carga de planillas**.")
    st.stop()

revisadas = sum(e.revisado for e in estados)
st.progress(revisadas / len(estados), text=f"Revisadas por el jefe: {revisadas} de {len(estados)}")
st.caption("Criterio para pasar a la fase 1a: todas las máquinas del listado y sus componentes cargados y revisados por el jefe.")
st.dataframe([{
    "Revisada": "✔" if e.revisado else "", "Código": e.codigo, "Máquina": e.nombre, "Componentes": e.posiciones,
    "Críticos": e.posiciones_criticas, "Clase": e.criticidad or "—", "Catastro": f"{e.catastro_completo:.0%}",
    "Pendiente": "; ".join(e.faltantes),
} for e in estados], hide_index=True, use_container_width=True)

with db.lectura() as s:
    todas = [tuple(r) for r in s.execute(select(Activo.codigo, Activo.nombre).where(Activo.activo.is_(True)).order_by(Activo.codigo))]
st.download_button("Etiquetas QR de todas las máquinas (PDF)", etiquetas_pdf(todas, cfg.url_base),
                   file_name="etiquetas_qr.pdf", use_container_width=True)
st.caption(f"Los QR apuntan a {cfg.url_base}. Si la dirección de la mini PC es otra, cambiar CIRCULARIS_URL_BASE en el archivo .env.")

st.divider()
codigos = [e.codigo for e in estados]
inicial = st.session_state.get("maquina_qr")
codigo = st.selectbox("Máquina", codigos, index=codigos.index(inicial) if inicial in codigos else 0,
                      format_func=lambda c: next(f"{e.codigo} · {e.nombre}" for e in estados if e.codigo == c))
estado = next(e for e in estados if e.codigo == codigo)
with db.lectura() as s:
    a = s.scalar(select(Activo).where(Activo.codigo == codigo))


def guardar(cambios: dict) -> None:
    try:
        with db.escritura(usuario_id=contexto.id_usuario()) as s:
            cambiados = catastro.actualizar_catastro(s, codigo, cambios)
        st.success(f"Guardado ({len(cambiados)} campos cambiados)." if cambiados else "No había cambios.")
    except ValueError as e:
        st.error(str(e))


t_rev, t_ident, t_inst, t_dim, t_oper, t_comp, t_ficha = st.tabs(
    ["Revisión", "Identificación", "Instalación", "Dimensiones", "Operación", "Componentes", "Ficha y QR"])

with t_rev:
    if estado.faltantes:
        st.warning("Pendiente: " + "; ".join(estado.faltantes))
    else:
        st.success("No hay pendientes detectados por el sistema.")
    if estado.revisado:
        st.info(f"Revisada por {estado.revisado_por}.")
        if st.button("Quitar la marca de revisada", use_container_width=True):
            with db.escritura(usuario_id=contexto.id_usuario()) as s:
                catastro.marcar_revisado(s, codigo, contexto.id_usuario(), revisado=False)
            st.rerun()
    elif st.button("Marcar como revisada", type="primary", use_container_width=True):
        with db.escritura(usuario_id=contexto.id_usuario()) as s:
            catastro.marcar_revisado(s, codigo, contexto.id_usuario())
        st.rerun()

with t_ident, st.form("ident"):
    c = {"nombre": st.text_input("Máquina", a.nombre),
         "numero_serie": st.text_input("N.º de serie", a.numero_serie or ""),
         "fabricante": st.text_input("Fabricante", a.fabricante or ""),
         "modelo": st.text_input("Modelo", a.modelo or ""),
         "proveedor": st.text_input("Proveedor", a.proveedor or "")}
    if st.form_submit_button("Guardar", use_container_width=True):
        guardar(c)

with t_inst, st.form("inst"):
    c = {"ubicacion": st.text_input("Localización", a.ubicacion or ""),
         "fecha_instalacion": st.date_input("Fecha de instalación", a.fecha_instalacion, min_value=date(1970, 1, 1),
                                            format="DD/MM/YYYY"),
         "ruta_documentos": st.text_input("Planos, manuales y catálogos (carpeta)", a.ruta_documentos or ""),
         "funcion": st.text_area("Función", a.funcion or ""),
         "caracteristicas_tecnicas": st.text_area("Características técnicas", a.caracteristicas_tecnicas or "")}
    if st.form_submit_button("Guardar", use_container_width=True):
        guardar(c)

with t_dim, st.form("dim"):
    c = {k: st.number_input(et, value=getattr(a, k), min_value=0.0, step=1.0, format="%.0f")
         for k, et in (("ancho_mm", "Ancho (mm)"), ("alto_mm", "Alto (mm)"), ("largo_mm", "Largo (mm)"),
                       ("peso_kg", "Peso (kg)"))}
    c["condiciones_almacenamiento"] = st.text_input("Condiciones de almacenamiento", a.condiciones_almacenamiento or "")
    if st.form_submit_button("Guardar", use_container_width=True):
        guardar(c)

with t_oper, st.form("oper"):
    unidades = [u.value for u in UnidadProduccion]
    c = {"horas_promedio_dia": st.number_input("Horas de operación por día", value=a.horas_promedio_dia, min_value=0.0,
                                               max_value=24.0, step=0.5),
         "autonomia_pulmon_h": st.number_input("Autonomía de pulmón (h)", value=a.autonomia_pulmon_h, min_value=0.0, step=0.5,
                                               help="Horas que la línea aguanta con esta máquina parada antes de frenar la extrusora"),
         "unidad_produccion": UnidadProduccion(st.selectbox("Unidad de la cantidad procesada", unidades,
                                                            index=unidades.index(a.unidad_produccion.value))),
         "factor_toneladas": st.number_input("Toneladas por unidad", value=a.factor_toneladas, min_value=0.0, format="%.4f"),
         "ciclo_teorico_s": st.number_input("Ciclo teórico (s)", value=a.ciclo_teorico_s, min_value=0.0)}
    if st.form_submit_button("Guardar", use_container_width=True):
        guardar(c)
    st.caption(f"Criticidad: {a.criticidad_clase.value if a.criticidad_clase else '—'} "
               f"({a.criticidad_nivel or '—'}, {numero(a.criticidad_puntaje, 0)} puntos). Se carga en la planilla, hoja 'criticidad'.")

with t_comp:
    with db.lectura() as s:
        filas = [{"Posición": p.codigo, "Componente": t.nombre, "Cantidad": p.cantidad, "Crítica": p.critica}
                 for p, t in s.execute(select(PosicionComponente, TipoComponente)
                                       .join(TipoComponente, TipoComponente.id == PosicionComponente.id_tipo_componente)
                                       .where(PosicionComponente.id_activo == a.id).order_by(PosicionComponente.codigo))]
    st.caption("Marcá como **crítica** cada posición cuyo estado debe definir el color de la máquina.")
    editado = st.data_editor(filas, disabled=["Posición", "Componente", "Cantidad"], hide_index=True,
                             use_container_width=True, key=f"comp_{codigo}")
    if st.button("Guardar posiciones críticas", use_container_width=True):
        with db.escritura(usuario_id=contexto.id_usuario()) as s:
            n = catastro.marcar_criticas(s, codigo, {f["Posición"]: f["Crítica"] for f in editado})
        st.success(f"{n} posiciones actualizadas.")
        st.rerun()

with t_ficha:
    with db.lectura() as s:
        pdf = catastro.ficha_pdf(s, codigo)
    st.download_button("Ficha de registro e histórico (PDF, MANT/RHM001)", pdf, file_name=f"ficha_{codigo}.pdf",
                       use_container_width=True)
    st.download_button("Etiqueta QR de esta máquina (PDF)", etiquetas_pdf([(a.codigo, a.nombre)], cfg.url_base),
                       file_name=f"qr_{codigo}.pdf", use_container_width=True)
