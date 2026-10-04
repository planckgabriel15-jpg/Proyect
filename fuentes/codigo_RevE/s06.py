from lib import *
import data as D
import math
from s04 import chain_section

TAN = math.tan(math.radians(35))


def brazo_pts(sg):
    """Brazo a 35°: superficie superior desde (103,-371) hasta vuelo 220."""
    x0, z0 = 103, -371
    x1, z1 = 323, -371 - 220 * TAN
    t = 6 / math.cos(math.radians(35))
    return [(sg * x0, z0), (sg * x1, z1), (sg * x1, z1 - t), (sg * x0, z0 - t)]


def build(out):
    sh = Sheet('DET-06', 'Compuerta guillotina, boca en pantalón y brazos distribuidores',
               'Descarga a ambos lados de la viga carrilera sin invadir la pasarela · 22 conjuntos (11 por línea)',
               '1:10 / 1:20 / 1:2', 7)
    FS = 5.0
    # ===================== A — SECCION TRANSVERSAL POR LA COMPUERTA 1:10 =====================
    sh.vtitle(24, 276, 'A — SECCIÓN TRANSVERSAL POR LA COMPUERTA (L1)   Esc. 1:10')
    v = View(sh, 100, 205, 10)
    # conducto (compartimiento de trabajo, cortado arriba)
    v.R(-300, 0, 600, 420, fc='#eef4fa', ec='none', lw=0, chk=False, z=1)
    for sg in (-1, 1):
        v.R(sg * 302 - 2, 0, 4, 420, fc='k', lw=0.3)
        v.P([(sg * 304, 0), (sg * 344, 0), (sg * 344, 4), (sg * 308, 4), (sg * 308, 40), (sg * 304, 40)],
            fc='#888888', lw=0.3)
        chain_section(v, sg * 241, 35)
        v.R(sg * 241 - 35, 4, 70, 6, fc='#444444', lw=0.2)
        # guia L40x40x4 + planchuela de retencion 30x5
        v.P([(sg * 318, -4), (sg * 358, -4), (sg * 358, -40), (sg * 354, -40), (sg * 354, -4 + 0),
             (sg * 318, 0)][0:0] or [(sg * 318, 0), (sg * 358, 0), (sg * 358, -40), (sg * 354, -40),
                                    (sg * 354, -4), (sg * 318, -4)], fc='#888888', lw=0.3)
        v.R(min(sg * 328, sg * 354), -16, 26, 5, fc='#555555', lw=0.3)
        # sello
        v.R(min(sg * 280, sg * 315), -5, 35, 5, fc='#333333', lw=0.2)
    sh.breakline(*v.p(-360, 420), *v.p(360, 420))
    # placa guillotina (cerrada)
    v.R(-350, -11, 700, 6, fc='#4f6f92', lw=0.4)
    # divisor a dos aguas sobre el tubo
    v.P([(0, -16), (103, -100), (103, -104), (0, -20), (-103, -104), (-103, -100)], fc='#666666', lw=0.4)
    # piernas del pantalon
    for sg in (-1, 1):
        v.R(sg * 301.5 - 1.5, -361, 3, 345, fc='#666666', lw=0.2)
        v.R(sg * 104.5 - 1.5, -361, 3, 257, fc='#666666', lw=0.2)
        v.R(min(sg * 106, sg * 300), -361, 194, 345 - 0, fc='#f3f6fa', ec='none', lw=0, chk=False, z=1)
    # tubo
    v.ipn_like_tube(0, -400, 200, 300, 10, hatch='////')
    # chapa de anclaje y orejas + brazos
    v.R(-100, -410, 200, 10, fc='#999999', lw=0.4)
    for sg in (-1, 1):
        v.P([(sg * 40, -410), (sg * 100, -410), (sg * 100, -385), (sg * 240, -483), (sg * 190, -483)],
            fc='#bbbbbb', lw=0.4)
        v.P(brazo_pts(sg), fc='#4f6f92', lw=0.4)
        v.C(sg * 170, -430, 7, fc='white', lw=0.4)
    # actuador (detras, oculto) centrado bajo el conducto
    v.R(-45, -85, 90, 70, fc='none', lw=0.5, ls=(0, (3, 2)))
    # pasarela (lado +x): rejilla y chapa de borde
    v.R(350, -321, 160, 30, fc='#dddddd', lw=0.4)
    v.R(350, -341, 4, 50, fc='#888888', lw=0.3)
    sh.breakline(*v.p(510, -360), *v.p(510, -270))
    # flujo (flechas)
    for sg in (-1, 1):
        sh.ax.annotate('', xy=v.p(sg * 200, -330), xytext=v.p(sg * 200, -60),
                       arrowprops=dict(arrowstyle='-|>', color='#c00000', lw=0.8))
        sh.ax.annotate('', xy=v.p(sg * 480, -640), xytext=v.p(sg * 300, -540),
                       arrowprops=dict(arrowstyle='-|>', color='#c00000', lw=0.8))
    v.cl((0, -680), (0, 440))
    # cotas
    v.dim((-300, 300), (300, 300), 0, '600 (abertura)', ext=False)
    v.dim((323, -371 - 220 * TAN), (103, -371 - 220 * TAN), 9, 'vuelo 220', fs=FS)
    sh.T(v.X(430), v.Y(-275), 'paso libre 0,90 (sigue)', fs=FS, ha='left') if False else None
    for z, s_ in [(0, '+4,341'), (-100, '+4,241'), (-291, 'NPP +4,05'), (-400, '+3,941')]:
        sh.lev(182, v.Y(z), s_, ln=12)
    sh.labels([(v.X(-200), v.Y(-11), 'placa guillotina e = 6 (cerrada)', v.Y(60)),
               (v.X(-50), v.Y(-30), 'divisor a dos aguas (39°)', v.Y(-20)),
               (v.X(-60), v.Y(-405), 'chapa de anclaje 200×380×10\nsoldada al tubo', v.Y(-410)),
               (v.X(-300), v.Y(-560), 'brazo distribuidor 350×220×6 a 35°', v.Y(-560))],
              23.5, ha='left', fs=FS, sp=7.0)
    sh.labels([(v.X(356), v.Y(-30), 'guía L40×40×4 (ver D)', v.Y(120)),
               (v.X(40), v.Y(-70), 'actuador (detrás, oculto)', v.Y(30)),
               (v.X(220), v.Y(-470), 'oreja e = 8 + M12', v.Y(-500)),
               (v.X(200), v.Y(-200), 'pierna del pantalón 194×350, e = 3', v.Y(-250)),
               (v.X(430), v.Y(-306), 'pasarela (rejilla + chapa de borde)', v.Y(-640))],
              v.X(380), ha='left', fs=FS, sp=4.0)

    # ===================== B — CORTE LONGITUDINAL POR LA PIERNA 1:20 =====================
    sh.vtitle(206, 276, 'B — CORTE LONGITUDINAL POR LA PIERNA (lado pasarela)   Esc. 1:20')
    vb = View(sh, 340, 228, 20)
    vb.R(-1450, 4, 1950, 300, fc='#eef4fa', ec='none', lw=0, chk=False, z=1)
    vb.R(-1450, 0, 1275, 4, fc='k', lw=0.2)
    vb.R(175, 0, 325, 4, fc='k', lw=0.2)
    sh.breakline(*vb.p(-1450, -30), *vb.p(-1450, 330))
    sh.breakline(*vb.p(500, -30), *vb.p(500, 330))
    vb.R(-650, -16, 900, 5, fc='#555555', lw=0.2)
    vb.R(-225, -11, 450, 6, fc='#4f6f92', lw=0.4)
    vb.R(-625, -11, 450, 6, fc='none', lw=0.5, ls=(0, (3, 2)))
    vb.R(-1300, -85, 600, 70, fc='#9fb3c8', lw=0.5)
    vb.R(-700, -55, 475, 10, fc='#bbbbbb', lw=0.4)
    vb.R(-1330, -95, 30, 95, fc='#777777', lw=0.4)
    for sx in (-225, -625):
        vb.R(sx - 25, -40, 50, 25, fc='#f2c98a', lw=0.4)
    vb.R(-1450, -400, 1950, 300, fc='#e0e0e0', lw=LW)
    vb.R(-175, -361, 350, 345, fc='#f3f6fa', lw=0.5, z=3)
    vb.L([(-175, -361), (-175, -16)], lw=0.8, z=4)
    vb.L([(175, -361), (175, -16)], lw=0.8, z=4)
    vb.R(-175, -371 - 220 * TAN - 8, 350, 18, fc='#4f6f92', lw=0.4)
    vb.R(-1420, -100, 50, 100, fc=C_STEEL, lw=0.4)
    sh.ax.annotate('', xy=vb.p(0, -330), xytext=vb.p(0, 150),
                   arrowprops=dict(arrowstyle='-|>', color='#c00000', lw=0.8))
    vb.dim((-175, 4), (175, 4), 0, '350', ext=False, fs=FS) if False else None
    vb.dim((-175, 0), (175, 0), 6, 'abertura 350', fs=FS)
    vb.dim((-225, -11), (225, -11), -6, 'placa 450', fs=FS) if False else None
    vb.dim((-625, -110), (-225, -110), -3, 'carrera 400', fs=FS) if False else None
    vb.dim((-1330, 304), (225, 304), 5, 'zona libre de silletas y bridas ≈ 1.550', fs=FS)
    vb.dim((-625, -16), (-225, -16), -27, 'carrera 400', fs=FS)
    sh.labels([(vb.X(-1000), vb.Y(-50), 'actuador lineal eléctrico ≥ 1.000 N,\ncarrera 400, IP65', vb.Y(-120)),
               (vb.X(-1315), vb.Y(-60), 'soporte del actuador', vb.Y(-260))],
              204, ha='left', fs=FS, sp=7.0) if False else None
    sh.lead(vb.X(-1000), vb.Y(-85), 214, vb.Y(-200), 'actuador lineal eléctrico ≥ 1.000 N', fs=FS)
    sh.T(213.2, vb.Y(-200) - 3.4, 'carrera 400 · IP65 · 2 finales de carrera', fs=FS, ha='right')
    sh.lead(vb.X(-625), vb.Y(-40), vb.X(-560), vb.Y(-480), 'finales de carrera', fs=FS)
    sh.lead(vb.X(150), vb.Y(-8), 368, vb.Y(80), 'placa 450 (cerrada)', fs=FS, ha='left')
    sh.lead(vb.X(240), vb.Y(-14), 368, vb.Y(-60), 'guía + planchuela', fs=FS, ha='left')
    sh.lead(vb.X(-500), vb.Y(-8), vb.X(-1430), vb.Y(110), 'posición abierta', fs=FS, ha='left')
    sh.lead(vb.X(120), vb.Y(-8), vb.X(320), vb.Y(170), 'placa 450 (cerrada)', fs=FS, ha='left') if False else None
    sh.T(vb.X(-1000), vb.Y(-250), 'viga carrilera (tubo)', fs=FS, ha='center')

    # ===================== C — VISTA DESDE ABAJO 1:20 =====================
    sh.vtitle(206, 177, 'C — VISTA DESDE ABAJO   Esc. 1:20')
    vc = View(sh, 340, 142, 20)
    vc.R(-1450, -304, 1950, 608, fc=C_NEW, lw=LW)
    sh.breakline(*vc.p(-1450, -330), *vc.p(-1450, 330))
    sh.breakline(*vc.p(500, -330), *vc.p(500, 330))
    for sg in (-1, 1):
        vc.R(-650, sg * 356 - 2, 900, 4, fc='#888888', lw=0.3)
    vc.R(-225, -350, 450, 700, fc='none', lw=0.5, ls=(0, (3, 2)))
    vc.R(-1450, -100, 1950, 200, fc='#e0e0e0', lw=LW)
    vc.R(-1300, -40, 600, 80, fc='none', lw=0.5, ls=(0, (3, 2)))
    for sg in (-1, 1):
        vc.R(-175, min(sg * 103, sg * 300), 350, 197, fc='#f3f6fa', lw=0.5)
        vc.R(-175, min(sg * 300, sg * 323), 350, 23, fc='#4f6f92', lw=0.4)
    vc.R(-190, -100, 380, 200, fc='#999999', lw=0.4)
    vc.dim((500, -304), (500, 304), -4, '608', fs=FS)
    vc.dim((-650, 356), (-650, -356), 4, '712 (guías)', fs=FS) if False else None
    sh.lead(vc.X(-1300), vc.Y(356), 214, vc.Y(380), 'guías L40 (sep. 650 entre bordes)', fs=FS, ha='left') if False else None
    sh.labels([(vc.X(-100), vc.Y(200), 'pierna del pantalón', vc.Y(330)),
               (vc.X(-400), vc.Y(356), 'guías L40 + planchuela 30×5', vc.Y(430)),
               (vc.X(-1000), vc.Y(0), 'actuador (sobre el tubo)', vc.Y(120)),
               (vc.X(-50), vc.Y(-310), 'brazo (ambos lados)', vc.Y(-430)),
               (vc.X(-600), vc.Y(-80), 'tubo 300×200×10', vc.Y(-120))],
              204, ha='left', fs=FS, sp=3.6)

    # ===================== D — DETALLE DE GUIA Y SELLO 1:2 =====================
    sh.vtitle(24, 130, 'D — GUÍA, SELLO Y PLACA   Esc. 1:2')
    vd = View(sh, -70, 88, 2)
    vd.R(300, 0, 4, 60, fc='k', lw=0.3)
    vd.P([(304, 0), (344, 0), (344, 4), (308, 4), (308, 40), (304, 40)], fc='#888888', lw=0.4, hatch='////')
    vd.P([(318, 0), (358, 0), (358, -40), (354, -40), (354, -4), (318, -4)], fc='#bbbbbb', lw=0.5,
         hatch='\\\\\\\\')
    vd.R(328, -16, 26, 5, fc='#777777', lw=0.5)
    vd.R(240, -11, 110, 6, fc='#4f6f92', lw=0.5)
    vd.R(240, -5, 75, 5, fc='#333333', lw=0.3)
    vd.R(229, -60, 8, 50, fc='none', lw=0.0)
    sh.breakline(*vd.p(240, -20), *vd.p(240, 4))
    vd.dim((318, -40), (358, -40), -4, '40', fs=FS)
    sh.labels([(vd.X(302), vd.Y(50), 'lateral del conducto e = 4', vd.Y(60)),
               (vd.X(320), vd.Y(30), 'rigidizador L40×40×4', vd.Y(44)),
               (vd.X(290), vd.Y(-3), 'sello fieltro/goma e = 5', vd.Y(16)),
               (vd.X(270), vd.Y(-8), 'placa guillotina e = 6', vd.Y(4)),
               (vd.X(340), vd.Y(-14), 'planchuela de retención 30×5\nsoldada a la guía', vd.Y(-12)),
               (vd.X(356), vd.Y(-30), 'guía L40×40×4 soldada\nbajo el conducto', vd.Y(-32))],
              122, ha='left', fs=FS, sp=6.2)

    # ===================== TABLA =====================
    rows = [['Dato', 'Valor'],
            ['Abertura en el fondo del conducto', '600 × 350 mm'],
            ['Placa guillotina', '700 × 450 × 6, ST-37'],
            ['Carrera', '400 mm'],
            ['Guías', 'L40×40×4 + planchuela 30×5, sep. 650'],
            ['Sello perimetral', 'fieltro / goma, e = 5'],
            ['Fuerza de diseño', '588 N (Nitrocomplex, μ 0,35, FS 2,0)'],
            ['Actuador', 'eléctrico lineal ≥ 1.000 N, IP65'],
            ['Brazo distribuidor', 'chapa curva 350 × 220 × 6 a 35°, ST-37'],
            ['Impacto sobre el brazo', '46,7 N (64,2 t/h; h = 0,35 m)'],
            ['Cantidad', '22 compuertas (11 por línea) · 44 brazos']]
    sh.table(245, 108, [52, 111 - 52 + 50], rows, rowh=4.2, fs=5.0)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/DET-06')
