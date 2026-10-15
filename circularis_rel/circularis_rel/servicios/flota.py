"""Flota (Plan §5; PLAN_TECNICO §7.6): el mismo componente en varias máquinas.

- Grupo por tipo: todas las posiciones de un tipo de componente que está en dos o más máquinas.
- Grupo por equivalencia: posiciones que el jefe declara equivalentes (`equivalencia_componente`), aunque
  tengan códigos de tipo distintos (por ejemplo, el mismo rulemán en dos máquinas).

Antes de agrupar se hace la prueba de razón de verosimilitud: LR = 2(Σ ℓ por máquina − ℓ agrupado) ~ χ² con
2(k − 1) grados de libertad. Si p > `motor.flota_p_valor` no hay evidencia de que las máquinas sean distintas
y el ajuste agrupado puede usarse en el semáforo de las posiciones que no tienen ajuste propio (D-049).
Las máquinas con menos de 2 fallas no entran en la prueba (no se puede ajustar su MLE), pero sí en el ajuste.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import Alcance, ConjuntoDatos, TipoFin
from circularis_rel.datos.modelos import (
    Activo,
    Catalogo,
    EquivalenciaComponente,
    PosicionComponente,
    ResultadoWeibull,
    TipoComponente,
    VidaComponente,
)
from circularis_rel.motor import weibull as W
from circularis_rel.motor.preparacion import armar_poblacion
from circularis_rel.motor.tipos import Observacion
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios import recalculo


@dataclass
class Grupo:
    clave: str  # "tipo:<id>" o "equiv:<nombre>"
    nombre: str
    posiciones: list[int]
    id_tipo: int  # tipo de referencia (el de la primera posición)


def grupos(s: Session) -> list[Grupo]:
    salida = []
    por_tipo: dict[int, list[PosicionComponente]] = {}
    for pos in s.scalars(select(PosicionComponente).join(Activo, Activo.id == PosicionComponente.id_activo)
                         .where(PosicionComponente.activa.is_(True), Activo.activo.is_(True)).order_by(PosicionComponente.id)):
        por_tipo.setdefault(pos.id_tipo_componente, []).append(pos)
    for id_tipo, posiciones in por_tipo.items():
        if len({p.id_activo for p in posiciones}) >= 2:
            salida.append(Grupo(f"tipo:{id_tipo}", f"{s.get(TipoComponente, id_tipo).nombre} (mismo tipo)",
                                [p.id for p in posiciones], id_tipo))
    equivalencias: dict[str, list[int]] = {}
    for e in s.scalars(select(EquivalenciaComponente).order_by(EquivalenciaComponente.id)):
        equivalencias.setdefault(e.grupo, []).append(e.id_posicion)
    for nombre, ids in sorted(equivalencias.items()):
        if len(ids) >= 2:
            salida.append(Grupo(f"equiv:{nombre}", f"{nombre} (equivalencia)", ids,
                                s.get(PosicionComponente, ids[0]).id_tipo_componente))
    return salida


def modos(s: Session, g: Grupo) -> list[Catalogo]:
    """Modos con al menos una falla en las posiciones del grupo."""
    ids = s.scalars(select(VidaComponente.id_modo_falla).where(VidaComponente.id_posicion.in_(g.posiciones),
                                                               VidaComponente.tipo_fin == TipoFin.FALLA,
                                                               VidaComponente.id_modo_falla.is_not(None)).distinct()).all()
    return list(s.scalars(select(Catalogo).where(Catalogo.id.in_(ids)).order_by(Catalogo.descripcion)))


def _observaciones(s: Session, g: Grupo, id_modo: int, tz: ZoneInfo) -> dict[str, list[Observacion]]:
    """Observaciones por máquina (código), sin las marcadas solo para pronóstico."""
    salida: dict[str, list[Observacion]] = {}
    por_activo: dict[int, list[int]] = {}
    for i in g.posiciones:
        por_activo.setdefault(s.get(PosicionComponente, i).id_activo, []).append(i)
    for id_activo, ids in por_activo.items():
        vidas = recalculo.vidas_de_poblacion(s, g.id_tipo, None, tz, ids_posiciones=ids)
        obs, _ = armar_poblacion(vidas, id_modo)
        salida[s.get(Activo, id_activo).codigo] = [o for o in obs if not o.solo_pronostico]
    return salida


@dataclass
class PruebaFlota:
    lr: float | None
    p: float | None
    gl: int | None
    agrupable: bool
    por_maquina: dict[str, tuple[int, int]] = field(default_factory=dict)  # código -> (fallas, suspensiones)
    nota: str = ""


def probar(s: Session, g: Grupo, id_modo: int, tz: ZoneInfo) -> PruebaFlota:
    obs = _observaciones(s, g, id_modo, tz)
    por_maquina = {c: (sum(o.estado == "F" for o in v), sum(o.estado == "S" for o in v)) for c, v in obs.items()}
    con_datos = {c: v for c, v in obs.items() if sum(o.estado in ("F", "I") for o in v) >= 2}
    if len(con_datos) < 2:
        return PruebaFlota(None, None, None, False, por_maquina,
                           "Hacen falta al menos dos máquinas con 2 o más fallas para la prueba")
    lr, p, gl = W.prueba_flota(con_datos)
    umbral = P.obtener(s, "motor.flota_p_valor")
    agrupable = p > umbral
    afuera = sorted(set(obs) - set(con_datos))
    nota = (f"p = {p:.3f} {'>' if agrupable else '≤'} {umbral:g}: "
            + ("no hay evidencia de que las máquinas se comporten distinto; se pueden agrupar." if agrupable
               else "las máquinas se comportan distinto; conviene analizarlas por separado."))
    if afuera:
        nota += f" Sin fallas suficientes para la prueba: {', '.join(afuera)}."
    return PruebaFlota(lr, p, gl, agrupable, por_maquina, nota)


def vigente(s: Session, g: Grupo, id_modo: int) -> ResultadoWeibull | None:
    for r in s.scalars(select(ResultadoWeibull).where(ResultadoWeibull.alcance == Alcance.FLOTA, ResultadoWeibull.id_modo == id_modo,
                                                      ResultadoWeibull.vigente.is_(True))):
        if (r.comparacion or {}).get("grupo") == g.clave:
            return r
    return None


def ajustar(s: Session, g: Grupo, id_modo: int, tz: ZoneInfo) -> ResultadoWeibull:
    """Ajuste agrupado; guarda la prueba con el resultado para que el semáforo sepa si puede usarlo."""
    prueba = probar(s, g, id_modo, tz)
    obs = [o for v in _observaciones(s, g, id_modo, tz).values() for o in v]
    tipo = s.get(TipoComponente, g.id_tipo)
    res = W.ajustar(obs, recalculo.configuracion(s), beta_ref=tipo.beta_ref)
    anterior = vigente(s, g, id_modo)
    if anterior is not None:
        if anterior.hash_datos == res.hash_datos and anterior.version_motor == W.__version__:
            return anterior
        anterior.vigente = False
    fila = recalculo._fila(res.vigente, g.id_tipo, id_modo, None, ConjuntoDatos.NUEVOS, res.hash_datos, True)
    fila.alcance = Alcance.FLOTA
    activos = sorted({s.get(PosicionComponente, i).id_activo for i in g.posiciones})
    fila.ids_activos_flota = activos
    fila.comparacion = (fila.comparacion or {}) | {
        "grupo": g.clave, "nombre_grupo": g.nombre, "posiciones": g.posiciones, "agrupable": prueba.agrupable,
        "prueba": {"lr": prueba.lr, "p": prueba.p, "gl": prueba.gl, "nota": prueba.nota, "por_maquina": prueba.por_maquina}}
    s.add(fila)
    s.flush()
    return fila


def declarar_equivalencia(s: Session, nombre: str, ids_posiciones: list[int]) -> None:
    """Reemplaza las posiciones del grupo de equivalencia `nombre` (una posición está en un solo grupo)."""
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("Poné un nombre al grupo")
    if len(set(ids_posiciones)) < 2:
        raise ValueError("Un grupo de equivalencia necesita al menos dos posiciones")
    for e in s.scalars(select(EquivalenciaComponente).where(EquivalenciaComponente.grupo == nombre)):
        s.delete(e)
    s.flush()
    for i in sorted(set(ids_posiciones)):
        otra = s.scalar(select(EquivalenciaComponente).where(EquivalenciaComponente.id_posicion == i))
        if otra is not None:
            raise ValueError(f"La posición {s.get(PosicionComponente, i).codigo} ya está en el grupo '{otra.grupo}'")
        s.add(EquivalenciaComponente(grupo=nombre, id_posicion=i))
    s.flush()


def recalcular_flotas(s: Session, tz: ZoneInfo) -> int:
    """Rehace los ajustes de flota que el jefe ya pidió (los que tienen un resultado vigente), con los datos nuevos."""
    n = 0
    for g in grupos(s):
        for r in list(s.scalars(select(ResultadoWeibull).where(ResultadoWeibull.alcance == Alcance.FLOTA,
                                                               ResultadoWeibull.vigente.is_(True)))):
            if (r.comparacion or {}).get("grupo") == g.clave:
                ajustar(s, g, r.id_modo, tz)
                n += 1
    return n
