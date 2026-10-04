from lib import *
import data as D
from sct02 import tab_top, roof_top

S_ELEV = 37.40
SREF = 43.5


def red(sh, x, y, n):
    sh.C(x, y, 2.2, fc='#c0392b', ec='#c0392b', lw=0.3, z=8)
    sh.T(x, y, str(n), fs=5.4, ha='center', bold=True, c='white', z=9, chk=False)


def build(out):
    sh = Sheet('CL-03', 'Corte longitudinal B-B (quebrado) — recorrido del producto',
               'Interior: plano del eje de L1 (x = 7,90) · Exterior: plano del eje del elevador y la fosa (x = 11,35) · sin producto',
               '1:125 / 1:150', 4)
    FS = 5.0
    sh.vtitle(26, 281, 'CORTE B-B (quebrado)   Esc. 1:125')
    v = View(sh, 40, 182, 125)

    def P(s, z):
        return ((SREF - s) * 1000, z * 1000)

    def R(s0, s1, z0, z1, **kw):
        a = P(max(s0, s1), z0)
        return v.R(a[0], a[1], abs(s1 - s0) * 1000, (z1 - z0) * 1000, **kw)

    def LL(pts, **kw):
        return v.L([P(*p) for p in pts], **kw)
    # terreno exterior y piso interior
    sh.ground(v.X(P(43.5, 0)[0]), v.X(P(41.45, 0)[0]), v.Y(-200))
    sh.ground(v.X(P(36.45, 0)[0]), v.X(P(36.325, 0)[0]), v.Y(-200)) if False else None
    R(-0.175, 36.325, -0.15, 0.0, fc='#eeeeee', lw=0.5)
    # muros perimetrales (cortados)
    for a, b in ((35.975, 36.325), (-0.175, 0.175)):
        R(a, b, -0.4, 3.90, fc='#dddddd', lw=0.6)
        LL([((a + b) / 2, 3.90), ((a + b) / 2, 5.6)], lw=0.8)
    # cubierta en el plano de L1 y viga longitudinal / columnas (mas alla)
    rt = roof_top(D.X_L1)
    R(-0.175, 36.325, rt - 0.30, rt, fc=C_WOOD, lw=0.5)
    for st in D.S_TAB:
        R(st - 0.10, st + 0.10, 0.0, 5.76, fc='#e4e4e4', lw=0.3)
    R(-0.175, 36.325, 5.76, 5.95, fc='#bfa27a', lw=0.3)
    # tabiques (cortados) con dado de L1
    for st in D.S_TAB[1:-1]:
        R(st - 0.10, st + 0.10, 0.0, tab_top(D.X_L1), fc='#dddddd', lw=0.6)
        R(st - 0.10, st + 0.10, tab_top(D.X_L1), 3.90, fc='#bbbbbb', lw=0.5)
    # vigas carrileras
    sup = [36.15, 27.075, 18.075, 13.575, 9.075, 0.0]
    R(36.16, 37.975, 3.941, 4.241, fc='none', lw=0.4, ls=(0, (3, 2)))
    for a, b in zip(sup[1:], sup[:-1]):
        R(a + 0.01, b - 0.01, 3.941, 4.241, fc='#e0e0e0', lw=0.5)
    for st in sup:
        R(st - 0.09, st + 0.09, 3.90, 3.941, fc='#666666', lw=0.2)
    # conducto, cabezal y cola
    R(1.27, 36.325, 4.341, 5.151, fc=C_NEW, lw=0.6)
    R(36.325, 37.27, 4.341, 5.151, fc='none', lw=0.4, ls=(0, (3, 2)))
    LL([(1.27, 4.745), (36.325, 4.745)], lw=0.3, ls=(0, (4, 2)))
    for b in D.BRIDAS[:-1]:
        LL([(b, 4.341), (b, 5.151)], lw=0.25)
        R(b - 0.03, b + 0.03, 4.241, 4.341, fc=C_STEEL, lw=0.2)
    for sc, sty in ((D.S_HEAD, '-'), (D.S_TAIL, (0, (3, 2)))):
        R(sc - 0.45, sc + 0.45, 4.30, 5.19, fc=C_NEW2 if sty == '-' else 'none', lw=0.6 if sty == '-' else 0.4,
          ls=sty)
        cx, cy = v.p(*P(sc, 4.731))
        sh.C(cx, cy, 0.355 * 8, fc='none', lw=0.4, ls=sty)
    R(0.55, 1.0, 5.19, 5.40, fc='#9fb3c8', lw=0.4)
    sh.T(v.X(P(0.775, 0)[0]), v.Y(5300), 'M', fs=4.0, ha='center', bold=True, chk=False)
    # compuertas con pantalon y brazos
    for n, sg in D.GATES.items():
        R(sg - 0.175, sg + 0.175, 3.98, 4.341, fc='#c8d6e5', lw=0.4)
        LL([(sg - 0.175, 3.98), (sg - 0.30, 3.85)], lw=0.6)
        LL([(sg + 0.175, 3.98), (sg + 0.30, 3.85)], lw=0.6)
        cx, cy = v.p(*P(sg, 3.45))
        sh.C(cx, cy, 1.8, fc='white', lw=0.5)
        sh.T(cx, cy, str(n), fs=4.2, ha='center', bold=True)
    # baranda de la pasarela (mas alla)
    LL([(1.45, 5.15), (36.15, 5.15)], lw=0.4, c='#777777')
    # ---------------- exterior: plataforma, elevador, fosa ----------------
    R(36.325, 38.60, 4.02, 4.05, fc='#bbbbbb', lw=0.4)
    for sp in (37.0, 38.5):
        R(sp - 0.05, sp + 0.05, -0.20, 4.02, fc='#bbbbbb', lw=0.3)
    R(37.925, 38.025, 3.75, 4.02, fc='k', lw=0.2)
    # fosa
    f0, f1 = 36.70, 41.20
    R(f0 - 0.25, f1 + 0.25, -3.65, -3.40, fc='#d0d0d0', lw=0.5)
    R(f0 - 0.25, f0, -3.40, -0.20, fc='#d0d0d0', lw=0.5)
    R(f1, f1 + 0.25, -3.40, -0.20, fc='#d0d0d0', lw=0.5)
    v.P([P(40.70, -0.20), P(38.70, -0.20), P(39.45, -1.90), P(39.95, -1.90)], fc='#f4f4f4', lw=0.6)
    LL([(38.60, -0.20), (40.80, -0.20)], lw=1.4)
    R(38.35, 40.75, -2.50, -2.20, fc='#999999', lw=0.4)
    for sd in (38.35, 40.75):
        cx, cy = v.p(*P(sd, -2.35))
        sh.C(cx, cy, 1.0, fc='white', lw=0.4)
    # elevador (cuerpo 730 x 1220: 1,22 en el plano)
    R(S_ELEV - 0.61, S_ELEV + 0.61, -3.30, 9.60, fc='#e8c4bd', lw=0.6)
    v.P([P(S_ELEV - 0.70, 9.60), P(S_ELEV + 0.70, 9.60), P(S_ELEV + 0.70, 10.10), P(S_ELEV + 0.45, 10.33),
         P(S_ELEV - 0.45, 10.33), P(S_ELEV - 0.70, 10.10)], fc='#d9a49a', lw=0.6)
    R(S_ELEV - 0.25, S_ELEV + 0.10, 10.33, 10.55, fc='#9fb3c8', lw=0.4)
    LL([(S_ELEV - 0.30, -2.85), (S_ELEV - 0.30, 9.88)], lw=0.3, ls=(0, (3, 2)))
    LL([(S_ELEV + 0.30, -2.85), (S_ELEV + 0.30, 9.88)], lw=0.3, ls=(0, (3, 2)))
    R(S_ELEV - 1.1, S_ELEV + 1.1, 8.66, 8.70, fc='k', lw=0.2)
    LL([(S_ELEV + 0.61, 8.70), (S_ELEV + 1.1, 8.70)], lw=0.3) if False else None
    R(S_ELEV + 0.65, S_ELEV + 0.85, 4.05, 8.66, fc='none', lw=0.4)
    # desviador y chute (visto en escorzo)
    R(S_ELEV - 0.25, S_ELEV + 0.25, 8.78, 9.38, fc='#c9b0a8', lw=0.4)
    LL([(S_ELEV - 0.10, 8.78), (37.07, 5.25)], lw=1.2)
    # camion
    v.P([P(43.5, 0.25), P(41.7, 0.25), P(41.7, 1.25), P(42.6, 2.6), P(43.5, 2.6)], fc='none', lw=0.5,
        ls=(0, (4, 2)))
    for sw in (42.2, 43.2):
        cx, cy = v.p(*P(sw, 0.25))
        sh.C(cx, cy, 2.6, fc='none', lw=0.5, ls=(0, (3, 2)))
    sh.T(v.X(P(42.6, 0)[0]), v.Y(3100), 'camión batea', fs=4.4, ha='center', c='#555555')
    # ---------------- recorrido (rojo) ----------------
    reds = [(42.6, 1.6), (39.7, -1.0), (39.2, -2.6), (S_ELEV, 6.5), (S_ELEV, 9.05), (36.9, 7.2), (31.9, 4.75),
            (33.02, 2.72)]
    for i, (s_, z_) in enumerate(reds, 1):
        red(sh, *v.p(*P(s_, z_)), i)
    sh.ax.annotate('', xy=v.p(*P(40.3, -0.1)), xytext=v.p(*P(41.6, 1.2)),
                   arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=0.8))
    sh.ax.annotate('', xy=v.p(*P(S_ELEV - 0.2, 8.6)), xytext=v.p(*P(S_ELEV - 0.2, 0.5)),
                   arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=0.8))
    sh.ax.annotate('', xy=v.p(*P(26.0, 4.55)), xytext=v.p(*P(35.0, 4.55)),
                   arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=0.8))
    sh.ax.annotate('', xy=v.p(*P(32.3, 2.7)), xytext=v.p(*P(33.02, 3.5)),
                   arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=0.8))
    # ---------------- cotas ----------------
    v.dim(P(37.72, 5.19), P(D.S_HEAD, 5.19), 11, 'L = 36,90 entre ejes de ruedas', fs=FS)
    luces = [(36.15, 27.075, '9,08'), (27.075, 18.075, '9,00'), (18.075, 13.575, '4,50'), (13.575, 9.075, '4,50'),
             (9.075, 0.0, '9,07')]
    for a, b, t in luces:
        v.dim(P(a, 5.19), P(b, 5.19), 5, t, fs=FS)
    chain = [36.325, 35.975, 27.175, 26.975, 18.175, 17.975, 13.675, 13.475, 9.175, 8.975, 0.175, -0.175]
    labs = ['0,35', '8,80', '0,20', '8,80', '0,20', '4,30', '0,20', '4,30', '0,20', '8,80', '0,35']
    for a, b, t in zip(chain[:-1], chain[1:], labs):
        if b - a > -1:
            continue
        v.dim(P(a, -0.4), P(b, -0.4), -4, t, fs=FS)
    v.dim(P(36.325, -0.4), P(-0.175, -0.4), -10, '36,50', fs=FS)
    # box
    for nm, a, b in (('BOX 1 (G)', 35.975, 27.175), ('BOX 2 (G)', 26.975, 18.175), ('BOX 3 (C)', 17.975, 13.675),
                     ('BOX 4 (C)', 13.475, 9.175), ('BOX 5 (G)', 8.975, 0.175)):
        sh.T(v.X(P((a + b) / 2, 0)[0]), v.Y(1700), nm, fs=5.6, ha='center', bold=True, c='#777777')
    # niveles
    for z, t in [(10.33, '+10,33'), (9.88, '+9,88'), (8.78, '+8,78'), (4.05, '+4,05'), (-0.20, '−0,20'),
                 (-1.90, '−1,90'), (-3.40, '−3,40')]:
        sh.lev(30, v.Y(z * 1000), t, ln=8, fs=4.8)
    for z, t in [(5.151, '+5,151'), (3.90, '+3,90'), (0.0, '±0,00')]:
        sh.lev(395, v.Y(z * 1000), t, ln=9, fs=4.8)
    sh.labels([(v.X(P(S_ELEV + 0.61, 0)[0]), v.Y(7000), 'elevador de cangilones (DET-10)', v.Y(8900)),
               (v.X(P(39.7, 0)[0]), v.Y(-1000), 'tolva en fosa + alimentador de banda (DET-11)', v.Y(-1500))],
              v.X(P(34.0, 0)[0]), ha='left', fs=FS, sp=4.0) if False else None
    sh.lead(*v.p(*P(S_ELEV + 0.61, 7.0)), v.X(P(35.2, 0)[0]), v.Y(8300), 'elevador de cangilones (DET-10)', fs=FS,
            ha='left')
    sh.lead(*v.p(*P(38.2, -2.3)), v.X(P(35.2, 0)[0]), v.Y(-2600), 'tolva en fosa + alimentador de banda (DET-11)',
            fs=FS, ha='left')
    sh.lead(*v.p(*P(36.15, 2.0)), v.X(P(34.2, 0)[0]), v.Y(800), 'apoyo en cabecera + pasamuro (DET-08)', fs=FS,
            ha='left')
    sh.lead(*v.p(*P(27.075, 1.4)), v.X(P(26.2, 0)[0]), v.Y(1000), 'tabique T1 (cortado)', fs=FS, ha='left')
    sh.lead(*v.p(*P(1.0, 5.30)), v.X(P(3.0, 0)[0]), v.Y(6900), 'cabezal motriz (punto fijo)', fs=FS, ha='left')
    sh.lead(*v.p(*P(13.575, 2.6)), v.X(P(13.3, 0)[0]), v.Y(2600), 'columnas existentes (más allá)', fs=FS,
            ha='left')
    sh.T(v.X(P(20.0, 0)[0]), v.Y(2800), 'compuertas L1.01 … L1.11', fs=FS, ha='center')

    # ===================== VISTA C-C 1:150 =====================
    sh.vtitle(26, 146, 'VISTA C-C (desde el exterior, mirando al galpón)   Esc. 1:150')
    vc = View(sh, 28, 66, 150)

    def Q(x, z):
        return ((x - 0.5) * 1000, z * 1000)
    sh.ground(vc.X(Q(0.5, 0)[0]), vc.X(Q(16.0, 0)[0]), vc.Y(-200))
    # muro sur / cerramiento (detras)
    vc.R(*Q(0.5, 0.0), 15500, 3900, fc='#f2f2f2', lw=0.4)
    # plataforma y postes
    vc.R(*Q(6.90, 4.02), 8900, 30, fc='#bbbbbb', lw=0.4)
    for xp in (7.0, 9.0, 13.7, 15.7):
        vc.R(*Q(xp - 0.05, -0.20), 100, 4220, fc='#bbbbbb', lw=0.3)
    # colas L1 / L2
    for xl in (D.X_L1, D.X_L2):
        vc.R(*Q(xl - 0.34, 4.30), 680, 890, fc=C_NEW2, lw=0.5)
        cx, cy = vc.p(*Q(xl, 4.731))
        sh.C(cx, cy, 0.7, fc='white', lw=0.4)
    # elevador
    vc.R(*Q(D.X_ELEV - 0.365, -3.30), 730, 12900, fc='#e8c4bd', lw=0.6)
    vc.R(*Q(D.X_ELEV - 0.45, 9.60), 900, 730, fc='#d9a49a', lw=0.6)
    vc.R(*Q(D.X_ELEV + 0.45, 9.70), 400, 300, fc='#9fb3c8', lw=0.4)
    vc.R(*Q(D.X_ELEV - 1.1, 8.66), 2200, 40, fc='k', lw=0.2)
    # desviador y chutes a 45°
    vc.P([Q(D.X_ELEV - 0.30, 9.38), Q(D.X_ELEV + 0.30, 9.38), Q(D.X_ELEV + 0.35, 8.78), Q(D.X_ELEV - 0.35, 8.78)],
         fc='#c9b0a8', lw=0.4)
    for sgn, xl in ((-1, D.X_L1), (1, D.X_L2)):
        x0 = D.X_ELEV + sgn * 0.30
        z0 = 8.78
        vc.L([Q(x0, z0), Q(xl, 5.25)], lw=1.4)
    # escalera
    vc.L([Q(6.9, 4.05), Q(4.15, 2.13), Q(3.25, 2.13), Q(0.5, -0.20)], lw=0.9)
    # fosa (oculta)
    vc.R(*Q(9.6, -3.65), 3500, 3450, fc='none', lw=0.4, ls=(0, (3, 2)))
    vc.P([Q(10.10, -0.20), Q(12.60, -0.20), Q(11.65, -1.90), Q(11.05, -1.90)], fc='none', lw=0.4, ls=(0, (3, 2)))
    vc.dim(Q(D.X_L1, 9.6), Q(D.X_ELEV, 9.6), 4, '3,45', fs=FS)
    vc.dim(Q(D.X_ELEV, 9.6), Q(D.X_L2, 9.6), 4, '3,45', fs=FS)
    sh.T(vc.X(Q(8.95, 0)[0]), vc.Y(7600), '45°', fs=FS)
    sh.T(vc.X(Q(13.0, 0)[0]), vc.Y(7600), '45°', fs=FS)
    sh.lead(*vc.p(*Q(D.X_L1, 5.0)), vc.X(Q(3.6, 0)[0]), vc.Y(6200), 'cola L1', fs=FS, ha='right')
    sh.lead(*vc.p(*Q(D.X_L2, 5.0)), vc.X(Q(15.6, 0)[0]), vc.Y(6200), 'cola L2', fs=FS, ha='left')
    sh.lead(*vc.p(*Q(D.X_ELEV, 9.1)), vc.X(Q(13.2, 0)[0]), vc.Y(8900), 'desviador 2 vías', fs=FS, ha='left')
    sh.lead(*vc.p(*Q(4.7, 2.5)), vc.X(Q(2.6, 0)[0]), vc.Y(5200), 'escalera', fs=FS, ha='right')
    sh.lead(*vc.p(*Q(11.0, -2.5)), vc.X(Q(14.5, 0)[0]), vc.Y(-2600), 'fosa (oculta)', fs=FS, ha='left')

    # ===================== RECORRIDO + TABLAS =====================
    sh.T(136, 143, 'RECORRIDO DEL PRODUCTO (números en rojo)', fs=6.0, bold=True)
    steps = ['El camión batea retrocede hasta el tope y descarga sobre la reja (buffer 3,70 m³).',
             'La tolva en fosa escurre por gravedad (paredes ≥ 60°).',
             'El alimentador de banda dosifica 64,2 t/h con variador.',
             'El elevador de descarga continua sube el producto a 0,635 m/s.',
             'El desviador de 2 vías envía el producto a L1 o L2 (+8,78).',
             'Chute a 45° hasta la boca de carga de la cola.',
             'El Redler arrastra por el compartimiento inferior a 0,24 m/s.',
             'La compuerta abierta descarga por el pantalón y los brazos.']
    for i, t in enumerate(steps, 1):
        y = 136 - (i - 1) * 4.6
        red(sh, 138.2, y, i)
        sh.T(142.0, y, t, fs=4.8)
    rows = [['Equipo', 'Dato principal'],
            ['Tolva en fosa', '2.500×2.000 / 600×500, H 1,70 m, V = 3,70 m³'],
            ['Alimentador de banda', 'banda 800, L 2,40 m, regula a 64,2 t/h'],
            ['Elevador', 'Martin C248-725, MF 24×8, 0,635 m/s, H 12,13 m'],
            ['Desviador + chutes', '2 vías, chutes a 45°'],
            ['Redler L1 / L2', '600×400 doble, v 0,24 m/s, L 36,90 m'],
            ['Compuertas', '11 por línea: 3 por box G, 1 por box C']]
    sh.table(136, 95, [30, 64], rows, rowh=4.2, fs=4.8)
    lv = [['Nivel', 'Referencia (exterior)'],
          ['+10,33', 'superior cabeza del elevador'], ['+9,88', 'eje rueda de cabeza'],
          ['+9,38', 'descarga en la cabeza'], ['+8,78', 'salida del desviador'],
          ['+8,68', 'plataforma de cabeza'], ['+4,05', 'NPP plataforma / pasarelas'],
          ['−0,20', 'NTN terreno exterior'], ['−1,90', 'boca inferior de la tolva'],
          ['−2,20', 'banda del alimentador'], ['−2,75', 'boca de la bota'],
          ['−3,30', 'fondo de bota'], ['−3,40', 'piso de fosa']]
    sh.table(330, 146, [16, 62], lv, rowh=4.0, fs=4.8)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/CL-03')
