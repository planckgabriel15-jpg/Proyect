"""Mini motor axonometrico con z-buffer (caras convexas planas) -> imagen RGBA con aristas."""
import numpy as np
from matplotlib.colors import to_rgb

# proyeccion (x, s, z) -> (u, v)
PU = np.array([0.92, 0.80, 0.0])
PV = np.array([0.38, -0.55, 1.0])
DV = np.cross(PU, PV)            # direccion de vista (hacia el fondo)
SHADE = {(0, 0, 1): 1.00, (-1, 0, 0): 0.82, (0, 1, 0): 0.66, (0, 0, -1): 0.55, (1, 0, 0): 0.6, (0, -1, 0): 0.6}


class Scene:
    def __init__(self):
        self.faces = []   # (verts(n,3), rgb, tag)

    def face(self, verts, color, tag=None):
        self.faces.append((np.asarray(verts, float), np.array(to_rgb(color)), tag))

    def box(self, x0, x1, s0, s1, z0, z1, color, tag=None, top=None):
        x0, x1 = sorted((x0, x1)); s0, s1 = sorted((s0, s1)); z0, z1 = sorted((z0, z1))
        P = lambda x, s, z: (x, s, z)
        self.face([P(x0, s0, z1), P(x1, s0, z1), P(x1, s1, z1), P(x0, s1, z1)], top or color, tag)
        self.face([P(x0, s0, z0), P(x0, s1, z0), P(x1, s1, z0), P(x1, s0, z0)], color, tag)
        self.face([P(x0, s0, z0), P(x0, s0, z1), P(x0, s1, z1), P(x0, s1, z0)], color, tag)
        self.face([P(x1, s0, z0), P(x1, s1, z0), P(x1, s1, z1), P(x1, s0, z1)], color, tag)
        self.face([P(x0, s0, z0), P(x1, s0, z0), P(x1, s0, z1), P(x0, s0, z1)], color, tag)
        self.face([P(x0, s1, z0), P(x0, s1, z1), P(x1, s1, z1), P(x1, s1, z0)], color, tag)

    def prism(self, base, z0, z1, color, tag=None):
        """Prisma vertical de base poligonal convexa [(x,s),...]."""
        b = [(x, s, z0) for x, s in base]
        t = [(x, s, z1) for x, s in base]
        self.face(t, color, tag)
        self.face(b[::-1], color, tag)
        n = len(base)
        for i in range(n):
            j = (i + 1) % n
            self.face([b[i], b[j], t[j], t[i]], color, tag)

    def xprism(self, prof, s0, s1, color, tag=None):
        """Prisma con perfil convexo en el plano (x, z), extruido en s."""
        a = [(x, s0, z) for x, z in prof]
        b = [(x, s1, z) for x, z in prof]
        self.face(a, color, tag)
        self.face(b[::-1], color, tag)
        n = len(prof)
        for i in range(n):
            j = (i + 1) % n
            self.face([a[i], a[j], b[j], b[i]], color, tag)

    def bar(self, p0, p1, w, color, tag=None):
        """Barra de seccion cuadrada w entre p0 y p1."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0
        d /= np.linalg.norm(d)
        ref = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
        e1 = np.cross(d, ref); e1 /= np.linalg.norm(e1)
        e2 = np.cross(d, e1)
        h = w / 2
        c = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        A = [p0 + h * (a * e1 + b * e2) for a, b in c]
        B = [p1 + h * (a * e1 + b * e2) for a, b in c]
        self.face(A[::-1], color, tag)
        self.face(B, color, tag)
        for i in range(4):
            j = (i + 1) % 4
            self.face([A[i], A[j], B[j], B[i]], color, tag)

    # ------------------------------------------------------------------
    @staticmethod
    def proj(p):
        p = np.asarray(p, float)
        return p @ PU, p @ PV

    def bounds(self):
        allv = np.vstack([f[0] for f in self.faces])
        u, v = allv @ PU, allv @ PV
        return u.min(), u.max(), v.min(), v.max()

    def render(self, pxm, bnds, edge_rgb=(0.15, 0.15, 0.15)):
        """pxm: pixeles por unidad de modelo (m). Devuelve RGBA (H, W, 4)."""
        umin, umax, vmin, vmax = bnds
        W = int(np.ceil((umax - umin) * pxm)) + 4
        H = int(np.ceil((vmax - vmin) * pxm)) + 4
        zb = np.full((H, W), np.inf, np.float32)
        ib = np.full((H, W), -1, np.int32)
        cb = np.ones((H, W, 3), np.float32)
        for k, (V, rgb, tag) in enumerate(self.faces):
            n = np.cross(V[1] - V[0], V[2] - V[0])
            nn = np.linalg.norm(n)
            if nn < 1e-12:
                continue
            n = n / nn
            if n @ DV > -1e-6:      # cara de espaldas
                continue
            px = (V @ PU - umin) * pxm + 2
            py = (vmax - V @ PV) * pxm + 2
            dz = V @ DV
            x0, x1 = int(max(np.floor(px.min()), 0)), int(min(np.ceil(px.max()), W - 1))
            y0, y1 = int(max(np.floor(py.min()), 0)), int(min(np.ceil(py.max()), H - 1))
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            m = len(px)
            area = sum(px[i] * py[(i + 1) % m] - px[(i + 1) % m] * py[i] for i in range(m))
            if abs(area) < 1e-6:
                continue
            sg = 1 if area > 0 else -1
            inside = np.ones(gx.shape, bool)
            for i in range(m):
                j = (i + 1) % m
                cr = (px[j] - px[i]) * (gy - py[i]) - (py[j] - py[i]) * (gx - px[i])
                inside &= sg * cr >= -1e-9
            if not inside.any():
                continue
            # plano de profundidad
            Am = np.array([[px[0], py[0], 1], [px[1], py[1], 1], [px[2], py[2], 1]])
            try:
                a, b, c = np.linalg.solve(Am, dz[:3])
            except np.linalg.LinAlgError:
                continue
            d = a * gx + b * gy + c
            sub = zb[y0:y1 + 1, x0:x1 + 1]
            upd = inside & (d < sub - 1e-5)
            sub[upd] = d[upd]
            ib[y0:y1 + 1, x0:x1 + 1][upd] = k
            key = tuple(int(round(t)) for t in n)
            f = SHADE.get(key, 0.75)
            cb[y0:y1 + 1, x0:x1 + 1][upd] = np.clip(rgb * f + (1 - f) * 0.0, 0, 1)
        # aristas por cambio de cara
        e = np.zeros((H, W), bool)
        e[:, 1:] |= ib[:, 1:] != ib[:, :-1]
        e[1:, :] |= ib[1:, :] != ib[:-1, :]
        e2 = e.copy()
        e2[:, 1:] |= e[:, :-1]
        e2[1:, :] |= e[:-1, :]
        img = np.zeros((H, W, 4), np.float32)
        img[..., :3] = cb
        img[..., 3] = (ib >= 0).astype(np.float32)
        img[e2 & ((ib >= 0) | np.roll(ib >= 0, 1, 0) | np.roll(ib >= 0, 1, 1)), :3] = edge_rgb
        img[e2, 3] = 1.0
        return img
