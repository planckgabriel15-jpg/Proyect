"""AMFE con ocurrencia automática (Plan §8; fase 4).

- NPR = G × O × D, como en el TP N.º 1.
- O calculada: con el Weibull vigente del componente y modo, F(1 año) = probabilidad de que una pieza nueva falle
  dentro del uso de un año de la máquina (horas por día de los últimos 30 días × 365). Se convierte a la escala de 1
  a 10 con los cortes de `amfe.escala_ocurrencia` (propuesta editable: la escala del TP es cualitativa; D-064).
  El 1 nunca se asigna solo: en la escala del TP significa "causa eliminada por diseño".
- La O del TP (ilustrativa) no se pisa: la calculada se muestra al lado y el jefe decide si la adopta.
- Prioridad de acción (AP) AIAG-VDA: se carga a mano (la tabla del manual no está en el proyecto; B-018).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import Alcance, ConjuntoDatos, OrigenDato
from circularis_rel.datos.modelos import (
    Activo,
    AmfeItem,
    Catalogo,
    PosicionComponente,
    ResultadoWeibull,
    TipoComponente,
)
from circularis_rel.motor import kpis
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios import recalculo


def ocurrencia_por_f(f: float, escala: list[list[float]]) -> int:
    """escala = [[F mínima, O], ...] ordenada de mayor a menor; devuelve la primera O cuyo mínimo se alcanza (≥ 2)."""
    for minimo, o in sorted(escala, key=lambda x: -x[0]):
        if f >= minimo:
            return int(o)
    return 2


def f_un_anio(s: Session, item: AmfeItem, hoy: date) -> tuple[float | None, str]:
    """(F(1 año), explicación) del par del ítem, o (None, motivo)."""
    consulta = select(ResultadoWeibull).where(ResultadoWeibull.id_tipo_componente == item.id_tipo_componente,
                                              ResultadoWeibull.id_modo == item.id_modo, ResultadoWeibull.vigente.is_(True),
                                              ResultadoWeibull.conjunto_datos == ConjuntoDatos.NUEVOS,
                                              ResultadoWeibull.beta.is_not(None))
    resultados = list(s.scalars(consulta))
    if item.id_activo is not None:
        propios = [r for r in resultados if r.id_activo == item.id_activo]
        resultados = propios or [r for r in resultados if r.alcance == Alcance.FLOTA]
    if not resultados:
        return None, "Sin Weibull para este componente y modo"
    r = resultados[0]
    id_activo = item.id_activo or r.id_activo
    if id_activo is None:
        pos = s.scalar(select(PosicionComponente).where(PosicionComponente.id_tipo_componente == item.id_tipo_componente).limit(1))
        id_activo = pos.id_activo if pos else None
    tipo = s.get(TipoComponente, item.id_tipo_componente)
    ritmo = recalculo.ritmo_diario(s, id_activo, tipo.variable_edad.value == "TONELADAS", hoy) if id_activo else None
    if not ritmo:
        return None, "Sin ritmo de uso de la máquina"
    uso = ritmo * 365
    f = kpis.infiabilidad(uso, r.beta, r.eta, r.gamma or 0.0)
    return f, f"F({uso:.0f} h de un año) = {f:.0%} con β = {r.beta:.2f}, η = {r.eta:.0f} (confianza {r.confianza.value.lower()})"


def actualizar_ocurrencias(s: Session, hoy: date) -> int:
    escala = P.obtener(s, "amfe.escala_ocurrencia")
    if not escala:
        return 0
    n = 0
    for item in s.scalars(select(AmfeItem)):
        f, _texto = f_un_anio(s, item, hoy)
        nueva = ocurrencia_por_f(f, escala) if f is not None else None
        if item.o_calculada != nueva:
            item.o_calculada = nueva
            n += 1
    s.flush()
    return n


@dataclass
class FilaAmfe:
    id: int
    maquina: str
    componente: str
    modo: str
    g: int
    o: int
    d: int
    o_calculada: int | None
    explicacion: str
    ap: str | None
    acciones: str | None
    origen: str

    @property
    def npr(self) -> int:
        return self.g * self.o * self.d

    @property
    def npr_calculado(self) -> int | None:
        return self.g * self.o_calculada * self.d if self.o_calculada else None


def filas(s: Session, hoy: date) -> list[FilaAmfe]:
    salida = []
    for item in s.scalars(select(AmfeItem)):
        _f, texto = f_un_anio(s, item, hoy)
        salida.append(FilaAmfe(item.id, s.get(Activo, item.id_activo).codigo if item.id_activo else "(todas)",
                               s.get(TipoComponente, item.id_tipo_componente).nombre, s.get(Catalogo, item.id_modo).descripcion,
                               item.g, item.o, item.d, item.o_calculada, texto, item.ap, item.acciones, item.origen.value))
    return sorted(salida, key=lambda f: -(f.npr_calculado or f.npr))


def editar(s: Session, id_item: int, *, g: int, o: int, d: int, ap: str | None, acciones: str | None,
           responsable: str | None, fecha: date | None) -> AmfeItem:
    for nombre, v in (("G", g), ("O", o), ("D", d)):
        if not 1 <= v <= 10:
            raise ValueError(f"{nombre} va de 1 a 10")
    if ap not in (None, "", "H", "M", "L"):
        raise ValueError("La prioridad de acción es H, M o L")
    item = s.get(AmfeItem, id_item)
    item.g, item.o, item.d = g, o, d
    item.ap = ap or None
    item.acciones = (acciones or "").strip() or None
    item.responsable = (responsable or "").strip() or None
    item.fecha = fecha
    if item.origen in (OrigenDato.TP1_ILUSTRATIVO, OrigenDato.PROPUESTA):
        item.origen = OrigenDato.JEFE  # revisado por el jefe
    s.flush()
    return item
