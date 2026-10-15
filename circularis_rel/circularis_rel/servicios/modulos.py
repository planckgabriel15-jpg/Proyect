"""Módulos del asistente que el jefe habilita a medida que la planta madura (P-06; UNIDAD 6: informatizar de a poco)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.modelos import ModuloHabilitado


def habilitado(s: Session, codigo: str) -> bool:
    m = s.get(ModuloHabilitado, codigo)
    return bool(m and m.habilitado)


def todos(s: Session) -> list[ModuloHabilitado]:
    return list(s.scalars(select(ModuloHabilitado).order_by(ModuloHabilitado.codigo)))


def fijar(s: Session, codigo: str, valor: bool) -> None:
    m = s.get(ModuloHabilitado, codigo)
    if m is None:
        raise ValueError(f"Módulo desconocido: {codigo}")
    if m.habilitado != valor:
        m.habilitado = valor
    s.flush()
