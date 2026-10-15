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
VARIABLES_COMPLETO: dict[str, tuple[str, str]] = {
    "CMOC": ("Costo de mano de obra contratada (servicios externos)", "ARS"),
    "CMOP": ("Costo de mano de obra propia", "ARS"),
    "CPROD": ("Costo de producción del mes", "ARS"),
    "VIB": ("Valor inmovilizado bruto (máquinas y equipos)", "ARS"),
    "HHML": ("Horas-hombre de mantenimiento en línea (autónomo)", "HH"),
    "HHEI": ("Horas-hombre de entrenamiento interno", "HH"),
    "EMMM": ("Efectivo medio del personal de mantenimiento en los últimos meses", "personas"),
    "NOTR": ("Transferencias del personal en el período", "personas"),
    "NODV": ("Renuncias voluntarias en el período", "personas"),
    "HHEF": ("Horas-hombre efectivas (del plantel)", "HH"),
    "HHAF": ("Horas-hombre apartadas (vacaciones, enfermedad, accidentes)", "HH"),
    "CFJ": ("Costos fijos de mantenimiento (preventivo: mano de obra y materiales)", "ARS"),
    "CV": ("Costos variables de mantenimiento (correctivo: mano de obra directa y materiales)", "ARS"),
    "CFN": ("Costos financieros (repuestos inmovilizados, amortización de equipos de reserva)", "ARS"),
    "CFA": ("Costo por falla (producción perdida)", "ARS"),
}
VARIABLES |= VARIABLES_COMPLETO
SOLO_CARGA = {"FETP", "HHDP", "CPROD", "VIB", "HHEI", "EMMM", "NOTR", "NODV", "HHEF", "HHAF", "CFN"}


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


