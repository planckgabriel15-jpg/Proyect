"""Construcción de la plantilla PF-IRAM-A3 con ezdxf.

crear_documento() devuelve un documento DXF R2018 con:
  variables de dibujo, tipos de línea, capas, estilos de texto, de cota y de
  multileader, bloques de anotación con atributos (anotativos), rótulo IRAM 4508,
  lista de materiales y un layout A3 vacío con su configuración de impresión.
"""
import math

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from ezdxf.colors import BY_LAYER_RAW_VALUE as BYLAYER_RAW_VALUE, BY_BLOCK_RAW_VALUE as BYBLOCK_RAW_VALUE
from ezdxf.math import Vec2

from . import config as C

ANNO_APP = 'AcadAnnotative'
LW_MARCO = 70


# ======================================================================= utilidades
def marcar_anotativo(entity):
    """Marca un estilo o un registro de bloque como anotativo (XDATA de AutoCAD)."""
    entity.set_xdata(ANNO_APP, [(1000, 'AnnotativeData'), (1002, '{'), (1070, 1), (1070, 1), (1002, '}')])


_FUENTE_MEDIDA = {}


def ancho_texto(s: str, h: float, negrita=False) -> float:
    """Ancho (mm) de un texto de altura h medido con la fuente que usa el render de control
    (DejaVu Sans, más ancha que ISOCPEUR): si no se superpone ahí, tampoco en AutoCAD."""
    from ezdxf.fonts import fonts
    if h not in _FUENTE_MEDIDA:
        _FUENTE_MEDIDA[h] = fonts.make_font(C.FUENTE_TTF, cap_height=h)
    return _FUENTE_MEDIDA[h].text_width(s) * (1.10 if negrita else 1.0)


# ======================================================================= variables
def variables(doc):
    """Variables que el DXF guarda en el encabezado. Las demás (MSLTSCALE, ANNOAUTOSCALE,
    FIELDEVAL, HPASSOC) las fija PF-POST.lsp dentro de AutoCAD."""
    valores = {'$INSUNITS': 4, '$LUNITS': 2, '$LUPREC': 0, '$AUNITS': 0, '$AUPREC': 1, '$MEASUREMENT': 1,
               '$LTSCALE': 1.0, '$PSLTSCALE': 1, '$CELTSCALE': 1.0, '$DIMASSOC': 2, '$DIMDSEP': ord(','),
               '$LWDISPLAY': 1, '$PLINEGEN': 1, '$MIRRTEXT': 0, '$ANGBASE': 0.0, '$ANGDIR': 0}
    for k, v in valores.items():
        doc.header[k] = v


# ======================================================================= tipos de línea y capas
def tipos_linea(doc):
    for nombre, desc, patron in C.TIPOS_LINEA:
        if nombre not in doc.linetypes:
            doc.linetypes.add(nombre, patron, description=desc)


def capas(doc):
    for nombre, color, lw, lt, imprime, desc in C.CAPAS:
        lay = doc.layers.add(nombre, color=color, linetype=lt)
        lay.dxf.lineweight = int(round(lw * 100)) if lw is not None else -3
        lay.dxf.plot = 1 if imprime else 0
        lay.description = desc
    # la capa 0 no se usa salvo dentro de bloques
    doc.layers.get('0').description = 'Solo dentro de bloques'


# ======================================================================= estilos
def estilos_texto(doc):
    for nombre, negrita, anot in ((C.ST_ANNO, False, True), (C.ST_N, False, False), (C.ST_NEG, True, False)):
        st = doc.styles.add(nombre, font=C.FUENTE_TTF)
        st.dxf.width = 1.0
        st.dxf.oblique = 0.0
        st.dxf.height = 0.0
        st.set_extended_font_data(family=C.FAMILIA_TTF, italic=False, bold=negrita)
        if anot:
            marcar_anotativo(st)


