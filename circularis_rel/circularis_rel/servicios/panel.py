"""Datos del panel de planta y de máquina (Plan §7; fase 1c).

- Estado de cada máquina: el peor color de sus componentes críticos (último `estado_componente`) y
  rojo si tiene un aviso abierto.
- Ranking de riesgo: P(falla en Δ) × Cf de cada componente (Plan §7). Sin costos cargados se ordena
  por P y se avisa qué falta.
- Pareto de fallas validadas por frecuencia, horas de parada o costo, agrupado por máquina,
  componente y modo [12.D].
- Tendencia mensual, línea de tiempo de la máquina y sugerencias de análisis de causa raíz.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import (
    Alcance,
    Confianza,
    ConjuntoDatos,
    EstadoEvento,
    EstadoPDCA,
    EtapaProceso,
    Interpretacion,
    OrigenAnalisis,
    TipoOT,
)
from circularis_rel.datos.modelos import (
    Activo,
    AnalisisProblema,
    Catalogo,
    EstadoComponente,
    EventoFalla,
    MotivoParada,
    OrdenTrabajo,
    ParteTurno,
    PosicionComponente,
    ResultadoWeibull,
    TarjetaTPM,
    TipoComponente,
)
from circularis_rel.motor import kpis, semaforo
from circularis_rel.servicios import costos as servicio_costos
from circularis_rel.servicios import parametros as P

ABIERTOS = (EstadoEvento.AVISADO, EstadoEvento.EN_REPARACION, EstadoEvento.DEVUELTO)
ORDEN_ETAPA = {e: i for i, e in enumerate(EtapaProceso)}


@dataclass
class ComponenteEstado:
    id_posicion: int
    codigo: str
    tipo: str
    id_tipo: int
    critica: bool
    color: str
    confianza: str
    edad: float | None
    delta: float | None
    p: float | None
    p_inf: float | None
    p_sup: float | None
    intervalo: float | None
    fuente_intervalo: str
    vida_rem_mediana: float | None
    vida_rem_90: float | None
    motivos: list[str]
    fecha: date | None
    id_resultado: int | None


@dataclass
class MaquinaEstado:
    id: int
    codigo: str
    nombre: str
    etapa: str
    clase: str | None
    color: str
    confianza: str
    motivos: list[str]
    avisos_abiertos: int
    componentes: list[ComponenteEstado] = field(default_factory=list)


def ultimo_estado(s: Session, id_posicion: int) -> EstadoComponente | None:
    return s.scalar(select(EstadoComponente).where(EstadoComponente.id_posicion == id_posicion)
                    .order_by(EstadoComponente.fecha.desc()).limit(1))


def componentes(s: Session, id_activo: int) -> list[ComponenteEstado]:
    salida = []
    for pos in s.scalars(select(PosicionComponente).where(PosicionComponente.id_activo == id_activo,
                                                          PosicionComponente.activa.is_(True))
                         .order_by(PosicionComponente.codigo)):
        tipo = s.get(TipoComponente, pos.id_tipo_componente)
        e = ultimo_estado(s, pos.id)
        if e is None:
            salida.append(ComponenteEstado(pos.id, pos.codigo, tipo.nombre, tipo.id, pos.critica, "GRIS", "GRIS", None, None,
                                           None, None, None, None, "NINGUNO", None, None,
                                           ["Sin cálculo todavía (corre cada noche o al validar)"], None, None))
            continue
        salida.append(ComponenteEstado(pos.id, pos.codigo, tipo.nombre, tipo.id, pos.critica, e.semaforo.value,
                                       e.confianza.value, e.edad, e.delta, e.p_falla_delta, e.p_falla_delta_inf,
                                       e.p_falla_delta_sup, e.intervalo_vigente, e.fuente_intervalo.value,
                                       e.vida_rem_mediana, e.vida_rem_90, list(e.motivos or []), e.fecha,
                                       e.id_resultado_weibull))
    return salida


def avisos_abiertos(s: Session, id_activo: int) -> int:
    return s.scalar(select(func.count()).select_from(EventoFalla).where(EventoFalla.id_activo == id_activo,
                                                                       EventoFalla.estado.in_(ABIERTOS)))


def estado_maquina(s: Session, a: Activo) -> MaquinaEstado:
    comps = componentes(s, a.id)
    criticos = [semaforo.Color(c.color, c.motivos, c.confianza) for c in comps if c.critica]
    col = semaforo.color_maquina(criticos)
    avisos = avisos_abiertos(s, a.id)
    motivos = list(col.motivos)
    color = col.color
    if avisos:
        color = "ROJO"
        motivos.insert(0, f"{avisos} aviso(s) de falla abierto(s)")
    return MaquinaEstado(a.id, a.codigo, a.nombre, a.etapa_proceso.value, a.criticidad_clase.value if a.criticidad_clase else None,
                         color, col.confianza, motivos, avisos, comps)


def estado_maquinas(s: Session, ids: list[int] | None = None) -> list[MaquinaEstado]:
    consulta = select(Activo).where(Activo.activo.is_(True))
    if ids is not None:
        consulta = consulta.where(Activo.id.in_(ids))
    activos = sorted(s.scalars(consulta), key=lambda a: (ORDEN_ETAPA.get(a.etapa_proceso, 99), a.orden_proceso or 0, a.codigo))
    return [estado_maquina(s, a) for a in activos]


# ---------------------------------------------------------------------------
# Ranking de riesgo
# ---------------------------------------------------------------------------


@dataclass
class FilaRiesgo:
    maquina: str
    componente: str
    id_posicion: int
    p: float
    cf: float | None
    riesgo: float | None
    color: str
    confianza: str
    faltan: list[str]


def ranking_riesgo(s: Session, hoy: date, limite: int = 10) -> list[FilaRiesgo]:
    filas = []
    for pos, codigo in s.execute(select(PosicionComponente, Activo.codigo).join(Activo, Activo.id == PosicionComponente.id_activo)
                                 .where(PosicionComponente.activa.is_(True), Activo.activo.is_(True))):
        e = ultimo_estado(s, pos.id)
        if e is None or e.p_falla_delta is None:
            continue
        modo = s.get(ResultadoWeibull, e.id_resultado_weibull).id_modo if e.id_resultado_weibull else None
        c = servicio_costos.costos_decision(s, pos.id_tipo_componente, modo, pos.id_activo, hoy)
        riesgo = e.p_falla_delta * c.cf if c.cf is not None else None
        filas.append(FilaRiesgo(codigo, pos.codigo, pos.id, e.p_falla_delta, c.cf, riesgo, e.semaforo.value,
                                e.confianza.value, c.faltan))
    filas.sort(key=lambda f: (f.riesgo is not None, f.riesgo or 0.0, f.p), reverse=True)
    return filas[:limite]


# ---------------------------------------------------------------------------
# Pareto, tendencia y línea de tiempo
# ---------------------------------------------------------------------------


def _rango(desde: date, hasta: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    return datetime.combine(desde, time.min, tzinfo=tz), datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=tz)


def eventos_validados(s: Session, desde: date, hasta: date, tz: ZoneInfo, id_activo: int | None = None) -> list[EventoFalla]:
    ini, fin = _rango(desde, hasta, tz)
    consulta = select(EventoFalla).where(EventoFalla.estado == EstadoEvento.VALIDADO, EventoFalla.fecha_hora_falla >= ini,
                                         EventoFalla.fecha_hora_falla < fin)
    if id_activo is not None:
        consulta = consulta.where(EventoFalla.id_activo == id_activo)
    return list(s.scalars(consulta))


def etiqueta_par(s: Session, id_activo: int, id_tipo: int, id_modo: int) -> str:
    """"AGR-001 · CUCHILLAS · Pérdida de filo": máquina, posiciones de ese tipo en la máquina y modo."""
    posiciones = s.scalars(select(PosicionComponente.codigo).where(PosicionComponente.id_activo == id_activo,
                                                                   PosicionComponente.id_tipo_componente == id_tipo)).all()
    componente = "/".join(sorted(posiciones)) or s.get(TipoComponente, id_tipo).nombre
    return f"{s.get(Activo, id_activo).codigo} · {componente} · {s.get(Catalogo, id_modo).descripcion}"


@dataclass
class FilaPareto:
    etiqueta: str
    id_activo: int
    id_tipo: int
    id_modo: int
    n: int = 0
    horas: float = 0.0
    costo: float = 0.0
    sin_costo: int = 0
    valor: float = 0.0
    fraccion: float = 0.0
    acumulado: float = 0.0
    dentro_corte: bool = False


CRITERIOS_PARETO = {"frecuencia": "Cantidad de fallas", "horas": "Horas de parada", "costo": "Costo (ARS)"}


def pareto(s: Session, desde: date, hasta: date, tz: ZoneInfo, criterio: str = "frecuencia",
           id_activo: int | None = None) -> list[FilaPareto]:
    """Pareto por máquina · componente · modo. Con criterio "costo", las fallas sin costo calculable
    (faltan tarifas) no suman y se cuentan en `sin_costo`."""
    if criterio not in CRITERIOS_PARETO:
        raise ValueError(f"Criterio desconocido: {criterio}")
    corte = P.obtener(s, "pareto.corte")
    grupos: dict[tuple[int, int, int], FilaPareto] = {}
    for ev in eventos_validados(s, desde, hasta, tz, id_activo):
        pos = s.get(PosicionComponente, ev.id_posicion)
        clave = (ev.id_activo, pos.id_tipo_componente, ev.id_modo)
        if clave not in grupos:
            grupos[clave] = FilaPareto(etiqueta_par(s, *clave), *clave)
        g = grupos[clave]
        g.n += 1
        g.horas += ev.horas_parada or 0.0
        if criterio == "costo":
            c = servicio_costos.costo_historico(s, ev)
            if c.ars is None:
                g.sin_costo += 1
            else:
                g.costo += c.ars
    filas = list(grupos.values())
    for f in filas:
        f.valor = {"frecuencia": float(f.n), "horas": f.horas, "costo": f.costo}[criterio]
    filas.sort(key=lambda f: (-f.valor, f.etiqueta))
    total = sum(f.valor for f in filas)
    acumulado = 0.0
    for f in filas:
        f.fraccion = f.valor / total if total else 0.0
        anterior = acumulado
        acumulado += f.fraccion
        f.acumulado = acumulado
        f.dentro_corte = total > 0 and anterior < corte  # las barras que llegan hasta el corte (incluida la que lo cruza)
    return filas


def meses(desde: date, hasta: date) -> list[str]:
    salida, d = [], date(desde.year, desde.month, 1)
    while d <= hasta:
        salida.append(f"{d:%Y-%m}")
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return salida


def tendencia_mensual(s: Session, desde: date, hasta: date, tz: ZoneInfo, id_activo: int | None = None,
                      con_costo: bool = True) -> list[dict]:
    """Por mes: fallas validadas, horas de parada, disponibilidad operacional, MTBF y costo de las fallas
    (Plan §7). El costo queda None si en el mes hay alguna falla sin costo calculable."""
    motivos = {m.id: m for m in s.scalars(select(MotivoParada))}
    datos = {m: {"periodo": m, "fallas": 0, "horas_parada": 0.0, "horas_operadas": 0.0, "requeridas": 0.0,
                 "paradas": 0.0, "ao": None, "mtbf": None, "costo": 0.0 if con_costo else None}
             for m in meses(desde, hasta)}
    for ev in eventos_validados(s, desde, hasta, tz, id_activo):
        d = datos.get(f"{ev.fecha_hora_falla.astimezone(tz):%Y-%m}")
        if d is None:
            continue
        d["fallas"] += 1
        d["horas_parada"] += ev.horas_parada or 0.0
        if con_costo and d["costo"] is not None:
            c = servicio_costos.costo_historico(s, ev)
            d["costo"] = None if c.ars is None else d["costo"] + c.ars
    consulta = select(ParteTurno).where(ParteTurno.fecha.between(desde, hasta))
    if id_activo is not None:
        consulta = consulta.where(ParteTurno.id_activo == id_activo)
    for p in s.scalars(consulta):
        d = datos.get(f"{p.fecha:%Y-%m}")
        if d is None:
            continue
        m = motivos.get(p.id_motivo) if p.id_motivo else None
        no_requeridas = p.horas_no_operadas if (m is not None and not m.cuenta_como_requerida) else 0.0
        d["horas_operadas"] += p.horas_operadas or 0.0
        d["requeridas"] += p.horas_turno - no_requeridas
        d["paradas"] += p.horas_no_operadas - no_requeridas
    for d in datos.values():
        d["mtbf"] = kpis.mtbf(d["horas_operadas"], d["fallas"])
        d["ao"] = kpis.disponibilidad_operacional(d["requeridas"], d["paradas"])
    return list(datos.values())


def linea_tiempo(s: Session, id_activo: int, tz: ZoneInfo, limite: int = 200) -> list[dict]:
    """Historia de la máquina, de lo más nuevo a lo más viejo: fallas, cambios preventivos y tarjetas."""
    salida = []
    for ev in s.scalars(select(EventoFalla).where(EventoFalla.id_activo == id_activo, EventoFalla.estado != EstadoEvento.ANULADO)
                        .order_by(EventoFalla.fecha_hora_falla.desc()).limit(limite)):
        pos = s.get(PosicionComponente, ev.id_posicion) if ev.id_posicion else None
        modo = s.get(Catalogo, ev.id_modo).descripcion if ev.id_modo else "—"
        salida.append({"fecha": ev.fecha_hora_falla.astimezone(tz), "tipo": "Falla", "componente": pos.codigo if pos else "—",
                       "detalle": modo, "horas_parada": ev.horas_parada, "estado": ev.estado.value.capitalize()})
    for ot in s.scalars(select(OrdenTrabajo).where(OrdenTrabajo.id_activo == id_activo,
                                                   OrdenTrabajo.tipo.in_([TipoOT.PREVENTIVA, TipoOT.INSPECCION,
                                                                          TipoOT.MODIFICATIVO]))
                        .order_by(OrdenTrabajo.creado_en.desc()).limit(limite)):
        pos = s.get(PosicionComponente, ot.id_posicion) if ot.id_posicion else None
        cuando = ot.fin_real or ot.inicio_real or ot.creado_en
        salida.append({"fecha": cuando.astimezone(tz), "tipo": ot.tipo.value.capitalize(),
                       "componente": pos.codigo if pos else "—", "detalle": ot.numero, "horas_parada": None,
                       "estado": ot.estado.value.capitalize()})
    for t in s.scalars(select(TarjetaTPM).where(TarjetaTPM.id_activo == id_activo)
                       .order_by(TarjetaTPM.creado_en.desc()).limit(limite)):
        salida.append({"fecha": t.creado_en.astimezone(tz), "tipo": f"Tarjeta {t.color.value.lower()}", "componente": "—",
                       "detalle": t.anomalia or t.observaciones or "", "horas_parada": None,
                       "estado": t.estado.value.capitalize()})
    salida.sort(key=lambda d: d["fecha"], reverse=True)
    return salida[:limite]


# ---------------------------------------------------------------------------
# Sugerencias de análisis de causa raíz [12.D]
# ---------------------------------------------------------------------------


@dataclass
class Sugerencia:
    id_activo: int
    id_tipo: int
    id_modo: int
    etiqueta: str
    origen: OrigenAnalisis
    motivos: list[str]


def _analisis_abierto(s: Session, id_activo: int, id_tipo: int, id_modo: int) -> bool:
    return s.scalar(select(AnalisisProblema.id).where(
        AnalisisProblema.id_activo == id_activo, AnalisisProblema.id_tipo_componente == id_tipo,
        AnalisisProblema.id_modo == id_modo, AnalisisProblema.estado_pdca != EstadoPDCA.CERRADO).limit(1)) is not None


def sugerencias_rca(s: Session, hoy: date, tz: ZoneInfo) -> list[Sugerencia]:
    """Tres disparadores (PLAN_TECNICO §8.3, 12.D):
    1. los primeros del Pareto de horas de parada del último año;
    2. β ≈ 1 (fallas al azar) con confianza media o alta: el reemplazo preventivo no sirve, hay que buscar la causa;
    3. N o más fallas validadas del mismo par en los últimos M días.
    No se sugiere un par que ya tiene un análisis abierto."""
    sugeridas: dict[tuple[int, int, int], Sugerencia] = {}

    def agregar(clave, etiqueta, origen, motivo):
        if clave not in sugeridas:
            sugeridas[clave] = Sugerencia(*clave, etiqueta, origen, [])
        sugeridas[clave].motivos.append(motivo)

    filas = pareto(s, hoy - timedelta(days=365), hoy, tz, "horas")
    for f in [f for f in filas if f.valor > 0][: P.obtener(s, "rca.top_pareto")]:
        agregar((f.id_activo, f.id_tipo, f.id_modo), f.etiqueta, OrigenAnalisis.SUGERIDO_PARETO,
                f"Está entre los primeros del Pareto de horas de parada del último año ({f.horas:.0f} h, {f.fraccion:.0%})")

    for r in s.scalars(select(ResultadoWeibull).where(
            ResultadoWeibull.vigente.is_(True), ResultadoWeibull.alcance == Alcance.MAQUINA,
            ResultadoWeibull.conjunto_datos == ConjuntoDatos.NUEVOS,
            ResultadoWeibull.interpretacion == Interpretacion.ALEATORIA,
            ResultadoWeibull.confianza.in_([Confianza.MEDIA, Confianza.ALTA]))):
        etiqueta = etiqueta_par(s, r.id_activo, r.id_tipo_componente, r.id_modo)
        agregar((r.id_activo, r.id_tipo_componente, r.id_modo), etiqueta, OrigenAnalisis.SUGERIDO_BETA,
                f"Falla al azar (β = {r.beta:.2f}, confianza {r.confianza.value.lower()}): cambiar antes no ayuda; "
                "conviene buscar la causa (lubricación, montaje, operación)")

    n_min, dias = P.obtener(s, "rca.repeticiones_n"), P.obtener(s, "rca.repeticiones_dias")
    for f in pareto(s, hoy - timedelta(days=dias), hoy, tz, "frecuencia"):
        if f.n >= n_min:
            agregar((f.id_activo, f.id_tipo, f.id_modo), f.etiqueta, OrigenAnalisis.SUGERIDO_REPETICION,
                    f"Se repitió {f.n} veces en los últimos {dias} días")

    return [sg for clave, sg in sugeridas.items() if not _analisis_abierto(s, *clave)]


def calidad_datos_linea(s: Session, desde: date, hasta: date, tz: ZoneInfo) -> list[dict]:
    """Indicador de calidad de datos por máquina (Plan §11)."""
    from circularis_rel.servicios import kpis_planta
    from circularis_rel.servicios.turnos import laborables

    salida = []
    for a in s.scalars(select(Activo).where(Activo.activo.is_(True)).order_by(Activo.codigo)):
        c = kpis_planta.calidad_de_datos(s, a.id, desde, hasta, len(laborables(s, a.id, desde, hasta)), tz)
        salida.append({"maquina": a.codigo, **c})
    return salida


# ---------------------------------------------------------------------------
# Datos para la ficha y el análisis Weibull
# ---------------------------------------------------------------------------

TEXTO_INTERPRETACION = {
    "MORTALIDAD_INFANTIL": "Fallas de juventud (β < 1): revisar montaje, calidad del repuesto y arranque. "
                           "Cambiar antes no ayuda.",
    "ALEATORIA": "Fallas al azar (β ≈ 1): la edad no influye; cambiar antes no ayuda. Buscar la causa "
                 "(lubricación, sobrecarga, operación).",
    "DESGASTE": "Desgaste (β > 1): el riesgo crece con la edad. Conviene el reemplazo preventivo.",
    "DESGASTE_RAPIDO": "Desgaste rápido (β alto): la vida es muy predecible; el preventivo funciona muy bien.",
}


def resultados_vigentes(s: Session, id_activo: int, id_tipo: int | None = None) -> list[ResultadoWeibull]:
    consulta = select(ResultadoWeibull).where(ResultadoWeibull.id_activo == id_activo, ResultadoWeibull.vigente.is_(True),
                                              ResultadoWeibull.conjunto_datos == ConjuntoDatos.NUEVOS)
    if id_tipo is not None:
        consulta = consulta.where(ResultadoWeibull.id_tipo_componente == id_tipo)
    return list(s.scalars(consulta))


def alternativa(s: Session, r: ResultadoWeibull) -> ResultadoWeibull | None:
    """El otro método calculado con los mismos datos (mismo hash), si lo hay."""
    return s.scalar(select(ResultadoWeibull).where(
        ResultadoWeibull.id_tipo_componente == r.id_tipo_componente, ResultadoWeibull.id_modo == r.id_modo,
        ResultadoWeibull.id_activo == r.id_activo, ResultadoWeibull.hash_datos == r.hash_datos,
        ResultadoWeibull.vigente.is_(False), ResultadoWeibull.id != r.id).order_by(ResultadoWeibull.id.desc()).limit(1))


def rangos_par(s: Session, r: ResultadoWeibull, tz: ZoneInfo) -> list[tuple[float, float, float]] | None:
    """Puntos del gráfico de probabilidad: los guardados con el resultado o, si el método no los usa (MLE),
    se calculan con la misma población (sin guardar nada)."""
    guardados = (r.comparacion or {}).get("rangos")
    if guardados:
        return [tuple(x) for x in guardados]
    from circularis_rel.motor import weibull as W
    from circularis_rel.motor.preparacion import armar_poblacion
    from circularis_rel.servicios.recalculo import vidas_de_poblacion

    with s.no_autoflush:
        vidas = vidas_de_poblacion(s, r.id_tipo_componente, r.id_activo, tz, r.conjunto_datos)
    for obj in list(s.dirty):  # la edad recalculada no se guarda desde una lectura
        s.expire(obj)
    obs, _ = armar_poblacion(vidas, r.id_modo)
    datos = [o for o in obs if not o.solo_pronostico and o.estado in ("F", "S")]
    if not any(o.estado == "F" for o in datos):
        return None
    return W.rangos_johnson(datos)


def ultima_intervencion(s: Session, id_activo: int) -> OrdenTrabajo | None:
    return s.scalar(select(OrdenTrabajo).where(OrdenTrabajo.id_activo == id_activo, OrdenTrabajo.fin_real.is_not(None))
                    .order_by(OrdenTrabajo.fin_real.desc()).limit(1))


@dataclass
class AnalisisCosto:
    costos: servicio_costos.CostosDecision
    recomendacion: object  # politicas.Recomendacion
    curva: list[tuple[float, float, float]] | None = None
    t_optimo: float | None = None
    costo_optimo: float | None = None
    costo_falla_por_hora: float | None = None
    intervalo_redondeado: float | None = None
    ahorro: float | None = None


def analisis_costo(s: Session, r: ResultadoWeibull, hoy: date) -> AnalisisCosto:
    """Recomendación del Plan §8 para el par y, si hay costos y desgaste, la curva C(T) completa
    (aunque la regla que mande sea la de confiabilidad objetivo, la curva se muestra como información)."""
    from circularis_rel.motor import politicas

    tipo = s.get(TipoComponente, r.id_tipo_componente)
    activo = s.get(Activo, r.id_activo)
    c = servicio_costos.costos_decision(s, tipo.id, r.id_modo, activo.id, hoy)
    paso = P.obtener(s, "politicas.paso_redondeo_h")
    rec = politicas.recomendar(r.beta, r.eta, cp=c.cp, cf=c.cf, critico=activo.criticidad_clase == "A",
                               seguridad=tipo.funcion_seguridad, intervalo_pf=tipo.intervalo_pf,
                               r_objetivo=P.obtener(s, "politicas.r_objetivo"), cf_cp_minimo=P.obtener(s, "politicas.cf_cp_minimo"),
                               paso_redondeo=paso, interpretacion=r.interpretacion.value if r.interpretacion else None,
                               gamma=r.gamma or 0.0)
    salida = AnalisisCosto(c, rec)
    if c.completo and r.beta and r.eta and r.beta > 1:
        gamma = r.gamma or 0.0
        salida.curva = politicas.curva_costo(c.cp, c.cf, r.beta, r.eta, gamma)
        salida.costo_falla_por_hora = politicas.costo_hasta_falla(c.cf, r.beta, r.eta, gamma)
        opt = politicas.intervalo_optimo(c.cp, c.cf, r.beta, r.eta, gamma)
        if opt is not None:
            salida.t_optimo, salida.costo_optimo = opt
            salida.intervalo_redondeado = politicas.redondear_intervalo(opt[0], paso)
            salida.ahorro = 1 - politicas.costo_por_hora(salida.intervalo_redondeado, c.cp, c.cf, r.beta, r.eta, gamma) \
                / salida.costo_falla_por_hora
    return salida


def cuadrantes(s: Session, desde: date, hasta: date, tz: ZoneInfo, id_activo: int | None = None) -> dict:
    """Fallas validadas por forma de aparición (repentina / progresiva) y capacidad (total / parcial) [12.C].
    Las progresivas se pueden anticipar con inspección o predictivo; las repentinas y totales son las que
    más duelen. Devuelve {(aparicion, capacidad): n} y cuántas quedaron sin clasificar."""
    conteo: dict[tuple[str, str], int] = {(a, c): 0 for a in ("REPENTINA", "PROGRESIVA") for c in ("TOTAL", "PARCIAL")}
    sin = 0
    for ev in eventos_validados(s, desde, hasta, tz, id_activo):
        if ev.aparicion is None or ev.capacidad is None:
            sin += 1
        else:
            conteo[(ev.aparicion.value, ev.capacidad.value)] += 1
    return {"conteo": conteo, "sin_clasificar": sin}
