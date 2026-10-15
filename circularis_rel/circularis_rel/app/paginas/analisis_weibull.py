"""Análisis Weibull (jefe, Plan §5 y §8): método elegido y alternativa, comparación de distribuciones,
forzar un método con justificación y curva de costo C(T)."""

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import formularios as F
from circularis_rel.app.componentes import graficos as G
from circularis_rel.datos.enums import AccionAuditoria, Alcance, ConjuntoDatos
from circularis_rel.datos.modelos import (
    Activo,
    Catalogo,
    PosicionComponente,
    ResultadoWeibull,
    TipoComponente,
)
from circularis_rel.servicios import panel, recalculo
from circularis_rel.servicios.permisos import Accion, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.CONFIGURAR)
db = contexto.db()
tz = contexto.config().zona_horaria
hoy = F.hoy()
st.header("📈 Análisis Weibull")
F.mensaje_ok("weibull")

with db.lectura() as s:
    pares = {}
    for r in s.scalars(select(ResultadoWeibull).where(ResultadoWeibull.vigente.is_(True), ResultadoWeibull.alcance == Alcance.MAQUINA,
                                                      ResultadoWeibull.conjunto_datos == ConjuntoDatos.NUEVOS)):
        etiqueta = (f"{s.get(Activo, r.id_activo).codigo} · {s.get(TipoComponente, r.id_tipo_componente).nombre} · "
                    f"{s.get(Catalogo, r.id_modo).descripcion}")
        pares[etiqueta] = (r.id_tipo_componente, r.id_modo, r.id_activo)
if not pares:
    st.info("Todavía no hay ajustes: aparecen cuando se valida la primera falla de un componente.")
    st.stop()

etiqueta = st.selectbox("Máquina · componente · modo", sorted(pares))
id_tipo, id_modo, id_activo = pares[etiqueta]

with db.lectura() as s:
    r = s.scalar(select(ResultadoWeibull).where(
        ResultadoWeibull.id_tipo_componente == id_tipo, ResultadoWeibull.id_modo == id_modo,
        ResultadoWeibull.id_activo == id_activo, ResultadoWeibull.vigente.is_(True),
        ResultadoWeibull.conjunto_datos == ConjuntoDatos.NUEVOS))
    alt = panel.alternativa(s, r)
    rangos = panel.rangos_par(s, r, tz)
    costo = panel.analisis_costo(s, r, hoy) if r.beta else None
    edad = None
    for pos in s.scalars(select(PosicionComponente).where(PosicionComponente.id_activo == id_activo,
                                                          PosicionComponente.id_tipo_componente == id_tipo)):
        e = panel.ultimo_estado(s, pos.id)
        edad = e.edad if e else None


def fila(x: ResultadoWeibull, rol: str) -> dict:
    ic = lambda a, b, d: f"{A.numero(a, d)} a {A.numero(b, d)}" if a is not None and b is not None else "—"  # noqa: E731
    return {"": rol, "Método": x.metodo.value if x.metodo else "—", "Fallas": x.n_fallas, "Suspensiones": x.n_suspensiones,
            "β": A.numero(x.beta, 2) if x.beta else "—", f"IC β ({x.nivel_ic or 0.9:.0%})": ic(x.beta_inf, x.beta_sup, 2),
            "η (h)": A.numero(x.eta, 0) if x.eta else "—", "IC η": ic(x.eta_inf, x.eta_sup, 0),
            "IC por": x.metodo_ic.value, "r²": A.numero(x.r2, 4) if x.r2 else "—",
            "r² crítico": A.numero(x.r2_critico, 4) if x.r2_critico else "—", "Confianza": x.confianza.value.capitalize()}


st.dataframe([fila(r, "Vigente" + (" (forzado)" if r.forzado else "")), *([fila(alt, "Alternativa")] if alt else [])],
             hide_index=True, width="stretch")
if r.forzado:
    st.warning(f"Método forzado por el jefe. Justificación: {r.justificacion}")
if r.interpretacion:
    st.info(panel.TEXTO_INTERPRETACION[r.interpretacion.value])
for adv in (r.comparacion or {}).get("advertencias", []):
    st.caption("⚠️ " + adv)
if r.r2 is not None and r.r2_critico is not None and r.r2 < r.r2_critico:
    st.warning("r² menor que el crítico: los puntos no siguen bien una recta. Puede haber dos modos de falla "
               "mezclados o un γ (vida mínima). Mirá la comparación de distribuciones.")

if r.beta:
    g1, g2 = st.columns(2)
    ic_b = (r.beta_inf, r.beta_sup) if r.beta_inf and r.beta_sup else None
    ic_e = (r.eta_inf, r.eta_sup) if r.eta_inf and r.eta_sup else None
    g1.plotly_chart(G.probabilidad(rangos, r.beta, r.eta, ic_b, ic_e), width="stretch")
    g2.plotly_chart(G.confiabilidad_y_tasa(r.beta, r.eta, edad, r.gamma or 0.0), width="stretch")
    c1, c2, c3 = st.columns(3)
    A.boton("grafico_probabilidad", c1)
    A.boton("beta", c2)
    A.boton("eta", c3)

