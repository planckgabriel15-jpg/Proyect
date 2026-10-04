from lib import *
import data as D
import math


def grid(sh, v, x0, y0, x1, y1, step=100):
    xs, ys = [], []
    for x in np.arange(min(x0, x1), max(x0, x1) + 1e-6, step):
        xs += [v.X(x), v.X(x), np.nan]
        ys += [v.Y(y0), v.Y(y1), np.nan]
    for y in np.arange(min(y0, y1), max(y0, y1) + 1e-6, step):
        xs += [v.X(x0), v.X(x1), np.nan]
        ys += [v.Y(y), v.Y(y), np.nan]
    sh.L(xs, ys, lw=0.2, c='#a8a8a8', chk=False, z=1)


def head_box_plan(v, xc, fc=C_NEW2):
    """Caja de cabezal en planta, centrada en el eje de rueda xc; extremo achaflanado hacia +x."""
    v.P([(xc - 450, -340), (xc + 300, -340), (xc + 450, -190), (xc + 450, 190), (xc + 300, 340),
         (xc - 450, 340)], fc=fc, lw=LW)


def head_box_elev(v, xc, sgn=1, fc=C_NEW2):
    """Caja en elevacion: chaflanes del lado sgn."""
    a, b = xc - 450 * sgn, xc + 450 * sgn
    c = xc + 300 * sgn
    v.P([(a, -40), (c, -40), (b, 110), (b, 700), (c, 850), (a, 850)], fc=fc, lw=LW)


