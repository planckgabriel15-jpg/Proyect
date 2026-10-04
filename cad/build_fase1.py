#!/usr/bin/env python3
"""Fase 1: plantilla PF-IRAM-A3, base del dibujo PLANOS_AGD-2026, CTB, LISP y capturas.

Salidas en Projects/VJN001/:
  dwg/PF-IRAM-A3.dxf          plantilla (se guarda como .dwt con PF-GUARDAR-DWT)
  dwg/PLANOS_AGD-2026.dxf     base del legajo: plantilla + zonas y UCS del espacio modelo
  dwg/PF-IRAM-MONO.ctb        tabla de estilos de trazado monocroma
  dwg/PF-POST.lsp             post-proceso en AutoCAD
  png/F1_*.png                capturas para aprobación
  F1_capas_estilos_bloques.md listado generado desde el DXF
"""
import shutil
import sys
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

sys.path.insert(0, str(Path(__file__).parent))
from pf import config as C                      # noqa: E402
from pf import template as T                    # noqa: E402
from pf.ctb import crear_ctb                    # noqa: E402
from pf.preview import render_layout            # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / 'Projects' / 'VJN001'
DWG, PNG = OUT / 'dwg', OUT / 'png'


def demo_lamina(doc):
    """Layout de muestra (solo para la captura): rótulo de PL-01 y lista de materiales apilada."""
    lay = doc.layouts.new('MUESTRA-PL-01')
    T.configurar_layout(lay)
    T.dibujar_formato(lay, T.atributos_rotulo(
        'PL-01', 'Planta general de distribución',
        'Columnas intermedias a 4,00 m entre ejes · L2 simétrica respecto de X = 11,35 · galpón sin producto',
        '1:125', 2))
    x1, y0 = C.MARCO[2], C.MARCO[1] + T.ROT_ALTO
    lay.add_blockref('LISTA-MATERIALES', (x1, y0), dxfattribs={'layer': 'G-ROTULO'})
    filas = [  # demostración de formato (valores de DET-07, peso = volumen × 7850 kg/m³)
        ('1', '12', 'Placa de apoyo', 'Acero F-24', 'Pl. 1000×180×18', '25,43', '6 por línea'),
        ('2', '48', 'Anclaje químico', 'cal. 8.8', 'M16 · hef 125', '—', 'resina epoxi'),
        ('3', '24', 'Placa base', 'F-24', 'Pl. 1000×80×18', '11,30', '2 por tramo'),
    ]
    for k, f in enumerate(filas):
        r = lay.add_blockref('LM-FILA', (x1, y0 + T.LM_H_ENC + k * T.LM_H_FILA), dxfattribs={'layer': 'G-ROTULO'})
        r.add_auto_attribs(dict(zip(['POS', 'CANT', 'DENOM', 'MAT', 'DIM', 'PESO', 'OBS'], f)))
    return lay


