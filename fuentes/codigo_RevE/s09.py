from lib import *
import data as D
import math

# z en mm desde +3,90
Z_TI, Z_TS = 41, 341
Z_MS = 121          # cara sup. ménsula UPC 80 (+4,021)
Z_NPP = 151         # rejilla (NPP +4,05)
Z_PM = Z_NPP + 1100  # pasamanos (+5,15)
X_MT = 1209          # cara interior del montante


def grating_section(v, x0, x1, z0, h=30, step=30):
    v.R(x0, z0, x1 - x0, h, fc='#eeeeee', lw=0.5)
    xs, ys = [], []
    for x in np.arange(x0 + step, x1, step):
        xs += [v.X(x), v.X(x), np.nan]
        ys += [v.Y(z0), v.Y(z0 + h), np.nan]
    v.sh.L(xs, ys, lw=0.25, chk=False)


def build(out):
    sh = Sheet('DET-09', 'Pasarela de mantenimiento y escalera de acceso',
               'Ménsulas UPC 80 c/1,00 m con cartela · rejilla electrosoldada · baranda 1,10 m con montante en cada ménsula',
               '1:10 / 1:20 / 1:25 / 1:100', 10)
    FS = 5.0
    # ===================== A — SECCION TIPO 1:10 =====================
    sh.vtitle(24, 276, 'A — SECCIÓN TIPO DE PASARELA (L1)   Esc. 1:10')
    v = View(sh, 56, 138, 10)
    # conducto (parcial) y silleta
    v.R(-304, 441, 608, 810, fc=C_NEW, lw=LW)
    v.L([(-304, 845), (304, 845)], lw=0.4, ls=(0, (4, 2)))
    v.R(-400, 341, 800, 100, fc=C_STEEL, lw=0.5)
    # tubo
    v.ipn_like_tube(0, Z_TI, 200, 300, 10, hatch='////')
    # mensula UPC 80 (vista longitudinal) + cartela
    v.R(100, Z_TI, 1164, 80, fc='#d9d9d9', lw=LW)
    v.L([(100, Z_TI + 7), (1264, Z_TI + 7)], lw=0.3)
    v.L([(100, Z_MS - 7), (1264, Z_MS - 7)], lw=0.3)
    v.P([(100, Z_MS), (100, Z_MS + 180), (350, Z_MS)], fc='#bdbdbd', lw=0.6)
    # larguero UPN 80 (corte)
    v.P([(1264, Z_TI), (1219, Z_TI), (1219, Z_TI + 8), (1258, Z_TI + 8), (1258, Z_MS - 8), (1219, Z_MS - 8),
         (1219, Z_MS), (1264, Z_MS)], fc='white', lw=0.5, hatch='////')
    # rejilla
    grating_section(v, 350, X_MT - 3, Z_MS)
    # rodapie, montante, pasamanos, travesano
    v.R(X_MT - 3, Z_NPP, 3, 150, fc='k', lw=0.2)
    v.R(X_MT, Z_MS, 50, Z_PM - 20 - Z_MS, fc='white', lw=LW)
    v.R(X_MT - 5, Z_MS - 6, 60, 6, fc='#888888', lw=0.3) if False else None
    v.R(X_MT + 5, Z_PM - 40, 40, 40, fc='white', lw=0.6, hatch='////')
    v.R(X_MT - 30, Z_NPP + 500 - 15, 30, 30, fc='white', lw=0.6, hatch='////')
    # columna existente C1
    v.R(1350, -40, 200, 1400, fc=C_EXIST, lw=LW)
    sh.breakline(*v.p(1330, 1360), *v.p(1570, 1360))
    sh.breakline(*v.p(1330, -40), *v.p(1570, -40))
    v.cl((0, -60), (0, 1320))
    v.cl((1450, -60), (1450, 1380))
    # cotas
    v.dim((304, 1180), (X_MT, 1180), 0, 'paso libre 0,905', ext=False, fs=FS)
    v.dim((1259, Z_PM), (1350, Z_PM), 14, '91', fs=FS) if False else None
    v.dim((1264, 15), (1350, 15), 0, '86', ext=False, fs=FS)
    v.dim((0, Z_TI), (1264, Z_TI), -9, 'vuelo de la ménsula 1.264 (desde el eje de la viga)', fs=FS)
    v.dim((0, Z_TI), (1450, Z_TI), -16, '1.450 (eje viga – eje columna C1)', fs=FS)
    v.dim((1290, Z_NPP), (1290, Z_PM), 0, '1.100', ext=False, fs=FS)
    v.dim((1328, Z_NPP), (1328, Z_NPP + 500), 0, '500', ext=False, fs=FS)
    v.dim((1170, Z_NPP), (1170, Z_NPP + 150), 0, '150', ext=False, fs=FS, tside=-1) if False else None
    sh.lev(v.X(450), v.Y(Z_NPP), 'NPP +4,05', ln=10)
    sh.lev(v.X(450), v.Y(Z_PM), '+5,15 pasamanos', ln=16)
    sh.labels([(v.X(1234), v.Y(Z_PM - 20), 'pasamanos caño 40×40×2', v.Y(1050)),
               (v.X(1450), v.Y(1250), 'columna existente C1 (0,20×0,20)', v.Y(980)),
               (v.X(1234), v.Y(950), 'montante caño 50×50×3 c/1,00', v.Y(910)),
               (v.X(1209), v.Y(Z_NPP + 500), 'travesaño caño 30×30×2', v.Y(840)),
               (v.X(1207), v.Y(260), 'rodapié chapa 150×3', v.Y(770)),
                              (v.X(1240), v.Y(81), 'larguero de borde UPN 80', v.Y(560)),
               (v.X(1000), v.Y(81), 'ménsula UPC 80 c/1,00 m', v.Y(490))],
              v.X(1100), ha='right', fs=FS, sp=5.0)
    sh.lead(v.X(370), v.Y(136), v.X(400), v.Y(345), 'rejilla electrosoldada galv. 30×30×3', fs=FS, ha='left')
    sh.lead(v.X(170), v.Y(150), v.X(400), v.Y(285), 'cartela 250×180×12, a6 (ver E)', fs=FS, ha='left')
    sh.lead(v.X(100), v.Y(250), v.X(400), v.Y(225), 'viga carrilera tubo 300×200×10', fs=FS, ha='left')
    sh.T(v.X(0), v.Y(1000), 'conducto Redler', fs=FS, ha='center')
    sh.T(v.X(0), v.Y(390), 'silleta UPN 100', fs=FS, ha='center')

    # ===================== B — ELEVACION DE BARANDA 1:20 =====================
    sh.vtitle(216, 276, 'B — ELEVACIÓN DE BARANDA (lado columna)   Esc. 1:20')
    vb = View(sh, 230, 195, 20)
    vb.R(-150, Z_TI, 2300, 80, fc='#d9d9d9', lw=LW)      # larguero
    vb.R(-150, Z_NPP, 2300, 150, fc='#eeeeee', lw=0.5)   # rodapie
    for s0 in (0, 1000, 2000):
        vb.R(s0 - 25, Z_MS, 50, Z_PM - 20 - Z_MS, fc='white', lw=LW)
        vb.R(s0 - 22.5, Z_TI - 30, 45, 30, fc='#999999', lw=0.4)
    vb.R(-150, Z_PM - 40, 2300, 40, fc='white', lw=LW)
    vb.R(-150, Z_NPP + 485, 2300, 30, fc='white', lw=0.6)
    sh.breakline(*vb.p(-150, Z_TI - 40), *vb.p(-150, Z_PM + 20))
    sh.breakline(*vb.p(2150, Z_TI - 40), *vb.p(2150, Z_PM + 20))
    vb.dim((0, Z_PM), (1000, Z_PM), 4, '1.000', fs=FS)
    vb.dim((1000, Z_PM), (2000, Z_PM), 4, '1.000', fs=FS)
    vb.dim((2000, Z_NPP), (2000, Z_PM), -9, '1.100', fs=FS)
    vb.dim((2000, Z_NPP), (2000, Z_NPP + 500), -4, '500', fs=FS)
    vb.dim((-150, Z_NPP), (-150, Z_NPP + 150), 4, '150', fs=FS, tside=1)
    sh.lead(*vb.p(500, Z_NPP + 75), 260, 196, 'rodapié 150', fs=FS, ha='left') if False else None
    sh.labels([(vb.X(1000), vb.Y(700), 'montante 50×50×3 en cada ménsula', vb.Y(1500)),
               (vb.X(1500), vb.Y(81), 'larguero UPN 80 / ménsula UPC 80 (debajo)', vb.Y(-160))],
              vb.X(1150), ha='left', fs=FS, sp=4.0) if False else None
    sh.lead(*vb.p(1000, 900), vb.X(1150), vb.Y(1450), 'montante 50×50×3 en cada ménsula', fs=FS, ha='left')
    sh.lead(*vb.p(1000, Z_TI - 15), vb.X(1150), vb.Y(-140), 'ménsula UPC 80 (c/1,00)', fs=FS, ha='left')

    # ===================== C — PLANTA EN EL CRUCE DE UN TABIQUE 1:20 =====================
    sh.vtitle(216, 182, 'C — PLANTA EN EL CRUCE DE UN TABIQUE   Esc. 1:25')
    vc = View(sh, 282, 112, 25)
    # tabique (bajo)
    vc.R(-125, -150, 250, 1800, fc=C_WOOD, lw=0.4)
    vc.R(-100, -150, 200, 1800, fc='#efefef', lw=0.3)
    # columna C1
    vc.R(-100, 1350, 200, 200, fc=C_DARK, lw=0.5)
    # tubos con junta
    vc.R(-1250, -100, 1240, 200, fc='#d0d0d0', lw=LW)
    vc.R(10, -100, 1240, 200, fc='#d0d0d0', lw=LW)
    # menusulas y cartelas, montantes
    for s0 in (-1250, -250, 250, 1250):
        vc.R(s0 - 22.5, 100, 45, 1164, fc='#999999', lw=0.4)
        vc.R(s0 - 6, 100, 12, 250, fc='#555555', lw=0.2)
        vc.R(s0 - 25, X_MT, 50, 50, fc='white', lw=0.6)
    # larguero (dos tramos, sin vincular)
    vc.R(-1250, 1219, 1240, 45, fc='#bbbbbb', lw=0.4)
    vc.R(10, 1219, 1240, 45, fc='#bbbbbb', lw=0.4)
    # rejilla (dos paneles con junta sobre el tabique)
    for a0, a1 in ((-1250, -10), (10, 1250)):
        xs, ys = [], []
        for ss in np.arange(a0, a1, 60):
            xs += [vc.X(ss), vc.X(ss), np.nan]
            ys += [vc.Y(350), vc.Y(1206), np.nan]
        for xx in np.arange(350, 1206, 60):
            xs += [vc.X(a0), vc.X(a1), np.nan]
            ys += [vc.Y(xx), vc.Y(xx), np.nan]
        sh.L(xs, ys, lw=0.2, c='#9a9a9a', chk=False, z=1)
        vc.R(a0, 350, a1 - a0, 856, fc='none', lw=0.5)
    for sg in (-1, 1):
        sh.breakline(*vc.p(sg * 1250, -130), *vc.p(sg * 1250, 1300))
    vc.cl((0, -170), (0, 1600))
    vc.dim((250, 1264), (1250, 1264), 7, '1.000', fs=FS)
    vc.dim((-1250, 1264), (-1250, 1350), 0, '86', ext=False, fs=4.6, tside=-1) if False else None
    sh.labels([(vc.X(-100), vc.Y(1450), 'columna existente C1'),
               (vc.X(-700), vc.Y(1240), 'larguero UPN 80 (dos tramos)'),
               (vc.X(-30), vc.Y(800), 'junta de rejilla y de viga\nsobre el tabique (20 mm)', vc.Y(1000)),
               (vc.X(-250), vc.Y(700), 'ménsula UPC 80 a 250\ndel eje del tabique', vc.Y(780)),
               (vc.X(-600), vc.Y(0), 'viga carrilera (tubo)', vc.Y(150)),
               (vc.X(60), vc.Y(-130), 'tabique (debajo)', vc.Y(-60))],
              vc.X(1300), ha='left', fs=FS, sp=4.8)

    # ===================== D — ESCALERA 1:75 =====================
    sh.vtitle(24, 110, 'D — ESCALERA EXTERIOR DE ACCESO   Esc. 1:100')
    vd = View(sh, 28, 56, 100)
    h = 4250 / 24
    g = 250
    pts = [(0, 0)]
    x, z = 0, 0
    for k in range(12):
        z += h
        pts.append((x, z))
        x += g if k < 11 else 0
        pts.append((x, z))
    xl = x
    x += 900
    pts.append((x, z))
    for k in range(12):
        z += h
        pts.append((x, z))
        x += g if k < 11 else 0
        pts.append((x, z))
    pts.append((x + 600, z))
    vd.L(pts, lw=0.6)
    vd.L([(0, 0), (xl + 900 + 11 * g + 600, 0)], lw=0.6)
    sh.ground(vd.X(-150), vd.X(xl + 900 + 11 * g + 700), vd.Y(0))
    vd.L([(0, 900), (xl, 12 * h + 900)], lw=0.6)
    vd.L([(xl + 900, 12 * h + 900), (xl + 900 + 11 * g, 24 * h + 900)], lw=0.6)
    vd.R(xl, 12 * h - 120, 900, 120, fc='k', lw=0.3)
    vd.L([(xl + 450, 0), (xl + 450, 12 * h - 120)], lw=1.0)
    vd.L([(xl + 900 + 11 * g + 300, 0), (xl + 900 + 11 * g + 300, 24 * h)], lw=1.0)
    vd.dim((0, 0), (xl, 0), -4, '2,75', fs=FS)
    vd.dim((xl, 0), (xl + 900, 0), -4, '0,90', fs=FS)
    vd.dim((xl + 900, 0), (xl + 900 + 11 * g, 0), -4, '2,75', fs=FS)
    vd.dim((xl + 900 + 11 * g + 600, 0), (xl + 900 + 11 * g + 600, 24 * h), -5, '4,25', fs=FS)
    sh.T(vd.X(0), 45.5 + 0 * vd.Y(0), '2 tramos × 12 alzadas (11 pedadas c/u)', fs=FS)
    sh.T(vd.X(0), 42.0 + 0 * vd.Y(0), 'h ≈ 177 · g = 250 · 2h + g = 604 mm', fs=FS)
    sh.T(vd.X(0), 38.5 + 0 * vd.Y(0), 'pendiente ≈ 35° · ancho 0,90 m', fs=FS)
    sh.lead(*vd.p(xl + 450, 12 * h - 60), vd.X(xl + 900), vd.Y(1300), 'descanso', fs=FS, ha='left')
    sh.lev(vd.X(xl + 900 + 11 * g + 1300), vd.Y(24 * h), 'NPP +4,05', ln=10)
    sh.lev(vd.X(xl + 900 + 11 * g + 1300), vd.Y(0), 'NTN −0,20', ln=10)

    # ===================== E — UNION MENSULA – TUBO 1:5 =====================
    sh.vtitle(124, 104, 'E — UNIÓN MÉNSULA–VIGA CON CARTELA   Esc. 1:10')
    ve = View(sh, 148, 66, 10)
    ve.R(-200, -20, 100, 320, fc='#e6e6e6', lw=LW)
    ve.R(-110, -20, 10, 320, fc='#bbbbbb', lw=0.4, hatch='////')
    sh.breakline(*ve.p(-210, -20), *ve.p(-90, -20))
    sh.breakline(*ve.p(-210, 300), *ve.p(-90, 300))
    ve.R(-100, 0, 380, 80, fc='#d9d9d9', lw=LW)
    ve.L([(-100, 7), (280, 7)], lw=0.3)
    ve.L([(-100, 73), (280, 73)], lw=0.3)
    sh.breakline(*ve.p(280, -10), *ve.p(280, 90))
    ve.P([(-100, 80), (-100, 260), (150, 80)], fc='#bdbdbd', lw=0.6, hatch='\\\\\\\\')
    # simbolos de soldadura (triangulos)
    for (x, z) in [(-100, 170), (25, 80), (-100, 40)]:
        ve.P([(x, z - 8), (x + 10, z - 8), (x, z + 2)], fc='k', lw=0.2)
    ve.dim((-100, 80), (150, 80), -1, '250', fs=FS, ext=False) if False else None
    ve.dim((-100, 0), (150, 0), -5, '250', fs=FS)
    sh.labels([(ve.X(-100), ve.Y(170), 'a6 · 2 × 180 (al tubo)', ve.Y(250)),
               (ve.X(25), ve.Y(80), 'a6 · 2 × 250 (al UPC)', ve.Y(170)),
               (ve.X(-100), ve.Y(40), 'a6 perimetral UPC – tubo', ve.Y(110)),
               (ve.X(20), ve.Y(150), 'cartela 250×180×12 F-24', ve.Y(210))],
              ve.X(170), ha='left', fs=FS, sp=4.0)
    sh.T(ve.X(-150), ve.Y(-120), 'cara lateral del tubo', fs=FS, ha='center')
    sh.T(ve.X(120), ve.Y(-60), 'ménsula UPC 80', fs=FS, ha='left') if False else None

    # ===================== TABLA =====================
    rows = [['Elemento', 'Especificación', 'Verificación'],
            ['Ménsula', 'UPC 80, vuelo 1.264, c/1,00 m (fuera de compuertas)', 'Mu = 6,15 kN·m'],
            ['Cartela ménsula – viga', '250 × 180 × 12 F-24, filete a6', 'F = 34,2 kN'],
            ['Larguero de borde', 'UPN 80', 'luz 1,00 m'],
            ['Rejilla de piso', 'electrosoldada galv. 30×30×3', '3 kN/m² (CIRSOC 101)'],
            ['Montante', 'caño 50×50×3 sobre cada ménsula', 'σ = 131,9 MPa'],
            ['Pasamanos / travesaño', 'caño 40×40×2 a +1,10 / 30×30×2 a +0,50', '1 kN/m · 1 kN'],
            ['Rodapié', 'chapa 150 × 3', '—']]
    sh.table(232, 104, [34, 95, 47], rows, rowh=4.6, fs=5.0)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/DET-09')
