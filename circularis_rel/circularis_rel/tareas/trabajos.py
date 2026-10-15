"""Trabajos programados. Cada uno es una función que se puede correr sola (tests y línea de comandos)."""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path

from circularis_rel.config import Config
from circularis_rel.datos.db import BaseDatos, ahora
from circularis_rel.servicios import alertas, faltantes, vidas
from circularis_rel.servicios import parametros as P
from circularis_rel.tareas import backup

log = logging.getLogger("circularis.tareas")
MOTIVO_AUTOMATICO = "Proceso automático"


def nocturno(db: BaseDatos, cfg: Config) -> dict:
    """Partes estimados, edades de todas las vidas y (desde la fase 1b) recálculo completo."""
    hoy = ahora().astimezone(cfg.zona_horaria).date()
    with db.escritura(motivo=MOTIVO_AUTOMATICO) as s:
        estimados = faltantes.completar_estimados(s, hoy, cfg.zona_horaria)
        edades = vidas.actualizar_edades(s, cfg.zona_horaria)
    resultado = {"partes_estimados": estimados, "edades_actualizadas": edades}
    try:
        from circularis_rel.tareas import recalculo  # fase 1b

        resultado |= recalculo.recalcular_todo(db, cfg)
    except ImportError:
        pass
    log.info("Nocturno: %s", resultado)
    return resultado


def partes_faltantes(db: BaseDatos, cfg: Config) -> int:
    """Al día siguiente: alerta al encargado por cada parte que falta de ayer."""
    ayer = ahora().astimezone(cfg.zona_horaria).date() - timedelta(days=1)
    n = 0
    with db.escritura(motivo=MOTIVO_AUTOMATICO) as s:
        for f in faltantes.faltantes(s, ayer, ayer):
            if alertas.emitir(s, "PARTE_FALTANTE", "media", f"Falta el parte de {f.codigo} del {ayer:%d/%m} ({f.turno})",
                              f"parte:{f.id_activo}:{f.fecha}:{f.id_turno}", id_activo=f.id_activo,
                              destinatarios="ENCARGADO"):
                n += 1
    return n


def hacer_backup(db: BaseDatos, cfg: Config) -> Path:
    with db.lectura() as s:
        externa = P.obtener(s, "backup.carpeta_externa")
        diarios = P.obtener(s, "backup.retencion_diaria")
        mensuales = P.obtener(s, "backup.retencion_mensual")
    archivo = backup.hacer_backup(cfg.url_db, cfg.dir_backups, cfg.dir_fotos, Path(externa) if externa else None)
    backup.rotar(cfg.dir_backups, diarios, mensuales)
    log.info("Backup: %s", archivo)
    return archivo


def prueba_restauracion(db: BaseDatos, cfg: Config) -> backup.ResultadoPrueba:
    r = backup.probar_restauracion(cfg.dir_backups)
    if not r.ok:
        with db.escritura(motivo=MOTIVO_AUTOMATICO) as s:
            alertas.emitir(s, "BACKUP", "alta", f"La prueba mensual de restauración falló: {r.integridad}",
                           f"backup:prueba:{r.fecha[:7]}", destinatarios="JEFE")
    return r
