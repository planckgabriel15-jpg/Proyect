"""Auditoría automática de toda modificación (Plan §2, §11).

- `before_flush`: si se modifica o borra un registro validado y la sesión no trae motivo,
  aborta con `MotivoRequerido`. Vale aunque alguien escriba sin pasar por la pantalla.
- `after_flush`: escribe una fila de `auditoria` por campo modificado (o una por alta/baja)
  con usuario, fecha, valor anterior, valor nuevo y motivo. Se escribe con SQL directo sobre
  la misma conexión, dentro de la misma transacción: si la operación se revierte, la
  auditoría también.

El usuario, el motivo y la acción viajan en `session.info` (ver `BaseDatos.escritura`).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from enum import Enum

from sqlalchemy import event, insert, inspect
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import AccionAuditoria, EstadoEvento, EstadoOT
from circularis_rel.datos.modelos import (
    TABLAS_NO_AUDITADAS,
    Auditoria,
    EventoFalla,
    OrdenTrabajo,
    VidaComponente,
)

CAMPOS_IGNORADOS = {"creado_en", "actualizado_en", "version"}


class MotivoRequerido(Exception):
    """Se intentó corregir un registro validado sin indicar el motivo."""


def _serializar(valor) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, Enum):
        return str(valor.value)
    if isinstance(valor, datetime | date):
        return valor.isoformat()
    if isinstance(valor, dict | list):
        return json.dumps(valor, ensure_ascii=False, sort_keys=True, default=str)
    return str(valor)


def valor_original(obj, atributo: str):
    hist = inspect(obj).attrs[atributo].history
    if hist.deleted:
        return hist.deleted[0]
    if hist.unchanged:
        return hist.unchanged[0]
    return None


def _estaba_validado(obj) -> bool:
    if isinstance(obj, EventoFalla):
        return valor_original(obj, "estado") == EstadoEvento.VALIDADO
    if isinstance(obj, OrdenTrabajo):
        return valor_original(obj, "estado") == EstadoOT.VALIDADA
    if isinstance(obj, VidaComponente):
        return bool(valor_original(obj, "validado"))
    return False


def _cambios(obj) -> list[tuple[str, object, object]]:
    estado = inspect(obj)
    salida = []
    for col in estado.mapper.column_attrs:
        if col.key in CAMPOS_IGNORADOS:
            continue
        hist = estado.attrs[col.key].history
        if hist.has_changes():
            anterior = hist.deleted[0] if hist.deleted else None
            nuevo = hist.added[0] if hist.added else None
            if _serializar(anterior) != _serializar(nuevo):
                salida.append((col.key, anterior, nuevo))
    return salida


def _auditable(obj) -> bool:
    tabla = getattr(obj, "__tablename__", None)
    return tabla is not None and tabla not in TABLAS_NO_AUDITADAS


def _antes_de_flush(session: Session, _ctx, _instancias) -> None:
    motivo = (session.info.get("motivo") or "").strip()
    if motivo:
        return
    for obj in list(session.dirty) + list(session.deleted):
        if _auditable(obj) and _estaba_validado(obj):
            if obj in session.deleted or _cambios(obj):
                raise MotivoRequerido(
                    f"Corregir un registro validado ({obj.__tablename__} id={obj.id}) exige un motivo"
                )


def _accion_para(obj, cambios, por_defecto: AccionAuditoria) -> AccionAuditoria:
    for campo, _ant, nuevo in cambios:
        if campo == "estado" and nuevo in (EstadoEvento.VALIDADO, EstadoOT.VALIDADA):
            return AccionAuditoria.VALIDACION
        if campo == "estado" and nuevo == EstadoEvento.DEVUELTO:
            return AccionAuditoria.DEVOLUCION
    return por_defecto


def _despues_de_flush(session: Session, _ctx) -> None:
    usuario = session.info.get("usuario_id")
    motivo = session.info.get("motivo")
    accion_sesion = session.info.get("accion")
    filas: list[dict] = []
    momento = ahora()

    for obj in session.new:
        if not _auditable(obj):
            continue
        valores = {
            c.key: _serializar(getattr(obj, c.key))
            for c in inspect(obj).mapper.column_attrs
            if c.key not in CAMPOS_IGNORADOS and getattr(obj, c.key) is not None
        }
        filas.append(dict(
            fecha=momento, id_usuario=usuario,
            accion=accion_sesion or AccionAuditoria.ALTA,
            tabla=obj.__tablename__, id_registro=getattr(obj, "id", None), campo=None,
            valor_anterior=None, valor_nuevo=json.dumps(valores, ensure_ascii=False, sort_keys=True),
            motivo=motivo,
        ))

    for obj in session.dirty:
        if not _auditable(obj) or not session.is_modified(obj, include_collections=False):
            continue
        cambios = _cambios(obj)
        accion = _accion_para(obj, cambios, accion_sesion or AccionAuditoria.MODIFICACION)
        for campo, anterior, nuevo in cambios:
            filas.append(dict(
                fecha=momento, id_usuario=usuario, accion=accion,
                tabla=obj.__tablename__, id_registro=getattr(obj, "id", None), campo=campo,
                valor_anterior=_serializar(anterior), valor_nuevo=_serializar(nuevo), motivo=motivo,
            ))

    for obj in session.deleted:
        if not _auditable(obj):
            continue
        filas.append(dict(
            fecha=momento, id_usuario=usuario, accion=AccionAuditoria.BAJA,
            tabla=obj.__tablename__, id_registro=getattr(obj, "id", None), campo=None,
            valor_anterior=None, valor_nuevo=None, motivo=motivo,
        ))

    if filas:
        session.connection().execute(insert(Auditoria), filas)


_registrado = False


def registrar_auditoria() -> None:
    """Engancha los listeners a todas las sesiones (idempotente)."""
    global _registrado
    if _registrado:
        return
    event.listen(Session, "before_flush", _antes_de_flush)
    event.listen(Session, "after_flush", _despues_de_flush)
    _registrado = True