def catalogo(doc):
    """Layout de muestra con todos los bloques de anotación (solo para la captura)."""
    lay = doc.layouts.new('CATALOGO')
    T.configurar_layout(lay)
    x0, y0, x1, y1 = C.MARCO
    lay.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': 'G-MARCO'})

    def rot(texto, x, y):
        t = lay.add_text(texto, height=C.H_TXT, dxfattribs={'layer': 'AN-TEXTOS', 'style': C.ST_N})
        t.set_placement((x, y), align=TA.TOP_CENTER)

    items = [
        ('NIVEL-CORTE', {'COTA': '+3,90', 'DESC': 'tope machimbre'}, 'NIVEL-CORTE'),
        ('NIVEL-CORTE-IZQ', {'COTA': '−3,40', 'DESC': 'piso de fosa'}, 'NIVEL-CORTE-IZQ'),
        ('NIVEL-PLANTA', {'COTA': '±0,00'}, 'NIVEL-PLANTA'),
        ('CORTE', {'LETRA': 'A', 'LAMINA': 'CT-02'}, 'CORTE'),
        ('LLAMADA-DETALLE', {'DETALLE': 'D5', 'LAMINA': 'DET-05'}, 'LLAMADA-DETALLE'),
        ('NORTE', {'N': 'N'}, 'NORTE'),
        ('EJE', {'EJE': 'L1'}, 'EJE'),
        ('FLUJO', {}, 'FLUJO (rojo)'),
        ('PASO-RECORRIDO', {'N': '4'}, 'PASO-RECORRIDO (rojo)'),
        ('GLOBO', {'N': '12'}, 'GLOBO (de IRAM-GLOBO)'),
    ]
    cols, dx, dy = 4, 92, 52
    desplaz = {'NIVEL-CORTE': -25, 'NIVEL-CORTE-IZQ': 25}
    for k, (blk, atts, nombre) in enumerate(items):
        cx = x0 + 50 + (k % cols) * dx
        cy = y1 - 32 - (k // cols) * dy
        r = lay.add_blockref(blk, (cx + desplaz.get(blk, 0), cy), dxfattribs={'layer': 'AN-REFERENCIAS'})
        if atts:
            r.add_auto_attribs(atts)
        rot(nombre, cx, cy - 26)
    # título de vista (ancho completo)
    T.titulo_vista(lay, (x0 + 15, y0 + 105), 'A', 'CORTE LONGITUDINAL POR EL EJE DE LA FOSA', 'Esc. 1:25')
    rot('TITULO-VISTA (letra — título con doble subrayado — escala)', x0 + 110, y0 + 96)
    # líneas de muestra de cada tipo
    yy = y0 + 70
    muestras = [('G-EJES', 'Eje (ACAD_ISO04W100, 0,18)'), ('AN-OCULTO', 'Oculto (ACAD_ISO02W100, 0,25)'),
                ('AN-CORTES-LLAMADAS', 'Línea de corte (ACAD_ISO04W100, 0,18)'),
                ('NU-REDLER-CONDUCTO', 'Nuevo cortado / visto (0,50)'), ('NU-REDLER-MECANICO', 'Nuevo (0,35)'),
                ('EX-HORMIGON-CORTE', 'Existente cortado (0,35, gris)'), ('EX-HORMIGON-VISTA', 'Existente en vista (0,25, gris)'),
                ('AN-COTAS', 'Cotas y referencias (0,18)')]
    for k, (capa, txt) in enumerate(muestras):
        xa = x0 + 15 + (k % 2) * 185
        ya = yy - (k // 2) * 12
        lay.add_line((xa, ya), (xa + 90, ya), dxfattribs={'layer': capa})
        t = lay.add_text(txt, height=C.H_TXT, dxfattribs={'layer': 'AN-TEXTOS', 'style': C.ST_N})
        t.set_placement((xa + 95, ya), align=TA.MIDDLE_LEFT)
    return lay


def listado_md(doc, ruta):
    L = ['# Fase 1: capas, estilos y bloques de la plantilla PF-IRAM-A3', '',
         'Listado generado automáticamente desde `PF-IRAM-A3.dxf`.', '',
         '## Capas', '', '| Capa | Color | Espesor (mm) | Tipo de línea | Imprime | Contenido |',
         '|---|---|---|---|---|---|']
    for lay in doc.layers:
        n = lay.dxf.name
        if n in ('0', 'Defpoints'):
            continue
        lw = lay.dxf.lineweight
        L.append(f'| {n} | {lay.dxf.color} | {"—" if lw < 0 else f"{lw / 100:.2f}".replace(".", ",")} | '
                 f'{lay.dxf.linetype} | {"Sí" if lay.dxf.plot else "No"} | {lay.description} |')
    L += ['', '## Tipos de línea', '', '| Nombre | Patrón (mm, a escala de papel) |', '|---|---|']
    for nombre, desc, pat in C.TIPOS_LINEA:
        L.append(f'| {nombre} | {", ".join(str(p).replace(".", ",") for p in pat[1:])} ({desc}) |')
    L += ['', '## Estilos de texto', '', '| Estilo | Fuente | Ancho | Inclinación | Anotativo | Uso |',
          '|---|---|---|---|---|---|',
          f'| {C.ST_ANNO} | {C.FUENTE_TTF} | 1,0 | 0° | Sí | textos, cotas y referencias en el espacio modelo |',
          f'| {C.ST_N} | {C.FUENTE_TTF} | 1,0 | 0° | No | contenido de bloques y espacio papel |',
          f'| {C.ST_NEG} | {C.FUENTE_TTF} (negrita) | 1,0 | 0° | No | encabezados de tabla, títulos de vista y del rótulo |',
          '', 'Alturas en papel: 2,5 (cotas, referencias, tablas) · 3,5 (títulos de vista) · 5 (título del rótulo) · '
          '7 (código de lámina). Mínimo 2,5 mm en todo el legajo.',
          '', '## Estilos de cota (anotativos)', '',
          '| Estilo | Unidad mostrada | Decimales | Extremo | Texto | DIMEXO / DIMEXE / DIMGAP / DIMDLI |',
          '|---|---|---|---|---|---|',
          '| IRAM-OBRA | m (DIMLFAC 0,001) | 2 | trazo oblicuo 2 mm | 2,5 sobre la línea, alineado | 1,5 / 2 / 1 / 7 |',
          '| IRAM-OBRA-3 | m (DIMLFAC 0,001) | 3 | trazo oblicuo 2 mm | ídem | ídem |',
          '| IRAM-MEC | mm | 0 | flecha cerrada llena 2,5 mm | ídem | ídem |',
          '', 'Separador decimal: coma (DIMDSEP). Ángulos en grados enteros. Texto que no entra: afuera con '
          'leader (DIMATFIT 3, DIMTMOVE 1).',
          '', '## Estilos de multileader (anotativos)', '',
          '| Estilo | Contenido | Texto | Extremo | Quiebre |', '|---|---|---|---|---|',
          '| IRAM-REF | MTEXT | IRAM 2,5 | punto de 1 mm | horizontal de 3 mm |',
          '| IRAM-GLOBO | bloque GLOBO (Ø 6 con número) | 2,5 | punto de 1 mm | sin quiebre |',
          '', '## Estilo de tabla', '', 'IRAM-TABLA: texto 2,5 mm (IRAM-N), encabezado 2,5 mm en negrita '
          '(IRAM-NEGRITA), márgenes de celda 1 mm, borde exterior 0,35 e interiores 0,18. '
          'Lo crea `PF-ESTILO-TABLA` en AutoCAD porque el DXF no puede definir estilos de tabla.',
          '', '## Rayados (IRAM 4502-50)', '',
          '| Material | Patrón | Capa |', '|---|---|---|',
          '| Hormigón | AR-CONC | AN-RAYADO-EX / AN-RAYADO-NU |',
          '| Acero cortado | ANSI31, 2 mm en papel; relleno negro si la chapa mide menos de 2 mm en papel | AN-RAYADO-NU |',
          '| Madera | AR-RSHKE | AN-RAYADO-EX |', '| Terreno | EARTH | AN-RAYADO-EX |',
          '| Rejilla | NET | AN-RAYADO-NU |', '| Material a granel | AR-SAND | AN-RAYADO-NU |',
          '', '## Bloques', '', '| Bloque | Anotativo | Atributos |', '|---|---|---|']
    for blk in doc.blocks:
        n = blk.name
        if n.startswith('*') or n.startswith('_'):
            continue
        anot = 'Sí' if blk.block_record.has_xdata(T.ANNO_APP) else 'No'
        tags = ', '.join(a.dxf.tag for a in blk.query('ATTDEF'))
        L.append(f'| {n} | {anot} | {tags or "—"} |')
    L += ['', '## Zonas del espacio modelo (§6.3)', '', '| Zona | UCS | Origen (mm) | Eje X | Contenido |',
          '|---|---|---|---|---|']
    for n, (o, xa, rect, desc) in C.ZONAS.items():
        L.append(f'| {n} | UCS-{n} | ({o[0]}, {o[1]}) | ({xa[0]}, {xa[1]}) | {desc} |')
    Path(ruta).write_text('\n'.join(L) + '\n', encoding='utf-8')


def main():
    DWG.mkdir(parents=True, exist_ok=True)
    PNG.mkdir(parents=True, exist_ok=True)
    # plantilla
    tpl = T.crear_documento(con_zonas=False)
    a = tpl.audit()
    assert not a.errors, a.errors
    tpl.saveas(DWG / 'PF-IRAM-A3.dxf')
    # base del legajo
    base = T.crear_documento(con_zonas=True)
    base.layouts.rename('A3-IRAM', 'PL-00')
    a = base.audit()
    assert not a.errors, a.errors
    base.saveas(DWG / 'PLANOS_AGD-2026.dxf')
    crear_ctb(DWG / C.CTB)
    shutil.copy(Path(__file__).parent / 'lisp' / 'PF-POST.lsp', DWG / 'PF-POST.lsp')
    listado_md(tpl, OUT / 'F1_capas_estilos_bloques.md')
    # capturas
    demo = T.crear_documento(con_zonas=False)
    demo_lamina(demo)
    catalogo(demo)
    render_layout(demo, 'MUESTRA-PL-01', PNG / 'F1_lamina_A3_muestra.png', dpi=150)
    render_layout(demo, 'MUESTRA-PL-01', PNG / 'F1_rotulo.png', dpi=300, ventana=(228, 5, 415, 132))
    render_layout(demo, 'CATALOGO', PNG / 'F1_bloques_y_lineas.png', dpi=150)
    print('Fase 1 lista en', OUT)


if __name__ == '__main__':
    main()
