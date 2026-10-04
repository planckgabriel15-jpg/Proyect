"""Render de layouts y del espacio modelo a PNG con ezdxf.addons.drawing (vista previa de control).

Simula la impresión con PF-IRAM-MONO.ctb: todo negro, ACI 8 gris 60 %, ACI 9 gris 50 %,
ACI 10 rojo; espesores de línea reales en mm de papel.
La fuente isocpeur.ttf no está en Linux: el render usa DejaVu Sans, que es más ancha
(si no hay superposición acá, tampoco la hay en AutoCAD).
"""
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons import acadctb
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import Configuration, LineweightPolicy, ColorPolicy, BackgroundPolicy
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from . import config as C


def ctb_preview():
    ctb = acadctb.new_ctb()
    for aci in range(1, 256):
        ctb[aci].color = (0, 0, 0)
    ctb[8].color = (102, 102, 102)
    ctb[9].color = (128, 128, 128)
    ctb[C.ACI_FLUJO].color = (200, 30, 30)
    return ctb


def _config(lw_escala=1.0):
    return Configuration(lineweight_policy=LineweightPolicy.ABSOLUTE, lineweight_scaling=lw_escala,
                         color_policy=ColorPolicy.COLOR, background_policy=BackgroundPolicy.WHITE,
                         min_lineweight=0.08)


def _dibujar(doc, layout, ax, ventana, ancho_mm, alto_mm, archivo, dpi, fig):
    ctb = ctb_preview()
    ctx = RenderContext(doc, ctb=ctb)
    ctx.set_current_layout(layout, ctb=ctb)
    no_imprime = {l.dxf.name.upper() for l in doc.layers if not l.dxf.plot}

    def imprime(e):
        return e.dxf.get('layer', '0').upper() not in no_imprime
    Frontend(ctx, MatplotlibBackend(ax), config=_config()).draw_layout(layout, finalize=False, filter_func=imprime)
    x0, y0, x1, y1 = ventana
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.savefig(archivo, dpi=dpi, facecolor='white')
    plt.close(fig)


def render_layout(doc, nombre, archivo, dpi=200, ventana=None):
    """Layout de papel completo o recortado (ventana en mm de papel)."""
    lay = doc.layouts.get(nombre)
    ventana = ventana or (0, 0, *C.PAPEL)
    w, h = ventana[2] - ventana[0], ventana[3] - ventana[1]
    fig = plt.figure(figsize=(w / 25.4, h / 25.4), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    _dibujar(doc, lay, ax, ventana, w, h, archivo, dpi, fig)


def render_modelo(doc, ventana, escala, archivo, dpi=200, titulo=None):
    """Región del espacio modelo (mm reales) tal como se vería impresa a 1:escala."""
    x0, y0, x1, y1 = ventana
    w, h = (x1 - x0) / escala, (y1 - y0) / escala
    margen = 12 if titulo else 0
    fig = plt.figure(figsize=(w / 25.4, (h + margen) / 25.4), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, h / (h + margen)])
    if titulo:
        fig.text(0.01, 1 - 4 / (h + margen), titulo, fontsize=9, va='top', ha='left')
    _dibujar(doc, doc.modelspace(), ax, ventana, w, h, archivo, dpi, fig)
