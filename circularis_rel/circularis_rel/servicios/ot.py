"""Órdenes de trabajo (Plan §8): correctivas desde un aviso, cambios preventivos y retiros.

Estados: SOLICITADA → PLANIFICADA → EN_EJECUCION → CERRADA → VALIDADA.
Al cerrar una OT se cierra la vida del componente (FALLA o suspensión) y se abre la siguiente;
la vida queda `validado = False` hasta que el jefe valida (D-026).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import (
    AccionOT,
    AparicionFalla,
    CapacidadFalla,
    EfectoFalla,
    EstadoEvento,
    EstadoOT,
    TipoCatalogo,
    TipoFin,
    TipoOT,
)
from circularis_rel.datos.modelos import (
    Catalogo,
    CatalogoAplica,
    ConsumoRepuesto,
    EventoFalla,
    OrdenTrabajo,
    PosicionComponente,
    PrecioRepuesto,
    Repuesto,
    Usuario,
    VidaComponente,
)
from circularis_rel.servicios import vidas
from circularis_rel.servicios.permisos import Accion, requerir
from circularis_rel.servicios.registro import ErrorRegistro


def nuevo_numero(s: Session, momento: datetime | None = None) -> str:
    anio = (momento or ahora()).year
    n = s.scalar(select(func.count()).select_from(OrdenTrabajo).where(OrdenTrabajo.numero.like(f"OT-{anio}-%")))
    return f"OT-{anio}-{n + 1:05d}"


def _usuario(s: Session, id_usuario: int, accion: Accion) -> Usuario:
    u = s.get(Usuario, id_usuario)
    if u is None or not u.activo:
        raise ErrorRegistro("Usuario no válido")
    requerir(u.rol, accion)
    return u


def ot_de_evento(s: Session, ev: EventoFalla) -> OrdenTrabajo | None:
    return s.scalar(select(OrdenTrabajo).where(OrdenTrabajo.id_evento == ev.id))


def tomar_aviso(s: Session, id_usuario: int, id_evento: int) -> OrdenTrabajo:
    """El encargado toma el aviso: queda EN_REPARACION y se crea la OT correctiva."""
    u = _usuario(s, id_usuario, Accion.CERRAR_OT)
    ev = s.get(EventoFalla, id_evento)
    if ev is None or ev.estado not in (EstadoEvento.AVISADO, EstadoEvento.EN_REPARACION, EstadoEvento.DEVUELTO):
        raise ErrorRegistro("El aviso no está abierto")
    ot = ot_de_evento(s, ev)
    if ot is None:
        ot = OrdenTrabajo(numero=nuevo_numero(s), tipo=TipoOT.CORRECTIVA, id_activo=ev.id_activo, id_evento=ev.id,
                          estado=EstadoOT.EN_EJECUCION, responsable=u.nombre, inicio_real=ahora())
        s.add(ot)
    if ev.estado == EstadoEvento.AVISADO:
        ev.estado = EstadoEvento.EN_REPARACION
    s.flush()
    return ot


def modos_de_posicion(s: Session, id_posicion: int) -> list[Catalogo]:
    pos = s.get(PosicionComponente, id_posicion)
    return list(s.scalars(select(Catalogo).join(CatalogoAplica, CatalogoAplica.id_catalogo == Catalogo.id).where(
        Catalogo.tipo == TipoCatalogo.MODO, Catalogo.activo.is_(True),
        CatalogoAplica.id_tipo_componente == pos.id_tipo_componente).order_by(Catalogo.descripcion)))


def causas_de_posicion(s: Session, id_posicion: int) -> list[Catalogo]:
    pos = s.get(PosicionComponente, id_posicion)
    restringidas = select(CatalogoAplica.id_catalogo)
    propias = select(CatalogoAplica.id_catalogo).where(CatalogoAplica.id_tipo_componente == pos.id_tipo_componente)
    return list(s.scalars(select(Catalogo).where(
        Catalogo.tipo == TipoCatalogo.CAUSA, Catalogo.activo.is_(True),
        Catalogo.id.not_in(restringidas) | Catalogo.id.in_(propias)).order_by(Catalogo.descripcion)))


@dataclass
class CierreOT:
    """Datos del cierre: paso 1 (obligatorio) y paso 2 (con valores por defecto, D-010)."""

    id_posicion: int
    id_modo: int
    id_causa: int
    accion: AccionOT
    inicio: datetime
    fin: datetime
    repuestos: list[tuple[int, float]] = field(default_factory=list)  # (id_repuesto, cantidad)
    efecto: EfectoFalla | None = None
    capacidad: CapacidadFalla | None = None
    aparicion: AparicionFalla | None = None
    hh: float | None = None
    observaciones: str | None = None


def _consumir(s: Session, ot: OrdenTrabajo, repuestos: list[tuple[int, float]], cuando: datetime) -> None:
    for id_rep, cant in repuestos:
        if cant <= 0:
            continue
        rep = s.get(Repuesto, id_rep)
        if rep is None:
            raise ErrorRegistro("Repuesto no válido")
        precio = s.scalar(select(PrecioRepuesto).where(PrecioRepuesto.id_repuesto == id_rep,
                                                       PrecioRepuesto.fecha <= cuando.date())
                          .order_by(PrecioRepuesto.fecha.desc()).limit(1))
        s.add(ConsumoRepuesto(id_ot=ot.id, id_repuesto=id_rep, cantidad=cant, fecha=cuando.date(),
                              precio_unitario=precio.precio if precio else None,
                              moneda=precio.moneda if precio else None))
        if rep.stock_actual is not None:
            rep.stock_actual = max(0.0, rep.stock_actual - cant)


def cerrar_correctiva(s: Session, id_usuario: int, id_evento: int, d: CierreOT) -> EventoFalla:
    u = _usuario(s, id_usuario, Accion.CERRAR_OT)
    ev = s.get(EventoFalla, id_evento)
    if ev is None or ev.estado not in (EstadoEvento.AVISADO, EstadoEvento.EN_REPARACION, EstadoEvento.DEVUELTO):
        raise ErrorRegistro("El aviso no está abierto")
    pos = s.get(PosicionComponente, d.id_posicion)
    if pos is None or pos.id_activo != ev.id_activo:
        raise ErrorRegistro("El componente no es de la máquina del aviso")
    if d.id_modo not in {m.id for m in modos_de_posicion(s, d.id_posicion)}:
        raise ErrorRegistro("El modo de falla no corresponde a ese componente")
    if d.id_causa not in {c.id for c in causas_de_posicion(s, d.id_posicion)}:
        raise ErrorRegistro("La causa no corresponde a ese componente")
    if d.inicio < ev.fecha_hora_falla:
        raise ErrorRegistro("La reparación no puede empezar antes de la falla")
    if d.fin <= d.inicio:
        raise ErrorRegistro("El fin de la reparación tiene que ser posterior al inicio")
    if d.fin > ahora():
        raise ErrorRegistro("El fin de la reparación no puede ser futuro")
    if d.accion not in (AccionOT.REEMPLAZO, AccionOT.REPARACION_MINIMA, AccionOT.AJUSTE):
        raise ErrorRegistro("Acción no válida para una correctiva")
    reabierto = ev.estado == EstadoEvento.DEVUELTO
    ot = tomar_aviso(s, id_usuario, id_evento)  # crea la OT si no existe; respeta el estado DEVUELTO
    ev.id_posicion = d.id_posicion
    ev.id_modo = d.id_modo
    ev.id_causa = d.id_causa
    ev.inicio_reparacion = d.inicio
    ev.fin_reparacion = d.fin
    ev.tiempo_reparacion_h = round((d.fin - d.inicio).total_seconds() / 3600, 4)
    ev.tiempo_espera_h = round((d.inicio - ev.fecha_hora_falla).total_seconds() / 3600, 4)
    ev.horas_parada = round((d.fin - ev.fecha_hora_falla).total_seconds() / 3600, 4) if ev.parada_total is not False else 0.0
    ev.efecto, ev.capacidad, ev.aparicion = d.efecto, d.capacidad, d.aparicion
    if d.observaciones:
        ev.observaciones = ((ev.observaciones or "") + "\n" + d.observaciones).strip()
    ev.estado = EstadoEvento.CERRADO
    ev.id_usuario_cierre = u.id
    ot.estado = EstadoOT.CERRADA
    ot.id_posicion = d.id_posicion
    ot.accion = d.accion
    ot.inicio_real, ot.fin_real = d.inicio, d.fin
    ot.hh_propias = d.hh if d.hh is not None else ev.tiempo_reparacion_h
    s.flush()
    if reabierto:  # corregido tras devolución: rehacer la vida que se había cerrado
        previa = s.scalar(select(VidaComponente).where(VidaComponente.id_evento_cierre == ev.id))
        if previa is not None:
            vidas.deshacer_cierre(s, previa)
        for c in s.scalars(select(ConsumoRepuesto).where(ConsumoRepuesto.id_ot == ot.id)):
            s.delete(c)
        s.flush()
    vidas.cerrar_y_abrir(s, d.id_posicion, ev.fecha_hora_falla, TipoFin.FALLA, d.id_modo,
                         reemplazo=d.accion == AccionOT.REEMPLAZO, momento_nueva=d.fin, id_evento=ev.id, id_ot=ot.id)
    _consumir(s, ot, d.repuestos, d.fin)
    s.flush()
    return ev


def registrar_cambio(s: Session, id_usuario: int, id_posicion: int, momento: datetime, *, preventivo: bool = True,
                     hh: float | None = None, repuestos: list[tuple[int, float]] | None = None,
                     observaciones: str | None = None) -> OrdenTrabajo:
    """Cambio sin falla: preventivo (SUSPENSION_PREVENTIVA) u otro retiro (SUSPENSION_OTRA)."""
    u = _usuario(s, id_usuario, Accion.CERRAR_OT)
    pos = s.get(PosicionComponente, id_posicion)
    if pos is None:
        raise ErrorRegistro("Componente no válido")
    if momento > ahora():
        raise ErrorRegistro("La fecha del cambio no puede ser futura")
    ot = OrdenTrabajo(numero=nuevo_numero(s, momento), tipo=TipoOT.PREVENTIVA if preventivo else TipoOT.INSPECCION,
                      id_activo=pos.id_activo, id_posicion=id_posicion, estado=EstadoOT.CERRADA,
                      responsable=u.nombre, inicio_real=momento, fin_real=momento, hh_propias=hh,
                      accion=AccionOT.REEMPLAZO, observaciones=observaciones, fecha_programada=momento.date())
    s.add(ot)
    s.flush()
    vidas.cerrar_y_abrir(s, id_posicion, momento,
                         TipoFin.SUSPENSION_PREVENTIVA if preventivo else TipoFin.SUSPENSION_OTRA, None,
                         reemplazo=True, id_ot=ot.id)
    _consumir(s, ot, repuestos or [], momento)
    s.flush()
    return ot
