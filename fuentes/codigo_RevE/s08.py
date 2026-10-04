from lib import *
import data as D
from sct02 import roof_top

FS = 5.0


def wall(v, u0, u1, ztop, zbot, seed):
    v.concrete([(u0, zbot), (u1, zbot), (u1, ztop), (u0, ztop)], seed=seed)
    v.R(min(u0, u1), zbot, abs(u1 - u0), ztop - zbot, fc='none', lw=LW)


def build(out):
    sh = Sheet('DET-08', 'Pasamuro y apoyos en los muros de cabecera',
               'Cabecera de recepción: entrada del Redler, plataforma y puerta de pasarela · Cabecera opuesta: cabezal motriz',
               '1:25 / 1:5', 9)
    ZR = roof_top(D.X_L1) * 1000
    # ===================== A — CABECERA DE RECEPCION 1:25 =====================
    sh.vtitle(24, 279, 'A — CABECERA DE RECEPCIÓN · CORTE POR EL EJE DE L1   Esc. 1:25')
    v = View(sh, 130, 160, 25, mx=0, my=3400)   # x = -u (u hacia afuera); z absoluto mm

    def X(u):
        return -u
    # muro sur y cerramiento
    wall(v, X(-175), X(175), 3900, 3400, 21)
    sh.breakline(*v.p(X(-260), 3400), *v.p(X(260), 3400))
    v.L([(X(175), 3900), (X(175), 4241)], lw=0.9)
    v.L([(X(175), 5251), (X(175), ZR - 40)], lw=0.9)
    for zz in (5500, 5950):
        v.R(X(175) , zz, 60, 60, fc=C_WOOD, lw=0.4)
    v.L([(X(-2100), ZR), (X(2400), ZR)], lw=1.2)
    # pasamuro: marco + faldon, babeta
    v.R(X(225), 4241, 50, 1010, fc='none', lw=0.6)
    v.P([(X(175), 5291), (X(420), 5180), (X(420), 5200), (X(175), 5320)], fc='#bdbdbd', lw=0.4)
    # placa de apoyo sobre el muro: fijo tramo 1 (adentro) / libre tramo 0 (afuera)
    v.R(X(-90), 3900, 180, 18, fc='#888888', lw=0.4)
    v.R(X(-90), 3918, 80, 5, fc='#666666', lw=0.3)
    v.R(X(10), 3918, 80, 5, fc='#bbbbbb', lw=0.3)
    v.R(X(-90), 3923, 80, 18, fc='#999999', lw=0.4)
    v.R(X(10), 3923, 80, 18, fc='#999999', lw=0.4)
    # vigas (tubo): tramo 1 hacia adentro, tramo 0 hacia afuera hasta B2
    v.R(X(-10), 3941, 1990, 300, fc='#e0e0e0', lw=LW)
    v.R(X(1900), 3941, 1890, 300, fc='#e0e0e0', lw=LW)
    sh.breakline(*v.p(X(-2000), 3900), *v.p(X(-2000), 4280))
    # viga B2 IPN 200 (corte) y plataforma
    v.R(X(1870), 3741, 90, 200, fc='white', lw=0.5, hatch='////')
    v.R(X(2500), 4021, 2325, 30, fc='none', lw=0.4, ls=(0, (3, 2)))
    v.R(X(400), 3941, 225, 80, fc='#bbbbbb', lw=0.4)
    sh.breakline(*v.p(X(2500), 3950), *v.p(X(2500), 4100))
    # conducto, boca de carga, cola
    v.R(X(1120), 4341, 3120, 810, fc=C_NEW, lw=LW)
    v.L([(X(-2000), 4745), (X(720), 4745)], lw=0.4, ls=(0, (4, 2)))
    sh.breakline(*v.p(X(-2000), 4300), *v.p(X(-2000), 5200))
    v.P([(X(1120), 4301), (X(1270), 4301 - 40 + 40), (X(2020), 4301), (X(2020), 5191), (X(1270), 5191),
         (X(1120), 5041)][0:0] or [(X(1120), 4301), (X(2020), 4301), (X(2020), 5191), (X(1120), 5191)],
        fc=C_NEW2, lw=LW)
    v.C(X(1570), 4731, 355, fc='none', lw=0.4, ls=(0, (5, 2)))
    v.C(X(1570), 4731, 70, fc='white', lw=0.6)
    v.R(X(1120), 5151, 400, 60, fc='#9fb3c8', lw=0.4)
    jx, jy = [], []
    for kk in range(9):
        xx = X(1100) + kk * 45
        jx += [v.X(xx), v.X(xx), np.nan]
        jy += [v.Y(5211), v.Y(5400), np.nan]
    sh.L(jx, jy, lw=0.4, chk=False)
    v.R(X(1120), 5211, 400, 190, fc='none', lw=0.6)
    v.P([(X(1070), 5400), (X(770), 5400), (X(620), ZR - 100), (X(920), ZR - 100)], fc='#e4ebf3', lw=LW)
    # puerta (mas alla)
    v.R(X(175) - 0, 4051, 0, 0, fc='none', lw=0)
    # cotas
    v.dim((X(0), 3741), (X(1825), 3741), 6, '1.825', fs=FS)
    v.dim((X(0), 3741), (X(1570), 3741), 12, '1.570 (eje de cola)', fs=FS)
    v.dim((X(175), 3650), (X(-175), 3650), 3, '350', fs=FS) if False else None
    for z, t in [(5151, '+5,151'), (4051, 'NPP +4,05'), (3900, '+3,90')]:
        sh.lev(v.X(X(-2000)) - 4, v.Y(z), t, side='left', ln=14)
    sh.balloons([(1, v.p(X(800), 5800), v.p(X(1500), 6050)),
                 (2, v.p(X(900), 5180), v.p(X(1300), 5650)),
                 (3, v.p(X(1800), 5000), v.p(X(2300), 5400)),
                 (4, v.p(X(2300), 4036), v.p(X(2300), 4500)),
                 (5, v.p(X(1915), 3800), v.p(X(2300), 3600)),
                 (6, v.p(X(500), 3981), v.p(X(900), 3650)),
                 (7, v.p(X(-40), 3909), v.p(X(-600), 3650)),
                 (8, v.p(X(250), 4900), v.p(X(-500), 5600)),
                 (9, v.p(X(300), 5250), v.p(X(-300), 5950)),
                 (10, v.p(X(175), 5700), v.p(X(-900), 6000)),
                 (11, v.p(X(0), 3600), v.p(X(-600), 3500)),
                 (12, v.p(X(-1200), 4100), v.p(X(-1300), 3650))])
    # ===================== B — VISTA DESDE EL EXTERIOR 1:25 =====================
    sh.vtitle(232, 279, 'B — CABECERA DE RECEPCIÓN · VISTA DESDE EL EXTERIOR   Esc. 1:25')
    vb = View(sh, 290, 174, 25, mx=D.X_L1 * 1000, my=3900)
    xl = D.X_L1 * 1000
    x0, x1 = xl - 1300, xl + 1700
    vb.R(x0, 3550, x1 - x0, 350, fc='#eeeeee', lw=0.5)
    sh.breakline(*vb.p(x0, 3550), *vb.p(x1, 3550))
    xs, ys = [], []
    for xx in np.arange(x0 + 60, x1, 60):
        xs += [vb.X(xx), vb.X(xx), np.nan]
        ys += [vb.Y(3900), vb.Y(roof_top(xx / 1000) * 1000), np.nan]
    sh.L(xs, ys, lw=0.2, c='#a0a0a0', chk=False)
    vb.L([(x0, roof_top(x0 / 1000) * 1000), (x1, roof_top(x1 / 1000) * 1000)], lw=1.4)
    # columna en el muro
    vb.R(D.X_C1 * 1000 - 100, 3550, 200, roof_top(D.X_C1) * 1000 - 3550 - 60, fc=C_EXIST, lw=0.6)
    # hueco y conducto
    vb.R(xl - 354, 4291, 708, 910, fc='white', lw=0.9)
    vb.R(xl - 304, 4341, 608, 810, fc=C_NEW, lw=0.6)
    vb.L([(xl - 304, 4745), (xl + 304, 4745)], lw=0.3)
    vb.R(xl - 100, 3941, 200, 300, fc='#999999', lw=0.5)
    vb.R(xl - 500, 3900, 1000, 41, fc='#777777', lw=0.4)
    # puerta de acceso a la pasarela
    vb.R(8300, 4051, 840, 1890, fc='#e6e6e6', lw=0.9)
    vb.R(8340, 4051, 760, 1850, fc='none', lw=0.4)
    vb.C(9030, 5000, 18, fc='k', lw=0.2)
    # plataforma (borde) a NPP
    vb.R(x0, 4021, x1 - x0, 30, fc='#333333', lw=0.2)
    vb.dim((xl - 354, 5201), (xl + 354, 5201), 4, '708 (hueco)', fs=FS)
    vb.dim((xl - 354, 4291), (xl - 354, 5201), 5, '910', fs=FS, tside=1)
    vb.dim((8300, 5941), (9140, 5941), 4, '840', fs=FS)
    vb.dim((9140, 4051), (9140, 5941), -5, '1.890', fs=FS)
    sh.labels([(vb.X(8600), vb.Y(5600), 'puerta de acceso a la pasarela\n(baja: señalizar y acolchar dintel)', vb.Y(6050)),
               (vb.X(D.X_C1 * 1000 + 100), vb.Y(5200), 'columna existente en el muro', vb.Y(5500)),
               (vb.X(xl + 200), vb.Y(4500), 'conducto L1 + huelgo 50', vb.Y(4300)),
               (vb.X(xl + 400), vb.Y(3920), 'placa de apoyo + viga (tubo)', vb.Y(3780))],
              vb.X(x1) + 4, ha='left', fs=FS, sp=7.0)

    # ===================== C — CABECERA OPUESTA 1:25 =====================
    sh.vtitle(24, 152, 'C — CABECERA OPUESTA · CORTE POR EL EJE DE L1   Esc. 1:25')
    vc = View(sh, 105, 62, 25, mx=0, my=3450)   # x = -s (s hacia el interior a la izquierda)
    wall(vc, -175, 175, 3900, 3450, 23)
    sh.breakline(*vc.p(-260, 3450), *vc.p(260, 3450))
    vc.L([(175, 3900), (175, 5350)], lw=0.9)
    for zz in (4300, 5000):
        vc.R(115, zz, 60, 60, fc=C_WOOD, lw=0.4)
    vc.R(-90, 3900, 180, 18, fc='#888888', lw=0.4)
    vc.R(-90, 3918, 80, 5, fc='#bbbbbb', lw=0.3)
    vc.R(-90, 3923, 80, 18, fc='#999999', lw=0.4)
    vc.R(-2000, 3941, 1990, 300, fc='#e0e0e0', lw=LW)
    sh.breakline(*vc.p(-2000, 3900), *vc.p(-2000, 4280))
    vc.R(-2000, 4341, 730, 810, fc=C_NEW, lw=LW)
    sh.breakline(*vc.p(-2000, 4300), *vc.p(-2000, 5200))
    vc.P([(-1270, 4301), (-520, 4301), (-370, 4451), (-370, 5040), (-520, 5191), (-1270, 5191)], fc=C_NEW2, lw=LW)
    vc.C(-820, 4731, 355, fc='none', lw=0.4, ls=(0, (5, 2)))
    vc.C(-820, 4731, 70, fc='white', lw=0.6)
    vc.R(-1250, 4241, 50, 60, fc=C_STEEL, lw=0.3)
    vc.R(-430, 4241, 50, 60, fc=C_STEEL, lw=0.3)
    vc.L([(-1450, 4051), (-1450, 5151)], lw=0.9)
    vc.L([(-1450, 5151), (-1250, 5151)], lw=0.9) if False else None
    vc.dim((-820, 5191), (0, 5191), 8, '820', fs=FS)
    vc.dim((-370, 5191), (-175, 5191), 3, '195', fs=FS)
    for z, t in [(5151, '+5,151'), (4731, '+4,731 eje'), (3900, '+3,90')]:
        sh.lev(vc.X(260), vc.Y(z), t, ln=14)
    sh.balloons([(13, vc.p(-560, 5100), vc.p(-1000, 5480)),
                 (14, vc.p(-1450, 4700), vc.p(-1750, 5450)),
                 (15, vc.p(0, 3909), vc.p(-600, 3600)),
                 (16, vc.p(175, 5250), vc.p(-300, 5480))])
    # ===================== D — SELLO DEL PASAMURO 1:5 =====================
    sh.vtitle(140, 152, 'D — SELLO DEL PASAMURO   Esc. 1:5')
    vd = View(sh, 160, 100, 5)
    vd.R(-120, -150, 116, 300, fc=C_NEW, lw=0.4)
    vd.R(-4, -150, 4, 300, fc='k', lw=0.3)
    sh.breakline(*vd.p(-120, -150), *vd.p(0, -150))
    sh.breakline(*vd.p(-120, 150), *vd.p(0, 150))
    vd.R(50, -2, 220, 4, fc='#888888', lw=0.3)
    vd.P([(50, 2), (100, 2), (100, 7), (55, 7), (55, 52), (50, 52)], fc='#666666', lw=0.4)
    vd.P([(50, -2), (100, -2), (100, -7), (55, -7), (55, -52), (50, -52)], fc='#666666', lw=0.4) if False else None
    # burlete de cepillo
    vd.R(8, -10, 42, 20, fc='#cccccc', lw=0.4)
    xs, ys = [], []
    for yy in np.arange(-8, 9, 3):
        xs += [vd.X(0), vd.X(8), np.nan]
        ys += [vd.Y(yy), vd.Y(yy), np.nan]
    sh.L(xs, ys, lw=0.3, chk=False)
    # faldon de neopreno
    vd.P([(55, 50), (58, 50), (3, 110), (0, 110)], fc='#333333', lw=0.3)
    vd.L([(77, 7), (77, -25)], lw=1.0)
    vd.dim((0, -60), (50, -60), -4, 'huelgo 50', fs=FS)
    sh.labels([(vd.X(-60), vd.Y(100), 'lateral del conducto', vd.Y(140)),
               (vd.X(30), vd.Y(80), 'faldón de neopreno 3 mm', vd.Y(90)),
               (vd.X(75), vd.Y(4.5), 'marco L50×50×5 + chapa', vd.Y(40)),
               (vd.X(25), vd.Y(-8), 'burlete de cepillo', vd.Y(-80)),
               (vd.X(240), vd.Y(0), 'cerramiento de chapa', vd.Y(-40))],
              vd.X(140), ha='left', fs=FS, sp=5.0)

    # ===================== TABLA =====================
    rows = [['N.º', 'Elemento', 'Especificación'],
            ['1', 'Chute + junta flexible', 'desde el desviador (DET-10), manga de lona siliconada'],
            ['2', 'Boca de carga', '600 × 400 sobre el tramo de cola, divisor abierto'],
            ['3', 'Cola tensora', 'rueda Z = 11, tensor M30 (DET-05)'],
            ['4', 'Plataforma exterior', 'rejilla electrosoldada, NPP +4,05'],
            ['5', 'Viga B2 de la plataforma', 'IPN 200 (apoyo fijo del tramo 0)'],
            ['6', 'Ménsula de plataforma', 'anclada al muro de cabecera'],
            ['7', 'Placa de apoyo muro sur', '1.000×180×18 + 4 M16: fijo tramo 1 / libre tramo 0'],
            ['8', 'Marco pasamuro', 'L50×50×5, hueco 708 × 910 por línea + sello (D)'],
            ['9', 'Babeta', 'chapa plegada galvanizada sobre el hueco'],
            ['10', 'Cerramiento', 'chapa sobre correas de madera (existente)'],
            ['11', 'Muro de cabecera sur', 'H° existente, tope +3,90'],
            ['12', 'Viga carrilera', 'tubo 300×200×10: tramo 1 (interior) / tramo 0 (1,825)'],
            ['13', 'Cabezal motriz', 'punto fijo del conducto (DET-05)'],
            ['14', 'Baranda de cierre', 'fin de la pasarela junto al cabezal'],
            ['15', 'Placa de apoyo muro norte', '1.000×180×18 + 4 M16: libre último tramo'],
            ['16', 'Cerramiento norte', 'sin perforar'],
            ['—', 'Puerta de acceso (B)', '0,84 × 1,89 m, señalizada, dintel acolchado']]
    sh.table(226, 150, [8, 44, 130], rows, rowh=5.4, fs=5.0)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/DET-08')
