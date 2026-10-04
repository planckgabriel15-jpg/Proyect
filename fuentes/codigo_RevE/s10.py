from lib import *
import data as D
import math

FS = 5.0
C_EL = '#e8c4bd'
C_EL2 = '#d9a49a'


def bucket_profile(v, s0, z0, flip=1, fc=C_NEW2):
    """Perfil MF: respaldo vertical de 295, proyeccion 203 (hacia flip)."""
    pts = [(0, 295), (0, 40), (30, 0), (150, 0), (203, 120), (203, 270), (190, 295)]
    v.P([(s0 + flip * p[0], z0 + p[1]) for p in pts], fc=fc, lw=0.6)


def build(out):
    sh = Sheet('DET-10', 'Elevador de cangilones, desviador de 2 vías y chutes',
               'Martin serie 700 C248-725 · descarga continua · cangilón MF 24×8×11⅝ in · 0,635 m/s · chutes a 45° hacia L1 y L2',
               '1:75 / 1:100 / 1:20 / 1:15', 11)
    # ===================== A — ELEVACION LATERAL 1:75 =====================
    sh.vtitle(24, 276, 'A — ELEVACIÓN LATERAL   Esc. 1:75')
    v = View(sh, 62, 108, 75, mx=0, my=0)   # z absoluto (mm), s local
    # fosa y terreno
    v.R(-1400, -3650, 2800, 250, fc='#d6d6d6', lw=0.5)
    v.R(-1400, -3400, 250, 3200, fc='#d6d6d6', lw=0.5)
    sh.ground(v.X(-2400), v.X(-1400), v.Y(-200))
    sh.ground(v.X(1600), v.X(2600), v.Y(-200))
    v.L([(1150, -200), (1600, -200)], lw=0.6)
    # bota
    v.R(-650, -3300, 1300, 1000, fc=C_EL2, lw=0.7)
    v.C(0, -2850, 317, fc='none', lw=0.5)
    v.R(-1050, -2850, 400, 120, fc='#bbbbbb', lw=0.4)
    # cuerpo
    v.R(-610, -2300, 1220, 11900, fc=C_EL, lw=0.7)
    for ss in (-317, 317):
        v.L([(ss, -2850), (ss, 9880)], lw=0.4, ls=(0, (4, 2)))
    for zz in np.arange(-2000, 9400, 1500):
        v.R(-560, zz, 150, 200, fc='white', lw=0.3)
    # cabeza
    v.P([(-700, 9600), (700, 9600), (700, 10100), (480, 10330), (-480, 10330), (-700, 10100)], fc=C_EL2, lw=0.7)
    v.C(0, 9880, 317, fc='none', lw=0.5)
    v.R(-700, 10000, 300, 250, fc='#9fb3c8', lw=0.4) if False else None
    v.R(-1050, 9750, 350, 260, fc='#9fb3c8', lw=0.5)
    # desviador (lado descendente) y chute
    v.P([(610, 9380), (1060, 9380), (1060, 8780), (610, 8780)], fc='#c9b0a8', lw=0.5)
    v.L([(840, 8780), (330, 5400)], lw=1.4)
    # plataforma de cabeza + baranda, marinera con jaula
    v.R(-1300, 8660, 2600, 40, fc='k', lw=0.2)
    v.L([(-1300, 8700), (-1300, 9800)], lw=0.6)
    v.L([(-1300, 9800), (-700, 9800)], lw=0.6)
    v.L([(-1300, 9250), (-700, 9250)], lw=0.4)
    v.L([(-950, 4050), (-950, 8660)], lw=0.5)
    v.L([(-1250, 4050), (-1250, 8660)], lw=0.5)
    for zz in np.arange(4300, 8660, 300):
        v.L([(-1250, zz), (-950, zz)], lw=0.3)
    for zz in np.arange(6250, 8660, 600):
        cx, cy = v.p(-1100, zz)
        sh.ax.add_patch(matplotlib.patches.Arc((cx, cy), 7.2, 4, theta1=180, theta2=360, lw=0.4))
    # plataforma exterior +4,05
    v.R(-2400, 4020, 1790, 30, fc='#999999', lw=0.3)
    v.R(610, 4020, 1600, 30, fc='#999999', lw=0.3)
    # cotas
    v.dim((-610, -2750), (-610, 9380), 14, 'H = 12,13 (elevación)', fs=FS, tpos=0.3)
    v.dim((-610, -2850), (-610, 9880), 22, '12,73 entre ejes', fs=FS, tpos=0.3)
    for z, t in [(10330, '+10,33'), (9880, '+9,88'), (9380, '+9,38'), (8680, '+8,68'), (4050, '+4,05'),
                 (-200, '−0,20'), (-2750, '−2,75'), (-3300, '−3,30')]:
        sh.lev(23.5, v.Y(z), t, ln=7, fs=4.8)
    sh.labels([(v.X(0), v.Y(10200), 'cabeza: rueda 13 d., Dp 635'),
               (v.X(-875), v.Y(9880), 'motorreductor 5,5 kW'),
               (v.X(1060), v.Y(9100), 'desviador de 2 vías', v.Y(9300)),
               (v.X(1300), v.Y(8680), 'plataforma de cabeza +8,68', v.Y(8500)),
               (v.X(692), v.Y(7800), 'chute a 45° hacia L1 / L2', v.Y(7300)),
               (v.X(-1100), v.Y(6000), 'marinera con jaula', v.Y(6000)),
               (v.X(317), v.Y(3000), 'pata descendente', v.Y(3300)),
               (v.X(-317), v.Y(1500), 'pata ascendente', v.Y(1800)),
               (v.X(610), v.Y(600), 'cuerpo 730 × 1.220 (chapa 3 + L40)', v.Y(600)),
               (v.X(650), v.Y(-2700), 'bota + tensor', v.Y(-2300)),
               (v.X(1150), v.Y(-1500), 'fosa (DET-11)', v.Y(-1300))],
              v.X(1900), ha='left', fs=FS, sp=4.0)

    # ===================== B — VISTA FRONTAL 1:100 =====================
    sh.vtitle(150, 276, 'B — VISTA FRONTAL (desde el exterior)   Esc. 1:100')
    vb = View(sh, 186, 110, 100, mx=0, my=0)
    sh.ground(vb.X(-4300), vb.X(-1500), vb.Y(-200))
    sh.ground(vb.X(1500), vb.X(4300), vb.Y(-200))
    vb.L([(-1500, -200), (1500, -200)], lw=0.6)
    vb.R(-1500, -3650, 3000, 3450, fc='none', lw=0.4, ls=(0, (3, 2)))
    vb.R(-650, -3300, 1300, 1000, fc=C_EL2, lw=0.6)
    vb.R(-365, -2300, 730, 11900, fc=C_EL, lw=0.6)
    vb.R(-450, 9600, 900, 730, fc=C_EL2, lw=0.6)
    vb.R(450, 9750, 350, 260, fc='#9fb3c8', lw=0.4)
    vb.P([(-300, 9380), (300, 9380), (350, 8780), (-350, 8780)], fc='#c9b0a8', lw=0.5)
    for sg in (-1, 1):
        vb.L([(sg * 330, 8780), (sg * 3450, 5300)], lw=1.4)
        vb.R(sg * 3450 - 340, 4300, 680, 890, fc=C_NEW2, lw=0.5)
        vb.R(sg * 3450 - 304, 4341, 608, 0, fc='none', lw=0)
    vb.R(-4300, 4020, 8600, 30, fc='#999999', lw=0.3)
    for xp in (-3900, -1500, 1500, 3900):
        vb.R(xp - 50, -200, 100, 4220, fc='#bbbbbb', lw=0.3)
    vb.R(-1300, 8660, 2600, 40, fc='k', lw=0.2)
    vb.L([(600, 4050), (600, 8660)], lw=0.5)
    vb.L([(900, 4050), (900, 8660)], lw=0.5)
    for sg in (-1, 1):
        vb.L([(sg * 400, 9600), (sg * 4300, -200)], lw=0.4, ls=(0, (4, 2)))
    vb.dim((-3450, 9900), (0, 9900), 4, '3,45', fs=FS)
    vb.dim((0, 9900), (3450, 9900), 4, '3,45', fs=FS)
    sh.T(vb.X(-2300), vb.Y(7300), '45°', fs=FS)
    sh.T(vb.X(1950), vb.Y(7300), '45°', fs=FS)
    sh.labels([(vb.X(-3450), vb.Y(5190), 'boca de carga L1', vb.Y(6400)),
               (vb.X(-3000), vb.Y(3000), 'vientos Ø 12 (3)', vb.Y(3200)),
               (vb.X(-1400), vb.Y(-1500), 'fosa (oculta)', vb.Y(-1500))],
              vb.X(-4300), ha='right', fs=FS, sp=4.0) if False else None
    sh.lead(vb.X(-3450), vb.Y(5190), vb.X(-3300), vb.Y(6500), 'boca de carga L1', fs=FS, ha='right')
    sh.lead(vb.X(3450), vb.Y(5190), vb.X(3300), vb.Y(6500), 'boca de carga L2', fs=FS, ha='left')
    sh.lead(vb.X(-4100), vb.Y(300), vb.X(-4350), vb.Y(-900), 'vientos Ø 12 (3)', fs=FS, ha='right')
    sh.lead(vb.X(750), vb.Y(6000), vb.X(1500), vb.Y(6900), 'marinera con jaula', fs=FS, ha='left') if False else None
    sh.lead(vb.X(0), vb.Y(9080), vb.X(1500), vb.Y(8000), 'desviador 2 vías', fs=FS, ha='left') if False else None

    # ===================== E — DESVIADOR 1:20 =====================
    sh.vtitle(232, 276, 'E — DESVIADOR DE 2 VÍAS   Esc. 1:20')
    ve = View(sh, 300, 222, 20)
    ve.R(-150, 600, 300, 300, fc='#eeeeee', lw=0.6)
    ve.P([(-300, 0), (300, 0), (150, 600), (-150, 600)], fc='#f6f6f6', lw=0.7)
    for sg in (-1, 1):
        ve.P([(sg * 60, 0), (sg * 300, 0), (sg * 640, -340), (sg * 400, -340)], fc='#f6f6f6', lw=0.7)
    ve.L([(0, 600), (-170, 60)], lw=1.4)
    cx, cy = ve.p(0, 600)
    sh.C(cx, cy, 0.8, fc='k', lw=0.2)
    ve.R(260, 620, 200, 150, fc='#9fb3c8', lw=0.5)
    sh.ax.annotate('', xy=ve.p(180, -150), xytext=ve.p(10, 880),
                   arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=0.8))
    sh.labels([(ve.X(360), ve.Y(700), 'actuador rotativo +\n2 finales de carrera', ve.Y(850)),
               (ve.X(-100), ve.Y(300), 'clapeta pivotante (posición L2)', ve.Y(480)),
               (ve.X(-500), ve.Y(-250), 'a L1 (chute 45°)', ve.Y(-120)),
               (ve.X(500), ve.Y(-250), 'a L2 (chute 45°)', ve.Y(-300))],
              ve.X(700), ha='left', fs=FS, sp=5.0)
    ve.dim((-300, 0), (300, 0), -4, '600', fs=FS) if False else None

    # ===================== C — SECCION DEL CUERPO 1:20 =====================
    sh.vtitle(232, 200, 'C — SECCIÓN DEL CUERPO   Esc. 1:20')
    vc = View(sh, 262, 158, 20)
    vc.R(-365, -610, 730, 1220, fc='white', lw=0.9)
    vc.R(-362, -607, 724, 1214, fc='none', lw=0.3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            vc.P([(sx * 365, sy * 610), (sx * 325, sy * 610), (sx * 325, sy * 606), (sx * 361, sy * 606),
                  (sx * 361, sy * 570), (sx * 365, sy * 570)], fc='#888888', lw=0.3)
    for sg in (-1, 1):
        vc.R(-305, sg * 317.5 - (213 if sg < 0 else -10) - (0 if sg < 0 else 0), 610, 203,
             fc=C_NEW2, lw=0.5) if False else None
    vc.R(-305, -317.5 - 213, 610, 203, fc=C_NEW2, lw=0.5)
    vc.R(-305, 317.5 + 10, 610, 203, fc=C_NEW2, lw=0.5)
    for sg in (-1, 1):
        vc.R(-40, sg * 317.5 - 10, 80, 20, fc='#555555', lw=0.3)
    vc.dim((-365, 610), (365, 610), 4, '730', fs=FS)
    vc.dim((365, -610), (365, 610), -4, '1.220', fs=FS)
    vc.dim((-305, -317.5 - 213), (305, -317.5 - 213), -2.5, '610', fs=4.6, ext=False) if False else None
    sh.labels([(vc.X(0), vc.Y(-420), 'cangilón MF (pata ascendente)', vc.Y(-450)),
               (vc.X(0), vc.Y(430), 'cangilón MF (pata descendente)', vc.Y(500)),
               (vc.X(40), vc.Y(-317), 'cadena serie 700 (fabricante)', vc.Y(-150)),
               (vc.X(345), vc.Y(590), 'chapa 3 + L40 esquineros', vc.Y(150))],
              vc.X(560), ha='left', fs=FS, sp=4.0)

    # ===================== D — CANGILON (perfil) 1:5 =====================
    sh.vtitle(330, 196, 'D — CANGILÓN MF (perfil)   Esc. 1:5') if False else None
    sh.vtitle(232, 120, 'D — CANGILÓN MF (perfil)   Esc. 1:15')
    vd = View(sh, 250, 70, 5) if False else None

    # ===================== TABLA =====================
    rows = [['Dato', 'Valor'],
            ['Equipo', 'Martin serie 700 C248-725, descarga continua'],
            ['Caudal de diseño', '64,20 t/h (caudal del Redler)'],
            ['Capacidad máxima', '69,32 t/h (3.400 ft³/h al 75 %, Urea)'],
            ['Velocidad de cadena', '0,635 m/s (125 ft/min)'],
            ['Cangilón', 'MF 24×8×11⅝ in (610×203×295), 17,1 L equiv.'],
            ['Paso / cantidad', '304,8 mm (12 in) · ≈ 90 cangilones'],
            ['Rueda de cabeza', '13 dientes, Dp 635 mm, 19,1 rpm'],
            ['Altura de elevación', 'H = 12,13 m (12,73 m entre ejes)'],
            ['P teórica = Q·H / 367', '2,12 kW'],
            ['P instalada', '× 1,75 / 0,85 × 1,25 = 5,46 kW → motor 5,5 kW']]
    sh.table(296, 128, [34, 79], rows, rowh=4.0, fs=4.8)
    # cangilon D
    vd = View(sh, 252, 62, 15)
    for k_ in range(2):
        bucket_profile(vd, 0, k_ * 304.8)
    vd.R(-12, -20, 12, 660, fc='#777777', lw=0.4)
    for k_ in range(2):
        for zz in (90, 210):
            vd.R(-16, k_ * 304.8 + zz - 5, 22, 10, fc='k', lw=0.2)
    vd.dim((0, 304.8 + 295), (203, 304.8 + 295), 4, '203', fs=FS)
    vd.dim((203, 304.8), (203, 304.8 + 295), -6, '295', fs=FS)
    vd.dim((-12, 0), (-12, 304.8), 6, '304,8 = paso', fs=FS, tside=1)
    sh.labels([(vd.X(-6), vd.Y(500), 'cadena', vd.Y(560)),
               (vd.X(-10), vd.Y(210), '2 bulones a la cadena', vd.Y(380) - 0),
               (vd.X(195), vd.Y(290), 'labio (guía del siguiente)', vd.Y(260) - 30)],
              vd.X(280), ha='left', fs=FS, sp=4.0) if False else None
    sh.lead(vd.X(-12), vd.Y(520), vd.X(-120), vd.Y(560), 'cadena', fs=FS, ha='right')
    sh.lead(vd.X(195), vd.Y(304.8 + 290), vd.X(300), vd.Y(640), 'labio (guía del siguiente)', fs=FS, ha='left') if False else None
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/DET-10')
