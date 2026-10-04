from lib import *
import data as D
from sct02 import roof_top, roof_under, tab_top, XR
from PIL import Image

FS = 5.0
C_BRN = '#8b6b45'


def build(out):
    sh = Sheet('DET-12', 'Galpón existente — pórtico tipo, tabique y cerramiento',
               'Columnas intermedias a 4,00 m entre ejes · tabique de H° con suplemento de machimbre · cerramiento de chapa',
               '1:100 / 1:25 / 1:50 / 1:150 / 1:20', 13)
    W_ = D.ANCHO * 1000
    # ===================== A — PORTICO TIPO 1:100 =====================
    sh.vtitle(24, 276, 'A — PÓRTICO TIPO EN LÍNEA DE TABIQUE   Esc. 1:100')
    v = View(sh, 33, 197, 100)
    v.concrete([(0, -150), (W_, -150), (W_, 0), (0, 0)], seed=3, dens=0.06)
    v.R(0, -150, W_, 150, fc='none', lw=0.5)
    for xw in (-150, W_):
        v.R(xw, -350, 150, 4250, fc=C_EXIST, lw=0.5)
        v.R(xw - 150, -500, 450, 150, fc=C_EXIST, lw=0.4)
    sh.ground(v.X(-1000), v.X(-150), v.Y(-200))
    sh.ground(v.X(W_ + 150), v.X(W_ + 1000), v.Y(-200))
    for xw, xr in ((-75, 0), (W_ + 75, D.ANCHO)):
        v.L([(xw, 3900), (xw, roof_top(xr) * 1000 - 120)], lw=0.8)
    # tabique en vista
    v.R(0, 0, W_, 3000, fc='#ececec', lw=0.5)
    for xx in np.arange(1000, W_, 1000):
        v.L([(xx, 0), (xx, 3000)], lw=0.2, c='#b0b0b0', chk=False)
    v.P([(5700, 3000), (8100, 3900), (W_, 3900), (W_, 3000)], fc=C_WOOD, lw=0.5)
    for zz in (3300, 3600):
        v.L([(5700 + (zz - 3000) / 900 * 2400, zz), (W_, zz)], lw=0.25, c='#a07d50', chk=False)
    v.P([(7400, tab_top(7.4) * 1000), (8100, 3900), (7400, 3900)], fc='#cfcfcf', lw=0.4)
    # columnas intermedias + viga longitudinal
    for xc in (D.X_C1, D.X_C2):
        v.R(xc * 1000 - 100, 0, 200, 5760, fc=C_EXIST, lw=0.6)
        v.R(xc * 1000 - 100, 5760, 200, roof_under(xc) * 1000 - 5760 + 120, fc=C_BRN, lw=0.4)
    # cubierta
    xs = np.linspace(-300, W_ + 300, 50)
    top = [roof_top(min(max(x / 1000, 0), D.ANCHO)) * 1000 for x in xs]
    v.L(list(zip(xs, top)), lw=1.3)
    v.P([(0, roof_top(0) * 1000 - 50), (XR * 1000, roof_top(XR) * 1000 - 50), (W_, roof_top(D.ANCHO) * 1000 - 50),
         (W_, roof_top(D.ANCHO) * 1000 - 300), (XR * 1000, roof_top(XR) * 1000 - 300),
         (0, roof_top(0) * 1000 - 300)], fc=C_WOOD, lw=0.4)
    # lineas Redler (referencia)
    for xa in (D.X_L1, D.X_L2):
        X1 = xa * 1000
        v.R(X1 - 100, 3941, 200, 300, fc='white', lw=0.4)
        v.R(X1 - 304, 4341, 608, 810, fc=C_NEW, lw=0.5)
        v.cl((X1, -100), (X1, 5450))
    # cotas
    for a, b, t in ((0, D.X_C1, '9,35'), (D.X_C1, D.X_C2, '4,00'), (D.X_C2, D.ANCHO, '9,35')):
        v.dim((a * 1000, -150), (b * 1000, -150), -5, t, fs=FS)
    v.dim((0, -150), (W_, -150), -11, '22,70 (interior)', fs=FS)
    # niveles
    sh.lev(v.X(XR * 1000), v.Y(roof_top(XR) * 1000), 'NTT +6,55', ln=13, fs=4.8)
    sh.lev(v.X(1200), v.Y(roof_top(1.2) * 1000), 'NTT +5,60 (oeste)', ln=13, fs=4.8) if False else None
    sh.lev(v.X(20300), v.Y(3900), '+3,90', ln=9, fs=4.8)
    sh.lev(v.X(3300), v.Y(3000), '+3,00', ln=9, fs=4.8)
    sh.lev(v.X(20300), v.Y(0), '±0,00', ln=9, fs=4.8)
    # referencias
    sh.lead(*v.p(1000, roof_top(1.0) * 1000 - 180), 52, 266, 'cabios + correas de madera, cubierta de chapa', fs=FS,
            ha='left')
    sh.lead(*v.p(D.X_C1 * 1000, 5800), 110, 270, '+5,76 inf. viga longitudinal (madera)', fs=FS, ha='left')
    sh.lead(*v.p(D.X_L1 * 1000 - 304, 4900), v.X(6000), v.Y(4900), 'Redler L1 (proyecto)', fs=FS, ha='right')
    sh.lead(*v.p(D.X_L2 * 1000 + 304, 4900), v.X(16600), v.Y(4900), 'Redler L2 (proyecto)', fs=FS, ha='left')
    sh.lead(*v.p(D.X_C2 * 1000 + 100, 1600), v.X(15000), v.Y(1000), 'columnas intermedias existentes', fs=FS,
            ha='left')
    sh.lead(*v.p(16000, 3500), v.X(17000), v.Y(2300), 'suplemento de machimbre', fs=FS, ha='left')
    sh.lead(*v.p(7600, 3800), v.X(6000), v.Y(4300), 'dado de H° (ver F)', fs=FS, ha='right')
    sh.T(v.X(1800), v.Y(1500), 'tabique H° (ver B)', fs=FS)
    sh.T(v.X(-500), v.Y(4400), 'muro + chapa (ver C)', fs=4.6, ha='left', rot=90) if False else None

    # ===================== D — RELEVAMIENTO FOTOGRAFICO =====================
    sh.vtitle(270, 276, 'D — RELEVAMIENTO FOTOGRÁFICO')
    caps = [('1 · Interior de box: tabiques de H° y columnas', 'intermedias sobre la línea de tabique'),
            ('2 · Tope de tabique (+3,90) con suplemento', 'de machimbre y columna'),
            ('3 · Cerramiento: chapa sobre correas de', 'madera, columna en muro'),
            ('4 · Box vacío: pórticos de madera y viga', 'longitudinal sobre columnas')]
    pw, ph = 64.0, 35.3
    for i in range(4):
        x0 = 271 + (i % 2) * (pw + 5)
        y1 = 269 - (i // 2) * (ph + 13)
        img = np.asarray(Image.open(f'img/foto{i + 1}.png'))
        sh.ax.imshow(img, extent=(x0, x0 + pw, y1 - ph, y1), zorder=2, interpolation='bilinear')
        sh.P([(x0, y1 - ph), (x0 + pw, y1 - ph), (x0 + pw, y1), (x0, y1)], fc='none', lw=0.6, chk=False)
        sh.T(x0, y1 - ph - 2.6, caps[i][0], fs=4.6)
        sh.T(x0, y1 - ph - 5.2, caps[i][1], fs=4.6)

    # ===================== B — TABIQUE 1:25 =====================
    sh.vtitle(24, 176, 'B — TABIQUE H° + MACHIMBRE (corte)   Esc. 1:25')
    vb = View(sh, 60, 92, 25, mx=0, my=0)   # z: tramo superior desplazado (quiebre)
    DZ = 2300   # el tramo superior (z>=2.80) se dibuja bajado DZ mm

    def zb(z):
        return z - DZ if z >= 2700 else z
    # fundacion y losa
    vb.concrete([(-450, -600), (450, -600), (450, -300), (-450, -300)], seed=4)
    vb.R(-450, -600, 900, 300, fc='none', lw=0.6)
    vb.concrete([(-700, -150), (-100, -150), (-100, 0), (-700, 0)], seed=5)
    vb.concrete([(100, -150), (700, -150), (700, 0), (100, 0)], seed=6)
    vb.R(-700, -150, 600, 150, fc='none', lw=0.6)
    vb.R(100, -150, 600, 150, fc='none', lw=0.6)
    for xa, xb_ in ((-700, -100), (100, 700)):
        vb.R(xa, -300, xb_ - xa, 150, fc='#f3f3f3', lw=0.4, hatch='....')
    # tabique tramo inferior (-0.30 a +0.60)
    vb.concrete([(-100, -300), (100, -300), (100, 600), (-100, 600)], seed=7)
    vb.R(-100, -300, 200, 900, fc='none', lw=0.7)
    sh.breakline(*vb.p(-160, 600), *vb.p(160, 600))
    # tramo superior (+2,70 a +3,90) dibujado con quiebre
    vb.concrete([(-100, zb(2700)), (100, zb(2700)), (100, zb(3000)), (-100, zb(3000))], seed=8)
    vb.R(-100, zb(2700), 200, 300, fc='none', lw=0.7)
    sh.breakline(*vb.p(-160, zb(2700)), *vb.p(160, zb(2700)))
    vb.concrete([(-100, zb(3000)), (100, zb(3000)), (100, zb(3900)), (-100, zb(3900))], seed=9)
    vb.R(-100, zb(3000), 200, 900, fc='none', lw=0.7)
    for xa in (-125, 100):
        vb.R(xa, zb(3000), 25, 900, fc=C_WOOD, lw=0.5, hatch='////')
    vb.L([(-125, zb(3000)), (125, zb(3000))], lw=0.6, ls=(0, (3, 2)))
    # armaduras (puntos y barras)
    for xa in (-60, 60):
        vb.L([(xa, -560), (xa, 600)], lw=0.5, c='#444444')
        vb.L([(xa, zb(2700)), (xa, zb(2950))], lw=0.5, c='#444444')
    for zz in (-100, 100, 300, 500):
        for xa in (-60, 60):
            vb.C(xa, zz, 8, fc='k', lw=0.2)
    # placa de apoyo
    vb.R(-90, zb(3900), 180, 18, fc='#888888', lw=0.4)
    # cotas
    vb.dim((-100, zb(3900) + 18), (100, zb(3900) + 18), 6, '200', fs=FS)
    vb.dim((-125, zb(3000)), (-125, zb(3900)), 7, '0,90', fs=FS)
    vb.dim((-450, -600), (450, -600), -5, '0,90', fs=FS)
    vb.dim((450, -600), (450, -300), -5, '0,30', fs=FS)
    sh.lev(vb.X(-500), vb.Y(0), '±0,00', side='right', ln=8, fs=4.8)
    sh.lev(vb.X(700), vb.Y(zb(3900)) + 0.0, '+3,90', side='right', ln=8, fs=4.8)
    sh.lev(vb.X(700), vb.Y(zb(3000)), '+3,00', side='right', ln=8, fs=4.8)
    sh.labels([(vb.X(90), vb.Y(zb(3909)), 'placa de apoyo 1.000×180×18 (DET-07)', vb.Y(zb(4150))),
               (vb.X(112), vb.Y(zb(3500)), 'suplemento: 2 tablas e = 25\n+ núcleo de H°', vb.Y(zb(3600))),
               (vb.X(125), vb.Y(zb(3000)), 'junta de hormigonado', vb.Y(zb(2850))),
               (vb.X(60), vb.Y(300), 'armadura c/20 en ambas direcciones', vb.Y(500)),
               (vb.X(800), vb.Y(-75), 'losa 0,15 + base 0,15', vb.Y(150)),
               (vb.X(300), vb.Y(-500), 'fundación corrida de H°', vb.Y(-560))],
              vb.X(1600), ha='left', fs=FS, sp=5)

    # ===================== C — MURO PERIMETRAL 1:50 =====================
    sh.vtitle(150, 176, 'C — MURO PERIMETRAL (corte)   Esc. 1:50')
    vc = View(sh, 205, 70, 50)
    DZC = 2000

    def zc(z):
        return z - DZC if z >= 2900 else z
    vc.concrete([(-300, -500), (150, -500), (150, -350), (-300, -350)], seed=2)
    vc.R(-300, -500, 450, 150, fc='none', lw=0.6)
    vc.concrete([(0, -350), (150, -350), (150, 700), (0, 700)], seed=3)
    vc.R(0, -350, 150, 1050, fc='none', lw=0.6)
    sh.breakline(*vc.p(-60, 700), *vc.p(210, 700))
    vc.concrete([(150, -150), (1100, -150), (1100, 0), (150, 0)], seed=4)
    vc.R(150, -150, 950, 150, fc='none', lw=0.6)
    sh.ground(vc.X(-900), vc.X(0), vc.Y(-200))
    vc.concrete([(0, zc(3300)), (150, zc(3300)), (150, zc(3900)), (0, zc(3900))], seed=5)
    vc.R(0, zc(3300), 150, 600, fc='none', lw=0.6)
    sh.breakline(*vc.p(-60, zc(3300)), *vc.p(210, zc(3300)))
    # chapa + correas + cabio
    zr = roof_top(0) * 1000
    vc.L([(-20, zc(3850)), (-20, zc(zr) - 60)], lw=0.9)
    for zz in (4300, 5000):
        vc.R(-15, zc(zz), 50, 75, fc=C_WOOD, lw=0.4)
    vc.L([(-400, zc(zr) - 60), (1100, zc(zr) - 60 + 1500 * 0.0837)], lw=1.3)
    vc.P([(0, zc(zr) - 110), (1100, zc(zr) - 110 + 1100 * 0.0837), (1100, zc(zr) - 360 + 1100 * 0.0837),
          (0, zc(zr) - 360)], fc=C_WOOD, lw=0.4)
    sh.lev(vc.X(600), vc.Y(zc(zr) + 30), 'NTT +5,60', side='right', ln=10, fs=4.8)
    sh.lev(vc.X(700), vc.Y(zc(3900)), '+3,90', side='right', ln=9, fs=4.8)
    sh.lev(vc.X(700), vc.Y(0), '±0,00', side='right', ln=9, fs=4.8)
    vc.dim((0, zc(3600)), (150, zc(3600)), -6, '0,15', fs=FS) if False else None
    sh.labels([(vc.X(300), vc.Y(zc(zr) - 200), 'cabio de madera', vc.Y(zc(zr) + 300)),
               (vc.X(-20), vc.Y(zc(4600)), 'chapa ondulada', vc.Y(zc(4650))),
               (vc.X(10), vc.Y(zc(4337)), 'correas de madera', vc.Y(zc(4250))),
               (vc.X(75), vc.Y(zc(3600)), 'muro H° e = 0,15', vc.Y(zc(3550))),
               (vc.X(-200), vc.Y(-430), 'zapata corrida 0,45 × 0,15', vc.Y(-650))],
              vc.X(-700), ha='right', fs=FS, sp=5)

    # ===================== E — SUPLEMENTO 1:150 =====================
    sh.vtitle(232, 176, 'E — TABIQUE INTERIOR T1 a T4 · CORTE DEL SUPLEMENTO   Esc. 1:150')
    ve = View(sh, 247, 124, 150, my=0)
    ve.R(0, 0, W_, 3000, fc='#ececec', lw=0.5)
    for xx in np.arange(1000, W_, 1000):
        ve.L([(xx, 0), (xx, 3000)], lw=0.2, c='#b0b0b0', chk=False)
    ve.P([(5700, 3000), (8100, 3900), (W_, 3900), (W_, 3000)], fc=C_WOOD, lw=0.5)
    ve.P([(7400, tab_top(7.4) * 1000), (8100, 3900), (7400, 3900)], fc='#9a9a9a', lw=0.4)
    ve.L([(0, 0), (W_, 0)], lw=1.0)
    for xa, t in ((D.X_L1, 'L1'), (D.X_L2, 'L2')):
        ve.cl((xa * 1000, -200), (xa * 1000, 4300))
        sh.T(ve.X(xa * 1000) + (-1.2 if t == 'L1' else 1.2), ve.Y(4230), t, fs=5.2, ha=('right' if t == 'L1' else 'left'), bold=True, c='#1f4e79')
    for a, b, t in ((0, 5.70, '5,70'), (5.70, 8.10, '2,40'), (8.10, D.ANCHO, '14,60')):
        ve.dim((a * 1000, 3900), (b * 1000, 3900), 5, t, fs=FS)
    ve.dim((5700, 3900), (W_, 3900), 10.5, '17,00 (suplemento)', fs=FS)
    for a, b, t in ((0, D.X_L1, '7,90'), (D.X_L1, D.X_L2, '6,90'), (D.X_L2, D.ANCHO, '7,90')):
        ve.dim((a * 1000, 0), (b * 1000, 0), -4, t, fs=4.6)
    ve.dim((0, 0), (W_, 0), -9.5, '22,70 (interior)', fs=FS)
    sh.lev(ve.X(W_) + 4, ve.Y(3900), '+3,90', ln=8, fs=4.8)
    sh.lev(ve.X(W_) + 4, ve.Y(0), '±0,00', ln=8, fs=4.8)
    sh.lev(ve.X(1000), ve.Y(3000), '+3,00', ln=8, fs=4.8)
    sh.T(ve.X(2800), ve.Y(1500), 'H° (sin suplemento)', fs=FS, ha='center')
    sh.T(ve.X(15500), ve.Y(1500), 'tabique H° h = 3,00', fs=FS, ha='center')
    sh.T(ve.X(18800), ve.Y(3450), 'suplemento de machimbre (H° entre tablas)', fs=4.6, ha='center')
    sh.lead(*ve.p(7650, 3780), ve.X(5000), ve.Y(3450), 'dado de H° (ver F)', fs=4.6, ha='right')
    sh.T(ve.X(-200), ve.Y(1500), 'muro oeste\n(portones)', fs=4.4, ha='right') if False else None

    # ===================== F — DADO DE APOYO L1 1:20 =====================
    sh.vtitle(232, 106, 'F — DADO DE APOYO DE L1 (vista del tabique)   Esc. 1:20')
    X1 = D.X_L1 * 1000
    vf = View(sh, 290, 60, 20, mx=X1, my=3500)
    xl, xr_ = X1 - 800, X1 + 800
    prof = [(x, tab_top(x / 1000) * 1000) for x in np.linspace(xl, xr_, 40)]
    vf.P([(xl, 3500)] + prof + [(xr_, 3500)], fc=C_WOOD, lw=0.5)
    sh.breakline(*vf.p(xl, 3500), *vf.p(xr_, 3500))
    sh.breakline(*vf.p(xl, 3500), *vf.p(xl, tab_top(xl / 1000) * 1000))
    sh.breakline(*vf.p(xr_, 3500), *vf.p(xr_, 3900))
    vf.P([(X1 - 500, tab_top((X1 - 500) / 1000) * 1000), (8100, 3900), (X1 + 500, 3900), (X1 - 500, 3900)],
         fc='#cfcfcf', lw=0.6)
    # barras Ø10 c/200
    for xb_ in (X1 - 300, X1 - 100):
        zbot = tab_top(xb_ / 1000) * 1000
        vf.L([(xb_, zbot - 100), (xb_, 3870)], lw=0.8, c='#333333')
    # anclajes M16
    for xa in (X1 - 450, X1 + 450):
        vf.L([(xa, 3941 + 30), (xa, tab_top(xa / 1000) * 1000 - 125)], lw=1.0, ls=(0, (2, 1)))
    # placa, asiento, placas base, tubo, cartelas
    vf.R(X1 - 500, 3900, 1000, 18, fc='#888888', lw=0.4)
    vf.R(X1 - 500, 3923, 1000, 18, fc='#aaaaaa', lw=0.4)
    for sg in (-1, 1):
        vf.P([(X1 + sg * 100, 3941), (X1 + sg * 500, 3941), (X1 + sg * 500, 4001), (X1 + sg * 100, 4141)],
             fc='#e2e2e2', lw=0.4)
    vf.ipn_like_tube(X1, 3941, 200, 300, 10)
    # cotas
    vf.dim((X1 - 500, 3500), (X1 + 500, 3500), -3.5, '1.000', fs=FS)
    vf.dim((X1 - 500, tab_top((X1 - 500) / 1000) * 1000), (X1 - 500, 3900), -9, '263', fs=4.6)
    sh.lev(vf.X(xr_) + 3, vf.Y(3900), '+3,90', ln=8, fs=4.8)
    sh.labels([(vf.X(X1 + 60), vf.Y(4200), 'tubo 300×200×10 (viga carrilera)', 95),
               (vf.X(X1 + 300), vf.Y(4010), 'cartelas 400×200×12', 90),
               (vf.X(X1 + 300), vf.Y(3909), 'placa 1.000×180×18 + chapa de asiento', 85),
               (vf.X(X1 + 450), vf.Y(3800), 'anclajes químicos M16 (DET-07)', 80),
               (vf.X(X1 - 200), vf.Y(3700), 'dado H° H-21 1.000 × 200 (ancho del núcleo),\nsuperficie picada + puente de adherencia', 75),
               (vf.X(X1 - 100), vf.Y(3800), '2 barras Ø10 c/200 ancladas con epoxi (hef 100)', 68),
               (vf.X(X1 + 600), vf.Y(3650), 'suplemento de machimbre (pendiente)', 63)],
              vf.X(xr_) + 14, ha='left', fs=4.6, sp=4.6)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/DET-12')
