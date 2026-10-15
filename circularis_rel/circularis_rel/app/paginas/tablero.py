"""Tablero de comando [12.E]: ratios de la UNIDAD 5 con objetivo, límites y color; con el módulo 12E, el
tablero completo, el CIT y la curva de equilibrio preventivo/correctivo."""

from datetime import date

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import formularios as F
from circularis_rel.app.componentes import graficos as G
from circularis_rel.asistente import tablero as T
from circularis_rel.datos.modelos import IndicadorObjetivo
from circularis_rel.servicios import modulos, panel
from circularis_rel.servicios.permisos import Accion, puede, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.VER_TABLERO)
editar = puede(u["rol"], Accion.CONFIGURAR)
db = contexto.db()
tz = contexto.config().zona_horaria
hoy = F.hoy()
st.header("🎯 Tablero de comando")
F.mensaje_ok("tablero")
st.caption("Indicadores de mantenimiento de la cátedra (UNIDAD 5). Lo que el sistema no puede saber (facturación, "
           "horas-hombre disponibles) lo carga el jefe cada mes; lo cargado manda sobre lo calculado.")

periodos = list(reversed(panel.meses(date(hoy.year - 1, hoy.month, 1), hoy)))
periodo = st.selectbox("Mes", periodos, index=1 if len(periodos) > 1 else 0,
                       help="Por defecto, el último mes cerrado")
with db.lectura() as s:
    completo = modulos.habilitado(s, "12E")
    valores = T.tablero(s, periodo, tz, completo)
    cargados = T.datos_cargados(s, periodo)
    sistema, _faltan = T.variables_sistema(s, periodo, tz)
    cit = T.cit(s, periodo, tz) if completo else None
if not completo:
    st.caption("Tablero básico. El completo (mano de obra externa, costo por producción y por valor inmovilizado, trabajo "
               "en línea, entrenamiento, clima social, efectivo real y CIT) se habilita en Parámetros › Módulos (12E).")

for fila in range(0, len(valores), 3):
    cols = st.columns(3)
    for col, v in zip(cols, valores[fila:fila + 3], strict=False):
        with col.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"{G.EMOJI[v.color]} **{v.codigo}** · {v.nombre}")
            A.boton(v.codigo, c2)
            st.metric(f"{v.codigo} del mes", A.porcentaje(v.valor), label_visibility="collapsed")
            st.caption(f"{v.codigo} = {v.formula}")
            objetivo = []
            if v.objetivo is not None:
                objetivo.append(f"objetivo {A.porcentaje(v.objetivo)}")
            if v.limite_inf is not None or v.limite_sup is not None:
                objetivo.append(f"límites {A.porcentaje(v.limite_inf)} a {A.porcentaje(v.limite_sup)}")
            st.caption(" · ".join(objetivo) if objetivo else "Sin objetivo cargado")
            if v.referencia:
                st.caption(f"Referencia: {v.referencia}")
            if v.faltan:
                st.caption("Falta: " + ", ".join(v.faltan))
            for n in v.notas:
                st.caption("ℹ️ " + n)

if cit is not None:
    st.subheader("Costo total de mantenimiento (CIT)")
    st.caption("CIT = CFJ + CV + CFN + CFA (UNIDAD 5): fijos (≈ preventivo), variables (≈ correctivo), financieros y por "
               "falla (producción perdida). La gestión busca el punto de menor costo entre preventivo y correctivo.")
    c = st.columns(5)
    for col, (nombre, (valor, origen)) in zip(c, (("Fijos (CFJ)", cit.cfj), ("Variables (CV)", cit.cv),
                                                  ("Financieros (CFN)", cit.cfn), ("Por falla (CFA)", cit.cfa)), strict=False):
        col.metric(nombre, A.pesos(valor), help=f"Origen: {origen}", border=True)
    c[4].metric("CIT", A.pesos(cit.total), border=True)
    if cit.faltan:
        st.caption("Falta: " + ", ".join(cit.faltan))

