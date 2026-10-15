"""Alertas (Plan §7). Se registran en la tabla `alerta` (panel) y, si hay SMTP, también van por mail
(fase 3). Sin SMTP el sistema funciona igual: las alertas quedan solo en el panel."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.modelos import Alerta


def emitir(s: Session, tipo: str, severidad: str, mensaje: str, clave_dedup: str, *, id_activo: int | None = None,
           id_posicion: int | None = None, destinatarios: str | None = None) -> Alerta | None:
    """Crea la alerta si no hay otra abierta con la misma clave. Devuelve la nueva o None."""
    abierta = s.scalar(select(Alerta).where(Alerta.clave_dedup == clave_dedup, Alerta.resuelta_en.is_(None)))
    if abierta is not None:
        if abierta.mensaje != mensaje:
            abierta.mensaje = mensaje
        return None
    a = Alerta(tipo=tipo, severidad=severidad, mensaje=mensaje, clave_dedup=clave_dedup, id_activo=id_activo,
               id_posicion=id_posicion, destinatarios=destinatarios)
    s.add(a)
    s.flush()
    return a


def resolver(s: Session, clave_dedup: str) -> None:
    for a in s.scalars(select(Alerta).where(Alerta.clave_dedup == clave_dedup, Alerta.resuelta_en.is_(None))):
        a.resuelta_en = ahora()


def abiertas(s: Session, destinatario: str | None = None) -> list[Alerta]:
    consulta = select(Alerta).where(Alerta.resuelta_en.is_(None)).order_by(Alerta.creado_en.desc())
    if destinatario:
        consulta = consulta.where(Alerta.destinatarios.like(f"%{destinatario}%"))
    return list(s.scalars(consulta))
