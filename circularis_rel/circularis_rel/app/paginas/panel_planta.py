"""Panel de planta (jefe y gerencia, Plan §7): qué máquina está en riesgo, por qué y qué hacer."""

from datetime import date, timedelta

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import formularios as F
from circularis_rel.app.componentes import graficos as G
from circularis_rel.datos.enums import EtapaProceso
from circularis_rel.servicios import alertas, costos, kpis_planta, panel
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.permisos import Accion, puede, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.VER_PANEL_GERENCIAL)
ver_costos = puede(u["rol"], Accion.VER_COSTOS)
db = contexto.db()
tz = contexto.config().zona_horaria
hoy = F.hoy()

st.header("📊 Panel de planta")
PERIODOS = {"Últimos 30 días": 30, "Últimos 90 días": 90, "Último año": 365}
periodo = st.segmented_control("Período", list(PERIODOS), default="Últimos 30 días", key="panel_periodo") or "Últimos 30 días"
desde = hoy - timedelta(days=PERIODOS[periodo])
hasta = hoy

with db.lectura() as s:
    linea = kpis_planta.kpis_linea(s, desde, hasta, tz)
    maquinas = panel.estado_maquinas(s)
    ranking = panel.ranking_riesgo(s, hoy)
    inicio_mes = date(hoy.year, hoy.month, 1)
    costo_mes, sin_costo = 0.0, 0
    if ver_costos:
        for ev in panel.eventos_validados(s, inicio_mes, hoy, tz):
            c = costos.costo_historico(s, ev)
            if c.ars is None:
                sin_costo += 1
            else:
                costo_mes += c.ars
    corte = P.obtener(s, "pareto.corte")
    sugerencias = panel.sugerencias_rca(s, hoy, tz)
    calidad = panel.calidad_datos_linea(s, desde, hasta - timedelta(days=1), tz)

componentes = [c for m in maquinas for c in m.componentes]
rojas = sum(c.color == "ROJO" for c in componentes)
amarillas = sum(c.color == "AMARILLO" for c in componentes)

# Tarjetas
c = st.columns(5 if ver_costos else 4)
A.metrica(c[0], "Disponibilidad de la línea", A.porcentaje(linea.ao), "ao")
A.metrica(c[1], "MTBF", A.numero(linea.mtbf, 0, "h"), "mtbf")
A.metrica(c[2], "MTTR", A.numero(linea.mttr, 1, "h"), "mttr")
A.metrica(c[3], "Alertas 🔴 / 🟡", f"{rojas} / {amarillas}", "semaforo")
if ver_costos:
    texto = A.pesos(costo_mes) + (" *" if sin_costo else "")
    A.metrica(c[4], "Costo fallas del mes", texto, "costo_falla",
              f"{sin_costo} falla(s) sin costo calculable (faltan tarifas)" if sin_costo else None)
st.caption(f"{linea.n_fallas} falla{'s' if linea.n_fallas != 1 else ''} validada{'s' if linea.n_fallas != 1 else ''} y {A.numero(linea.horas_operadas, 0)} h operadas en el período. "
           "Solo lo validado por el jefe entra en los números.")

# Esquema de la línea
st.subheader("Línea en orden de proceso")
etapas = [e for e in EtapaProceso if any(m.etapa == e.value for m in maquinas)]
if not maquinas:
    st.info("No hay máquinas cargadas.")
for fila in range(0, len(etapas), 3):
    cols = st.columns(3)
    for col, etapa in zip(cols, etapas[fila:fila + 3], strict=False):
        col.markdown(f"**{A.ETAPAS[etapa.value]}**")
        for m in [m for m in maquinas if m.etapa == etapa.value]:
            with col.container(border=True):
                clase = f" · clase {m.clase}" if m.clase else ""
                st.markdown(f"{G.EMOJI[m.color]} **{m.codigo}**{clase}  \n{m.nombre}")
                if m.motivos:
                    st.caption(m.motivos[0] + (f" (+{len(m.motivos) - 1})" if len(m.motivos) > 1 else ""))
                st.caption(f"Confianza {m.confianza.lower()}" if m.confianza != "GRIS" else "Confianza gris: datos insuficientes")
                if st.button("Ver ficha", key=f"ficha_{m.codigo}", width="stretch"):
                    st.session_state["ficha_maquina"] = m.codigo
                    st.switch_page("paginas/ficha_maquina.py")

