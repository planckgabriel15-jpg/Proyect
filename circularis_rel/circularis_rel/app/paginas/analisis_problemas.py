"""Análisis de problemas [12.D]: Pareto, sugerencias automáticas y 5 Porqués con su ciclo PDCA."""

from datetime import timedelta

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import formularios as F
from circularis_rel.app.componentes import graficos as G
from circularis_rel.asistente import rca
from circularis_rel.datos.enums import EstadoPDCA, TipoAnalisis, TipoCatalogo
from circularis_rel.datos.modelos import (
    Activo,
    AnalisisProblema,
    Catalogo,
    CatalogoAplica,
    OrdenTrabajo,
    PosicionComponente,
    TipoComponente,
)
from circularis_rel.servicios import panel
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.permisos import Accion, puede, requerir
from circularis_rel.servicios.registro import ErrorRegistro

u = contexto.usuario()
requerir(u["rol"], Accion.CARGAR_ANALISIS)
ver_costos = puede(u["rol"], Accion.VER_COSTOS)
db = contexto.db()
tz = contexto.config().zona_horaria
hoy = F.hoy()
st.header("🔍 Análisis de problemas")
F.mensaje_ok("rca")

TIPOS = {TipoAnalisis.CINCO_PORQUES: "5 Porqués", TipoAnalisis.ISHIKAWA_5M: "Ishikawa (5M)",
         TipoAnalisis.CINCO_W_1H: "5W + 1H", TipoAnalisis.HOJA_VERIFICACION: "Hoja de verificación"}


def formulario_otro_tipo(a, cont: dict, cerrado: bool) -> None:
    """Ishikawa, 5W+1H u hoja de verificación (el plan de acción va debajo, igual que en 5 Porqués)."""
    with st.form(f"contenido_{a.id}"):
        if a.tipo == TipoAnalisis.ISHIKAWA_5M:
            st.caption("Una causa posible por renglón en cada una de las 5M.")
            previas = cont.get("causas", {})
            causas = {}
            cols = st.columns(len(rca.CINCO_M))
            for col, m in zip(cols, rca.CINCO_M, strict=True):
                causas[m] = col.text_area(m, "\n".join(previas.get(m, [])), height=140, disabled=cerrado,
                                          key=f"5m_{a.id}_{m}").splitlines()
            principal = st.text_input("Causa más probable (se toma como causa raíz)", cont.get("principal") or "",
                                      disabled=cerrado)
            contenido = {"causas": causas, "principal": principal}
        elif a.tipo == TipoAnalisis.CINCO_W_1H:
            previas = cont.get("respuestas", {})
            contenido = {k: st.text_input(p, previas.get(k, ""), disabled=cerrado, key=f"5w_{a.id}_{k}")
                         for k, p in rca.CINCO_W_1H.items()}
        else:
            previos = cont.get("items") or []
            if not previos and a.id_activo:
                with db.lectura() as s:
                    previos = rca.conteo_para_hoja(s, a.id_activo, hoy - timedelta(days=90), tz)
                st.caption("Precargada con los síntomas y causas de los avisos de los últimos 90 días; corregí o agregá.")
            editada = st.data_editor(previos or [{"categoria": "", "conteo": 0}], num_rows="dynamic", disabled=cerrado,
                                     column_config={"categoria": "Categoría", "conteo": st.column_config.NumberColumn("Veces", min_value=0)},
                                     key=f"hoja_{a.id}", width="stretch")
            contenido = {"items": editada}
        if st.form_submit_button("Guardar", width="stretch", disabled=cerrado):
            try:
                with db.escritura(usuario_id=u["id"]) as s:
                    rca.guardar_contenido(s, u["id"], a.id, contenido)
                st.session_state["rca_abierto"] = a.id
                F.guardar_mensaje_ok("rca", "Análisis guardado.")
                st.rerun()
            except ErrorRegistro as e:
                st.error(str(e))
    if a.tipo == TipoAnalisis.ISHIKAWA_5M and cont.get("causas"):
        st.html(rca.ishikawa_svg(cont.get("problema", ""), cont["causas"]))


