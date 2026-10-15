"""Piloto (fase 2, Plan §10): uso real en las máquinas del piloto y criterio para pasar de fase.

Criterio del Plan: dos semanas seguidas con más del 90 % de los partes completos. "Completo" = cargado por
el operario (un parte estimado por el sistema no cuenta). Las semanas son de lunes a domingo, ya cerradas.
También se muestra el uso de los catálogos, para ajustarlos con el jefe: lo que nunca se usa sobra y lo que
se carga como "Otro" falta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import EstadoEvento, OrigenParte, TipoCatalogo
from circularis_rel.datos.modelos import Activo, Catalogo, EventoFalla, MotivoParada, ParteTurno
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios.turnos import laborables


@dataclass
class SemanaPartes:
    inicio: date
    fin: date
    esperados: int
    del_operario: int

    @property
    def fraccion(self) -> float | None:
        return self.del_operario / self.esperados if self.esperados else None


@dataclass
class EstadoMaquinaPiloto:
    id: int
    codigo: str
    semanas: list[SemanaPartes]
    cumple: bool
    validados_48h: float | None
    avisos_sin_validar: int


@dataclass
class EstadoPiloto:
    maquinas: list[EstadoMaquinaPiloto]
    minimo: float
    semanas_requeridas: int
    sin_maquinas_definidas: bool = False
    faltan_codigos: list[str] = field(default_factory=list)

    @property
    def cumple(self) -> bool:
        return bool(self.maquinas) and all(m.cumple for m in self.maquinas)


def maquinas_piloto(s: Session) -> tuple[list[Activo], list[str], bool]:
    """(máquinas del piloto que existen, códigos del parámetro que no existen, se usaron todas por defecto)."""
    codigos = P.obtener(s, "piloto.maquinas") or []
    activos = list(s.scalars(select(Activo).where(Activo.codigo.in_(codigos), Activo.activo.is_(True)).order_by(Activo.codigo)))
    faltan = [c for c in codigos if c not in {a.codigo for a in activos}]
    if not activos:
        return list(s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo))), faltan, True
    return activos, faltan, False


def semanas_cerradas(hoy: date, n: int) -> list[tuple[date, date]]:
    """Las últimas n semanas completas (lunes a domingo) antes de hoy, de la más vieja a la más nueva."""
    lunes_actual = hoy - timedelta(days=hoy.weekday())
    return [(lunes_actual - timedelta(weeks=k), lunes_actual - timedelta(weeks=k) + timedelta(days=6))
            for k in range(n, 0, -1)]


def semana_partes(s: Session, id_activo: int, inicio: date, fin: date) -> SemanaPartes:
    esperados = {(f, t.id) for f, t in laborables(s, id_activo, inicio, fin)}
    cargados = {(p.fecha, p.id_turno) for p in s.scalars(select(ParteTurno).where(
        ParteTurno.id_activo == id_activo, ParteTurno.fecha.between(inicio, fin), ParteTurno.origen != OrigenParte.ESTIMADO_SISTEMA))}
    return SemanaPartes(inicio, fin, len(esperados), len(esperados & cargados))


def estado(s: Session, hoy: date, tz: ZoneInfo, semanas_a_mostrar: int = 4) -> EstadoPiloto:
    minimo = P.obtener(s, "piloto.partes_minimo")
    requeridas = int(P.obtener(s, "piloto.semanas"))
    activos, faltan, por_defecto = maquinas_piloto(s)
    salida = []
    for a in activos:
        semanas = [semana_partes(s, a.id, i, f) for i, f in semanas_cerradas(hoy, max(semanas_a_mostrar, requeridas))]
        ultimas = semanas[-requeridas:]
        cumple = all(w.fraccion is not None and w.fraccion > minimo for w in ultimas)
        desde = datetime.combine(hoy - timedelta(days=28), time.min, tzinfo=tz)
        validados = list(s.scalars(select(EventoFalla).where(EventoFalla.id_activo == a.id, EventoFalla.estado == EstadoEvento.VALIDADO,
                                                             EventoFalla.fecha_hora_falla >= desde)))
        rapidos = sum((e.validado_en - e.fecha_hora_falla) <= timedelta(hours=48) for e in validados if e.validado_en)
        sin_validar = s.scalar(select(func.count()).select_from(EventoFalla).where(
            EventoFalla.id_activo == a.id, EventoFalla.estado == EstadoEvento.CERRADO))
        salida.append(EstadoMaquinaPiloto(a.id, a.codigo, semanas, cumple, rapidos / len(validados) if validados else None,
                                          sin_validar))
    return EstadoPiloto(salida, minimo, requeridas, por_defecto, faltan)


def uso_catalogos(s: Session, desde: date, hasta: date, tz: ZoneInfo) -> dict[str, list[dict]]:
    """Cuántas veces se usó cada síntoma, modo y causa (avisos no anulados) y cada motivo de parada (partes)."""
    ini = datetime.combine(desde, time.min, tzinfo=tz)
    fin = datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=tz)
    eventos = list(s.scalars(select(EventoFalla).where(EventoFalla.estado != EstadoEvento.ANULADO,
                                                       EventoFalla.fecha_hora_falla >= ini, EventoFalla.fecha_hora_falla < fin)))
    salida: dict[str, list[dict]] = {}
    for tipo, campo in ((TipoCatalogo.SINTOMA, "id_sintoma"), (TipoCatalogo.MODO, "id_modo"), (TipoCatalogo.CAUSA, "id_causa")):
        cuenta: dict[int, int] = {}
        for e in eventos:
            i = getattr(e, campo)
            if i is not None:
                cuenta[i] = cuenta.get(i, 0) + 1
        salida[tipo.value] = sorted(
            ({"codigo": c.codigo, "descripcion": c.descripcion, "usos": cuenta.get(c.id, 0), "activo": c.activo}
             for c in s.scalars(select(Catalogo).where(Catalogo.tipo == tipo))),
            key=lambda d: (-d["usos"], d["codigo"]))
    cuenta_m: dict[int, int] = {}
    for (i,) in s.execute(select(ParteTurno.id_motivo).where(ParteTurno.fecha.between(desde, hasta), ParteTurno.id_motivo.is_not(None))):
        cuenta_m[i] = cuenta_m.get(i, 0) + 1
    salida["MOTIVO"] = sorted(({"codigo": m.codigo, "descripcion": m.descripcion, "usos": cuenta_m.get(m.id, 0), "activo": m.activo}
                               for m in s.scalars(select(MotivoParada))), key=lambda d: (-d["usos"], d["codigo"]))
    return salida
