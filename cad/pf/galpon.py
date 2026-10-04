"""Fase 2: galpón existente en el espacio modelo (1:1, mm).

Fuente: PDF Rev E (PL-01, CT-02, CL-03, DET-08, DET-12) y su código (fuentes/codigo_RevE).
Coordenadas: X de oeste a este (0 = cara interior del muro oeste), s de norte a sur
(0 = eje del muro norte), Z cota (0 = NPT). Todo en mm.
"""
from . import config as C
from .dib import Vista, ESC_HORMIGON, ESC_TERRENO, ESC_MADERA

# ------------------------------------------------------------------ datos (Rev E)
ANCHO = 22700
E_LAT, E_CAB = 150, 350
S_EJES = [0, 9075, 13575, 18075, 27075, 36150]            # muro N, T4, T3, T2, T1, muro S
S_TAB = S_EJES[1:-1]
E_TAB = 200
S_CAB_N, S_CAB_S = (-175, 175), (35975, 36325)
X_C1, X_C2, X_CUMBRERA = 9350, 13350, 11350
COL = 200
BOXES = [('5', 175, 8975), ('4', 9175, 13475), ('3', 13675, 17975), ('2', 18175, 26975), ('1', 27175, 35975)]
Z_TAB, Z_SUP = 3000, 3900
X_SUP0, X_SUP1 = 5700, 8100                                # rampa del suplemento
Z_VIGA_MADERA = 5760
NTT_O, NTT_C, NTT_E = 5600, 6550, 5750
PAQ_CUBIERTA = 350                                          # NTT a cara inferior de cabios
CORREA = (120, 50)                                          # correa de cubierta (ancho × alto)
CORREAS_X = [800 + 1500 * k for k in range(15) if 800 + 1500 * k < ANCHO]
ALERO = 300                                                 # vuelo de la cubierta desde la cara interior
NTN = -200
LOSA, BASE = 150, 150
MURO_FUND, ZAP = -350, (450, 150)                           # muro perimetral hasta -0,35; zapata 0,45 × 0,15
CAB_FUND = -400                                             # cabeceras hasta -0,40 (CL-03)
TAB_FUND, FUND_TAB = -300, (900, 300)                       # tabique hasta -0,30; fundación corrida 0,90 × 0,30
CHAPA_OFF = 20                                              # chapa a 20 mm de la cara exterior del muro (DET-12·C)
CORREAS_MURO_Z = [4300, 5000]                               # correas del cerramiento (50 × 75)
MACH = 25                                                   # tablas del suplemento


def ntt(x):
    """Nivel de techo terminado (mm) en la abscisa x (mm)."""
    if x <= X_CUMBRERA:
        return NTT_O + (NTT_C - NTT_O) * x / X_CUMBRERA
    return NTT_C - (NTT_C - NTT_E) * (x - X_CUMBRERA) / (ANCHO - X_CUMBRERA)


def tope_tabique(x):
    if x <= X_SUP0:
        return Z_TAB
    if x <= X_SUP1:
        return Z_TAB + (Z_SUP - Z_TAB) * (x - X_SUP0) / (X_SUP1 - X_SUP0)
    return Z_SUP


def portones():
    """Portones del muro oeste: uno por box, centrados (ancho según el dibujo del PDF Rev E, sin cota)."""
    out = []
    for _, a, b in BOXES:
        m, w = (a + b) / 2, min(3500, (b - a) * 0.6)
        out.append((m - w / 2, m + w / 2))
    return out


