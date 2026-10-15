"""Tablero de comando básico [12.E]: ratios de mantenimiento de la UNIDAD 5 (diap. 16–24).

| Código | Nombre | Fórmula |
|---|---|---|
| CMFT | Costo de mantenimiento por facturación | CTMN / FETP |
| CPCT | Costo preventivo sobre costo total | Cprev / (Cprev + Ccorr) |
| HPHP | Horas de paro sobre horas de producción | Horas de paro por mantenimiento / horas de producción realizadas |
| TBMP | Trabajo en mantenimiento preventivo | HHMP / HHDP |
| TBMC | Trabajo en mantenimiento correctivo | HHMC / HHDP |
| OCPM | Ociosidad del personal de mantenimiento | (HHDP − HHTM) / HHDP |

Cada variable sale del sistema cuando se puede (OT, avisos y partes del mes) o de lo que el jefe carga en
`dato_mensual`; lo cargado manda sobre lo calculado (por ejemplo, el costo total contable). Lo que no está
queda "falta dato": nunca se completa con un cero.

Color con el objetivo y los límites de `indicador_objetivo` (D-040): fuera de los límites, rojo; dentro de
los límites pero del lado malo del objetivo, amarillo; si no, verde. Sin objetivo ni límites, gris.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import EstadoEvento, EstadoOT, TipoOT
from circularis_rel.datos.modelos import (
    DatoMensual,
    EventoFalla,
    IndicadorObjetivo,
    OrdenTrabajo,
    ParteTurno,
)
from circularis_rel.servicios import costos as servicio_costos

VARIABLES: dict[str, tuple[str, str]] = {
    "CTMN": ("Costo total de mantenimiento del mes", "ARS"),
    "FETP": ("Facturación total del mes", "ARS"),
    "CPREV": ("Costo del mantenimiento preventivo", "ARS"),
    "CCORR": ("Costo del mantenimiento correctivo", "ARS"),
    "HPM": ("Horas de paro de máquina por mantenimiento (averías)", "h"),
    "HPR": ("Horas de producción realizadas", "h"),
    "HHMP": ("Horas-hombre en mantenimiento preventivo", "HH"),
    "HHMC": ("Horas-hombre en mantenimiento correctivo", "HH"),
    "HHTM": ("Horas-hombre totales trabajadas en mantenimiento", "HH"),
    "HHDP": ("Horas-hombre disponibles del personal de mantenimiento", "HH"),
}
SOLO_CARGA = {"FETP", "HHDP"}  # el sistema no puede saberlas


@dataclass(frozen=True)
class Definicion:
    nombre: str
    formula: str
    variables: tuple[str, ...]
    fuente: str


INDICADORES_BASICOS: dict[str, Definicion] = {
    "CMFT": Definicion("Costo de mantenimiento por facturación", "CTMN / FETP", ("CTMN", "FETP"), "UNIDAD 5, diap. 16"),
    "CPCT": Definicion("Costo preventivo sobre el costo total de mantenimiento", "Cprev / (Cprev + Ccorr)",
                       ("CPREV", "CCORR"), "UNIDAD 5, diap. 20"),
    "HPHP": Definicion("Horas de paro por horas de producción", "Horas de paro por mantenimiento / horas producidas",
                       ("HPM", "HPR"), "UNIDAD 5, diap. 21"),
    "TBMP": Definicion("Trabajo en mantenimiento preventivo", "HHMP / HHDP", ("HHMP", "HHDP"), "UNIDAD 5, diap. 22"),
    "TBMC": Definicion("Trabajo en mantenimiento correctivo", "HHMC / HHDP", ("HHMC", "HHDP"), "UNIDAD 5, diap. 23"),
    "OCPM": Definicion("Ociosidad del personal de mantenimiento", "(HHDP − HHTM) / HHDP", ("HHDP", "HHTM"),
                       "UNIDAD 5, diap. 24"),
}


def _rango_mes(periodo: str, tz: ZoneInfo) -> tuple[datetime, datetime]:
    anio, mes = (int(x) for x in periodo.split("-"))
    ini = date(anio, mes, 1)
    fin = date(anio + (mes == 12), mes % 12 + 1, 1)
    return datetime.combine(ini, time.min, tzinfo=tz), datetime.combine(fin, time.min, tzinfo=tz)


def variables_sistema(s: Session, periodo: str, tz: ZoneInfo) -> tuple[dict[str, float], list[str]]:
    """Variables que salen de los registros del mes (OT cerradas o validadas, avisos validados y partes)."""
    ini, fin = _rango_mes(periodo, tz)
    faltan: set[str] = set()
    v = {"CPREV": 0.0, "CCORR": 0.0, "CTMN": 0.0, "HHMP": 0.0, "HHMC": 0.0, "HHTM": 0.0}
    for ot in s.scalars(select(OrdenTrabajo).where(OrdenTrabajo.estado.in_([EstadoOT.CERRADA, EstadoOT.VALIDADA]),
                                                   OrdenTrabajo.fin_real >= ini, OrdenTrabajo.fin_real < fin)):
        costo, f = servicio_costos.costo_directo_ot(s, ot)
        faltan.update(f)
        hh = ot.hh_propias or 0.0
        v["HHTM"] += hh
        if costo is not None:
            v["CTMN"] += costo
        if ot.tipo in (TipoOT.PREVENTIVA, TipoOT.INSPECCION, TipoOT.PRUEBA_FUNCIONAL):
            v["HHMP"] += hh
            v["CPREV"] += costo or 0.0
        elif ot.tipo == TipoOT.CORRECTIVA:
            v["HHMC"] += hh
            v["CCORR"] += costo or 0.0
    v["HPM"] = float(sum(e.horas_parada or 0.0 for e in s.scalars(select(EventoFalla).where(
        EventoFalla.estado == EstadoEvento.VALIDADO, EventoFalla.fecha_hora_falla >= ini, EventoFalla.fecha_hora_falla < fin))))
    v["HPR"] = sum(s.scalars(select(ParteTurno.horas_operadas).where(ParteTurno.fecha >= ini.date(),
                                                                   ParteTurno.fecha < fin.date())))
    if "tarifa de mano de obra" in faltan:
        for clave in ("CPREV", "CCORR", "CTMN"):
            v.pop(clave)
    return v, sorted(faltan)


def datos_cargados(s: Session, periodo: str) -> dict[str, float]:
    return {d.clave: d.valor for d in s.scalars(select(DatoMensual).where(DatoMensual.periodo == periodo))}


def cargar_dato(s: Session, periodo: str, clave: str, valor: float | None) -> None:
    """Carga (o borra, con None) un dato del mes. La auditoría registra quién y cuándo."""
    if clave not in VARIABLES:
        raise ValueError(f"Variable desconocida: {clave}")
    if valor is not None and valor < 0:
        raise ValueError("El valor no puede ser negativo")
    d = s.scalar(select(DatoMensual).where(DatoMensual.periodo == periodo, DatoMensual.clave == clave))
    if valor is None:
        if d is not None:
            s.delete(d)
    elif d is None:
        s.add(DatoMensual(periodo=periodo, clave=clave, valor=float(valor)))
    else:
        d.valor = float(valor)
    s.flush()


def color(valor: float | None, objetivo: float | None, limite_inf: float | None, limite_sup: float | None,
          mayor_es_mejor: bool) -> str:
    if valor is None or (objetivo is None and limite_inf is None and limite_sup is None):
        return "GRIS"
    if (limite_inf is not None and valor < limite_inf) or (limite_sup is not None and valor > limite_sup):
        return "ROJO"
    if objetivo is not None and ((mayor_es_mejor and valor < objetivo) or (not mayor_es_mejor and valor > objetivo)):
        return "AMARILLO"
    return "VERDE"


@dataclass
class ValorIndicador:
    codigo: str
    nombre: str
    formula: str
    fuente: str
    valor: float | None
    color: str
    objetivo: float | None
    limite_inf: float | None
    limite_sup: float | None
    mayor_es_mejor: bool
    referencia: str | None
    variables: dict[str, tuple[float | None, str]] = field(default_factory=dict)  # clave -> (valor, origen)
    faltan: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)


def _calcular(codigo: str, x: dict[str, float]) -> float | None:
    try:
        if codigo == "CMFT":
            return x["CTMN"] / x["FETP"]
        if codigo == "CPCT":
            return x["CPREV"] / (x["CPREV"] + x["CCORR"])
        if codigo == "HPHP":
            return x["HPM"] / x["HPR"]
        if codigo == "TBMP":
            return x["HHMP"] / x["HHDP"]
        if codigo == "TBMC":
            return x["HHMC"] / x["HHDP"]
        if codigo == "OCPM":
            return (x["HHDP"] - x["HHTM"]) / x["HHDP"]
    except ZeroDivisionError:
        return None
    raise ValueError(codigo)


def tablero(s: Session, periodo: str, tz: ZoneInfo) -> list[ValorIndicador]:
    sistema, faltan_sistema = variables_sistema(s, periodo, tz)
    cargados = datos_cargados(s, periodo)
    objetivos = {o.codigo: o for o in s.scalars(select(IndicadorObjetivo))}
    salida = []
    for codigo, d in INDICADORES_BASICOS.items():
        variables: dict[str, tuple[float | None, str]] = {}
        faltan: list[str] = []
        for clave in d.variables:
            if clave in cargados:
                variables[clave] = (cargados[clave], "cargado")
            elif clave in sistema and clave not in SOLO_CARGA:
                variables[clave] = (sistema[clave], "sistema")
            else:
                variables[clave] = (None, "falta")
                faltan.append(VARIABLES[clave][0])
        valor = None if faltan else _calcular(codigo, {k: v for k, (v, _o) in variables.items()})
        if valor is None and not faltan:
            faltan.append("el denominador es cero en el mes")
        notas = []
        if codigo == "CMFT" and variables["CTMN"][1] == "sistema":
            notas.append("CTMN estimado con lo registrado en las OT (mano de obra, externos y repuestos); "
                         "no incluye gastos generales. Cargá el total contable si lo tenés.")
        if codigo in ("CMFT", "CPCT") and faltan_sistema:
            notas.append("Algunas OT no tienen costo completo: " + ", ".join(faltan_sistema))
        if codigo == "OCPM" and valor is not None and valor < 0:
            notas.append("Negativo: se trabajaron más horas que las disponibles (horas extra; UNIDAD 5, diap. 28)")
        o = objetivos.get(codigo)
        obj, li, ls = (o.objetivo, o.limite_inf, o.limite_sup) if o else (None, None, None)
        mayor = o.mayor_es_mejor if o else True
        salida.append(ValorIndicador(codigo, d.nombre, d.formula, d.fuente, valor, color(valor, obj, li, ls, mayor), obj, li,
                                     ls, mayor, o.referencia_bibliografia if o else None, variables, faltan, notas))
    return salida


def serie(s: Session, codigo: str, periodos: list[str], tz: ZoneInfo) -> list[tuple[str, float | None]]:
    return [(p, next(v.valor for v in tablero(s, p, tz) if v.codigo == codigo)) for p in periodos]


def fijar_objetivo(s: Session, codigo: str, objetivo: float | None, limite_inf: float | None,
                   limite_sup: float | None) -> IndicadorObjetivo:
    o = s.scalar(select(IndicadorObjetivo).where(IndicadorObjetivo.codigo == codigo))
    if o is None:
        raise ValueError(f"Indicador desconocido: {codigo}")
    if limite_inf is not None and limite_sup is not None and limite_inf > limite_sup:
        raise ValueError("El límite inferior no puede ser mayor que el superior")
    o.objetivo, o.limite_inf, o.limite_sup = objetivo, limite_inf, limite_sup
    s.flush()
    return o
