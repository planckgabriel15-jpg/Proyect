"""Historia DEMO (FICTICIA) para ver el panel con datos: unos dos años y medio de partes de turno,
fallas validadas y cambios preventivos de las máquinas DEMO.

- DEMO-AGR-001 · cuchillas: vidas parecidas al ejemplo del Plan §15 (296 S, 408 F, 560 F, 648 S, 688 F,
  784 F, 920 F; ahora en servicio). Se usan múltiplos de 8 h para que cada falla caiga al final del
  turno y la edad calculada desde los partes coincida.
- DEMO-AGR-001 y DEMO-LAV-001 · rulemanes: fallas casi al azar (β ≈ 1), para la sugerencia de análisis
  de causa raíz.
- DEMO-EXT-001 · husillo: una sola falla (Weibayes con β de referencia ficticio). La extrusora trabaja
  dos turnos; su válvula de seguridad tiene edad desconocida (instalada antes del sistema).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
from sqlalchemy import select

from circularis_rel.datos.db import BaseDatos
from circularis_rel.datos.enums import (
    AccionOT,
    AparicionFalla,
    CapacidadFalla,
    EfectoFalla,
    EstadoEvento,
    EstadoOT,
    EstadoParte,
    TipoCatalogo,
    TipoFin,
    TipoOT,
)
from circularis_rel.datos.modelos import (
    Activo,
    Catalogo,
    EventoFalla,
    MotivoParada,
    OrdenTrabajo,
    ParteTurno,
    PosicionComponente,
    Turno,
    Usuario,
    VidaComponente,
)
from circularis_rel.servicios import parametros as P

FUENTE_DEMO = "DEMO (ficticio)"
TURNO_INICIO = time(6)
HORAS_TURNO = 8.0


def _dias_habiles_hacia_atras(hasta: date, n: int) -> list[date]:
    dias: list[date] = []
    d = hasta
    while len(dias) < n:
        if d.weekday() < 5:
            dias.append(d)
        d -= timedelta(days=1)
    return sorted(dias)


def _momento(dias: list[date], horas: float, tz: ZoneInfo) -> datetime:
    """Momento en que se acumulan `horas` operadas (turno de 6 a 14, de lunes a viernes)."""
    completos = int(horas // HORAS_TURNO)
    resto = horas - completos * HORAS_TURNO
    if resto == 0:  # termina justo al final del turno
        return datetime.combine(dias[completos - 1], TURNO_INICIO, tzinfo=tz) + timedelta(hours=HORAS_TURNO)
    return datetime.combine(dias[completos], TURNO_INICIO, tzinfo=tz) + timedelta(hours=resto)


def cargar_historia_demo(db: BaseDatos, tz: ZoneInfo, hoy: date | None = None) -> dict:
    hoy = hoy or datetime.now(tz).date()
    rng = np.random.default_rng(2026)
    cuchillas = [(296, "S"), (408, "F"), (560, "F"), (648, "S"), (688, "F"), (784, "F"), (920, "F")]
    total = sum(e for e, _ in cuchillas) + 520
    dias = _dias_habiles_hacia_atras(hoy - timedelta(days=1), int(total / HORAS_TURNO) + 1)
    resumen = {"partes": 0, "fallas": 0, "preventivos": 0}
    with db.escritura(motivo="Historia DEMO (ficticia)") as s:
        turno = s.scalar(select(Turno).where(Turno.codigo == "DEMO-M"))
        tarde = s.scalar(select(Turno).where(Turno.codigo == "DEMO-T"))
        jefe = s.scalar(select(Usuario).where(Usuario.usuario == "demo.jefe"))
        enc = s.scalar(select(Usuario).where(Usuario.usuario == "demo.encargado"))
        ruido = s.scalar(select(Catalogo.id).where(Catalogo.tipo == TipoCatalogo.SINTOMA, Catalogo.codigo == "RUIDO"))
        causa = s.scalar(select(Catalogo.id).where(Catalogo.tipo == TipoCatalogo.CAUSA, Catalogo.codigo == "DESGASTE"))
        lubric = s.scalar(select(Catalogo.id).where(Catalogo.tipo == TipoCatalogo.CAUSA, Catalogo.codigo == "LUBRICACION"))
        activos = {a.codigo: a for a in s.scalars(select(Activo).where(Activo.codigo.like("DEMO-%")))}
        posiciones = {(p.id_activo, p.codigo): p for p in s.scalars(select(PosicionComponente))}
        modo = {c.codigo: c.id for c in s.scalars(select(Catalogo).where(Catalogo.codigo.like("DEMO-%")))}
        limpieza = s.scalar(select(MotivoParada.id).where(MotivoParada.codigo == "LIMPIEZA"))
        if s.scalar(select(ParteTurno.id).where(ParteTurno.id_activo == activos["DEMO-AGR-001"].id).limit(1)):
            return {"ya_cargada": True}
        # Partes de turno: todos los días hábiles (la extrusora, también a la tarde), con algo de limpieza
        # ocasional fuera de la agrumadora (así su edad coincide con la del Plan §15).
        for codigo, a in activos.items():
            turnos = [turno, tarde] if codigo == "DEMO-EXT-001" else [turno]
            for d in dias:
                for t in turnos:
                    no_op = 0.0
                    if codigo != "DEMO-AGR-001" and rng.random() < 0.05:
                        no_op = float(rng.choice([0.5, 1.0, 1.5]))
                    cantidad = rechazada = None
                    if codigo == "DEMO-EXT-001":  # durmientes: ciclo real algo más lento que el teórico y algún rechazo
                        cantidad = float(round((HORAS_TURNO - no_op) * 3600 / (120 * rng.uniform(1.05, 1.25))))
                        rechazada = float(round(cantidad * rng.uniform(0.0, 0.04)))
                    s.add(ParteTurno(id_activo=a.id, fecha=d, id_turno=t.id, horas_turno=HORAS_TURNO,
                                     estado=EstadoParte.PARCIAL if no_op else EstadoParte.TODO, horas_no_operadas=no_op,
                                     horas_operadas=HORAS_TURNO - no_op, id_motivo=limpieza if no_op else None,
                                     cantidad_procesada=cantidad, cantidad_rechazada=rechazada))
                    resumen["partes"] += 1
        s.flush()

        def falla(pos: PosicionComponente, inicio_vida: datetime, fin: datetime, id_modo: int, id_causa: int,
                  reparacion_h: float) -> datetime:
            ev = EventoFalla(id_activo=pos.id_activo, id_posicion=pos.id, fecha_hora_falla=fin, id_sintoma=ruido,
                             id_modo=id_modo, id_causa=id_causa, inicio_reparacion=fin,
                             fin_reparacion=fin + timedelta(hours=reparacion_h), tiempo_espera_h=0.0,
                             tiempo_reparacion_h=reparacion_h, parada_total=True, horas_parada=reparacion_h,
                             efecto=EfectoFalla.PRODUCCION, capacidad=CapacidadFalla.TOTAL,
                             aparicion=AparicionFalla.PROGRESIVA, estado=EstadoEvento.VALIDADO,
                             id_usuario_alta=enc.id, id_usuario_cierre=enc.id, id_usuario_validacion=jefe.id,
                             validado_en=fin + timedelta(hours=20))
            s.add(ev)
            s.flush()
            ot = OrdenTrabajo(numero=f"DEMO-OT-{ev.id:05d}", tipo=TipoOT.CORRECTIVA, id_activo=pos.id_activo,
                              id_posicion=pos.id, id_evento=ev.id, estado=EstadoOT.VALIDADA, inicio_real=fin,
                              fin_real=fin + timedelta(hours=reparacion_h), hh_propias=reparacion_h,
                              accion=AccionOT.REEMPLAZO)
            s.add(ot)
            s.flush()
            s.add(VidaComponente(id_posicion=pos.id, fecha_instalacion=inicio_vida, fecha_fin=fin, tipo_fin=TipoFin.FALLA,
                                 id_modo_falla=id_modo, id_evento_cierre=ev.id, id_ot_cierre=ot.id, validado=True))
            resumen["fallas"] += 1
            return fin + timedelta(hours=reparacion_h)

        def preventivo(pos: PosicionComponente, inicio_vida: datetime, fin: datetime) -> datetime:
            ot = OrdenTrabajo(numero=f"DEMO-OTP-{pos.id}-{fin:%Y%m%d}", tipo=TipoOT.PREVENTIVA, id_activo=pos.id_activo,
                              id_posicion=pos.id, estado=EstadoOT.VALIDADA, inicio_real=fin, fin_real=fin + timedelta(hours=2),
                              hh_propias=2, accion=AccionOT.REEMPLAZO, fecha_programada=fin.date())
            s.add(ot)
            s.flush()
            s.add(VidaComponente(id_posicion=pos.id, fecha_instalacion=inicio_vida, fecha_fin=fin,
                                 tipo_fin=TipoFin.SUSPENSION_PREVENTIVA, id_ot_cierre=ot.id, validado=True))
            resumen["preventivos"] += 1
            return fin + timedelta(hours=2)

        # Cuchillas de DEMO-AGR-001 (como el Plan §15)
        agr = activos["DEMO-AGR-001"]
        pos = posiciones[(agr.id, "CUCHILLAS")]
        acumulado = 0.0
        inicio = datetime.combine(dias[0], TURNO_INICIO, tzinfo=tz)
        for edad, estado in cuchillas:
            acumulado += edad
            fin = _momento(dias, acumulado, tz)
            inicio = (falla(pos, inicio, fin, modo["DEMO-PERDIDA-FILO"], causa, 4.5) if estado == "F"
                      else preventivo(pos, inicio, fin))
        s.add(VidaComponente(id_posicion=pos.id, fecha_instalacion=inicio, tipo_fin=TipoFin.EN_SERVICIO))

        # Rulemanes (fallas casi al azar) en DEMO-AGR-001 y DEMO-LAV-001
        for codigo in ("DEMO-AGR-001", "DEMO-LAV-001"):
            pos = posiciones[(activos[codigo].id, "RULEMANES")]
            inicio = datetime.combine(dias[0], TURNO_INICIO, tzinfo=tz)
            acumulado = 0.0
            while True:
                edad = float(np.ceil(650 * rng.weibull(1.0) / 8) * 8)
                if acumulado + edad >= total - 40:
                    break
                acumulado += edad
                inicio = falla(pos, inicio, _momento(dias, acumulado, tz), modo["DEMO-RUIDO-DESGASTE"], lubric, 6.0)
            s.add(VidaComponente(id_posicion=pos.id, fecha_instalacion=inicio, tipo_fin=TipoFin.EN_SERVICIO))

        # Husillo de la extrusora: una falla (Weibayes) y vida actual. La extrusora trabaja dos turnos:
        # 1200 h del turno mañana son unas 2400 h de edad.
        ext = activos["DEMO-EXT-001"]
        pos = posiciones[(ext.id, "HUSILLO")]
        inicio = datetime.combine(dias[0], TURNO_INICIO, tzinfo=tz)
        inicio = falla(pos, inicio, _momento(dias, 1200, tz), modo["DEMO-DESGASTE-HUSILLO"], causa, 30.0)
        s.add(VidaComponente(id_posicion=pos.id, fecha_instalacion=inicio, tipo_fin=TipoFin.EN_SERVICIO))
        pos = posiciones[(ext.id, "VALV-SEG")]
        s.add(VidaComponente(id_posicion=pos.id, fecha_instalacion=datetime.combine(dias[0], TURNO_INICIO, tzinfo=tz),
                             tipo_fin=TipoFin.EN_SERVICIO, edad_conocida=False))

        # Costos ficticios para la demo (valen desde el inicio de la historia).
        desde = dias[0]
        for clave, valor in (("costos.tarifa_mo_ars_h", 25_000), ("costos.margen_linea_ars_h", 600_000),
                             ("costos.horas_parada_defecto_h", 6)):
            if P.obtener(s, clave, hoy) is None:
                P.fijar(s, clave, valor, desde).fuente = FUENTE_DEMO
        # Las máquinas DEMO son el piloto de la demo (se vuelve al valor anterior al borrar la demo).
        P.fijar(s, "piloto.maquinas", sorted(activos), desde).fuente = FUENTE_DEMO
    return resumen


def historia_demo_y_recalculo(db: BaseDatos, tz: ZoneInfo) -> dict:
    from circularis_rel.servicios import alertas, amfe, flota, recalculo, sistemas

    r = cargar_historia_demo(db, tz)
    with db.escritura(motivo="Recálculo de la historia DEMO") as s:
        # Los rulemanes de la agrumadora y del lavado como flota (mismo tipo en dos máquinas).
        for g in flota.grupos(s):
            for m in flota.modos(s, g):
                flota.ajustar(s, g, m.id, tz)
        r |= recalculo.recalcular_todo(s, tz)
        hoy = datetime.now(tz).date()
        r["alertas"] = alertas.actualizar_riesgo(s, hoy)
        r["tendencias"] = len(sistemas.recalcular(s, hoy - timedelta(days=1000), hoy, tz))
        r["amfe"] = amfe.actualizar_ocurrencias(s, hoy)
    return r
