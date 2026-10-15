"""Etiquetas QR plastificables por máquina (Plan §10).

El QR codifica `http://<ip fija>:8501/?maq=AGR-001`: la cámara del celular lo abre sin app y la
página deja la máquina preseleccionada.
"""

from __future__ import annotations

import io
from urllib.parse import quote

import segno

from circularis_rel.servicios.pdf import PDF

COLUMNAS, FILAS = 2, 4
ANCHO, ALTO = 93.0, 68.0


def url_maquina(url_base: str, codigo: str) -> str:
    return f"{url_base.rstrip('/')}/?maq={quote(codigo)}"


def png_qr(texto: str, escala: int = 10) -> bytes:
    buffer = io.BytesIO()
    segno.make(texto, error="m").save(buffer, kind="png", scale=escala, border=2)
    return buffer.getvalue()


def etiquetas_pdf(maquinas: list[tuple[str, str]], url_base: str) -> bytes:
    """maquinas = [(código, nombre)]. A4 con 8 etiquetas de 93 × 68 mm."""
    pdf = PDF(titulo="", referencia=None)
    pdf.set_auto_page_break(auto=False)
    for i, (codigo, nombre) in enumerate(maquinas):
        if i % (COLUMNAS * FILAS) == 0:
            pdf.add_page()
        pos = i % (COLUMNAS * FILAS)
        x = 12 + (pos % COLUMNAS) * ANCHO
        y = 12 + (pos // COLUMNAS) * ALTO
        pdf.set_draw_color(150, 150, 150)
        pdf.rect(x, y, ANCHO - 2, ALTO - 2)
        lado_qr = 52
        pdf.image(io.BytesIO(png_qr(url_maquina(url_base, codigo))), x=x + 2, y=y + 6, w=lado_qr, h=lado_qr)
        x_texto, ancho_texto = x + lado_qr + 4, ANCHO - lado_qr - 10
        tamano = 20
        pdf.set_font("DejaVu", "B", tamano)
        while pdf.get_string_width(codigo) > ancho_texto and tamano > 8:
            tamano -= 1
            pdf.set_font("DejaVu", "B", tamano)
        pdf.set_xy(x_texto, y + 8)
        pdf.cell(ancho_texto, 10, codigo, align="L")
        pdf.set_xy(x_texto, y + 20)
        pdf.set_font("DejaVu", "", 9)
        pdf.multi_cell(ancho_texto, 4.5, nombre[:60], align="L")
        pdf.set_xy(x_texto, y + 42)
        pdf.set_font("DejaVu", "B", 7.5)
        pdf.multi_cell(ancho_texto, 3.6, "Circularis\nEscaneá para reportar una falla o cargar el parte de turno", align="L")
    return pdf.a_bytes()
