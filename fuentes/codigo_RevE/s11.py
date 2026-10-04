from lib import *
import data as D

FS = 5.0
S_ELEV = 37.40
DASH = (0, (3, 2))
C_MAT = '#efe3c4'
C_EL = '#e8c4bd'
C_EL2 = '#d9a49a'

# geometria (s en m desde muro norte del galpon, z en m)
S_TC, S_TM = 40.75, 38.35          # tambor de cola / motriz
Z_TB = -2.35                        # eje tambores
R_TB = 0.15


def upn_pts(uw, ztop, d=1, h=200, b=75, tw=8.5, tf=11.5):
    """UPN en corte: uw = cara exterior del alma (mm), d = sentido de las alas (+1/-1)."""
    zb = ztop - h
    return [(uw, ztop), (uw + d * b, ztop), (uw + d * b, ztop - tf), (uw + d * tw, ztop - tf),
            (uw + d * tw, zb + tf), (uw + d * b, zb + tf), (uw + d * b, zb), (uw, zb)]


def build(out):
    sh = Sheet('DET-11', 'Tolva de recepción en fosa y alimentador de banda',
               'Buffer 3,70 m³ · alimentador de banda 800 con variador · descarga a la bota del elevador',
               '1:30 / 1:50 / 1:10', 12)
    # ===================== A — CORTE LONGITUDINAL 1:30 =====================
    sh.vtitle(24, 276, 'A — CORTE LONGITUDINAL POR EL EJE DE LA FOSA   Esc. 1:30')
    v = View(sh, 62, 232, 30)

    def U(s):
        return (41.45 - s) * 1000

    def P(s, z):
        return (U(s), z * 1000)

    def R(s0, s1, z0, z1, **kw):
        return v.P([P(s0, z0), P(s1, z0), P(s1, z1), P(s0, z1)], **kw)

    def X(s):
        return v.X(U(s))

    def Y(z):
        return v.Y(z * 1000)

    # --- fosa de H°A°
    walls = [[P(41.45, -3.40), P(41.20, -3.40), P(41.20, -0.20), P(41.45, -0.20)],
             [P(36.70, -3.40), P(36.45, -3.40), P(36.45, -0.20), P(36.70, -0.20)],
             [P(36.45, -3.65), P(40.65, -3.65), P(40.65, -3.85), P(41.45, -3.85), P(41.45, -3.40),
              P(41.15, -3.40), P(41.15, -3.60), P(40.75, -3.60), P(40.75, -3.40), P(36.45, -3.40)]]
    for i, w in enumerate(walls):
        v.concrete(w, seed=i + 2)
        v.P(w, fc='none', lw=LW)
    sh.ground(X(42.35), X(41.45), Y(-0.20))
    sh.ground(X(36.45), X(36.05), Y(-0.20))
    # L embutidos en coronamiento (apoyo de tapa)
    for s0, s1 in ((41.20, 41.25), (36.70, 36.65)):
        R(min(s0, s1), max(s0, s1), -0.25, -0.207, fc='k', lw=0.2)

    # --- vigas UPN 200 + marco L50 + tolva
    for uw, d in ((U(38.655), 1), (U(40.745), -1)):
        v.P(upn_pts(uw, -206.4, d), fc=C_STEEL, lw=0.5)
        L = [(uw - d * 50, -257), (uw, -257), (uw, -207), (uw - d * 5, -207), (uw - d * 5, -252),
             (uw - d * 50, -252)]
        v.P(L, fc='k', lw=0.2)
    v.P([P(40.70, -0.257), P(38.70, -0.257), P(39.45, -1.90), P(39.95, -1.90)], fc='#f4f4f4', ec='none', lw=0)
    v.L([P(40.70, -0.257), P(39.95, -1.90)], lw=1.1)
    v.L([P(38.70, -0.257), P(39.45, -1.90)], lw=1.1)
    # brida de boca
    R(39.95, 40.02, -1.91, -1.90, fc='k', lw=0.2)
    R(39.38, 39.45, -1.91, -1.90, fc='k', lw=0.2)
    # anillos de refuerzo L40 c/600
    ring_pts = []
    for zz in (-0.857, -1.457):
        t = (-0.257 - zz) / 1.643
        for s_top, s_bot, sg in ((40.70, 39.95, -1), (38.70, 39.45, 1)):
            ss = s_top + (s_bot - s_top) * t
            cx, cy = v.p(*P(ss, zz))
            cx += sg * 0.9 * (1 if sg > 0 else 1)
            sh.P([(cx - 0.65, cy - 0.65), (cx + 0.65, cy - 0.65), (cx + 0.65, cy + 0.65), (cx - 0.65, cy + 0.65)],
                 fc='k', lw=0.2)
            ring_pts.append((cx, cy))
    # reja de gruesos (barra vista en largo)
    R(38.662, 40.738, -0.252, -0.202, fc='white', lw=0.5)
    # sensor ultrasonico bajo el marco norte
    R(38.71, 38.79, -0.36, -0.26, fc='#9fb3c8', lw=0.4)
    # tapa de chapa
    for s0, s1 in ((41.20, 40.825), (38.575, 38.015), (36.785, 36.70)):
        v.L([P(s0, -0.203), P(s1, -0.203)], lw=1.4)

    # --- compuerta manual de guillotina en la boca
    R(39.40, 40.00, -1.97, -1.91, fc='white', lw=0.5)
    R(39.42, 40.32, -1.945, -1.935, fc='k', lw=0.2)
    v.L([P(40.32, -1.90), P(40.32, -1.98)], lw=1.0)
    # --- material sobre la banda
    v.P([P(39.98, -2.20), P(39.98, -1.98), P(39.07, -1.98), P(39.07, -2.04), P(38.42, -2.04),
         P(S_TM, -2.20)], fc=C_MAT, lw=0.3, z=2)
    # faldones (vista mas alla del corte)
    R(39.05, 40.00, -2.18, -1.97, fc='none', lw=0.5)
    # compuerta reguladora de lecho
    R(39.035, 39.055, -2.04, -1.85, fc='k', lw=0.2)
    # --- tolvin de descarga a la bota
    v.P([P(38.55, -2.05), P(38.05, -2.05), P(38.05, -2.90), P(38.25, -2.60), P(38.55, -2.60)],
        fc='#dddddd', lw=0.6, z=1)
    # rascador
    v.L([P(38.27, -2.47), P(38.18, -2.56)], lw=0.9)
    # --- banda, tambores, rodillos
    v.L([P(S_TC, -2.20), P(S_TM, -2.20)], lw=0.9, z=4)
    v.L([P(S_TC, -2.50), P(S_TM, -2.50)], lw=0.9, z=4)
    for sd in (S_TC, S_TM):
        cx, cy = v.p(*P(sd, Z_TB))
        sh.C(cx, cy, R_TB * 1000 / 30, fc='white', lw=0.7, z=4)
        sh.C(cx, cy, 0.5, fc='k', lw=0.2, z=5)
    for sr in np.arange(38.75, 40.51, 0.25):
        cx, cy = v.p(*P(sr, -2.245))
        sh.C(cx, cy, 1.45, fc='white', lw=0.35, z=4)
    cx, cy = v.p(*P(39.55, -2.545))
    sh.C(cx, cy, 1.45, fc='white', lw=0.35, z=4)
    ret_roller = (cx, cy)
    # tensor a tornillo del tambor de cola
    v.L([P(S_TC, Z_TB), P(41.08, Z_TB)], lw=0.6)
    R(41.00, 41.10, -2.40, -2.30, fc=C_STEEL, lw=0.4)
    # bastidor
    R(38.60, 40.95, -2.66, -2.56, fc=C_STEEL, lw=0.4)
    for sl in (40.85, 39.60, 38.65):
        R(sl - 0.03, sl + 0.03, -3.40, -2.66, fc=C_STEEL, lw=0.3)
        R(sl - 0.08, sl + 0.08, -3.40, -3.388, fc='k', lw=0.2)
    # --- elevador: bota + cuerpo
    R(36.75, 38.05, -3.30, -2.30, fc=C_EL2, lw=0.7)
    cx, cy = v.p(*P(S_ELEV, -2.85))
    sh.C(cx, cy, 317 / 30, fc='none', lw=0.5)
    sh.C(cx, cy, 0.5, fc='k', lw=0.2)
    bota_c = (cx, cy)
    R(36.79, 38.01, -2.30, 0.60, fc=C_EL, lw=0.7)
    for ss in (S_ELEV - 0.317, S_ELEV + 0.317):
        v.L([P(ss, -2.85), P(ss, 0.60)], lw=0.35, ls=DASH)
    R(38.01, 38.04, -0.20, -0.12, fc='k', lw=0.2)
    R(36.76, 36.79, -0.20, -0.12, fc='k', lw=0.2)
    sh.breakline(X(38.12), Y(0.60), X(36.68), Y(0.60))
    # --- sumidero y bomba
    R(40.86, 41.04, -3.58, -3.32, fc='#888888', lw=0.4)
    v.L([P(40.95, -3.32), P(40.95, -3.20), P(41.13, -3.20), P(41.13, -0.45), P(41.45, -0.45)], lw=0.9)
    # llamada detalle D
    dcx, dcy = v.p(*P(38.64, -0.31))
    sh.C(dcx, dcy, 6.5, fc='none', lw=0.5, ls=(0, (4, 2)))
    sh.T(dcx + 7.5, dcy + 6.0, 'D', fs=7.0, bold=True)

    # --- cotas
    for a, b, t in ((41.45, 41.20, '0,25'), (41.20, 36.70, '4,50 (interior)'), (36.70, 36.45, '0,25')):
        v.dim(P(a, -3.85), P(b, -3.85), -5, t, fs=FS)
    v.dim(P(40.70, -0.20), P(38.70, -0.20), 5, '2.000', fs=FS, ext0=1.6)
    v.dim(P(S_TC, Z_TB), P(S_TM, Z_TB), -(Z_TB + 3.10) * 1000 / 30, '2,40 entre ejes', fs=FS, tpos=0.66,
          ext0=5.6)
    v.dim(P(36.45, -0.20), P(36.45, -3.40), 6, '3,20', fs=FS)
    sh.T(X(39.25), Y(-1.15), '66°', fs=FS, ha='center')
    sh.T(X(38.80), Y(-2.12) + 3.4, 'h = 160', fs=4.6, ha='center')
    for z, t in [(-0.20, '−0,20 NTN / reja'), (-1.90, '−1,90 boca tolva'), (-2.20, '−2,20 banda'),
                 (-2.75, '−2,75 boca bota'), (-3.40, '−3,40 piso fosa')]:
        sh.lev(39, Y(z), t, side='right', ln=16, fs=4.8)

    # --- globos
    pr = lambda s, z: v.p(*P(s, z))
    t_s = lambda zz, top, bot: top + (bot - top) * ((-0.257 - zz) / 1.643)
    sh.balloons([
        (1, pr(39.90, -0.227), (X(39.90), 245)),
        (16, pr(38.30, -0.203), (X(38.30), 242)),
        (19, pr(41.32, -1.00), (49, 200)),
        (4, pr(t_s(-1.20, 40.70, 39.95), -1.20), (82, 205)),
        (7, pr(40.32, -1.94), (86, 181)),
        (11, pr(S_TC - 0.10, Z_TB + 0.08), (77.5, 165)),
        (6, pr(38.75, -0.31), (166, 214)),
        (5, ring_pts[1], (166, 204)),
        (8, pr(39.045, -1.90), (166, 190)),
        (10, pr(S_TM, Z_TB), (159, 177)),
        (9, pr(40.10, -2.50), (98, 137)),
        (12, ret_roller, (135, 137)),
        (13, pr(39.10, -2.66), (146, 137)),
        (14, pr(38.13, -2.78), (170, 123)),
        (15, bota_c, (197, 175)),
        (18, pr(40.95, -3.45), (52, 107)),
    ])

    # ===================== B — PLANTA DE LA FOSA 1:50 =====================
    sh.vtitle(240, 276, 'B — PLANTA DE LA FOSA   Esc. 1:50')
    vb = View(sh, 268, 224, 50)

    def Q(s, x):
        return ((41.45 - s) * 1000, (x - D.X_ELEV) * 1000)

    def RB(s0, s1, x0, x1, **kw):
        return vb.P([Q(s0, x0), Q(s1, x0), Q(s1, x1), Q(s0, x1)], **kw)
    wall_o = [Q(41.45, 9.60), Q(36.45, 9.60), Q(36.45, 13.10), Q(41.45, 13.10)]
    vb.concrete(wall_o, seed=5)
    RB(41.45, 36.45, 9.60, 13.10, fc='none', lw=0.6)
    RB(41.20, 36.70, 9.85, 12.85, fc='#f1f1f1', lw=0.6, z=3)
    RB(40.70, 38.70, 10.10, 12.60, fc='white', lw=0.6, z=3)
    xs, ys = [], []
    for xx in np.arange(10.145, 12.60, 0.09):
        a0, a1 = Q(40.70, xx), Q(38.70, xx)
        xs += [vb.X(a0[0]), vb.X(a1[0]), np.nan]
        ys += [vb.Y(a0[1]), vb.Y(a1[1]), np.nan]
    sh.L(xs, ys, lw=0.25, chk=False, z=4)
    for s0, s1 in ((38.58, 38.655), (40.745, 40.82)):
        RB(s0, s1, 9.85, 12.85, fc='#999999', lw=0.4, z=4)
        RB(s0, s1, 9.70, 9.85, fc='none', lw=0.4, ls=DASH, z=4)
        RB(s0, s1, 12.85, 13.00, fc='none', lw=0.4, ls=DASH, z=4)
    # ocultos: boca, banda, motor, sumidero
    RB(39.95, 39.45, 11.05, 11.65, fc='none', lw=0.4, ls=DASH, z=5)
    RB(40.90, 38.20, 10.95, 11.75, fc='none', lw=0.4, ls=DASH, z=5)
    RB(38.50, 38.20, 11.80, 12.25, fc='none', lw=0.4, ls=DASH, z=5)
    RB(41.15, 40.75, 9.95, 10.75, fc='none', lw=0.4, ls=DASH, z=5)
    # elevador
    RB(38.01, 36.79, D.X_ELEV - 0.365, D.X_ELEV + 0.365, fc=C_EL2, lw=0.6, z=5)
    # escotilla
    RB(37.55, 36.75, 12.00, 12.80, fc='white', lw=0.6, z=5)
    RB(37.50, 36.80, 12.05, 12.75, fc='none', lw=0.3, z=5)
    vb.L([Q(37.55, 12.00), Q(36.75, 12.80)], lw=0.25, z=5)
    vb.L([Q(37.55, 12.80), Q(36.75, 12.00)], lw=0.25, z=5)
    # tope de ruedas
    RB(41.95, 41.75, 9.60, 13.10, fc='#999999', lw=0.5)
    # cotas
    for a, b, t in ((41.45, 40.70, '0,75'), (40.70, 38.70, '2,00'), (38.70, 36.45, '2,25')):
        vb.dim(Q(a, 13.10), Q(b, 13.10), 4, t, fs=FS)
    vb.dim(Q(41.45, 13.10), Q(36.45, 13.10), 9.5, '5,00', fs=FS)
    vb.dim(Q(36.45, 13.10), Q(36.45, 9.60), 5, '3,50', fs=FS)
    pb = lambda s, x: vb.p(*Q(s, x))
    sh.balloons([
        (1, pb(40.30, 12.30), (250, 250)),
        (2, pb(40.78, 12.00), (250, 240)),
        (18, pb(40.95, 10.35), (250, 206)),
        (20, pb(41.85, 9.90), (250, 196)),
        (17, pb(36.95, 12.40), (386, 255)),
        (10, pb(38.35, 12.02), (386, 232)),
        (15, pb(37.40, D.X_ELEV), (386, 218)),
        (16, pb(37.10, 10.30), (386, 203)),
    ])

    # ===================== C — CORTE TRANSVERSAL POR LA TOLVA 1:50 =====================
    sh.vtitle(242, 180, 'C — CORTE TRANSVERSAL   Esc. 1:50')
    vc = View(sh, 290, 170, 50)

    def T(x, z):
        return ((x - D.X_ELEV) * 1000, z * 1000)

    def RC(x0, x1, z0, z1, **kw):
        return vc.P([T(x0, z0), T(x1, z0), T(x1, z1), T(x0, z1)], **kw)
    for i, w in enumerate([[T(9.60, -3.40), T(9.85, -3.40), T(9.85, -0.20), T(9.60, -0.20)],
                           [T(12.85, -3.40), T(13.10, -3.40), T(13.10, -0.20), T(12.85, -0.20)],
                           [T(9.60, -3.65), T(13.10, -3.65), T(13.10, -3.40), T(9.60, -3.40)]]):
        vc.concrete(w, seed=i + 6)
        vc.P(w, fc='none', lw=0.6)
    sh.ground(vc.X(T(9.10, 0)[0]), vc.X(T(9.60, 0)[0]), vc.Y(-200))
    sh.ground(vc.X(T(13.10, 0)[0]), vc.X(T(13.60, 0)[0]), vc.Y(-200))
    # viga UPN (al fondo) apoyada en nichos
    RC(9.85, 12.85, -0.4064, -0.2064, fc='#d6d6d6', lw=0.4, z=1)
    RC(9.70, 9.85, -0.4064, -0.2064, fc='none', lw=0.4, ls=DASH, z=4)
    RC(12.85, 13.00, -0.4064, -0.2064, fc='none', lw=0.4, ls=DASH, z=4)
    # tolva
    vc.P([T(10.10, -0.257), T(12.60, -0.257), T(11.65, -1.90), T(11.05, -1.90)], fc='#f4f4f4', ec='none', lw=0,
         z=2)
    vc.L([T(10.10, -0.257), T(11.05, -1.90)], lw=1.0)
    vc.L([T(12.60, -0.257), T(11.65, -1.90)], lw=1.0)
    for zz in (-0.857, -1.457):
        t = (-0.257 - zz) / 1.643
        for xt, xb, sg in ((10.10, 11.05, -1), (12.60, 11.65, 1)):
            xx = xt + (xb - xt) * t
            cx, cy = vc.p(*T(xx, zz))
            cx += sg * 0.8
            sh.P([(cx - 0.5, cy - 0.5), (cx + 0.5, cy - 0.5), (cx + 0.5, cy + 0.5), (cx - 0.5, cy + 0.5)],
                 fc='k', lw=0.2)
    # marco L y barras de reja en corte
    for xm, d in ((10.10, -1), (12.60, 1)):
        RC(min(xm, xm + d * 0.05), max(xm, xm + d * 0.05), -0.257, -0.252, fc='k', lw=0.2)
    xs, ys = [], []
    for xx in np.arange(10.145, 12.60, 0.09):
        xs += [vc.X(T(xx, 0)[0])] * 2 + [np.nan]
        ys += [vc.Y(-252), vc.Y(-202), np.nan]
    sh.L(xs, ys, lw=0.5, chk=False)
    # tapa a ambos lados
    vc.L([T(9.85, -0.203), T(10.05, -0.203)], lw=1.2)
    vc.L([T(12.65, -0.203), T(12.85, -0.203)], lw=1.2)
    # boca, compuerta, faldones, banda
    RC(11.00, 11.70, -1.97, -1.90, fc='white', lw=0.5)
    RC(11.05, 11.65, -2.18, -1.97, fc=C_MAT, lw=0.5)
    vc.L([T(10.95, -2.20), T(11.75, -2.20)], lw=1.2)
    RC(10.90, 11.80, -2.29, -2.21, fc='white', lw=0.4)
    vc.L([T(10.95, -2.50), T(11.75, -2.50)], lw=1.0)
    for xl in (10.80, 11.90):
        RC(xl - 0.04, xl + 0.04, -2.66, -2.20, fc=C_STEEL, lw=0.4)
        RC(xl - 0.03, xl + 0.03, -3.40, -2.66, fc=C_STEEL, lw=0.3)
    RC(10.76, 11.94, -2.66, -2.60, fc=C_STEEL, lw=0.3)
    # cotas
    vc.dim(T(10.10, -0.20), T(12.60, -0.20), 4, '2.500', fs=FS)
    vc.dim(T(11.05, -1.90), T(11.65, -1.90), 9.5, '600', fs=4.6, ext0=1.0)
    vc.dim(T(9.85, -3.65), T(12.85, -3.65), -4, '3,00 (interior)', fs=FS)
    vc.dim(T(12.60, -0.20), T(12.60, -1.90), 13, '1.700', fs=FS, ext0=1.0)
    sh.T(vc.X(T(11.80, 0)[0]), vc.Y(-1200), '61°', fs=FS, ha='center')
    pc = lambda x, z: vc.p(*T(x, z))
    sh.balloons([
        (4, pc(10.45, -0.86), (262, 150)),
        (2, pc(9.95, -0.30), (262, 160)),
        (8, pc(11.05, -2.07), (262, 128)),
        (9, pc(10.98, -2.20), (262, 120)),
        (13, pc(10.80, -2.90), (262, 110)),
        (12, pc(11.70, -2.25), (317, 128)),
        (5, pc(12.36, -0.86), (317, 150)),
        (19, pc(12.97, -1.80), (331, 140)),
    ])

    # ===================== D — DETALLE DE APOYO 1:10 =====================
    sh.vtitle(342, 180, 'D — APOYO DE TOLVA Y REJA   Esc. 1:10')
    vd = View(sh, 340, 100, 10, mx=2450, my=-700)
    vd.P(upn_pts(2795, -206.4, 1), fc=C_STEEL, lw=0.6, hatch='/////')
    vd.P([(2745, -257), (2795, -257), (2795, -207), (2790, -207), (2790, -252), (2745, -252)], fc='k', lw=0.3)
    # bulon M12
    vd.P([(2780, -240), (2790, -240), (2790, -221), (2780, -221)], fc='#777777', lw=0.3)
    vd.L([(2790, -230.5), (2818, -230.5)], lw=1.4)
    vd.P([(2803.5, -240), (2813.5, -240), (2813.5, -221), (2803.5, -221)], fc='#777777', lw=0.3)
    # barra de reja (vista en largo) y separador
    vd.P([(2470, -252), (2787, -252), (2787, -202), (2470, -202)], fc='white', lw=0.7)
    vd.C(2600, -227, 8, fc='white', lw=0.5)
    sh.breakline(vd.X(2470), vd.Y(-195), vd.X(2470), vd.Y(-259))
    # chapa de tolva e=5 (65,5°)
    k = 750 / 1643
    zb = -680
    vd.P([(2744.5, -257), (2750, -257), (2750 - k * (zb + 257) * -1, zb), (2744.5 - k * (zb + 257) * -1, zb)],
         fc='k', lw=0.3)
    # cordon de soldadura tolva-marco
    vd.P([(2750, -257), (2758, -257), (2750, -265)], fc='k', lw=0.2)
    # refuerzo L40x40x4 (primer anillo)
    zr = -580
    ur = 2750 - k * (-257 - zr)
    vd.P([(ur, zr), (ur + 40, zr), (ur + 40, zr - 4), (ur + 4, zr - 4), (ur + 4, zr - 40), (ur, zr - 40)],
         fc='k', lw=0.2)
    # tapa chapa semilla de melon
    vd.P([(2812, -206.4), (2990, -206.4), (2990, -200), (2812, -200)], fc='k', lw=0.2)
    sh.breakline(vd.X(2990), vd.Y(-192), vd.X(2990), vd.Y(-214))
    sh.breakline(vd.X(2520), vd.Y(zb), vd.X(2580), vd.Y(zb))
    # cotas
    vd.dim((2870, -206.4), (2870, -406.4), 12, '200', fs=FS)
    vd.dim((2470, -202), (2470, -252), 4, '50', fs=FS, tside=1)
    pdd = lambda u, z: vd.p(u, z)
    sh.balloons([
        (1, pdd(2650, -215), (352, 160)),
        (16, pdd(2950, -203), (398, 167)),
        (3, pdd(2770, -254), (372, 128)),
        (2, pdd(2835, -390), (388, 118)),
        (4, pdd(2700, -350), (355, 140)),
        (5, pdd(ur + 20, zr - 2), (352, 116)),
    ])
    sh.lead(*pdd(2815, -230.5), 382, 155.5, 'M12 c/300', fs=4.8, ha='left')
    sh.lead(*pdd(2600, -227), 372, 163, 'Ø16 c/500', fs=4.8, ha='left')

    # ===================== DATOS =====================
    rows = [['Datos de diseño', ''],
            ['Volumen útil de tolva', '3,70 m³'],
            ['Ángulos de paredes', '60,8° / 66,2°'],
            ['Caudal del alimentador', '64,2 t/h (variador)'],
            ['Altura de lecho', '160 mm'],
            ['Fosa (interior)', '4,50 × 3,00 × 3,20 m']]
    sh.table(228, 86, [44, 52], rows, rowh=4.4, fs=FS)

    # ===================== TABLA DE ELEMENTOS =====================
    items = [('1', 'Reja de gruesos', 'pl. 10×50 c/90 (luz 80) + separadores Ø16 c/500'),
             ('2', 'Vigas de apoyo', '2 × UPN 200, L 3,30, en nicho de muro s/placa 10'),
             ('3', 'Marco perimetral', 'L 50×50×5 abulonado al alma UPN (M12 c/300)'),
             ('4', 'Tolva', 'ST-37 e = 5, 2.500×2.000 / 600×500, H 1,70'),
             ('5', 'Refuerzos', 'L 40×40×4 perimetrales c/600'),
             ('6', 'Sensor de nivel', 'ultrasónico, bajo el marco norte'),
             ('7', 'Compuerta manual', 'guillotina en boca 600×500'),
             ('8', 'Faldones y regulador', 'faldones 600 c/goma; compuerta de lecho h 160'),
             ('9', 'Banda', 'goma, ancho 800, 2,40 entre ejes'),
             ('10', 'Tambor motriz', 'Ø300 + motorreductor con variador'),
             ('11', 'Tambor de cola', 'Ø300 + tensor a tornillo'),
             ('12', 'Rodillos', 'impacto Ø89 c/250 + rodillo de retorno'),
             ('13', 'Bastidor', 'largueros UPN 140 + patas, anclaje químico M12'),
             ('14', 'Tolvín de descarga', 'chapa e = 5 a 56° + rascador en tambor'),
             ('15', 'Elevador', 'bota c/tensor + cuerpo 730×1.220 (DET-10)'),
             ('16', 'Tapa', 'chapa semilla de melón e = 6,4 s/L 50×50×5'),
             ('17', 'Escotilla', '800×800 abisagrada + escalera marinera'),
             ('18', 'Sumidero', '400×800×200 + bomba sumergible, desc. Ø50'),
             ('19', 'Fosa', 'H° A° e = 25, interior 4,50×3,00×3,20'),
             ('20', 'Tope de ruedas', 'H° A° 200×150 a 0,30 del borde')]
    hdr = ['N°', 'Elemento', 'Especificación']
    sh.table(25, 92, [6, 27, 65], [hdr] + [list(r) for r in items[:10]], rowh=4.3, fs=4.8)
    sh.table(124, 92, [6, 27, 65], [hdr] + [list(r) for r in items[10:]], rowh=4.3, fs=4.8)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/DET-11')
