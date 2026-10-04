"""Datos de proyecto Rev E (texto RV1 + paleta 370x280 / v = 0,24 m/s)."""
# --- niveles (m)
TAB = 3.90          # tope tabique / machimbre
PLACA = 3.918       # cara sup. placa de apoyo 1000x180x18
ASIENTO = 3.923     # cara sup. chapa de asiento 5 mm (fijo) / PTFE 3 + inox 2 (libre)
TUBO_INF = 3.941    # cara inf. tubo 300x200x10 (sobre placa base 18)
TUBO_SUP = 4.241
COND_INF = 4.341    # cara inf. conducto (silletas UPN 100)
DIV = 4.745         # divisor trabajo / retorno (cara inf.)
COND_SUP = 5.151
MEN_INF = 3.941     # ménsula UPC 80 alineada con la cara inferior del tubo
MEN_SUP = 4.021
NPP = 4.05          # nivel piso pasarela (rejilla 30 sobre ménsula)
PASAM = 5.15        # pasamanos NPP + 1,10

# --- planta (m)
X_L1, X_L2 = 7.90, 14.80
X_C1, X_C2 = 9.35, 13.35
X_ELEV = 11.35
ANCHO = 22.70
LARGO = 36.50
# eje longitudinal s desde el eje del muro norte (m)
S_TAB = [0.0, 9.075, 13.575, 18.075, 27.075, 36.15]  # ejes de apoyo (muro N, T4, T3, T2, T1, muro S)
LUCES = [9.07, 4.50, 4.50, 9.00, 9.08]                 # de norte a sur
S_HEAD = 0.82        # eje rueda motriz (cabezal, punto fijo del conducto)
S_TAIL = 37.72       # eje rueda de cola (exterior, sobre plataforma)
S_B2 = 36.15 + 1.825 # viga B2 de la plataforma
BRIDAS = [1.27 + 2.5 * k for k in range(15)]          # 1.27 ... 36.27 ; tramo de ajuste 36.27-37.27
GATES = {  # numero: s (m)
    1: 33.02, 2: 30.77, 3: 28.52, 4: 25.52, 5: 23.02, 6: 20.52,
    7: 15.77, 8: 11.02, 9: 7.77, 10: 5.27, 11: 2.77}

# --- conducto y cadena (mm)
B_INT = 600; H_COMP = 400; T_FONDO = 4; T_LAT = 4; T_DIV = 3; T_TAPA = 3
B_EXT = 608; H_TOT = 810
X_CAD = 241          # eje de cada ramal desde el eje del conducto
DP = 709.9           # diámetro primitivo rueda Z = 11
PAL_B, PAL_H = 370, 280

# --- resultados de cálculo (Rev E)
Q = 64.20; V = 0.24; K = 0.43
WM = 74.30; WC = 61
F = 33412; F_KGF = 3406
P_MEC = 8.02; P_INST = 11.79; MOTOR = 15
N_EJE = 6.46; T_EJE = 11.86; D_EJE_REQ = 134.0; D_EJE = 140
C_ROD = 39.15
I_RED = 225
T_ROT_MIN = 13283; MARGEN_CAD = 1.72
N_PAL = 380; LAZO = 76.03
# elevador
Q_ELEV_MAX = 69.32; V_ELEV = 0.635; H_ELEV = 12.13; ENTRE_EJES_ELEV = 12.73
P_ELEV_T = 2.12; P_ELEV_I = 5.46; MOTOR_ELEV = 5.5