def _dimstyle(doc, nombre, **kw):
    ds = doc.dimstyles.new(nombre)
    base = dict(
        dimtxt=C.H_TXT, dimexo=1.5, dimexe=2.0, dimgap=1.0, dimdli=7.0,
        dimtad=1, dimtih=0, dimtoh=0, dimjust=0, dimtvp=0.0,
        dimdsep=ord(','), dimzin=0, dimlunit=2, dimaunit=0, dimadec=0, dimazin=0,
        dimscale=1.0, dimclrd=256, dimclre=256, dimclrt=256, dimlwd=-1, dimlwe=-1,
        dimatfit=3, dimtmove=1, dimtofl=1, dimtix=0, dimsoxd=0, dimupt=0,
        dimdle=0.0, dimcen=0.0, dimtsz=0.0, dimfxlon=0, dimrnd=0.0,
    )
    base.update(kw)
    for k, v in base.items():
        ds.dxf.set(k, v)
    ds.dxf.dimtxsty = C.ST_ANNO
    marcar_anotativo(ds)
    return ds


def estilos_cota(doc):
    for nombre in ('OBLIQUE', 'DOT'):
        doc.acquire_arrow(nombre)
    obra = dict(dimlfac=0.001, dimdec=2, dimasz=2.0)
    ds = _dimstyle(doc, 'IRAM-OBRA', **obra)
    ds.set_arrows(blk='OBLIQUE')
    ds = _dimstyle(doc, 'IRAM-OBRA-3', **dict(obra, dimdec=3))
    ds.set_arrows(blk='OBLIQUE')
    ds = _dimstyle(doc, 'IRAM-MEC', dimlfac=1.0, dimdec=0, dimasz=2.5)
    ds.set_arrows(blk='')
    doc.header['$DIMSTYLE'] = 'IRAM-OBRA'
    doc.header['$TEXTSTYLE'] = C.ST_ANNO


def estilos_multileader(doc, globo_blk):
    st_handle = doc.styles.get(C.ST_ANNO).dxf.handle
    from ezdxf.render.arrows import ARROWS
    doc.acquire_arrow('DOT')
    dot_handle = doc.blocks.get(ARROWS.block_name('DOT')).block_record_handle

    def comun(ml):
        d = ml.dxf
        d.leader_type = 1                 # recta
        d.leader_line_color = BYLAYER_RAW_VALUE
        d.leader_lineweight = -1
        d.max_leader_segments_points = 2
        d.arrow_head_handle = dot_handle
        d.arrow_head_size = 1.0
        d.text_style_handle = st_handle
        d.char_height = C.H_TXT
        d.text_color = BYLAYER_RAW_VALUE
        d.is_annotative = 1
        d.scale = 1.0
        d.has_dogleg = 1
        d.dogleg_length = 3.0
        d.landing_gap_size = 1.0
        d.has_landing = 1

    ref = doc.mleader_styles.new('IRAM-REF')
    comun(ref)
    ref.dxf.content_type = 2                  # MTEXT
    ref.dxf.text_left_attachment_type = 1     # medio de la línea superior
    ref.dxf.text_right_attachment_type = 1
    ref.dxf.text_attachment_direction = 0     # horizontal
    glo = doc.mleader_styles.new('IRAM-GLOBO')
    comun(glo)
    glo.dxf.content_type = 1                  # bloque
    glo.dxf.block_record_handle = globo_blk.block_record_handle
    glo.dxf.block_connection_type = 1         # al contorno (círculo)
    glo.dxf.block_color = BYBLOCK_RAW_VALUE
    glo.dxf.has_dogleg = 0
    glo.dxf.dogleg_length = 0.0
    # el estilo de multileader actual (CMLEADERSTYLE) lo fija PF-POST.lsp


# ======================================================================= bloques de anotación
def _attdef(blk, tag, pos, h, valor='', align=TA.MIDDLE_CENTER, style=C.ST_N, prompt=None, color=0, rot=0.0):
    a = blk.add_attdef(tag, pos, text=valor, height=h,
                       dxfattribs={'style': style, 'layer': '0', 'color': color, 'rotation': rot,
                                   'prompt': prompt or tag})
    a.set_placement(pos, align=align)
    return a