# Alertas de riesgo
with db.lectura() as s:
    abiertas = [a for a in alertas.abiertas(s) if a.tipo in ("RIESGO", "RIESGO_ORIENTATIVO", "DEGRADACION", "PREDICTIVO")]
if abiertas:
    st.subheader("Alertas de riesgo")
    for a in abiertas:
        if a.tipo in ("RIESGO", "PREDICTIVO") and a.severidad == "alta":
            st.error(f"🔔 {a.mensaje}")
        elif a.tipo in ("DEGRADACION", "PREDICTIVO"):
            st.warning(f"📉 {a.mensaje}")
        else:
            st.warning(f"Orientativa: {a.mensaje}")
    st.caption("Las alertas firmes se habilitan por componente recién con confianza media o alta (UNIDAD 6, etapa 16); "
               "antes son orientativas y no se mandan por mail.")

# Ranking de riesgo
st.subheader("Ranking de riesgo")
A.boton("riesgo")
if not ranking:
    st.caption("Todavía no hay componentes con probabilidad de falla calculada (hace falta al menos 1 falla validada "
               "con β de referencia, o 3 fallas).")
else:
    filas = []
    for f in ranking:
        fila = {"": G.EMOJI[f.color], "Máquina": f.maquina, "Componente": f.componente,
                "P(falla en el horizonte)": A.porcentaje(f.p), "Confianza": f.confianza.capitalize()}
        if ver_costos:
            fila["Costo de una falla"] = A.pesos(f.cf)
            fila["Riesgo ($)"] = A.pesos(f.riesgo) if f.riesgo is not None else "falta: " + ", ".join(f.faltan)
        filas.append(fila)
    st.dataframe(filas, hide_index=True, width="stretch")

# Pareto y tendencia
st.subheader("Pareto de modos de falla")
A.boton("pareto")
opciones = ["horas", "costo", "frecuencia"] if ver_costos else ["horas", "frecuencia"]
criterio = st.segmented_control("Ordenar por", opciones, default="horas", format_func=lambda k: panel.CRITERIOS_PARETO[k],
                                key="panel_pareto") or "horas"
with db.lectura() as s:
    filas_p = panel.pareto(s, desde, hasta, tz, criterio)
    tend = panel.tendencia_mensual(s, hoy - timedelta(days=365), hoy, tz, con_costo=ver_costos)
if filas_p and sum(f.valor for f in filas_p) > 0:
    st.plotly_chart(G.pareto([f.etiqueta for f in filas_p], [f.valor for f in filas_p], [f.acumulado for f in filas_p],
                             corte, f"Pareto por {panel.CRITERIOS_PARETO[criterio].lower()} ({periodo.lower()})",
                             panel.CRITERIOS_PARETO[criterio]), width="stretch")
    sin = sum(f.sin_costo for f in filas_p)
    if sin:
        st.caption(f"{sin} falla(s) sin costo calculable no suman al Pareto de costo.")
else:
    st.caption("Sin fallas validadas en el período.")
c1, c2 = st.columns(2)
c1.plotly_chart(G.tendencia(tend, ver_costos), width="stretch")
c2.plotly_chart(G.mtbf_mensual(tend), width="stretch")

# Sugerencias de análisis
st.subheader("Sugerencias de análisis de causa raíz")
if sugerencias:
    for sg in sugerencias:
        st.warning(f"**{sg.etiqueta}**: " + " · ".join(sg.motivos))
    if puede(u["rol"], Accion.CARGAR_ANALISIS) and st.button("Ir a Análisis de problemas"):
        st.switch_page("paginas/analisis_problemas.py")
else:
    st.caption("No hay sugerencias pendientes.")

# Calidad de datos
st.subheader("Calidad de los datos")
A.boton("calidad_datos")
st.dataframe([{"Máquina": q["maquina"], "Partes esperados": q["partes_esperados"], "Cargados por el operario": q["partes_operario"],
               "% partes completos": A.porcentaje(q["partes_completos"], 0),
               "% validados en 48 h": A.porcentaje(q["validados_48h"], 0)} for q in calidad],
             hide_index=True, width="stretch")
