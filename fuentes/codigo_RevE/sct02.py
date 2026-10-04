from lib import *
import data as D
import math

ROOF_W, ROOF_R, ROOF_E = 5.60, 6.55, 5.75
XR = 11.35


def roof_top(x):
    if x <= XR:
        return ROOF_W + (ROOF_R - ROOF_W) * x / XR
    return ROOF_R - (ROOF_R - ROOF_E) * (x - XR) / (D.ANCHO - XR)


def roof_under(x):
    return roof_top(x) - 0.35


def tab_top(x):
    """Perfil superior del tabique (con suplemento) en m."""
    if x <= 5.70:
        return 3.00
    if x <= 8.10:
        return 3.00 + 0.90 * (x - 5.70) / 2.40
    return 3.90


def redler_section(v, xa, side, sh, detailed=False):
    """Seccion simplificada de una linea (v en mm, x en mm absolutos, z en mm absolutos)."""
    za = 3900
    zt0, zt1 = 3941, 4241
    v.R(xa - 100, zt0, 200, 300, fc='white', lw=0.5, hatch='////')
    v.R(xa - 400, 4241, 800, 100, fc=C_STEEL, lw=0.3)
    v.R(xa - 304, 4341, 608, 810, fc=C_NEW, lw=0.6)
    v.L([(xa - 304, 4745), (xa + 304, 4745)], lw=0.3)
    v.R(xa - 185, 4355, 370, 280, fc=C_NEW2, lw=0.3)
    # pasarela
    s = side
    x0, x1 = xa + s * 100, xa + s * 1264
    v.R(min(x0, x1), 3941, abs(x1 - x0), 80, fc='#d0d0d0', lw=0.4)
    xr0, xr1 = xa + s * 350, xa + s * 1206
    v.R(min(xr0, xr1), 4021, abs(xr1 - xr0), 30, fc='#eeeeee', lw=0.3)
    xm = xa + s * 1234
    v.L([(xm, 4021), (xm, 5151)], lw=0.8)
    v.L([(xa + s * 1209, 5151), (xa + s * 1259, 5151)], lw=1.0)
    v.L([(xa + s * 1209, 4551), (xa + s * 1259, 4551)], lw=0.6)
    v.P([(x0, 4021), (x0, 4201), (xa + s * 350, 4021)], fc='#bdbdbd', lw=0.4)
    # bandejas lado opuesto
    for zb in (4541, 4801):
        xb0 = xa - s * 354
        xb1 = xa - s * 504
        v.R(min(xb0, xb1), zb, 150, 60, fc='none', lw=0.4)