def _t(blk, s, pos, h, align=TA.MIDDLE_CENTER, style=C.ST_N, color=0, rot=0.0):
    t = blk.add_text(s, height=h, dxfattribs={'style': style, 'layer': '0', 'color': color, 'rotation': rot})
    t.set_placement(pos, align=align)
    return t


def _ln(blk, a, b, lw=None, color=0):
    att = {'layer': '0', 'color': color}
    if lw is not None:
        att['lineweight'] = lw
    return blk.add_line(a, b, dxfattribs=att)


def _poly(blk, pts, close=True, lw=None, color=0):
    att = {'layer': '0', 'color': color}
    if lw is not None:
        att['lineweight'] = lw
    return blk.add_lwpolyline(pts, close=close, dxfattribs=att)


def _relleno(blk, pts, color=0):
    h = blk.add_hatch(color=color, dxfattribs={'layer': '0'})
    h.paths.add_polyline_path(pts, is_closed=True)
    return h


def _nuevo_bloque(doc, nombre, anotativo=True, desc=''):
    blk = doc.blocks.new(nombre)
    if anotativo:
        marcar_anotativo(blk.block_record)
    return blk


TV_GUION, TV_TITULO, TV_SEP_ESCALA = 4.5, 10.5, 6.0     # posiciones dentro de TITULO-VISTA
TV_SUBRAYADO = (-1.4, -2.4)                            # doble subrayado bajo el título


def titulo_vista(layout, pos, letra, titulo, escala, capa='AN-TEXTOS'):
    """Inserta TITULO-VISTA, ubica la escala después del título y agrega el doble subrayado."""
    x, y = pos
    r = layout.add_blockref('TITULO-VISTA', (x, y), dxfattribs={'layer': capa})
    r.add_auto_attribs({'LETRA': letra, 'TITULO': titulo, 'ESCALA': escala})
    w = TV_TITULO + ancho_texto(titulo, C.H_TIT, negrita=True)
    for a in r.attribs:
        if a.dxf.tag == 'ESCALA':
            a.set_placement((x + w + TV_SEP_ESCALA, y), align=TA.LEFT)
    for dy in TV_SUBRAYADO:
        layout.add_line((x, y + dy), (x + w, y + dy), dxfattribs={'layer': capa})
    w_total = w + TV_SEP_ESCALA + ancho_texto(escala, C.H_TIT)
    return r, (x, y + TV_SUBRAYADO[1], x + w_total, y + C.H_TIT)


