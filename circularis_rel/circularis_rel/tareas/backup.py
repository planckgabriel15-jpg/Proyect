"""Backup diario, restauración y prueba mensual de restauración (Plan §10; PLAN_TECNICO §3.8).

- Usa la API de backup en línea de SQLite: es consistente aunque haya usuarios conectados.
- Cada backup = `circularis_AAAAMMDD_HHMM.db` + `fotos_AAAAMMDD_HHMM.zip`.
- Rotación: se conservan N diarios y el primero de cada mes durante M meses.
- Copia opcional a una carpeta externa (disco o carpeta sincronizada con Google Drive).
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

PREFIJO = "circularis_"


@dataclass
class ResultadoPrueba:
    fecha: str
    archivo: str
    integridad: str
    conteos_iguales: bool
    detalle: dict

    @property
    def ok(self) -> bool:
        return self.integridad == "ok" and self.conteos_iguales


def _ruta_sqlite(url: str) -> Path:
    if not url.startswith("sqlite:///"):
        raise ValueError("El backup automático es para SQLite; con PostgreSQL usar pg_dump")
    return Path(url.removeprefix("sqlite:///"))


def hacer_backup(url_db: str, dir_backups: Path, dir_fotos: Path | None = None, carpeta_externa: Path | None = None,
                 momento: datetime | None = None) -> Path:
    momento = momento or datetime.now()
    dir_backups.mkdir(parents=True, exist_ok=True)
    sello = momento.strftime("%Y%m%d_%H%M")
    destino = dir_backups / f"{PREFIJO}{sello}.db"
    origen = sqlite3.connect(_ruta_sqlite(url_db))
    copia = sqlite3.connect(destino)
    with copia:
        origen.backup(copia)
    copia.close()
    origen.close()
    archivos = [destino]
    if dir_fotos is not None and dir_fotos.exists():
        zip_fotos = dir_backups / f"fotos_{sello}.zip"
        with zipfile.ZipFile(zip_fotos, "w", zipfile.ZIP_DEFLATED) as z:
            for f in dir_fotos.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(dir_fotos))
        archivos.append(zip_fotos)
    if carpeta_externa is not None:
        carpeta_externa.mkdir(parents=True, exist_ok=True)
        for f in archivos:
            shutil.copy2(f, carpeta_externa / f.name)
    return destino


def rotar(dir_backups: Path, diarios: int, mensuales: int) -> list[Path]:
    """Conserva los últimos `diarios` backups y el primero de cada uno de los últimos `mensuales` meses."""
    backups = sorted(dir_backups.glob(f"{PREFIJO}*.db"))  # el nombre lleva AAAAMMDD_HHMM: orden = fecha
    conservar = set(backups[-diarios:]) if diarios > 0 else set()
    primeros_del_mes: dict[str, Path] = {}
    for b in backups:
        primeros_del_mes.setdefault(b.stem.removeprefix(PREFIJO)[:6], b)
    for mes in sorted(primeros_del_mes)[-mensuales:] if mensuales > 0 else []:
        conservar.add(primeros_del_mes[mes])
    borrados = []
    for b in backups:
        if b not in conservar:
            b.unlink()
            fotos = b.with_name(f"fotos_{b.stem.removeprefix(PREFIJO)}.zip")
            if fotos.exists():
                fotos.unlink()
            borrados.append(b)
    return borrados


def ultimo_backup(dir_backups: Path) -> Path | None:
    backups = sorted(dir_backups.glob(f"{PREFIJO}*.db"))
    return backups[-1] if backups else None


def restaurar(archivo: Path, url_destino: str, dir_fotos: Path | None = None) -> None:
    """Restaura un backup sobre la base de destino (hacer antes un backup de la actual)."""
    destino = _ruta_sqlite(url_destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    origen = sqlite3.connect(archivo)
    nueva = sqlite3.connect(destino)
    with nueva:
        origen.backup(nueva)
    nueva.close()
    origen.close()
    zip_fotos = archivo.with_name(f"fotos_{archivo.stem.removeprefix(PREFIJO)}.zip")
    if dir_fotos is not None and zip_fotos.exists():
        with zipfile.ZipFile(zip_fotos) as z:
            z.extractall(dir_fotos)


def _conteos(ruta: Path) -> dict[str, int]:
    con = sqlite3.connect(ruta)
    tablas = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    conteos = {t: con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tablas}
    con.close()
    return conteos


def probar_restauracion(dir_backups: Path) -> ResultadoPrueba:
    """Restaura el último backup en una carpeta temporal y verifica integridad y conteos contra el archivo."""
    archivo = ultimo_backup(dir_backups)
    if archivo is None:
        r = ResultadoPrueba(datetime.now().isoformat(timespec="seconds"), "", "sin backups", False, {})
    else:
        with tempfile.TemporaryDirectory() as tmp:
            prueba = Path(tmp) / "restaurada.db"
            restaurar(archivo, f"sqlite:///{prueba}")
            con = sqlite3.connect(prueba)
            integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
            con.close()
            originales, restaurados = _conteos(archivo), _conteos(prueba)
        r = ResultadoPrueba(datetime.now().isoformat(timespec="seconds"), archivo.name, integridad,
                            originales == restaurados, {"tablas": len(originales), "filas": sum(originales.values())})
    (dir_backups / "ultima_prueba_restauracion.json").parent.mkdir(parents=True, exist_ok=True)
    (dir_backups / "ultima_prueba_restauracion.json").write_text(
        json.dumps(r.__dict__ | {"ok": r.ok}, ensure_ascii=False, indent=1), encoding="utf-8")
    return r
