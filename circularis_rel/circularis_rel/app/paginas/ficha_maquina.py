"""Ficha de máquina (todos los roles, Plan §7). El operario la ve sin costos."""

from datetime import date, timedelta

import streamlit as st
from sqlalchemy import select

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import formularios as F
from circularis_rel.app.componentes import graficos as G
from circularis_rel.datos.modelos import Activo, Catalogo
from circularis_rel.servicios import kpis_planta, panel
from circularis_rel.servicios.permisos import Accion, requerir

u = contexto.usuario()
requerir(u["rol"], Accion.VER_FICHA)
db = contexto.db()
tz = contexto.config().zona_horaria
hoy = F.hoy()

st.header("🏭 Ficha de máquina")
with db.lectura() as s:
    activos = list(s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo)))
if not activos:
    st.info("No hay máquinas cargadas.")
    st.stop()
codigos = [a.codigo for a in activos]
pedida = st.session_state.pop("ficha_maquina", None)
indice = codigos.index(pedida) if pedida in codigos else F.indice_maquina(codigos)
codigo = st.selectbox("Máquina", codigos, index=indice, format_func=lambda c: f"{c} · {next(a.nombre for a in activos if a.codigo == c)}")
F.recordar_maquina(codigo)
activo = next(a for a in activos if a.codigo == codigo)

inicio_mes = date(hoy.year, hoy.month, 1)
with db.lectura() as s:
    m = panel.estado_maquina(s, s.get(Activo, activo.id))
    k_mes = kpis_planta.kpis_maquina(s, activo.id, inicio_mes, hoy, tz)
    k_90 = kpis_planta.kpis_maquina(s, activo.id, hoy - timedelta(days=90), hoy, tz)
    ultima = panel.ultima_intervencion(s, activo.id)
    historia = panel.linea_tiempo(s, activo.id, tz)
    resultados = {}
    for c in m.componentes:
        lista = []
        for r in panel.resultados_vigentes(s, activo.id, c.id_tipo):
            lista.append({"r": r, "modo": s.get(Catalogo, r.id_modo).descripcion, "rangos": panel.rangos_par(s, r, tz),
                          "alt": panel.alternativa(s, r)})
        resultados[c.id_posicion] = lista

# Encabezado
st.subheader(f"{G.EMOJI[m.color]} {m.codigo} · {m.nombre}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Semáforo", m.color.capitalize(), help="Peor color de sus componentes críticos, o rojo si hay un aviso abierto")
c2.metric("Criticidad", f"Clase {m.clase}" if m.clase else "Sin evaluar")
c3.metric("Horas operadas del mes", A.numero(k_mes.horas_operadas, 0, "h"))
c4.metric("Última intervención", f"{ultima.fin_real.astimezone(tz):%d/%m/%Y}" if ultima else "—",
          help=f"{ultima.numero} ({ultima.tipo.value.lower()})" if ultima else None)
for motivo in m.motivos:
    (st.error if m.color == "ROJO" else st.warning if m.color == "AMARILLO" else st.info)(motivo)

st.markdown("**Últimos 90 días**")
c = st.columns(4)
A.metrica(c[0], "Disponibilidad Ao", A.porcentaje(k_90.ao), "ao")
A.metrica(c[1], "MTBF", A.numero(k_90.mtbf, 0, "h") if k_90.n_fallas else "sin fallas", "mtbf")
A.metrica(c[2], "MTTR", A.numero(k_90.mttr, 1, "h") if k_90.n_fallas else "sin fallas", "mttr")
A.metrica(c[3], "Fallas validadas", str(k_90.n_fallas))