def bloques_anotacion(doc):
    H = C.H_TXT
    out = {}

    # --- GLOBO (contenido del multileader IRAM-GLOBO)
    b = _nuevo_bloque(doc, 'GLOBO', anotativo=False)
    b.add_circle((0, 0), 3.0, dxfattribs={'layer': '0', 'color': 0})
    _attdef(b, 'N', (0, 0), H, '1', prompt='Número de globo')
    out['GLOBO'] = b

    # --- NIVEL en corte o vista: triángulo de 3 mm con el vértice en el nivel
    th = 3.0 * math.sqrt(3) / 2
    for nombre, sg in (('NIVEL-CORTE', 1), ('NIVEL-CORTE-IZQ', -1)):
        b = _nuevo_bloque(doc, nombre)
        _poly(b, [(0, 0), (-1.5, th), (1.5, th)])
        _ln(b, (-1.5 * sg, th), (13.5 * sg, th))
        al = TA.BOTTOM_LEFT if sg > 0 else TA.BOTTOM_RIGHT
        _attdef(b, 'COTA', (-1.5 * sg, th + 0.8), H, '+0,00', align=al, prompt='Cota con signo (+3,90)')
        al2 = TA.MIDDLE_LEFT if sg > 0 else TA.MIDDLE_RIGHT
        _attdef(b, 'DESC', (14.5 * sg, th), H, '', align=al2, prompt='Descripción del nivel')
        out[nombre] = b

    # --- NIVEL en planta: círculo cruzado con dos cuadrantes llenos
    b = _nuevo_bloque(doc, 'NIVEL-PLANTA')
    r = 2.0
    b.add_circle((0, 0), r, dxfattribs={'layer': '0', 'color': 0})
    _ln(b, (-r, 0), (r, 0))
    _ln(b, (0, -r), (0, r))
    for a0 in (0, 180):
        pts = [(0, 0)] + [(r * math.cos(math.radians(a0 + k * 10)), r * math.sin(math.radians(a0 + k * 10)))
                          for k in range(10)]
        _relleno(b, pts)
    _attdef(b, 'COTA', (r + 1.2, 0), H, '+0,00', align=TA.MIDDLE_LEFT, prompt='Cota con signo')
    out['NIVEL-PLANTA'] = b

    # --- CORTE: extremo de línea de corte (trazo grueso + flecha de observación + letra)
    b = _nuevo_bloque(doc, 'CORTE')
    _ln(b, (0, 0), (8, 0), lw=LW_MARCO)
    _ln(b, (2, 0), (2, -6))
    _relleno(b, [(2, -9), (0.9, -5.6), (3.1, -5.6)])
    _attdef(b, 'LETRA', (2, -13.5), 5.0, 'A', prompt='Letra del corte')
    _attdef(b, 'LAMINA', (2, -19.5), H, 'CT-02', prompt='Lámina de destino')
    out['CORTE'] = b

    # --- LLAMADA-DETALLE: círculo dividido (número arriba, lámina abajo)
    b = _nuevo_bloque(doc, 'LLAMADA-DETALLE')
    b.add_circle((0, 0), 8.0, dxfattribs={'layer': '0', 'color': 0})
    _ln(b, (-8, 0), (8, 0))
    _attdef(b, 'DETALLE', (0, 3.6), C.H_TIT, 'D5', prompt='Número de detalle')
    _attdef(b, 'LAMINA', (0, -3.4), H, 'DET-05', prompt='Lámina')
    out['LLAMADA-DETALLE'] = b

    # --- TITULO-VISTA: letra — título (doble subrayado) + escala
    b = _nuevo_bloque(doc, 'TITULO-VISTA')
    _attdef(b, 'LETRA', (0, 0), C.H_TIT, 'A', align=TA.LEFT, style=C.ST_NEG, prompt='Letra de la vista')
    _t(b, '—', (TV_GUION, 0), C.H_TIT, align=TA.LEFT, style=C.ST_NEG)
    _attdef(b, 'TITULO', (TV_TITULO, 0), C.H_TIT, 'TÍTULO DE LA VISTA', align=TA.LEFT, style=C.ST_NEG,
            prompt='Título de la vista')
    _attdef(b, 'ESCALA', (90.0, 0), C.H_TIT, 'Esc. 1:10', align=TA.LEFT, style=C.ST_N, prompt='Escala')
    out['TITULO-VISTA'] = b

    # --- NORTE
    b = _nuevo_bloque(doc, 'NORTE')
    b.add_circle((0, 0), 6.0, dxfattribs={'layer': '0', 'color': 0})
    _poly(b, [(0, 6), (-2.6, -4.5), (0, -2.8), (2.6, -4.5)])
    _relleno(b, [(0, 6), (0, -2.8), (2.6, -4.5)])
    _attdef(b, 'N', (0, 9.5), 5.0, 'N', prompt='Letra norte')
    out['NORTE'] = b

    # --- EJE: círculo de Ø8 con designación
    b = _nuevo_bloque(doc, 'EJE')
    b.add_circle((0, 0), 4.0, dxfattribs={'layer': '0', 'color': 0})
    _attdef(b, 'EJE', (0, 0), C.H_TIT, 'L1', prompt='Designación del eje')
    out['EJE'] = b

    # --- FLUJO: flecha roja (el CTB imprime el ACI 10 en rojo)
    b = _nuevo_bloque(doc, 'FLUJO')
    _ln(b, (0, 0), (7, 0), lw=35, color=C.ACI_FLUJO)
    _relleno(b, [(10, 0), (7, 1.1), (7, -1.1)], color=C.ACI_FLUJO)
    out['FLUJO'] = b

    # --- PASO-RECORRIDO: círculo rojo con número 1 a 8
    b = _nuevo_bloque(doc, 'PASO-RECORRIDO')
    b.add_circle((0, 0), 3.0, dxfattribs={'layer': '0', 'color': C.ACI_FLUJO, 'lineweight': 35})
    _attdef(b, 'N', (0, 0), H, '1', color=C.ACI_FLUJO, style=C.ST_NEG, prompt='Paso del recorrido')
    out['PASO-RECORRIDO'] = b
    return out


