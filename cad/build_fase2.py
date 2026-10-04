#!/usr/bin/env python3
"""Fase 2: galpón existente dibujado 1:1 en el espacio modelo de PLANOS_AGD-2026.

Salidas en Projects/VJN001/:
  dwg/PLANOS_AGD-2026.dxf      plantilla + zonas + galpón existente
  png/F2_*.png                 capturas del espacio modelo por zona, a la escala de su lámina
  F2_conteo_por_capa.md        cantidad de objetos por capa y por zona
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pf import config as C                       # noqa: E402
from pf import template as T, galpon as G        # noqa: E402
from pf.dib import rellenos_al_fondo             # noqa: E402
from pf.preview import render_modelo             # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / 'Projects' / 'VJN001'
DWG, PNG = OUT / 'dwg', OUT / 'png'

# (archivo, ventana del espacio modelo en mm, escala, título)
CAPTURAS = [
    ('F2_P_planta_1-125.png', (-3000, -39500, 26000, 3000), 125, 'Zona P — Planta general (PL-01) · 1:125'),
    ('F2_A_corte_AA_1-75.png', (-2000, 59200, 24700, 67000), 75,
     'Zona A — Corte A-A, s = 26,85 mirando al norte (CT-02; también DET-12·A a 1:100) · 1:75'),
    ('F2_B_corte_BB_1-125.png', (66000, 59200, 111000, 67000), 125,
     'Zona B — Corte B-B quebrado, mirando al oeste (CL-03) · 1:125'),
    ('F2_C_vista_CC_1-125.png', (118000, 59400, 144500, 67000), 125, 'Zona C — Vista C-C desde el exterior (CL-03) · 1:125'),
    ('F2_DET12_B_tabique_1-25.png', (-1000, 359000, 1000, 362400), 25, 'DET-12·B — Tabique H° + machimbre · 1:25'),
    ('F2_DET12_C_muro_1-50.png', (4800, 359200, 7400, 364300), 50, 'DET-12·C — Muro perimetral · 1:50'),
    ('F2_DET12_E_suplemento_1-200.png', (11000, 359600, 35400, 364400), 200,
     'DET-12·E — Corte del suplemento T1 a T4 · 1:200'),
    ('F2_DET12_F_dado_existente_1-20.png', (46900, 363200, 48900, 364100), 20,
     'DET-12·F — Suplemento en la zona del dado de L1 (parte existente) · 1:20'),
]


def zona_de(e):
    """Nombre de la zona del espacio modelo que contiene el objeto."""
    try:
        bb = e.dxf.get('start') or None
        if bb is None:
            pts = list(e.get_points('xy')) if e.dxftype() == 'LWPOLYLINE' else None
            if pts:
                bb = pts[0]
            elif e.dxftype() == 'HATCH':
                bb = e.paths[0].vertices[0] if hasattr(e.paths[0], 'vertices') else None
            elif e.dxftype() in ('TEXT', 'CIRCLE'):
                bb = e.dxf.get('insert') or e.dxf.get('center')
        x, y = bb[0], bb[1]
    except Exception:
        return '?'
    for n, (_, _, (x0, y0, x1, y1), _) in C.ZONAS.items():
        if x0 <= x <= x1 and y0 <= y <= y1:
            return n
    return '?'


def main():
    DWG.mkdir(parents=True, exist_ok=True)
    PNG.mkdir(parents=True, exist_ok=True)
    doc = T.crear_documento(con_zonas=True)
    doc.layouts.rename('A3-IRAM', 'PL-00')
    G.dibujar(doc)
    msp = doc.modelspace()
    rellenos_al_fondo(msp)
    a = doc.audit()
    assert not a.errors, [e.message for e in a.errors]
    doc.saveas(DWG / 'PLANOS_AGD-2026.dxf')
    # conteo por capa y zona
    cnt = Counter((zona_de(e), e.dxf.layer, e.dxftype()) for e in msp)
    en_capa0 = sum(1 for e in msp if e.dxf.layer == '0')
    L = ['# Fase 2: objetos del galpón existente por zona y capa', '',
         f'Total en el espacio modelo: {len(msp)} objetos. En capa 0: {en_capa0}.', '',
         '| Zona | Capa | Tipo | Cantidad |', '|---|---|---|---|']
    for (z, l, t), n in sorted(cnt.items()):
        L.append(f'| {z} | {l} | {t} | {n} |')
    (OUT / 'F2_conteo_por_capa.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    for archivo, ventana, esc, tit in CAPTURAS:
        render_modelo(doc, ventana, esc, PNG / archivo, dpi=200, titulo=tit)
    print('Fase 2 lista:', len(msp), 'objetos; capa 0:', en_capa0)


if __name__ == '__main__':
    main()
