"""Gráficos del panel (Plotly). Solo dibujan: los números vienen del motor y de los servicios."""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go

from circularis_rel.motor import kpis

COLORES = {"VERDE": "#1e8e3e", "AMARILLO": "#f9ab00", "ROJO": "#d93025", "GRIS": "#80868b"}
EMOJI = {"VERDE": "🟢", "AMARILLO": "🟡", "ROJO": "🔴", "GRIS": "⚪"}
_BASE = dict(margin=dict(l=10, r=10, t=40, b=10), height=420, legend=dict(orientation="h", y=-0.3, yanchor="top"))


def _y_weibull(f: float) -> float:
    f = min(max(f, 1e-12), 1 - 1e-12)  # F = 0 o 1 por redondeo en los extremos
    return math.log(-math.log(1 - f))


# Papel de Weibull de la cátedra (UNIDAD 2, diap. 35): grilla verde, polo con abanico de β, línea de η al 63,2 %.
_PAPEL = dict(grilla="rgba(67,160,71,0.45)", decada="#2e7d32", rotulos="#c62828", beta="#3949ab", recta="#202124",
              puntos="#e53935", lectura="#c62828", ic="#9aa0a6")
_F_GRILLA = (0.001, 0.002, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.20, 0.30, 0.40, 0.50,
             0.60, 0.70, 0.80, 0.90, 0.95, 0.99, 0.999)
_F_MARCAS = (0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.632, 0.80, 0.90, 0.99, 0.999)
BETAS_ABANICO = (6.0, 3.0, 2.0, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5)  # escala de β del papel (diap. 35)


def _num(x: float, decimales: int = 0) -> str:
    texto = f"{x:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return texto


def _pct(f: float) -> str:
    v = round(100 * f, 1)
    return str(int(v)) if v.is_integer() else _num(v, 1)


def _limites_papel(xs: list[float], fs: list[float]) -> tuple[int, int, float, float]:
    """Décadas enteras de tiempo (al menos dos, para que entre todo el abanico de β) y rango de F."""
    lo = math.floor(math.log10(min(xs)))
    hi = math.ceil(math.log10(max(xs)) + 1e-9)
    hi = max(hi, lo + 2)
    f_min = min([0.01, *[f * 0.7 for f in fs]])
    f_max = max([0.99, *[1 - (1 - f) * 0.7 for f in fs]])
    return lo, hi, max(f_min, 0.0005), min(f_max, 0.9995)


