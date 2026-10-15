"""La máquina como sistema reparable (Plan §5 y §7; fase 4): Crow-AMSAA y prueba de Laplace sobre las fallas
validadas, con el tiempo medido en horas operadas acumuladas (de los partes de turno).

- Crow-AMSAA β > 1: la máquina se degrada (las fallas se aceleran); β < 1: mejora; ≈ 1: estable.
- Laplace U > 0 con p chico: tendencia a fallar más seguido. Se pide al menos `sistemas.min_fallas` fallas.
- La hora de cada falla se ubica sumando las horas de los días anteriores y la mitad de las de ese día (los partes
  son por turno, no por hora; el error es de unas pocas horas sobre cientos).
- Una máquina con tendencia a degradarse y significativa (p < `sistemas.p_tendencia`) genera la alerta semanal
  "tendencia en degradación" (Plan §7).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.modelos import Activo, ParteTurno, ResultadoSistema
from circularis_rel.motor import sistemas as M
from circularis_rel.motor import weibull as W
from circularis_rel.servicios import alertas, panel
from circularis_rel.servicios import parametros as P


@dataclass
class Tendencia:
    codigo: str
    n: int
    T: float
    tiempos: list[float]
    crow: M.CrowAMSAA | None
    laplace_u: float | None
    laplace_p: float | None
    texto: str

    @property
    def degradacion(self) -> bool:
        return self.laplace_u is not None and self.laplace_u > 0 and self.laplace_p is not None and self.laplace_p < 0.05


def tiempos_de_falla(s: Session, id_activo: int, desde: date, hasta: date, tz: ZoneInfo) -> tuple[list[float], float]:
    """(horas operadas acumuladas en cada falla validada, horas operadas totales del período)."""
    por_dia: dict[date, float] = defaultdict(float)
    for fecha, horas in s.execute(select(ParteTurno.fecha, ParteTurno.horas_operadas).where(
            ParteTurno.id_activo == id_activo, ParteTurno.fecha.between(desde, hasta))):
        por_dia[fecha] += horas or 0.0
    dias = sorted(por_dia)
    acumulado, antes = 0.0, {}
    for d in dias:
        antes[d] = acumulado
        acumulado += por_dia[d]
    tiempos = []
    for ev in panel.eventos_validados(s, desde, hasta, tz, id_activo):
        d = ev.fecha_hora_falla.astimezone(tz).date()
        previos = [x for x in dias if x <= d]
        if not previos:
            continue
        ultimo = previos[-1]
        t = antes[ultimo] + (por_dia[ultimo] / 2 if ultimo == d else por_dia[ultimo])
        if t > 0:
            tiempos.append(t)
    return sorted(tiempos), acumulado


def analizar(s: Session, id_activo: int, desde: date, hasta: date, tz: ZoneInfo) -> Tendencia:
    a = s.get(Activo, id_activo)
    tiempos, T = tiempos_de_falla(s, id_activo, desde, hasta, tz)
    minimo = int(P.obtener(s, "sistemas.min_fallas"))
    if len(tiempos) < minimo or T <= 0:
        return Tendencia(a.codigo, len(tiempos), T, tiempos, None, None, None,
                         f"Hacen falta al menos {minimo} fallas validadas en el período para ver la tendencia")
    crow = M.crow_amsaa(tiempos, T)
    u, p = M.laplace(tiempos, T)
    if u > 0 and p < P.obtener(s, "sistemas.p_tendencia"):
        texto = f"Se degrada: las fallas se aceleran (β de Crow-AMSAA = {crow.beta:.2f}; Laplace U = {u:.2f}, p = {p:.3f})"
    elif u < 0 and p < P.obtener(s, "sistemas.p_tendencia"):
        texto = f"Mejora: las fallas se espacian (β = {crow.beta:.2f}; U = {u:.2f}, p = {p:.3f})"
    else:
        texto = f"Sin tendencia clara (β = {crow.beta:.2f}; U = {u:.2f}, p = {p:.3f})"
    return Tendencia(a.codigo, len(tiempos), T, tiempos, crow, u, p, texto)


def recalcular(s: Session, desde: date, hasta: date, tz: ZoneInfo) -> list[Tendencia]:
    """Guarda el resultado de cada máquina y emite o resuelve la alerta de degradación (semanal)."""
    salida = []
    umbral = P.obtener(s, "sistemas.p_tendencia")
    for a in s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo)):
        t = analizar(s, a.id, desde, hasta, tz)
        salida.append(t)
        clave = f"degradacion:{a.id}"
        if t.crow is None:
            alertas.resolver(s, clave)
            continue
        s.add(ResultadoSistema(id_activo=a.id, periodo_desde=desde, periodo_hasta=hasta, n_fallas=t.n, beta=t.crow.beta,
                               lambda_=t.crow.lam, beta_inf=t.crow.beta_ic[0], beta_sup=t.crow.beta_ic[1],
                               laplace_u=t.laplace_u, laplace_p=t.laplace_p, version_motor=W.__version__))
        if t.laplace_u > 0 and t.laplace_p < umbral:
            alertas.emitir(s, "DEGRADACION", "media", f"{a.codigo}: {t.texto}", clave, id_activo=a.id, destinatarios="JEFE")
        else:
            alertas.resolver(s, clave)
    s.flush()
    return salida