tab_pareto, tab_sug, tab_analisis, tab_nuevo = st.tabs(["Pareto", "Sugerencias", "Análisis en curso", "Nuevo análisis"])

with tab_pareto:
    c1, c2, c3 = st.columns([3, 3, 1])
    dias = c1.segmented_control("Período", [30, 90, 365], default=365, format_func=lambda d: f"{d} días",
                                key="rca_dias") or 365
    opciones = ["horas", "costo", "frecuencia"] if ver_costos else ["horas", "frecuencia"]
    criterio = c2.segmented_control("Ordenar por", opciones, default="horas", format_func=lambda k: panel.CRITERIOS_PARETO[k],
                                    key="rca_criterio") or "horas"
    A.boton("pareto", c3)
    with db.lectura() as s:
        filas = panel.pareto(s, hoy - timedelta(days=dias), hoy, tz, criterio)
        corte = P.obtener(s, "pareto.corte")
    if filas and sum(f.valor for f in filas) > 0:
        st.plotly_chart(G.pareto([f.etiqueta for f in filas], [f.valor for f in filas], [f.acumulado for f in filas], corte,
                                 f"Pareto por {panel.CRITERIOS_PARETO[criterio].lower()}", panel.CRITERIOS_PARETO[criterio]),
                        width="stretch")
        st.dataframe([{"Máquina · componente · modo": f.etiqueta, "Fallas": f.n, "Horas de parada": A.numero(f.horas, 1),
                       **({"Costo": A.pesos(f.costo)} if criterio == "costo" else {}),
                       "% acumulado": A.porcentaje(f.acumulado, 0), "Atacar primero": "Sí" if f.dentro_corte else ""}
                      for f in filas], hide_index=True, width="stretch")
    else:
        st.caption("Sin fallas validadas en el período.")

with tab_sug:
    st.caption("El sistema sugiere un análisis cuando un problema está entre los primeros del Pareto, cuando falla al "
               "azar (β ≈ 1, donde cambiar antes no sirve) o cuando se repite. Los umbrales están en Parámetros (grupo asistente).")
    with db.lectura() as s:
        sugerencias = panel.sugerencias_rca(s, hoy, tz)
    if not sugerencias:
        st.info("No hay sugerencias pendientes.")
    for i, sg in enumerate(sugerencias):
        with st.container(border=True):
            st.markdown(f"**{sg.etiqueta}**")
            for m in sg.motivos:
                st.write("• " + m)
            if st.button("Iniciar 5 Porqués", key=f"sug_{i}", type="primary"):
                with db.escritura(usuario_id=u["id"]) as s:
                    a = rca.crear(s, u["id"], f"Fallas de {sg.etiqueta}", id_activo=sg.id_activo, id_tipo=sg.id_tipo,
                                  id_modo=sg.id_modo, origen=sg.origen, motivos_sugerencia=sg.motivos)
                st.session_state["rca_abierto"] = a.id
                F.guardar_mensaje_ok("rca", f"Análisis n.º {a.id} creado: completalo en la pestaña \"Análisis en curso\".")
                st.rerun()

