"""Exportación total a Excel: una hoja por tabla (Plan §10: la empresa nunca queda atada al software)."""

from __future__ import annotations

import io
import json
from datetime import date, datetime
from enum import Enum

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.modelos import Base

EXCLUIR = {"usuario": {"hash_password"}}


def _celda(v):
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, datetime):
        return v.replace(tzinfo=None)
    if isinstance(v, dict | list):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, date | int | float | str | bool) or v is None:
        return v
    return str(v)


def exportar_todo(s: Session) -> bytes:
    wb = Workbook(write_only=True)
    for tabla in Base.metadata.sorted_tables:
        ws = wb.create_sheet(tabla.name[:31])
        columnas = [c for c in tabla.columns if c.name not in EXCLUIR.get(tabla.name, set())]
        ws.append([c.name for c in columnas])
        for fila in s.execute(select(*columnas)):
            ws.append([_celda(v) for v in fila])
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
