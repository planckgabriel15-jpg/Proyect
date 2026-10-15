"""Partes faltantes (Plan §4, §11): aviso al encargado al día siguiente y, si sigue faltando,
se completa con las horas promedio por día del listado, marcado como estimado (nivel E, D-029)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import EstadoParte, NivelHora, OrigenParte
from circularis_rel.datos.modelos import Activo, MotivoParada, ParteTurno, Turno
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.turnos import laborables


@dataclass(frozen=True)
class Faltante:
    id_activo: int
    codigo: str
    fecha: date
    id_turno: int
    turno: str


def faltantes(s: Session, desde: date, hasta: date) -> list[Faltante]:
    salida = []
    for a in s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo)):
        hay = {(p.fecha, p.id_turno) for p in s.scalars(select(ParteTurno).where(
            ParteTurno.id_activo == a.id, ParteTurno.fecha.between(desde, hasta)))}
        for fecha, turno in laborables(s, a.id, desde, hasta):
            if (fecha, turno.id) not in hay:
                salida.append(Faltante(a.id, a.codigo, fecha, turno.id, turno.nombre))
    return salida


def completar_estimados(s: Session, hoy: date, tz: ZoneInfo, dias_atras: int = 30) -> int:
    """Completa los partes que siguen faltando pasados `partes.dias_para_estimar` días."""
    espera = int(P.obtener(s, "partes.dias_para_estimar"))
    hasta = hoy - timedelta(days=espera)
    desde = hasta - timedelta(days=dias_atras)
    motivo = s.scalar(select(MotivoParada.id).where(MotivoParada.codigo == "SIN_DATO"))
    n = 0
    pendientes = faltantes(s, desde, hasta)
    turnos_por_dia: dict[tuple[int, date], int] = {}
    for f in pendientes:
        turnos_por_dia[(f.id_activo, f.fecha)] = len(laborables(s, f.id_activo, f.fecha, f.fecha))
    for f in pendientes:
        a = s.get(Activo, f.id_activo)
        turno = s.get(Turno, f.id_turno)
        if a.horas_promedio_dia is None:
            continue  # sin promedio no se inventa nada: queda como faltante
        horas = min(turno.duracion_h, a.horas_promedio_dia / max(1, turnos_por_dia[(f.id_activo, f.fecha)]))
        horas = round(horas * 2) / 2
        no_op = turno.duracion_h - horas
        estado = EstadoParte.TODO if no_op == 0 else EstadoParte.NO_OPERO if horas == 0 else EstadoParte.PARCIAL
        s.add(ParteTurno(id_activo=a.id, fecha=f.fecha, id_turno=turno.id, horas_turno=turno.duracion_h, estado=estado,
                         horas_no_operadas=no_op, horas_operadas=horas, id_motivo=motivo if no_op > 0 else None,
                         nivel_hora=NivelHora.E, origen=OrigenParte.ESTIMADO_SISTEMA))
        n += 1
    s.flush()
    return n
