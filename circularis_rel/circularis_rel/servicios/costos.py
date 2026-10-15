"""Costos calculados desde parámetros (Plan §12; D-008). El sistema no pide Cp ni Cf a mano.

- Costo de DECISIÓN (Cp/Cf de un tipo de componente y modo): precios y tarifas vigentes HOY. Se usa
  para el intervalo óptimo, el ranking y el riesgo; cambia solo cuando cambia un precio o una tarifa.
- Costo HISTÓRICO de cada falla: precios, tarifa y tipo de cambio vigentes a la FECHA del evento.
  Se usa en reportes, Pareto por costo y costo del mes. Desglose CTMC = CDMC + CLC (UNIDAD 3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import EstadoEvento, Moneda
from circularis_rel.datos.modelos import (
    Activo,
    ConsumoRepuesto,
    EventoFalla,
    OrdenTrabajo,
    PosicionComponente,
    PrecioRepuesto,
    Repuesto,
    TipoCambio,
    TipoComponente,
)
from circularis_rel.motor import costos as mc
from circularis_rel.servicios import parametros as P


def tipo_cambio(s: Session, fecha: date) -> float | None:
    tc = s.scalar(select(TipoCambio).where(TipoCambio.fecha <= fecha).order_by(TipoCambio.fecha.desc()).limit(1))
    if tc is None:
        tc = s.scalar(select(TipoCambio).order_by(TipoCambio.fecha).limit(1))
    return tc.ars_por_usd if tc else None


def _a_ars(s: Session, monto: float, moneda: Moneda | str | None, fecha: date) -> float | None:
    if moneda in (None, Moneda.ARS, "ARS"):
        return monto
    tc = tipo_cambio(s, fecha)
    return monto * tc if tc else None


def precio_repuesto_ars(s: Session, id_tipo_componente: int, fecha: date) -> float | None:
    """Precio del repuesto que reemplaza a ese tipo de componente, vigente a la fecha (en pesos)."""
    for rep in s.scalars(select(Repuesto).where(Repuesto.id_tipo_componente == id_tipo_componente).order_by(Repuesto.codigo)):
        p = s.scalar(select(PrecioRepuesto).where(PrecioRepuesto.id_repuesto == rep.id, PrecioRepuesto.fecha <= fecha)
                     .order_by(PrecioRepuesto.fecha.desc()).limit(1))
        if p is not None:
            return _a_ars(s, p.precio, p.moneda, fecha)
    return None


def horas_parada_tipicas(s: Session, id_tipo: int, id_modo: int | None, fecha: date | None = None) -> float | None:
    consulta = select(EventoFalla.horas_parada).join(PosicionComponente, PosicionComponente.id == EventoFalla.id_posicion).where(
        PosicionComponente.id_tipo_componente == id_tipo, EventoFalla.estado == EstadoEvento.VALIDADO,
        EventoFalla.horas_parada.is_not(None))
    if id_modo is not None:
        consulta = consulta.where(EventoFalla.id_modo == id_modo)
    valores = list(s.scalars(consulta))
    if valores:
        return sum(valores) / len(valores)
    return P.obtener(s, "costos.horas_parada_defecto_h", fecha)


@dataclass
class CostosDecision:
    cp: float | None
    cf: float | None
    faltan: list[str] = field(default_factory=list)
    detalle: dict = field(default_factory=dict)

    @property
    def completo(self) -> bool:
        return self.cp is not None and self.cf is not None


def costos_decision(s: Session, id_tipo: int, id_modo: int | None, id_activo: int, hoy: date | None = None) -> CostosDecision:
    hoy = hoy or date.today()
    tipo = s.get(TipoComponente, id_tipo)
    activo = s.get(Activo, id_activo)
    faltan = []
    precio = precio_repuesto_ars(s, id_tipo, hoy)
    tarifa = P.obtener(s, "costos.tarifa_mo_ars_h", hoy)
    margen = P.obtener(s, "costos.margen_linea_ars_h", hoy)
    parada = horas_parada_tipicas(s, id_tipo, id_modo, hoy)
    if precio is None:
        faltan.append("precio del repuesto")
    if tarifa is None:
        faltan.append("tarifa de mano de obra")
    if margen is None:
        faltan.append("margen por hora de la línea")
    if tipo.hh_preventiva is None or tipo.hh_correctiva is None:
        faltan.append("horas-hombre del componente")
    if parada is None:
        faltan.append("horas de parada típicas")
    if faltan:
        return CostosDecision(None, None, faltan)
    cp = mc.cp(precio, tipo.hh_preventiva, tarifa)
    cf = mc.cf(precio, tipo.hh_correctiva, tarifa, parada, activo.autonomia_pulmon_h or 0.0, margen)
    return CostosDecision(cp, cf, [], {"precio": precio, "tarifa": tarifa, "margen": margen, "horas_parada": parada,
                                       "pulmon": activo.autonomia_pulmon_h or 0.0})


@dataclass
class CostoEvento:
    ars: float | None
    usd: float | None
    desglose: mc.DesgloseCTMC | None
    faltan: list[str]


def costo_historico(s: Session, ev: EventoFalla) -> CostoEvento:
    """Costo de una falla a la fecha del evento (D-008)."""
    fecha = ev.fecha_hora_falla.date()
    faltan = []
    ot = s.scalar(select(OrdenTrabajo).where(OrdenTrabajo.id_evento == ev.id))
    cr = 0.0
    if ot is not None:
        for c in s.scalars(select(ConsumoRepuesto).where(ConsumoRepuesto.id_ot == ot.id)):
            if c.precio_unitario is None:
                faltan.append("precio de un repuesto usado")
                continue
            monto = _a_ars(s, c.precio_unitario * c.cantidad, c.moneda, fecha)
            cr += monto or 0.0
    tarifa = P.obtener(s, "costos.tarifa_mo_ars_h", fecha)
    margen = P.obtener(s, "costos.margen_linea_ars_h", fecha)
    hh = (ot.hh_propias if ot and ot.hh_propias is not None else ev.tiempo_reparacion_h) or 0.0
    if tarifa is None:
        faltan.append("tarifa de mano de obra")
    if margen is None:
        faltan.append("margen por hora de la línea")
    if tarifa is None or margen is None:
        return CostoEvento(None, None, None, faltan)
    activo = s.get(Activo, ev.id_activo)
    co = mc.lucro_cesante(ev.horas_parada or 0.0, activo.autonomia_pulmon_h or 0.0, margen)
    externo = (ot.costo_externo_ars or 0.0) if ot else 0.0
    d = mc.DesgloseCTMC(modm=hh * tarifa + externo, cr=cr, co=co)
    tc = tipo_cambio(s, fecha)
    return CostoEvento(d.ctmc, mc.a_dolares(d.ctmc, tc) if tc else None, d, faltan)
