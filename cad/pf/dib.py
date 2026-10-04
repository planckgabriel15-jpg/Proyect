"""Primitivas de dibujo en el espacio modelo (mm reales) con rayado asociativo."""
import math

from ezdxf.math import Vec2


class Vista:
    """Sistema local de una vista: u horizontal, v vertical, en mm reales.

    origen: punto del espacio modelo (mm) que corresponde a u = v = 0.
    sx: +1 si u crece hacia la derecha, -1 si crece hacia la izquierda.
    escala: denominador de la escala de la ventana que la muestra (para rayados y símbolos).
    """

    def __init__(self, msp, origen, sx=1, escala=100):
        self.msp = msp
        self.o = Vec2(origen)
        self.sx = sx
        self.escala = escala

    def p(self, u, v):
        return (self.o.x + self.sx * u, self.o.y + v)

    def pts(self, lst):
        return [self.p(u, v) for u, v in lst]

    # ------------------------------------------------------------ entidades
    def linea(self, a, b, capa, **kw):
        return self.msp.add_line(self.p(*a), self.p(*b), dxfattribs=dict(layer=capa, **kw))

    def polilinea(self, pts, capa, cerrada=False, **kw):
        return self.msp.add_lwpolyline(self.pts(pts), close=cerrada, dxfattribs=dict(layer=capa, **kw))

    def rect(self, u0, v0, u1, v1, capa, **kw):
        return self.polilinea([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], capa, cerrada=True, **kw)

    def circulo(self, c, r, capa, **kw):
        return self.msp.add_circle(self.p(*c), r, dxfattribs=dict(layer=capa, **kw))

    def punto(self, c, d, capa):
        """Punto lleno de diámetro d (polilínea con ancho, como DONUT)."""
        x, y = self.p(*c)
        pl = self.msp.add_lwpolyline([(x - d / 4, y, 0, 0, 1), (x + d / 4, y, 0, 0, 1)], format='xyseb',
                                     close=True, dxfattribs={'layer': capa})
        pl.dxf.const_width = d / 2
        return pl

    # ------------------------------------------------------------ rayado asociativo
    def rayar(self, contorno, patron, capa, escala_papel=None, angulo=0.0, color=256):
        """Rayado asociativo al contorno (LWPOLYLINE cerrada).

        escala_papel: factor del patrón por unidad de escala de ventana (se multiplica por self.escala).
        """
        h = self.msp.add_hatch(color=color, dxfattribs={'layer': capa})
        if patron == 'SOLID':
            h.set_solid_fill(color=color)
        else:
            h.set_pattern_fill(patron, scale=escala_papel * self.escala, angle=angulo, color=color)
        pts = [Vec2(p[0], p[1]) for p in contorno.get_points('xy')]
        path = h.paths.add_polyline_path(pts, is_closed=True)
        path.source_boundary_objects = [contorno.dxf.handle]
        h.dxf.associative = 1
        contorno.append_reactor_handle(h.dxf.handle)
        return h

    # ------------------------------------------------------------ símbolos
    def zigzag(self, a, b, amp_papel=2.0, largo_papel=3.0):
        """Puntos locales (u, v) de una línea de quiebre normalizada de a a b (sin prolongación)."""
        A, B = Vec2(a), Vec2(b)
        L = (B - A).magnitude
        t = (B - A).normalize()
        n = Vec2(-t.y, t.x)
        k = self.escala
        d = min(largo_papel * k, 0.8 * L) / 2
        h = min(amp_papel * k, 0.6 * L)
        m = (A + B) / 2
        q = [A, m - t * d, m - t * (d / 3) + n * h, m + t * (d / 3) - n * h, m + t * d, B]
        return [(p.x, p.y) for p in q]

    def prolongar(self, a, b, capa, extra_papel=2.0):
        """Prolongación de una línea de quiebre más allá del contorno, en ambos extremos."""
        A, B = Vec2(a), Vec2(b)
        t = (B - A).normalize() * extra_papel * self.escala
        self.linea(((A - t).x, (A - t).y), (A.x, A.y), capa)
        self.linea((B.x, B.y), ((B + t).x, (B + t).y), capa)

    def quiebre(self, a, b, capa, **kw):
        """Línea de quiebre suelta (cuando no es borde de un contorno rayado)."""
        self.polilinea(self.zigzag(a, b, **kw), capa)
        self.prolongar(a, b, capa)


# ---------------------------------------------------------------- escalas de rayado (§8.3)
# factor por unidad de escala de ventana para que el patrón se lea igual en el papel
ESC_HORMIGON = 0.02     # AR-CONC
ESC_TERRENO = 0.30      # EARTH
ESC_ACERO = 2.0 / 3.175  # ANSI31 a 2 mm en papel
ESC_MADERA = 1.0 / 3.175  # ANSI31 girado a 0°: líneas cada 1 mm en papel
ESC_REJILLA = 0.63      # NET
ESC_GRANEL = 0.066      # AR-SAND


def rellenos_al_fondo(layout):
    """Orden de dibujo (SORTENTSTABLE): rayados y rellenos detrás de los contornos."""
    orden, k = [], 1
    for e in layout:
        if e.dxftype() == 'HATCH':
            orden.append((e.dxf.handle, f'{k:X}'))
            k += 1
    for e in layout:
        if e.dxftype() != 'HATCH':
            orden.append((e.dxf.handle, f'{k:X}'))
            k += 1
    layout.set_redraw_order(orden)
