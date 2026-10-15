"""Plan preventivo [12.G; Plan §8]: aprobación del intervalo, calendario de 52 semanas, OT preventivas con
anticipación, pruebas funcionales de fallas ocultas y diagnóstico de sobre y sub-mantenimiento.

- **Del fabricante al calculado:** mientras no hay Weibull se usa el intervalo del fabricante; cuando el par
  tiene un ajuste de desgaste con confianza suficiente, el sistema propone el calculado. El jefe aprueba: el
  plan vigente manda sobre los dos (D-037).
- **Fechas:** el intervalo está en horas de uso (o toneladas). La fecha prevista sale de la edad actual del
  componente y del ritmo real de la máquina (horas por día de los últimos 30 días).
- **Pruebas funcionales** (fallas ocultas, UNIDAD 3): el intervalo es de tiempo calendario (horas corridas),
  porque el componente está en reserva y su falla recién se ve cuando hace falta la función.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import (
    AccionOT,
    EstadoEvento,
    EstadoOT,
    FuenteIntervalo,
    OrigenEvento,
    ReglaPlan,
    TipoFin,
    TipoOT,
    VariableEdad,
)
from circularis_rel.datos.modelos import (
    Activo,
    EventoFalla,
    IntervencionProgramada,
    OrdenTrabajo,
    OTTarea,
    PlanPreventivo,
    PosicionComponente,
    ResultadoWeibull,
    TipoComponente,
    Usuario,
    VidaComponente,
)
from circularis_rel.motor import kpis
from circularis_rel.servicios import panel, recalculo
from circularis_rel.servicios import parametros as P
from circularis_rel.servicios import vidas as servicio_vidas
from circularis_rel.servicios.ot import nuevo_numero
from circularis_rel.servicios.permisos import Accion, requerir
from circularis_rel.servicios.registro import ErrorRegistro

ABIERTAS = (EstadoOT.SOLICITADA, EstadoOT.PLANIFICADA, EstadoOT.EN_EJECUCION)


def _usuario(s: Session, id_usuario: int, accion: Accion) -> Usuario:
    u = s.get(Usuario, id_usuario)
    if u is None or not u.activo:
        raise ErrorRegistro("Usuario no válido")
    requerir(u.rol, accion)
    return u


def plan_vigente(s: Session, id_posicion: int) -> PlanPreventivo | None:
    return s.scalar(select(PlanPreventivo).where(PlanPreventivo.id_posicion == id_posicion, PlanPreventivo.vigente.is_(True))
                    .order_by(PlanPreventivo.vigente_desde.desc(), PlanPreventivo.id.desc()).limit(1))


# ---------------------------------------------------------------------------
# Propuestas y aprobación
# ---------------------------------------------------------------------------


@dataclass
class Propuesta:
    id_posicion: int
    maquina: str
    componente: str
    tipo: str
    falla_oculta: bool
    plan: PlanPreventivo | None
    fabricante: float | None
    calculado: float | None
    regla_calculada: str | None
    texto_calculado: str
    confianza: str
    id_resultado: int | None
    t_optimo: float | None
    ahorro: float | None
    sugerencia: str
    diagnostico: list[str] = field(default_factory=list)


def propuestas(s: Session, hoy: date, tz: ZoneInfo) -> list[Propuesta]:
    minima = P.obtener(s, "plan.confianza_para_calculado") or "MEDIA"
    orden = ["GRIS", "BAJA", "MEDIA", "ALTA"]
    salida = []
    for pos, activo in s.execute(select(PosicionComponente, Activo).join(Activo, Activo.id == PosicionComponente.id_activo)
                                 .where(PosicionComponente.activa.is_(True), Activo.activo.is_(True))
                                 .order_by(Activo.codigo, PosicionComponente.codigo)):
        tipo = s.get(TipoComponente, pos.id_tipo_componente)
        plan = plan_vigente(s, pos.id)
        ajustes = recalculo.ajustes_para_semaforo(s, tipo.id, activo.id, pos.id)
        desgaste = [r for r in ajustes if r.beta and r.beta > 1]
        calculado = regla = t_opt = ahorro = None
        texto = "Sin Weibull de desgaste todavía"
        confianza = "GRIS"
        id_res = None
        if tipo.falla_oculta:
            texto = "Falla oculta: prueba funcional periódica"
        elif desgaste:
            r = min(desgaste, key=lambda x: x.eta)
            a = panel.analisis_costo(s, r, hoy)
            confianza, id_res = r.confianza.value, r.id
            calculado, regla, texto = a.recomendacion.intervalo, a.recomendacion.regla, a.recomendacion.texto
            t_opt, ahorro = a.t_optimo, a.ahorro
        elif ajustes:
            r = ajustes[0]
            confianza, id_res = r.confianza.value, r.id
            texto = "β ≤ 1 o fallas al azar: el cambio por tiempo no sirve (inspección, predictivo o causa raíz)"
        if plan is not None:
            sugerencia = f"Plan aprobado ({plan.regla.value.lower().replace('_', ' ')}): {plan.intervalo:g}"
            if calculado and plan.intervalo and abs(calculado - plan.intervalo) / plan.intervalo > 0.2 \
                    and orden.index(confianza) >= orden.index(minima):
                sugerencia += f". El cálculo actual da {calculado:g}: conviene revisarlo"
        elif calculado and orden.index(confianza) >= orden.index(minima):
            sugerencia = f"Aprobar el calculado: {calculado:g}"
        elif ajustes and not desgaste and not tipo.falla_oculta:
            sugerencia = "Sin cambio por tiempo: fallas al azar o de juventud. Inspección, predictivo o análisis de causa raíz"
        elif tipo.intervalo_fabricante:
            sugerencia = f"Usar el del fabricante ({tipo.intervalo_fabricante:g}) hasta tener confianza {minima.lower()}"
        elif tipo.falla_oculta:
            sugerencia = "Aprobar una prueba funcional periódica"
        else:
            sugerencia = "Sin intervalo: cargar el del fabricante o esperar datos"
        p = Propuesta(pos.id, activo.codigo, pos.codigo, tipo.nombre, tipo.falla_oculta, plan, tipo.intervalo_fabricante,
                      calculado, regla, texto, confianza, id_res, t_opt, ahorro, sugerencia)
        p.diagnostico = diagnostico(s, pos, plan, ajustes, tz)
        salida.append(p)
    return salida


def aprobar(s: Session, id_usuario: int, id_posicion: int, regla: ReglaPlan, intervalo: float | None, *,
            t_optimo: float | None = None, id_resultado: int | None = None, desde: date | None = None) -> PlanPreventivo:
    _usuario(s, id_usuario, Accion.CONFIGURAR)
    pos = s.get(PosicionComponente, id_posicion)
    if pos is None:
        raise ErrorRegistro("Componente no válido")
    if regla != ReglaPlan.NINGUNO and (intervalo is None or intervalo <= 0):
        raise ErrorRegistro("El intervalo tiene que ser mayor que cero")
    tipo = s.get(TipoComponente, pos.id_tipo_componente)
    for previo in s.scalars(select(PlanPreventivo).where(PlanPreventivo.id_posicion == id_posicion, PlanPreventivo.vigente.is_(True))):
        previo.vigente = False
    plan = PlanPreventivo(id_posicion=id_posicion, regla=regla, intervalo=intervalo if regla != ReglaPlan.NINGUNO else None,
                          unidad=tipo.variable_edad, t_optimo_calculado=t_optimo, vigente_desde=desde or date.today(),
                          vigente=True, id_resultado_weibull=id_resultado)
    s.add(plan)
    s.flush()
    return plan


# ---------------------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------------------


def _ultima_prueba(s: Session, id_posicion: int) -> datetime | None:
    return s.scalar(select(OrdenTrabajo.fin_real).where(OrdenTrabajo.id_posicion == id_posicion,
                                                        OrdenTrabajo.tipo == TipoOT.PRUEBA_FUNCIONAL,
                                                        OrdenTrabajo.estado.in_([EstadoOT.CERRADA, EstadoOT.VALIDADA]))
                    .order_by(OrdenTrabajo.fin_real.desc()).limit(1))


def fechas_previstas(s: Session, plan: PlanPreventivo, hoy: date, tz: ZoneInfo, dias: int = 364) -> tuple[list[date], str | None]:
    """Fechas de las próximas intervenciones del plan dentro de `dias`. Devuelve también un aviso si hubo que suponer algo."""
    if not plan.intervalo:
        return [], None
    pos = s.get(PosicionComponente, plan.id_posicion)
    hasta = hoy + timedelta(days=dias)
    if plan.regla == ReglaPlan.PRUEBA_FUNCIONAL:
        periodo = plan.intervalo / 24
        base = _ultima_prueba(s, pos.id)
        aviso = None
        if base is None:
            vida = servicio_vidas.vida_abierta(s, pos.id)
            base = vida.fecha_instalacion if vida and vida.edad_conocida else None
        if base is None:
            primera, aviso = hoy, "Sin prueba registrada: la primera queda para ya"
        else:
            primera = max(hoy, base.astimezone(tz).date() + timedelta(days=periodo))
    else:
        toneladas = plan.unidad == VariableEdad.TONELADAS
        ritmo = recalculo.ritmo_diario(s, pos.id_activo, toneladas, hoy)
        if not ritmo:
            return [], "Sin ritmo de uso (faltan partes y horas promedio por día): no se puede fechar"
        periodo = plan.intervalo / ritmo
        vida = servicio_vidas.vida_abierta(s, pos.id)
        aviso = None
        if vida is None or not vida.edad_conocida:
            primera, aviso = hoy, "Edad desconocida: el primer cambio queda para ya"
        else:
            servicio_vidas.actualizar_edad(s, vida, tz)
            edad = (vida.edad_toneladas if toneladas else vida.edad_horas) or 0.0
            primera = hoy + timedelta(days=max(0.0, (plan.intervalo - edad) / ritmo))
    # Si ya hay una OT abierta de este plan, la próxima va un período después de esa.
    abierta = s.scalar(select(OrdenTrabajo.fecha_programada).where(OrdenTrabajo.id_plan == plan.id, OrdenTrabajo.estado.in_(ABIERTAS))
                       .order_by(OrdenTrabajo.fecha_programada.desc()).limit(1))
    if abierta is not None:
        primera = max(primera, abierta + timedelta(days=periodo))
    fechas, f = [], primera
    while f <= hasta and len(fechas) < 400:
        fechas.append(f)
        f = f + timedelta(days=max(periodo, 1))
    return fechas, aviso


def programar(s: Session, hoy: date, tz: ZoneInfo, dias: int = 364) -> dict[str, int]:
    """Rehace las intervenciones futuras sin OT de cada plan vigente (las que ya tienen OT no se tocan)."""
    n_planes = n_fechas = 0
    for plan in s.scalars(select(PlanPreventivo).where(PlanPreventivo.vigente.is_(True), PlanPreventivo.regla != ReglaPlan.NINGUNO)):
        for vieja in s.scalars(select(IntervencionProgramada).where(IntervencionProgramada.id_plan == plan.id,
                                                                     IntervencionProgramada.id_ot.is_(None))):
            s.delete(vieja)
        s.flush()
        fechas, aviso = fechas_previstas(s, plan, hoy, tz, dias)
        for f in fechas:
            s.add(IntervencionProgramada(id_plan=plan.id, fecha_prevista=f, ventana=aviso))
        n_planes += 1
        n_fechas += len(fechas)
    # Las intervenciones sin OT de planes que ya no están vigentes se borran.
    for vieja in s.scalars(select(IntervencionProgramada).join(PlanPreventivo, PlanPreventivo.id == IntervencionProgramada.id_plan)
                           .where(PlanPreventivo.vigente.is_(False), IntervencionProgramada.id_ot.is_(None))):
        s.delete(vieja)
    s.flush()
    return {"planes": n_planes, "intervenciones": n_fechas}


@dataclass
class FilaCalendario:
    maquina: str
    nombre_maquina: str
    tarea: str
    lugar: str
    tiempo_h: float | None
    semanas: set[int]  # 1..52 desde la semana de inicio
    id_plan: int


def lunes(d: date) -> date:
    return d - timedelta(days=d.weekday())


def calendario(s: Session, inicio: date, semanas: int = 52) -> list[FilaCalendario]:
    """Grilla máquina × tarea × semana (formato MANT/1CMP001 y MANT/2CMP001) desde el lunes de `inicio`."""
    base = lunes(inicio)
    fin = base + timedelta(weeks=semanas)
    filas: dict[int, FilaCalendario] = {}
    for iv, plan in s.execute(select(IntervencionProgramada, PlanPreventivo)
                              .join(PlanPreventivo, PlanPreventivo.id == IntervencionProgramada.id_plan)
                              .where(IntervencionProgramada.fecha_prevista >= base, IntervencionProgramada.fecha_prevista < fin)):
        if plan.id not in filas:
            pos = s.get(PosicionComponente, plan.id_posicion)
            activo = s.get(Activo, pos.id_activo)
            tipo = s.get(TipoComponente, pos.id_tipo_componente)
            verbo = "Prueba funcional de" if plan.regla == ReglaPlan.PRUEBA_FUNCIONAL else "Cambio de"
            filas[plan.id] = FilaCalendario(activo.codigo, activo.nombre, f"{verbo} {tipo.nombre} ({pos.codigo})",
                                            pos.ubicacion or activo.ubicacion or "", tipo.hh_preventiva, set(), plan.id)
        filas[plan.id].semanas.add((iv.fecha_prevista - base).days // 7 + 1)
    return sorted(filas.values(), key=lambda f: (f.maquina, f.tarea))


# ---------------------------------------------------------------------------
# OT preventivas y pruebas funcionales
# ---------------------------------------------------------------------------


def generar_ot(s: Session, hoy: date) -> list[OrdenTrabajo]:
    """OT de las intervenciones que caen dentro de la anticipación (`politicas.anticipacion_ot_dias`)."""
    anticipacion = int(P.obtener(s, "politicas.anticipacion_ot_dias"))
    nuevas = []
    for iv, plan in s.execute(select(IntervencionProgramada, PlanPreventivo)
                              .join(PlanPreventivo, PlanPreventivo.id == IntervencionProgramada.id_plan)
                              .where(PlanPreventivo.vigente.is_(True), IntervencionProgramada.id_ot.is_(None),
                                     IntervencionProgramada.fecha_prevista <= hoy + timedelta(days=anticipacion))
                              .order_by(IntervencionProgramada.fecha_prevista)):
        if s.scalar(select(OrdenTrabajo.id).where(OrdenTrabajo.id_plan == plan.id, OrdenTrabajo.estado.in_(ABIERTAS)).limit(1)):
            continue  # una OT abierta por plan
        pos = s.get(PosicionComponente, plan.id_posicion)
        tipo = s.get(TipoComponente, pos.id_tipo_componente)
        prueba = plan.regla == ReglaPlan.PRUEBA_FUNCIONAL
        ot = OrdenTrabajo(numero=nuevo_numero(s), tipo=TipoOT.PRUEBA_FUNCIONAL if prueba else TipoOT.PREVENTIVA,
                          id_activo=pos.id_activo, id_posicion=pos.id, id_plan=plan.id, fecha_programada=iv.fecha_prevista,
                          estado=EstadoOT.PLANIFICADA)
        s.add(ot)
        s.flush()
        if prueba:
            tareas = [f"Prueba funcional de {tipo.nombre} ({pos.codigo}): provocar la condición y verificar que actúe",
                      "Anotar el resultado: actuó bien o no actuó (si no actuó, queda el aviso de falla)"]
        else:
            tareas = [f"Reemplazar {tipo.nombre} ({pos.codigo})", "Verificar el funcionamiento y limpiar la zona"]
        for i, texto in enumerate(tareas, 1):
            s.add(OTTarea(id_ot=ot.id, numero=i, descripcion=texto, tiempo_h=tipo.hh_preventiva if i == 1 else None))
        iv.id_ot = ot.id
        nuevas.append(ot)
    s.flush()
    return nuevas


def cerrar_prueba_funcional(s: Session, id_usuario: int, id_ot: int, momento: datetime, actuo: bool,
                            hh: float | None = None, observaciones: str | None = None) -> OrdenTrabajo:
    """Cierra la prueba. Si el componente no actuó, la falla oculta queda revelada: se crea el aviso de falla
    (origen PRUEBA_FUNCIONAL) para que siga el circuito normal de reparación y validación."""
    u = _usuario(s, id_usuario, Accion.CERRAR_OT)
    ot = s.get(OrdenTrabajo, id_ot)
    if ot is None or ot.tipo != TipoOT.PRUEBA_FUNCIONAL or ot.estado not in ABIERTAS:
        raise ErrorRegistro("La OT no es una prueba funcional abierta")
    if momento > ahora():
        raise ErrorRegistro("La fecha no puede ser futura")
    ot.inicio_real = ot.inicio_real or momento
    ot.fin_real = momento
    ot.hh_propias = hh
    ot.responsable = ot.responsable or u.nombre
    ot.accion = AccionOT.INSPECCION_OK if actuo else AccionOT.INSPECCION_FALLA
    ot.observaciones = observaciones
    ot.estado = EstadoOT.CERRADA
    if not actuo:
        s.add(EventoFalla(id_activo=ot.id_activo, id_posicion=ot.id_posicion, fecha_hora_falla=momento,
                          origen=OrigenEvento.PRUEBA_FUNCIONAL, estado=EstadoEvento.AVISADO, id_usuario_alta=u.id,
                          observaciones=f"No actuó en la prueba funcional {ot.numero}"))
    s.flush()
    return ot


def estado_prueba(s: Session, pos: PosicionComponente, hoy: date, tz: ZoneInfo) -> tuple[str, str] | None:
    """Semáforo de un componente con falla oculta según su prueba funcional: (color, motivo), o None si no aplica."""
    tipo = s.get(TipoComponente, pos.id_tipo_componente)
    if not tipo.falla_oculta:
        return None
    plan = plan_vigente(s, pos.id)
    if plan is None or plan.regla != ReglaPlan.PRUEBA_FUNCIONAL or not plan.intervalo:
        return "GRIS", "Falla oculta: falta el plan de prueba funcional (sin eventos no quiere decir que funcione)"
    ultima = _ultima_prueba(s, pos.id)
    if ultima is None:
        return "ROJO", "Falla oculta sin prueba funcional registrada"
    dias = (hoy - ultima.astimezone(tz).date()).days
    periodo = plan.intervalo / 24
    if dias > periodo:
        return "ROJO", f"Prueba funcional vencida hace {dias - periodo:.0f} días"
    if dias > P.obtener(s, "semaforo.fraccion_intervalo_amarillo") * periodo:
        return "AMARILLO", f"Prueba funcional por vencer (faltan {periodo - dias:.0f} días)"
    return "VERDE", f"Última prueba funcional hace {dias} días"


# ---------------------------------------------------------------------------
# Sobre y sub-mantenimiento (UNIDAD 3, diap. 48–52)
# ---------------------------------------------------------------------------


def diagnostico(s: Session, pos: PosicionComponente, plan: PlanPreventivo | None, ajustes: list[ResultadoWeibull],
                tz: ZoneInfo) -> list[str]:
    """Explicaciones en lenguaje de planta. Sobre-mantenimiento: el preventivo corta vidas muy por debajo de la vida
    útil (o hay preventivo por tiempo con β ≤ 1). Sub-mantenimiento: el intervalo es largo y fallan antes del cambio."""
    textos = []
    frac_sobre = P.obtener(s, "plan.sobre_fraccion")
    frac_sub = P.obtener(s, "plan.sub_fraccion_fallas")
    vidas = list(s.scalars(select(VidaComponente).where(VidaComponente.id_posicion == pos.id, VidaComponente.validado.is_(True),
                                                        VidaComponente.tipo_fin.in_([TipoFin.FALLA, TipoFin.SUSPENSION_PREVENTIVA]),
                                                        VidaComponente.edad_conocida.is_(True))))
    edades_prev = [v.edad_horas for v in vidas if v.tipo_fin == TipoFin.SUSPENSION_PREVENTIVA and v.edad_horas]
    edades_falla = [v.edad_horas for v in vidas if v.tipo_fin == TipoFin.FALLA and v.edad_horas]
    desgaste = [r for r in ajustes if r.beta and r.beta > 1]
    if plan is not None and plan.regla != ReglaPlan.PRUEBA_FUNCIONAL and plan.intervalo and ajustes \
            and all(r.beta and r.beta <= 1 for r in ajustes):
        textos.append("Sobre-mantenimiento: hay cambio por tiempo, pero las fallas son al azar o de juventud (β ≤ 1). "
                      "Cambiar antes no reduce las fallas y suma gasto.")
    if desgaste and edades_prev:
        r = min(desgaste, key=lambda x: x.eta)
        referencia = plan.t_optimo_calculado if plan and plan.t_optimo_calculado else r.eta
        cortas = [e for e in edades_prev if e < frac_sobre * referencia]
        if len(cortas) / len(edades_prev) > 0.5:
            textos.append(f"Sobre-mantenimiento: {len(cortas)} de {len(edades_prev)} cambios preventivos se hicieron antes del "
                          f"{frac_sobre:.0%} de la vida de referencia ({referencia:.0f} h). Se tira vida útil.")
    if plan is not None and plan.intervalo and plan.regla != ReglaPlan.PRUEBA_FUNCIONAL and edades_falla:
        antes = [e for e in edades_falla if e < plan.intervalo]
        total = len(edades_falla) + len(edades_prev)
        frac = len(antes) / total
        if frac > frac_sub:
            esperado = ""
            if desgaste:
                r = min(desgaste, key=lambda x: x.eta)
                esperado = f" (con el Weibull se esperaría {kpis.infiabilidad(plan.intervalo, r.beta, r.eta):.0%})"
            textos.append(f"Sub-mantenimiento: el {frac:.0%} de los cambios fueron por falla antes del intervalo de "
                          f"{plan.intervalo:g} h{esperado}. El correctivo le gana al preventivo: revisar el intervalo.")
    return textos


def fuente_actual(s: Session, pos: PosicionComponente) -> FuenteIntervalo:
    plan = plan_vigente(s, pos.id)
    if plan is not None and plan.intervalo:
        return FuenteIntervalo.CALCULADO
    tipo = s.get(TipoComponente, pos.id_tipo_componente)
    return FuenteIntervalo.FABRICANTE if tipo.intervalo_fabricante else FuenteIntervalo.NINGUNO
