"""Recálculo desde el proceso de tareas: cola por evento (cada 5 s) y recálculo completo nocturno."""

from __future__ import annotations

from circularis_rel.config import Config
from circularis_rel.datos.db import BaseDatos
from circularis_rel.servicios import recalculo

MOTIVO = "Recálculo automático"


def procesar_cola(db: BaseDatos, cfg: Config) -> int:
    with db.escritura(motivo=MOTIVO) as s:
        return recalculo.procesar_cola(s, cfg.zona_horaria)


def recalcular_todo(db: BaseDatos, cfg: Config) -> dict:
    with db.escritura(motivo=MOTIVO) as s:
        return recalculo.recalcular_todo(s, cfg.zona_horaria)