# ================================================================== zona P: planta
def planta(msp):
    v = Vista(msp, C.ZONAS['P'][0], 1, escala=125)

    def R(x0, s0, x1, s1, capa):
        return v.rect(x0, -s0, x1, -s1, capa)

    hc = 'EX-HORMIGON-CORTE'
    # cabeceras y muro este
    for s0, s1 in (S_CAB_N, S_CAB_S):
        v.rayar(R(-E_LAT, s0, ANCHO + E_LAT, s1, hc), 'SOLID', 'AN-RAYADO-EX')
    v.rayar(R(ANCHO, S_CAB_N[1], ANCHO + E_LAT, S_CAB_S[0], hc), 'SOLID', 'AN-RAYADO-EX')
    # muro oeste interrumpido por los portones
    cortes = [S_CAB_N[1]] + [c for p in portones() for c in p] + [S_CAB_S[0]]
    for s0, s1 in zip(cortes[0::2], cortes[1::2]):
        v.rayar(R(-E_LAT, s0, 0, s1, hc), 'SOLID', 'AN-RAYADO-EX')
    for s0, s1 in portones():          # hoja del portón (cerramiento existente)
        v.linea((-E_LAT / 2, -s0), (-E_LAT / 2, -s1), 'EX-CERRAMIENTO')
    # tabiques: sin suplemento (X 0 a 5,70) solo contorno; con suplemento, relleno
    for s in S_TAB:
        v.polilinea([(X_SUP0, -(s - E_TAB / 2)), (0, -(s - E_TAB / 2)), (0, -(s + E_TAB / 2)),
                     (X_SUP0, -(s + E_TAB / 2))], hc)
        v.rayar(R(X_SUP0, s - E_TAB / 2, ANCHO, s + E_TAB / 2, hc), 'SOLID', 'AN-RAYADO-EX')
    # columnas: intermedias C1/C2 y en los muros, en cada línea de apoyo
    for s in S_EJES:
        for x in (X_C1, X_C2, -E_LAT / 2, ANCHO + E_LAT / 2):
            v.rayar(R(x - COL / 2, s - COL / 2, x + COL / 2, s + COL / 2, 'EX-COLUMNAS'), 'SOLID', 'AN-RAYADO-EX',
                    color=7)
    # ejes del edificio
    for s in S_EJES:
        v.linea((-2500, -s), (ANCHO + 2500, -s), 'G-EJES')
    for x in (X_C1, X_CUMBRERA, X_C2):
        v.linea((x, 2500), (x, -(S_CAB_S[1] + 2500)), 'G-EJES')


# ================================================================== cubierta (corte transversal)
def _cubierta_transversal(v, x0=-ALERO, x1=ANCHO + ALERO, cabio_desde=-E_LAT, cabio_hasta=ANCHO + E_LAT):
    """Cubierta de chapa (cortada), correas (cortadas) y cabios (en vista) en un corte X-Z."""
    xs = [x0, X_CUMBRERA, x1]
    v.polilinea([(x, ntt(x)) for x in xs], 'EX-CERRAMIENTO', lineweight=35)
    # cabios: de NTT − 0,05 a NTT − 0,35
    ca = [cabio_desde, X_CUMBRERA, cabio_hasta]
    v.polilinea([(x, ntt(x) - CORREA[1]) for x in ca] + [(x, ntt(x) - PAQ_CUBIERTA) for x in reversed(ca)],
                'EX-MADERA', cerrada=True)
    # correas cortadas, perpendiculares a la pendiente
    for xc in CORREAS_X:
        a, b = xc - CORREA[0] / 2, xc + CORREA[0] / 2
        pl = v.polilinea([(a, ntt(a)), (b, ntt(b)), (b, ntt(b) - CORREA[1]), (a, ntt(a) - CORREA[1])],
                         'EX-MADERA', cerrada=True)
        v.rayar(pl, 'SOLID', 'AN-RAYADO-EX')