def build(out):
    sh = Sheet('CT-02', 'Corte transversal A-A',
               'Plano y = 9,30 m desde el muro sur (box 2), mirando al norte, hacia el tabique T2 · galpón vacío, sin producto',
               '1:75 / 1:25', 3)
    FS = 5.0
    # ===================== CORTE A-A 1:75 =====================
    sh.vtitle(26, 281, 'CORTE A-A   Esc. 1:75')
    v = View(sh, 50, 190, 75)
    W_ = D.ANCHO * 1000
    # piso y fundaciones
    v.concrete([(0, -150), (W_, -150), (W_, 0), (0, 0)], seed=11, dens=0.05)
    v.R(0, -150, W_, 150, fc='none', lw=0.6)
    for xw in (-150, W_):
        v.concrete([(xw, -350), (xw + 150, -350), (xw + 150, 3900), (xw, 3900)], seed=int(xw) % 7 + 2,
                   dens=0.05)
        v.R(xw, -350, 150, 4250, fc='none', lw=0.6)
        v.R(xw - 150, -500, 450, 150, fc=C_EXIST, lw=0.5)
    sh.ground(v.X(-1100), v.X(-450), v.Y(-200))
    sh.ground(v.X(W_ + 450), v.X(W_ + 1100), v.Y(-200))
    # cerramiento de chapa sobre los muros
    for xw in (-75, W_ + 75):
        v.L([(xw, 3900), (xw, (roof_top(0) if xw < 0 else roof_top(D.ANCHO)) * 1000 - 100)], lw=0.8)
    # tabique T2 en vista (H° hasta +3,00 + suplemento)
    v.R(0, 0, W_, 3000, fc='#ececec', lw=0.5)
    sup = [(5700, 3000), (8100, 3900), (W_, 3900), (W_, 3000)]
    v.P(sup, fc=C_WOOD, lw=0.5)
    for zz in (3300, 3600):
        xs0 = 5700 + (zz - 3000) / 900 * 2400
        v.L([(xs0, zz), (W_, zz)], lw=0.25, c='#a07d50')
    for xx in np.arange(1000, W_, 1000):
        v.L([(xx, 0), (xx, 3000)], lw=0.2, c='#b0b0b0', chk=False)
    # dado de H° bajo la placa de L1
    xd0, xd1 = D.X_L1 * 1000 - 500, D.X_L1 * 1000 + 500
    v.P([(xd0, tab_top(xd0 / 1000) * 1000), (8100, 3900), (xd1, 3900), (xd1, 3900), (xd0, 3900)],
        fc='#cfcfcf', lw=0.5)
    # columnas existentes (detras, sobre la linea del tabique)
    for xc in (D.X_C1, D.X_C2):
        v.R(xc * 1000 - 100, 0, 200, 5760, fc=C_EXIST, lw=0.6)
        v.R(xc * 1000 - 100, 5760, 200, (roof_under(xc) * 1000) - 5760, fc='#8b6b45', lw=0.4)
    # cubierta
    xs = np.linspace(-300, W_ + 300, 60)
    top = [roof_top(min(max(x / 1000, 0), D.ANCHO)) * 1000 + (0 if 0 <= x <= W_ else 0) for x in xs]
    v.L(list(zip(xs, top)), lw=1.4)
    v.L(list(zip(xs[3:-3], [t - 350 for t in top[3:-3]])), lw=0.5)
    v.P([(0, roof_top(0) * 1000 - 50), (XR * 1000, roof_top(XR) * 1000 - 50), (W_, roof_top(D.ANCHO) * 1000 - 50),
         (W_, roof_top(D.ANCHO) * 1000 - 300), (XR * 1000, roof_top(XR) * 1000 - 300),
         (0, roof_top(0) * 1000 - 300)], fc=C_WOOD, lw=0.4)
    for xx in np.arange(800, W_, 1500):
        zt = roof_top(xx / 1000) * 1000
        v.R(xx - 60, zt - 50, 120, 50, fc='white', lw=0.3)
    # lineas Redler
    redler_section(v, D.X_L1 * 1000, +1, sh)
    redler_section(v, D.X_L2 * 1000, -1, sh)
    v.cl((D.X_L1 * 1000, -200), (D.X_L1 * 1000, 5600))
    v.cl((D.X_L2 * 1000, -200), (D.X_L2 * 1000, 5600))
    # cotas
    pts = [0, D.X_L1, D.X_C1, D.X_C2, D.X_L2, D.ANCHO]
    txt = ['7,90', '1,45', '4,00', '1,45', '7,90']
    for a, b, t in zip(pts[:-1], pts[1:], txt):
        v.dim((a * 1000, -150), (b * 1000, -150), -6, t, fs=FS)
    v.dim((0, -150), (W_, -150), -12, '22,70 (ancho interior)', fs=FS)
    # galibos
    for xa, sg in ((D.X_L1, 1), (D.X_L2, -1)):
        xg = (xa + sg * 0.75) * 1000
        zu = roof_under(xa + sg * 0.75) * 1000
        v.dim((xg, 4051), (xg, zu), 0, f'gálibo {fmt_m((zu - 4051) / 1000)}', ext=False, fs=4.6)
    # niveles
    levs_r = [(3900, '+3,90 tope machimbre'), (3000, '+3,00 tabique H°'), (0, '±0,00 NPT'),
              (roof_top(D.ANCHO) * 1000, 'NTT +5,75')]
    for z, t in levs_r:
        sh.lev(v.X(W_ + 700), v.Y(z), t, ln=22)
    sh.lev(v.X(-700), v.Y(roof_top(0) * 1000), 'NTT +5,60', side='left', ln=14)
    sh.lev(v.X(XR * 1000), v.Y(roof_top(XR) * 1000), 'NTT +6,55', ln=12)
    sh.lead(*v.p(D.X_L1 * 1000, 5151), v.X(5200), 276, 'Redler L1', fs=5.6, ha='right', bold=True)
    sh.lead(*v.p(D.X_L2 * 1000, 5151), v.X(17300), 276, 'Redler L2', fs=5.6, ha='left', bold=True)
    sh.lead(*v.p(D.X_C1 * 1000, 5000), v.X(10000), 268.5, 'C1 columna existente', fs=FS, ha='left')
    sh.lead(*v.p(D.X_C2 * 1000, 4300), v.X(15900), 264, 'C2 columna existente', fs=FS, ha='left') if False else None
    sh.lead(*v.p(D.X_C2 * 1000, 2500), v.X(14200), v.Y(1800), 'C2 columna existente', fs=FS, ha='left')
    sh.lead(*v.p(D.X_L1 * 1000 - 300, 3700), v.X(3200), v.Y(4600), 'dado de H° bajo la placa de L1 (DET-12)', fs=FS,
            ha='right')
    sh.T(v.X(3000), v.Y(1500), 'Tabique T2 (H° + machimbre) en vista', fs=FS, ha='left')
    sh.T(v.X(16500), v.Y(3450), 'suplemento de machimbre', fs=FS, ha='center')
    sh.T(v.X(2900), v.Y(3250), 'tabique sin suplemento (tope +3,00)', fs=FS, ha='center') if False else None
    sh.lead(*v.p(18500, roof_top(18.5) * 1000 - 150), v.X(20000), 272, 'cabios / correas de madera', fs=FS,
            ha='left')
    sh.T(v.X(D.X_L1 * 1000 + 700), v.Y(3600), 'pasarela L1', fs=4.6, ha='center') if False else None
    sh.T(v.X(5600), v.Y(500), 'BOX 2 (plano de corte)  ← muro oeste (portones) · muro este →', fs=4.8,
         ha='center', c='#555555')

    # ===================== DETALLE 1 1:25 =====================
    sh.vtitle(26, 166, 'DETALLE 1 — L1, PASARELA Y COLUMNA C1   Esc. 1:25')
    vd = View(sh, 72, 74, 25, mx=D.X_L1 * 1000, my=3900)
    X1 = D.X_L1 * 1000
    xl, xr_ = X1 - 650, X1 + 1650
    # tabique con suplemento (en vista) y dado
    prof = [(x, tab_top(x / 1000) * 1000) for x in np.linspace(xl, xr_, 30)]
    v_poly = [(xl, 3550)] + prof + [(xr_, 3550)]
    vd.P(v_poly, fc=C_WOOD, lw=0.5)
    vd.P([(X1 - 500, tab_top((X1 - 500) / 1000) * 1000), (8100, 3900), (X1 + 500, 3900), (X1 - 500, 3900)],
         fc='#cfcfcf', lw=0.5)
    sh.breakline(*vd.p(xl, 3550), *vd.p(xr_, 3550))
    # placa de apoyo (detras, en T2) y cartelas
    vd.R(X1 - 500, 3900, 1000, 18, fc='#888888', lw=0.4)
    vd.R(X1 - 500, 3923, 1000, 18, fc='#aaaaaa', lw=0.4)
    for sg in (-1, 1):
        vd.P([(X1 + sg * 100, 3941), (X1 + sg * 500, 3941), (X1 + sg * 500, 4001), (X1 + sg * 100, 4141)],
             fc='#e2e2e2', lw=0.4)
    # pasarela L1 detallada
    vd.R(X1 + 100, 3941, 1164, 80, fc='#d0d0d0', lw=0.6)
    vd.P([(X1 + 100, 4021), (X1 + 100, 4201), (X1 + 350, 4021)], fc='#bdbdbd', lw=0.5)
    vd.R(X1 + 350, 4021, 856, 30, fc='#eeeeee', lw=0.4)
    vd.R(X1 + 1219, 3941, 45, 80, fc='white', lw=0.5, hatch='////')
    vd.R(X1 + 1206, 4051, 3, 150, fc='k', lw=0.2)
    vd.R(X1 + 1209, 4021, 50, 1110, fc='white', lw=0.6)
    vd.R(X1 + 1214, 5111, 40, 40, fc='white', lw=0.5, hatch='////')
    vd.R(X1 + 1179, 4536, 30, 30, fc='white', lw=0.5, hatch='////')
    # tubo, silleta, conducto
    vd.R(X1 - 100, 3941, 200, 300, fc='white', lw=0.6, hatch='////')
    vd.R(X1 - 400, 4241, 800, 100, fc=C_STEEL, lw=0.4)
    vd.R(X1 - 304, 4341, 608, 810, fc=C_NEW, lw=0.7)
    vd.L([(X1 - 300, 4745), (X1 + 300, 4745)], lw=0.5)
    vd.R(X1 - 185, 4355, 370, 280, fc=C_NEW2, lw=0.4)
    vd.R(X1 - 185, 4827, 370, 280, fc='#dde6ef', lw=0.4)
    for sg in (-1, 1):
        for zc in (4376, 5086):
            vd.R(X1 + sg * 241 - 49, zc - 25, 98, 50, fc='#777777', lw=0.3)
    # bandejas
    for zb in (4541, 4801):
        vd.R(X1 - 504, zb, 150, 60, fc='none', lw=0.6)
        vd.L([(X1 - 480, zb - 5), (X1 - 304, zb - 5)], lw=0.8)
    # columna C1
    vd.R(D.X_C1 * 1000 - 100, 3550, 200, 2500, fc=C_EXIST, lw=0.7)
    sh.breakline(*vd.p(D.X_C1 * 1000 - 150, 6050), *vd.p(D.X_C1 * 1000 + 150, 6050))
    # cubierta (cara inferior)
    xs = np.linspace(xl, xr_, 10)
    vd.L([(x, roof_under(x / 1000) * 1000) for x in xs], lw=0.8)
    vd.P([(xl, roof_under(xl / 1000) * 1000), (xr_, roof_under(xr_ / 1000) * 1000),
          (xr_, roof_under(xr_ / 1000) * 1000 + 120), (xl, roof_under(xl / 1000) * 1000 + 120)], fc=C_WOOD, lw=0.4)
    vd.cl((X1, 3560), (X1, 5400))
    vd.cl((D.X_C1 * 1000, 3560), (D.X_C1 * 1000, 6000))
    # cotas detalle
    vd.dim((X1 + 304, 5300), (X1 + 1209, 5300), 0, '0,905 paso libre', ext=False, fs=4.6)
    vd.dim((X1 + 1264, 4400), (D.X_C1 * 1000 - 100, 4400), 0, '86', ext=False, fs=4.6) if False else None
    vd.dim((X1, 3560), (D.X_C1 * 1000, 3560), -3, '1,45', fs=4.6)
    vd.dim((X1 + 1100, 4051), (X1 + 1100, 5151), 0, '1,10', ext=False, fs=4.6)
    # globos
    BL = [(1, (X1 - 300, 3910), (X1 - 1000, 3800)),
          (15, (X1 - 350, 3750), (X1 - 1000, 3650)),
          (2, (X1 - 60, 4100), (X1 - 1000, 4060)),
          (16, (X1 - 380, 4290), (X1 - 1000, 4290)),
          (14, (X1 - 504, 4590), (X1 - 1000, 4600)),
          (3, (X1 - 304, 5000), (X1 - 1000, 5000)),
          (4, (X1 - 241, 4376), (X1 - 1000, 4450)) if False else (4, (X1 + 241, 5086), (X1 + 500, 5600)),
          (5, (X1 + 100, 4500), (X1 + 600, 4800)),
          (13, (X1 + 150, 4100), (X1 + 600, 4400)),
          (7, (X1 + 800, 4036), (X1 + 900, 4300)),
          (6, (X1 + 700, 3981), (X1 + 700, 3720)),
          (8, (X1 + 1240, 3960), (X1 + 1000, 3700)),
          (11, (X1 + 1207, 4150), (X1 + 950, 4550)),
          (10, (X1 + 1194, 4551), (X1 + 950, 4950)),
          (9, (X1 + 1234, 4900), (X1 + 950, 5100)) if False else (9, (X1 + 1234, 4900), (X1 + 1000, 5150)),
          (12, (D.X_C1 * 1000 + 100, 5000), (D.X_C1 * 1000 + 450, 5200))]
    for n, pm, bm in BL:
        px, py = vd.p(*pm)
        bx, by = vd.p(*bm)
        lid = sh.nid()
        d = np.array([bx - px, by - py])
        dd = np.hypot(*d)
        e = np.array([bx, by]) - d / dd * 2.3
        sh.L([px, e[0]], [py, e[1]], lw=LW_T, owner=lid)
        sh.C(px, py, 0.35, fc='k', ec='k', lw=0.2, owner=lid, z=7)
        sh.balloon(bx, by, n)

    # ===================== TABLAS =====================
    rows = [['N.º', 'Elemento', 'Especificación'],
            ['1', 'Placa de apoyo sobre tabique', '1.000×180×18 F-24 + 4 anclajes químicos M16'],
            ['2', 'Viga carrilera', 'tubo 300×200×10 F-24, tramos simpl. apoyados'],
            ['3', 'Conducto Redler', '600×400 + 600×400, chapa 4/3 mm'],
            ['4', 'Cadena de arrastre', '2 × DIN 8167 M224 paso 200'],
            ['5', 'Paleta', '370×280×5 + L50×50×5, en cada eslabón'],
            ['6', 'Ménsula', 'UPC 80, c/1,00 m, vuelo 1,264'],
            ['7', 'Rejilla de piso', 'electrosoldada galv. 30×30×3'],
            ['8', 'Larguero de borde', 'UPN 80'],
            ['9', 'Montante de baranda', 'caño 50×50×3 en cada ménsula (c/1,00)'],
            ['10', 'Pasamanos / barra int.', '40×40×2 a +1,10 / 30×30×2 a +0,50'],
            ['11', 'Rodapié', 'chapa 150×3'],
            ['12', 'Columna existente C1', 'existente, 0,20×0,20'],
            ['13', 'Cartela ménsula–viga', '250×180×12 F-24, soldada a6 (DET-09)'],
            ['14', 'Bandejas portacables', '150×60 c/tapa: potencia y control (sep. 200)'],
            ['15', 'Dado de apoyo (solo L1)', 'H° H-21 1.000×200 hasta +3,90 (DET-12)'],
            ['16', 'Silleta', 'UPN 100 × 800, c/2,50 m']]
    sh.table(150, 160, [7, 38, 72], rows, rowh=3.9, fs=4.8)
    lv = [['Nivel', 'Elemento'],
          ['+3,90', 'tope de tabique / machimbre'],
          ['+3,918', 'cara sup. placa de apoyo'],
          ['+3,923', 'asiento (fijo) / PTFE + inox (libre)'],
          ['+3,941', 'inferior tubo y ménsula UPC 80'],
          ['+4,021', 'cara superior ménsula'],
          ['+4,05', 'NPP pasarela (rejilla)'],
          ['+4,241', 'cara superior tubo'],
          ['+4,341', 'inferior conducto (silletas UPN 100)'],
          ['+4,745', 'divisor trabajo / retorno'],
          ['+5,15', 'pasamanos (NPP + 1,10)'],
          ['+5,151', 'superior conducto (tapa)']]
    sh.table(272, 160, [14, 52], lv, rowh=3.9, fs=4.8)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/CT-02')