def probabilidad(rangos: list[tuple[float, float, float]] | None, beta: float | None, eta: float | None,
                 beta_ic: tuple[float, float] | None = None, eta_ic: tuple[float, float] | None = None,
                 titulo: str = "Papel de Weibull", t_mision: float | None = None, etiquetas_max: int = 10,
                 unidad: str = "h") -> go.Figure:
    """Papel de Weibull como el de la cátedra (UNIDAD 2, diap. 35–38).

    Eje x = tiempo en escala logarítmica (décadas completas); eje y = F(t) en escala de Weibull, ln(−ln(1−F)).
    Puntos = fallas con su F(i) por rango de Benard; recta = ajuste. El **polo** (borde izquierdo, a la altura del
    63,2 %) con el abanico de β permite leer la pendiente: β es la guía paralela a la recta. La horizontal punteada
    del 63,2 % corta a la recta en η (flecha hacia el eje). Con `t_mision` se dibuja la lectura de F y R a ese tiempo
    (diap. 38). Las rectas punteadas grises son los extremos del IC (orientativo, D-041).
    """
    fig = go.Figure()
    rangos = rangos or []
    xs = [r[0] for r in rangos if r[0] > 0]
    fs = [r[2] for r in rangos]
    hay_ajuste = bool(beta and eta)
    if hay_ajuste:
        xs.append(eta)
    if t_mision and t_mision > 0:
        xs.append(t_mision)
    if not xs:
        fig.update_layout(title=titulo, **_BASE)
        return fig
    lo, hi, f_min, f_max = _limites_papel(xs, fs)
    x0, x1 = 10.0 ** lo, 10.0 ** hi
    y0, y1 = _y_weibull(f_min), _y_weibull(f_max)

    # Grilla del papel: 1 a 9 en cada década y los valores de F de siempre.
    menores_x, decadas_x = [], []
    for d in range(lo, hi + 1):
        for k in range(1, 10):
            x = k * 10.0 ** d
            if x0 <= x <= x1:
                (decadas_x if k == 1 else menores_x).extend([x, x, None])
    fy = [f for f in _F_GRILLA if f_min <= f <= f_max]
    menores_y = []
    for f in fy:
        menores_y.extend([_y_weibull(f), _y_weibull(f), None])
    fig.add_trace(go.Scatter(x=menores_x, y=[y0, y1, None] * (len(menores_x) // 3), mode="lines", hoverinfo="skip",
                             line=dict(color=_PAPEL["grilla"], width=1), showlegend=False))
    fig.add_trace(go.Scatter(x=decadas_x, y=[y0, y1, None] * (len(decadas_x) // 3), mode="lines", hoverinfo="skip",
                             line=dict(color=_PAPEL["decada"], width=1.6), showlegend=False))
    fig.add_trace(go.Scatter(x=[x0, x1, None] * len(fy), y=menores_y, mode="lines", hoverinfo="skip",
                             line=dict(color=_PAPEL["grilla"], width=1), showlegend=False))

    # Polo, abanico de β y escala de β arriba.
    anotaciones = []
    for b in BETAS_ABANICO:
        x_top = x0 * math.exp(y1 / b)
        if x_top > x1:
            continue
        fig.add_trace(go.Scatter(x=[x0, x_top], y=[0, y1], mode="lines", showlegend=False, hoverinfo="text",
                                 hovertext=f"Guía de β = {_num(b, 1)}: si la recta de tus datos es paralela a esta, "
                                           f"β ≈ {_num(b, 1)}",
                                 line=dict(color=_PAPEL["beta"], width=1, dash="dash")))
        anotaciones.append(dict(x=math.log10(x_top), y=y1, text=_num(b, 1), showarrow=False, textangle=-90,
                                yanchor="bottom", font=dict(color=_PAPEL["beta"], size=11)))
    anotaciones.append(dict(x=lo, y=y1, text="<b>β</b>", showarrow=False, xanchor="right", yanchor="bottom",
                            font=dict(color=_PAPEL["beta"], size=14)))
    fig.add_trace(go.Scatter(x=[x0], y=[0], mode="markers", showlegend=False, hoverinfo="text",
                             hovertext="Polo (punto de estimación): desde acá se traza la paralela a la recta "
                                       "y se lee β en la escala de arriba",
                             marker=dict(size=9, color="white", line=dict(color=_PAPEL["recta"], width=1.5))))
    # Línea auxiliar del 63,2 %
    fig.add_trace(go.Scatter(x=[x0, x1], y=[0, 0], mode="lines", showlegend=False, hoverinfo="text",
                             hovertext="F = 63,2 %: la recta corta esta línea en η (vida característica)",
                             line=dict(color=_PAPEL["recta"], width=1.2, dash="dash")))
    anotaciones.append(dict(x=hi, y=0, text="<b>η</b>", showarrow=False, xanchor="left",
                            font=dict(color=_PAPEL["beta"], size=14)))

    if hay_ajuste:
        t = np.geomspace(x0, x1, 80)
        y_recta = [_y_weibull(kpis.infiabilidad(x, beta, eta)) for x in t]
        fig.add_trace(go.Scatter(x=t, y=y_recta, mode="lines", name=f"Recta de Weibull (β = {_num(beta, 2)}, "
                                 f"η = {_num(eta)} {unidad})", hoverinfo="skip", line=dict(color=_PAPEL["recta"], width=2.5)))
        if beta_ic and eta_ic and all(map(math.isfinite, [*beta_ic, *eta_ic])):
            for b, e in ((beta_ic[0], eta_ic[0]), (beta_ic[1], eta_ic[1])):
                fig.add_trace(go.Scatter(x=t, y=[_y_weibull(kpis.infiabilidad(x, b, e)) for x in t], mode="lines",
                                         name="Extremos del intervalo de confianza", showlegend=b == beta_ic[0],
                                         hoverinfo="skip", line=dict(color=_PAPEL["ic"], dash="dot")))
        # Paralela por el polo: flecha con el valor de β
        y_flecha = y1 * 0.92
        x_flecha = x0 * math.exp(y_flecha / beta)
        if x_flecha > x1:
            x_flecha, y_flecha = x1, beta * math.log(x1 / x0)
        anotaciones.append(dict(x=math.log10(x_flecha), y=y_flecha, ax=lo, ay=0, axref="x", ayref="y", text="",
                                showarrow=True, arrowhead=2, arrowwidth=2.2, arrowcolor=_PAPEL["recta"]))
        anotaciones.append(dict(x=math.log10(x_flecha), y=y_flecha, text=f"<b>β = {_num(beta, 2)}</b>", showarrow=False,
                                xanchor="left", yanchor="middle", xshift=6, font=dict(size=13, color=_PAPEL["recta"]),
                                bgcolor="rgba(255,255,255,0.85)"))
        # η: de la intersección con el 63,2 % baja al eje
        anotaciones.append(dict(x=math.log10(eta), y=y0, ax=math.log10(eta), ay=0, axref="x", ayref="y", text="",
                                showarrow=True, arrowhead=2, arrowwidth=2.2, arrowcolor=_PAPEL["recta"]))
        anotaciones.append(dict(x=math.log10(eta), y=y0, text=f"<b>η = {_num(eta)} {unidad}</b>", showarrow=False,
                                yanchor="bottom", xanchor="left", xshift=6, yshift=4, font=dict(size=13),
                                bgcolor="rgba(255,255,255,0.85)"))
        if t_mision and t_mision > 0:
            f_m = kpis.infiabilidad(t_mision, beta, eta)
            y_m = _y_weibull(f_m)
            fig.add_trace(go.Scatter(x=[t_mision, t_mision, x0], y=[y0, y_m, y_m], mode="lines", showlegend=False,
                                     hoverinfo="text", hovertext=f"Lectura a t = {_num(t_mision)} {unidad}: "
                                     f"F = {_num(100 * f_m, 1)} %, R = {_num(100 * (1 - f_m), 1)} %",
                                     line=dict(color=_PAPEL["lectura"], width=1.8, dash="dashdot")))
            anotaciones.append(dict(x=math.log10(t_mision), y=y_m, text=f"t = {_num(t_mision)} {unidad} → "
                                    f"F = {_num(100 * f_m, 1)} % · R = {_num(100 * (1 - f_m), 1)} %",
                                    showarrow=False, xanchor="left", yanchor="top", xshift=6, yshift=-4,
                                    font=dict(color=_PAPEL["lectura"], size=12), bgcolor="rgba(255,255,255,0.85)"))

    if rangos:
        textos = [f"Falla N.º {_num(r[1], 2) if abs(r[1] - round(r[1])) > 1e-9 else int(round(r[1]))}<br>"
                  f"t = {_num(r[0])} {unidad}<br>F(i) = {_num(100 * r[2], 2)} % (rango de Benard)" for r in rangos]
        fig.add_trace(go.Scatter(x=[r[0] for r in rangos], y=[_y_weibull(r[2]) for r in rangos], mode="markers",
                                 name="Fallas, F(i) por Benard", hoverinfo="text", hovertext=textos,
                                 marker=dict(size=11, color=_PAPEL["puntos"], line=dict(color="#7f0000", width=1))))
        if len(rangos) <= etiquetas_max:
            for r in rangos:
                anotaciones.append(dict(x=math.log10(r[0]), y=_y_weibull(r[2]), xanchor="left", xshift=10, yshift=-10,
                                        text=f"t={_num(r[0])}, F={_num(100 * r[2], 2)} %", showarrow=False,
                                        font=dict(size=10), bgcolor="rgba(255,255,255,0.9)", bordercolor="#5f6368",
                                        borderwidth=1))

    marcas = [f for f in _F_MARCAS if f_min <= f <= f_max]
    fig.update_xaxes(type="log", range=[lo, hi], title=f"Tiempo t ({unidad}), escala logarítmica", showgrid=False,
                     zeroline=False, tickvals=[10.0 ** d for d in range(lo, hi + 1)],
                     ticktext=[_num(10.0 ** d, max(0, -d)) for d in range(lo, hi + 1)],
                     tickfont=dict(color=_PAPEL["rotulos"]), showline=True, linecolor="#5f6368", mirror=True)
    fig.update_yaxes(title="Infiabilidad F(t) (%)", range=[y0, y1], showgrid=False, zeroline=False,
                     tickvals=[_y_weibull(f) for f in marcas], ticktext=[_pct(f) for f in marcas],
                     tickfont=dict(color=_PAPEL["rotulos"]), showline=True, linecolor="#5f6368", mirror=True)
    fig.update_layout(title=titulo, annotations=anotaciones, plot_bgcolor="white", hovermode="closest",
                      **{**_BASE, "height": 560, "margin": dict(l=10, r=30, t=70, b=10)})
    return fig


def confiabilidad_y_tasa(beta: float, eta: float, edad: float | None, gamma: float = 0.0) -> go.Figure:
    """R(t) y h(t) con la edad actual marcada."""
    hasta = max(2.5 * eta, (edad or 0) * 1.3)
    t = np.linspace(hasta / 200, hasta, 200)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=[kpis.confiabilidad(x, beta, eta, gamma) for x in t], name="Confiabilidad R(t)",
                             line=dict(color="#1e8e3e", width=2)))
    fig.add_trace(go.Scatter(x=t, y=[kpis.tasa_falla(x, beta, eta, gamma) for x in t], name="Tasa de falla h(t)",
                             yaxis="y2", line=dict(color="#d93025", width=2)))
    if edad is not None:
        fig.add_vline(x=edad, line_dash="dash", line_color="#202124",
                      annotation_text=f"Edad actual {edad:.0f} h", annotation_position="top left")
    fig.update_layout(title="Confiabilidad y tasa de falla", xaxis=dict(title="Edad (h)", range=[0, hasta]),
                      yaxis=dict(title="R(t)", range=[0, 1.02], tickformat=".0%"),
                      yaxis2=dict(title="h(t) (fallas por hora)", overlaying="y", side="right", showgrid=False,
                                  rangemode="tozero"), **_BASE)
    return fig


