"""Fotos de avisos y tarjetas: se reducen a 1.280 px (JPEG) y se guardan en datos/fotos/AAAA/MM/."""

from __future__ import annotations

import io
import uuid
from datetime import date
from pathlib import Path

from PIL import Image, ImageOps

LADO_MAXIMO = 1280
TAMANO_MAXIMO = 20 * 1024 * 1024


class FotoInvalida(ValueError):
    pass


def guardar(contenido: bytes, dir_fotos: Path, hoy: date | None = None) -> str:
    """Devuelve la ruta relativa a `dir_fotos`."""
    if len(contenido) > TAMANO_MAXIMO:
        raise FotoInvalida("La foto es demasiado grande (máximo 20 MB)")
    try:
        img = Image.open(io.BytesIO(contenido))
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception as e:  # PIL lanza varios tipos según el formato
        raise FotoInvalida("El archivo no es una imagen válida") from e
    img.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
    hoy = hoy or date.today()
    relativa = Path(f"{hoy:%Y}") / f"{hoy:%m}" / f"{uuid.uuid4().hex}.jpg"
    destino = dir_fotos / relativa
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, "JPEG", quality=82, optimize=True)
    return relativa.as_posix()