# Componentes
st.subheader("Componentes")
st.caption("Edad, probabilidad de falla hasta la próxima parada (horizonte), vida remanente y semáforo de cada componente.")
c1, c2, c3 = st.columns(3)
A.boton("p_delta", c1)
A.boton("confianza", c2)
A.boton("vida_remanente", c3)
filas = []
for comp in m.componentes:
    principal = resultados[comp.id_posicion][0]["r"] if resultados[comp.id_posicion] else None
    banda = (f" ({A.porcentaje(comp.p_inf, 0)}–{A.porcentaje(comp.p_sup, 0)})"
             if comp.p is not None and comp.p_inf is not None else "")
    filas.append({
        "": G.EMOJI[comp.color], "Componente": comp.codigo, "Tipo": comp.tipo, "Crítico": "Sí" if comp.critica else "No",
        "Edad (h)": A.numero(comp.edad, 0) if comp.edad is not None else "desconocida" if comp.motivos and "Edad desconocida" in " ".join(comp.motivos) else "—",
        "β": A.numero(principal.beta, 2) if principal and principal.beta else "—",
        "η (h)": A.numero(principal.eta, 0) if principal and principal.eta else "—",
        "P(falla en el horizonte)": (A.porcentaje(comp.p) + banda) if comp.p is not None else "—",
        "Vida remanente (mediana)": A.numero(comp.vida_rem_mediana, 0, "h") if comp.vida_rem_mediana else "—",
        "Intervalo recomendado": A.numero(comp.intervalo, 0, "h") if comp.intervalo else "—",
        "Confianza": comp.confianza.capitalize(),
    })
st.dataframe(filas, hide_index=True, width="stretch")

for comp in m.componentes:
    with st.expander(f"{G.EMOJI[comp.color]} {comp.codigo} · {comp.tipo}"):
        for motivo in comp.motivos:
            st.write("• " + motivo)
        if not resultados[comp.id_posicion]:
            st.caption("Sin ajuste de Weibull todavía: hacen falta fallas validadas de este componente "
                       "(3 o más; con 1 o 2, solo si hay un β de referencia cargado).")
        for item in resultados[comp.id_posicion]:
            r = item["r"]
            st.markdown(f"**Modo: {item['modo']}** · método {r.metodo.value if r.metodo else '—'}"
                        f"{' (forzado por el jefe)' if r.forzado else ''} · {r.n_fallas} fallas, "
                        f"{r.n_suspensiones} suspensiones · confianza {r.confianza.value.lower()}")
            if r.beta is None:
                st.caption("Datos insuficientes para ajustar.")
                continue
            ic_b = (f" (IC {r.nivel_ic:.0%}: {A.numero(r.beta_inf, 2)} a {A.numero(r.beta_sup, 2)})"
                    if r.beta_inf and r.beta_sup else "")
            ic_e = (f" (IC: {A.numero(r.eta_inf)} a {A.numero(r.eta_sup)} h)" if r.eta_inf and r.eta_sup
                    else f" (IC inferior: {A.numero(r.eta_inf)} h)" if r.eta_inf else "")
            st.write(f"β = {A.numero(r.beta, 2)}{ic_b} · η = {A.numero(r.eta)} h{ic_e}")
            if r.interpretacion:
                st.info(panel.TEXTO_INTERPRETACION[r.interpretacion.value])
            for adv in (r.comparacion or {}).get("advertencias", []):
                st.caption("⚠️ " + adv)
            g1, g2 = st.columns(2)
            ic_beta = (r.beta_inf, r.beta_sup) if r.beta_inf and r.beta_sup else None
            ic_eta = (r.eta_inf, r.eta_sup) if r.eta_inf and r.eta_sup else None
            g1.plotly_chart(G.probabilidad(item["rangos"], r.beta, r.eta, ic_beta, ic_eta), width="stretch",
                            key=f"prob_{r.id}")
            g2.plotly_chart(G.confiabilidad_y_tasa(r.beta, r.eta, comp.edad, r.gamma or 0.0), width="stretch", key=f"rh_{r.id}")
            b1, b2 = st.columns(2)
            A.boton("grafico_probabilidad", b1)
            A.boton("beta", b2)

# Línea de tiempo y horas perdidas
st.subheader("Línea de tiempo")
if historia:
    st.dataframe([{"Fecha": f"{h['fecha']:%d/%m/%Y %H:%M}", "Qué": h["tipo"], "Componente": h["componente"],
                   "Detalle": h["detalle"], "Horas de parada": A.numero(h["horas_parada"], 1) if h["horas_parada"] else "",
                   "Estado": h["estado"]} for h in historia], hide_index=True, width="stretch", height=300)
else:
    st.caption("Sin registros todavía.")

st.subheader("Horas perdidas por motivo (últimos 90 días)")
if k_90.horas_por_motivo:
    motivos = sorted(k_90.horas_por_motivo.items(), key=lambda x: x[1])
    st.plotly_chart(G.barras([k for k, _ in motivos], [v for _, v in motivos], "Horas no operadas por motivo", "h"),
                    width="stretch")
else:
    st.caption("Sin horas perdidas registradas en los partes.")
