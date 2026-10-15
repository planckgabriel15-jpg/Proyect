"""Catálogos editables por el jefe (UNIDAD 6, etapas 5 y 14: terminología única y códigos de ocurrencias).

- Nada se borra: lo que no se usa se desactiva (los registros viejos siguen apuntando al código).
- El código no cambia una vez creado; la descripción sí (la auditoría guarda el texto anterior).
- Un modo de falla tiene que aplicar al menos a un tipo de componente; una causa o un síntoma sin tipos
  aplica a todos (D-019).
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import Categoria6P, OrigenDato, TipoCatalogo
from circularis_rel.datos.modelos import Catalogo, CatalogoAplica, MotivoParada

PATRON = re.compile(r"^[A-Z0-9][A-Z0-9_\-]{1,59}$")


class ErrorCatalogo(ValueError):
    pass


def _codigo(codigo: str) -> str:
    c = (codigo or "").strip().upper().replace(" ", "_")
    if not PATRON.match(c):
        raise ErrorCatalogo(f"Código inválido '{codigo}': solo mayúsculas, números, '_' y '-' (2 a 60 caracteres)")
    return c


def guardar_item(s: Session, tipo: TipoCatalogo, codigo: str, descripcion: str, *, activo: bool = True,
                 tipos_aplica: list[int] | None = None) -> Catalogo:
    """Crea o actualiza un síntoma, modo o causa. `tipos_aplica` None no toca los tipos."""
    codigo = _codigo(codigo)
    descripcion = (descripcion or "").strip()
    if not descripcion:
        raise ErrorCatalogo("Falta la descripción")
    item = s.scalar(select(Catalogo).where(Catalogo.tipo == tipo, Catalogo.codigo == codigo))
    if item is None:
        item = Catalogo(tipo=tipo, codigo=codigo, descripcion=descripcion, activo=activo, origen=OrigenDato.JEFE)
        s.add(item)
        s.flush()
    else:
        if item.descripcion != descripcion:
            item.descripcion = descripcion
        if item.activo != activo:
            item.activo = activo
        if item.origen != OrigenDato.JEFE and item.origen != OrigenDato.DEMO:
            item.origen = OrigenDato.JEFE  # revisado por el jefe
    if tipos_aplica is not None:
        actuales = set(s.scalars(select(CatalogoAplica.id_tipo_componente).where(CatalogoAplica.id_catalogo == item.id)))
        nuevos = set(tipos_aplica)
        for t in actuales - nuevos:
            s.delete(s.get(CatalogoAplica, (item.id, t)))
        for t in nuevos - actuales:
            s.add(CatalogoAplica(id_catalogo=item.id, id_tipo_componente=t))
        s.flush()
    if tipo == TipoCatalogo.MODO and item.activo:
        n = len(s.scalars(select(CatalogoAplica.id_tipo_componente).where(CatalogoAplica.id_catalogo == item.id)).all())
        if n == 0:
            raise ErrorCatalogo(f"El modo '{codigo}' tiene que aplicar al menos a un tipo de componente")
    s.flush()
    return item


def guardar_motivo(s: Session, codigo: str, descripcion: str, *, cuenta_como_requerida: bool = True, es_falla: bool = False,
                   es_setup: bool = False, categoria_6p: Categoria6P | None = None, activo: bool = True,
                   orden: int | None = None) -> MotivoParada:
    codigo = _codigo(codigo)
    descripcion = (descripcion or "").strip()
    if not descripcion:
        raise ErrorCatalogo("Falta la descripción")
    m = s.scalar(select(MotivoParada).where(MotivoParada.codigo == codigo))
    valores = {"descripcion": descripcion, "cuenta_como_requerida": cuenta_como_requerida, "es_falla": es_falla,
               "es_setup": es_setup, "categoria_6p": categoria_6p, "activo": activo}
    if orden is not None:
        valores["orden"] = orden
    if m is None:
        m = MotivoParada(codigo=codigo, **valores)
        s.add(m)
    else:
        for k, v in valores.items():
            if getattr(m, k) != v:
                setattr(m, k, v)
    s.flush()
    return m
