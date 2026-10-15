"""Configuración de la instalación (rutas, base de datos, zona horaria).

Se lee de variables de entorno o de un archivo `.env` en la carpeta del proyecto.
Nunca hay credenciales en el código: el SMTP y la clave de la cookie van en `.env`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


def _leer_env(ruta: Path) -> dict[str, str]:
    valores: dict[str, str] = {}
    if not ruta.exists():
        return valores
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valores[clave.strip()] = valor.strip().strip('"').strip("'")
    return valores


@dataclass(frozen=True)
class Config:
    dir_datos: Path
    url_db: str
    zona_horaria: ZoneInfo
    clave_cookie: str
    nombre_cookie: str
    dias_cookie: int
    url_base: str  # dirección fija de la mini PC, para los QR
    smtp_servidor: str = ""
    smtp_puerto: int = 587
    smtp_usuario: str = ""
    smtp_clave: str = ""
    smtp_remitente: str = ""

    @property
    def smtp_configurado(self) -> bool:
        return bool(self.smtp_servidor and self.smtp_remitente)

    @property
    def dir_fotos(self) -> Path:
        return self.dir_datos / "fotos"

    @property
    def dir_backups(self) -> Path:
        return self.dir_datos / "backups"

    @property
    def dir_exportaciones(self) -> Path:
        return self.dir_datos / "exportaciones"

    @property
    def dir_reportes(self) -> Path:
        return self.dir_datos / "reportes"


def cargar_config() -> Config:
    env = {**_leer_env(RAIZ_PROYECTO / ".env"), **os.environ}
    dir_datos = Path(env.get("CIRCULARIS_DATA_DIR", RAIZ_PROYECTO / "datos")).resolve()
    url_db = env.get("CIRCULARIS_DB_URL", f"sqlite:///{dir_datos / 'circularis.db'}")
    return Config(
        dir_datos=dir_datos,
        url_db=url_db,
        zona_horaria=ZoneInfo(env.get("CIRCULARIS_TZ", "America/Argentina/Cordoba")),
        clave_cookie=env.get("CIRCULARIS_CLAVE_COOKIE", "cambiar-esta-clave-en-el-archivo-env"),
        nombre_cookie=env.get("CIRCULARIS_NOMBRE_COOKIE", "circularis_sesion"),
        dias_cookie=int(env.get("CIRCULARIS_DIAS_COOKIE", "30")),
        url_base=env.get("CIRCULARIS_URL_BASE", "http://192.168.0.10:8501"),
        smtp_servidor=env.get("SMTP_SERVIDOR", ""),
        smtp_puerto=int(env.get("SMTP_PUERTO") or 587),
        smtp_usuario=env.get("SMTP_USUARIO", ""),
        smtp_clave=env.get("SMTP_CLAVE", ""),
        smtp_remitente=env.get("SMTP_REMITENTE", ""),
    )