def pareto(etiquetas: list[str], valores: list[float], acumulado: list[float], corte: float, titulo: str,
           eje: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=etiquetas, y=valores, name=eje, marker_color="#1a73e8"))
    fig.add_trace(go.Scatter(x=etiquetas, y=acumulado, name="% acumulado", yaxis="y2", mode="lines+markers",
                             line=dict(color="#d93025")))
    fig.add_hline(y=corte, yref="y2", line_dash="dot", line_color="#80868b", annotation_text=f"{corte:.0%}")
    fig.update_layout(title=titulo, yaxis=dict(title=eje),
                      yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0, 1.05], tickformat=".0%",
                                  showgrid=False), **_BASE)
    fig.update_xaxes(tickangle=-30)
    return fig


def tendencia(filas: list[dict], con_costo: bool) -> go.Figure:
    periodos = [f["periodo"] for f in filas]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=periodos, y=[f["fallas"] for f in filas], name="Fallas", marker_color="#9aa0a6"))
    fig.add_trace(go.Scatter(x=periodos, y=[f["ao"] for f in filas], name="Disponibilidad Ao", yaxis="y2",
                             mode="lines+markers", line=dict(color="#1e8e3e")))
    if con_costo:
        fig.add_trace(go.Scatter(x=periodos, y=[f["costo"] for f in filas], name="Costo de fallas (ARS)", yaxis="y3",
                                 mode="lines+markers", line=dict(color="#d93025", dash="dot")))
    fig.update_layout(title="Tendencia mensual", yaxis=dict(title="Fallas"),
                      yaxis2=dict(title="Ao", overlaying="y", side="right", tickformat=".0%", showgrid=False),
                      yaxis3=dict(overlaying="y", side="right", visible=False), **_BASE)
    return fig


