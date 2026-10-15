"""Alertas (Plan §7). Se registran en la tabla `alerta` (panel) y, si hay SMTP, también van por mail
(fase 3). Sin SMTP el sistema funciona igual: las alertas quedan solo en el panel."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.db import ahora
from circularis_rel.datos.modelos import Activo, Alerta, EstadoComponente, PosicionComponente


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


ORDEN_CONFIANZA = ["GRIS", "BAJA", "MEDIA", "ALTA"]


def es_firme(confianza: str, minima: str) -> bool:
    return ORDEN_CONFIANZA.index(confianza) >= ORDEN_CONFIANZA.index(minima)


def actualizar_riesgo(s: Session, hoy: date) -> dict[str, int]:
    """Alertas por componente en rojo (UNIDAD 6, etapa 16: las alertas firmes se habilitan por componente
    recién con confianza media o alta). Con menos confianza la alerta es "orientativa": queda en el panel
    pero no se manda por mail. Se resuelven solas cuando el componente sale del rojo (D-048)."""
    from circularis_rel.servicios import parametros as P

    minima = P.obtener(s, "alertas.confianza_firme") or "MEDIA"
    conteo = {"firmes": 0, "orientativas": 0, "resueltas": 0}
    for pos, codigo in s.execute(select(PosicionComponente, Activo.codigo).join(Activo, Activo.id == PosicionComponente.id_activo)
                                 .where(PosicionComponente.activa.is_(True))):
        e = s.scalar(select(EstadoComponente).where(EstadoComponente.id_posicion == pos.id, EstadoComponente.fecha <= hoy)
                     .order_by(EstadoComponente.fecha.desc()).limit(1))
        firme, orientativa = f"riesgo:{pos.id}", f"riesgo_orientativo:{pos.id}"
        motivos = [m for m in (e.motivos or []) if not m.startswith("Intervalo:")] if e else []
        en_riesgo = e is not None and e.semaforo.value == "ROJO" and motivos != ["OT correctiva abierta"]
        if not en_riesgo:
            for clave in (firme, orientativa):
                if s.scalar(select(Alerta.id).where(Alerta.clave_dedup == clave, Alerta.resuelta_en.is_(None))):
                    resolver(s, clave)
                    conteo["resueltas"] += 1
            continue
        texto = f"{codigo} · {pos.codigo}: " + "; ".join(motivos)
        if es_firme(e.confianza.value, minima):
            resolver(s, orientativa)
            emitir(s, "RIESGO", "alta", texto, firme, id_activo=pos.id_activo, id_posicion=pos.id, destinatarios="JEFE")
            conteo["firmes"] += 1
        else:
            resolver(s, firme)
            emitir(s, "RIESGO_ORIENTATIVO", "baja", texto + f" (confianza {e.confianza.value.lower()}: orientativa)",
                   orientativa, id_activo=pos.id_activo, id_posicion=pos.id)
            conteo["orientativas"] += 1
    s.flush()
    return conteo
