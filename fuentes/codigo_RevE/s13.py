from lib import *
import data as D
from iso import Scene

C_COND = '#9fc0e6'
C_GATE = '#2f5f8f'
C_HEAD = '#3d6fa3'
C_YEL = '#f2c14e'
C_ELE = '#b8392b'
C_FOSA = '#6e6e6e'
C_COL = '#9a9a9a'
C_TAB = '#c4c4c4'
C_MACH = '#e3cfa8'
C_WALL = '#cdcdcd'
C_FLOOR = '#ececec'
C_WOODB = '#9c7a4f'
C_TUBO = '#666666'
S_ELEV = 37.40


def scene():
    sc = Scene()
    W = D.ANCHO
    # piso
    sc.box(-0.15, W + 0.15, -0.175, 36.325, -0.15, 0.0, C_FLOOR)
    # muros perimetrales (recortados al frente)
    def wall_x(x0, x1, s0, s1, h, step=1.5):
        ss = list(np.arange(s0, s1, step)) + [s1]
        for a, b in zip(ss[:-1], ss[1:]):
            sc.box(x0, x1, a, b, 0, h, C_WALL)

    def wall_s(s0, s1, x0, x1, h, step=1.5):
        xx = list(np.arange(x0, x1, step)) + [x1]
        for a, b in zip(xx[:-1], xx[1:]):
            sc.box(a, b, s0, s1, 0, h, C_WALL)
    wall_x(-0.15, 0.0, -0.175, 36.325, 1.20)
    wall_x(W, W + 0.15, -0.175, 36.325, 3.90)
    wall_s(-0.175, 0.175, 0.0, W, 3.90)
    wall_s(35.975, 36.325, 0.0, W, 1.20)
    # tabiques con suplemento
    tabs = [(8.975, 9.175), (13.475, 13.675), (17.975, 18.175), (26.975, 27.175)]
    for a, b in tabs:
        xx = list(np.arange(0, W, 1.5)) + [W]
        for x0, x1 in zip(xx[:-1], xx[1:]):
            sc.box(x0, x1, a, b, 0, 3.00, C_TAB)
        sc.xprism([(5.70, 3.00), (8.10, 3.00), (8.10, 3.90)], a, b, C_MACH)
        sc.box(8.10, W, a, b, 3.00, 3.90, C_MACH)
        sc.xprism([(7.40, 3.6375), (8.10, 3.90), (7.40, 3.90)], a - 0.001, b + 0.001, '#9a9a9a')
    # columnas intermedias y vigas longitudinales de madera
    for scol in [0.0, 9.075, 13.575, 18.075, 27.075, 36.15]:
        for xc in (D.X_C1, D.X_C2):
            sc.box(xc - 0.1, xc + 0.1, scol - 0.1, scol + 0.1, 0, 5.76, C_COL)
    for xc in (D.X_C1, D.X_C2):
        sc.box(xc - 0.075, xc + 0.075, -0.1, 36.25, 5.76, 6.06, C_WOODB)
    # lineas Redler
    for xl, sd in ((D.X_L1, 1), (D.X_L2, -1)):
        sc.box(xl - 0.1, xl + 0.1, 0.175, 37.975, D.TUBO_INF, D.TUBO_SUP, C_TUBO)
        sc.box(xl - 0.304, xl + 0.304, 1.27, 37.27, D.COND_INF, D.COND_SUP, C_COND)
        sc.box(xl - 0.34, xl + 0.34, 0.37, 1.27, 4.20, 5.40, C_HEAD)
        sc.box(xl + sd * 0.56, xl + sd * 0.88, 0.62, 1.02, 4.40, 4.95, C_HEAD)
        sc.box(xl - 0.34, xl + 0.34, 37.27, 38.17, 4.25, 5.25, C_HEAD)
        for sg in D.GATES.values():
            sc.box(xl - 0.30, xl + 0.30, sg - 0.175, sg + 0.175, 4.06, D.COND_INF, C_GATE)
        # pasarela + baranda
        xa, xb = xl + sd * 0.35, xl + sd * 1.264
        sc.box(xa, xb, 1.45, 36.15, 4.021, D.NPP, C_YEL)
        xr = xl + sd * 1.234
        for z in (D.PASAM - 0.025, 4.575):
            sc.box(xr - 0.025, xr + 0.025, 1.45, 36.15, z - 0.025, z + 0.025, C_YEL)
        for sp in np.arange(1.50, 36.16, 1.0):
            sc.box(xr - 0.025, xr + 0.025, sp - 0.025, sp + 0.025, D.NPP, D.PASAM, C_YEL)
    # plataforma exterior
    sc.box(6.9, 15.8, 36.325, 38.60, 4.02, 4.05, C_YEL)
    for sp in (37.0, 38.5):
        for xp in (7.0, 11.35, 15.7):
            if xp == 11.35 and sp < 38.2:
                continue
            sc.box(xp - 0.06, xp + 0.06, sp - 0.06, sp + 0.06, -0.20, 4.02, C_COL)
    for z in (D.PASAM - 0.025, 4.575):
        sc.box(6.9, 15.8, 38.55, 38.60, z - 0.025, z + 0.025, C_YEL)
        sc.box(15.75, 15.8, 36.325, 38.60, z - 0.025, z + 0.025, C_YEL)
    for xp in np.arange(6.95, 15.8, 1.0):
        sc.box(xp - 0.025, xp + 0.025, 38.55, 38.60, 4.05, D.PASAM, C_YEL)
    # escalera exterior (s 36,40-37,30; x 0,50 -> 6,90)
    def flight(x0, x1, z0, z1):
        n = int(round((z1 - z0) / 0.18))
        run = (x1 - x0) / n
        for i in range(n):
            zt = z0 + (i + 1) * (z1 - z0) / n
            sc.box(x0 + i * run, x0 + (i + 1) * run, 36.42, 37.28, zt - 0.04, zt, C_YEL)
        for ss in (36.42, 37.28):
            sc.bar((x0, ss, z0 - 0.1), (x1, ss, z1 - 0.1), 0.06, '#c99a2e')
    flight(0.50, 3.25, 0.0, 2.025)
    sc.box(3.25, 4.15, 36.42, 37.28, 1.985, 2.025, C_YEL)
    flight(4.15, 6.90, 2.025, 4.05)
    for xp in (3.30, 4.10):
        sc.box(xp - 0.05, xp + 0.05, 37.20, 37.30, 0, 1.985, C_COL)
    # fosa, tolva y tope
    sc.box(8.8, 13.9, 36.33, 42.3, -0.32, -0.21, '#d9d9d9')
    sc.box(9.60, 13.10, 36.45, 41.45, -0.30, -0.20, '#b5b5b5')
    sc.box(10.10, 12.60, 38.70, 40.70, -0.30, -0.19, C_FOSA)
    sc.box(12.00, 12.80, 36.75, 37.55, -0.30, -0.19, '#8c8c8c')
    sc.box(9.60, 13.10, 41.75, 41.95, -0.21, -0.06, '#8c8c8c')
    # elevador, desviador y chutes
    sc.box(D.X_ELEV - 0.365, D.X_ELEV + 0.365, S_ELEV - 0.61, S_ELEV + 0.61, -0.20, 9.60, C_ELE)
    sc.box(D.X_ELEV - 0.45, D.X_ELEV + 0.45, S_ELEV - 0.70, S_ELEV + 0.70, 9.60, 10.33, C_ELE)
    sc.box(D.X_ELEV - 0.30, D.X_ELEV + 0.30, S_ELEV - 0.55, S_ELEV - 0.05, 9.25, 9.60, '#8e2a20')
    for xl in (D.X_L1, D.X_L2):
        sg = 1 if xl > D.X_ELEV else -1
        sc.bar((D.X_ELEV + sg * 0.25, S_ELEV - 0.30, 9.35), (xl, 37.07, D.COND_SUP + 0.12), 0.26, '#8e2a20')
    return sc


