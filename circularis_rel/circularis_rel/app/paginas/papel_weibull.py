"""Papel de Weibull [12.H, P1]: el procedimiento de la cátedra con datos propios (UNIDAD 2, diap. 31–38).

No guarda nada: es para practicar, revisar un TP o probar datos antes de cargarlos al sistema.
"""

import math

import streamlit as st

from circularis_rel.app import contexto
from circularis_rel.app.componentes import ayuda as A
from circularis_rel.app.componentes import graficos as G
from circularis_rel.asistente import papel_weibull as PW
from circularis_rel.servicios import recalculo
from circularis_rel.servicios.permisos import Accion, requerir

requerir(contexto.usuario()["rol"], Accion.VER_PANEL_GERENCIAL)
st.header("📐 Papel de Weibull")
st.caption("El procedimiento de la cátedra con tus propios datos (UNIDAD 2, diap. 31–38): se ordenan los tiempos, "
           "se calcula F(i) por Benard, se trazan los puntos en el papel y se leen β, η y la confiabilidad para un "
           "tiempo de misión. Cargá **un solo componente y un solo modo de falla** por vez.")
b1, b2, b3, b4 = st.columns(4)
A.boton("grafico_probabilidad", b1)
A.boton("rango_benard", b2)
A.boton("polo_beta", b3)
A.boton("suspension", b4)
c1, c2, c3 = st.columns(3)
unidad = c1.radio("Los tiempos están en", ["horas", "días"], horizontal=True, key="papel_unidad",
                  help="Tiempo de funcionamiento hasta la falla (TBF). Si lo tenés en días, se pasa a horas.")
horas_dia = c2.number_input("Horas de trabajo por día", min_value=0.5, max_value=24.0, value=None, step=0.5,
                            disabled=unidad == "horas", key="papel_horas_dia",
                            help="Solo para pasar días a horas (el TP N.º 1 usa las horas por día de cada máquina)")
mision = c3.number_input("Tiempo de misión (h)", min_value=0.0, value=PW.EJEMPLO_UNIDAD2["mision"], step=1.0,
                         key="papel_mision", help="Para leer F(t) y R(t) en el papel. 0 = no leer.")
st.caption(f"Ejemplo precargado: {PW.EJEMPLO_UNIDAD2['fuente']}. Borrá las filas y pegá tus datos desde Excel "
           "(Ctrl+V sobre la tabla).")
filas_papel = st.data_editor([{"tiempo": t, "falló": True} for t in PW.EJEMPLO_UNIDAD2["tiempos"]],
                             num_rows="dynamic", width="stretch", key="papel_datos",
                             column_config={"tiempo": st.column_config.NumberColumn("Tiempo hasta la falla", min_value=0.0),
                                            "falló": st.column_config.CheckboxColumn(
                                                "¿Falló?", help="Destildá si la pieza no falló por este modo (se "
                                                "cambió en un preventivo o sigue andando): es una suspensión")})
validas = [f for f in filas_papel if f.get("tiempo")]
try:
    tiempos = PW.a_horas([float(f["tiempo"]) for f in validas], "h" if unidad == "horas" else "días", horas_dia)
    with contexto.db().lectura() as s:
        cfg = recalculo.configuracion(s)
    res = PW.calcular([(t, f.get("falló") is not False) for t, f in zip(tiempos, validas, strict=True)],
                      mision or None, cfg)
except ValueError as e:
    st.error(str(e))
    res = None
if res is not None:
    for aviso in res.avisos:
        st.warning(aviso)
    if res.beta:
        m = st.columns(5)
        A.metrica(m[0], "β (pendiente)", A.numero(res.beta, 2), "beta")
        A.metrica(m[1], "η (vida característica)", A.numero(res.eta, 0, "h"), "eta")
        A.metrica(m[2], "r² del papel", A.numero(res.r2, 3), "r2",
                  f"r² crítico para {res.n_fallas} fallas: {A.numero(res.r2_critico, 3)}" if res.r2_critico else None)
        A.metrica(m[3], f"R({A.numero(mision, 0)} h)" if mision else "R(t de misión)",
                  A.porcentaje(res.r_mision) if res.r_mision is not None else "—", "lectura_mision")
        A.metrica(m[4], "MTTF", A.numero(res.mttf, 0, "h"), "mttf")
        st.info(f"**Estado: {res.estado}.** En t = η = {A.numero(res.eta, 0)} h ya falló el 63,2 % y queda "
                f"R = {A.porcentaje(PW.r_en_eta())}: a esa edad conviene por lo menos un control del equipo y "
                "revisar el preventivo (UNIDAD 2, diap. 37).")
        A.boton("estado_weibull")
    st.plotly_chart(G.probabilidad(res.rangos, res.beta, res.eta, t_mision=mision or None,
                                   titulo="Papel de Weibull con tus datos"), width="stretch", key="papel_fig")
    with st.expander("Tabla para el papel (tiempos ordenados y F(i))", expanded=len(res.filas) <= 12):
        st.dataframe([{"N.º": f.orden, "t (h)": A.numero(f.tiempo, 1), "Dato": "Falla" if f.falla else "Suspensión",
                       "i (rango)": A.numero(f.rango, 2) if f.rango is not None else "—",
                       "F(i) Benard": A.porcentaje(f.f_benard, 2) if f.f_benard is not None else "—"} for f in res.filas],
                     hide_index=True, width="stretch", height=min(520, 42 + 38 * len(res.filas)))
        st.caption("F(i) = (i − 0,3) / (N + 0,4). Con suspensiones, i es el rango ajustado de Johnson.")
    if res.ajuste is not None and res.ajuste.vigente.beta:
        v = res.ajuste.vigente
        ic_b = f" (IC {v.nivel_ic:.0%}: {A.numero(v.beta_ic[0], 2)} a {A.numero(v.beta_ic[1], 2)})" if v.beta_ic else ""
        ic_e = (f" (IC: {A.numero(v.eta_ic[0], 0)} a {A.numero(v.eta_ic[1], 0)} h)"
                if v.eta_ic and all(map(math.isfinite, v.eta_ic)) else "")
        with st.expander("Lo que calcularía el sistema con estos datos (mismo motor que el semáforo)"):
            st.write(f"Método {v.metodo}: β = {A.numero(v.beta, 2)}{ic_b} · η = {A.numero(v.eta, 0)} h{ic_e} · "
                     f"confianza {v.confianza.lower()}.")
            st.caption("El papel usa la recta por regresión (RRX), como la lectura gráfica. Con más de 20 fallas el "
                       "sistema pasa a máxima verosimilitud (MLE). El intervalo de confianza dice cuánto se puede "
                       "mover β con esta cantidad de datos.")

