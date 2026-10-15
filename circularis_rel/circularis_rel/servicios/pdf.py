"""Base para los PDF (fpdf2, sin dependencias del sistema: funciona en Windows nativo, D-022).

Usa la tipografía DejaVu que viene con matplotlib, así no hace falta internet ni instalar
fuentes, y se pueden escribir todos los caracteres (–, ≥, ñ, °…).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
from fpdf import FPDF

_FUENTES = Path(matplotlib.get_data_path()) / "fonts" / "ttf"


class PDF(FPDF):
    def __init__(self, titulo: str, referencia: str | None = None, orientacion: str = "P") -> None:
        super().__init__(orientation=orientacion, unit="mm", format="A4")
        self.add_font("DejaVu", "", str(_FUENTES / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(_FUENTES / "DejaVuSans-Bold.ttf"))
        self.add_font("DejaVu", "I", str(_FUENTES / "DejaVuSans-Oblique.ttf"))
        self.titulo = titulo
        self.referencia = referencia
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(12, 12, 12)

    def header(self) -> None:
        if not self.titulo:
            return
        self.set_font("DejaVu", "B", 12)
        self.cell(0, 7, self.titulo, align="L")
        if self.referencia:
            self.set_font("DejaVu", "", 9)
            self.cell(0, 7, f"Ref.: {self.referencia}", align="R")
        self.ln(9)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("DejaVu", "I", 7)
        self.cell(0, 5, f"Circularis · Sistema de confiabilidad · página {self.page_no()}", align="C")

    def campo(self, etiqueta: str, valor, ancho_etiqueta: float = 64) -> None:
        self.set_font("DejaVu", "B", 9)
        self.cell(ancho_etiqueta, 6, etiqueta, border=1)
        self.set_font("DejaVu", "", 9)
        texto = "—" if valor in (None, "") else str(valor)
        self.multi_cell(0, 6, texto, border=1, new_x="LMARGIN", new_y="NEXT")

    def subtitulo(self, texto: str) -> None:
        self.ln(3)
        self.set_font("DejaVu", "B", 10)
        self.set_fill_color(220, 220, 220)
        self.cell(0, 7, texto, border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    def tabla(self, encabezados: list[str], anchos: list[float], filas: list[list], vacias: int = 0) -> None:
        self.set_font("DejaVu", "B", 8)
        for e, w in zip(encabezados, anchos, strict=True):
            self.cell(w, 6, e, border=1, align="C")
        self.ln()
        self.set_font("DejaVu", "", 8)
        for fila in filas:
            for v, w in zip(fila, anchos, strict=True):
                self.cell(w, 6, self.recortar("" if v is None else str(v), w - 1.5), border=1)
            self.ln()
        for _ in range(vacias):
            for w in anchos:
                self.cell(w, 6, "", border=1)
            self.ln()

    def recortar(self, texto: str, ancho: float) -> str:
        """Recorta el texto con "…" para que entre en el ancho de la celda."""
        if self.get_string_width(texto) <= ancho:
            return texto
        while texto and self.get_string_width(texto + "…") > ancho:
            texto = texto[:-1]
        return texto + "…"

    def a_bytes(self) -> bytes:
        return bytes(self.output())