# ======================================================================= rótulo IRAM 4508
# celdas: (tag, etiqueta, x0, x1, y0, y1, altura de valor, alineación del valor, valor por defecto)
ROT_W = C.ROT_ANCHO
X0 = -ROT_W
ROT_FILAS = [0.0, 15.0, 24.5, 34.0, 43.5, 67.5, 77.5]   # bordes de filas del rótulo
REV_FILAS = [77.5, 83.5, 89.5]                         # encabezado y fila de la revisión E
ROT_ALTO = REV_FILAS[-1]

CELDAS = [
    # fila 1 (0–15)
    ('CODIGO', 'CÓDIGO', X0, -133, 0, 15, C.H_COD, 'c', 'PL-00'),
    ('LAMINA', 'LÁMINA', -133, -107, 0, 15, C.H_TIT, 'c', '1 de 14'),
    ('REV', 'REV.', -107, -91, 0, 15, C.H_TIT, 'c', 'E'),
    ('UNIDAD', 'UNIDAD', -91, -30, 0, 15, C.H_TXT, 'u', ''),
    # fila 2 (15–24,5)
    ('ESCALA', 'ESCALA(S)', X0, -90, 15, 24.5, C.H_TXT, 'l', '—'),
    ('FECHA', 'FECHA', -90, -60, 15, 24.5, C.H_TXT, 'l', ''),
    ('IMPRESION', 'IMPRESIÓN', -60, -30, 15, 24.5, C.H_TXT, 'l', '--/--/----'),
    # fila 3 (24,5–34)
    ('DIBUJO', 'DIBUJÓ', X0, -121, 24.5, 34, C.H_TXT, 'l', ''),
    ('VERIFICO', 'VERIFICÓ', -121, -81, 24.5, 34, C.H_TXT, 'l', ''),
    ('TUTOR', 'TUTOR EXTERNO', -81, -33, 24.5, 34, C.H_TXT, 'l', ''),
    ('NPROYECTO', 'N.º PROYECTO', -33, 0, 24.5, 34, C.H_TXT, 'l', ''),
    # fila 4 (34–43,5)
    ('INTEGRANTES', 'INTEGRANTES', X0, -58, 34, 43.5, C.H_TXT, 'l', ''),
    ('ARCHIVO', 'ARCHIVO', -58, 0, 34, 43.5, C.H_TXT, 'l', ''),
]
REV_COLS = [('REV', 'REV.', X0, -160), ('FECHA', 'FECHA', -160, -132),
            ('DESCRIPCION', 'DESCRIPCIÓN', -132, -45), ('DIBUJO', 'DIBUJÓ', -45, 0)]


