"""Lectura y escritura de parámetros con historia (`parametro.vigente_desde`).

Un parámetro sin valor devuelve None: quien lo usa debe mostrar "falta dato", nunca un cero.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import TipoParametro
from circularis_rel.datos.modelos import Parametro


class ParametroDesconocido(KeyError):
    pass


def _convertir(texto: str | None, tipo: TipoParametro) -> Any:
    if texto is None:
        return None
    match tipo:
        case TipoParametro.ENTERO:
            return int(float(texto))
        case TipoParametro.REAL:
            return float(texto)
        case TipoParametro.BOOL:
            return texto.strip().lower() in {"1", "true", "si", "sí", "verdadero"}
        case TipoParametro.JSON:
            return json.loads(texto)
        case _:
            return texto


def _a_texto(valor: Any, tipo: TipoParametro) -> str | None:
    if valor is None:
        return None
    if tipo == TipoParametro.JSON:
        return json.dumps(valor, ensure_ascii=False)
    if tipo == TipoParametro.BOOL:
        return "1" if valor else "0"
    return str(valor)


def registro_vigente(s: Session, clave: str, fecha: date | None = None) -> Parametro:
    fecha = fecha or date.today()
    p = s.scalar(
        select(Parametro)
        .where(Parametro.clave == clave, Parametro.vigente_desde <= fecha)
        .order_by(Parametro.vigente_desde.desc())
        .limit(1)
    )
    if p is None:
        # Si solo hay valores futuros o la fecha es anterior a todos, tomar el más antiguo.
        p = s.scalar(select(Parametro).where(Parametro.clave == clave).order_by(Parametro.vigente_desde).limit(1))
    if p is None:
        raise ParametroDesconocido(clave)
    return p


def obtener(s: Session, clave: str, fecha: date | None = None) -> Any:
    p = registro_vigente(s, clave, fecha)
    return _convertir(p.valor, p.tipo)


def fijar(s: Session, clave: str, valor: Any, vigente_desde: date | None = None) -> Parametro:
    """Guarda un valor nuevo. Si ya hay uno con la misma fecha, lo reemplaza (queda auditado)."""
    base = registro_vigente(s, clave)
    vigente_desde = vigente_desde or date.today()
    texto = _a_texto(_convertir(_a_texto(valor, base.tipo), base.tipo), base.tipo)  # valida el tipo
    existente = s.scalar(select(Parametro).where(Parametro.clave == clave, Parametro.vigente_desde == vigente_desde))
    if existente is not None:
        existente.valor = texto
        return existente
    nuevo = Parametro(clave=clave, valor=texto, tipo=base.tipo, unidad=base.unidad, grupo=base.grupo,
                      descripcion=base.descripcion, fuente="Editado por el jefe", vigente_desde=vigente_desde)
    s.add(nuevo)
    return nuevo
