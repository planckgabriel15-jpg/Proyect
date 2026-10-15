"""KPIs empíricos por máquina y por línea desde partes y eventos validados (Plan §6).

- Horas requeridas = Σ horas de turno − horas con motivo que no cuenta como requerido (sin demanda,
  huelga, sin dato; D-007, D-029).
- Horas paradas = horas no operadas con motivo requerido.
- MTBF = horas operadas / fallas validadas; MTTR = Σ reparación activa / n; MTTR total = Σ parada / n.
- OEE = disponibilidad × rendimiento × calidad. Rendimiento = cantidad × ciclo teórico / horas operadas;
  sin dato de calidad (piezas rechazadas) el OEE queda "falta dato" (se completa en la fase 4).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import EstadoEvento
from circularis_rel.datos.modelos import Activo, EventoFalla, MotivoParada, ParteTurno
from circularis_rel.motor import kpis


@dataclass
class KPIsMaquina:
    codigo: str
    horas_turno: float
    horas_requeridas: float
    horas_paradas: float
    horas_operadas: float
    horas_por_motivo: dict[str, float]
    n_fallas: int
    mtbf: float | None
    mttr: float | None
    mttr_total: float | None
    ai: float | None
    ao: float | None
    rendimiento: float | None
    oee: float | None
    partes_estimados: int
    partes: int


def _rango(desde: date, hasta: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    return datetime.combine(desde, time.min, tzinfo=tz), datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=tz)


def kpis_maquina(s: Session, id_activo: int, desde: date, hasta: date, tz: ZoneInfo) -> KPIsMaquina:
    a = s.get(Activo, id_activo)
    motivos = {m.id: m for m in s.scalars(select(MotivoParada))}
    turno = requeridas = paradas = operadas = cantidad = 0.0
    por_motivo: dict[str, float] = {}
    estimados = n_partes = 0
    hay_cantidad = False
    for p in s.scalars(select(ParteTurno).where(ParteTurno.id_activo == id_activo, ParteTurno.fecha.between(desde, hasta))):
        n_partes += 1
        estimados += p.origen == "ESTIMADO_SISTEMA"
        turno += p.horas_turno
        operadas += p.horas_operadas
        m = motivos.get(p.id_motivo) if p.id_motivo else None
        no_requeridas = p.horas_no_operadas if (m is not None and not m.cuenta_como_requerida) else 0.0
        requeridas += p.horas_turno - no_requeridas
        paradas += p.horas_no_operadas - no_requeridas
        if p.horas_no_operadas and m is not None:
            por_motivo[m.descripcion] = por_motivo.get(m.descripcion, 0.0) + p.horas_no_operadas
        if p.cantidad_procesada is not None:
            cantidad += p.cantidad_procesada
            hay_cantidad = True
    ini, fin = _rango(desde, hasta, tz)
    eventos = list(s.scalars(select(EventoFalla).where(
        EventoFalla.id_activo == id_activo, EventoFalla.estado == EstadoEvento.VALIDADO,
        EventoFalla.fecha_hora_falla >= ini, EventoFalla.fecha_hora_falla < fin)))
    n = len(eventos)
    mtbf = kpis.mtbf(operadas, n)
    mttr = kpis.mttr([e.tiempo_reparacion_h for e in eventos if e.tiempo_reparacion_h is not None])
    mttr_t = kpis.mttr_total([e.horas_parada or 0.0 for e in eventos], n)
    ao = kpis.disponibilidad_operacional(requeridas, paradas)
    rendimiento = None
    if hay_cantidad and a.ciclo_teorico_s and operadas > 0:
        rendimiento = min(1.0, cantidad * a.ciclo_teorico_s / 3600 / operadas)
    return KPIsMaquina(a.codigo, turno, requeridas, paradas, operadas, por_motivo, n, mtbf, mttr, mttr_t,
                       kpis.disponibilidad_inherente(mtbf, mttr), ao, rendimiento,
                       kpis.oee(ao, rendimiento, None), estimados, n_partes)


@dataclass
class KPIsLinea:
    ao: float | None
    mtbf: float | None
    mttr: float | None
    n_fallas: int
    horas_operadas: float
    maquinas: list[KPIsMaquina]


def kpis_linea(s: Session, desde: date, hasta: date, tz: ZoneInfo, ids: list[int] | None = None) -> KPIsLinea:
    consulta = select(Activo.id).where(Activo.activo.is_(True))
    if ids:
        consulta = consulta.where(Activo.id.in_(ids))
    maquinas = [kpis_maquina(s, i, desde, hasta, tz) for i in s.scalars(consulta)]
    req = sum(m.horas_requeridas for m in maquinas)
    par = sum(m.horas_paradas for m in maquinas)
    op = sum(m.horas_operadas for m in maquinas)
    n = sum(m.n_fallas for m in maquinas)
    reparaciones = [m.mttr * m.n_fallas for m in maquinas if m.mttr is not None]
    return KPIsLinea(kpis.disponibilidad_operacional(req, par), kpis.mtbf(op, n),
                     (sum(reparaciones) / n) if n and reparaciones else None, n, op, maquinas)


def calidad_de_datos(s: Session, id_activo: int, desde: date, hasta: date, laborables: int, tz: ZoneInfo) -> dict:
    """Indicador del Plan §11: % de partes completos y % de eventos validados en menos de 48 h."""
    partes = list(s.scalars(select(ParteTurno).where(ParteTurno.id_activo == id_activo,
                                                     ParteTurno.fecha.between(desde, hasta))))
    del_operario = sum(p.origen != "ESTIMADO_SISTEMA" for p in partes)
    ini, fin = _rango(desde, hasta, tz)
    validados = list(s.scalars(select(EventoFalla).where(
        EventoFalla.id_activo == id_activo, EventoFalla.estado == EstadoEvento.VALIDADO,
        EventoFalla.fecha_hora_falla >= ini, EventoFalla.fecha_hora_falla < fin)))
    rapidos = sum((e.validado_en - e.fecha_hora_falla) <= timedelta(hours=48) for e in validados if e.validado_en)
    return {
        "partes_completos": del_operario / laborables if laborables else None,
        "validados_48h": rapidos / len(validados) if validados else None,
        "partes_esperados": laborables,
        "partes_operario": del_operario,
    }
