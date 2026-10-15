"""Vidas de componente: apertura, cierre y edad (Plan §3; D-009, D-026, D-028).

- Edad = suma de horas operadas (o toneladas) de los partes de la máquina entre la instalación y
  el fin. En los turnos de borde se prorratea por la fracción del turno que cae dentro de la vida.
- Nivel de hora de la vida = el peor de los partes que la componen (M < D < E).
- Si una posición no tiene vida abierta (componente instalado antes del sistema), se crea una con
  `edad_conocida = False`: el motor la excluye por defecto (Plan §5, edad desconocida).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import NivelHora, TipoFin, TipoReparacion
from circularis_rel.datos.modelos import (
    Activo,
    ParteTurno,
    PosicionComponente,
    Turno,
    VidaComponente,
)
from circularis_rel.servicios.turnos import ventana

_ORDEN_NIVEL = {NivelHora.M: 0, NivelHora.D: 1, NivelHora.E: 2}


def vida_abierta(s: Session, id_posicion: int) -> VidaComponente | None:
    return s.scalar(select(VidaComponente).where(VidaComponente.id_posicion == id_posicion,
                                                 VidaComponente.tipo_fin == TipoFin.EN_SERVICIO))


def asegurar_vida_abierta(s: Session, id_posicion: int, antes_de: datetime) -> VidaComponente:
    """Vida en servicio de la posición; si no hay, crea una de edad desconocida."""
    v = vida_abierta(s, id_posicion)
    if v is not None:
        return v
    pos = s.get(PosicionComponente, id_posicion)
    primer_parte = s.scalar(select(ParteTurno.fecha).where(ParteTurno.id_activo == pos.id_activo)
                            .order_by(ParteTurno.fecha).limit(1))
    inicio = antes_de - timedelta(seconds=1)
    if primer_parte is not None:
        inicio = min(inicio, datetime.combine(primer_parte, datetime.min.time(), tzinfo=antes_de.tzinfo))
    v = VidaComponente(id_posicion=id_posicion, fecha_instalacion=inicio, tipo_fin=TipoFin.EN_SERVICIO,
                       edad_conocida=False, nivel_hora=NivelHora.E)
    s.add(v)
    s.flush()
    return v


def iniciar_vidas(s: Session, momento: datetime | None = None) -> int:
    """Al empezar la captura: una vida en servicio (edad desconocida) por cada posición que no tenga."""
    momento = momento or ahora()
    n = 0
    for pos in s.scalars(select(PosicionComponente).where(PosicionComponente.activa.is_(True))):
        if vida_abierta(s, pos.id) is None:
            s.add(VidaComponente(id_posicion=pos.id, fecha_instalacion=momento, tipo_fin=TipoFin.EN_SERVICIO,
                                 edad_conocida=False, nivel_hora=NivelHora.E))
            n += 1
    s.flush()
    return n


def cerrar_y_abrir(s: Session, id_posicion: int, momento_fin: datetime, tipo_fin: TipoFin,
                   id_modo: int | None, *, reemplazo: bool, momento_nueva: datetime | None = None,
                   id_evento: int | None = None, id_ot: int | None = None) -> tuple[VidaComponente, VidaComponente]:
    """Cierra la vida en servicio y abre la siguiente (Plan §3: el evento cierra; la OT abre)."""
    if tipo_fin == TipoFin.EN_SERVICIO:
        raise ValueError("tipo_fin no puede ser EN_SERVICIO al cerrar")
    actual = asegurar_vida_abierta(s, id_posicion, momento_fin)
    if momento_fin < actual.fecha_instalacion:
        raise ValueError("La falla es anterior a la instalación del componente en servicio")
    actual.fecha_fin = momento_fin
    actual.tipo_fin = tipo_fin
    actual.id_modo_falla = id_modo if tipo_fin == TipoFin.FALLA else None
    actual.id_evento_cierre = id_evento
    actual.id_ot_cierre = id_ot
    s.flush()
    nueva = VidaComponente(id_posicion=id_posicion, fecha_instalacion=momento_nueva or momento_fin,
                           tipo_fin=TipoFin.EN_SERVICIO, id_ot_apertura=id_ot,
                           tipo_reparacion=TipoReparacion.REEMPLAZO if reemplazo else TipoReparacion.REPARACION_MINIMA)
    s.add(nueva)
    s.flush()
    return actual, nueva


def deshacer_cierre(s: Session, vida_cerrada: VidaComponente) -> None:
    """Anulación de un evento: borra la vida que se abrió después y reabre la cerrada."""
    siguiente = s.scalar(select(VidaComponente).where(
        VidaComponente.id_posicion == vida_cerrada.id_posicion, VidaComponente.fecha_instalacion >= vida_cerrada.fecha_fin,
        VidaComponente.id != vida_cerrada.id).order_by(VidaComponente.fecha_instalacion).limit(1))
    if siguiente is not None:
        if siguiente.tipo_fin != TipoFin.EN_SERVICIO:
            raise ValueError("No se puede anular: después de esta falla ya hubo otro cambio del mismo componente")
        s.delete(siguiente)
        s.flush()
    vida_cerrada.fecha_fin = None
    vida_cerrada.tipo_fin = TipoFin.EN_SERVICIO
    vida_cerrada.id_modo_falla = None
    vida_cerrada.id_evento_cierre = None
    vida_cerrada.id_ot_cierre = None
    vida_cerrada.validado = False
    s.flush()


def calcular_edad(s: Session, vida: VidaComponente, tz: ZoneInfo, hasta: datetime | None = None) -> tuple[float, float | None, NivelHora]:
    """(horas, toneladas o None, nivel de hora) de la vida, desde los partes de turno."""
    pos = s.get(PosicionComponente, vida.id_posicion)
    activo = s.get(Activo, pos.id_activo)
    inicio = vida.fecha_instalacion
    fin = vida.fecha_fin or hasta or ahora()
    if fin <= inicio:
        return 0.0, 0.0 if activo.factor_toneladas else None, NivelHora.D
    desde_fecha = inicio.astimezone(tz).date() - timedelta(days=1)
    hasta_fecha = fin.astimezone(tz).date()
    partes = s.execute(select(ParteTurno, Turno).join(Turno, Turno.id == ParteTurno.id_turno).where(
        ParteTurno.id_activo == pos.id_activo, ParteTurno.fecha.between(desde_fecha, hasta_fecha)))
    horas = 0.0
    toneladas = 0.0 if activo.factor_toneladas else None
    peor = NivelHora.M
    hubo = False
    for parte, turno in partes:
        ini_t, fin_t = ventana(parte.fecha, turno, tz)
        solape = (min(fin, fin_t) - max(inicio, ini_t)).total_seconds()
        if solape <= 0:
            continue
        fraccion = min(1.0, solape / (fin_t - ini_t).total_seconds())
        horas += parte.horas_operadas * fraccion
        if toneladas is not None and parte.cantidad_procesada is not None:
            toneladas += parte.cantidad_procesada * activo.factor_toneladas * fraccion
        if _ORDEN_NIVEL[parte.nivel_hora] > _ORDEN_NIVEL[peor]:
            peor = parte.nivel_hora
        hubo = True
    if not vida.edad_conocida:
        peor = NivelHora.E
    return round(horas, 4), (round(toneladas, 4) if toneladas is not None else None), (peor if hubo else NivelHora.D)


def actualizar_edad(s: Session, vida: VidaComponente, tz: ZoneInfo, hasta: datetime | None = None) -> None:
    vida.edad_horas, vida.edad_toneladas, vida.nivel_hora = calcular_edad(s, vida, tz, hasta)


def actualizar_edades(s: Session, tz: ZoneInfo, solo_abiertas: bool = False) -> int:
    consulta = select(VidaComponente)
    if solo_abiertas:
        consulta = consulta.where(VidaComponente.tipo_fin == TipoFin.EN_SERVICIO)
    n = 0
    for v in s.scalars(consulta):
        h, t, nivel = calcular_edad(s, v, tz)
        if (v.edad_horas, v.edad_toneladas, v.nivel_hora) != (h, t, nivel):
            v.edad_horas, v.edad_toneladas, v.nivel_hora = h, t, nivel
            n += 1
    s.flush()
    return n
