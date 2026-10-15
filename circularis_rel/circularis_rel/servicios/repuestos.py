"""Repuestos (Plan §8; UNIDAD 5): cuánto se va a necesitar y cuánto tener.

- **Demanda esperada en el lead time** = Σ, en cada componente que usa el repuesto, P(falla dentro del lead time
  dada su edad) + los preventivos programados dentro del lead time, por las unidades que lleva cada cambio.
  Un componente sin Weibull usa su tasa empírica (fallas / horas operadas) por las horas del lead time.
- **Stock mínimo:** el menor s con P(demanda ≤ s) ≥ nivel de servicio, con demanda Poisson.
- **Lote económico** q = √(2·K·D / (b·p)) y **stock de protección** Sp = H·√(c·d) de la UNIDAD 5 (diap. 56–68),
  con D = demanda anual esperada, K = costo de cada pedido, b = costo anual de almacenar ($ por $ inmovilizado),
  p = precio, H = factor del riesgo de rotura, c = consumo diario y d = demora en días. Sin K o b, "falta dato".
- Unidades por cambio: `cantidad_instalada` del repuesto en esa máquina; si no está, 1 (D-055).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import EstadoEvento, VariableEdad
from circularis_rel.datos.modelos import (
    Activo,
    EventoFalla,
    IntervencionProgramada,
    ParteTurno,
    PlanPreventivo,
    PosicionComponente,
    Repuesto,
    RepuestoActivo,
    TipoComponente,
)
from circularis_rel.motor import kpis, politicas
from circularis_rel.servicios import alertas, recalculo
from circularis_rel.servicios import costos as servicio_costos
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios import vidas as servicio_vidas


@dataclass
class EstadoRepuesto:
    id: int
    codigo: str
    descripcion: str
    uso: str | None
    stock: float | None
    stock_minimo_manual: float | None
    lead_time_dias: float | None
    precio: float | None
    demanda_lead: float | None
    stock_minimo: int | None
    demanda_anual: float | None
    lote_economico: float | None
    stock_proteccion: float | None
    faltan: list[str] = field(default_factory=list)
    detalle: list[str] = field(default_factory=list)

    @property
    def minimo_vigente(self) -> float | None:
        """El manual manda si está cargado; si no, el calculado."""
        return self.stock_minimo_manual if self.stock_minimo_manual is not None else self.stock_minimo

    @property
    def bajo_minimo(self) -> bool:
        return self.stock is not None and self.minimo_vigente is not None and self.stock < self.minimo_vigente


def _unidades(s: Session, id_repuesto: int, id_activo: int) -> float:
    c = s.scalar(select(RepuestoActivo.cantidad_instalada).where(RepuestoActivo.id_repuesto == id_repuesto,
                                                                 RepuestoActivo.id_activo == id_activo))
    return c or 1.0


def _tasa_empirica(s: Session, pos: PosicionComponente, hoy: date, tz: ZoneInfo, dias: int = 365) -> float | None:
    """Fallas por hora operada de esa posición en el último año (None si no hay horas)."""
    desde = hoy - timedelta(days=dias)
    horas = s.scalar(select(func.sum(ParteTurno.horas_operadas)).where(ParteTurno.id_activo == pos.id_activo,
                                                                       ParteTurno.fecha.between(desde, hoy)))
    if not horas:
        return None
    n = s.scalar(select(func.count()).select_from(EventoFalla).where(
        EventoFalla.id_posicion == pos.id, EventoFalla.estado == EstadoEvento.VALIDADO,
        EventoFalla.fecha_hora_falla >= datetime.combine(desde, time.min, tzinfo=tz)))
    return n / horas


def demanda(s: Session, rep: Repuesto, hoy: date, tz: ZoneInfo, dias: float) -> tuple[float | None, float | None, list[str]]:
    """(demanda esperada en `dias`, demanda anual esperada, detalle por componente)."""
    if rep.id_tipo_componente is None:
        return None, None, ["El repuesto no está asociado a un tipo de componente"]
    tipo = s.get(TipoComponente, rep.id_tipo_componente)
    toneladas = tipo.variable_edad == VariableEdad.TONELADAS
    total = anual = 0.0
    detalle = []
    sin_datos = []
    for pos in s.scalars(select(PosicionComponente).join(Activo, Activo.id == PosicionComponente.id_activo).where(
            PosicionComponente.id_tipo_componente == tipo.id, PosicionComponente.activa.is_(True), Activo.activo.is_(True))):
        codigo = s.get(Activo, pos.id_activo).codigo
        unidades = _unidades(s, rep.id, pos.id_activo)
        ritmo = recalculo.ritmo_diario(s, pos.id_activo, toneladas, hoy)
        if not ritmo:
            sin_datos.append(f"{codigo} · {pos.codigo}")
            continue
        uso = ritmo * dias
        ajustes = recalculo.ajustes_para_semaforo(s, tipo.id, pos.id_activo, pos.id)
        vida = servicio_vidas.vida_abierta(s, pos.id)
        edad = None
        if vida is not None and vida.edad_conocida:
            edad = (vida.edad_toneladas if toneladas else vida.edad_horas) or 0.0
        plan = s.scalar(select(PlanPreventivo).where(PlanPreventivo.id_posicion == pos.id, PlanPreventivo.vigente.is_(True),
                                                     PlanPreventivo.intervalo.is_not(None)).limit(1))
        programados = s.scalar(select(func.count()).select_from(IntervencionProgramada).where(
            IntervencionProgramada.id_plan == plan.id, IntervencionProgramada.fecha_prevista <= hoy + timedelta(days=dias))) if plan else 0
        if ajustes and edad is not None:
            p = kpis.prob_condicional_combinada(edad, uso, [(r.beta, r.eta, r.gamma or 0.0) for r in ajustes])
            vida_media = plan.intervalo if plan else min(kpis.mttf(r.beta, r.eta, r.gamma or 0.0) for r in ajustes)
            origen = "Weibull"
        else:
            tasa = _tasa_empirica(s, pos, hoy, tz)
            if tasa is None:
                sin_datos.append(f"{codigo} · {pos.codigo}")
                continue
            p = tasa * uso
            vida_media = plan.intervalo if plan else (1 / tasa if tasa > 0 else None)
            origen = "tasa empírica"
        esperado = (p + programados) * unidades
        total += esperado
        if vida_media:
            anual += ritmo * 365 / vida_media * unidades
        detalle.append(f"{codigo} · {pos.codigo}: {esperado:.2f} ({origen}; {programados} preventivo(s) programado(s); "
                       f"{unidades:g} u. por cambio)")
    if sin_datos:
        detalle.append("Sin datos de uso o de fallas: " + ", ".join(sin_datos))
    if not detalle or (sin_datos and len(detalle) == 1):
        return None, None, detalle
    return total, anual, detalle


def estado(s: Session, hoy: date, tz: ZoneInfo) -> list[EstadoRepuesto]:
    nivel = P.obtener(s, "politicas.nivel_servicio_stock")
    K = P.obtener(s, "repuestos.costo_pedido_ars")
    b = P.obtener(s, "repuestos.tasa_almacenamiento_anual")
    salida = []
    for rep in s.scalars(select(Repuesto).order_by(Repuesto.codigo)):
        faltan = []
        precio = servicio_costos.precio_repuesto_ars(s, rep.id_tipo_componente, hoy) if rep.id_tipo_componente else None
        if rep.lead_time_dias is None:
            faltan.append("lead time")
            dem_lead = None
            _d, anual, detalle = demanda(s, rep, hoy, tz, 1)
        else:
            dem_lead, anual, detalle = demanda(s, rep, hoy, tz, rep.lead_time_dias)
        minimo = politicas.stock_minimo_poisson(dem_lead, nivel) if dem_lead is not None else None
        eoq = sp = None
        if anual:
            if K is None:
                faltan.append("costo de cada pedido (K)")
            if b is None:
                faltan.append("costo anual de almacenamiento (b)")
            if precio is None:
                faltan.append("precio")
            if K is not None and b and precio:
                eoq = politicas.lote_economico(K, anual, b, precio)
            if rep.lead_time_dias:
                sp = politicas.stock_proteccion(1 - nivel, anual / 365, rep.lead_time_dias)
        salida.append(EstadoRepuesto(rep.id, rep.codigo, rep.descripcion, rep.uso.value if rep.uso else None, rep.stock_actual,
                                     rep.stock_minimo_manual, rep.lead_time_dias, precio, dem_lead, minimo, anual, eoq, sp,
                                     faltan, detalle))
    return salida


def alertas_stock(s: Session, hoy: date, tz: ZoneInfo) -> int:
    """Alerta diaria: stock menor al mínimo (demanda esperada en el lead time). Se resuelve sola al reponer."""
    n = 0
    for e in estado(s, hoy, tz):
        clave = f"stock:{e.id}"
        if e.bajo_minimo:
            alertas.emitir(s, "STOCK", "media", f"{e.codigo} ({e.descripcion}): stock {e.stock:g}, mínimo {e.minimo_vigente:g}",
                           clave, destinatarios="JEFE,ENCARGADO")
            n += 1
        else:
            alertas.resolver(s, clave)
    return n


def ajustar_stock(s: Session, id_repuesto: int, nuevo: float, motivo: str) -> Repuesto:
    """Conteo físico: el motivo queda en la auditoría (la sesión debe abrirse con ese motivo)."""
    if nuevo < 0:
        raise ValueError("El stock no puede ser negativo")
    if not motivo or not motivo.strip():
        raise ValueError("Indicá el motivo del ajuste")
    rep = s.get(Repuesto, id_repuesto)
    rep.stock_actual = nuevo
    s.flush()
    return rep