def bloque_rotulo(doc):
    P = C.PROYECTO
    defaults = {'FECHA': P['fecha'], 'DIBUJO': P['dibujo'], 'VERIFICO': P['verifico'], 'TUTOR': P['tutor'],
                'NPROYECTO': P['n_proyecto'], 'INTEGRANTES': P['integrantes'], 'ARCHIVO': P['archivo'],
                'REV': P['rev']}
    b = doc.blocks.new('ROTULO-A3')          # no anotativo: va en el espacio papel a 1:1
    H = C.H_TXT
    # contorno exterior (grueso) y divisiones interiores
    _poly(b, [(X0, 0), (0, 0), (0, ROT_ALTO), (X0, ROT_ALTO)], lw=LW_MARCO)
    for y in ROT_FILAS[1:] + REV_FILAS[1:-1]:
        x1 = -30 if y == ROT_FILAS[1] else 0
        _ln(b, (X0, y), (x1, y))
    # divisiones verticales por fila
    F, R = ROT_FILAS, REV_FILAS
    filas_v = {(F[0], F[1]): [-133, -107, -91, -30], (F[1], F[2]): [-90, -60, -30], (F[2], F[3]): [-121, -81, -33],
               (F[3], F[4]): [-58], (R[0], R[2]): [-160, -132, -45]}
    for (y0, y1), xs in filas_v.items():
        for x in xs:
            _ln(b, (x, y0), (x, y1))
    # celdas con etiqueta + atributo
    for tag, etiqueta, x0, x1, y0, y1, hv, al, dflt in CELDAS:
        _t(b, etiqueta, (x0 + 1.0, y1 - 1.2), H, align=TA.TOP_LEFT)
        if al == 'c':
            _attdef(b, tag, ((x0 + x1) / 2, y0 + 1.5), hv, dflt, align=TA.BOTTOM_CENTER)
        elif al == 'u':
            _attdef(b, 'UNIDAD', (x0 + 1.0, y0 + 5.2), H, P['unidad'], align=TA.BOTTOM_LEFT)
            _attdef(b, 'UNIDAD_NOTA', (x0 + 1.0, y0 + 1.2), H, P['unidad_nota'], align=TA.BOTTOM_LEFT)
        else:
            _attdef(b, tag, (x0 + 1.0, y0 + 1.2), hv, defaults.get(tag, dflt), align=TA.BOTTOM_LEFT)
    # método de proyección ISO E (primer diedro), celda (-30..0) x (0..24,5)
    _t(b, 'MÉTODO ISO E', (-29.0, ROT_FILAS[2] - 1.2), H, align=TA.TOP_LEFT)
    cy = 9.5
    _poly(b, [(-26.5, cy - 2.0), (-18.5, cy - 4.0), (-18.5, cy + 4.0), (-26.5, cy + 2.0)])
    b.add_circle((-9.5, cy), 4.0, dxfattribs={'layer': '0', 'color': 0})
    b.add_circle((-9.5, cy), 2.0, dxfattribs={'layer': '0', 'color': 0})
    for a, c in (((-28.0, cy), (-17.0, cy)), ((-15.0, cy), (-4.0, cy)), ((-9.5, cy - 5.5), (-9.5, cy + 5.5))):
        b.add_line(a, c, dxfattribs={'layer': '0', 'color': 0, 'linetype': C.ISO04, 'ltscale': 0.15,
                                      'lineweight': 18})
    # título y subtítulo (atributos multilínea)
    y0, y1 = ROT_FILAS[4], ROT_FILAS[5]
    a = _attdef(b, 'TITULO', (X0 + 2.0, y1 - 1.5), C.H_ROT_TIT, 'Título de la lámina', align=TA.TOP_LEFT,
                style=C.ST_NEG)
    a.set_mtext(_mtext(doc, 'Título de la lámina', (X0 + 2.0, y1 - 1.5), C.H_ROT_TIT, ROT_W - 4.0, 1,
                       C.ST_NEG))
    a = _attdef(b, 'SUBTITULO', (X0 + 2.0, y0 + 1.3), H, 'Subtítulo', align=TA.BOTTOM_LEFT)
    a.set_mtext(_mtext(doc, 'Subtítulo', (X0 + 2.0, y0 + 1.3), H, ROT_W - 4.0, 7, C.ST_N))
    # encabezado (2 líneas)
    y0, y1 = ROT_FILAS[5], ROT_FILAS[6]
    _attdef(b, 'ENCABEZADO', (X0 + 2.0, y1 - 1.2), H, P['encabezado'], align=TA.TOP_LEFT, style=C.ST_NEG)
    _attdef(b, 'SISTEMA', (X0 + 2.0, y0 + 1.2), H, P['sistema'], align=TA.BOTTOM_LEFT)
    # tabla de revisiones: encabezado abajo, fila E arriba (crece hacia arriba)
    ye, yf = (REV_FILAS[0] + REV_FILAS[1]) / 2, (REV_FILAS[1] + REV_FILAS[2]) / 2
    for tag, et, x0, x1 in REV_COLS:
        _t(b, et, ((x0 + x1) / 2, ye), H, style=C.ST_NEG)
        val = {'REV': P['rev'], 'FECHA': P['fecha'], 'DESCRIPCION': P['rev_desc'], 'DIBUJO': P['dibujo_corto']}[tag]
        if tag in ('REV', 'FECHA'):
            _attdef(b, f'REV1_{tag}', ((x0 + x1) / 2, yf), H, val)
        else:
            _attdef(b, f'REV1_{tag}', (x0 + 1.0, yf), H, val, align=TA.MIDDLE_LEFT)
    return b