def build(out):
    sh = Sheet('ISO-13', 'Vista axonométrica del sistema (esquemática)',
               'Muros perimetrales recortados y cubierta retirada para ver el interior · galpón sin producto',
               's/e', 14)
    sc = scene()
    umin, umax, vmin, vmax = sc.bounds()
    # encaje en la hoja
    X0, X1, Y0, Y1 = 62, 392, 66, 274
    k = min((X1 - X0) / (umax - umin), (Y1 - Y0) / (vmax - vmin))
    ox = X0 + ((X1 - X0) - k * (umax - umin)) / 2 - k * umin
    oy = Y0 + ((Y1 - Y0) - k * (vmax - vmin)) / 2 - k * vmin
    pxmm = 11.0
    img = sc.render(k * pxmm, (umin, umax, vmin, vmax))
    H, Wp = img.shape[:2]
    ex0 = ox + k * umin - 2 / pxmm
    ey1 = oy + k * vmax + 2 / pxmm
    sh.ax.imshow(img, extent=(ex0, ex0 + Wp / pxmm, ey1 - H / pxmm, ey1), zorder=2, interpolation='bilinear')

    def P(x, s, z):
        u, v = Scene.proj((x, s, z))
        return ox + k * u, oy + k * v

    FS = 5.4
    sh.lead(*P(D.X_L1, 12.0, D.COND_SUP), 115, 262, 'Redler L1', fs=FS, ha='right')
    sh.lead(*P(D.X_L2, 6.0, D.COND_SUP), 230, 262, 'Redler L2', fs=FS, ha='left')
    sh.lead(*P(D.X_L1 - 0.34, 0.8, 5.40), 85, 240, 'cabezales motrices (punto fijo)', fs=FS, ha='right')
    sh.lead(*P(D.X_C1 - 0.1, 18.075, 5.2), 88, 150, 'columnas C1 / C2 (4,00 m entre ejes)', fs=FS, ha='right')
    sh.lead(*P(4.0, 18.075, 3.00), 70, 175, 'tabiques H° + suplemento de machimbre (+3,90)', fs=FS, ha='right') \
        if False else None
    sh.lead(*P(D.X_L2 + 1.0, 30.0, D.NPP), 330, 205, 'pasarelas NPP +4,05 (baranda +5,15)', fs=FS, ha='left')
    sh.lead(*P(D.X_ELEV, S_ELEV, 10.33), 300, 240, 'elevador de cangilones (cabeza +10,33)', fs=FS, ha='left')
    sh.lead(*P(15.8, 38.0, 4.05), 366, 100, 'plataforma exterior\nNPP +4,05', fs=FS, ha='left')
    sh.lead(*P(1.5, 36.85, 0.6), 190, 74, 'escalera exterior', fs=FS, ha='right')
    sh.lead(*P(11.35, 39.7, -0.19), 292, 62, 'tolva en fosa (reja a nivel de terreno)', fs=FS, ha='right')
    sh.lead(*P(20.0, 27.175, 3.90), 350, 192, 'tabiques H° + suplemento (+3,90)', fs=FS, ha='left')

    # referencias
    sh.T(26, 74, 'REFERENCIAS', fs=6.2, bold=True)
    refs = [(C_COND, 'Redler L1 / L2 (conducto 600×400 doble)'),
            (C_GATE, 'compuertas + pantalón (11 por línea)'),
            (C_TUBO, 'viga carrilera tubo 300×200×10'),
            (C_YEL, 'pasarelas, plataforma exterior y escalera'),
            (C_ELE, 'elevador de cangilones + desviador y chutes'),
            (C_FOSA, 'tolva en fosa (reja a nivel de terreno)'),
            (C_COL, 'columnas intermedias existentes (4,00 m)'),
            (C_MACH, 'tabiques con suplemento de machimbre (+3,90)')]
    for i, (c, t) in enumerate(refs):
        y = 67 - i * 6.2
        sh.P([(26, y - 1.8), (34, y - 1.8), (34, y + 1.8), (26, y + 1.8)], fc=c, lw=0.4, chk=False)
        sh.T(36.5, y, t, fs=5.2)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/ISO-13')
