#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera las 14 láminas Rev E (PNG + PDF en ./out) y las une en un solo PDF A3.

Uso:  python3 build_all.py
Requisitos: python ≥ 3.9, matplotlib, numpy, shapely, pillow, pypdf

Estructura del código
---------------------
  lib.py     Marco del dibujo: hoja A3, rótulo, vistas a escala (View), cotas, niveles,
             referencias, globos, tablas, hormigón, terreno, cortes y el verificador
             automático de superposiciones (textos ↔ textos, textos ↔ líneas, fuera de hoja).
  data.py    Datos de proyecto Rev E: niveles, ejes en planta, compuertas, bridas y
             resultados de cálculo. Es la única fuente de cotas compartidas entre láminas.
  iso.py     Mini motor axonométrico con z-buffer (usado por ISO-13).
  s00.py … s13.py, spl01.py, sct02.py, scl03.py
             Una función build(out) por lámina. Cada vista se dibuja en coordenadas reales
             (mm del modelo) con View(sh, ox, oy, escala); las cotas y referencias se
             verifican al guardar ("[CÓDIGO] N problemas").
"""
import importlib
import os
import sys

ORDEN = [('s00', 'PL-00'), ('spl01', 'PL-01'), ('sct02', 'CT-02'), ('scl03', 'CL-03'), ('s04', 'DET-04'),
         ('s05', 'DET-05'), ('s06', 'DET-06'), ('s07', 'DET-07'), ('s08', 'DET-08'), ('s09', 'DET-09'),
         ('s10', 'DET-10'), ('s11', 'DET-11'), ('s12', 'DET-12'), ('s13', 'ISO-13')]


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs('out', exist_ok=True)
    total = 0
    for mod, code in ORDEN:
        m = importlib.import_module(mod)
        n = m.build(f'out/{code}')
        total += len(n) if isinstance(n, (list, tuple)) else (n or 0)
    from pypdf import PdfWriter
    w = PdfWriter()
    for _, code in ORDEN:
        w.append(f'out/{code}.pdf')
    w.write('out/Planos_RevE_Redler_AGD.pdf')
    print(f'Listo: out/Planos_RevE_Redler_AGD.pdf · problemas de superposición: {total}')
    return 0 if total == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
