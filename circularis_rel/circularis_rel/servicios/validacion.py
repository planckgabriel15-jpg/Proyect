"""Bandeja de validación del jefe (Plan §2, §11). Solo lo validado alimenta el cálculo.

Controles que ADVIERTEN al validar (los que bloquean ya están en la carga y en la base):
- reparación atípica: más de 3× el MTTR del modo (con al menos 3 antecedentes validados);
- vida atípica: edad < 5 % de η o > 3·η (si hay Weibull vigente del par);
- falla sin parada: hay parte del turno de la falla y no tiene horas no operadas;
- duplicado de aviso: misma máquina y posición con menos de 30 min;
- vida de edad desconocida (componente instalado antes del sistema).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, true
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import Alcance, EstadoEvento, EstadoOT, TipoOT
from circularis_rel.datos.modelos import (
    EventoFalla,
    OrdenTrabajo,
    ParteTurno,
    PosicionComponente,
    RecalculoPendiente,
    ResultadoWeibull,
    Usuario,
    VidaComponente,
)
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios import vidas
from circularis_rel.servicios.permisos import Accion, requerir
from circularis_rel.servicios.registro import ErrorRegistro
from circularis_rel.servicios.turnos import turno_en


@dataclass
class ItemBandeja:
    tipo: str  # "evento" | "ot"
    id: int
    id_activo: int
    momento: datetime
    horas_espera: float
    advertencias: list[str] = field(default_factory=list)


def encolar_recalculo(s: Session, id_tipo_componente: int, id_modo: int, id_activo: int | None, motivo: str) -> None:
    pendiente = s.scalar(select(RecalculoPendiente).where(
        RecalculoPendiente.id_tipo_componente == id_tipo_componente, RecalculoPendiente.id_modo == id_modo,
        RecalculoPendiente.id_activo == id_activo, RecalculoPendiente.tomado_en.is_(None)))
    if pendiente is None:
        s.add(RecalculoPendiente(id_tipo_componente=id_tipo_componente, id_modo=id_modo, id_activo=id_activo,
                                 alcance=Alcance.MAQUINA, motivo=motivo))


def _mttr_modo(s: Session, id_modo: int, excluir: int) -> tuple[float | None, int]:
    tiempos = [t for t in s.scalars(select(EventoFalla.tiempo_reparacion_h).where(
        EventoFalla.id_modo == id_modo, EventoFalla.estado == EstadoEvento.VALIDADO, EventoFalla.id != excluir))
        if t is not None]
    return (sum(tiempos) / len(tiempos), len(tiempos)) if tiempos else (None, 0)


def controles(s: Session, ev: EventoFalla, tz: ZoneInfo) -> list[str]:
    adv: list[str] = []
    if ev.id_modo and ev.tiempo_reparacion_h is not None:
        mttr, n = _mttr_modo(s, ev.id_modo, ev.id)
        factor = P.obtener(s, "validacion.factor_reparacion_atipica")
        if mttr and n >= 3 and ev.tiempo_reparacion_h > factor * mttr:
            adv.append(f"Reparación atípica: {ev.tiempo_reparacion_h:.1f} h, más de {factor:g}× el MTTR del modo ({mttr:.1f} h)")
    vida = s.scalar(select(VidaComponente).where(VidaComponente.id_evento_cierre == ev.id))
    if vida is not None:
        if not vida.edad_conocida:
            adv.append("El componente estaba instalado antes del sistema: edad desconocida (no entra al ajuste por defecto)")
        else:
            vidas.actualizar_edad(s, vida, tz)
            pos = s.get(PosicionComponente, vida.id_posicion)
            rw = s.scalar(select(ResultadoWeibull).where(
                ResultadoWeibull.id_tipo_componente == pos.id_tipo_componente, ResultadoWeibull.id_modo == ev.id_modo,
                ResultadoWeibull.vigente.is_(True), ResultadoWeibull.eta.is_not(None)).limit(1))
            if rw is not None and vida.edad_horas is not None:
                minimo = P.obtener(s, "validacion.vida_atipica_min_frac_eta") * rw.eta
                maximo = P.obtener(s, "validacion.vida_atipica_max_mult_eta") * rw.eta
                if vida.edad_horas < minimo:
                    adv.append(f"Vida atípica: {vida.edad_horas:.0f} h es menos del 5 % de η ({rw.eta:.0f} h). "
                               "¿Error de carga o mortalidad infantil (montaje, repuesto)?")
                elif vida.edad_horas > maximo:
                    adv.append(f"Vida atípica: {vida.edad_horas:.0f} h supera 3·η ({rw.eta:.0f} h). ¿Error de carga?")
    if ev.parada_total is not False:
        turno = turno_en(s, ev.fecha_hora_falla, tz)
        if turno is not None:
            parte = s.scalar(select(ParteTurno).where(ParteTurno.id_activo == ev.id_activo, ParteTurno.fecha == turno[0],
                                                      ParteTurno.id_turno == turno[1].id))
            if parte is not None and parte.horas_no_operadas == 0:
                adv.append("Falla sin parada: el parte de ese turno dice que la máquina operó todo el turno")
    minutos = P.obtener(s, "validacion.duplicado_aviso_min")
    duplicados = s.scalars(select(EventoFalla.id).where(
        EventoFalla.id != ev.id, EventoFalla.id_activo == ev.id_activo, EventoFalla.estado != EstadoEvento.ANULADO,
        EventoFalla.id_posicion == ev.id_posicion if ev.id_posicion else true(),
        EventoFalla.fecha_hora_falla.between(ev.fecha_hora_falla - timedelta(minutes=minutos),
                                             ev.fecha_hora_falla + timedelta(minutes=minutos)))).all()
    if duplicados:
        adv.append(f"Posible duplicado: hay otro aviso de la misma máquina a menos de {minutos} min (n.º {duplicados[0]})")
    return adv


def bandeja(s: Session, tz: ZoneInfo) -> list[ItemBandeja]:
    momento = ahora()
    limite = P.obtener(s, "validacion.eventos_sin_validar_h")
    items: list[ItemBandeja] = []
    for ev in s.scalars(select(EventoFalla).where(EventoFalla.estado == EstadoEvento.CERRADO)
                        .order_by(EventoFalla.fecha_hora_falla)):
        espera = (momento - ev.actualizado_en).total_seconds() / 3600
        adv = controles(s, ev, tz)
        if espera > limite:
            adv.insert(0, f"Esperando validación hace más de {limite} h")
        items.append(ItemBandeja("evento", ev.id, ev.id_activo, ev.fecha_hora_falla, espera, adv))
    for ot in s.scalars(select(OrdenTrabajo).where(OrdenTrabajo.estado == EstadoOT.CERRADA,
                                                   OrdenTrabajo.tipo != TipoOT.CORRECTIVA).order_by(OrdenTrabajo.fin_real)):
        espera = (momento - ot.actualizado_en).total_seconds() / 3600
        adv = [f"Esperando validación hace más de {limite} h"] if espera > limite else []
        items.append(ItemBandeja("ot", ot.id, ot.id_activo, ot.fin_real or ot.creado_en, espera, adv))
    return items


def _jefe(s: Session, id_usuario: int, accion: Accion = Accion.VALIDAR_EVENTO) -> Usuario:
    u = s.get(Usuario, id_usuario)
    if u is None:
        raise ErrorRegistro("Usuario no válido")
    requerir(u.rol, accion)
    return u


def _vida_de(s: Session, *, id_evento: int | None = None, id_ot: int | None = None) -> VidaComponente | None:
    if id_evento is not None:
        return s.scalar(select(VidaComponente).where(VidaComponente.id_evento_cierre == id_evento))
    return s.scalar(select(VidaComponente).where(VidaComponente.id_ot_cierre == id_ot))


def validar_evento(s: Session, id_usuario: int, id_evento: int) -> None:
    u = _jefe(s, id_usuario)
    ev = s.get(EventoFalla, id_evento)
    if ev is None or ev.estado != EstadoEvento.CERRADO:
        raise ErrorRegistro("Solo se validan avisos cerrados")
    ev.estado = EstadoEvento.VALIDADO
    ev.id_usuario_validacion = u.id
    ev.validado_en = ahora()
    ot = s.scalar(select(OrdenTrabajo).where(OrdenTrabajo.id_evento == ev.id))
    if ot is not None:
        ot.estado = EstadoOT.VALIDADA
    vida = _vida_de(s, id_evento=ev.id)
    if vida is not None:
        vida.validado = True
        pos = s.get(PosicionComponente, vida.id_posicion)
        encolar_recalculo(s, pos.id_tipo_componente, ev.id_modo, pos.id_activo, f"Validación del aviso {ev.id}")
    s.flush()


def validar_ot(s: Session, id_usuario: int, id_ot: int) -> None:
    _jefe(s, id_usuario)
    ot = s.get(OrdenTrabajo, id_ot)
    if ot is None or ot.estado != EstadoOT.CERRADA or ot.tipo == TipoOT.CORRECTIVA:
        raise ErrorRegistro("Solo se validan OT no correctivas cerradas desde acá")
    ot.estado = EstadoOT.VALIDADA
    vida = _vida_de(s, id_ot=ot.id)
    if vida is not None:
        vida.validado = True
        pos = s.get(PosicionComponente, vida.id_posicion)
        # Una suspensión afecta a todos los modos del componente: se recalculan los modos con historia.
        modos = set(s.scalars(select(VidaComponente.id_modo_falla).join(
            PosicionComponente, PosicionComponente.id == VidaComponente.id_posicion).where(
            PosicionComponente.id_tipo_componente == pos.id_tipo_componente, VidaComponente.id_modo_falla.is_not(None))))
        for m in modos:
            encolar_recalculo(s, pos.id_tipo_componente, m, pos.id_activo, f"Validación de la OT {ot.numero}")
    s.flush()


def devolver_evento(s: Session, id_usuario: int, id_evento: int, motivo: str) -> None:
    _jefe(s, id_usuario)
    if not motivo or not motivo.strip():
        raise ErrorRegistro("Indicá por qué se devuelve")
    ev = s.get(EventoFalla, id_evento)
    if ev is None or ev.estado != EstadoEvento.CERRADO:
        raise ErrorRegistro("Solo se devuelven avisos cerrados sin validar")
    ev.estado = EstadoEvento.DEVUELTO
    ev.observaciones = ((ev.observaciones or "") + f"\nDevuelto por el jefe: {motivo.strip()}").strip()
    ot = s.scalar(select(OrdenTrabajo).where(OrdenTrabajo.id_evento == ev.id))
    if ot is not None:
        ot.estado = EstadoOT.EN_EJECUCION
    s.flush()


def corregir_evento(s: Session, id_usuario: int, id_evento: int, cambios: dict, motivo: str) -> None:
    """Corrección de un evento ya validado (exige motivo; la sesión debe abrirse con ese motivo)."""
    _jefe(s, id_usuario, Accion.CORREGIR_VALIDADO)
    if not motivo or not motivo.strip():
        raise ErrorRegistro("Corregir un evento validado exige un motivo")
    s.info["motivo"] = motivo.strip()
    ev = s.get(EventoFalla, id_evento)
    if ev is None or ev.estado != EstadoEvento.VALIDADO:
        raise ErrorRegistro("Solo se corrigen eventos validados")
    permitidos = {"id_modo", "id_causa", "inicio_reparacion", "fin_reparacion", "efecto", "capacidad", "aparicion",
                  "observaciones", "parada_total"}
    if set(cambios) - permitidos:
        raise ErrorRegistro(f"No se puede corregir: {', '.join(sorted(set(cambios) - permitidos))}")
    vida = _vida_de(s, id_evento=ev.id)
    pos = s.get(PosicionComponente, ev.id_posicion)
    modo_anterior = ev.id_modo
    for k, v in cambios.items():
        setattr(ev, k, v)
    if ev.inicio_reparacion and ev.fin_reparacion:
        if ev.fin_reparacion <= ev.inicio_reparacion or ev.inicio_reparacion < ev.fecha_hora_falla:
            raise ErrorRegistro("Fechas de reparación incoherentes")
        ev.tiempo_reparacion_h = round((ev.fin_reparacion - ev.inicio_reparacion).total_seconds() / 3600, 4)
        ev.tiempo_espera_h = round((ev.inicio_reparacion - ev.fecha_hora_falla).total_seconds() / 3600, 4)
        ev.horas_parada = round((ev.fin_reparacion - ev.fecha_hora_falla).total_seconds() / 3600, 4) \
            if ev.parada_total is not False else 0.0
    if vida is not None and "id_modo" in cambios:
        vida.id_modo_falla = ev.id_modo
    s.flush()
    for m in {modo_anterior, ev.id_modo}:
        encolar_recalculo(s, pos.id_tipo_componente, m, pos.id_activo, f"Corrección del aviso {ev.id}")


def anular_evento(s: Session, id_usuario: int, id_evento: int, motivo: str) -> None:
    """Anula un aviso (duplicado, error). Si ya había cerrado una vida, la reabre."""
    _jefe(s, id_usuario, Accion.CORREGIR_VALIDADO)
    if not motivo or not motivo.strip():
        raise ErrorRegistro("Anular exige un motivo")
    s.info["motivo"] = motivo.strip()
    ev = s.get(EventoFalla, id_evento)
    if ev is None or ev.estado == EstadoEvento.ANULADO:
        raise ErrorRegistro("El aviso no existe o ya está anulado")
    vida = _vida_de(s, id_evento=ev.id)
    era_validado = ev.estado == EstadoEvento.VALIDADO
    if vida is not None:
        vidas.deshacer_cierre(s, vida)
    if era_validado and ev.id_posicion and ev.id_modo:
        pos = s.get(PosicionComponente, ev.id_posicion)
        encolar_recalculo(s, pos.id_tipo_componente, ev.id_modo, pos.id_activo, f"Anulación del aviso {ev.id}")
    ev.estado = EstadoEvento.ANULADO
    ot = s.scalar(select(OrdenTrabajo).where(OrdenTrabajo.id_evento == ev.id))
    if ot is not None:
        ot.observaciones = ((ot.observaciones or "") + f"\nAnulada: {motivo.strip()}").strip()
    s.flush()
