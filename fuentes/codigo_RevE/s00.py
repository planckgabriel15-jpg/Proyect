from lib import *
import data as D
from matplotlib.patches import FancyBboxPatch

BLUE = '#1f4e79'
S_ELEV = 37.40


def build(out):
    sh = Sheet('PL-00', 'Carátula e índice del legajo de planos', 'Tercera entrega · Ingeniería de detalle',
               '—', 1)
    # ===================== ENCABEZADO =====================
    sh.T(25, 273, 'PROYECTO FINAL — INGENIERÍA INDUSTRIAL · UTN FRC', fs=8.6, bold=True)
    sh.T(25, 264, 'Sistema de distribución de fertilizantes a granel con transportadores Redler', fs=15, bold=True)
    sh.T(25, 256, 'Aceitera General Deheza — Planta de Acopio Río Primero (Córdoba)', fs=9.5, c='#333333')
    sh.T(25, 249.5, 'Legajo de planos constructivos — Rev. E — 03/10/2026', fs=9.0, bold=True, c=BLUE)
    sh.L([25, 405], [245, 245], lw=1.0, chk=False)

    # ===================== INDICE =====================
    rows = [['Código', 'Lámina', 'Escala'],
            ['PL-00', 'Carátula e índice', '—'],
            ['PL-01', 'Planta general de distribución', '1:125'],
            ['CT-02', 'Corte transversal A-A + detalle 1', '1:75 / 1:25'],
            ['CL-03', 'Corte longitudinal B-B (quebrado) y vista C-C — recorrido del producto', '1:125 / 1:150'],
            ['DET-04', 'Conducto Redler, cadena y paletas', '1:5 / 1:10 / 1:20'],
            ['DET-05', 'Cabezal motriz y cola tensora', '1:10 / 1:25'],
            ['DET-06', 'Compuerta guillotina, boca en pantalón y brazos distribuidores', '1:2 / 1:10 / 1:20'],
            ['DET-07', 'Apoyo de la viga carrilera sobre tabique interior', '1:5 / 1:10'],
            ['DET-08', 'Pasamuro y apoyos en los muros de cabecera', '1:5 / 1:25'],
            ['DET-09', 'Pasarela de mantenimiento y escalera de acceso', '1:10 / 1:20 / 1:25 / 1:100'],
            ['DET-10', 'Elevador de cangilones, desviador de 2 vías y chutes', '1:15 / 1:20 / 1:75 / 1:100'],
            ['DET-11', 'Tolva de recepción en fosa y alimentador de banda', '1:10 / 1:30 / 1:50'],
            ['DET-12', 'Galpón existente — pórtico tipo, tabique y cerramiento', '1:20 / 1:25 / 1:50 / 1:100 / 1:150'],
            ['ISO-13', 'Vista axonométrica del sistema', 's/e']]
    sh.table(25, 240, [18, 108, 40], rows, rowh=4.2, fs=5.2, bold_first_col=True)

    # ===================== DATOS PRINCIPALES =====================
    sh.T(200, 240, 'DATOS PRINCIPALES DEL SISTEMA', fs=6.8, bold=True)
    datos = [['Elemento', 'Especificación'],
             ['Caudal de diseño', '64,20 t/h (urea, ρ = 720 kg/m³, k = 0,43)'],
             ['Redler L1 / L2', '36,90 m entre ejes · 600×400 doble compartimiento · 0,24 m/s'],
             ['Cadena / paletas', '2 × DIN 8167 M224 paso 200 · paleta 370×280×5 · 380 por lazo'],
             ['Accionamiento Redler', 'motorreductor 15 kW · i ≈ 225 · eje motriz Ø140 · ruedas Z = 11'],
             ['Esfuerzos', 'F = 33,4 kN · T = 11,86 kN·m · margen de la cadena 1,72'],
             ['Elevador de cangilones', 'Martin C248-725 · H = 12,13 m · 0,635 m/s · motor 5,5 kW'],
             ['Viga carrilera', 'tubo 300×200×10 F-24 · tramos simplemente apoyados'],
             ['Apoyo en tabique', 'placa 1.000×180×18 + 4 anclajes químicos M16'],
             ['Pasarela', 'ménsula UPC 80 c/1,00 m + cartela · paso libre 0,905 · NPP +4,05'],
             ['Baranda', 'montante 50×50×3 c/1,00 m · pasamanos +1,10 sobre NPP'],
             ['Compuertas', '11 por línea (22) · guillotina 600×350 + boca en pantalón'],
             ['Recepción', 'tolva en fosa 3,70 m³ + alimentador de banda 800 con variador']]
    sh.table(200, 236, [38, 128], datos, rowh=4.0, fs=5.0, bold_first_col=True)

    # ===================== DIAGRAMA DE PROCESO =====================
    sh.T(200, 172, 'DIAGRAMA DEL PROCESO DE DESCARGA Y DISTRIBUCIÓN', fs=6.8, bold=True)
    BW, BH = 42, 14

    def node(cx, cy, title, l1, l2, ref, fc='#f4f7fa'):
        p = FancyBboxPatch((cx - BW / 2, cy - BH / 2), BW, BH, boxstyle='round,pad=0,rounding_size=1.6',
                           fc=fc, ec=BLUE, lw=0.9, zorder=3)
        sh.ax.add_patch(p)
        sh.T(cx, cy + 4.3, title, fs=5.4, ha='center', bold=True, z=4)
        sh.T(cx, cy + 1.3, l1, fs=4.4, ha='center', z=4)
        sh.T(cx, cy - 1.2, l2, fs=4.4, ha='center', z=4)
        sh.T(cx, cy - 4.6, ref, fs=4.5, ha='center', bold=True, c=BLUE, z=4)

    def arrow(p0, p1):
        sh.ax.annotate('', xy=p1, xytext=p0, arrowprops=dict(arrowstyle='-|>', lw=1.0, color=BLUE,
                                                             shrinkA=0, shrinkB=0), zorder=2)
    xs = [222, 273, 324, 375]
    y1, y2, y3, ym = 152, 128, 103, 115.5
    node(xs[0], y1, '1 · Camión batea', 'descarga por gravedad', 'sobre reja a nivel de terreno', 'PL-01 / CL-03')
    node(xs[1], y1, '2 · Tolva en fosa', 'V = 3,70 m³ · reja 2,5 × 2,0 m', 'piso de fosa a −3,40', 'DET-11')
    node(xs[2], y1, '3 · Alimentador de banda', 'banda 800 con variador', 'regula el caudal a 64,2 t/h', 'DET-11')
    node(xs[3], y1, '4 · Elevador de cangilones', 'H = 12,13 m · 0,635 m/s', 'Martin C248-725 · 5,5 kW', 'DET-10')
    node(xs[3], ym, '5 · Desviador 2 vías', '+ chutes a 45° hacia la', 'boca de carga de L1 / L2', 'DET-10')
    node(xs[2], y2, '6 · Redler L1', 'L = 36,90 m · 0,24 m/s', 'Q = 64,2 t/h · doble cadena', 'DET-04 / 05 / 07 / 08')
    node(xs[2], y3, '6 · Redler L2', 'ídem L1 (simétrico)', 'sobre viga tubo 300×200 + pasarela', 'DET-04 / 05 / 07 / 08')
    node(xs[1], y2, '7 · Compuertas L1', '11 guillotinas + pantalón', '+ brazos distribuidores', 'DET-06')
    node(xs[1], y3, '7 · Compuertas L2', '11 guillotinas + pantalón', '+ brazos distribuidores', 'DET-06')
    node(xs[0], ym, '8 · Boxes 1 a 5', 'G · G · C · C · G (desde recepción)', 'por ambos flancos de cada box',
         'PL-01 / CT-02', fc='#eef4ea')
    for i in range(3):
        arrow((xs[i] + BW / 2, y1), (xs[i + 1] - BW / 2, y1))
    arrow((xs[3], y1 - BH / 2), (xs[3], ym + BH / 2))
    arrow((xs[3] - BW / 2, ym + 2), (xs[2] + BW / 2, y2 - 2))
    arrow((xs[3] - BW / 2, ym - 2), (xs[2] + BW / 2, y3 + 2))
    arrow((xs[2] - BW / 2, y2), (xs[1] + BW / 2, y2))
    arrow((xs[2] - BW / 2, y3), (xs[1] + BW / 2, y3))
    arrow((xs[1] - BW / 2, y2 - 2), (xs[0] + BW / 2, ym + 2))
    arrow((xs[1] - BW / 2, y3 + 2), (xs[0] + BW / 2, ym - 2))
    sh.T(200, 89, 'Numeración 1 a 8 = pasos del recorrido del producto (ver CL-03). Ubicación física de cada equipo: '
         'ver esquema de ubicación.', fs=4.6)

    # ===================== CONVENCIONES =====================
    sh.T(200, 80, 'CONVENCIONES DE DIBUJO', fs=6.8, bold=True)
    sh.P([(200, 72), (209, 72), (209, 75), (200, 75)], fc=C_EXIST, lw=0.4, chk=False)
    sh.T(212, 73.5, 'Construcción existente (gris)', fs=4.8)
    sh.P([(300, 72), (309, 72), (309, 75), (300, 75)], fc=C_NEW, lw=0.4, chk=False)
    sh.T(312, 73.5, 'Elemento nuevo del proyecto (celeste)', fs=4.8)
    sh.L([200, 209], [68.5, 68.5], lw=0.6, ls=(0, (3, 2)), chk=False)
    sh.T(212, 68.5, 'Oculto / bajo nivel', fs=4.8)
    sh.L([300, 309], [68.5, 68.5], lw=0.6, ls=(0, (8, 2, 1, 2)), chk=False)
    sh.T(312, 68.5, 'Eje / línea de corte', fs=4.8)
    sh.ax.annotate('', xy=(209, 63.5), xytext=(200, 63.5), arrowprops=dict(arrowstyle='-|>', lw=1.0, color=BLUE))
    sh.T(212, 63.5, 'Flujo de producto (flecha)', fs=4.8)
    sh.T(312, 63.5, 'Cotas en m (planta / cortes) y en mm (detalles)', fs=4.8)

    # ===================== ESQUEMA DE UBICACION 1:300 =====================
    sh.vtitle(25, 165, 'ESQUEMA DE UBICACIÓN Y REFERENCIA DE LÁMINAS   Esc. 1:300')
    v = View(sh, 36, 66, 300)

    def S(s):
        return s * 1000

    def R(s0, s1, x0, x1, **kw):
        return v.R(S(s0), S(x0), S(s1 - s0), S(x1 - x0), **kw)
    R(-0.175, 36.325, -0.15, 0.0, fc=C_EXIST, lw=0.4)
    R(-0.175, 36.325, 22.70, 22.85, fc=C_EXIST, lw=0.4)
    for a, b in [(-0.175, 0.175), (35.975, 36.325), (8.975, 9.175), (13.475, 13.675), (17.975, 18.175),
                 (26.975, 27.175)]:
        R(a, b, -0.15, 22.85, fc=C_EXIST, lw=0.4)
    for sc in [0.0, 9.075, 13.575, 18.075, 27.075, 36.15]:
        for xc in (D.X_C1, D.X_C2):
            R(sc - 0.2, sc + 0.2, xc - 0.2, xc + 0.2, fc=C_DARK, lw=0.2)
    for xl, sd in ((D.X_L1, 1), (D.X_L2, -1)):
        R(1.45, 36.15, min(xl + sd * 0.35, xl + sd * 1.264), max(xl + sd * 0.35, xl + sd * 1.264), fc='#f2f2f2',
          lw=0.3)
        R(1.27, 37.27, xl - 0.304, xl + 0.304, fc=C_NEW, lw=0.5)
        R(0.37, 1.27, xl - 0.34, xl + 0.34, fc=C_NEW2, lw=0.4)
        R(37.27, 38.17, xl - 0.34, xl + 0.34, fc=C_NEW2, lw=0.4)
        for sg in D.GATES.values():
            v.L([(S(sg), S(xl - 0.45)), (S(sg), S(xl + 0.45))], lw=0.5, c=BLUE)
    R(36.325, 38.60, 6.90, 15.80, fc='none', lw=0.4)
    R(36.40, 37.30, 0.50, 6.90, fc='none', lw=0.4)
    R(36.45, 41.45, 9.60, 13.10, fc=C_EXIST, lw=0.4)
    R(38.70, 40.70, 10.10, 12.60, fc='#8c8c8c', lw=0.3)
    R(S_ELEV - 0.61, S_ELEV + 0.61, D.X_ELEV - 0.365, D.X_ELEV + 0.365, fc='#d9a49a', lw=0.5)
    R(41.75, 41.95, 9.60, 13.10, fc='#999999', lw=0.3)
    boxes = [('BOX 5 (G)', 4.575), ('BOX 4 (C)', 11.325), ('BOX 3 (C)', 15.825), ('BOX 2 (G)', 22.575),
             ('BOX 1 (G)', 31.575)]
    for nm, sm in boxes:
        sh.T(v.X(S(sm)), v.Y(S(1.6)), nm, fs=4.4, ha='center', bold=True, c='#555555')
    sh.T(v.X(S(5.5)), v.Y(S(-1.3)), 'MURO OESTE — PORTONES', fs=4.4, ha='center', c='#555555')
    sh.T(v.X(S(13.0)), v.Y(S(24.1)), 'MURO ESTE', fs=4.4, ha='center', c='#555555')
    sh.T(v.X(S(2.6)), v.Y(S(D.X_L1 - 2.2)), 'L1', fs=6, ha='center', bold=True, c=BLUE)
    sh.T(v.X(S(2.6)), v.Y(S(D.X_L2 + 2.2)), 'L2', fs=6, ha='center', bold=True, c=BLUE)
    sh.T(v.X(S(43.0)), v.Y(S(15.2)), 'RECEPCIÓN (sur)\ncamión', fs=4.2, ha='left', c='#555555') if False else None

    def call(s_, x_, r_, code, lab):
        cx, cy = v.p(S(s_), S(x_))
        sh.C(cx, cy, r_, fc='none', lw=0.5, ls=(0, (3, 2)))
        bx, by = lab
        tid = sh.nid()
        d = np.array([bx - cx, by - cy])
        dd = np.hypot(*d)
        p0 = np.array([cx, cy]) + d / dd * r_
        p1 = np.array([bx, by]) - d / dd * 3.6
        sh.L([p0[0], p1[0]], [p0[1], p1[1]], lw=LW_T, owner=tid)
        sh.C(bx, by, 3.6, fc='white', lw=0.7, owner=tid, z=6)
        sh.L([bx - 3.6, bx + 3.6], [by, by], lw=0.4, owner=tid, z=7)
        sh.T(bx, by + 1.6, 'D' + code[-2:].lstrip('0'), fs=4.8, ha='center', bold=True, tid=tid, z=8)
        sh.T(bx, by - 1.6, code, fs=3.5, ha='center', tid=tid, z=8)
    call(0.8, D.X_L2, 3.2, 'DET-05', (44, 150))
    call(15.77, D.X_L2, 2.6, 'DET-06', (95, 150))
    call(18.075, D.X_L1, 2.6, 'DET-07', (92, 54))
    call(36.15, D.X_L1, 3.0, 'DET-08', (140, 54))
    call(6.5, D.X_L1 + 0.8, 2.4, 'DET-09', (60, 104))
    call(25.52, D.X_L1, 2.0, 'DET-04', (118, 54))
    call(S_ELEV, D.X_ELEV, 3.0, 'DET-10', (189, 128))
    call(39.7, D.X_ELEV, 3.4, 'DET-11', (189, 88))
    # cortes
    sA = 36.15 - 9.30
    v.L([(S(sA), S(-2.6)), (S(sA), S(24.6))], lw=0.5, ls=(0, (8, 2, 1, 2)), chk=False)
    for yy in (24.6, -2.6):
        px, py = v.p(S(sA), S(yy))
        sh.ax.annotate('', xy=(px - 4, py), xytext=(px, py), arrowprops=dict(arrowstyle='-|>', lw=0.9, color='k'))
        sh.T(px + 1.2, py, 'A', fs=6.4, bold=True, ha='left')
    for (xx, yy) in ((-1.4, D.X_L1), (43.2, D.X_ELEV)):
        px, py = v.p(S(xx), S(yy))
        sh.ax.annotate('', xy=(px, py - 4), xytext=(px, py), arrowprops=dict(arrowstyle='-|>', lw=0.9, color='k'))
        sh.T(px + 1.2, py - 3.5, 'B', fs=6.4, bold=True, ha='left')
    v.L([(S(-1.4), S(D.X_L1)), (S(43.2), S(D.X_L1))], lw=0.4, ls=(0, (8, 2, 1, 2)), chk=False) if False else None
    sC = 42.6
    for yy in (15.2, 7.4):
        px, py = v.p(S(sC), S(yy))
        sh.ax.annotate('', xy=(px - 4, py), xytext=(px, py), arrowprops=dict(arrowstyle='-|>', lw=0.9, color='k'))
        sh.T(px + 1.2, py, 'C', fs=6.4, bold=True, ha='left')
    v.L([(S(sC), S(7.4)), (S(sC), S(15.2))], lw=0.5, ls=(0, (8, 2, 1, 2)), chk=False)
    # norte
    nx, ny = 168, 150
    sh.C(nx, ny, 4.0, fc='white', lw=0.6, z=3)
    sh.P([(nx - 4.0, ny), (nx + 2.6, ny + 1.4), (nx + 1.3, ny), (nx + 2.6, ny - 1.4)], fc='k', lw=0.3, z=5)
    sh.T(nx - 6.6, ny, 'N', fs=7, bold=True, ha='center')
    sh.T(25, 42, 'Cortes: A-A → CT-02 · B-B → CL-03 · C-C → CL-03 · Galpón existente → DET-12 · Vista general → ISO-13',
         fs=4.8)
    return sh.save(out + '.png', out + '.pdf')


if __name__ == '__main__':
    build('out/PL-00')
