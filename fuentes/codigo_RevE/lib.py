"""Base de dibujo para el legajo de planos Rev E (A3 apaisado, unidades de hoja en mm)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Circle as MCirc
from matplotlib.path import Path
import numpy as np
from shapely.geometry import LineString, Polygon as SPoly, box as sbox
from shapely.strtree import STRtree

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['hatch.linewidth'] = 0.35
plt.rcParams['pdf.fonttype'] = 42

W, H = 420.0, 297.0
FX0, FY0, FX1, FY1 = 20.0, 10.0, 410.0, 287.0
TBX0, TBY0, TBX1, TBY1 = 225.0, 10.0, 410.0, 50.0
DPI = 200

# grosores (pt)
LW_K = 1.1    # contorno principal
LW = 0.7      # contorno
LW_T = 0.4    # fino
LW_D = 0.3    # cotas
FS_L = 5.6    # referencias
FS_D = 5.6    # cotas
FS_TAB = 5.5  # tablas
FS_VT = 7.6   # titulos de vista

C_NEW = '#e6eef7'   # elemento nuevo (celeste)
C_NEW2 = '#c9d9ea'
C_EXIST = '#d9d9d9'
C_WOOD = '#efe1c8'
C_STEEL = '#bdbdbd'
C_DARK = '#555555'


def fmt_mm(v):
    v = int(round(v))
    s = f"{abs(v):,}".replace(',', '.')
    return ('-' if v < 0 else '') + s


def fmt_m(v, nd=2):
    s = f"{v:.{nd}f}".replace('.', ',')
    return s


class Sheet:
    def __init__(self, code, title, subtitle, escala, lamina, total=14, rev='E',
                 fecha='03/10/2026'):
        self.code = code
        self.fig = plt.figure(figsize=(W / 25.4, H / 25.4), dpi=DPI)
        ax = self.fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, W)
        ax.set_ylim(0, H)
        ax.set_aspect('equal')
        ax.axis('off')
        self.ax = ax
        self.texts = []    # dict(a=artist, id, chk, tb, fit)
        self.lines = []    # dict(a=artist, owner, chk)
        self.areas = []    # dict(a=patch, owner) zonas donde no puede ir texto
        self.vtitles = []
        self.fits = []     # (text_id, xmin, xmax) texto que debe caber en celda
        self._id = 0
        self._frame()
        self._titleblock(code, title, subtitle, escala, lamina, total, rev, fecha)

    # ------------------------------------------------------------ primitivas
    def nid(self):
        self._id += 1
        return self._id

    def L(self, xs, ys, lw=LW, ls='-', c='k', owner=None, chk=True, z=3, **kw):
        a, = self.ax.plot(xs, ys, lw=lw, ls=ls, color=c, zorder=z,
                          solid_capstyle='butt', **kw)
        self.lines.append(dict(a=a, owner=owner, chk=chk))
        return a

    def P(self, pts, fc='none', ec='k', lw=LW, hatch=None, z=2, owner=None, chk=True,
          block=False, closed=True, ls='-'):
        p = MPoly(np.asarray(pts, float), closed=closed, fc=fc, ec=ec, lw=lw,
                  hatch=hatch, zorder=z, joinstyle='miter', ls=ls)
        self.ax.add_patch(p)
        if ec != 'none' and lw > 0:
            self.lines.append(dict(a=p, owner=owner, chk=chk))
        if block or hatch or (fc not in ('none', 'white', '#ffffff') and _dark(fc)):
            self.areas.append(dict(a=p, owner=owner))
        return p

    def C(self, x, y, r, fc='none', ec='k', lw=LW, z=3, owner=None, chk=True, block=False,
          hatch=None, ls='-'):
        p = MCirc((x, y), r, fc=fc, ec=ec, lw=lw, zorder=z, hatch=hatch, ls=ls)
        self.ax.add_patch(p)
        if ec != 'none':
            self.lines.append(dict(a=p, owner=owner, chk=chk))
        if block or hatch:
            self.areas.append(dict(a=p, owner=owner))
        return p

    def T(self, x, y, s, fs=FS_L, ha='left', va='center', rot=0, bold=False, c='k',
          chk=True, bg=False, z=6, tb=False, style='normal', tid=None):
        tid = tid or self.nid()
        kw = {}
        if bg:
            kw['bbox'] = dict(fc='white', ec='none', pad=0.6)
        a = self.ax.text(x, y, s, fontsize=fs, ha=ha, va=va, rotation=rot, color=c,
                         fontweight='bold' if bold else 'normal', zorder=z,
                         rotation_mode='anchor', fontstyle=style, **kw)
        self.texts.append(dict(a=a, id=tid, chk=chk, tb=tb))
        return tid

    # ------------------------------------------------------------ marco y rotulo
    def _frame(self):
        self.L([FX0, FX1, FX1, FX0, FX0], [FY0, FY0, FY1, FY1, FY0], lw=1.6, chk=False)
        mx, my = (FX0 + FX1) / 2, (FY0 + FY1) / 2
        for xs, ys in [([mx, mx], [FY1, FY1 + 5]), ([mx, mx], [FY0 - 5, FY0]),
                       ([FX0 - 5, FX0], [my, my]), ([FX1, FX1 + 5], [my, my])]:
            self.L(xs, ys, lw=0.8, chk=False)

    def _titleblock(self, code, title, subtitle, escala, lamina, total, rev, fecha):
        x0, y0, x1, y1 = TBX0, TBY0, TBX1, TBY1
        self.P([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fc='white', lw=1.2, z=1, chk=False)
        hs = [y0 + 8.2, y0 + 17.2, y0 + 30.2]
        for h in hs:
            self.L([x0, x1], [h, h], lw=0.7, chk=False)
        self.T(x0 + 2, y1 - 3.0, 'UTN — Facultad Regional Córdoba · Ingeniería Industrial · Proyecto Final',
               fs=6.3, bold=True, tb=True)
        self.T(x0 + 2, y1 - 7.0, 'Sistema de distribución de fertilizantes a granel — Redler — AGD Río Primero',
               fs=5.8, tb=True)
        self.T(x0 + 2, y0 + 26.3, title, fs=9.6, bold=True, tb=True)
        self.T(x0 + 2, y0 + 21.3, subtitle, fs=5.2, tb=True)
        self.T(x0 + 2, y0 + 14.7, 'Integrantes: Fernández · Planckensteiner · Quiroga Palacio · Solera',
               fs=5.5, tb=True)
        self.T(x0 + 2, y0 + 10.6, 'Verificó: Ing. R. Bonaiuti   ·   Tutor externo: C. D. Solera (AGD)',
               fs=5.5, tb=True)
        ws = [38, 50, 30, 21.8, 18.1, 27.1]
        labels = ['CÓDIGO', 'ESCALA', 'LÁMINA', 'REV.', 'UNID.', 'FECHA']
        vals = [code, escala, f'{lamina} de {total}', rev, 'm / mm', fecha]
        xx = x0
        for w, lab, v in zip(ws, labels, vals):
            if xx > x0:
                self.L([xx, xx], [y0, y0 + 8.2], lw=0.7, chk=False)
            self.T(xx + 1.0, y0 + 6.9, lab, fs=3.9, tb=True)
            fsv = 7.0 if len(v) < 16 else (6.0 if len(v) < 22 else 5.0)
            tid = self.T(xx + w / 2, y0 + 2.9, v, fs=fsv, bold=True, ha='center', tb=True)
            self.fits.append((tid, xx + 0.5, xx + w - 0.5))
            xx += w
        self.fits.append((None, 0, 0))

    # ------------------------------------------------------------ ayudas de dibujo
    def vtitle(self, x, y, s, fs=FS_VT):
        tid = self.T(x, y, s, fs=fs, bold=True, va='baseline')
        self.vtitles.append(tid)
        return tid

    def lev(self, x, y, s, side='right', fs=FS_L, ln=14):
        """Marca de nivel: triangulo invertido con punta en (x,y)."""
        tid = self.nid()
        self.P([(x, y), (x - 1.2, y + 1.8), (x + 1.2, y + 1.8)], fc='white', lw=0.5,
               owner=tid, z=5)
        if side == 'right':
            self.L([x - 1.6, x + ln], [y + 1.8, y + 1.8], lw=LW_T, owner=tid)
            self.T(x + 1.8, y + 3.2, s, fs=fs, ha='left', tid=tid)
        else:
            self.L([x - ln, x + 1.6], [y + 1.8, y + 1.8], lw=LW_T, owner=tid)
            self.T(x - 1.8, y + 3.2, s, fs=fs, ha='right', tid=tid)
        return tid

    def lead(self, px, py, tx, ty, s, ha=None, fs=FS_L, dot=True, knee=True, va='center',
             bold=False):
        """Referencia: punto (px,py) en hoja -> texto en (tx,ty)."""
        tid = self.nid()
        if ha is None:
            ha = 'left' if tx >= px else 'right'
        gap = 0.8 if ha == 'left' else -0.8
        if knee:
            kx = tx - (2.5 if ha == 'left' else -2.5)
            self.L([px, kx, tx - gap * 0.2], [py, ty, ty], lw=LW_T, owner=tid)
        else:
            self.L([px, tx - gap * 0.2], [py, ty], lw=LW_T, owner=tid)
        if dot:
            self.C(px, py, 0.38, fc='k', ec='k', lw=0.2, owner=tid, z=7)
        self.T(tx + gap, ty, s, fs=fs, ha=ha, va=va, tid=tid, bold=bold)
        return tid

    def labels(self, items, x, ha='left', ymin=None, ymax=None, sp=3.4, fs=FS_L, knee=2.5):
        """Distribuye referencias en una columna x (hoja). items: (px, py, texto[, ty]).
        Ordena por altura para que las guias no se crucen."""
        it = sorted(items, key=lambda t: -(t[3] if len(t) > 3 else t[1]))
        ys = [(t[3] if len(t) > 3 else t[1]) for t in it]
        if ymax is not None:
            ys = [min(y, ymax) for y in ys]
        for i in range(1, len(ys)):
            if ys[i] > ys[i - 1] - sp:
                ys[i] = ys[i - 1] - sp
        if ymin is not None and ys and ys[-1] < ymin:
            ys[-1] = ymin
            for i in range(len(ys) - 2, -1, -1):
                if ys[i] < ys[i + 1] + sp:
                    ys[i] = ys[i + 1] + sp
        ids = []
        for t, y in zip(it, ys):
            px, py, txt = t[0], t[1], t[2]
            lines = txt.split('\n')
            tid = self.lead(px, py, x, y, lines[0], ha=ha, fs=fs)
            for j, extra in enumerate(lines[1:]):
                self.T(x + (0.8 if ha == 'left' else -0.8), y - (j + 1) * fs * 0.42, extra, fs=fs, ha=ha, tid=tid)
            ids.append(tid)
        return ids

    def balloons(self, items, r=2.3):
        for n, (px, py), (bx, by) in items:
            lid = self.nid()
            d = np.array([bx - px, by - py])
            dd = np.hypot(*d)
            e = np.array([bx, by]) - d / dd * r
            self.L([px, e[0]], [py, e[1]], lw=LW_T, owner=lid)
            self.C(px, py, 0.35, fc='k', ec='k', lw=0.2, owner=lid, z=7)
            self.balloon(bx, by, n, r=r)

    def balloon(self, x, y, n, r=2.3, fs=5.6):
        tid = self.nid()
        self.C(x, y, r, fc='white', lw=0.6, owner=tid, z=6)
        self.T(x, y, str(n), fs=fs, ha='center', va='center', bold=True, tid=tid, z=7)
        return tid

    def dim(self, p1, p2, off, text, tpos=0.5, fs=FS_D, ext=True, tside=1, ext0=0.8,
            tick='slash', textoff=None):
        """Cota alineada entre p1 y p2 (hoja mm). off: desplazamiento perpendicular (signo:
        izquierda del vector p1->p2). El texto va del lado exterior (tside=1) o interior."""
        tid = self.nid()
        p1 = np.array(p1, float)
        p2 = np.array(p2, float)
        d = p2 - p1
        Ld = np.hypot(*d)
        u = d / Ld
        n = np.array([-u[1], u[0]])
        sgn = 1 if off >= 0 else -1
        a1 = p1 + n * off
        a2 = p2 + n * off
        if ext:
            for p, a in [(p1, a1), (p2, a2)]:
                if abs(off) > 1.0:
                    s0 = p + n * sgn * ext0
                    s1 = a + n * sgn * 1.2
                    self.L([s0[0], s1[0]], [s0[1], s1[1]], lw=LW_D, owner=tid)
        self.L([a1[0] - u[0] * 1.2, a2[0] + u[0] * 1.2], [a1[1] - u[1] * 1.2, a2[1] + u[1] * 1.2],
               lw=LW_D, owner=tid)
        for a in (a1, a2):
            if tick == 'slash':
                t = (u + n) / np.sqrt(2) * 1.0
                self.L([a[0] - t[0], a[0] + t[0]], [a[1] - t[1], a[1] + t[1]], lw=0.6, owner=tid)
            else:
                self.C(a[0], a[1], 0.35, fc='k', lw=0.2, owner=tid)
        ang = np.degrees(np.arctan2(u[1], u[0]))
        if ang > 90.01:
            ang -= 180
        if ang <= -90.01:
            ang += 180
        mid = a1 + (a2 - a1) * tpos
        # el texto va del lado de "afuera" (lejos del objeto) => mismo signo que off
        nn = np.array([-np.sin(np.radians(ang)), np.cos(np.radians(ang))])  # normal "arriba" del texto
        side = sgn * tside
        to = 1.25 if textoff is None else textoff
        if np.dot(nn, n * side) >= 0:
            pos = mid + nn * to
            va = 'bottom'
        else:
            pos = mid - nn * to
            va = 'top'
        self.T(pos[0], pos[1], text, fs=fs, ha='center', va=va, rot=ang, tid=tid, bg=False)
        return tid

    def table(self, x, y, colw, rows, rowh=4.0, fs=FS_TAB, header=True, bold_first_col=False):
        tid0 = self.nid()
        n = len(rows)
        W_ = sum(colw)
        if header:
            self.P([(x, y), (x + W_, y), (x + W_, y - rowh), (x, y - rowh)], fc='#eeeeee',
                   ec='none', lw=0, z=1, chk=False)
        self.P([(x, y), (x + W_, y), (x + W_, y - n * rowh), (x, y - n * rowh)], lw=0.7,
               owner=tid0, chk=False)
        for i in range(1, n):
            self.L([x, x + W_], [y - i * rowh] * 2, lw=0.3, owner=tid0, chk=False)
        xx = x
        for w in colw[:-1]:
            xx += w
            self.L([xx, xx], [y, y - n * rowh], lw=0.3, owner=tid0, chk=False)
        for i, r in enumerate(rows):
            xx = x
            for j, (w, s) in enumerate(zip(colw, r)):
                b = (header and i == 0) or (bold_first_col and j == 0)
                t = self.T(xx + 1.0, y - (i + 0.5) * rowh, s, fs=fs, bold=b)
                self.fits.append((t, xx + 0.4, xx + w - 0.4))
                xx += w
        return y - n * rowh

    def concrete(self, pts, seed=1, dens=0.10, size=0.9, owner=None):
        """Patron de hormigon (triangulos y puntos) recortado al poligono (hoja mm)."""
        rng = np.random.default_rng(seed)
        poly = Path(np.asarray(pts))
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        area = SPoly(pts).area
        nn = int(area * dens) + 3
        segx, segy = [], []
        dx, dy = [], []
        for _ in range(nn * 3):
            px = rng.uniform(min(xs), max(xs))
            py = rng.uniform(min(ys), max(ys))
            if not poly.contains_point((px, py), radius=-size * 1.2):
                continue
            if rng.random() < 0.45:
                a = rng.uniform(0, 2 * np.pi)
                tri = [(px + size * 0.6 * np.cos(a + k * 2.1), py + size * 0.6 * np.sin(a + k * 2.1))
                       for k in range(3)]
                tri.append(tri[0])
                segx += [t[0] for t in tri] + [np.nan]
                segy += [t[1] for t in tri] + [np.nan]
            else:
                dx.append(px)
                dy.append(py)
            if len(dx) + len(segx) / 5 > nn:
                break
        self.ax.plot(segx, segy, lw=0.3, color='#555555', zorder=2)
        self.ax.plot(dx, dy, ls='none', marker='.', ms=0.6, color='#555555', zorder=2)
        p = self.P(pts, fc='#f2f2f2', ec='none', lw=0, z=1, chk=False, block=True, owner=owner)
        return p

    def ground(self, x0, x1, y, n=None, chk=True):
        self.L([x0, x1], [y, y], lw=LW, chk=chk)
        n = n or max(2, int((x1 - x0) / 3.0))
        xs, ys = [], []
        for k in range(n):
            xx = x0 + (k + 0.5) * (x1 - x0) / n
            xs += [xx, xx - 1.6, np.nan]
            ys += [y, y - 1.6, np.nan]
        self.L(xs, ys, lw=0.35, chk=False)

    def breakline(self, x0, y0, x1, y1, lw=LW_T, owner=None, chk=True, amp=1.4):
        p0 = np.array([x0, y0])
        p1 = np.array([x1, y1])
        d = p1 - p0
        L_ = np.hypot(*d)
        u = d / L_
        n = np.array([-u[1], u[0]])
        m = p0 + d * 0.5
        pts = [p0, m - u * 1.2, m - u * 0.4 + n * amp, m + u * 0.4 - n * amp, m + u * 1.2, p1]
        pts = np.array(pts)
        self.L(pts[:, 0], pts[:, 1], lw=lw, owner=owner, chk=chk)

    # ------------------------------------------------------------ finalizar y verificar
    def finalize(self):
        r = self.fig.canvas.get_renderer()
        self.fig.canvas.draw()
        for tid in self.vtitles:
            t = [d for d in self.texts if d['id'] == tid][0]['a']
            bb = t.get_window_extent(r)
            inv = self.ax.transData.inverted()
            (xa, ya), (xb, yb) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
            self.L([xa, xb], [ya - 1.0, ya - 1.0], lw=0.9, owner=tid)
            self.L([xa, xb], [ya - 1.8, ya - 1.8], lw=0.4, owner=tid)

    def check(self, verbose=True):
        r = self.fig.canvas.get_renderer()
        self.fig.canvas.draw()
        to_mm = self.ax.transData.inverted()
        boxes = []
        for d in self.texts:
            a = d['a']
            if not a.get_text().strip():
                continue
            bb = a.get_window_extent(r)
            # para textos rotados get_window_extent da caja envolvente: usar polígono real
            boxes.append((d, bb))
        issues = []
        # 1) texto-texto
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                di, bi = boxes[i]
                dj, bj = boxes[j]
                if di['id'] == dj['id']:
                    continue
                ox = min(bi.x1, bj.x1) - max(bi.x0, bj.x0)
                oy = min(bi.y1, bj.y1) - max(bi.y0, bj.y0)
                if ox > 0.5 and oy > 0.5:
                    issues.append(f"TXT-TXT: '{di['a'].get_text()[:40]}' <> '{dj['a'].get_text()[:40]}'")
        # 2) texto-linea
        geoms, owners = [], []
        for d in self.lines:
            if not d['chk']:
                continue
            a = d['a']
            try:
                if hasattr(a, 'get_xydata') and not hasattr(a, 'get_path') or a.__class__.__name__ == 'Line2D':
                    xy = a.get_transform().transform(a.get_xydata())
                    polys = [xy]
                else:
                    path = a.get_path().transformed(a.get_transform())
                    polys = path.to_polygons(closed_only=False)
            except Exception:
                continue
            for pl in polys:
                pl = np.asarray(pl)
                # cortar por NaN
                good = ~np.isnan(pl).any(axis=1)
                segs = []
                cur = []
                for k, g in enumerate(good):
                    if g:
                        cur.append(pl[k])
                    else:
                        if len(cur) > 1:
                            segs.append(cur)
                        cur = []
                if len(cur) > 1:
                    segs.append(cur)
                for s in segs:
                    geoms.append(LineString(s))
                    owners.append(d['owner'])
        tree = STRtree(geoms) if geoms else None
        areas = []
        for d in self.areas:
            a = d['a']
            try:
                path = a.get_path().transformed(a.get_transform())
                for pl in path.to_polygons():
                    if len(pl) >= 3:
                        areas.append((SPoly(pl).buffer(0), d['owner']))
            except Exception:
                pass
        for d, bb in boxes:
            if not d['chk']:
                continue
            a = d['a']
            rot = a.get_rotation()
            if abs(rot) > 0.1 and abs(abs(rot) - 90) > 0.1:
                # caja real rotada
                bbt = a.get_window_extent(r)
                g = sbox(bbt.x0 + 1.5, bbt.y0 + 1.5, bbt.x1 - 1.5, bbt.y1 - 1.5)
                # aproximación conservadora: usar caja reducida
            else:
                g = sbox(bb.x0 + 1.0, bb.y0 + 1.0, bb.x1 - 1.0, bb.y1 - 1.0)
            if tree is not None:
                for k in tree.query(g):
                    if owners[k] is not None and owners[k] == d['id']:
                        continue
                    if geoms[k].intersects(g):
                        issues.append(f"TXT-LIN: '{a.get_text()[:45]}'")
                        break
            for ag, ow in areas:
                if ow is not None and ow == d['id']:
                    continue
                if ag.intersects(g):
                    issues.append(f"TXT-AREA: '{a.get_text()[:45]}'")
                    break
            # fuera del marco / dentro del rotulo
            (xa, ya), (xb, yb) = to_mm.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
            if xa < FX0 + 0.5 or xb > FX1 - 0.5 or ya < FY0 + 0.5 or yb > FY1 - 0.5:
                issues.append(f"FUERA: '{a.get_text()[:45]}'")
            if not d['tb'] and xb > TBX0 and ya < TBY1 and yb > TBY0 and xa < TBX1:
                issues.append(f"ROTULO: '{a.get_text()[:45]}'")
        # 3) textos que no caben en su celda
        for tid, xmin, xmax in self.fits:
            if tid is None:
                continue
            t = [d for d in self.texts if d['id'] == tid]
            if not t:
                continue
            bb = t[0]['a'].get_window_extent(r)
            (xa, _), (xb, _) = to_mm.transform([(bb.x0, 0), (bb.x1, 0)])
            if xa < xmin - 0.2 or xb > xmax + 0.2:
                issues.append(f"NO CABE: '{t[0]['a'].get_text()[:45]}' ({xb - xmax:.1f} mm)")
        if verbose:
            print(f"[{self.code}] {len(issues)} problemas")
            for s in issues:
                print('   ', s)
        return issues

    def save(self, path_png, path_pdf=None):
        self.finalize()
        iss = self.check()
        self.fig.savefig(path_png, dpi=DPI)
        if path_pdf:
            self.fig.savefig(path_pdf)
        plt.close(self.fig)
        return iss


def _dark(fc):
    try:
        from matplotlib.colors import to_rgb
        r, g, b = to_rgb(fc)
        return (r + g + b) / 3 < 0.55
    except Exception:
        return False


class View:
    """Vista a escala: modelo en mm -> hoja en mm. X = ox + (x-mx)/N"""

    def __init__(self, sh, ox, oy, N, mx=0.0, my=0.0):
        self.sh, self.ox, self.oy, self.N, self.mx, self.my = sh, ox, oy, N, mx, my

    def p(self, x, y):
        return (self.ox + (x - self.mx) / self.N, self.oy + (y - self.my) / self.N)

    def X(self, x):
        return self.ox + (x - self.mx) / self.N

    def Y(self, y):
        return self.oy + (y - self.my) / self.N

    def pts(self, pts):
        return [self.p(*q) for q in pts]

    def L(self, pts, **kw):
        q = self.pts(pts)
        return self.sh.L([a[0] for a in q], [a[1] for a in q], **kw)

    def P(self, pts, **kw):
        return self.sh.P(self.pts(pts), **kw)

    def R(self, x, y, w, h, **kw):
        return self.P([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], **kw)

    def C(self, x, y, r, **kw):
        cx, cy = self.p(x, y)
        return self.sh.C(cx, cy, r / self.N, **kw)

    def dim(self, p1, p2, off, text=None, **kw):
        if text is None:
            text = fmt_mm(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))
        return self.sh.dim(self.p(*p1), self.p(*p2), off, text, **kw)

    def lead(self, x, y, tx, ty, s, **kw):
        px, py = self.p(x, y)
        return self.sh.lead(px, py, tx, ty, s, **kw)

    def concrete(self, pts, **kw):
        return self.sh.concrete(self.pts(pts), **kw)

    def cl(self, p1, p2, lw=LW_T, ext=0.0):
        """Linea de eje (trazo y punto)."""
        return self.L([p1, p2], lw=lw, ls=(0, (8, 2, 1.5, 2)), c='k', chk=False)

    # perfiles en corte -------------------------------------------------------------
    def ipn_like_tube(self, cx, y0, b, h, t, hatch='////', fc='white', **kw):
        """Tubo rectangular hueco en corte (cx centro, y0 base)."""
        o = [(cx - b / 2, y0), (cx + b / 2, y0), (cx + b / 2, y0 + h), (cx - b / 2, y0 + h)]
        i = [(cx - b / 2 + t, y0 + t), (cx + b / 2 - t, y0 + t), (cx + b / 2 - t, y0 + h - t),
             (cx - b / 2 + t, y0 + h - t)]
        verts = self.pts(o) + [self.pts(o)[0]] + self.pts(i)[::-1] + [self.pts(i)[::-1][0]]
        codes = [Path.MOVETO] + [Path.LINETO] * 3 + [Path.CLOSEPOLY] + [Path.MOVETO] + \
            [Path.LINETO] * 3 + [Path.CLOSEPOLY]
        from matplotlib.patches import PathPatch
        pp = PathPatch(Path(verts, codes), fc=fc, ec='k', lw=LW, hatch=hatch, zorder=3)
        self.sh.ax.add_patch(pp)
        self.sh.lines.append(dict(a=pp, owner=None, chk=True))
        self.sh.areas.append(dict(a=pp, owner=None))
        return pp