INDICADORES_COMPLETOS: dict[str, Definicion] = {
    "CMOE": Definicion("Mano de obra externa", "CMOC / (CMOC + CMOP)", ("CMOC", "CMOP"), "UNIDAD 5, diap. 17"),
    "CMPP": Definicion("Costo de mantenimiento por producción", "CTMN / costo de producción", ("CTMN", "CPROD"),
                       "UNIDAD 5, diap. 18"),
    "CMPV": Definicion("Costo de mantenimiento por valor inmovilizado", "CTMN / valor inmovilizado bruto", ("CTMN", "VIB"),
                       "UNIDAD 5, diap. 19"),
    "TBML": Definicion("Trabajo de mantenimiento en línea", "HHML / HHDP", ("HHML", "HHDP"), "UNIDAD 4 (TPM)"),
    "PETI": Definicion("Entrenamiento interno", "HHEI / HHDP", ("HHEI", "HHDP"), "UNIDAD 5, diap. 25"),
    "CSMP": Definicion("Clima social: movimiento de personal", "EMMM / (EMMM + NOTR + NODV)", ("EMMM", "NOTR", "NODV"),
                       "UNIDAD 5, diap. 26"),
    "EFMD": Definicion("Efectivo real", "(HHEF − HHAF) / HHEF", ("HHEF", "HHAF"), "UNIDAD 5, diap. 27–28 (B-009)"),
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
    # Tablero completo: mano de obra propia y contratada, trabajo en línea y CIT (UNIDAD 5, diap. 33–43).
    from circularis_rel.servicios import parametros as P

    v["CMOC"] = v["CMOP"] = v["HHML"] = 0.0
    for ot in s.scalars(select(OrdenTrabajo).where(OrdenTrabajo.estado.in_([EstadoOT.CERRADA, EstadoOT.VALIDADA]),
                                                   OrdenTrabajo.fin_real >= ini, OrdenTrabajo.fin_real < fin)):
        tarifa = P.obtener(s, "costos.tarifa_mo_ars_h", ot.fin_real.date())
        v["CMOC"] += ot.costo_externo_ars or 0.0
        if tarifa is not None:
            v["CMOP"] += (ot.hh_propias or 0.0) * tarifa
        if ot.tipo == TipoOT.AUTONOMO:
            v["HHML"] += ot.hh_propias or 0.0
    cfa = 0.0
    for ev in s.scalars(select(EventoFalla).where(EventoFalla.estado == EstadoEvento.VALIDADO,
                                                  EventoFalla.fecha_hora_falla >= ini, EventoFalla.fecha_hora_falla < fin)):
        c = servicio_costos.costo_historico(s, ev)
        if c.desglose is None:  # falta el margen de la línea: CFA queda "falta dato" (no afecta a los otros ratios)
            cfa = None
            break
        cfa += c.desglose.co
    if cfa is not None:
        v["CFA"] = cfa
    if "tarifa de mano de obra" in faltan:
        for clave in ("CPREV", "CCORR", "CTMN", "CMOP"):
            v.pop(clave, None)
    else:
        v["CFJ"], v["CV"] = v["CPREV"], v["CCORR"]
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
        if codigo == "CMOE":
            return x["CMOC"] / (x["CMOC"] + x["CMOP"])
        if codigo == "CMPP":
            return x["CTMN"] / x["CPROD"]
        if codigo == "CMPV":
            return x["CTMN"] / x["VIB"]
        if codigo == "TBML":
            return x["HHML"] / x["HHDP"]
        if codigo == "PETI":
            return x["HHEI"] / x["HHDP"]
        if codigo == "CSMP":
            return x["EMMM"] / (x["EMMM"] + x["NOTR"] + x["NODV"])
        if codigo == "EFMD":
            return (x["HHEF"] - x["HHAF"]) / x["HHEF"]
    except ZeroDivisionError:
        return None
    raise ValueError(codigo)


def definiciones(completo: bool = False) -> dict[str, Definicion]:
    return INDICADORES_BASICOS | (INDICADORES_COMPLETOS if completo else {})


def tablero(s: Session, periodo: str, tz: ZoneInfo, completo: bool = False) -> list[ValorIndicador]:
    sistema, faltan_sistema = variables_sistema(s, periodo, tz)
    cargados = datos_cargados(s, periodo)
    objetivos = {o.codigo: o for o in s.scalars(select(IndicadorObjetivo))}
    salida = []
    for codigo, d in definiciones(completo).items():
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
        if codigo == "EFMD" and valor is not None:
            notas.append(f"Ausentismo = HHAF / HHEF = {1 - valor:.1%} (B-009)")
        if codigo == "OCPM" and valor is not None and valor < 0:
            notas.append("Negativo: se trabajaron más horas que las disponibles (horas extra; UNIDAD 5, diap. 28)")
        o = objetivos.get(codigo)
        obj, li, ls = (o.objetivo, o.limite_inf, o.limite_sup) if o else (None, None, None)
        mayor = o.mayor_es_mejor if o else True
        salida.append(ValorIndicador(codigo, d.nombre, d.formula, d.fuente, valor, color(valor, obj, li, ls, mayor), obj, li,
                                     ls, mayor, o.referencia_bibliografia if o else None, variables, faltan, notas))
    return salida


def serie(s: Session, codigo: str, periodos: list[str], tz: ZoneInfo) -> list[tuple[str, float | None]]:
    if codigo == "DISP":
        return [(p, disponibilidad_mes(s, p, tz)) for p in periodos]
    completo = codigo in INDICADORES_COMPLETOS
    return [(p, next(v.valor for v in tablero(s, p, tz, completo) if v.codigo == codigo)) for p in periodos]


def disponibilidad_mes(s: Session, periodo: str, tz: ZoneInfo) -> float | None:
    """Disponibilidad operacional de la línea en el mes (Plan §6), para el gráfico con objetivo y límites."""
    from datetime import timedelta

    from circularis_rel.servicios import kpis_planta

    ini, fin = _rango_mes(periodo, tz)
    return kpis_planta.kpis_linea(s, ini.date(), fin.date() - timedelta(days=1), tz).ao


@dataclass
class CIT:
    cfj: tuple[float | None, str]
    cv: tuple[float | None, str]
    cfn: tuple[float | None, str]
    cfa: tuple[float | None, str]
    faltan: list[str]

    @property
    def total(self) -> float | None:
        valores = [self.cfj[0], self.cv[0], self.cfn[0], self.cfa[0]]
        return None if any(x is None for x in valores) else sum(valores)


def cit(s: Session, periodo: str, tz: ZoneInfo) -> CIT:
    """CIT = CFJ + CV + CFN + CFA (UNIDAD 5, diap. 42). Fijos ≈ preventivo y variables ≈ correctivo (diap. 35 y 37),
    calculados desde las OT; financieros, a mano; por falla = producción perdida de los avisos validados."""
    sistema, _f = variables_sistema(s, periodo, tz)
    cargados = datos_cargados(s, periodo)
    partes = {}
    faltan = []
    for clave in ("CFJ", "CV", "CFN", "CFA"):
        if clave in cargados:
            partes[clave] = (cargados[clave], "cargado")
        elif clave in sistema and clave not in SOLO_CARGA:
            partes[clave] = (sistema[clave], "sistema")
        else:
            partes[clave] = (None, "falta")
            faltan.append(VARIABLES[clave][0])
    return CIT(partes["CFJ"], partes["CV"], partes["CFN"], partes["CFA"], faltan)


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
