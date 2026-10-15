"""Reporte PDF del período (mensual para el jefe y la gerencia; semanal como resumen gerencial; Plan §7 y §10).

Resume lo que muestra el panel: KPIs de la línea, estado por máquina, ranking de riesgo, Pareto, tablero de
comando, alertas abiertas y calidad de los datos. Si hay datos DEMO, cada página lo dice.
"""

from __future__ import annotations

from datetime import date, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from circularis_rel.asistente import tablero as T
from circularis_rel.servicios import alertas, costos, kpis_planta, panel
from circularis_rel.servicios.demo import hay_demo
from circularis_rel.servicios.pdf import PDF


def _pct(x: float | None) -> str:
    return "falta dato" if x is None else f"{x:.1%}".replace(".", ",")


def _num(x: float | None, d: int = 0) -> str:
    if x is None:
        return "—"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mes_anterior(hoy: date) -> tuple[date, date]:
    fin = date(hoy.year, hoy.month, 1) - timedelta(days=1)
    return date(fin.year, fin.month, 1), fin


def pdf(s: Session, desde: date, hasta: date, tz: ZoneInfo, titulo: str = "Reporte de mantenimiento",
        hoy: date | None = None) -> bytes:
    """El resumen, el Pareto y el tablero son del período; el estado y el ranking, de hoy (lo que hay que atender)."""
    hoy = hoy or date.today()
    demo = hay_demo(s)
    doc = PDF(titulo + (" · DATOS FICTICIOS (DEMO)" if demo else ""))
    doc.add_page()
    doc.campo("Período", f"{desde:%d/%m/%Y} al {hasta:%d/%m/%Y}")
    linea = kpis_planta.kpis_linea(s, desde, hasta, tz)
    eventos = panel.eventos_validados(s, desde, hasta, tz)
    costo, sin_costo = 0.0, 0
    for ev in eventos:
        c = costos.costo_historico(s, ev)
        if c.ars is None:
            sin_costo += 1
        else:
            costo += c.ars
    doc.subtitulo("Resumen de la línea")
    doc.campo("Disponibilidad operacional", _pct(linea.ao))
    doc.campo("MTBF", f"{_num(linea.mtbf)} h" if linea.mtbf else "sin fallas")
    doc.campo("MTTR", f"{_num(linea.mttr, 1)} h" if linea.mttr else "sin fallas")
    doc.campo("Fallas validadas", str(linea.n_fallas))
    doc.campo("Horas operadas", _num(linea.horas_operadas))
    doc.campo("Costo de las fallas", f"$ {_num(costo)}" + (f" ({sin_costo} sin costo calculable)" if sin_costo else ""))

    doc.subtitulo("Estado de las máquinas (hoy)")
    doc.tabla(["Máquina", "Clase", "Semáforo", "Confianza", "Motivo principal"], [26, 14, 22, 22, 102],
              [[m.codigo, m.clase or "—", m.color.capitalize(), m.confianza.capitalize(), m.motivos[0] if m.motivos else ""]
               for m in panel.estado_maquinas(s)])

    ranking = panel.ranking_riesgo(s, hoy)
    if ranking:
        doc.subtitulo("Ranking de riesgo hoy (probabilidad de falla en el horizonte × costo de una falla)")
        doc.tabla(["Máquina", "Componente", "P(falla)", "Costo falla", "Riesgo", "Confianza"], [28, 34, 24, 34, 36, 30],
                  [[f.maquina, f.componente, _pct(f.p), f"$ {_num(f.cf)}" if f.cf else "—",
                    f"$ {_num(f.riesgo)}" if f.riesgo is not None else "—", f.confianza.capitalize()] for f in ranking])

    filas = panel.pareto(s, desde, hasta, tz, "horas")
    if filas:
        doc.subtitulo("Pareto por horas de parada")
        doc.tabla(["Máquina · componente · modo", "Fallas", "Horas", "% acumulado"], [116, 20, 24, 26],
                  [[f.etiqueta, f.n, _num(f.horas, 1), _pct(f.acumulado)] for f in filas[:10]])

    periodo = f"{hasta:%Y-%m}"
    doc.subtitulo(f"Tablero de comando ({periodo})")
    doc.tabla(["Indicador", "Valor", "Objetivo", "Color", "Falta"], [70, 24, 24, 20, 48],
              [[f"{v.codigo} · {v.nombre}", _pct(v.valor), _pct(v.objetivo) if v.objetivo is not None else "—",
                v.color.capitalize(), ", ".join(v.faltan)] for v in T.tablero(s, periodo, tz)])

    abiertas = [a for a in alertas.abiertas(s) if a.tipo != "RIESGO_ORIENTATIVO"]
    if abiertas:
        doc.subtitulo("Alertas abiertas")
        doc.tabla(["Tipo", "Mensaje"], [34, 152], [[a.tipo.replace("_", " ").capitalize(), a.mensaje] for a in abiertas[:25]])

    doc.subtitulo("Calidad de los datos")
    doc.tabla(["Máquina", "Partes esperados", "Del operario", "% completos", "% validados en 48 h"], [36, 36, 36, 36, 42],
              [[q["maquina"], q["partes_esperados"], q["partes_operario"], _pct(q["partes_completos"]),
                _pct(q["validados_48h"])] for q in panel.calidad_datos_linea(s, desde, hasta, tz)])
    return doc.a_bytes()
