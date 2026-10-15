"""Puesta en marcha guiada [12.A]: las 14 etapas de la UNIDAD 6 en tres fases.

Cada etapa tiene un estado manual (pendiente / en curso / hecha) y, cuando se puede, un
criterio verificable por el sistema. El criterio no cambia el estado solo: lo informa y el
jefe decide (así nunca se marca "hecho" algo que el sistema no puede saber).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import (
    Confianza,
    EstadoEtapa,
    EstadoEvento,
    TipoCatalogo,
)
from circularis_rel.datos.modelos import (
    Activo,
    Catalogo,
    CatalogoAplica,
    DatoMensual,
    EtapaImplementacion,
    EventoFalla,
    MotivoParada,
    ParteTurno,
    PlanPreventivo,
    PosicionComponente,
    Repuesto,
    RepuestoActivo,
    ResultadoWeibull,
)
from circularis_rel.datos.semillas import DESVENTAJAS_INFORMATIZAR

PATRON_CODIGO = r"^[A-Z]{3}-[0-9]{3}$"


@dataclass(frozen=True)
class Verificacion:
    cumple: bool | None  # None = el sistema no lo puede verificar
    detalle: str


def _activos(s: Session) -> list[Activo]:
    return list(s.scalars(select(Activo).where(Activo.activo.is_(True))))


def _hay_activos(s):
    n = len(_activos(s))
    return Verificacion(n > 0, f"{n} máquinas cargadas")


def _catastro_completo(s):
    from circularis_rel.servicios.catastro import CAMPOS_CATASTRO  # import tardío: evita ciclo

    activos = _activos(s)
    if not activos:
        return Verificacion(False, "No hay máquinas")
    incompletas = [a.codigo for a in activos if any(getattr(a, c) in (None, "") for c in CAMPOS_CATASTRO)]
    return Verificacion(not incompletas, "Completo" if not incompletas else
                        f"Faltan datos de catastro en {len(incompletas)} máquinas: {', '.join(incompletas[:5])}")


def _repuestos_cargados(s):
    activos = _activos(s)
    sin = [a.codigo for a in activos if s.scalar(select(func.count()).select_from(RepuestoActivo)
                                                 .where(RepuestoActivo.id_activo == a.id)) == 0]
    sin_uso = s.scalar(select(func.count()).select_from(Repuesto).where(Repuesto.uso.is_(None)))
    ok = bool(activos) and not sin and sin_uso == 0
    partes = []
    if sin:
        partes.append(f"{len(sin)} máquinas sin repuestos")
    if sin_uso:
        partes.append(f"{sin_uso} repuestos sin marcar común/específico")
    return Verificacion(ok, "Completo" if ok else "; ".join(partes) or "No hay máquinas")


def _catalogos_cargados(s):
    tipos_sin_modo = s.scalar(select(func.count()).select_from(PosicionComponente).where(
        ~PosicionComponente.id_tipo_componente.in_(
            select(CatalogoAplica.id_tipo_componente).join(Catalogo, Catalogo.id == CatalogoAplica.id_catalogo)
            .where(Catalogo.tipo == TipoCatalogo.MODO))))
    sintomas = s.scalar(select(func.count()).select_from(Catalogo).where(Catalogo.tipo == TipoCatalogo.SINTOMA))
    ok = tipos_sin_modo == 0 and sintomas > 0 and len(_activos(s)) > 0
    return Verificacion(ok, "Cada componente tiene sus modos de falla" if ok else
                        f"{tipos_sin_modo} posiciones cuyo tipo de componente no tiene modos de falla")


def _criticidad_completa(s):
    activos = _activos(s)
    sin = [a.codigo for a in activos if a.criticidad_clase is None]
    return Verificacion(bool(activos) and not sin, "Todas las máquinas tienen clase" if activos and not sin
                        else f"Sin criticidad: {', '.join(sin[:8]) or 'no hay máquinas'}")


def _codigos_activos(s):
    import re

    activos = _activos(s)
    malos = [a.codigo for a in activos if not re.match(PATRON_CODIGO, a.codigo)]
    return Verificacion(bool(activos) and not malos, "Todos con formato AAA-000" if activos and not malos
                        else f"Códigos con otro formato: {', '.join(malos[:8]) or 'no hay máquinas'}")


def _plan_preventivo(s):
    n = s.scalar(select(func.count()).select_from(PlanPreventivo).where(PlanPreventivo.vigente.is_(True)))
    return Verificacion(n > 0, f"{n} planes vigentes")


def _hh_disponibles(s):
    n = s.scalar(select(func.count()).select_from(DatoMensual).where(DatoMensual.clave == "HHDP"))
    return Verificacion(n > 0, f"{n} meses con horas-hombre disponibles cargadas")


def _partes_cargados(s):
    desde = (ahora() - timedelta(days=7)).date()
    activos = _activos(s)
    con = {a for (a,) in s.execute(select(ParteTurno.id_activo).where(ParteTurno.fecha >= desde).distinct())}
    sin = [a.codigo for a in activos if a.id not in con]
    return Verificacion(bool(activos) and not sin, "Todas las máquinas con partes en los últimos 7 días"
                        if activos and not sin else f"Sin partes en 7 días: {', '.join(sin[:8]) or 'no hay máquinas'}")


def _motivos_y_sintomas(s):
    m = s.scalar(select(func.count()).select_from(MotivoParada).where(MotivoParada.activo.is_(True)))
    si = s.scalar(select(func.count()).select_from(Catalogo).where(Catalogo.tipo == TipoCatalogo.SINTOMA))
    return Verificacion(m > 0 and si > 0, f"{m} motivos de parada y {si} síntomas")


def _eventos_validados(s):
    n = s.scalar(select(func.count()).select_from(EventoFalla).where(EventoFalla.estado == EstadoEvento.VALIDADO))
    return Verificacion(n > 0, f"{n} fallas validadas")


def _confianza_media(s):
    n = s.scalar(select(func.count()).select_from(ResultadoWeibull).where(
        ResultadoWeibull.vigente.is_(True), ResultadoWeibull.confianza.in_([Confianza.MEDIA, Confianza.ALTA])))
    if n == 0:
        return Verificacion(False, "Todavía no hay datos suficientes: seguí cargando partes y avisos")
    return Verificacion(True, f"{n} componentes con confianza media o alta")


def _fase1_estable(s):
    """Criterio de la fase 2 del Plan (§10): dos semanas seguidas con más del 90 % de partes completos en las
    máquinas del piloto, y fallas que ya se validan."""
    from circularis_rel.servicios import piloto  # import tardío: evita ciclo

    hoy = ahora().date()
    e = piloto.estado(s, hoy, ZoneInfo("UTC"), semanas_a_mostrar=0)
    validadas = _eventos_validados(s)
    if not e.maquinas:
        return Verificacion(False, "No hay máquinas")
    flojas = [m.codigo for m in e.maquinas if not m.cumple]
    texto = (f"Partes: {e.semanas_requeridas} semanas seguidas con más del {e.minimo:.0%} en "
             + ("todas las máquinas del piloto" if not flojas else f"falta en {', '.join(flojas[:6])}"))
    return Verificacion(not flojas and bool(validadas.cumple), f"{texto}. {validadas.detalle}.")


def _provisto(_s):
    return Verificacion(True, "Lo provee el sistema")


CRITERIOS: dict[str, Callable[[Session], Verificacion]] = {
    "hay_activos": _hay_activos,
    "provisto": _provisto,
    "catastro_completo": _catastro_completo,
    "repuestos_cargados": _repuestos_cargados,
    "catalogos_cargados": _catalogos_cargados,
    "criticidad_completa": _criticidad_completa,
    "codigos_activos": _codigos_activos,
    "plan_preventivo": _plan_preventivo,
    "hh_disponibles": _hh_disponibles,
    "partes_cargados": _partes_cargados,
    "motivos_y_sintomas": _motivos_y_sintomas,
    "eventos_validados": _eventos_validados,
    "confianza_media": _confianza_media,
    "fase1_estable": _fase1_estable,
}


@dataclass
class VistaEtapa:
    numero: int
    fase: int
    titulo: str
    que_es: str
    por_que: str
    pantalla: str | None
    estado: EstadoEtapa
    verificacion: Verificacion
    notas: str | None


def listar(s: Session) -> list[VistaEtapa]:
    salida = []
    for e in s.scalars(select(EtapaImplementacion).order_by(EtapaImplementacion.numero)):
        verif = CRITERIOS[e.criterio](s) if e.criterio in CRITERIOS else Verificacion(None, "Verificación manual")
        salida.append(VistaEtapa(e.numero, e.fase, e.titulo, e.que_es, e.por_que, e.pantalla, e.estado, verif, e.notas))
    return salida


def progreso(etapas: list[VistaEtapa]) -> float:
    if not etapas:
        return 0.0
    puntos = {EstadoEtapa.PENDIENTE: 0.0, EstadoEtapa.EN_CURSO: 0.5, EstadoEtapa.HECHA: 1.0}
    return sum(puntos[e.estado] for e in etapas) / len(etapas)


def marcar(s: Session, numero: int, estado: EstadoEtapa, id_usuario: int | None, notas: str | None = None) -> None:
    e = s.scalar(select(EtapaImplementacion).where(EtapaImplementacion.numero == numero))
    if e is None:
        raise ValueError(f"No existe la etapa {numero}")
    e.estado = estado
    e.fecha_hecha = ahora() if estado == EstadoEtapa.HECHA else None
    e.id_usuario_marco = id_usuario
    if notas is not None:
        e.notas = notas


def desventajas() -> list[str]:
    return list(DESVENTAJAS_INFORMATIZAR)
