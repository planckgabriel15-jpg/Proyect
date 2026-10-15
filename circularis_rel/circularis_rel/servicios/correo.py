"""Correo saliente (opcional). Sin SMTP configurado no se manda nada y las alertas quedan en el panel (Plan §7).

- Inmediatas: alertas firmes de riesgo (cambio a rojo con confianza suficiente), predictivo sobre el límite de
  acción y fallas del backup.
- Resumen diario: el resto de las alertas abiertas que todavía no se mandaron (partes faltantes, stock, edad sobre
  el intervalo, eventos sin validar).
- Las alertas orientativas nunca se mandan (D-048).
"""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.config import Config
from circularis_rel.datos.db import ahora
from circularis_rel.datos.enums import Rol
from circularis_rel.datos.modelos import Alerta, Usuario

INMEDIATAS = {"RIESGO", "BACKUP"}
NUNCA = {"RIESGO_ORIENTATIVO"}


def enviar(cfg: Config, para: list[str], asunto: str, cuerpo: str, adjuntos: list[tuple[str, bytes, str]] | None = None) -> bool:
    """Manda un mail. Devuelve False (sin error) si no hay SMTP o no hay destinatarios."""
    if not cfg.smtp_configurado or not para:
        return False
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = cfg.smtp_remitente, ", ".join(sorted(set(para))), asunto
    m.set_content(cuerpo)
    for nombre, datos, tipo in adjuntos or []:
        principal, sub = tipo.split("/", 1)
        m.add_attachment(datos, maintype=principal, subtype=sub, filename=nombre)
    contexto = ssl.create_default_context()
    if cfg.smtp_puerto == 465:
        with smtplib.SMTP_SSL(cfg.smtp_servidor, cfg.smtp_puerto, context=contexto, timeout=30) as smtp:
            if cfg.smtp_usuario:
                smtp.login(cfg.smtp_usuario, cfg.smtp_clave)
            smtp.send_message(m)
    else:
        with smtplib.SMTP(cfg.smtp_servidor, cfg.smtp_puerto, timeout=30) as smtp:
            smtp.starttls(context=contexto)
            if cfg.smtp_usuario:
                smtp.login(cfg.smtp_usuario, cfg.smtp_clave)
            smtp.send_message(m)
    return True


def destinatarios(s: Session, roles: str | None) -> list[str]:
    """Mails de los usuarios activos de esos roles ("JEFE,ENCARGADO"); sin roles, el jefe."""
    lista = [Rol(r.strip()) for r in (roles or "JEFE").split(",") if r.strip()]
    return [u.email for u in s.scalars(select(Usuario).where(Usuario.activo.is_(True), Usuario.rol.in_(lista),
                                                             Usuario.email.is_not(None))) if u.email]


def pendientes(s: Session, inmediatas: bool) -> list[Alerta]:
    tipos = select(Alerta).where(Alerta.resuelta_en.is_(None), Alerta.enviada_mail_en.is_(None), Alerta.tipo.not_in(NUNCA))
    lista = list(s.scalars(tipos.order_by(Alerta.creado_en)))
    return [a for a in lista if (a.tipo in INMEDIATAS or (a.tipo == "PREDICTIVO" and a.severidad == "alta")) == inmediatas]


def enviar_alertas(s: Session, cfg: Config, inmediatas: bool) -> int:
    """Manda las alertas pendientes agrupadas por destinatarios y las marca como enviadas."""
    if not cfg.smtp_configurado:
        return 0
    por_grupo: dict[str, list[Alerta]] = {}
    for a in pendientes(s, inmediatas):
        por_grupo.setdefault(a.destinatarios or "JEFE", []).append(a)
    n = 0
    for roles, lista in por_grupo.items():
        para = destinatarios(s, roles)
        if not para:
            continue
        asunto = (f"Circularis: {lista[0].mensaje[:80]}" if len(lista) == 1
                  else f"Circularis: {len(lista)} alertas de mantenimiento")
        cuerpo = "\n".join(f"- [{a.severidad}] {a.mensaje}" for a in lista)
        cuerpo += "\n\nDetalle en el panel de Circularis. Este mensaje lo manda el sistema; no hace falta responderlo."
        if enviar(cfg, para, asunto, cuerpo):
            for a in lista:
                a.enviada_mail_en = ahora()
            n += len(lista)
    s.flush()
    return n