definiciones = T.definiciones(completo)
codigos = [v.codigo for v in valores] + ["DISP"]
codigo = st.selectbox("Ver la evolución de", codigos,
                      format_func=lambda c: "DISP · Disponibilidad de la línea" if c == "DISP" else f"{c} · {definiciones[c].nombre}")
ultimos = list(reversed(periodos[:12]))
with db.lectura() as s:
    serie = T.serie(s, codigo, ultimos, tz)
    obj = s.scalar(select(IndicadorObjetivo).where(IndicadorObjetivo.codigo == codigo))
st.plotly_chart(G.serie_indicador([p for p, _ in serie], [x for _, x in serie], obj.objetivo if obj else None, codigo,
                                  obj.limite_inf if obj else None, obj.limite_sup if obj else None), width="stretch")

if completo:
    with db.lectura() as s:
        meses_cit = [(p, T.cit(s, p, tz)) for p in ultimos]
    st.plotly_chart(G.equilibrio([p for p, _ in meses_cit], [c.cfj[0] for _, c in meses_cit],
                                 [(c.cv[0] or 0) + (c.cfa[0] or 0) if c.cv[0] is not None else None for _, c in meses_cit]),
                    width="stretch")

if editar:
    st.subheader(f"Datos del mes {periodo}")
    with st.form("datos_mes"):
        nuevos = {}
        cols = st.columns(2)
        variables = T.VARIABLES if completo else {k: v for k, v in T.VARIABLES.items() if k not in T.VARIABLES_COMPLETO}
        for i, (clave, (nombre, unidad)) in enumerate(variables.items()):
            calculado = sistema.get(clave)
            ayuda_txt = (f"Calculado por el sistema: {A.numero(calculado, 1)} {unidad}. Dejalo vacío para usar ese valor."
                         if calculado is not None and clave not in T.SOLO_CARGA else "Solo se carga a mano.")
            nuevos[clave] = cols[i % 2].number_input(f"{nombre} ({unidad})", min_value=0.0, value=cargados.get(clave),
                                                     help=ayuda_txt, key=f"dm_{periodo}_{clave}")
        if st.form_submit_button("Guardar datos del mes", width="stretch"):
            with db.escritura(usuario_id=u["id"], motivo=f"Datos mensuales {periodo}") as s:
                for clave, valor in nuevos.items():
                    if valor != cargados.get(clave):
                        T.cargar_dato(s, periodo, clave, valor)
            F.guardar_mensaje_ok("tablero", f"Datos de {periodo} guardados.")
            st.rerun()

    with st.expander("Objetivos y límites de cada indicador"):
        st.caption("En fracción (0,20 = 20 %). La UNIDAD 5 da referencias orientativas: CPCT ≈ 20 %, HPHP entre 1 % y 3 %. "
                   "Cada planta fija los suyos.")
        with st.form("objetivos"):
            entradas = {}
            for v in valores:
                c0, c1, c2, c3 = st.columns([2, 2, 2, 2])
                c0.markdown(f"**{v.codigo}**  \n{'mayor es mejor' if v.mayor_es_mejor else 'menor es mejor'}")
                entradas[v.codigo] = (
                    c1.number_input("Objetivo", value=v.objetivo, format="%.4f", key=f"obj_{v.codigo}"),
                    c2.number_input("Límite inferior", value=v.limite_inf, format="%.4f", key=f"li_{v.codigo}"),
                    c3.number_input("Límite superior", value=v.limite_sup, format="%.4f", key=f"ls_{v.codigo}"),
                )
            if st.form_submit_button("Guardar objetivos", width="stretch"):
                try:
                    with db.escritura(usuario_id=u["id"], motivo="Objetivos del tablero") as s:
                        for codigo_i, (o, li, ls) in entradas.items():
                            T.fijar_objetivo(s, codigo_i, o, li, ls)
                    F.guardar_mensaje_ok("tablero", "Objetivos guardados.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