with tab_analisis:
    with db.lectura() as s:
        lista = list(s.scalars(select(AnalisisProblema).order_by(AnalisisProblema.estado_pdca == EstadoPDCA.CERRADO,
                                                                 AnalisisProblema.id.desc())))
        nombres = {}
        for a in lista:
            maq = s.get(Activo, a.id_activo).codigo if a.id_activo else "sin máquina"
            nombres[a.id] = (f"n.º {a.id} · {TIPOS[a.tipo]} · {maq} · {rca.NOMBRE_PDCA[a.estado_pdca]} · "
                             f"{(a.contenido or {}).get('problema', '')[:60]}")
    if not lista:
        st.info("Todavía no hay análisis. Arrancá desde una sugerencia o creá uno nuevo.")
    else:
        ids = [a.id for a in lista]
        pedido = st.session_state.get("rca_abierto")
        aid = st.selectbox("Análisis", ids, index=ids.index(pedido) if pedido in ids else 0, format_func=nombres.get)
        a = next(x for x in lista if x.id == aid)
        cont = a.contenido or {}
        c1, c2, c3 = st.columns([8, 1, 1])
        c1.markdown(f"**Problema:** {cont.get('problema', '')}")
        A.boton("cinco_porques", c2)
        A.boton("pdca", c3)
        for m in cont.get("motivos_sugerencia", []):
            st.caption("Sugerido porque: " + m)
        st.progress((rca.ORDEN_PDCA.index(a.estado_pdca)) / (len(rca.ORDEN_PDCA) - 1),
                    text=f"PDCA: {rca.NOMBRE_PDCA[a.estado_pdca]}. {rca.QUE_ES_PDCA[a.estado_pdca]}")
        cerrado = a.estado_pdca == EstadoPDCA.CERRADO
        if a.tipo != TipoAnalisis.CINCO_PORQUES:
            formulario_otro_tipo(a, cont, cerrado)
        with st.form(f"porques_{a.id}") if a.tipo == TipoAnalisis.CINCO_PORQUES else st.container():
            previos = cont.get("porques", [])
            porques = []
            anterior = cont.get("problema", "el problema")
            for i in range(rca.MAX_PORQUES if a.tipo == TipoAnalisis.CINCO_PORQUES else 0):
                valor = previos[i] if i < len(previos) else ""
                porques.append(st.text_input(f"{i + 1}. ¿Por qué? ({anterior[:60]})" if i == 0 else f"{i + 1}. ¿Por qué?",
                                             valor, disabled=cerrado, key=f"pq_{a.id}_{i}"))
            causa = st.text_input("Causa raíz" + (" (si la dejás vacía se toma el último porqué)"
                                                  if a.tipo == TipoAnalisis.CINCO_PORQUES else ""),
                                  a.causa_raiz or "", disabled=cerrado, key=f"causa_{a.id}")
            accion = st.text_area("Acción correctiva o preventiva (qué, dónde, cómo)", a.accion_correctiva or "", disabled=cerrado,
                                  key=f"acc_{a.id}")
            c1, c2 = st.columns(2)
            responsable = c1.text_input("Responsable (quién)", a.responsable or "", disabled=cerrado, key=f"resp_{a.id}")
            fecha = c2.date_input("Fecha de compromiso (cuándo)", a.fecha_compromiso, format="DD/MM/YYYY", disabled=cerrado,
                                  key=f"fecha_{a.id}")
            enviar = (st.form_submit_button("Guardar", width="stretch", disabled=cerrado) if a.tipo == TipoAnalisis.CINCO_PORQUES
                      else st.button("Guardar plan de acción", width="stretch", disabled=cerrado, key=f"accion_{a.id}"))
            if enviar:
                try:
                    with db.escritura(usuario_id=u["id"]) as s:
                        if a.tipo == TipoAnalisis.CINCO_PORQUES:
                            rca.guardar_porques(s, u["id"], a.id, porques, causa_raiz=causa, accion=accion,
                                                responsable=responsable, fecha_compromiso=fecha)
                        else:
                            rca.guardar_accion(s, u["id"], a.id, causa_raiz=causa, accion=accion, responsable=responsable,
                                               fecha_compromiso=fecha)
                    st.session_state["rca_abierto"] = a.id
                    F.guardar_mensaje_ok("rca", "Análisis guardado.")
                    st.rerun()
                except ErrorRegistro as e:
                    st.error(str(e))
        if not cerrado:
            siguiente = rca.ORDEN_PDCA[rca.ORDEN_PDCA.index(a.estado_pdca) + 1]
            nota = st.text_input("Nota del paso (qué se hizo o qué se verificó)", key=f"nota_{a.id}")
            c1, c2 = st.columns(2)
            if c1.button(f"Pasar a: {rca.NOMBRE_PDCA[siguiente]}", width="stretch", key=f"av_{a.id}"):
                try:
                    with db.escritura(usuario_id=u["id"]) as s:
                        rca.avanzar(s, u["id"], a.id, nota)
                    st.session_state["rca_abierto"] = a.id
                    F.guardar_mensaje_ok("rca", f"Análisis n.º {a.id}: {rca.NOMBRE_PDCA[siguiente]}.")
                    st.rerun()
                except ErrorRegistro as e:
                    st.error(str(e))
            if a.id_ot_generada is None and c2.button("Generar OT modificativa con la acción", width="stretch", key=f"ot_{a.id}"):
                try:
                    with db.escritura(usuario_id=u["id"]) as s:
                        ot = rca.convertir_en_ot(s, u["id"], a.id)
                    st.session_state["rca_abierto"] = a.id
                    F.guardar_mensaje_ok("rca", f"OT {ot.numero} (modificativo) creada.")
                    st.rerun()
                except ErrorRegistro as e:
                    st.error(str(e))
        if a.id_ot_generada:
            with db.lectura() as s:
                ot = s.get(OrdenTrabajo, a.id_ot_generada)
                st.caption(f"OT generada: {ot.numero} · {ot.estado.value.lower()}")
        with st.expander("Historia del PDCA"):
            for paso in cont.get("pdca", []):
                st.write(f"{paso['fecha'][:16].replace('T', ' ')} · {rca.NOMBRE_PDCA[EstadoPDCA(paso['estado'])]} · "
                         f"{paso['usuario']}: {paso['nota']}")