def mtbf_mensual(filas: list[dict]) -> go.Figure:
    fig = go.Figure(go.Scatter(x=[f["periodo"] for f in filas], y=[f["mtbf"] for f in filas], mode="lines+markers",
                               name="MTBF (h)", line=dict(color="#1a73e8")))
    fig.update_layout(title="MTBF por mes (meses sin fallas quedan en blanco)", yaxis_title="h", **_BASE)
    return fig


def barras(etiquetas: list[str], valores: list[float], titulo: str, eje: str) -> go.Figure:
    fig = go.Figure(go.Bar(x=valores, y=etiquetas, orientation="h", marker_color="#1a73e8"))
    fig.update_layout(title=titulo, xaxis_title=eje, **_BASE)
    return fig


def curva_costo(curva: list[tuple[float, float, float]], t_opt: float | None, intervalo: float | None,
                costo_falla_h: float | None) -> go.Figure:
    fig = go.Figure(go.Scatter(x=[c[0] for c in curva], y=[c[1] for c in curva], name="C(T) ($/h)",
                               line=dict(color="#1a73e8", width=2)))
    if costo_falla_h:
        fig.add_hline(y=costo_falla_h, line_dash="dot", line_color="#d93025", annotation_text="Hasta la falla")
    if t_opt:
        fig.add_vline(x=t_opt, line_dash="dash", line_color="#202124", annotation_text=f"T* {t_opt:.0f} h")
    if intervalo and intervalo != t_opt:
        fig.add_vline(x=intervalo, line_dash="dot", line_color="#1e8e3e", annotation_text=f"Redondeado {intervalo:.0f} h",
                      annotation_position="bottom right")
    fig.update_layout(title="Costo por hora según el intervalo de cambio C(T)", xaxis_title="Intervalo T (h)",
                      yaxis_title="$/h", **_BASE)
    return fig


