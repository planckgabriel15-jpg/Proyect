from lib import *
import data as D

# z en mm medido desde el tope del tabique (+3,90)
Z_PL = 18; Z_AS = 23; Z_TI = 41; Z_TS = 341; Z_CI = 441


def nut(v, x, z0, w=24, h=13):
    v.R(x - w / 2 - 4, z0, w + 8, 3, fc='#999999', lw=0.3)
    v.R(x - w / 2, z0 + 3, w, h, fc='#666666', lw=0.3)


def build(out):
    sh = Sheet('DET-07', 'Apoyo de la viga carrilera sobre tabique interior',
               'Placa de apoyo 1.000×180×18 anclada al núcleo del tabique · extremo fijo soldado / extremo deslizante sobre PTFE',
               '1:5 / 1:10', 8)
    FS = 5.0
    # ===================== A — ELEVACION POR EL EJE DEL REDLER 1:5 =====================
    sh.vtitle(24, 276, 'A — ELEVACIÓN POR EL EJE DEL REDLER (corte y-z)   Esc. 1:5')
    v = View(sh, 112, 118, 5)
    W_ = 280
    v.concrete([(-100, -200), (100, -200), (100, 0), (-100, 0)], seed=4)
    v.R(-100, -200, 200, 200, fc='none', lw=LW)
    for sg in (-1, 1):
        v.R(min(sg * 100, sg * 125), -200, 25, 200, fc=C_WOOD, lw=0.5)
    sh.breakline(*v.p(-150, -200), *v.p(150, -200))
    v.R(-90, 0, 180, 18, fc='#888888', lw=0.5, hatch='////')
    v.R(-90, 18, 80, 3, fc='#ffffff', lw=0.4)
    v.R(-90, 21, 80, 2, fc='#bbbbbb', lw=0.3)
    v.R(-90, 23, 80, 18, fc='#888888', lw=0.5, hatch='////')
    v.R(10, 18, 80, 5, fc='#666666', lw=0.4)
    v.R(10, 23, 80, 18, fc='#888888', lw=0.5, hatch='////')
    v.P([(90, 23), (98, 23), (90, 31)], fc='k', lw=0.3)
    v.R(-W_, 41, W_ - 10, 300, fc='#e6e6e6', lw=LW)
    v.R(10, 41, W_ - 10, 300, fc='#e6e6e6', lw=LW)
    v.R(-20, 41, 10, 300, fc='#999999', lw=0.4)
    v.R(10, 41, 10, 300, fc='#999999', lw=0.4)
    for s0 in (-90, 78):
        v.R(s0, 41, 12, 200, fc='#bdbdbd', lw=0.5)
    for s0 in (-45, 45):
        v.L([(s0, -125), (s0, 57)], lw=1.4, c='#333333')
        v.L([(s0 - 8, -125), (s0 - 8, 0)], lw=0.3, ls=(0, (2, 1.5)))
        v.L([(s0 + 8, -125), (s0 + 8, 0)], lw=0.3, ls=(0, (2, 1.5)))
        nut(v, s0, 41)
    for s0 in (-250, 250):
        v.R(s0 - 22.5, 41, 45, 80, fc='#d9d9d9', lw=0.5)
        v.R(s0 - 6, 121, 12, 180, fc='#c8c8c8', lw=0.4)
    v.R(-W_, 441, 2 * W_, 4, fc='k', lw=0.3)
    v.R(-W_, 445, 2 * W_, 30, fc=C_NEW, lw=0.3)
    for sg in (-1, 1):
        sh.breakline(*v.p(sg * W_, 20), *v.p(sg * W_, 490))
    v.cl((0, -215), (0, 500))
    v.dim((-10, 475), (10, 475), 5, '20', fs=FS, textoff=3.2)
    v.dim((-90, 475), (-10, 475), 5, '80', fs=FS)
    v.dim((10, 475), (90, 475), 5, '80', fs=FS)
    v.dim((-90, 475), (90, 475), 11, '180 (placa de apoyo)', fs=FS, tpos=0.12)
    v.dim((0, 475), (250, 475), 17, '250', fs=FS, ext0=12.5)
    v.dim((-125, -200), (125, -200), -6, '250 (núcleo 200 + machimbre)', fs=FS)
    sh.labels([(v.X(-200), v.Y(300), 'viga que llega (tramo anterior):\nEXTREMO DESLIZANTE', v.Y(330)),
               (v.X(-15), v.Y(230), 'chapa de cierre del tubo e = 10', v.Y(240)),
               (v.X(-84), v.Y(150), 'cartela 400×200×12 (de canto)', v.Y(175)),
               (v.X(-250), v.Y(100), 'ménsula UPC 80 + cartela\n(a ± 250 del eje del tabique)', v.Y(110)),
               (v.X(-60), v.Y(32), 'placa base 1.000×80×18', v.Y(40)),
               (v.X(-60), v.Y(19.5), 'PTFE e = 3 + inox AISI 304 e = 2', v.Y(5)),
               (v.X(-45), v.Y(-60), 'anclaje químico M16 cal. 8.8\nhef 125, resina epoxi', v.Y(-45)),
               (v.X(-112), v.Y(-150), 'tabla de machimbre e = 25', v.Y(-150)),
               (v.X(0), v.Y(-180), 'núcleo de H° H-21', v.Y(-185))],
              22.5, ha='left', fs=4.8, sp=5.2)
    sh.labels([(v.X(200), v.Y(300), 'viga que sale (tramo\nsiguiente): EXTREMO FIJO', v.Y(330)),
               (v.X(94), v.Y(26), 'filete a6 · 2 × 80', v.Y(70)),
               (v.X(50), v.Y(20.5), 'chapa de asiento\n1.000×80×5', v.Y(10)),
               (v.X(70), v.Y(9), 'placa de apoyo\n1.000×180×18', v.Y(-60))],
              v.X(W_) + 5, ha='left', fs=4.8, sp=7.5)

    # ===================== B — VISTA TRANSVERSAL 1:10 =====================
    sh.vtitle(212, 276, 'B — VISTA TRANSVERSAL (a lo largo del tabique)   Esc. 1:10')
    vb = View(sh, 282, 218, 10)
    vb.R(-560, -200, 1260, 200, fc=C_WOOD, lw=0.5)
    sh.breakline(*vb.p(-560, -200), *vb.p(-560, 0))
    sh.breakline(*vb.p(700, -200), *vb.p(700, 0))
    for sg in (-1, 1):
        vb.L([(sg * 450 - 8, -125), (sg * 450 - 8, 0)], lw=0.3, ls=(0, (2, 1.5)))
        vb.L([(sg * 450 + 8, -125), (sg * 450 + 8, 0)], lw=0.3, ls=(0, (2, 1.5)))
    vb.R(-500, 0, 1000, 18, fc='#888888', lw=0.5)
    vb.R(-500, 18, 1000, 5, fc='#666666', lw=0.3)
    vb.R(-500, 23, 1000, 18, fc='#888888', lw=0.5)
    vb.R(100, 41, 600, 80, fc='#e9e9e9', lw=0.4)
    vb.P([(100, 121), (100, 301), (350, 121)], fc='#e9e9e9', lw=0.4)
    sh.breakline(*vb.p(700, 20), *vb.p(700, 140))
    for sg in (-1, 1):
        vb.P([(sg * 100, 41), (sg * 500, 41), (sg * 500, 101), (sg * 100, 241)], fc='#bdbdbd', lw=0.6)
    vb.R(-100, 41, 200, 300, fc='#999999', lw=LW)
    vb.R(-90, 51, 180, 280, fc='none', lw=0.3, ls=(0, (2, 1.5)))
    for sg in (-1, 1):
        nut(vb, sg * 450, 41)
    vb.R(-400, 341, 800, 100, fc=C_STEEL, lw=0.4)
    vb.R(-304, 441, 608, 50, fc=C_NEW, lw=0.5)
    sh.breakline(*vb.p(-380, 491), *vb.p(380, 491))
    vb.cl((0, -210), (0, 510))
    vb.dim((-500, 0), (500, 0), -24, '1.000 (placa de apoyo)', fs=FS)
    vb.dim((-450, -125), (450, -125), -4, '900 (anclajes)', fs=FS)
    vb.dim((-500, 241), (-100, 241), 4, '400', fs=FS)
    vb.dim((-500, 41), (-500, 241), 6, '200', fs=FS, tside=1)
    for z, s_ in [(441, '+4,341'), (341, '+4,241'), (41, '+3,941'), (0, '+3,90')]:
        sh.lev(vb.X(720), vb.Y(z), s_, ln=8)
    sh.labels([(vb.X(200), vb.Y(400), 'silleta UPN 100'),
               (vb.X(60), vb.Y(300), 'tubo + chapa de cierre', vb.Y(320)),
               (vb.X(300), vb.Y(120), 'cartela 400×200×12', vb.Y(270)),
               (vb.X(600), vb.Y(80), 'ménsula UPC 80\n(detrás)', vb.Y(150)),
               (vb.X(450), vb.Y(55), 'anclaje M16\n+ tuerca', vb.Y(-80))],
              366, ha='left', fs=4.8, sp=4.2)

    # ===================== C — PLANTA DE LA PLACA DE APOYO 1:10 =====================
    sh.vtitle(212, 170, 'C — PLANTA DE LA PLACA DE APOYO   Esc. 1:10')
    vc = View(sh, 290, 140, 10)
    vc.R(-560, -125, 1120, 250, fc=C_WOOD, lw=0.4)
    vc.R(-560, -100, 1120, 200, fc='#efefef', lw=0.3)
    vc.R(-500, -90, 1000, 180, fc='#cccccc', lw=0.6)
    vc.R(-500, -90, 1000, 80, fc='#e0e0e0', lw=0.5)
    vc.R(-500, 10, 1000, 80, fc='#e0e0e0', lw=0.5)
    vc.R(-100, -125, 200, 115, fc='none', lw=0.6, ls=(0, (3, 2)))
    vc.R(-100, 10, 200, 115, fc='none', lw=0.6, ls=(0, (3, 2)))
    for sg in (-1, 1):
        vc.R(min(sg * 100, sg * 500), -90, 400, 12, fc='#888888', lw=0.3)
        vc.R(min(sg * 100, sg * 500), 78, 400, 12, fc='#888888', lw=0.3)
        vc.C(sg * 450, 45, 9, fc='white', lw=0.5)
        vc.P([(sg * 450 - 9, -75), (sg * 450 + 9, -75), (sg * 450 + 9, -15), (sg * 450 - 9, -15)],
             fc='white', lw=0.5)
        vc.C(sg * 450, -45, 8, fc='#666666', lw=0.3)
        vc.R(sg * 500 - (4 if sg > 0 else 0), 10, 4, 80, fc='k', lw=0.2)
    vc.dim((-500, 125), (500, 125), 3, '1.000', fs=FS)
    vc.dim((560, -90), (560, -10), -3, '80', fs=4.6)
    vc.dim((560, 10), (560, 90), -3, '80', fs=4.6)
    sh.lead(vc.X(-450), vc.Y(45), 212.5, vc.Y(70), 'Ø18', fs=FS, ha='right') if False else None
    sh.lead(vc.X(-300), vc.Y(50), vc.X(-560), vc.Y(220), 'viga que sale — extremo fijo: agujeros redondos Ø18, filete a6 en ambos extremos', fs=4.8, ha='left')
    sh.lead(vc.X(-450), vc.Y(-60), vc.X(-560), vc.Y(-200), 'viga que llega — extremo libre: agujeros rasgados 18×60 según el eje (guían el deslizamiento)', fs=4.8, ha='left')
    sh.T(vc.X(0), vc.Y(-160), 'tubo', fs=4.6, ha='center') if False else None

    # ===================== TABLA =====================
    rows = [['Pieza (por tabique y por línea)', 'Especificación', 'Cant.'],
            ['Placa de apoyo', '1.000 × 180 × 18, F-24', '1'],
            ['Anclaje químico', 'M16 cal. 8.8, hef 125, resina epoxi', '4'],
            ['Placa base (por extremo de viga)', '1.000 × 80 × 18, F-24', '2'],
            ['Cartela (2 por extremo de viga)', '400 × 200 × 12, F-24', '4'],
            ['Chapa de asiento (extremo fijo)', '1.000 × 80 × 5, F-24', '1'],
            ['Soldadura placa base – asiento', 'filete a6, 2 × 80 mm (E70XX)', '—'],
            ['Deslizamiento (extremo libre)', 'PTFE e = 3 + inox AISI 304 e = 2', '1'],
            ['Chapa de cierre del tubo', '200 × 300 × 10, F-24', '2'],
            ['Nivelación', 'mortero epoxi ≤ 5 mm bajo placa', '—'],
            ['Dado de H° (solo línea L1)', 'H-21, 1.000 × 200 (ver DET-12)', '1']]
    sh.table(232, 104, [56, 106, 14], rows, rowh=4.0, fs=5.0)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/DET-07')
