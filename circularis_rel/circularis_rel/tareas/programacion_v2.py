"""Trabajos de la versión 2 (fase 3): plan preventivo, alertas diarias, mails y reportes.

Se agregan al planificador de `worker.py`. Cada uno se puede correr solo: `circularis tareas --una-vez plan`.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from apscheduler.triggers.cron import CronTrigger

from circularis_rel.config import Config
from circularis_rel.datos.db import BaseDatos, ahora
from circularis_rel.servicios import alertas, correo, plan_preventivo, reporte, repuestos

log = logging.getLogger("circularis.tareas")
MOTIVO = "Proceso automático"


def plan(db: BaseDatos, cfg: Config) -> dict:
    """Reprograma el calendario con la edad y el ritmo de hoy y genera las OT que entran en la anticipación."""
    hoy = ahora().astimezone(cfg.zona_horaria).date()
    with db.escritura(motivo=MOTIVO) as s:
        r = plan_preventivo.programar(s, hoy, cfg.zona_horaria)
        r["ot_generadas"] = len(plan_preventivo.generar_ot(s, hoy))
    log.info("Plan preventivo: %s", r)
    return r


def alertas_diarias(db: BaseDatos, cfg: Config) -> dict:
    hoy = ahora().astimezone(cfg.zona_horaria).date()
    with db.escritura(motivo=MOTIVO) as s:
        r = {"edad_intervalo": alertas.edad_sobre_intervalo(s, hoy), "stock": repuestos.alertas_stock(s, hoy, cfg.zona_horaria),
             "sin_validar": alertas.eventos_sin_validar(s)}
    log.info("Alertas diarias: %s", r)
    return r


def mails_inmediatos(db: BaseDatos, cfg: Config) -> int:
    with db.escritura(motivo=MOTIVO) as s:
        return correo.enviar_alertas(s, cfg, inmediatas=True)


def mails_resumen(db: BaseDatos, cfg: Config) -> int:
    with db.escritura(motivo=MOTIVO) as s:
        return correo.enviar_alertas(s, cfg, inmediatas=False)


def reporte_mensual(db: BaseDatos, cfg: Config) -> str:
    """El día 1: PDF del mes anterior, guardado en la carpeta de reportes y mandado al jefe y a la gerencia."""
    hoy = ahora().astimezone(cfg.zona_horaria).date()
    desde, hasta = reporte.mes_anterior(hoy)
    with db.lectura() as s:
        datos = reporte.pdf(s, desde, hasta, cfg.zona_horaria, "Reporte mensual de mantenimiento")
        para = correo.destinatarios(s, "JEFE,GERENCIA")
    cfg.dir_reportes.mkdir(parents=True, exist_ok=True)
    archivo = cfg.dir_reportes / f"reporte_{desde:%Y-%m}.pdf"
    archivo.write_bytes(datos)
    correo.enviar(cfg, para, f"Circularis: reporte de mantenimiento de {desde:%m/%Y}",
                  "Adjunto el reporte mensual de mantenimiento.", [(archivo.name, datos, "application/pdf")])
    return str(archivo)


def resumen_semanal(db: BaseDatos, cfg: Config) -> bool:
    """Lunes: resumen gerencial de la semana anterior en PDF (Plan §7)."""
    hoy = ahora().astimezone(cfg.zona_horaria).date()
    hasta = hoy - timedelta(days=hoy.weekday() + 1)
    desde = hasta - timedelta(days=6)
    with db.lectura() as s:
        datos = reporte.pdf(s, desde, hasta, cfg.zona_horaria, "Resumen semanal de mantenimiento")
        para = correo.destinatarios(s, "JEFE,GERENCIA")
    return correo.enviar(cfg, para, f"Circularis: resumen de la semana del {desde:%d/%m}", "Adjunto el resumen semanal.",
                         [(f"resumen_{desde:%Y-%m-%d}.pdf", datos, "application/pdf")])


TRABAJOS = {"plan": plan, "alertas_diarias": alertas_diarias, "mails": mails_inmediatos, "mails_resumen": mails_resumen,
            "reporte_mensual": reporte_mensual, "resumen_semanal": resumen_semanal}


def agregar(sch, db: BaseDatos, cfg: Config) -> None:
    tz = cfg.zona_horaria
    sch.add_job(plan, CronTrigger(hour=2, minute=30, timezone=tz), args=[db, cfg], id="plan")
    sch.add_job(alertas_diarias, CronTrigger(hour=6, minute=45, timezone=tz), args=[db, cfg], id="alertas_diarias")
    sch.add_job(mails_inmediatos, "interval", minutes=10, args=[db, cfg], id="mails", max_instances=1, coalesce=True)
    sch.add_job(mails_resumen, CronTrigger(hour=7, minute=0, timezone=tz), args=[db, cfg], id="mails_resumen")
    sch.add_job(resumen_semanal, CronTrigger(day_of_week="mon", hour=7, minute=30, timezone=tz), args=[db, cfg],
                id="resumen_semanal")
    sch.add_job(reporte_mensual, CronTrigger(day=1, hour=7, minute=15, timezone=tz), args=[db, cfg], id="reporte_mensual")
