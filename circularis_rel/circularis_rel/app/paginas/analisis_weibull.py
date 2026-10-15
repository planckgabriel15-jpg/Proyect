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
from circularis_rel.motor import bayes
from circularis_rel.motor.preparacion import armar_poblacion
from circularis_rel.servicios import flota, panel, recalculo
from circularis_rel.servicios import parametros as P
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
    ic_b = (r.beta_inf, r.beta_sup) if r.beta_inf and r.beta_sup else None
    ic_e = (r.eta_inf, r.eta_sup) if r.eta_inf and r.eta_sup else None
    mision = st.number_input("Leer en el papel a t (h)", min_value=0.0, value=float(round(edad)) if edad else 0.0,
                             step=10.0, help="Tiempo de misión: se lee F(t) y R(t) sobre la recta (UNIDAD 2, diap. 38). "
                                             "Por defecto, la edad actual del componente. 0 = no leer.")
    st.plotly_chart(G.probabilidad(rangos, r.beta, r.eta, ic_b, ic_e, t_mision=mision or None), width="stretch")
    claves = ("grafico_probabilidad", "rango_benard", "polo_beta", "beta", "eta", "lectura_mision")
    for grupo in (claves[:3], claves[3:]):
        for col, clave in zip(st.columns(3), grupo, strict=True):
            A.boton(clave, col)
    st.plotly_chart(G.confiabilidad_y_tasa(r.beta, r.eta, edad, r.gamma or 0.0), width="stretch")

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

# Weibull bayesiano (fase 4)
with db.lectura() as s:
    tipo_obj = s.get(TipoComponente, id_tipo)
    sd_defecto = P.obtener(s, "motor.bayes_sd_log_beta")
    vidas = recalculo.vidas_de_poblacion(s, id_tipo, id_activo, tz)
    for obj in list(s.dirty):
        s.expire(obj)
obs_bayes, _r = armar_poblacion(vidas, id_modo)
with st.expander("Weibull bayesiano: el β de referencia como creencia previa"):
    A.boton("bayes")
    c1, c2 = st.columns(2)
    previa = c1.number_input("β de referencia (previa)", min_value=0.1, value=float(tipo_obj.beta_ref or r.beta or 2.0), step=0.1,
                             help="Por defecto, el β de referencia del tipo de componente (con su fuente) o el del ajuste actual")
    sd = c2.number_input("Incertidumbre de la previa (desvío en logaritmo)", min_value=0.05, value=float(sd_defecto), step=0.05,
                         help="0,35 = 95 % de que β esté entre la mitad y el doble del de referencia")
    if any(o.estado in ("F", "I") for o in obs_bayes if not o.solo_pronostico):
        b = bayes.ajustar(obs_bayes, previa, sd, r.nivel_ic or 0.9)
        st.dataframe([fila(r, "Vigente"),
                      {"": "Bayesiano", "Método": "BAYES", "Fallas": b.n_fallas, "Suspensiones": b.n_suspensiones,
                       "β": A.numero(b.beta, 2), f"IC β ({r.nivel_ic or 0.9:.0%})": f"{A.numero(b.beta_ic[0], 2)} a {A.numero(b.beta_ic[1], 2)}",
                       "η (h)": A.numero(b.eta, 0), "IC η": f"{A.numero(b.eta_ic[0], 0)} a {A.numero(b.eta_ic[1], 0)}",
                       "IC por": "credibilidad", "r²": "—", "r² crítico": "—", "Confianza": "—"}],
                     hide_index=True, width="stretch")
        st.caption("Es una comparación: el semáforo sigue usando el método vigente. La fuente del β de referencia: "
                   + (tipo_obj.fuente_ref or "no cargada (se usó el β del ajuste actual)"))
    else:
        st.caption("Hace falta al menos una falla.")

# Histórico A/B
with db.lectura() as s:
    con_hist = s.scalar(select(ResultadoWeibull).where(
        ResultadoWeibull.id_tipo_componente == id_tipo, ResultadoWeibull.id_modo == id_modo,
        ResultadoWeibull.id_activo == id_activo, ResultadoWeibull.vigente.is_(True),
        ResultadoWeibull.conjunto_datos == ConjuntoDatos.NUEVOS_MAS_HIST_AB))
    usa_hist = P.obtener(s, "motor.semaforo_con_historico")
st.subheader("Datos nuevos contra nuevos + histórico")
if con_hist is None:
    st.caption("Sin histórico A/B para este componente (se carga y clasifica en Histórico (triage)).")
else:
    st.dataframe([fila(r, "Solo datos nuevos"), fila(con_hist, "Nuevos + histórico A/B")], hide_index=True, width="stretch")
    st.caption("El histórico tiene horas estimadas (nivel E) y, el de clase B, fechas aproximadas (censura por intervalo). "
               "Si los dos ajustes se parecen, el histórico suma información; si no, puede tener errores o la máquina "
               "cambió. El semáforo usa " + ("**nuevos + histórico**" if usa_hist else "**solo datos nuevos**")
               + " (parámetro motor.semaforo_con_historico).")

# Flota
with db.lectura() as s:
    grupos = [g for g in flota.grupos(s) if any(s.get(PosicionComponente, i).id_activo == id_activo
                                                 and s.get(PosicionComponente, i).id_tipo_componente == id_tipo
                                                 for i in g.posiciones)]
st.subheader("Flota: el mismo componente en otras máquinas")
if not grupos:
    st.caption("Este componente no está en otras máquinas ni en un grupo de equivalencia.")
for g in grupos:
    with db.lectura() as s:
        prueba = flota.probar(s, g, id_modo, tz)
        actual = flota.vigente(s, g, id_modo)
        codigos_grupo = sorted({s.get(Activo, s.get(PosicionComponente, i).id_activo).codigo for i in g.posiciones})
    with st.container(border=True):
        st.markdown(f"**{g.nombre}**: {', '.join(codigos_grupo)}")
        st.dataframe([{"Máquina": c, "Fallas": f, "Suspensiones": n} for c, (f, n) in prueba.por_maquina.items()],
                     hide_index=True)
        (st.success if prueba.agrupable else st.info)(prueba.nota)
        if actual is not None:
            st.dataframe([fila(actual, "Flota")], hide_index=True, width="stretch")
            st.caption("Se recalcula cada noche. " + ("Se usa en el semáforo de las posiciones de la flota que no "
                                                      "tienen ajuste propio." if (actual.comparacion or {}).get("agrupable")
                                                      else "No se usa en el semáforo: la prueba no permite agrupar."))
        if st.button("Ajustar como flota" if actual is None else "Recalcular la flota", key=f"flota_{g.clave}"):
            with db.escritura(usuario_id=u["id"], motivo=f"Ajuste de flota {g.nombre}") as s:
                flota.ajustar(s, g, id_modo, tz)
                for i in g.posiciones:
                    recalculo.actualizar_estado(s, s.get(PosicionComponente, i), tz)
            F.guardar_mensaje_ok("weibull", "Flota ajustada.")
            st.rerun()

# Costo
if costo is not None:
    st.subheader("Política de cambio y costo")
    c1, c2 = st.columns([3, 1])
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
