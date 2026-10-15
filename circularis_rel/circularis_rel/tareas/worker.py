"""Proceso de tareas (segundo servicio de Windows, separado de la app; PLAN_TECNICO §3.3).

    circularis tareas               corre el planificador
    circularis tareas --una-vez backup
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from circularis_rel.config import cargar_config
from circularis_rel.datos.db import BaseDatos
from circularis_rel.tareas import trabajos

TRABAJOS = {
    "nocturno": trabajos.nocturno,
    "faltantes": trabajos.partes_faltantes,
    "backup": trabajos.hacer_backup,
    "prueba_restauracion": trabajos.prueba_restauracion,
}


def _cola(db, cfg):
    try:
        from circularis_rel.tareas import recalculo
    except ImportError:
        return
    recalculo.procesar_cola(db, cfg)


def correr(una_vez: str | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = cargar_config()
    db = BaseDatos(cfg.url_db)
    if una_vez:
        if una_vez == "cola":
            _cola(db, cfg)
        else:
            print(TRABAJOS[una_vez](db, cfg))
        return 0
    tz = cfg.zona_horaria
    sch = BlockingScheduler(timezone=tz)
    sch.add_job(_cola, "interval", seconds=5, args=[db, cfg], id="cola", max_instances=1, coalesce=True)
    sch.add_job(trabajos.nocturno, CronTrigger(hour=2, minute=0, timezone=tz), args=[db, cfg], id="nocturno")
    sch.add_job(trabajos.hacer_backup, CronTrigger(hour=3, minute=0, timezone=tz), args=[db, cfg], id="backup")
    sch.add_job(trabajos.prueba_restauracion, CronTrigger(day=1, hour=4, minute=0, timezone=tz), args=[db, cfg],
                id="prueba_restauracion")
    sch.add_job(trabajos.partes_faltantes, CronTrigger(hour=6, minute=30, timezone=tz), args=[db, cfg], id="faltantes")
    try:
        from circularis_rel.tareas import programacion_v2  # fase 3: mails, alertas, OT preventivas

        programacion_v2.agregar(sch, db, cfg)
    except ImportError:
        pass
    logging.info("Proceso de tareas iniciado")
    sch.start()
    return 0