def _mtext(doc, texto, pos, h, ancho, attach, style):
    """MTEXT auxiliar (fuera de todo layout) para incrustar en un atributo multilínea.
    attach: 1 = arriba-izquierda, 7 = abajo-izquierda."""
    from ezdxf.entities import MText
    m = MText.new(dxfattribs={'insert': pos, 'char_height': h, 'width': ancho, 'attachment_point': attach,
                              'style': style, 'layer': '0', 'line_spacing_factor': 1.0})
    m.text = texto
    return m


# ======================================================================= lista de materiales IRAM 4508
LM_COLS = [  # (tag, encabezado (2 líneas), ancho, alineación)
    ('POS', ('Pos.', ''), 9, 'c'), ('CANT', ('Cant.', ''), 11, 'c'),
    ('DENOM', ('Denominación', ''), 35, 'l'), ('MAT', ('Material /', 'norma'), 29, 'l'),
    ('DIM', ('Dimensiones /', 'designación'), 38, 'l'), ('PESO', ('Peso unit.', '(kg)'), 22, 'c'),
    ('OBS', ('Observaciones', ''), 31, 'l')]
LM_H_ENC, LM_H_FILA = 10.0, 6.0


def bloques_lista_materiales(doc):
    H = C.H_TXT
    xs = [X0]
    for _, _, w, _ in LM_COLS:
        xs.append(xs[-1] + w)
    assert abs(xs[-1]) < 1e-6
    # encabezado
    b = doc.blocks.new('LISTA-MATERIALES')
    _poly(b, [(X0, 0), (0, 0), (0, LM_H_ENC), (X0, LM_H_ENC)], lw=50)
    for x in xs[1:-1]:
        _ln(b, (x, 0), (x, LM_H_ENC))
    for (tag, (l1, l2), w, al), xa in zip(LM_COLS, xs):
        xc = xa + w / 2
        if l2:
            _t(b, l1, (xc, 6.6), H, style=C.ST_NEG)
            _t(b, l2, (xc, 3.4), H, style=C.ST_NEG)
        else:
            _t(b, l1, (xc, 5.0), H, style=C.ST_NEG)
    # fila
    f = doc.blocks.new('LM-FILA')
    _poly(f, [(X0, 0), (0, 0), (0, LM_H_FILA), (X0, LM_H_FILA)])
    for x in xs[1:-1]:
        _ln(f, (x, 0), (x, LM_H_FILA))
    for (tag, _, w, al), xa in zip(LM_COLS, xs):
        if al == 'c':
            _attdef(f, tag, (xa + w / 2, LM_H_FILA / 2), H, '')
        else:
            _attdef(f, tag, (xa + 1.0, LM_H_FILA / 2), H, '', align=TA.MIDDLE_LEFT)
    return b, f


