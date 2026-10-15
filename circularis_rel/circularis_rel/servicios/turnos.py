"""Turnos: ventana horaria de cada turno, turno por defecto según la hora y turnos laborables."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.modelos import ActivoTurno, Feriado, Turno


def ventana(fecha: date, turno: Turno, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """Inicio y fin del turno de esa fecha (si cruza la medianoche, termina al día siguiente)."""
    inicio = datetime.combine(fecha, turno.hora_inicio, tzinfo=tz)
    fin = datetime.combine(fecha, turno.hora_fin, tzinfo=tz)
    if fin <= inicio:
        fin += timedelta(days=1)
    return inicio, fin


def turno_en(s: Session, momento: datetime, tz: ZoneInfo, ids_turno: list[int] | None = None) -> tuple[date, Turno] | None:
    """Turno (y fecha del turno) que contiene ese momento; None si cae fuera de todos."""
    local = momento.astimezone(tz)
    consulta = select(Turno).where(Turno.activo.is_(True))
    if ids_turno:
        consulta = consulta.where(Turno.id.in_(ids_turno))
    for turno in s.scalars(consulta.order_by(Turno.hora_inicio)):
        for fecha in (local.date(), local.date() - timedelta(days=1)):
            ini, fin = ventana(fecha, turno, tz)
            if ini <= local < fin:
                return fecha, turno
    return None


def turno_por_defecto(s: Session, momento: datetime, tz: ZoneInfo, ids_turno: list[int] | None = None) -> tuple[date, Turno] | None:
    """El turno que está terminando o terminó más recientemente (el parte se carga al final del turno)."""
    actual = turno_en(s, momento, tz, ids_turno)
    if actual is not None:
        return actual
    local = momento.astimezone(tz)
    mejor: tuple[datetime, date, Turno] | None = None
    consulta = select(Turno).where(Turno.activo.is_(True))
    if ids_turno:
        consulta = consulta.where(Turno.id.in_(ids_turno))
    for turno in s.scalars(consulta):
        for fecha in (local.date(), local.date() - timedelta(days=1)):
            _ini, fin = ventana(fecha, turno, tz)
            if fin <= local and (mejor is None or fin > mejor[0]):
                mejor = (fin, fecha, turno)
    return (mejor[1], mejor[2]) if mejor else None


def turnos_de_activo(s: Session, id_activo: int) -> list[tuple[Turno, set[int]]]:
    filas = s.execute(select(Turno, ActivoTurno.dias).join(ActivoTurno, ActivoTurno.id_turno == Turno.id)
                      .where(ActivoTurno.id_activo == id_activo, Turno.activo.is_(True)).order_by(Turno.hora_inicio))
    return [(t, {int(d) for d in dias.split(",") if d.strip()}) for t, dias in filas]


def laborables(s: Session, id_activo: int, desde: date, hasta: date) -> list[tuple[date, Turno]]:
    """Pares (fecha, turno) en que la máquina debería tener parte, sin feriados."""
    feriados = set(s.scalars(select(Feriado.fecha).where(Feriado.fecha.between(desde, hasta))))
    turnos = turnos_de_activo(s, id_activo)
    salida = []
    dia = desde
    while dia <= hasta:
        if dia not in feriados:
            salida += [(dia, t) for t, dias in turnos if dia.isoweekday() in dias]
        dia += timedelta(days=1)
    return salida


def etiqueta(fecha: date, turno: Turno, hoy: date) -> str:
    cuando = "Hoy" if fecha == hoy else "Ayer" if fecha == hoy - timedelta(days=1) else fecha.strftime("%d/%m")
    return f"{cuando} · {turno.nombre} ({turno.hora_inicio:%H:%M}–{turno.hora_fin:%H:%M})"


def hora(h: str) -> time:
    return datetime.strptime(h, "%H:%M").time()
