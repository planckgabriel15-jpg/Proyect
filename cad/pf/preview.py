"""Render de layouts y del espacio modelo a PNG/PDF con ezdxf.addons.drawing (vista previa).

La fuente isocpeur.ttf no está disponible en Linux: el render la sustituye por otra
sans-serif, así que los anchos de texto son aproximados. El tamaño y la posición de
cada elemento son exactos.
"""
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import Configuration, LineweightPolicy, ColorPolicy, BackgroundPolicy
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from . import config as C


def _config(mono=True):
    return Configuration(lineweight_policy=LineweightPolicy.ABSOLUTE, lineweight_scaling=1.0,
                         color_policy=ColorPolicy.BLACK if mono else ColorPolicy.COLOR,
                         background_policy=BackgroundPolicy.WHITE, min_lineweight=0.08)


def render_layout(doc, nombre, archivo, dpi=200, ventana=None, mono=True):
    """Renderiza un layout de papel. ventana = (x0, y0, x1, y1) en mm para recortar."""
    lay = doc.layouts.get(nombre)
    W, H = C.PAPEL
    if ventana:
        x0, y0, x1, y1 = ventana
    else:
        x0, y0, x1, y1 = 0, 0, W, H
    fig = plt.figure(figsize=((x1 - x0) / 25.4, (y1 - y0) / 25.4), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    ctx.set_current_layout(lay)
    Frontend(ctx, MatplotlibBackend(ax), config=_config(mono)).draw_layout(lay, finalize=False)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.savefig(archivo, dpi=dpi, facecolor='white')
    plt.close(fig)