# ======================================================================= formato A3 (IRAM 4504)
def configurar_layout(layout):
    layout.page_setup(size=C.PAPEL, margins=(0, 0, 0, 0), units='mm', offset=(0, 0), rotation=0,
                      scale=(1, 1), name=C.MEDIA_A3, device=C.PLOTTER)
    layout.set_plot_style(C.CTB, show=True)
    layout.use_plot_styles(True)
    layout.print_lineweights(True)
    layout.set_plot_type(5)            # layout


def dibujar_formato(layout, atributos: dict):
    """Recuadro, marcas de centrado y rótulo en un layout A3."""
    x0, y0, x1, y1 = C.MARCO
    W, H = C.PAPEL
    layout.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                          dxfattribs={'layer': 'G-MARCO'})
    # marcas de centrado: desde el borde de la hoja hasta 5 mm dentro del recuadro
    for a, b in (((W / 2, 0), (W / 2, y0 + 5)), ((W / 2, H), (W / 2, y1 - 5)),
                 ((0, H / 2), (x0 + 5, H / 2)), ((W, H / 2), (x1 - 5, H / 2))):
        layout.add_line(a, b, dxfattribs={'layer': 'G-MARCO'})
    ins = layout.add_blockref('ROTULO-A3', (x1, y0), dxfattribs={'layer': 'G-ROTULO'})
    ins.add_auto_attribs(atributos)
    return ins


def atributos_rotulo(codigo, titulo, subtitulo, escalas, n):
    P = C.PROYECTO
    return {'CODIGO': codigo, 'TITULO': titulo, 'SUBTITULO': subtitulo, 'ESCALA': escalas,
            'LAMINA': f'{n} de {P["total_laminas"]}', 'REV': P['rev'], 'FECHA': P['fecha'],
            'IMPRESION': '--/--/----'}


# ======================================================================= zonas y UCS (§6.3)
def zonas(doc):
    msp = doc.modelspace()
    for nombre, (orig, xax, rect, desc) in C.ZONAS.items():
        xa = Vec2(xax[0], xax[1])
        doc.ucs.new(f'UCS-{nombre}', dxfattribs={'origin': (orig[0], orig[1], 0), 'xaxis': (xax[0], xax[1], 0),
                                                  'yaxis': (0, 1, 0)})
        x0, y0, x1, y1 = rect
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                           dxfattribs={'layer': 'AN-NOPLOT'})
        t = msp.add_text(f'ZONA {nombre} — {desc}', height=600,
                         dxfattribs={'layer': 'AN-NOPLOT', 'style': C.ST_N})
        t.set_placement((x0 + 400, y1 - 400), align=TA.TOP_LEFT)
        # cruz en el origen de la zona
        o = Vec2(orig)
        msp.add_line(o - xa * 1000, o + xa * 1000, dxfattribs={'layer': 'AN-NOPLOT'})
        msp.add_line(o - Vec2(0, 1000), o + Vec2(0, 1000), dxfattribs={'layer': 'AN-NOPLOT'})


# ======================================================================= documento
def crear_documento(con_zonas=False):
    doc = ezdxf.new('R2018', setup=False, units=4)
    doc.appids.add(ANNO_APP)
    variables(doc)
    tipos_linea(doc)
    capas(doc)
    estilos_texto(doc)
    estilos_cota(doc)
    blks = bloques_anotacion(doc)
    estilos_multileader(doc, blks['GLOBO'])
    bloque_rotulo(doc)
    bloques_lista_materiales(doc)
    doc.header['$CLAYER'] = 'AN-NOPLOT'
    if con_zonas:
        zonas(doc)
    # layout A3 vacío
    lay = doc.layouts.get('Layout1')
    doc.layouts.rename('Layout1', 'A3-IRAM')
    lay = doc.layouts.get('A3-IRAM')
    configurar_layout(lay)
    dibujar_formato(lay, atributos_rotulo('PL-00', 'Título de la lámina', 'Subtítulo de la lámina', '—', 1))
    return doc
