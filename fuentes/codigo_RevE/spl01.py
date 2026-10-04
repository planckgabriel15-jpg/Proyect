from lib import *
import data as D

S_ELEV = 37.40
FOSA = (36.70, 41.20, 9.85, 12.85)   # s0, s1, x0, x1 (interior)
PLAT = (36.325, 38.60, 6.90, 15.80)
ESC = (36.40, 37.30, 0.50, 6.90)


def build(out):
    sh = Sheet('PL-01', 'Planta general de distribución',
               'Columnas intermedias a 4,00 m entre ejes · L1/L2 junto a las pasarelas · galpón sin producto',
               '1:125', 2)
    FS = 5.0
    v = View(sh, 40, 76, 125)   # X = s (m*1000), Y = x (m*1000)

    def S(s):
        return s * 1000

    def R(s0, s1, x0, x1, **kw):
        return v.R(S(s0), S(x0), S(s1 - s0), S(x1 - x0), **kw)

    # ---------------- edificio ----------------
    sw = [(-0.175, 0.175), (35.975, 36.325)]
    tabs = [(8.975, 9.175), (13.475, 13.675), (17.975, 18.175), (26.975, 27.175)]
    R(-0.175, 36.325, -0.15, 0.0, fc=C_EXIST, lw=0.5)
    R(-0.175, 36.325, 22.70, 22.85, fc=C_EXIST, lw=0.5)
    for a, b in sw:
        R(a, b, -0.15, 22.85, fc=C_EXIST, lw=0.5)
    for a, b in tabs:
        # tabique sin suplemento (x<5,70) y pendiente
        R(a, b, 0.0, 5.70, fc='#f2f2f2', lw=0.4)
        R(a, b, 5.70, 22.70, fc=C_EXIST, lw=0.4)
    # portones (muro oeste)
    for a, b in [(0.175, 8.975), (9.175, 13.475), (13.675, 17.975), (18.175, 26.975), (27.175, 35.975)]:
        m = (a + b) / 2
        w = min(3.5, (b - a) * 0.6)
        R(m - w / 2, m + w / 2, -0.15, 0.0, fc='white', lw=0.4, ls=(0, (3, 2)))
    # columnas
    lines_s = [0.0, 9.075, 13.575, 18.075, 27.075, 36.15]
    for sc in lines_s:
        for xc in (D.X_C1, D.X_C2):
            R(sc - 0.1, sc + 0.1, xc - 0.1, xc + 0.1, fc=C_DARK, lw=0.3)
        for xc in (-0.075, 22.775):
            R(sc - 0.1, sc + 0.1, xc - 0.1, xc + 0.1, fc=C_DARK, lw=0.3)
    v.L([(S(0), S(D.X_C1)), (S(36.15), S(D.X_C1))], lw=0.4, ls=(0, (6, 2, 1, 2)), chk=False)
    v.L([(S(0), S(D.X_C2)), (S(36.15), S(D.X_C2))], lw=0.4, ls=(0, (6, 2, 1, 2)), chk=False)

    # ---------------- pasarelas ----------------
    def grate(s0, s1, x0, x1, step=0.5):
        xs, ys = [], []
        for ss in np.arange(s0, s1, step):
            xs += [v.X(S(ss)), v.X(S(ss)), np.nan]
            ys += [v.Y(S(x0)), v.Y(S(x1)), np.nan]
        for xx in np.arange(x0, x1, step):
            xs += [v.X(S(s0)), v.X(S(s1)), np.nan]
            ys += [v.Y(S(xx)), v.Y(S(xx)), np.nan]
        sh.L(xs, ys, lw=0.15, c='#a0a0a0', chk=False, z=1)
        R(s0, s1, x0, x1, fc='none', lw=0.4)

    grate(1.45, 36.15, D.X_L1 + 0.35, D.X_L1 + 1.264)
    grate(1.45, 36.15, D.X_L2 - 1.264, D.X_L2 - 0.35)
    # ---------------- lineas Redler ----------------
    for xl, side, pre in ((D.X_L1, 1, '1'), (D.X_L2, -1, '2')):
        R(1.27, 37.27, xl - 0.304, xl + 0.304, fc=C_NEW, lw=0.6)
        for b in D.BRIDAS + [37.27]:
            v.L([(S(b), S(xl - 0.304)), (S(b), S(xl + 0.304))], lw=0.25)
        # cabezal y motor
        R(0.37, 1.27, xl - 0.34, xl + 0.34, fc=C_NEW2, lw=0.6)
        R(0.62, 1.02, xl + side * 0.56, xl + side * 0.88, fc='#9fb3c8', lw=0.4) if side > 0 else \
            R(0.62, 1.02, xl - 0.88, xl - 0.56, fc='#9fb3c8', lw=0.4)
        mx_ = xl + side * 0.72
        # cola
        R(37.27, 38.17, xl - 0.34, xl + 0.34, fc=C_NEW2, lw=0.6)
        # compuertas
        for n, sg in D.GATES.items():
            R(sg - 0.175, sg + 0.175, xl - 0.30, xl + 0.30, fc='white', lw=0.5)
            v.L([(S(sg - 0.175), S(xl - 0.30)), (S(sg + 0.175), S(xl + 0.30))], lw=0.4)
            v.L([(S(sg - 0.175), S(xl + 0.30)), (S(sg + 0.175), S(xl - 0.30))], lw=0.4)
            yl = xl - side * 0.75
            sh.T(v.X(S(sg)), v.Y(S(yl)), f'{pre}.{n:02d}', fs=4.4, ha='center', c='#1f4e79', bold=True)
        # flecha de flujo
        sh.ax.annotate('', xy=v.p(S(31.6), S(xl)), xytext=v.p(S(34.4), S(xl)),
                       arrowprops=dict(arrowstyle='-|>', color='#1f4e79', lw=0.8))
        v.cl((S(-1.2), S(xl)), (S(38.6), S(xl)))
    # ---------------- exterior: plataforma, escalera, elevador, fosa ----------------
    grate(PLAT[0], PLAT[1], PLAT[2], PLAT[3])
    R(*ESC, fc='white', lw=0.5)
    for xx in np.arange(ESC[2] + 0.25, ESC[3] - 0.1, 0.25):
        if abs(xx - 3.7) < 0.45:
            continue
        v.L([(S(ESC[0]), S(xx)), (S(ESC[1]), S(xx))], lw=0.25)
    R(ESC[0], ESC[1], 3.25, 4.15, fc='#eeeeee', lw=0.4)
    sh.T(v.X(S(36.85)), v.Y(S(3.70)), 'descanso', fs=3.8, ha='center', rot=90)
    # fosa
    f0, f1, fx0, fx1 = FOSA
    R(f0 - 0.25, f1 + 0.25, fx0 - 0.25, fx1 + 0.25, fc=C_EXIST, lw=0.5)
    R(f0, f1, fx0, fx1, fc='white', lw=0.5)
    R(38.70, 40.70, D.X_ELEV - 1.25, D.X_ELEV + 1.25, fc='none', lw=0.6)
    xs, ys = [], []
    for xx in np.arange(D.X_ELEV - 1.20, D.X_ELEV + 1.25, 0.10):
        xs += [v.X(S(38.72)), v.X(S(40.68)), np.nan]
        ys += [v.Y(S(xx)), v.Y(S(xx)), np.nan]
    sh.L(xs, ys, lw=0.2, chk=False)
    R(38.2, 40.9, D.X_ELEV - 0.40, D.X_ELEV + 0.40, fc='none', lw=0.4, ls=(0, (3, 2)))
    R(40.75, 41.15, fx0 + 0.1, fx0 + 0.9, fc='none', lw=0.4, ls=(0, (3, 2)))
    R(36.75, 37.55, 12.00, 12.80, fc='white', lw=0.5)
    v.L([(S(41.75), S(fx0 - 0.4)), (S(41.75), S(fx1 + 0.4))], lw=1.6)
    # elevador
    R(S_ELEV - 0.61, S_ELEV + 0.61, D.X_ELEV - 0.365, D.X_ELEV + 0.365, fc='#d9a49a', lw=0.7)
    # chutes
    for xl in (D.X_L1, D.X_L2):
        v.L([(S(S_ELEV), S(D.X_ELEV + (0.37 if xl > D.X_ELEV else -0.37))), (S(37.07), S(xl))], lw=1.2)
    # camion (contorno)
    R(42.2, 45.5, D.X_ELEV - 1.25, D.X_ELEV + 1.25, fc='none', lw=0.4, ls=(0, (4, 2)))
    # ---------------- cotas ----------------
    chain = [-0.175, 0.175, 8.975, 9.175, 13.475, 13.675, 17.975, 18.175, 26.975, 27.175, 35.975, 36.325]
    labs = ['0,35', '8,80', '0,20', '4,30', '0,20', '4,30', '0,20', '8,80', '0,20', '8,80', '0,35']
    for a, b, t in zip(chain[:-1], chain[1:], labs):
        small = b - a < 1
        v.dim((S(a), S(22.85)), (S(b), S(22.85)), 4, t, fs=3.6 if small else FS,
              tpos=0.5)
    v.dim((S(-0.175), S(22.85)), (S(36.325), S(22.85)), 10, '36,50 (exterior)', fs=FS)
    xc = [0.0, D.X_L1, D.X_C1, D.X_C2, D.X_L2, D.ANCHO]
    xl_ = ['7,90', '1,45', '4,00', '1,45', '7,90']
    for a, b, t in zip(xc[:-1], xc[1:], xl_):
        v.dim((S(-0.175), S(a)), (S(-0.175), S(b)), 6, t, fs=FS)
    v.dim((S(-0.175), S(0)), (S(-0.175), S(D.ANCHO)), 13, '22,70 (interior)', fs=FS)
    # ---------------- textos ----------------
    boxes = [('BOX 5', 'grande · 8,80 × 22,70 m', 4.575), ('BOX 4', 'chico · 4,30 × 22,70 m', 11.325),
             ('BOX 3', 'chico · 4,30 × 22,70 m', 15.825), ('BOX 2', 'grande · 8,80 × 22,70 m', 22.575),
             ('BOX 1', 'grande · 8,80 × 22,70 m', 31.575)]
    for nm, dsc, sm in boxes:
        sh.T(v.X(S(sm)), v.Y(S(4.0)), nm, fs=7.0, ha='center', bold=True, c='#555555')
        sh.T(v.X(S(sm)), v.Y(S(2.9)), dsc, fs=4.6, ha='center', c='#555555')
        sh.T(v.X(S(sm)), v.Y(S(19.5)), nm, fs=7.0, ha='center', bold=True, c='#999999')
    sh.T(v.X(S(18.0)), v.Y(S(-1.15)), 'MURO OESTE — FRENTE DE PORTONES (un portón por box)', fs=4.8, ha='center',
         bold=True, c='#555555')
    sh.T(v.X(S(4.0)), v.Y(S(22.0)), 'MURO ESTE (fondo de boxes)', fs=4.8, ha='center', bold=True, c='#555555')
    sh.T(v.X(S(0.75)), v.Y(S(11.35)), 'CABECERA NORTE', fs=4.6, ha='center', rot=90, bold=True, c='#555555')
    sh.T(v.X(S(36.9)), v.Y(S(20.0)), 'CABECERA SUR — RECEPCIÓN', fs=4.6, ha='center', rot=90, bold=True,
         c='#555555')
    sh.lead(*v.p(S(19.5), S(D.X_L2)), v.X(S(18.7)), v.Y(S(16.2)), 'Redler L2 — conducto 600×400 doble compartimiento',
            fs=FS, ha='left')
    sh.lead(*v.p(S(19.5), S(D.X_L1)), v.X(S(18.7)), v.Y(S(6.5)), 'Redler L1 — conducto 600×400 doble compartimiento',
            fs=FS, ha='left')
    sh.lead(*v.p(S(2.0), S(D.X_L2 - 0.8)), v.X(S(1.6)), v.Y(S(12.4)), 'Pasarela L2 (rejilla, paso libre 0,90 m)',
            fs=FS, ha='left')
    sh.lead(*v.p(S(2.0), S(D.X_L1 + 0.8)), v.X(S(1.6)), v.Y(S(10.3)), 'Pasarela L1 (rejilla, paso libre 0,90 m)',
            fs=FS, ha='left')
    sh.lead(*v.p(S(18.075), S(D.X_C1)), v.X(S(18.7)), v.Y(S(11.35)), 'Columnas intermedias existentes (4,00 m entre ejes)',
            fs=FS, ha='left')
    sh.lead(*v.p(S(0.82), S(D.X_L1 + 0.72)), v.X(S(2.2)), v.Y(S(5.4)), 'Cabezal motriz + motorreductor (L1 y L2)',
            fs=FS, ha='left')
    sh.labels([(v.X(S(37.0)), v.Y(S(15.6)), 'Plataforma exterior NPP +4,05', v.Y(S(21.5))),
               (v.X(S(S_ELEV + 0.5)), v.Y(S(D.X_ELEV + 0.2)), 'Elevador de cangilones (DET-10)', v.Y(S(20.0))),
               (v.X(S(39.7)), v.Y(S(D.X_ELEV + 1.2)), 'Tolva en fosa (DET-11)', v.Y(S(18.5))),
               (v.X(S(39.0)), v.Y(S(D.X_ELEV + 0.4)), 'Alimentador de banda (bajo tapa)', v.Y(S(17.0))),
               (v.X(S(41.75)), v.Y(S(fx1 + 0.3)), 'Tope de ruedas', v.Y(S(15.5))),
               (v.X(S(37.72)), v.Y(S(D.X_L1 - 0.2)), 'Cola tensora L1 / L2', v.Y(S(6.5))),
               (v.X(S(37.6)), v.Y(S(9.6)), 'Desviador 2 vías + chutes a 45°', v.Y(S(5.0))),
               (v.X(S(36.85)), v.Y(S(1.2)), 'Escalera de acceso', v.Y(S(3.5)))],
              v.X(S(42.0)), ha='left', fs=FS, sp=5.0)
    sh.T(v.X(S(43.85)), v.Y(S(D.X_ELEV)), 'camión batea', fs=4.4, ha='center', c='#777777')
    # ---------------- llamadas de detalle ----------------
    def call(s_, x_, r_, code, lab_s, lab_x):
        cx, cy = v.p(S(s_), S(x_))
        sh.C(cx, cy, r_, fc='none', lw=0.5, ls=(0, (3, 2)))
        bx, by = v.p(S(lab_s), S(lab_x))
        tid = sh.nid()
        d = np.array([bx - cx, by - cy])
        dd = np.hypot(*d)
        p0 = np.array([cx, cy]) + d / dd * r_
        p1 = np.array([bx, by]) - d / dd * 3.4
        sh.L([p0[0], p1[0]], [p0[1], p1[1]], lw=LW_T, owner=tid)
        sh.C(bx, by, 3.4, fc='white', lw=0.7, owner=tid, z=6)
        sh.L([bx - 3.4, bx + 3.4], [by, by], lw=0.4, owner=tid, z=7)
        sh.T(bx, by + 1.5, 'D' + code[-2:].lstrip('0'), fs=4.6, ha='center', bold=True, tid=tid, z=8)
        sh.T(bx, by - 1.5, code, fs=3.4, ha='center', tid=tid, z=8)
    call(0.8, D.X_L2, 5.0, 'DET-05', 2.0, 18.6)
    call(15.77, D.X_L2, 3.0, 'DET-06', 18.75, 17.8)
    call(13.575, D.X_L1, 3.0, 'DET-07', 13.0, 2.0)
    call(36.15, D.X_L1, 4.5, 'DET-08', 33.6, 2.4)
    call(6.5, D.X_L1 + 0.8, 3.0, 'DET-09', 7.3, 4.6)

    # ---------------- cortes ----------------
    sA = 36.15 - 9.30
    v.L([(S(sA), S(-1.4)), (S(sA), S(24.0))], lw=0.6, ls=(0, (8, 2, 1, 2)), chk=False)
    for xx, yy in ((sA, 24.0), (sA, -1.4)):
        px, py = v.p(S(xx), S(yy))
        sh.L([px, px], [py - (2.5 if yy < 0 else -2.5) * 0, py], lw=1.4)
        sh.ax.annotate('', xy=(px - 4, py), xytext=(px, py), arrowprops=dict(arrowstyle='-|>', lw=1.0, color='k'))
        sh.T(px + 1.5, py + (2.6 if yy > 0 else -2.6), 'A', fs=7, bold=True, ha='left')
    for (xx, yy) in ((-1.0, D.X_L1), (45.6, D.X_ELEV)):
        px, py = v.p(S(xx), S(yy))
        sh.ax.annotate('', xy=(px, py - 4), xytext=(px, py), arrowprops=dict(arrowstyle='-|>', lw=1.0, color='k'))
        sh.T(px + 1.2, py - 5.5, 'B', fs=7, bold=True, ha='left')
    # norte
    nx, ny = 392, 268
    sh.C(nx, ny, 4.5, fc='white', lw=0.6, z=3)
    sh.P([(nx - 4.5, ny), (nx + 3, ny + 1.6), (nx + 1.5, ny), (nx + 3, ny - 1.6)], fc='k', lw=0.3, z=5)
    sh.T(nx - 7.5, ny, 'N', fs=8, bold=True, ha='center')
    # ---------------- referencias ----------------
    sh.T(24, 46, 'REFERENCIAS', fs=6.0, bold=True)
    refs = [(C_EXIST, 'Construcción existente (muros, tabiques e = 0,20)'),
            (C_DARK, 'Columna existente'),
            ('#f2f2f2', 'Tabique sin suplemento (+3,00) / pendiente 2,40 m (ver DET-12)'),
            (C_NEW, 'Conducto Redler (nuevo)'),
            ('white', 'Pasarela / plataforma de rejilla (nueva)'),
            ('#d9a49a', 'Elevador de cangilones')]
    for i, (c, t) in enumerate(refs):
        y = 41 - i * 4.6
        x = 24 if i < 3 else 120
        y = 41 - (i % 3) * 4.6
        sh.P([(x, y - 1.4), (x + 7, y - 1.4), (x + 7, y + 1.4), (x, y + 1.4)], fc=c, lw=0.4)
        sh.T(x + 9, y, t, fs=4.8)
    x, y = 120 + 0, 41 - 3 * 4.6
    sh.P([(x, y - 1.4), (x + 7, y - 1.4), (x + 7, y + 1.4), (x, y + 1.4)], fc='white', lw=0.4)
    sh.L([x, x + 7], [y - 1.4, y + 1.4], lw=0.4)
    sh.L([x, x + 7], [y + 1.4, y - 1.4], lw=0.4)
    sh.T(x + 9, y, 'Compuerta guillotina (n.º línea.orden)', fs=4.8)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/PL-01')
