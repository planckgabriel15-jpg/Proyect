"""Usuarios y contraseñas (P-02, P-12).

- Contraseñas con bcrypt, compatibles con `streamlit-authenticator` (que solo se usa para el
  formulario y la cookie; ver `app/sesion.py`). Este archivo es el adaptador: si la librería
  cambia, se reemplaza la capa de la app, no los usuarios.
- Operarios: PIN de 4 a 6 dígitos (teclado numérico grande, uso con guantes).
  Encargado, jefe y gerencia: contraseña de al menos 8 caracteres.
"""

from __future__ import annotations

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import Rol
from circularis_rel.datos.modelos import Activo, Usuario, UsuarioActivo


class ClaveInvalida(ValueError):
    pass


def validar_clave(rol: Rol | str, clave: str) -> None:
    rol = Rol(rol)
    if rol == Rol.OPERARIO:
        if not (clave.isdigit() and 4 <= len(clave) <= 6):
            raise ClaveInvalida("El PIN del operario tiene que tener entre 4 y 6 números")
    elif len(clave) < 8:
        raise ClaveInvalida("La contraseña tiene que tener al menos 8 caracteres")


def hashear(clave: str) -> str:
    return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verificar(clave: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(clave.encode("utf-8"), hash_guardado.encode("ascii"))
    except ValueError:
        return False


def crear_usuario(s: Session, usuario: str, nombre: str, rol: Rol | str, clave: str,
                  email: str | None = None, maquinas: list[str] | None = None) -> Usuario:
    usuario = usuario.strip().lower()
    if not usuario or not usuario.replace(".", "").replace("_", "").isalnum():
        raise ValueError("El usuario solo puede tener letras, números, punto y guion bajo")
    if s.scalar(select(Usuario).where(Usuario.usuario == usuario)) is not None:
        raise ValueError(f"Ya existe el usuario '{usuario}'")
    validar_clave(rol, clave)
    u = Usuario(usuario=usuario, nombre=nombre.strip(), rol=Rol(rol), hash_password=hashear(clave), email=email)
    s.add(u)
    s.flush()
    asignar_maquinas(s, u, maquinas or [])
    return u


def asignar_maquinas(s: Session, u: Usuario, codigos: list[str]) -> None:
    ids = []
    for codigo in codigos:
        a = s.scalar(select(Activo).where(Activo.codigo == codigo))
        if a is None:
            raise ValueError(f"No existe la máquina '{codigo}'")
        ids.append(a.id)
    actuales = {ua.id_activo: ua for ua in s.scalars(select(UsuarioActivo).where(UsuarioActivo.id_usuario == u.id))}
    for id_activo, ua in actuales.items():
        if id_activo not in ids:
            s.delete(ua)
    for id_activo in ids:
        if id_activo not in actuales:
            s.add(UsuarioActivo(id_usuario=u.id, id_activo=id_activo))


def cambiar_clave(s: Session, u: Usuario, clave: str) -> None:
    validar_clave(u.rol, clave)
    u.hash_password = hashear(clave)


def autenticar(s: Session, usuario: str, clave: str) -> Usuario | None:
    u = s.scalar(select(Usuario).where(Usuario.usuario == usuario.strip().lower(), Usuario.activo.is_(True)))
    if u is None or not verificar(clave, u.hash_password):
        return None
    return u


def credenciales(s: Session) -> dict:
    """Diccionario en el formato de `streamlit-authenticator`, armado desde la base."""
    return {"usernames": {
        u.usuario: {"name": u.nombre, "password": u.hash_password, "email": u.email or "", "roles": [u.rol.value]}
        for u in s.scalars(select(Usuario).where(Usuario.activo.is_(True)))
    }}


def maquinas_de(s: Session, id_usuario: int) -> list[str]:
    return list(s.scalars(select(Activo.codigo).join(UsuarioActivo, UsuarioActivo.id_activo == Activo.id)
                          .where(UsuarioActivo.id_usuario == id_usuario).order_by(Activo.codigo)))


def fijar_activo(s: Session, id_usuario: int, activo: bool, id_actor: int | None = None) -> None:
    """Alta o baja lógica de un usuario. Nadie puede darse de baja a sí mismo."""
    if not activo and id_actor == id_usuario:
        raise ValueError("No podés darte de baja a vos mismo")
    u = s.get(Usuario, id_usuario)
    if u is None:
        raise ValueError("No existe el usuario")
    u.activo = activo
