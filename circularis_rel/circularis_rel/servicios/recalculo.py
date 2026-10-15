"""Recálculo: lee la base, llama al motor y guarda resultados con trazabilidad (Plan §5, §7).

- Por evento: al validar se encola el par (tipo de componente, modo, máquina); el proceso de tareas lo
  toma en segundos (`procesar_cola`).
- Cada noche: todos los pares y el estado (semáforo) de todos los componentes.
- Cada resultado guarda método, versión del motor, n de fallas/suspensiones/intervalos, nivel y método
  del IC, conjunto de datos y un hash de los datos. Se guardan los dos métodos cuando aplican.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from scipy import optimize
from sqlalchemy import func, select, true
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import (
    Alcance,
    Confianza,
    ConjuntoDatos,
    EstadoEvento,
    FuenteIntervalo,
    Interpretacion,
    MetodoIC,
    MetodoWeibull,
    ReglaPlan,
    Semaforo,
    TipoFin,
    TipoReparacion,
    VariableEdad,
)
from circularis_rel.datos.modelos import (
    Activo,
    ActivoTurno,
    EstadoComponente,
    EventoFalla,
    ParteTurno,
    PlanPreventivo,
    PosicionComponente,
    RecalculoPendiente,
    ResultadoWeibull,
    TipoComponente,
    VidaComponente,
    VidaHistorica,
)
from circularis_rel.motor import kpis, politicas, semaforo
from circularis_rel.motor import weibull as W
from circularis_rel.motor.preparacion import VidaDatos, armar_poblacion
from circularis_rel.motor.tipos import AjusteWeibull, Configuracion
from circularis_rel.servicios import costos as servicio_costos
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios import vidas as servicio_vidas


def configuracion(s: Session) -> Configuracion:
    g = lambda c: P.obtener(s, c)  # noqa: E731
    return Configuracion(
        nivel_ic=g("motor.nivel_ic"), min_fallas_rrx=g("motor.min_fallas_rrx"), min_fallas_mle=g("motor.min_fallas_mle"),
        max_frac_suspensiones_rrx=g("motor.max_frac_suspensiones_rrx"), n_max_rba=g("motor.n_max_rba"),
        beta_aleatoria_min=g("motor.beta_aleatoria_min"), beta_aleatoria_max=g("motor.beta_aleatoria_max"),
        beta_aleatoria_por_ic=g("motor.beta_aleatoria_por_ic"), beta_desgaste_rapido=g("motor.beta_desgaste_rapido"),
        confianza_baja_desde=g("motor.confianza_baja_desde"), confianza_media_desde=g("motor.confianza_media_desde"),
        confianza_alta_desde=g("motor.confianza_alta_desde"), bootstrap_replicas=g("motor.bootstrap_replicas"),
    )


def _dias_laborables(s: Session, id_activo: int, desde: date, hasta: date) -> int:
    dias = set()
    for (texto,) in s.execute(select(ActivoTurno.dias).where(ActivoTurno.id_activo == id_activo)):
        dias |= {int(d) for d in texto.split(",") if d.strip()}
    dias = dias or {1, 2, 3, 4, 5}
    n, d = 0, desde
    while d < hasta:
        n += d.isoweekday() in dias
        d += timedelta(days=1)
    return n


def vidas_de_poblacion(s: Session, id_tipo: int, id_activo: int | None, tz: ZoneInfo,
                       conjunto: ConjuntoDatos = ConjuntoDatos.NUEVOS) -> list[VidaDatos]:
    tipo = s.get(TipoComponente, id_tipo)
    toneladas = tipo.variable_edad == VariableEdad.TONELADAS
    posiciones = select(PosicionComponente.id).where(PosicionComponente.id_tipo_componente == id_tipo)
    if id_activo is not None:
        posiciones = posiciones.where(PosicionComponente.id_activo == id_activo)
    salida: list[VidaDatos] = []
    for v in s.scalars(select(VidaComponente).where(VidaComponente.id_posicion.in_(posiciones))):
        servicio_vidas.actualizar_edad(s, v, tz)
        salida.append(VidaDatos(
            edad=v.edad_toneladas if toneladas else v.edad_horas, tipo_fin=v.tipo_fin.value, id_modo=v.id_modo_falla,
            edad_conocida=v.edad_conocida, validado=v.validado, nivel_hora=v.nivel_hora.value,
            reparacion_minima=v.tipo_reparacion == TipoReparacion.REPARACION_MINIMA, etiqueta=f"vida {v.id}"))
    if conjunto == ConjuntoDatos.NUEVOS_MAS_HIST_AB and not toneladas:
        for h in s.scalars(select(VidaHistorica).where(VidaHistorica.id_posicion.in_(posiciones),
                                                       VidaHistorica.clase_triage.in_(["A", "B"]))):
            edad, edad_inf = h.edad_horas, None
            if h.clase_triage == "B" and h.edad_inf_h is not None:
                edad_inf, edad = h.edad_inf_h, h.edad_sup_h
            elif edad is None and h.fecha_instalacion:
                # Horas estimadas (nivel E): horas promedio por día × días laborables (Plan §4)
                activo = s.get(Activo, h.id_activo)
                if activo.horas_promedio_dia is None:
                    continue
                if h.fecha_fin is not None:
                    edad = activo.horas_promedio_dia * _dias_laborables(s, h.id_activo, h.fecha_instalacion, h.fecha_fin)
                elif h.fecha_fin_inf is not None and h.fecha_fin_sup is not None:
                    edad_inf = activo.horas_promedio_dia * _dias_laborables(s, h.id_activo, h.fecha_instalacion, h.fecha_fin_inf)
                    edad = activo.horas_promedio_dia * _dias_laborables(s, h.id_activo, h.fecha_instalacion, h.fecha_fin_sup)
            if edad is None:
                continue
            salida.append(VidaDatos(edad=edad, tipo_fin=h.tipo_fin.value, id_modo=h.id_modo_falla, edad_inf=edad_inf,
                                    origen=f"HIST_{h.clase_triage.value}", etiqueta=f"histórico {h.id}"))
    return salida


def _forzado(s: Session, id_tipo: int, id_modo: int, id_activo: int | None) -> ResultadoWeibull | None:
    return s.scalar(select(ResultadoWeibull).where(
        ResultadoWeibull.id_tipo_componente == id_tipo, ResultadoWeibull.id_modo == id_modo,
        ResultadoWeibull.id_activo == id_activo, ResultadoWeibull.forzado.is_(True))
        .order_by(ResultadoWeibull.fecha_calculo.desc()).limit(1))


def _fila(a: AjusteWeibull, id_tipo, id_modo, id_activo, conjunto, hash_datos, vigente, forzado=None) -> ResultadoWeibull:
    metodo = MetodoWeibull(a.metodo) if a.metodo != "NINGUNO" else None
    return ResultadoWeibull(
        id_tipo_componente=id_tipo, id_modo=id_modo, alcance=Alcance.MAQUINA if id_activo else Alcance.FLOTA,
        id_activo=id_activo, conjunto_datos=conjunto, n_fallas=a.n_fallas, n_suspensiones=a.n_suspensiones,
        n_intervalo=a.n_intervalo, metodo=metodo, forzado=forzado is not None,
        justificacion=forzado.justificacion if forzado else None, beta=a.beta, eta=a.eta, gamma=a.gamma,
        beta_inf=a.beta_ic[0] if a.beta_ic else None, beta_sup=a.beta_ic[1] if a.beta_ic else None,
        eta_inf=a.eta_ic[0] if a.eta_ic else None,
        eta_sup=a.eta_ic[1] if a.eta_ic and math.isfinite(a.eta_ic[1]) else None,
        metodo_ic=MetodoIC(a.metodo_ic),
        nivel_ic=a.nivel_ic, r2=a.r2, r2_critico=a.r2_critico, ad=a.ad,
        comparacion=(a.comparacion or {}) | {"advertencias": a.advertencias, "metodo_ic_detalle": a.metodo_ic,
                                              "beta_mle_sin_corregir": a.beta_mle_sin_corregir,
                                              "rangos": a.rangos},
        confianza=Confianza(a.confianza), interpretacion=Interpretacion(a.interpretacion) if a.interpretacion else None,
        version_motor=a.version_motor or W.__version__, hash_datos=hash_datos, vigente=vigente)


def recalcular_par(s: Session, id_tipo: int, id_modo: int, id_activo: int | None, tz: ZoneInfo,
                   conjunto: ConjuntoDatos = ConjuntoDatos.NUEVOS, forzar: str | None = None,
                   justificacion: str | None = None) -> ResultadoWeibull:
    """Ajusta un par y guarda el resultado (si los datos o el motor cambiaron). Devuelve el vigente."""
    cfg = configuracion(s)
    tipo = s.get(TipoComponente, id_tipo)
    vidas = vidas_de_poblacion(s, id_tipo, id_activo, tz, conjunto)
    obs, _resumen = armar_poblacion(vidas, id_modo)
    forzado = None
    if forzar:
        if not justificacion or not justificacion.strip():
            raise ValueError("Forzar un método exige una justificación")
        forzado = ResultadoWeibull(justificacion=justificacion.strip())
    else:
        previo = _forzado(s, id_tipo, id_modo, id_activo)
        if previo is not None and previo.metodo is not None:
            forzado, forzar = previo, previo.metodo.value
    try:
        res = W.ajustar(obs, cfg, beta_ref=tipo.beta_ref, metodo_forzado=forzar)
    except ValueError as e:
        res = W.ajustar([], cfg)
        res.vigente.advertencias.append(f"No se pudo forzar el método: {e}")
    anterior = s.scalar(select(ResultadoWeibull).where(
        ResultadoWeibull.id_tipo_componente == id_tipo, ResultadoWeibull.id_modo == id_modo,
        ResultadoWeibull.id_activo == id_activo, ResultadoWeibull.conjunto_datos == conjunto,
        ResultadoWeibull.vigente.is_(True)))
    if (anterior is not None and anterior.hash_datos == res.hash_datos and anterior.version_motor == W.__version__
            and not forzar and not anterior.forzado):
        return anterior
    if anterior is not None:
        anterior.vigente = False
    vigente = _fila(res.vigente, id_tipo, id_modo, id_activo, conjunto, res.hash_datos, True, forzado)
    s.add(vigente)
    if res.alternativa is not None:
        s.add(_fila(res.alternativa, id_tipo, id_modo, id_activo, conjunto, res.hash_datos, False))
    s.flush()
    return vigente


# ---------------------------------------------------------------------------
# Estado de cada componente (semáforo)
# ---------------------------------------------------------------------------


def ritmo_diario(s: Session, id_activo: int, toneladas: bool, hoy: date) -> float | None:
    """Horas (o toneladas) por día calendario de los últimos 30 días; si no hay partes, el promedio del listado."""
    desde = hoy - timedelta(days=30)
    partes = list(s.scalars(select(ParteTurno).where(ParteTurno.id_activo == id_activo, ParteTurno.fecha > desde,
                                                     ParteTurno.fecha <= hoy)))
    a = s.get(Activo, id_activo)
    if toneladas:
        cant = [p.cantidad_procesada for p in partes if p.cantidad_procesada is not None]
        return (sum(cant) * (a.factor_toneladas or 0) / 30) if cant and a.factor_toneladas else None
    if partes:
        return sum(p.horas_operadas for p in partes) / 30
    return (a.horas_promedio_dia * 5 / 7) if a.horas_promedio_dia else None


def horizonte(s: Session, id_activo: int, toneladas: bool, hoy: date) -> float | None:
    """Δ = uso hasta la próxima parada programada (o el horizonte por defecto) al ritmo real de la máquina."""
    ritmo = ritmo_diario(s, id_activo, toneladas, hoy)
    if ritmo is None:
        return None
    proxima = P.obtener(s, "semaforo.proxima_parada")
    dias = P.obtener(s, "semaforo.horizonte_dias_defecto")
    if proxima:
        try:
            fecha = date.fromisoformat(proxima)
            if fecha > hoy:
                dias = (fecha - hoy).days
        except ValueError:
            pass
    return ritmo * dias


def _vida_remanente_combinada(a: float, q: float, modos: list[tuple[float, float, float]]) -> float | None:
    f = lambda x: (1 - kpis.prob_condicional_combinada(a, x, modos)) - q  # noqa: E731
    alto = 1.0
    for _ in range(80):
        if f(alto) < 0:
            return optimize.brentq(f, 0, alto, xtol=1e-6)
        alto *= 2
    return None


@dataclass
class Intervalo:
    valor: float | None
    fuente: FuenteIntervalo
    regla: str | None = None
    texto: str | None = None


def intervalo_vigente(s: Session, pos: PosicionComponente, ajustes: list[ResultadoWeibull], hoy: date) -> Intervalo:
    """Plan preventivo aprobado > cálculo (si hay Weibull y costos) > fabricante."""
    plan = s.scalar(select(PlanPreventivo).where(PlanPreventivo.id_posicion == pos.id, PlanPreventivo.vigente.is_(True),
                                                 PlanPreventivo.regla != ReglaPlan.NINGUNO).limit(1))
    if plan is not None and plan.intervalo:
        return Intervalo(plan.intervalo, FuenteIntervalo.CALCULADO, plan.regla.value, "Plan preventivo aprobado")
    tipo = s.get(TipoComponente, pos.id_tipo_componente)
    activo = s.get(Activo, pos.id_activo)
    desgaste = [r for r in ajustes if r.beta and r.beta > 1 and r.interpretacion in (Interpretacion.DESGASTE,
                                                                                    Interpretacion.DESGASTE_RAPIDO)]
    if desgaste:
        r = min(desgaste, key=lambda x: x.eta)
        c = servicio_costos.costos_decision(s, tipo.id, r.id_modo, activo.id, hoy)
        rec = politicas.recomendar(r.beta, r.eta, cp=c.cp, cf=c.cf, critico=activo.criticidad_clase == "A",
                                   seguridad=tipo.funcion_seguridad, intervalo_pf=tipo.intervalo_pf,
                                   r_objetivo=P.obtener(s, "politicas.r_objetivo"),
                                   cf_cp_minimo=P.obtener(s, "politicas.cf_cp_minimo"),
                                   paso_redondeo=P.obtener(s, "politicas.paso_redondeo_h"),
                                   interpretacion=r.interpretacion.value if r.interpretacion else None)
        if rec.intervalo:
            return Intervalo(rec.intervalo, FuenteIntervalo.CALCULADO, rec.regla, rec.texto)
    if tipo.intervalo_fabricante:
        return Intervalo(tipo.intervalo_fabricante, FuenteIntervalo.FABRICANTE, "FABRICANTE", "Recomendación del fabricante")
    return Intervalo(None, FuenteIntervalo.NINGUNO)


def umbrales(s: Session) -> semaforo.Umbrales:
    return semaforo.Umbrales(P.obtener(s, "semaforo.p_amarillo"), P.obtener(s, "semaforo.p_rojo"),
                             P.obtener(s, "semaforo.p_amarillo_clase_a"), P.obtener(s, "semaforo.p_rojo_clase_a"),
                             P.obtener(s, "semaforo.fraccion_intervalo_amarillo"))


def actualizar_estado(s: Session, pos: PosicionComponente, tz: ZoneInfo, hoy: date | None = None) -> EstadoComponente:
    hoy = hoy or ahora().astimezone(tz).date()
    tipo = s.get(TipoComponente, pos.id_tipo_componente)
    activo = s.get(Activo, pos.id_activo)
    toneladas = tipo.variable_edad == VariableEdad.TONELADAS
    vida = servicio_vidas.vida_abierta(s, pos.id)
    edad = None
    if vida is not None:
        servicio_vidas.actualizar_edad(s, vida, tz)
        edad = vida.edad_toneladas if toneladas else vida.edad_horas
        if not vida.edad_conocida:
            edad = None  # instalado antes del sistema: la edad real es mayor y desconocida
    ajustes = [r for r in s.scalars(select(ResultadoWeibull).where(
        ResultadoWeibull.id_tipo_componente == tipo.id, ResultadoWeibull.id_activo == activo.id,
        ResultadoWeibull.vigente.is_(True), ResultadoWeibull.conjunto_datos == ConjuntoDatos.NUEVOS))
        if r.beta is not None and r.eta is not None]
    delta = horizonte(s, activo.id, toneladas, hoy)
    p = p_inf = p_sup = rem50 = rem90 = None
    confianza = "GRIS"
    dominante = None
    if ajustes and edad is not None and delta:
        modos = [(r.beta, r.eta, r.gamma or 0.0) for r in ajustes]
        p = kpis.prob_condicional_combinada(edad, delta, modos)
        dominante = max(ajustes, key=lambda r: kpis.prob_condicional(edad, delta, r.beta, r.eta))
        confianza = dominante.confianza.value
        esquinas = []
        bi, bs = dominante.beta_inf or dominante.beta, dominante.beta_sup or dominante.beta
        ei, es = dominante.eta_inf or dominante.eta, dominante.eta_sup or dominante.eta
        for b in (bi, bs):
            for e in (ei, es):
                otros = [(r.beta, r.eta, r.gamma or 0.0) for r in ajustes if r is not dominante]
                esquinas.append(kpis.prob_condicional_combinada(edad, delta, [(b, e, 0.0), *otros]))
        p_inf, p_sup = min(esquinas), max(esquinas)
        rem50 = _vida_remanente_combinada(edad, 0.5, modos)
        rem90 = _vida_remanente_combinada(edad, 0.9, modos)
    intervalo = intervalo_vigente(s, pos, ajustes, hoy)
    ot_abierta = s.scalar(select(func.count()).select_from(EventoFalla).where(
        EventoFalla.id_posicion == pos.id,
        EventoFalla.estado.in_([EstadoEvento.AVISADO, EstadoEvento.EN_REPARACION, EstadoEvento.DEVUELTO]))) > 0
    color = semaforo.color_componente(p, edad, intervalo.valor, ot_abierta, confianza,
                                      activo.criticidad_clase.value if activo.criticidad_clase else None,
                                      umbrales(s), delta)
    if vida is not None and not vida.edad_conocida:
        color.motivos.append("Edad desconocida: el componente estaba instalado antes del sistema")
    est = s.scalar(select(EstadoComponente).where(EstadoComponente.id_posicion == pos.id, EstadoComponente.fecha == hoy))
    valores = dict(edad=edad, delta=delta, p_falla_delta=p, p_falla_delta_inf=p_inf, p_falla_delta_sup=p_sup,
                   vida_rem_mediana=rem50, vida_rem_90=rem90, intervalo_vigente=intervalo.valor,
                   fuente_intervalo=intervalo.fuente, semaforo=Semaforo(color.color), confianza=Confianza(confianza),
                   motivos=color.motivos + ([f"Intervalo: {intervalo.texto}"] if intervalo.texto else []),
                   id_resultado_weibull=dominante.id if dominante else None)
    if est is None:
        est = EstadoComponente(id_posicion=pos.id, fecha=hoy, **valores)
        s.add(est)
    else:
        for k, v in valores.items():
            setattr(est, k, v)
    s.flush()
    return est


def pares_con_fallas(s: Session) -> set[tuple[int, int, int]]:
    """(tipo, modo, activo) de cada modo con al menos una vida cerrada por falla."""
    filas = s.execute(select(PosicionComponente.id_tipo_componente, VidaComponente.id_modo_falla, PosicionComponente.id_activo)
                      .join(PosicionComponente, PosicionComponente.id == VidaComponente.id_posicion)
                      .where(VidaComponente.tipo_fin == TipoFin.FALLA, VidaComponente.id_modo_falla.is_not(None)).distinct())
    return {(t, m, a) for t, m, a in filas}


def recalcular_todo(s: Session, tz: ZoneInfo, hoy: date | None = None) -> dict:
    n_pares = 0
    for t, m, a in pares_con_fallas(s):
        recalcular_par(s, t, m, a, tz)
        n_pares += 1
    n_pos = 0
    for pos in s.scalars(select(PosicionComponente).where(PosicionComponente.activa.is_(True))):
        actualizar_estado(s, pos, tz, hoy)
        n_pos += 1
    return {"pares": n_pares, "componentes": n_pos}


def procesar_cola(s: Session, tz: ZoneInfo, limite: int = 20) -> int:
    n = 0
    for item in s.scalars(select(RecalculoPendiente).where(RecalculoPendiente.tomado_en.is_(None))
                          .order_by(RecalculoPendiente.creado_en).limit(limite)):
        item.tomado_en = ahora()
        try:
            recalcular_par(s, item.id_tipo_componente, item.id_modo, item.id_activo, tz)
            for pos in s.scalars(select(PosicionComponente).where(
                    PosicionComponente.id_tipo_componente == item.id_tipo_componente,
                    PosicionComponente.id_activo == item.id_activo if item.id_activo else true())):
                actualizar_estado(s, pos, tz)
            item.terminado_en = ahora()
        except Exception as e:  # el error queda registrado en la cola y no frena a los demás
            item.error = str(e)[:500]
        n += 1
    s.flush()
    return n