def build(out):
    sh = Sheet('DET-05', 'Cabezal motriz y cola tensora del Redler (línea L1; L2 simétrica)',
               'Ruedas Z = 11, paso 200, Dp 709,9 · eje motriz Ø140 · soportes de rodamiento a rótula · tensor a tornillo',
               '1:25 / 1:10', 6)
    FS = 5.0
    # ===================== A — CABEZAL MOTRIZ · PLANTA 1:25 =======================
    sh.vtitle(24, 276, 'A — CABEZAL MOTRIZ · PLANTA   Esc. 1:25')
    v = View(sh, 138, 216, 25)
    v.concrete([(-175, -1150), (175, -1150), (175, 1150), (-175, 1150)], seed=3)
    v.R(-175, -1150, 350, 2300, fc='none', lw=LW)
    grid(sh, v, -2000, -1264, -1380, -350)
    v.R(-2000, -1264, 620, 914, fc='none', lw=0.4)
    v.L([(-2000, -1219), (-1380, -1219)], lw=0.8)
    v.L([(-1380, -1264), (-1380, -350)], lw=0.8)
    v.R(-2000, -304, 730, 608, fc=C_NEW, lw=LW)
    sh.breakline(*v.p(-2000, -420), *v.p(-2000, 420))
    head_box_plan(v, -820)
    for sg in (-1, 1):
        v.R(-820 - 355, sg * 241 - 30, 710, 60, fc='none', lw=0.4, ls=(0, (3, 2)))
    v.R(-890, -1010, 140, 1640, fc='white', lw=LW)
    v.cl((-820, -1080), (-820, 700))
    for sg in (-1, 1):
        v.R(-1030, sg * 470 - 60, 420, 120, fc='#cfcfcf', lw=LW)
        for xx in (-985, -655):
            v.C(xx, sg * 470, 18, fc='white', lw=0.4)
    v.R(-900, 640, 160, 110, fc='#e8e8e8', lw=0.5, ls=(0, (3, 2)))
    v.R(-1020, -880, 400, 300, fc='#9fb3c8', lw=LW)
    v.R(-1660, -810, 640, 160, fc='#9fb3c8', lw=LW)
    v.R(-1700, -830, 40, 200, fc='#6d86a0', lw=0.5)
    sh.T(v.X(-1340), v.Y(-730), 'M', fs=7, ha='center', bold=True)
    v.L([(-620, -730), (-420, -730), (-420, -340)], lw=0.9)
    v.C(-420, -730, 14, fc='k')
    # cotas
    v.dim((-1030, -470), (-1030, 470), 14, '940', tside=1)
    v.dim((-1175, -241), (-1175, 241), 3, '482', tside=1, fs=FS)
    v.dim((-1270, 340), (-370, 340), 3, '900', fs=FS)
    v.dim((-370, 340), (-175, 340), 3, '195', fs=FS, tpos=0.5)
    v.dim((-820, 1150), (0, 1150), 4, '820', fs=FS)
    sh.labels([(v.X(-820), v.Y(720), 'tapa de protección', v.Y(1000)),
               (v.X(-850), v.Y(560), 'eje Ø140 (AISI 1045)', v.Y(800)),
               (v.X(-700), v.Y(500), 'soporte SNL + rod. a rótula', v.Y(600)),
               (v.X(-420), v.Y(-500), 'brazo de reacción', v.Y(-560)),
               (v.X(-1500), v.Y(-730), 'motorreductor ortogonal\n15 kW, eje hueco, i ≈ 225', v.Y(-700)),
               (v.X(-1800), v.Y(-1000), 'pasarela L1\n(termina en el cabezal)', v.Y(-1000))],
              23.5, ha='left', fs=FS, sp=5.5)
    sh.lead(v.X(-640), v.Y(241), 147, v.Y(160), 'rueda Z = 11 (×2)', fs=FS)
    sh.T(v.X(0), v.Y(-1250), 'muro norte', fs=FS, ha='center')

    # ===================== B — CABEZAL · ELEVACION 1:25 ========================
    sh.vtitle(166, 276, 'B — CABEZAL MOTRIZ · ELEVACIÓN   Esc. 1:25')
    vb = View(sh, 280, 212, 25)
    vb.R(-2200, 0, 930, 810, fc=C_NEW, lw=LW)
    vb.L([(-2200, 405), (-1270, 405)], lw=0.4, ls=(0, (4, 2)))
    sh.breakline(*vb.p(-2200, -480), *vb.p(-2200, 900))
    head_box_elev(vb, -820, 1)
    vb.C(-820, 390, 355, fc='none', lw=0.4, ls=(0, (5, 2)))
    vb.R(-1030, 300, 420, 175, fc='#cfcfcf', lw=LW)
    vb.C(-820, 390, 70, fc='white', lw=LW, z=4)
    vb.R(-760, 850, 110, 90, fc='#f2c98a', lw=0.5)
    vb.R(-1660, 310, 640, 160, fc='none', lw=0.4, ls=(0, (3, 2)))
    vb.R(-1250, -100, 50, 60, fc=C_STEEL, lw=0.4)
    vb.R(-430, -100, 50, 60, fc=C_STEEL, lw=0.4)
    vb.R(-1950, -100, 50, 100, fc=C_STEEL, lw=0.4)
    vb.R(-2200, -400, 2250, 300, fc='#e0e0e0', lw=LW)
    vb.concrete([(-175, -700), (175, -700), (175, -441), (-175, -441)], seed=5)
    vb.R(-175, -700, 350, 259, fc='none', lw=LW)
    sh.breakline(*vb.p(-260, -700), *vb.p(260, -700))
    vb.R(-90, -441, 180, 18, fc='#777777', lw=0.4)
    vb.R(-40, -423, 80, 5, fc='#333333', lw=0.3)
    vb.R(-40, -418, 80, 18, fc='#999999', lw=0.4)
    vb.L([(175, -441), (175, 1000)], lw=0.9)
    for zz in (100, 700):
        vb.R(175, zz, 60, 60, fc=C_WOOD, lw=0.4)
    for z, s_ in [(810, '+5,151'), (390, '+4,731 eje'), (-400, '+3,941'), (-441, '+3,90')]:
        pass
    sh.lev(vb.X(270), vb.Y(810), '+5,151', ln=10)
    sh.lev(vb.X(270), vb.Y(390), '+4,731', ln=10)
    sh.lev(vb.X(270), vb.Y(-100), '+4,241', ln=10)
    sh.lev(vb.X(270), vb.Y(-441), '+3,90', ln=10)
    vb.dim((-820, 390), (-820, 0), 0, '390', ext=False, fs=FS, tside=-1)
    sh.labels([(vb.X(-1500), vb.Y(420), 'motorreductor\n(más allá)', vb.Y(560)),
               (vb.X(-1600), vb.Y(-250), 'viga carrilera\ntubo 300×200×10'),
               (vb.X(-1225), vb.Y(-70), 'silleta del cabezal', vb.Y(-520))],
              166, ha='left', fs=FS, sp=7.5)
    sh.labels([(vb.X(-600), vb.Y(470), 'soporte SNL'),
               (vb.X(-705), vb.Y(940), 'detector de atoramiento', vb.Y(1350)),
               (vb.X(-512.6), vb.Y(567.5), 'Dp 709,9', vb.Y(900)),
               (vb.X(-430), vb.Y(700), 'cabezal = punto fijo', vb.Y(1100)),
               ],
              vb.X(-150) + 0.5, ha='left', fs=FS, sp=3.6)

    # ===================== TABLA ==============================
    rows = [['Dato', 'Valor'],
            ['Rueda de cabeza y cola', 'Z = 11, paso 200, Dp 709,9 mm'],
            ['Velocidad de cadena', '0,24 m/s'],
            ['Caudal de diseño', '64,20 t/h (Urea 720 kg/m³)'],
            ['Giro del eje motriz', 'n = 6,46 rpm'],
            ['Fuerza resistente', 'F = 33,4 kN (Wc 61 · Wm 74,3 kg/m)'],
            ['Par en el eje', 'T = 11,86 kN·m'],
            ['Eje (τadm 40 MPa, Ks 1,5)', 'd ≥ 134,0 mm → Ø 140 AISI 1045'],
            ['Rodamientos (L10h 20.000 h)', 'rodillos a rótula, C ≥ 39,2 kN'],
            ['Potencia instalada', '11,79 kW → motor 15 kW'],
            ['Relación de reducción', 'i ≈ 225 (1.450 / 6,46)'],
            ['Paletas por línea', '380 (lazo de cadena 76,0 m)'],
            ['Tensor de cola', 'tornillo M30, carrera ± 150 mm']]
    sh.table(315, 276, [36, 57], rows, rowh=3.7, fs=4.9)

    # ===================== C — COLA TENSORA · PLANTA 1:25 =========================
    sh.vtitle(24, 152, 'C — COLA TENSORA · PLANTA   Esc. 1:25')
    vc = View(sh, 126, 100, 25)
    grid(sh, vc, -2450, -900, -175, 900)
    vc.R(-2450, -900, 2275, 1800, fc='none', lw=0.4)
    vc.concrete([(-175, -900), (175, -900), (175, 900), (-175, 900)], seed=7)
    vc.R(-175, -900, 350, 1800, fc='none', lw=LW)
    vc.L([(-1825, -900), (-1825, 900)], lw=0.5, ls=(0, (4, 2)))
    vc.R(-1120, -304, 1520, 608, fc=C_NEW, lw=LW)
    sh.breakline(*vc.p(400, -420), *vc.p(400, 420))
    vc.P([(-2020, -340), (-1270, -340), (-1120, -190), (-1120, 190), (-1270, 340), (-2020, 340)], fc=C_NEW2, lw=LW)
    vc.R(-1120, -300, 400, 600, fc='#9fb3c8', lw=0.6)
    vc.L([(-1120, -300), (-720, 300)], lw=0.3)
    vc.L([(-1120, 300), (-720, -300)], lw=0.3)
    for sg in (-1, 1):
        vc.R(-1570 - 355, sg * 241 - 30, 710, 60, fc='none', lw=0.4, ls=(0, (3, 2)))
    vc.R(-1640, -620, 140, 1240, fc='white', lw=LW)
    vc.cl((-1570, -700), (-1570, 760))
    for sg in (-1, 1):
        vc.R(-1780, sg * 470 - 60, 420, 120, fc='#cfcfcf', lw=LW)
        vc.R(-2380, sg * 470 - 10, 600, 20, fc='#777777', lw=0.4)
        vc.R(-2400, sg * 470 - 60, 20, 120, fc='k', lw=0.4)
    vc.R(-1620, 620, 100, 90, fc='#f2c98a', lw=0.5)
    vc.dim((-1780, -560), (-1360, -560), -2.5, '± 150 carrera', fs=4.6)
    vc.dim((-1400, -470), (-1400, 470), -2, '940', tside=1, fs=FS)
    vc.dim((-1120, 330), (-720, 330), 3, '400', fs=FS)
    vc.dim((-1570, 900), (0, 900), 3, '1.570', fs=FS)
    sh.T(vc.X(0), vc.Y(-1020), 'muro sur', fs=FS, ha='center')
    sh.labels([(vc.X(-2390), vc.Y(470), 'tensor M30'),
               (vc.X(-1570), vc.Y(700), 'sensor de rotación', vc.Y(800)),
               (vc.X(-920), vc.Y(150), 'boca de carga 600×400', vc.Y(1000))],
              vc.X(-2000), ha='right', fs=FS, sp=3.6) if False else None
    sh.lead(vc.X(-920), vc.Y(150), 146, vc.Y(560), 'boca de carga\n600 × 400', fs=FS) if False else None
    tb_ = sh.lead(vc.X(-920), vc.Y(150), 146, vc.Y(600), 'boca de carga', fs=FS)
    sh.T(146.8, vc.Y(600) - 2.2, '600 × 400', fs=FS, tid=tb_)
    sh.lead(vc.X(-1570), vc.Y(700), vc.X(-1500), 145.0, 'sensor de rotación', fs=FS, ha='right')
    sh.lead(vc.X(-2390), vc.Y(470), vc.X(-2200), 141.5, 'tensor M30', fs=FS, ha='right')
    sh.lead(vc.X(-2300), vc.Y(-800), vc.X(-2300), 58.0, 'plataforma exterior (rejilla) NPP +4,05', fs=FS)
    sh.lead(vc.X(-1825), vc.Y(-850), vc.X(-1250), 61.6, 'viga B2 IPN 200 (bajo rejilla)', fs=FS)

    # ===================== D — COLA TENSORA · ELEVACION 1:25 ========================
    sh.vtitle(166, 156, 'D — COLA TENSORA · ELEVACIÓN   Esc. 1:25')
    vd = View(sh, 282, 88, 25)
    vd.R(-1120, 0, 1720, 810, fc=C_NEW, lw=LW)
    vd.L([(-720, 405), (600, 405)], lw=0.4, ls=(0, (4, 2)))
    sh.breakline(*vd.p(600, -480), *vd.p(600, 900))
    head_box_elev(vd, -1570, -1)
    vd.C(-1570, 390, 355, fc='none', lw=0.4, ls=(0, (5, 2)))
    vd.R(-1780, 300, 420, 175, fc='#cfcfcf', lw=LW)
    vd.C(-1570, 390, 70, fc='white', lw=LW, z=4)
    vd.R(-2380, 380, 360, 20, fc='#777777', lw=0.4)
    vd.R(-1120, 810, 400, 60, fc='#9fb3c8', lw=0.5)
    jx, jy = [], []
    for kk in range(9):
        xx = -1100 + kk * 45
        jx += [vd.X(xx), vd.X(xx), np.nan]
        jy += [vd.Y(870), vd.Y(1060), np.nan]
    sh.L(jx, jy, lw=0.4, chk=False)
    vd.R(-1120, 870, 400, 190, fc='none', lw=0.6)
    vd.R(-1070, 1060, 300, 440, fc='#e4ebf3', lw=LW)
    sh.breakline(*vd.p(-1180, 1500), *vd.p(-710, 1500))
    vd.concrete([(-175, -700), (175, -700), (175, -441), (-175, -441)], seed=9)
    vd.R(-175, -700, 350, 259, fc='none', lw=LW)
    sh.breakline(*vd.p(-260, -700), *vd.p(260, -700))
    vd.L([(-175, -441), (-175, -30)], lw=0.9)
    vd.L([(-175, 860), (-175, 1500)], lw=0.9)
    vd.R(-235, -30, 60, 890, fc='none', lw=0.5)
    vd.P([(-175, 900), (-330, 830), (-330, 850), (-175, 930)], fc='#bdbdbd', lw=0.4)
    vd.R(-2450, -321, 2275, 30, fc='#dcdcdc', lw=0.5)
    vd.R(-1875, -521, 100, 200, fc='k', lw=0.4)
    vd.R(-1975, -400, 1965, 300, fc='#e0e0e0', lw=LW)
    vd.R(10, -400, 590, 300, fc='#e0e0e0', lw=LW)
    vd.R(-110, -441, 220, 18, fc='#777777', lw=0.4)
    for sil, hh in ((-1250, 60), (-430, 60), (300, 100)):
        vd.R(sil, -100, 50, hh, fc=C_STEEL, lw=0.4)
    sh.lev(vd.X(650), vd.Y(810), '+5,151', ln=9)
    sh.lev(vd.X(650), vd.Y(-291), '+4,05', ln=9)
    sh.lev(vd.X(650), vd.Y(-441), '+3,90', ln=9)
    vd.dim((-1975, -400), (-175, -400), -5, '1.800 (tramo 0)', fs=FS)
    sh.labels([(vd.X(-2380), vd.Y(390), 'tensor M30'),
               (vd.X(-1825), vd.Y(-480), 'viga B2\nIPN 200', vd.Y(-560))],
              166, ha='left', fs=FS, sp=8)
    sh.labels([(vd.X(-760), vd.Y(1300), 'chute a 45° (DET-10)'),
               (vd.X(-760), vd.Y(965), 'junta flexible'),
               (vd.X(-720), vd.Y(840), 'boca de carga 600×400'),
               ], vd.X(-100), ha='left', fs=FS, sp=3.6)
    sh.lead(vd.X(0), vd.Y(-432), vd.X(260), vd.Y(-600), 'placa 1.000×180×18', fs=FS)

    # ===================== E — PASO DE LA PALETA POR LA RUEDA 1:10 =================
    sh.vtitle(315, 221, 'E — PASO DE LA PALETA POR LA RUEDA   Esc. 1:10')
    ve = View(sh, 350, 176, 10)
    R = D.DP / 2
    th = [math.radians(-90 + kk * 360 / 11) for kk in range(6)]
    pins = [(R * math.cos(t), R * math.sin(t)) for t in th]
    p5 = pins[-1]
    xtop = p5[0] - math.sqrt(200 ** 2 - (R - p5[1]) ** 2)
    top = [(xtop - 200 * kk, R) for kk in range(2)]
    bot = [(-200 * kk, -R) for kk in range(1, 3)][::-1]
    chainpts = bot + pins + top
    ve.C(0, 0, R, fc='none', lw=0.4, ls=(0, (5, 2)))
    ve.C(0, 0, R + 28, fc='none', lw=0.6)
    ve.C(0, 0, 70, fc='white', lw=LW, hatch='////')
    ve.cl((-120, 0), (420, 0))
    ve.cl((0, -420), (0, 420))
    ve.L(chainpts, lw=1.4, c='#555555')
    for p in chainpts:
        ve.C(p[0], p[1], 12, fc='k', lw=0.2)
    for a, b in zip(chainpts[:-1], chainpts[1:]):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L_ = math.hypot(dx, dy)
        nx, ny = -dy / L_, dx / L_
        ve.L([(m[0] - nx * 21, m[1] - ny * 21), (m[0] + nx * 259, m[1] + ny * 259)], lw=1.6, c='#4f6f92')
    t0 = math.radians(-90 + 360 / 22)
    rm = R * math.cos(math.pi / 11) - 259
    ve.L([(70 * math.cos(t0), 70 * math.sin(t0)), (rm * math.cos(t0), rm * math.sin(t0))], lw=0.9, c='#c00000')
    th_ = sh.lead(*ve.p(80 * math.cos(t0), 80 * math.sin(t0)), 356, 131, 'holgura mín. paleta–eje ≈ 11 mm', fs=FS, ha='left')
    sh.T(356.8, 127.4, '(gira solidaria con la rueda)', fs=FS, tid=th_)
    sh.lead(*ve.p(0, 60), 397, 190, 'eje Ø140', fs=FS, ha='left')
    sh.lead(*ve.p(-300, -200), 330, 122.5, 'paleta 370×280', fs=FS, ha='left')
    sh.lead(*ve.p(R * math.cos(0.5), R * math.sin(0.5)), 397, 205, 'Dp 709,9', fs=FS, ha='left')
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/DET-05')
