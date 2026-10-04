from lib import *
import data as D


def chain_section(v, xc, zp, plates_h=50, dark='#6b6b6b'):
    """Ramal M224 visto según el eje del conducto: placas exteriores/interiores y casquillo."""
    zb, zt = zp - plates_h / 2, zp + plates_h / 2
    for x0, w in [(xc - 49, 8), (xc - 41, 8), (xc + 33, 8), (xc + 41, 8)]:
        v.R(x0, zb, w, plates_h, fc=dark, ec='k', lw=0.3)
    v.R(xc - 33, zp - 21.5, 66, 43, fc='#d0d0d0', ec='k', lw=0.3)
    v.R(xc - 51, zp - 6, 2, 12, fc='k', ec='k', lw=0.2)
    v.R(xc + 49, zp - 6, 2, 12, fc='k', ec='k', lw=0.2)


def build(out):
    sh = Sheet('DET-04', 'Detalle del conducto Redler, cadena y paletas',
               'Carcasa de doble compartimiento (trabajo abajo / retorno arriba) · doble cadena M224 · paleta 370×280 · bandejas portacables',
               '1:5 / 1:10 / 1:20', 5)

    # ======================= A — SECCION TRANSVERSAL TIPO 1:5 ===========================
    v = View(sh, 140, 92, 5)
    sh.vtitle(26, 276, 'A — SECCIÓN TRANSVERSAL TIPO (corte por la silleta)   Esc. 1:5')
    k = 'k'
    # interiores
    v.R(-300, 4, 600, 400, fc='#eef4fa', ec='none', lw=0, chk=False, z=1)
    v.R(-300, 407, 600, 400, fc='#f7f7f7', ec='none', lw=0, chk=False, z=1)
    # chapas (negro)
    for pts in [[(-304, 0), (304, 0), (304, 4), (-304, 4)],
                [(-304, 4), (-300, 4), (-300, 807), (-304, 807)],
                [(300, 4), (304, 4), (304, 807), (300, 807)],
                [(-300, 404), (300, 404), (300, 407), (-300, 407)],
                [(-334, 807), (334, 807), (334, 810), (-334, 810)]]:
        v.P(pts, fc='k', ec='k', lw=0.3, z=4)
    # angulos de tapa L30x30x3
    for sgn in (-1, 1):
        v.P([(sgn * 304, 777), (sgn * 307, 777), (sgn * 307, 804), (sgn * 334, 804), (sgn * 334, 807),
             (sgn * 304, 807)], fc='#888888', ec='k', lw=0.3, z=4)
        # bulon M8 de tapa
        v.L([(sgn * 322, 800), (sgn * 322, 818)], lw=0.8)
        # rigidizador L40x40x4 fondo-lateral
        v.P([(sgn * 304, 0), (sgn * 344, 0), (sgn * 344, 4), (sgn * 308, 4), (sgn * 308, 40),
             (sgn * 304, 40)], fc='#888888', ec='k', lw=0.3, z=4)
        # planchuelas de desgaste
        v.R(sgn * 241 - 35, 4, 70, 6, fc='#444444', ec='k', lw=0.2, z=4)
        # rieles de retorno L50x50x5
        v.P([(sgn * 300, 670), (sgn * 295, 670), (sgn * 295, 715), (sgn * 250, 715), (sgn * 250, 720),
             (sgn * 300, 720)], fc='#888888', ec='k', lw=0.3, z=4)
        # cadenas
        chain_section(v, sgn * D.X_CAD, 35)
        chain_section(v, sgn * D.X_CAD, 745)
        # aditamentos K2 (trabajo y retorno)
        v.R(sgn * 192 - (13 if sgn > 0 else 0), 22, 13, 30, fc='#9a9a9a', ec='k', lw=0.3, z=5)
        v.R(sgn * 192 - (13 if sgn > 0 else 0), 728, 13, 30, fc='#9a9a9a', ec='k', lw=0.3, z=5)
        # grapas sobre el ala de la L40 + bulon
        v.R(sgn * 336 - (60 if sgn < 0 else 0), 4, 60, 8, fc='#9a9a9a', ec='k', lw=0.3, z=5)
        v.L([(sgn * 376, 20), (sgn * 376, -14)], lw=1.0)
    # paleta de trabajo + angulo de base
    v.R(-185, 14, 370, 280, fc=C_NEW2, ec='k', lw=0.5, z=3)
    v.R(-185, 14, 370, 50, fc='#a9bfd6', ec='k', lw=0.4, z=3)
    # paleta de retorno (invertida)
    v.R(-185, 486, 370, 280, fc='#dde6ef', ec='k', lw=0.5, z=3)
    v.R(-185, 716, 370, 50, fc='#c3d1e0', ec='k', lw=0.4, z=3)
    # ejes de cadena
    for sgn in (-1, 1):
        v.cl((sgn * 241, -20), (sgn * 241, 420))
    v.cl((0, -250), (0, 860))
    # ventana de inspeccion (lado pasarela)
    v.R(304, 120, 8, 150, fc='#9fb8d3', ec='k', lw=0.4, z=4)
    v.R(312, 135, 4, 120, fc='white', ec='k', lw=0.3, z=4)
    # grasera
    v.C(-316, 696, 8, fc='k', ec='k', lw=0.3)
    v.L([(-304, 696), (-308, 696)], lw=1.2)
    # silleta UPN 100 x 800 (vista del alma) y viga carrilera (tubo 300x200x10, cortado)
    v.R(-400, -100, 800, 100, fc=C_STEEL, ec='k', lw=0.6, z=3)
    v.L([(-400, -8.5), (400, -8.5)], lw=0.3)
    v.L([(-400, -91.5), (400, -91.5)], lw=0.3)
    # tubo
    v.ipn_like_tube(0, -330, 200, 230, 10, hatch='////')
    sh.breakline(*v.p(-130, -330), *v.p(130, -330), lw=0.5)
    # bandejas portacables (lado opuesto a la pasarela)
    for zb, ncab, rr in [(200, 4, 15), (460, 6, 7)]:
        x0 = -354
        v.P([(x0, zb + 60), (x0, zb), (x0 - 150, zb), (x0 - 150, zb + 60)], fc='none', ec='k',
            lw=0.8, closed=False)
        v.L([(x0 + 4, zb + 64), (x0 - 154, zb + 64)], lw=0.8)  # tapa
        for kk in range(ncab):
            v.C(x0 - 18 - kk * (130 / max(ncab - 1, 1)) * 0.92, zb + rr + 2, rr, fc='#bbbbbb', lw=0.3)
        # soporte planchuela 50x5 + cartela
        v.R(-515, zb - 5, 211, 5, fc='#777777', ec='k', lw=0.2)
        v.P([(-304, zb - 5), (-304, zb - 70), (-372, zb - 5)], fc='none', ec='k', lw=0.5)

    # cotas A
    v.dim((-304, 810), (304, 810), 7, '608 (exterior)')
    v.dim((-300, 790), (300, 790), 0, '600 (interior)', ext=False)
    v.dim((334, 4), (334, 404), -5, '400')
    v.dim((334, 407), (334, 807), -5, '400')
    v.dim((334, 0), (334, 810), -11, '810')
    v.dim((-241, 320), (241, 320), 0, '482 (ejes de cadena)', ext=False)
    v.dim((-185, 250), (185, 250), 0, '370 (paleta)', ext=False)
    v.dim((-185, 14), (-185, 294), 0, '280 (paleta)', ext=False, tside=-1)
    v.dim((-515, 264), (-515, 460), 9, '200 (separación)', tside=1)
    v.dim((-100, -330), (100, -330), -9, '200')
    # niveles
    for z, s in [(810, '+5,151 sup. conducto'), (0, '+4,341 inf. conducto'),
                 (-100, '+4,241 sup. tubo')]:
        sh.lev(226, v.Y(z), s, ln=24)
    # globos
    balloons = [
        (1, (0, 160), (196, 128 + 92 - 92)),
    ]
    B = [  # (n, punto modelo, globo en modelo)
        (1, (150, 200), (245, 230)),
        (2, (241, 60), (245, 120)),
        (3, (-250, 7), (-245, 120)),
        (5, (-186, 37), (-245, 200)),
        (4, (275, 717), (245, 600)),
        (6, (220, 405), (245, 470)),
        (9, (306, 195), (245, 330)),
        (7, (-330, 809.5), (-420, 860)),
        (8, (-306, 790), (-420, 760)),
        (10, (-316, 696), (-420, 680)),
        (14, (-460, 524), (-520, 600)),
        (11, (-340, 2), (-560, 50)),
        (15, (-366, 10), (-560, 120)),
        (12, (-380, -50), (-560, -40)),
        (13, (100, -200), (170, -200)),
    ]
    B = [(n, pm, v.p(*bm)) for n, pm, bm in B]
    for n, pm, (bx, by) in B:
        px, py = v.p(*pm)
        lid = sh.nid()
        # linea al borde del globo
        d = np.array([bx - px, by - py])
        dd = np.hypot(*d)
        e = np.array([bx, by]) - d / dd * 2.3
        sh.L([px, e[0]], [py, e[1]], lw=LW_T, owner=lid)
        sh.C(px, py, 0.38, fc='k', ec='k', lw=0.2, owner=lid, z=7)
        sh.balloon(bx, by, n)
    sh.T(v.X(0), v.Y(372), 'COMPARTIMIENTO DE TRABAJO', fs=5.0, ha='center', c='#333333')
    sh.T(v.X(0), v.Y(446), 'COMPARTIMIENTO DE RETORNO', fs=5.0, ha='center', c='#333333')
    sh.T(v.X(-394), v.Y(290), 'potencia', fs=5.0, ha='center')
    sh.T(v.X(-394), v.Y(550), 'control', fs=5.0, ha='center')

    # ======================= B — VISTA LATERAL TRAMO TIPO 1:20 ===========================
    sh.vtitle(252, 276, 'B — VISTA LATERAL TRAMO TIPO   Esc. 1:20')
    vb = View(sh, 266, 222, 20)
    vb.R(0, 0, 2500, 810, fc=C_NEW, ec='k', lw=LW)
    vb.L([(0, 405), (2500, 405)], lw=0.4, ls=(0, (4, 2)))
    # bridas
    for s0 in (0, 2500):
        vb.R(s0 - 6 if s0 else -6, -40, 6 if s0 == 0 else 6, 890, fc='#888888', ec='k', lw=0.3)
    vb.R(2500, -40, 6, 890, fc='#888888', ec='k', lw=0.3)
    for zz in np.arange(60, 810, 150):
        for s0 in (-3, 2503):
            vb.C(s0, zz, 9, fc='k', ec='k', lw=0.2)
    # rigidizador inferior y angulo de tapa (bandas)
    vb.L([(0, 40), (2500, 40)], lw=0.3)
    vb.L([(0, 777), (2500, 777)], lw=0.3)
    # ventana de inspeccion
    vb.R(1150, 120, 200, 150, fc='#9fb8d3', ec='k', lw=0.5)
    # graseras
    for s0 in (250, 2250):
        vb.C(s0, 696, 16, fc='k', ec='k', lw=0.2)
    # silletas
    for s0 in (20, 2430):
        vb.R(s0, -100, 50, 100, fc=C_STEEL, ec='k', lw=0.4)
    # tubo
    vb.R(-120, -400, 2740, 300, fc='#e0e0e0', ec='k', lw=LW)
    vb.dim((0, 810), (2500, 810), 5, '2.500 (tramo estándar)')
    vb.dim((2500, 0), (2500, 810), -9, '810')
    vb.dim((1150, 270), (1350, 270), 3, '200', fs=5.0)
    vb.dim((1150, 120), (1150, 270), 3, '150', fs=5.0)
    vb.dim((2503, 60), (2503, 210), -4, '150', fs=5.0, tside=-1)
    sh.lead(*vb.p(1250, 195), 336, 230, 'ventana de inspección (1 cada 2 tramos)', fs=5.2)
    sh.lead(*vb.p(250, 696), 290, 250, 'grasera c/2 m (rieles de retorno)', fs=5.2, ha='left')
    sh.lead(*vb.p(-3, 510), 262, 243, 'brida 40×6 + M12 c/150', fs=5.2, ha='right')
    sh.lead(*vb.p(45, -50), 262, 228, 'silleta en cada brida', fs=5.2, ha='right')
    sh.T(vb.X(1250), vb.Y(-250), 'viga carrilera: tubo 300×200×10', fs=5.0, ha='center')

    # ======================= C — UNION ENTRE TRAMOS Y GRAPA 1:5 ============================
    sh.vtitle(252, 193, 'C — UNIÓN ENTRE TRAMOS   Esc. 1:5')
    vc = View(sh, 273, 158, 5)
    # piso del conducto y ala vertical del rigidizador (vista lateral)
    vc.R(-100, 0, 92.5, 4, fc='k', ec='k', lw=0.3)
    vc.R(7.5, 0, 102.5, 4, fc='k', ec='k', lw=0.3)
    vc.R(-100, 4, 92.5, 36, fc='#a0a0a0', ec='k', lw=0.3)
    vc.R(7.5, 4, 102.5, 36, fc='#a0a0a0', ec='k', lw=0.3)
    vc.R(-100, 40, 92.5, 60, fc=C_NEW, ec='k', lw=0.3)
    vc.R(7.5, 40, 102.5, 60, fc=C_NEW, ec='k', lw=0.3)
    sh.breakline(*vc.p(-100, 100), *vc.p(-100, 0), lw=0.4)
    sh.breakline(*vc.p(110, 100), *vc.p(110, 0), lw=0.4)
    # bridas cortadas + junta
    vc.R(-7.5, -40, 6, 140, fc='white', ec='k', lw=0.4, hatch='////')
    vc.R(1.5, -40, 6, 140, fc='white', ec='k', lw=0.4, hatch='////')
    vc.R(-1.5, -40, 3, 140, fc='#333333', ec='k', lw=0.2)
    # bulon M12 de brida
    vc.R(-20, -27, 12.5, 14, fc='#777777', ec='k', lw=0.3)
    vc.R(7.5, -27, 12.5, 14, fc='#777777', ec='k', lw=0.3)
    # silleta UPN 100 (vista de extremo) junto a la brida
    sx0 = 20
    vc.P([(sx0, 0), (sx0 + 50, 0), (sx0 + 50, -8.5), (sx0 + 6, -8.5), (sx0 + 6, -91.5), (sx0 + 50, -91.5),
          (sx0 + 50, -100), (sx0, -100)], fc=C_STEEL, ec='k', lw=0.5)
    # grapa sobre el ala de la L40 + bulon M12 (agujero ovalado)
    vc.R(sx0 - 10, 4, 70, 8, fc='#9a9a9a', ec='k', lw=0.4, z=5)
    vc.R(sx0 + 34, 12, 14, 9, fc='#555555', ec='k', lw=0.3, z=5)
    vc.R(sx0 + 34, -18, 14, 7, fc='#555555', ec='k', lw=0.3, z=5)
    # tope del tubo
    vc.R(-100, -130, 210, 30, fc='#e0e0e0', ec='k', lw=0.4)
    vc.dim((-7.5, -40), (-7.5, 0), 6, '40', fs=5.0)
    sh.lead(*vc.p(0, 85), 296, 184, 'junta neopreno e = 3', fs=5.0)
    sh.lead(*vc.p(4.5, 60), 296, 180, 'brida planchuela 40×6', fs=5.0)
    sh.lead(*vc.p(20, -20), 296, 140, 'bulón M12 c/150', fs=5.0)
    sh.lead(*vc.p(sx0 + 50, -60), 296, 144, 'silleta UPN 100 × 800', fs=5.0)
    sh.lead(*vc.p(sx0 + 55, 8), 296, 168, 'grapa 70×8 + M12', fs=5.0)
    sh.T(297, 164.4, 'agujero ovalado 14×40', fs=5.0)
    sh.T(297, 160.8, 'según eje (dilatación)', fs=5.0)
    sh.lead(*vc.p(90, 25), 296, 176, 'rigidizador L40×40×4', fs=5.0)
    sh.T(vc.X(5), vc.Y(-145), 'viga carrilera (tubo)', fs=5.0, ha='center')

    # ======================= D — CADENA Y PALETAS (planta) 1:10 ============================
    sh.vtitle(338, 193, 'D — CADENA Y PALETAS (planta)   Esc. 1:10')
    vd = View(sh, 374, 153, 10)
    vd.R(-304, -250, 4, 500, fc='k', ec='k', lw=0.3)
    vd.R(300, -250, 4, 500, fc='k', ec='k', lw=0.3)
    for sgn in (-1, 1):
        xc = sgn * 241
        vd.R(xc - 35, -250, 70, 500, fc='none', ec='k', lw=0.3, ls=(0, (3, 2)))
        for kk, s0 in enumerate(range(-300, 300, 200)):
            inner = kk % 2 == 0
            dx = 41 if inner else 49
            a0, a1 = max(s0 + 10, -250), min(s0 + 190, 250)
            for sg2 in (-1, 1):
                vd.R(xc + sg2 * dx - (8 if sg2 > 0 else 0), a0, 8, a1 - a0, fc='#8a8a8a', ec='k', lw=0.3)
        for s0 in (-100, 100):
            vd.R(xc - 51, s0 - 7, 102, 14, fc='#444444', ec='k', lw=0.2)
    for s0 in (-200, 0, 200):
        vd.R(-185, s0 - 2.5, 370, 5, fc='#4f6f92', ec='k', lw=0.3)
        vd.R(-185, s0 - 52.5, 370, 50, fc='none', ec='k', lw=0.3, ls=(0, (2, 1.5)))
        for sgn in (-1, 1):
            vd.R(sgn * 185 - (0 if sgn > 0 else 7), s0 - 10, 7, 20, fc='#9a9a9a', ec='k', lw=0.2)
    vd.dim((-300, 250), (300, 250), 4, '600')
    vd.dim((-241, -250), (241, -250), -4, '482')
    vd.dim((-185, -130), (185, -130), 0, '370', ext=False, fs=5.0)
    vd.dim((-304, 0), (-304, 200), 5, '200 = paso', fs=5.0, tside=1)
    sh.L([vd.X(330), vd.X(330)], [vd.Y(-160), vd.Y(160)], lw=0.8, c='#1f4e79')
    sh.P([(vd.X(330), vd.Y(190)), (vd.X(330) - 1.2, vd.Y(160)), (vd.X(330) + 1.2, vd.Y(160))],
         fc='#1f4e79', ec='#1f4e79', lw=0.3)
    sh.T(vd.X(330) + 1.0, vd.Y(-200), 'avance', fs=5.0, rot=90, ha='left', c='#1f4e79')
    sh.lead(*vd.p(-241, 150), 345, 113.5, 'cadena M224 (2 ramales)', fs=5.0, ha='left')
    sh.lead(*vd.p(60, 0), 372, 113.5, 'paleta + L50 + K2', fs=5.0, ha='left')

    # ======================= TABLA ======================================================
    rows = [['N.º', 'Pieza', 'Especificación'],
            ['1', 'Paleta de arrastre', 'chapa 370×280×5 ST-37 + L50×50×5, en cada eslabón (paso 200)'],
            ['2', 'Cadena (×2 por línea)', 'DIN 8167 / ISO 1977 M224, paso 200, rotura 224 kN por ramal'],
            ['3', 'Planchuela de desgaste', '70×6 acero antidesgaste (ej. 400 HB), atornillada, continua'],
            ['4', 'Riel de retorno', 'L50×50×5 soldado a los laterales'],
            ['5', 'Aditamento K2', 'en cada eslabón, bulones M10 cal. 8.8'],
            ['6', 'Divisor', 'chapa e = 3 (separa trabajo / retorno)'],
            ['7', 'Tapa superior', 'chapa e = 3, bulones M8 c/150 sobre ángulos'],
            ['8', 'Ángulo de tapa', 'L30×30×3 continuo'],
            ['9', 'Ventana de inspección', '200×150, cierre rápido, 1 cada 2 tramos'],
            ['10', 'Grasera', 'c/2 m, lubricación de rieles de retorno'],
            ['11', 'Rigidizador fondo-lateral', 'L40×40×4 continuo'],
            ['12', 'Silleta', 'UPN 100 × 800, en cada brida (c/2,50 m)'],
            ['13', 'Viga carrilera', 'tubo 300×200×10 F-24 (ver DET-07)'],
            ['14', 'Bandejas portacables', '150×60 perforadas c/tapa: potencia y control (sep. 200)'],
            ['15', 'Grapa de silleta', 'planchuela 70×8 + M12, agujero ovalado según eje']]
    sh.table(252, 107.5, [8, 38, 112], rows, rowh=3.5, fs=5.1)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/DET-04')