with tab_nuevo:
    with db.lectura() as s:
        activos = {a.codigo: a.id for a in s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo))}
    if not activos:
        st.info("No hay máquinas cargadas.")
    else:
        codigo = st.selectbox("Máquina", list(activos), key="rca_nuevo_maq")
        with db.lectura() as s:
            tipos = {f"{p.codigo} · {s.get(TipoComponente, p.id_tipo_componente).nombre}": p.id_tipo_componente
                     for p in s.scalars(select(PosicionComponente).where(PosicionComponente.id_activo == activos[codigo]))}
        tipo = st.selectbox("Componente (opcional)", ["—", *tipos], key="rca_nuevo_tipo")
        modos = {}
        if tipo != "—":
            with db.lectura() as s:
                modos = {c.descripcion: c.id for c in s.scalars(
                    select(Catalogo).join(CatalogoAplica, CatalogoAplica.id_catalogo == Catalogo.id)
                    .where(CatalogoAplica.id_tipo_componente == tipos[tipo], Catalogo.tipo == TipoCatalogo.MODO))}
        modo = st.selectbox("Modo de falla (opcional)", ["—", *modos], key="rca_nuevo_modo")
        tipo_nuevo = st.segmented_control("Herramienta", list(TIPOS), default=TipoAnalisis.CINCO_PORQUES,
                                          format_func=TIPOS.get, key="rca_nuevo_herramienta") or TipoAnalisis.CINCO_PORQUES
        problema = st.text_area("¿Cuál es el problema?", key="rca_nuevo_problema",
                                placeholder="Ej.: la cuba de lavado pierde agua por el sello cada dos semanas")
        if st.button("Crear análisis", type="primary", width="stretch"):
            try:
                with db.escritura(usuario_id=u["id"]) as s:
                    a = rca.crear(s, u["id"], problema, id_activo=activos[codigo],
                                  id_tipo=tipos.get(tipo), id_modo=modos.get(modo), tipo=tipo_nuevo)
                st.session_state["rca_abierto"] = a.id
                F.guardar_mensaje_ok("rca", f"Análisis n.º {a.id} creado: completalo en la pestaña \"Análisis en curso\".")
                st.rerun()
            except ErrorRegistro as e:
                st.error(str(e))
