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


def probabilidad(rangos: list[tuple[float, float, float]] | None, beta: float | None, eta: float | None,
                 beta_ic: tuple[float, float] | None = None, eta_ic: tuple[float, float] | None = None,
                 titulo: str = "Gráfico de probabilidad Weibull") -> go.Figure:
    """Papel Weibull: eje x = edad (log), eje y = ln(−ln(1−F)). Puntos = fallas con rango de Benard;
    recta = ajuste; líneas punteadas = rectas con los extremos del IC (orientativo, D-041)."""
    fig = go.Figure()
    marcas_f = [0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.632, 0.8, 0.9, 0.95, 0.99]
    if rangos:
        fig.add_trace(go.Scatter(x=[r[0] for r in rangos], y=[_y_weibull(r[2]) for r in rangos], mode="markers",
                                 name="Fallas (rango de Benard)", marker=dict(size=10, color="#1a73e8")))
    if beta and eta:
        xs = [r[0] for r in rangos] if rangos else [eta]
        t = np.geomspace(max(min(xs) * 0.5, 1e-6), max(max(xs), eta) * 2, 60)
        fig.add_trace(go.Scatter(x=t, y=[_y_weibull(kpis.infiabilidad(x, beta, eta)) for x in t], mode="lines",
                                 name=f"Ajuste β={beta:.2f}, η={eta:.0f}", line=dict(color="#202124", width=2)))
        if beta_ic and eta_ic and all(map(math.isfinite, [*beta_ic, *eta_ic])):
            for b, e in ((beta_ic[0], eta_ic[0]), (beta_ic[1], eta_ic[1])):
                fig.add_trace(go.Scatter(x=t, y=[_y_weibull(kpis.infiabilidad(x, b, e)) for x in t], mode="lines",
                                         name="Extremos del IC (orientativo)", showlegend=b == beta_ic[0],
                                         line=dict(color="#9aa0a6", dash="dot")))
    fig.update_xaxes(type="log", title="Edad (h)")
    fig.update_yaxes(title="Probabilidad de falla acumulada F", tickvals=[_y_weibull(f) for f in marcas_f],
                     ticktext=[f"{f:.0%}" if f != 0.632 else "63,2 %" for f in marcas_f], range=[_y_weibull(0.005), _y_weibull(0.995)])
    fig.update_layout(title=titulo, **_BASE)
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
