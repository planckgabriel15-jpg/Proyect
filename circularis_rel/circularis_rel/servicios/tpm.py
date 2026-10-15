"""TPM [12.F]: rendimiento operacional RO = Dp · Di · Rv · Tq (UNIDAD 4, diap. 31–34) y seis grandes pérdidas
(diap. 42–45), desde los partes de turno. Con las lecturas coherentes de B-003, B-004 y B-005:

- TT = tiempo requerido (horas de turno menos las que no cuentan: sin demanda, huelga, sin dato; D-007).
- TAP = paradas propias (preparación y ajuste, motivos `es_setup`). TR = TT − TAP. **Dp = TR / TT.**
- TAI = paradas inducidas o imprevistas (el resto de las horas no operadas que cuentan). **Di = (TR − TAI) / TR.**
- **Rv = ciclo teórico / ciclo real** = cantidad × ciclo teórico / horas operadas (≤ 1; B-004).
- **Tq = (piezas realizadas − rechazadas) / realizadas** (B-005).
- Sin cantidad o ciclo teórico, Rv queda "falta dato"; sin rechazadas cargadas, Tq también (no se supone 100 %).

Seis grandes pérdidas, en horas: averías, preparación y ajuste, vacío y paradas cortas y puesta en marcha salen de
los motivos de parada (su categoría); velocidad reducida = horas operadas × (1 − Rv); calidad y reproceso =
horas operadas × Rv × (1 − Tq) más las horas paradas por calidad. Lo que no tiene categoría va a "sin clasificar".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import Categoria6P
from circularis_rel.datos.modelos import Activo, MotivoParada, ParteTurno

NOMBRES_6P = {
    Categoria6P.AVERIA: "Averías",
    Categoria6P.PREPARACION_AJUSTE: "Preparación y ajuste",
    Categoria6P.VACIO_PARADAS_CORTAS: "Tiempo en vacío y paradas cortas",
    Categoria6P.VELOCIDAD_REDUCIDA: "Velocidad reducida",
    Categoria6P.CALIDAD_REPROCESO: "Defectos de calidad y reproceso",
    Categoria6P.PUESTA_EN_MARCHA: "Puesta en marcha",
}


@dataclass
class RendimientoOperacional:
    codigo: str
    tt: float
    tap: float
    tai: float
    horas_operadas: float
    cantidad: float | None
    rechazada: float | None
    dp: float | None
    di: float | None
    rv: float | None
    tq: float | None
    perdidas_h: dict[str, float] = field(default_factory=dict)
    faltan: list[str] = field(default_factory=list)

    @property
    def ro(self) -> float | None:
        valores = [self.dp, self.di, self.rv, self.tq]
        return None if any(v is None for v in valores) else self.dp * self.di * self.rv * self.tq


def calcular(s: Session, id_activo: int, desde: date, hasta: date) -> RendimientoOperacional:
    a = s.get(Activo, id_activo)
    motivos = {m.id: m for m in s.scalars(select(MotivoParada))}
    tt = tap = tai = operadas = 0.0
    cantidad = rechazada = 0.0
    hay_cantidad = hay_rechazada = False
    horas_cantidad = 0.0  # horas operadas de los partes con cantidad (para no mezclar con partes sin dato)
    perdidas = {nombre: 0.0 for nombre in NOMBRES_6P.values()} | {"Sin clasificar": 0.0}
    for p in s.scalars(select(ParteTurno).where(ParteTurno.id_activo == id_activo, ParteTurno.fecha.between(desde, hasta))):
        m = motivos.get(p.id_motivo) if p.id_motivo else None
        no_requeridas = p.horas_no_operadas if (m is not None and not m.cuenta_como_requerida) else 0.0
        tt += p.horas_turno - no_requeridas
        operadas += p.horas_operadas
        paradas = p.horas_no_operadas - no_requeridas
        if paradas > 0:
            if m is not None and m.es_setup:
                tap += paradas
            else:
                tai += paradas
            categoria = NOMBRES_6P.get(m.categoria_6p) if m is not None and m.categoria_6p else "Sin clasificar"
            perdidas[categoria] += paradas
        if p.cantidad_procesada is not None:
            hay_cantidad = True
            cantidad += p.cantidad_procesada
            horas_cantidad += p.horas_operadas
            if p.cantidad_rechazada is not None:
                hay_rechazada = True
                rechazada += p.cantidad_rechazada
    faltan = []
    tr = tt - tap
    dp = tr / tt if tt > 0 else None
    di = (tr - tai) / tr if tr > 0 else None
    rv = tq = None
    if not hay_cantidad:
        faltan.append("cantidad procesada en los partes")
    elif not a.ciclo_teorico_s:
        faltan.append("ciclo teórico de la máquina")
    elif horas_cantidad > 0:
        rv = min(1.0, cantidad * a.ciclo_teorico_s / 3600 / horas_cantidad)
    if hay_cantidad and not hay_rechazada:
        faltan.append("piezas rechazadas en los partes")
    elif hay_cantidad and cantidad > 0:
        tq = (cantidad - rechazada) / cantidad
    if rv is not None:
        perdidas[NOMBRES_6P[Categoria6P.VELOCIDAD_REDUCIDA]] += operadas * (1 - rv)
        if tq is not None:
            perdidas[NOMBRES_6P[Categoria6P.CALIDAD_REPROCESO]] += operadas * rv * (1 - tq)
    return RendimientoOperacional(a.codigo, tt, tap, tai, operadas, cantidad if hay_cantidad else None,
                                  rechazada if hay_rechazada else None, dp, di, rv, tq, perdidas, faltan)


def linea(s: Session, desde: date, hasta: date) -> list[RendimientoOperacional]:
    return [calcular(s, a.id, desde, hasta) for a in s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo))]