def _cerramiento_lateral(v, lado):
    """Muro perimetral cortado (H° + zapata), chapa y correas del cerramiento. lado: -1 oeste, +1 este."""
    hc = 'EX-HORMIGON-CORTE'
    xi = 0 if lado < 0 else ANCHO                 # cara interior
    xe = xi + lado * E_LAT                        # cara exterior
    m = v.rect(min(xi, xe), MURO_FUND, max(xi, xe), Z_SUP, hc)
    v.rayar(m, 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
    # zapata corrida 0,45 × 0,15: al ras de la cara interior y 0,30 hacia afuera (DET-12·C)
    zx0, zx1 = sorted((xi, xe + lado * (ZAP[0] - E_LAT)))
    zp = v.rect(zx0, MURO_FUND - ZAP[1], zx1, MURO_FUND, hc)
    v.rayar(zp, 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
    # chapa del cerramiento (cortada) por fuera del muro, hasta la cubierta
    xch = xe + lado * CHAPA_OFF
    v.linea((xch, Z_SUP - 50), (xch, ntt(xi) - CORREA[1]), 'EX-CERRAMIENTO', lineweight=35)
    for zc in CORREAS_MURO_Z:
        a, b = sorted((xch - lado * 5, xch - lado * 55))
        pl = v.rect(a, zc, b, zc + 75, 'EX-MADERA')
        v.rayar(pl, 'SOLID', 'AN-RAYADO-EX')
    # terreno exterior (NTN -0,20) con relleno
    ta, tb = sorted((xe, xe + lado * 1500))
    v.linea((ta, NTN), (tb, NTN), 'EX-TERRENO')
    tr = v.rect(ta, NTN - 150, tb, NTN, 'EX-TERRENO', lineweight=0)
    v.rayar(tr, 'EARTH', 'AN-RAYADO-EX', ESC_TERRENO)


# ================================================================== zona A: corte A-A (s = 26,85, mirando al norte)
def corte_aa(msp):
    v = Vista(msp, C.ZONAS['A'][0], 1, escala=75)
    hc = 'EX-HORMIGON-CORTE'
    # losa + base cortadas
    v.rayar(v.rect(0, -LOSA, ANCHO, 0, hc), 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
    v.rayar(v.rect(0, -LOSA - BASE, ANCHO, -LOSA, 'EX-TERRENO'), 'EARTH', 'AN-RAYADO-EX', ESC_TERRENO)
    for lado in (-1, 1):
        _cerramiento_lateral(v, lado)
    # tabique T2 en vista: H° hasta +3,00 y suplemento de machimbre (tablas c/0,30)
    cols = [(xc - COL / 2, xc + COL / 2) for xc in (X_C1, X_C2)]

    def tramos(x0, x1):
        """Tramos de [x0, x1] fuera de las columnas (las columnas tapan el tabique)."""
        out, a = [], x0
        for c0, c1 in cols:
            if c1 <= a or c0 >= x1:
                continue
            if c0 > a:
                out.append((a, c0))
            a = max(a, c1)
        if a < x1:
            out.append((a, x1))
        return out
    for a, b in tramos(0, X_SUP0):                              # tope del H° sin suplemento
        v.linea((a, Z_TAB), (b, Z_TAB), 'EX-HORMIGON-VISTA')
    for a, b in tramos(X_SUP0, ANCHO):                          # junta H° / suplemento
        v.linea((a, Z_TAB), (b, Z_TAB), 'EX-HORMIGON-VISTA')
    v.polilinea([(X_SUP0, Z_TAB), (X_SUP1, Z_SUP)], 'EX-MADERA')
    for a, b in tramos(X_SUP1, ANCHO):
        v.linea((a, Z_SUP), (b, Z_SUP), 'EX-MADERA')
    for z in (3300, 3600):                                      # tablas del machimbre c/0,30
        x = X_SUP0 + (z - Z_TAB) / (Z_SUP - Z_TAB) * (X_SUP1 - X_SUP0)
        for a, b in tramos(x, ANCHO):
            v.linea((a, z), (b, z), 'EX-MADERA', lineweight=18)
    # columnas C1/C2 en la línea de T2 (en vista) y viga longitudinal de madera (cortada)
    for c0, c1 in cols:
        for xc in (c0, c1):
            v.linea((xc, 0), (xc, Z_VIGA_MADERA), 'EX-COLUMNAS', lineweight=25)
    for xc in (X_C1, X_C2):
        top = ntt(xc) - PAQ_CUBIERTA
        pl = v.rect(xc - COL / 2, Z_VIGA_MADERA, xc + COL / 2, top, 'EX-MADERA', lineweight=35)
        v.rayar(pl, 'ANSI31', 'AN-RAYADO-EX', ESC_MADERA, angulo=-45)
    _cubierta_transversal(v)


# ================================================================== zona B: corte B-B quebrado (mirando al oeste)
X_PLANO_INT, X_PLANO_EXT, S_QUIEBRE = 7900, 11350, 36325


def corte_bb(msp):
    v = Vista(msp, C.ZONAS['B'][0], -1, escala=125)      # u = s (crece hacia la izquierda)
    hc = 'EX-HORMIGON-CORTE'
    # cabeceras cortadas + chapa hasta la cubierta en el plano X = 7,90
    rt = ntt(X_PLANO_INT)
    for s0, s1 in (S_CAB_N, S_CAB_S):
        v.rayar(v.rect(s0, CAB_FUND, s1, Z_SUP, hc), 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
        v.linea(((s0 + s1) / 2, Z_SUP), ((s0 + s1) / 2, rt - PAQ_CUBIERTA), 'EX-CERRAMIENTO', lineweight=35)
    # tabiques cortados en X = 7,90 (tope +3,825 sobre la rampa del suplemento), con fundación corrida
    zt = tope_tabique(X_PLANO_INT)
    for s in S_TAB:
        v.rayar(v.rect(s - E_TAB / 2, TAB_FUND, s + E_TAB / 2, zt, hc), 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
        for sg in (-1, 1):
            a, b = sorted((s + sg * E_TAB / 2, s + sg * (E_TAB / 2 + MACH)))
            v.rayar(v.rect(a, Z_TAB, b, zt, 'EX-MADERA'), 'SOLID', 'AN-RAYADO-EX')
        v.rayar(v.rect(s - FUND_TAB[0] / 2, TAB_FUND - FUND_TAB[1], s + FUND_TAB[0] / 2, TAB_FUND, hc),
                'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
    # losa y base entre apoyos
    bordes = [S_CAB_N[1]] + [c for s in S_TAB for c in (s - E_TAB / 2, s + E_TAB / 2)] + [S_CAB_S[0]]
    for a, b in zip(bordes[0::2], bordes[1::2]):
        v.rayar(v.rect(a, -LOSA, b, 0, hc), 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
        v.rayar(v.rect(a, -LOSA - BASE, b, -LOSA, 'EX-TERRENO'), 'EARTH', 'AN-RAYADO-EX', ESC_TERRENO)
    # cubierta cortada en el plano X = 7,90
    v.polilinea([(S_CAB_N[0], rt), (S_CAB_S[1], rt)], 'EX-CERRAMIENTO', lineweight=35)
    v.rect(S_CAB_N[0], rt - PAQ_CUBIERTA, S_CAB_S[1], rt - CORREA[1], 'EX-MADERA')
    # exterior (plano X = 11,35): terreno natural, interrumpido por la fosa (s 36,45 a 41,45)
    for a, b in ((S_QUIEBRE, 36450), (41450, 43500)):
        v.linea((a, NTN), (b, NTN), 'EX-TERRENO')
        v.rayar(v.rect(a, NTN - 150, b, NTN, 'EX-TERRENO', lineweight=0), 'EARTH', 'AN-RAYADO-EX', ESC_TERRENO)


# ================================================================== zona C: vista C-C desde el exterior (mirando al norte)
def vista_cc(msp):
    v = Vista(msp, C.ZONAS['C'][0], 1, escala=125)
    x0, x1 = -E_LAT, ANCHO + E_LAT
    v.polilinea([(x0, NTN), (x0, Z_SUP), (x1, Z_SUP), (x1, NTN)], 'EX-HORMIGON-VISTA')
    # cerramiento de chapa hasta la cubierta (frontón)
    v.polilinea([(x0, Z_SUP), (x0, ntt(x0) - PAQ_CUBIERTA), (X_CUMBRERA, ntt(X_CUMBRERA) - PAQ_CUBIERTA),
                 (x1, ntt(x1) - PAQ_CUBIERTA), (x1, Z_SUP)], 'EX-CERRAMIENTO')
    # borde de la cubierta (frontón): NTT y cara inferior de cabios
    xs = [-ALERO, X_CUMBRERA, ANCHO + ALERO]
    v.polilinea([(x, ntt(x)) for x in xs] + [(x, ntt(x) - PAQ_CUBIERTA) for x in reversed(xs)], 'EX-MADERA',
                cerrada=True)
    # columnas visibles sobre el muro (en la cabecera sur)
    for xc in (-E_LAT / 2, X_C1, X_C2, ANCHO + E_LAT / 2):
        v.rect(xc - COL / 2, Z_SUP, xc + COL / 2, ntt(xc) - PAQ_CUBIERTA, 'EX-COLUMNAS', lineweight=25)
    v.linea((-1500, NTN), (ANCHO + 1500, NTN), 'EX-TERRENO')
    v.rayar(v.rect(-1500, NTN - 150, ANCHO + 1500, NTN, 'EX-TERRENO', lineweight=0), 'EARTH', 'AN-RAYADO-EX',
            ESC_TERRENO)


# ================================================================== zona DET12: detalles del galpón
def _origen_det12(dx):
    o = C.ZONAS['DET12'][0]
    return (o[0] + dx, o[1])


def det12_b(msp):
    """B — Tabique H° + machimbre (corte), 1:25. Interrupción entre +0,60 y +2,70."""
    v = Vista(msp, _origen_det12(0), 1, escala=25)
    DZ = 1900

    def z(zz):
        return zz - DZ if zz >= 2700 else zz
    hc, q = 'EX-HORMIGON-CORTE', 'EX-HORMIGON-VISTA'
    v.rayar(v.rect(-FUND_TAB[0] / 2, TAB_FUND - FUND_TAB[1], FUND_TAB[0] / 2, TAB_FUND, hc), 'AR-CONC',
            'AN-RAYADO-EX', ESC_HORMIGON)
    for a, b in ((-700, -100), (100, 700)):
        v.rayar(v.rect(a, -LOSA, b, 0, hc), 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
        v.rayar(v.rect(a, -LOSA - BASE, b, -LOSA, 'EX-TERRENO'), 'EARTH', 'AN-RAYADO-EX', ESC_TERRENO)
    # tramo inferior (−0,30 a +0,60) con el quiebre como borde superior
    zz = v.zigzag((100, 600), (-100, 600))
    pl = v.polilinea([(-100, TAB_FUND), (100, TAB_FUND)] + zz, hc, cerrada=True)
    v.rayar(pl, 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
    v.prolongar((-100, 600), (100, 600), q)
    # tramo superior (+2,70 a +3,00) con el quiebre como borde inferior, y núcleo del suplemento
    zz = v.zigzag((-100, z(2700)), (100, z(2700)))
    pl = v.polilinea(zz + [(100, z(Z_TAB)), (-100, z(Z_TAB))], hc, cerrada=True)
    v.rayar(pl, 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
    v.prolongar((-100, z(2700)), (100, z(2700)), q)
    v.rayar(v.rect(-100, z(Z_TAB), 100, z(Z_SUP), hc), 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
    for a in (-100 - MACH, 100):
        v.rayar(v.rect(a, z(Z_TAB), a + MACH, z(Z_SUP), 'EX-MADERA'), 'ANSI31', 'AN-RAYADO-EX', ESC_MADERA,
                angulo=45)
    # armadura existente: barras verticales y horizontales (puntos) c/0,20
    for xa in (-60, 60):
        v.linea((xa, TAB_FUND - FUND_TAB[1] + 40), (xa, 560), q)
        v.linea((xa, z(2750)), (xa, z(2950)), q)
        for zz_ in (-100, 100, 300, 500):
            v.punto((xa, zz_), 12, q)
    return v


def det12_c(msp):
    """C — Muro perimetral (corte), 1:50. u = X + 0,15 (cara exterior en 0). Interrupción entre +0,70 y +3,30."""
    v = Vista(msp, _origen_det12(6000), 1, escala=50)
    DZ = 2000

    def z(zz):
        return zz - DZ if zz >= 2900 else zz
    hc, q = 'EX-HORMIGON-CORTE', 'EX-HORMIGON-VISTA'
    v.rayar(v.rect(E_LAT - ZAP[0], MURO_FUND - ZAP[1], E_LAT, MURO_FUND, hc), 'AR-CONC', 'AN-RAYADO-EX',
            ESC_HORMIGON)
    zz = v.zigzag((E_LAT, 700), (0, 700))
    v.rayar(v.polilinea([(0, MURO_FUND), (E_LAT, MURO_FUND)] + zz, hc, cerrada=True), 'AR-CONC', 'AN-RAYADO-EX',
            ESC_HORMIGON)
    v.prolongar((0, 700), (E_LAT, 700), q)
    zz = v.zigzag((0, z(3300)), (E_LAT, z(3300)))
    v.rayar(v.polilinea(zz + [(E_LAT, z(Z_SUP)), (0, z(Z_SUP))], hc, cerrada=True), 'AR-CONC', 'AN-RAYADO-EX',
            ESC_HORMIGON)
    v.prolongar((0, z(3300)), (E_LAT, z(3300)), q)
    v.rayar(v.rect(E_LAT, -LOSA, 1100, 0, hc), 'AR-CONC', 'AN-RAYADO-EX', ESC_HORMIGON)
    v.rayar(v.rect(E_LAT, -LOSA - BASE, 1100, -LOSA, 'EX-TERRENO'), 'EARTH', 'AN-RAYADO-EX', ESC_TERRENO)
    v.linea((-900, NTN), (0, NTN), 'EX-TERRENO')
    v.rayar(v.rect(-900, NTN - 150, 0, NTN, 'EX-TERRENO', lineweight=0), 'EARTH', 'AN-RAYADO-EX', ESC_TERRENO)

    def n(u):                      # NTT con X = u − 150
        return ntt(u - 150)
    v.linea((-CHAPA_OFF, z(Z_SUP - 50)), (-CHAPA_OFF, z(n(-CHAPA_OFF) - CORREA[1])), 'EX-CERRAMIENTO',
            lineweight=35)
    for zc in CORREAS_MURO_Z:
        v.rayar(v.rect(-CHAPA_OFF + 5, z(zc), -CHAPA_OFF + 55, z(zc + 75), 'EX-MADERA'), 'SOLID', 'AN-RAYADO-EX')
    u0, u1 = 150 - ALERO, 1100
    v.polilinea([(u0, z(n(u0))), (u1, z(n(u1)))], 'EX-CERRAMIENTO', lineweight=35)
    zz = v.zigzag((u1, z(n(u1) - CORREA[1])), (u1, z(n(u1) - PAQ_CUBIERTA)))
    v.polilinea([(0, z(n(0) - CORREA[1]))] + zz + [(0, z(n(0) - PAQ_CUBIERTA))], 'EX-MADERA', cerrada=True)
    v.prolongar((u1, z(n(u1) - CORREA[1])), (u1, z(n(u1) - PAQ_CUBIERTA)), q)
    return v


def det12_e(msp):
    """E — Tabique interior T1 a T4: corte del suplemento, 1:200 (vista del tabique)."""
    v = Vista(msp, _origen_det12(12000), 1, escala=200)
    v.polilinea([(0, 0), (0, Z_TAB), (X_SUP0, Z_TAB)], 'EX-HORMIGON-VISTA')
    v.linea((X_SUP0, Z_TAB), (ANCHO, Z_TAB), 'EX-HORMIGON-VISTA')
    v.polilinea([(X_SUP0, Z_TAB), (X_SUP1, Z_SUP), (ANCHO, Z_SUP)], 'EX-MADERA')
    v.linea((ANCHO, 0), (ANCHO, Z_SUP), 'EX-HORMIGON-VISTA')
    v.linea((-600, 0), (ANCHO + 600, 0), 'EX-HORMIGON-CORTE')
    return v


def det12_f(msp):
    """F — Dado de apoyo de L1 (vista del tabique), 1:20: parte existente (suplemento en rampa)."""
    v = Vista(msp, _origen_det12(40000), 1, escala=20)
    xl, xr, zb = 7100, 8700, 3400
    v.polilinea([(xl, tope_tabique(xl)), (X_SUP1, Z_SUP), (xr, Z_SUP)], 'EX-MADERA')
    q = 'EX-HORMIGON-VISTA'
    v.quiebre((xl, zb), (xr, zb), q)
    v.quiebre((xl, zb), (xl, tope_tabique(xl)), q)
    v.quiebre((xr, zb), (xr, Z_SUP), q)
    return v


def dibujar(doc):
    msp = doc.modelspace()
    planta(msp)
    corte_aa(msp)
    corte_bb(msp)
    vista_cc(msp)
    det12_b(msp)
    det12_c(msp)
    det12_e(msp)
    det12_f(msp)