# Comparación de distribuciones
tabla = {k: v for k, v in (r.comparacion or {}).items() if k in ("Weibull_2P", "Weibull_3P", "Lognormal_2P", "Exponential_1P")}
with st.expander("Comparación de distribuciones (AICc y Anderson-Darling: menor es mejor)"):
    if tabla:
        nombres = {"Weibull_2P": "Weibull 2 parámetros", "Weibull_3P": "Weibull 3 parámetros (con γ)",
                   "Lognormal_2P": "Lognormal", "Exponential_1P": "Exponencial"}
        st.dataframe([{"Distribución": nombres[k], "AICc": A.numero(v.get("AICc"), 2) if "AICc" in v else v.get("error", "—"),
                       "AD": A.numero(v.get("AD"), 3) if "AD" in v else "—"} for k, v in tabla.items()],
                     hide_index=True, width="stretch")
        st.caption("Con pocas fallas las diferencias de AICc menores a 2 no son concluyentes. El sistema usa Weibull "
                   "2 parámetros salvo que se fuerce otra cosa con justificación.")
    else:
        st.caption("Se calcula con 3 o más fallas y sin censura por intervalo.")

# Costo
if costo is not None:
    st.subheader("Política de cambio y costo")
    c1, c2 = st.columns([9, 1])
    c1.info(f"**Recomendación:** {costo.recomendacion.texto}" +
            (f" → intervalo **{costo.recomendacion.intervalo:.0f} h**" if costo.recomendacion.intervalo else ""))
    A.boton("intervalo", c2)
    if costo.costos.faltan:
        st.caption("Para la curva de costo falta: " + ", ".join(costo.costos.faltan) + " (se cargan en Parámetros y "
                   "en la planilla de repuestos).")
    if costo.curva:
        m = st.columns(4)
        m[0].metric("Cp (preventivo)", A.pesos(costo.costos.cp))
        m[1].metric("Cf (falla)", A.pesos(costo.costos.cf))
        m[2].metric("T* (óptimo)", A.numero(costo.t_optimo, 0, "h") if costo.t_optimo else "no hay")
        m[3].metric("Ahorro frente a correr hasta la falla", A.porcentaje(costo.ahorro, 0) if costo.ahorro is not None else "—")
        st.plotly_chart(G.curva_costo(costo.curva, costo.t_optimo, costo.intervalo_redondeado, costo.costo_falla_por_hora),
                        width="stretch")
        A.boton("costo_t")

# Forzar método
st.subheader("Cambiar el método")
st.caption("El sistema elige el método según la cantidad de fallas y suspensiones (Plan §5). Forzar otro exige "
           "una justificación, que queda en la auditoría y a la vista de todos.")
with st.form("forzar"):
    metodo = st.selectbox("Método", ["RRX", "MLE", "WEIBAYES"],
                          help="RRX: regresión en el papel Weibull. MLE: máxima verosimilitud (con 30 fallas o menos "
                               "lleva la corrección RBA). WEIBAYES necesita un β de referencia cargado en el tipo de componente.")
    justificacion = st.text_area("Justificación (obligatoria)")
    if st.form_submit_button("Forzar este método", width="stretch"):
        if not justificacion.strip():
            st.error("Escribí la justificación")
        else:
            with db.escritura(usuario_id=u["id"], motivo=justificacion, accion=AccionAuditoria.FORZADO_METODO) as s:
                recalculo.recalcular_par(s, id_tipo, id_modo, id_activo, tz, forzar=metodo, justificacion=justificacion)
                for pos in s.scalars(select(PosicionComponente).where(PosicionComponente.id_activo == id_activo,
                                                                      PosicionComponente.id_tipo_componente == id_tipo)):
                    recalculo.actualizar_estado(s, pos, tz)
            F.guardar_mensaje_ok("weibull", f"Método {metodo} forzado y recalculado.")
            st.rerun()
c1, c2 = st.columns(2)
if r.forzado and c1.button("Volver a la selección automática", width="stretch"):
    with db.escritura(usuario_id=u["id"], motivo="Vuelta a la selección automática del método",
                      accion=AccionAuditoria.FORZADO_METODO) as s:
        recalculo.quitar_forzado(s, id_tipo, id_modo, id_activo, tz)
        for pos in s.scalars(select(PosicionComponente).where(PosicionComponente.id_activo == id_activo,
                                                              PosicionComponente.id_tipo_componente == id_tipo)):
            recalculo.actualizar_estado(s, pos, tz)
    F.guardar_mensaje_ok("weibull", "Volvió a la selección automática.")
    st.rerun()
if c2.button("Recalcular ahora", width="stretch"):
    with db.escritura(usuario_id=u["id"], motivo="Recálculo manual") as s:
        recalculo.recalcular_par(s, id_tipo, id_modo, id_activo, tz)
        for pos in s.scalars(select(PosicionComponente).where(PosicionComponente.id_activo == id_activo,
                                                              PosicionComponente.id_tipo_componente == id_tipo)):
            recalculo.actualizar_estado(s, pos, tz)
    F.guardar_mensaje_ok("weibull", "Recalculado.")
    st.rerun()