def serie_indicador(periodos: list[str], valores: list[float | None], objetivo: float | None, nombre: str,
                    limite_inf: float | None = None, limite_sup: float | None = None) -> go.Figure:
    fig = go.Figure(go.Scatter(x=periodos, y=valores, mode="lines+markers", name=nombre, line=dict(color="#1a73e8")))
    if objetivo is not None:
        fig.add_hline(y=objetivo, line_dash="dot", line_color="#1e8e3e", annotation_text="Objetivo")
    for limite, texto in ((limite_inf, "Límite inferior"), (limite_sup, "Límite superior")):
        if limite is not None:
            fig.add_hline(y=limite, line_dash="dash", line_color="#d93025", annotation_text=texto)
    fig.update_layout(title=f"{nombre}: últimos meses", yaxis_tickformat=".1%", **_BASE)
    return fig


def equilibrio(periodos: list[str], preventivo: list[float | None], correctivo_y_falla: list[float | None]) -> go.Figure:
    """Preventivo contra correctivo + falla por mes (UNIDAD 5: costo óptimo o de equilibrio)."""
    total = [None if a is None or b is None else a + b for a, b in zip(preventivo, correctivo_y_falla, strict=True)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=periodos, y=preventivo, name="Preventivo (CFJ)", marker_color="#1e8e3e"))
    fig.add_trace(go.Bar(x=periodos, y=correctivo_y_falla, name="Correctivo + falla (CV + CFA)", marker_color="#d93025"))
    fig.add_trace(go.Scatter(x=periodos, y=total, name="Total", mode="lines+markers", line=dict(color="#202124")))
    fig.update_layout(title="Preventivo contra correctivo por mes (buscar el menor total)", barmode="group",
                      yaxis_title="ARS", **_BASE)
    return fig
