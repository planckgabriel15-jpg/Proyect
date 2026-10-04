# Fase 0: lectura del material, datos maestros y discrepancias

**Proyecto:** Sistema de distribución de fertilizantes a granel con transportadores Redler. AGD, Planta de Acopio Río Primero.
**Legajo:** Rev. E del 03/10/2026, 14 láminas A3.
**Fecha del informe:** 04/10/2026.
**Estado:** Fase 0 terminada. Espera aprobación para pasar a la Fase 1.

---

## 0. Material recibido y uso de cada fuente

| # | Archivo | Contenido verificado | Uso (jerarquía §3 del pedido) |
|---|---|---|---|
| 1 | `Planos_RevE_Redler_AGD.pdf` | 14 láminas A3 (PL-00 a ISO-13). Las leí todas, como texto y como imagen a 150 dpi. | **Fuente de verdad.** |
| 2 | `Planos_RevE_avance_10de14.pdf` | 10 láminas (PL-01 a DET-10), iguales a las páginas 2 a 11 del punto 1. La única diferencia está en CT-02: la referencia "dado de H° bajo la placa de L1" dice **(DET-07)** en el avance y **(DET-12)** en la Rev E. | Ninguno, porque está superado. Manda (DET-12). |
| 3 | `Codigo_planos_RevE.zip` | Código Python (matplotlib) que **generó** el PDF Rev E: `data.py`, `lib.py`, `s00…s13.py`, `spl01.py`, `sct02.py`, `scl03.py`, `iso.py` y 4 fotos. Lo copié a `fuentes/codigo_RevE/`. | Coordenadas exactas en m o mm con el mismo sistema X, s, Z del pedido. **Propongo usarlo en lugar de `modelo_galpon.json`, que no llegó** (pregunta P-03). |
| 4 | `RV1_Proyecto_FInal_Tercera_Entrega_1.docx` | Tercera entrega. **Es la versión anterior al recálculo**: Q = 62,21 t/h, v = 0,20 m/s, paleta 370×360 (ver D-13). | Solo para textos descriptivos que no traen números de cálculo. |
| 5 | Segunda entrega (Google Drive, "Proyecto Final_Segunda entrega", 05/07/2026) | Relevamiento, boxes y proceso. Trae el "Plano de implantación general" como imagen. | Solo contexto. Base de la propuesta IMP-01 (P-14). |
| — | `PLANOS_AGD-2026` (archivo CAD a modificar) | **No llegó.** | Pregunta P-01. |
| — | `modelo_galpon.json` | **No llegó.** | Lo reemplazo con el código del punto 3 (P-03). |
| — | Primera entrega | **No llegó.** No hace falta para las 14 láminas. | — |

**Convención de referencias.** "PL-01" quiere decir lámina PL-01 del PDF Rev E. "DET-07·B" quiere decir lámina DET-07, vista B. "`spl01.py:5`" quiere decir archivo y línea del código Rev E.

---

## 1. Tabla de datos maestros verificada contra la Rev E

Estados: ✔ = coincide con el PDF Rev E (y con el código). ✔c = no figura impreso en el PDF, pero está en el código que generó el PDF y es coherente con lo dibujado. ⚠ = hay una discrepancia o un faltante; ver el número indicado.

### 1.1 Niveles (m)

| Nivel | Valor §9 | Rev E (lámina·vista) | Estado |
|---|---|---|---|
| NPT interior | ±0,00 | CT-02, CL-03, DET-12·A/B | ✔ |
| NTN exterior | −0,20 | CL-03 (tabla), DET-09·D, DET-10·A, DET-11·A | ✔ |
| Tabique de H° | +3,00 | CT-02, DET-12·A/B/E | ✔ |
| Tope del suplemento de machimbre | +3,90 | CT-02, DET-07·B, DET-12 | ✔ |
| Cara superior de la placa de apoyo | +3,918 | CT-02 (tabla de niveles) | ✔ |
| Asiento (fijo) / PTFE + inox (libre) | +3,923 | CT-02 (tabla de niveles) | ✔ |
| Cara inferior / superior del tubo | +3,941 / +4,241 | CT-02, DET-04·A, DET-06·A, DET-07·B | ✔ |
| Cara inferior del conducto (silletas UPN 100) | +4,341 | CT-02, DET-04·A, DET-07·B | ✔ |
| Divisor trabajo / retorno | +4,745 | CT-02 (tabla) | ✔ |
| Cara superior del conducto | +5,151 | CT-02, CL-03, DET-04·A, DET-05·B/D, DET-08·A/C | ✔ |
| Ménsula de pasarela | +3,941 a +4,021 | CT-02 (tabla), DET-06·A, DET-07·B | ✔ |
| NPP de pasarelas y plataforma | +4,05 | CT-02, CL-03, DET-05·D, DET-06·A, DET-08·A, DET-09·A/D | ✔ |
| Pasamanos | +5,15 (NPP + 1,10) | CT-02 (tabla), DET-09·A | ✔ |
| Travesaño | NPP + 0,50 | CT-02·Det.1 (ítem 10), DET-09·A/B | ✔ |
| NTT oeste / cumbrera (X = 11,35) / este | +5,60 / +6,55 / +5,75 | CT-02, DET-12·A/C | ✔ |
| Cara inferior de la cubierta | NTT − 0,35 | No está impresa. `sct02.py:15` la usa para los gálibos 1,92 y 1,96. | ✔c (ver D-11) |
| Cara inferior de la viga longitudinal de madera | +5,76 | DET-12·A | ✔ (sección de la viga: ver D-10) |
| Eje de la rueda motriz del cabezal | **+4,731** *(no está en §9)* | DET-05·B, DET-08·C | ✔ (lo agrego) |
| Elevador: plataforma de cabeza / salida del desviador / descarga / eje de rueda de cabeza / tope de la cabeza | +8,68 / +8,78 / +9,38 / +9,88 / +10,33 | CL-03 (tabla), DET-10·A | ✔ |
| Elevador: eje de la rueda de bota | **−2,85** *(no está impreso)* | Sale de 9,88 − 12,73 (DET-10·A, "12,73 entre ejes"). | ✔c (derivado) |
| Elevador: base y tope de la bota / tope del cuerpo | −3,30 y −2,30 / +9,60 | `s10.py:30-40` | ✔c |
| Recepción: reja / boca de la tolva / banda / boca de la bota / fondo de la bota / piso de la fosa | −0,20 / −1,90 / −2,20 / −2,75 / −3,30 / −3,40 | CL-03 (tabla), DET-10·A, DET-11·A | ✔ |
| Extremo inferior del chute (sobre la junta flexible) | +5,40 | No está impreso. `s08.py:64-67` y `s10.py:46`. | ✔c (ver D-09) |
| Descanso de la escalera exterior | +1,925 | Sale de −0,20 + 12 × 0,177 = +1,924 (DET-09·D). | ⚠ D-03 |

### 1.2 Planta (m)

| Dato | Valor §9 | Rev E | Estado |
|---|---|---|---|
| Ancho interior | 22,70 | PL-01, CT-02, DET-12·A/E | ✔ |
| Muros laterales de H° | e = 0,15 | DET-12·C | ✔ |
| Cabeceras | e = 0,35, ejes en s = 0 y 36,15. Exterior 36,50. | PL-01 (cadena 0,35 · … · 0,35 = 36,50), CL-03 | ✔ |
| Cadena transversal | 7,90 · 1,45 · 4,00 · 1,45 · 7,90 | PL-01, CT-02 | ✔ |
| Ejes L1 / C1 / elevador y cumbrera / C2 / L2 | 7,90 / 9,35 / 11,35 / 13,35 / 14,80 | PL-01, CT-02, DET-12·A/E | ✔ |
| Tabiques T4 / T3 / T2 / T1 | s = 9,075 / 13,575 / 18,075 / 27,075 (e = 0,20) | PL-01 (cadena 8,80 · 0,20 · 4,30 …), `data.py:23` | ✔ |
| Luces de norte a sur | 9,07 · 4,50 · 4,50 · 9,00 · 9,08 | CL-03 | ⚠ D-01: la primera y la última luz miden **9,075** las dos. |
| Tramo exterior hasta B2 | 1,825 (B2 en s = 37,975) | DET-08·A "1.825" | ⚠ D-02: DET-05·D dice "1.800 (tramo 0)". |
| Boxes 5 / 4 / 3 / 2 / 1 | s = 0,175–8,975 / 9,175–13,475 / 13,675–17,975 / 18,175–26,975 / 27,175–35,975 | PL-01, CL-03 | ✔ |
| Medidas de los boxes | grandes 8,80 × 22,70; chicos 4,30 × 22,70 | PL-01 | ✔ (la 2.ª entrega dice 4,4: obsoleto) |
| Perfil del suplemento | de X = 0 a 5,70 a +3,00; de 5,70 a 8,10 en rampa; de 8,10 a 22,70 a +3,90 | DET-12·E (5,70 · 2,40 · 14,60; 17,00), `sct02.py:19` | ✔ |
| Rueda motriz y cabezal | eje en s = 0,82; cabezal de 0,37 a 1,27 | DET-05·A "820" y "900"; DET-08·C "820" y "195" | ✔ |
| Cola | eje en s = 37,72; cola de 37,27 a 38,17 | DET-05·C "1.570", DET-08·A "1.570 (eje de cola)" | ✔ |
| L entre ejes de ruedas | 36,90 | CL-03, PL-00 | ✔ |
| Bridas | cada 2,50 desde s = 1,27 hasta 36,27, más tramo de ajuste de 1,00 hasta 37,27 (14 + 1 tramos) | DET-04·B "2.500", `data.py:28` | ✔ |
| Silletas UPN 100 × 800 | una junto a cada brida | DET-04 (ítem 12), CT-02 (ítem 16) | ✔ (ver D-16) |
| Compuertas 1 a 11 | s = 33,02 · 30,77 · 28,52 · 25,52 · 23,02 · 20,52 · 15,77 · 11,02 · 7,77 · 5,27 · 2,77 | PL-01 (1.01…2.11), `data.py:29` | ✔ (lado del actuador: P-09) |
| Designación de las compuertas | L1.01…L1.11 y L2.01…L2.11 | PL-01 rotula "1.01 … 2.11" | ✔ (paso a "L1.01" según §9) |
| Pasarelas | lado de la columna: L1 al este, L2 al oeste; de s = 1,45 a 36,15 | PL-01, `spl01.py:61-62` | ✔ (ver D-18) |
| Rejilla / borde UPN 80 / paso libre / holgura con la columna | 0,35–1,206 / 1,264 / 0,905 / 0,086 | DET-09·A ("paso libre 0,905", "86", "1.264", "1.450"), `s09.py:10` | ✔ (PL-01 rotula "0,90 m": ver D-12) |
| Bandejas portacables | lado opuesto a la pasarela, de 0,354 a 0,504 del eje, en +4,541 y +4,801 | DET-04·A ("200 (separación)", 150×60) | ✔c (ver D-13d) |
| Plataforma exterior | s = 36,325–38,60; X = 6,90–15,80; NPP +4,05 | PL-01, `spl01.py:6` | ✔ (postes y vigas: F-04) |
| Escalera exterior | s = 36,40–37,30; X = 0,50–6,90; 2 × 12 alzadas (h = 177, g = 250); descanso de 0,90 | DET-09·D (2,75 · 0,90 · 2,75; 4,25), `spl01.py:7` | ✔ (nivel del descanso: D-03) |
| Puertas en la cabecera sur | 0,84 × 1,89; L1 de X = 8,30 a 9,14; L2 simétrica respecto de 11,35 (13,56 a 14,40) | DET-08·B, `s08.py:110` | ✔ (ver D-17) |
| Pasamuro | 708 × 910 por línea, entre +4,291 y +5,201 | DET-08·B, `s08.py:104` | ✔ (ver D-16) |
| Elevador | eje en X = 11,35, s = 37,40; cuerpo de 730 (X) × 1.220 (s) | DET-10·C, `spl01.py:110` | ✔ |
| Bota / cabeza | 1,30 × 1,30 de −3,30 a −2,30 / 1,40 (s) × 0,90 (X) de +9,60 a +10,33 | `s10.py`, `scl03.py:97-98` | ✔c |
| Desviador | lado norte, s = 36,34–36,79, Z = +8,78 a +9,38 | DET-10·A, `s10.py:45` | ✔ (ISO-13 lo ubica en otro lado: D-08) |
| Boca de carga de cada línea | s = 36,87–37,27, sobre el conducto, 600 × 400 | DET-05·C "400", DET-08 (ítem 2) | ✔ |
| Fosa | interior X = 9,85–12,85, s = 36,70–41,20; muros y losa de 0,25 | DET-11·A/B/C (4,50 × 3,00 × 3,20; 0,75 · 2,00 · 2,25 = 5,00; 3,50) | ✔ |
| Tolva | 2.500 × 2.000 / 600 × 500, H = 1,70, V = 3,70 m³, s = 38,70–40,70 | DET-11, `s11.py:67` | ✔ |
| Vigas de la tolva | 2 × UPN 200, L = 3,30 | DET-11 (ítem 2) | ✔ |
| Banda | 800, tambores en s = 38,35 y 40,75 (2,40 entre ejes) | DET-11·A, `s11.py:12` | ✔ |
| Tope de ruedas | a 0,30 del borde (s = 41,75–41,95), 200 × 150 | DET-11 (ítem 20) | ⚠ D-07 (largo) |
| Escotilla / sumidero | 800 × 800 (s = 36,75–37,55, X = 12,00–12,80) / 400 × 800 × 200 (s = 40,75–41,15, X = 9,95–10,75) | DET-11 (ítems 17 y 18), `spl01.py:106-107` | ✔ |

### 1.3 Componentes principales

| Componente | Especificación §9 | Rev E | Estado |
|---|---|---|---|
| Conducto | chapa 4/3; interior 600 × 400 por compartimiento; exterior 608 × 810; tapa con L 30×30×3 y M8; brida de planchuela 40×6 + M12 c/150; rigidizador L 40×40×4 | DET-04·A/C y tabla (ítems 6, 7, 8 y 11) | ✔ (4 + 400 + 3 + 400 + 3 = 810 ✔) |
| Cadena y paletas | 2 × DIN 8167 M224, paso 200; ejes a ±241 (482); paleta 370 × 280 × 5 + L50 + K2; 380 paletas por lazo | DET-04·D, CT-02 (ítems 4 y 5), DET-05 (tabla) | ✔ (la paleta lleva **L 50×50×5** y K2 con **M10 cal. 8.8**: DET-04, ítems 1 y 5) |
| Ruedas y accionamiento | Z = 11, Dp 709,9; eje Ø140 AISI 1045; C ≥ 39,2 kN; 15 kW; i ≈ 225; n = 6,46 rpm; tensor M30 ±150 | DET-05 (tabla) | ✔ |
| Apoyo en tabique | placa 1.000×180×18; asiento de 5 (fijo) o PTFE 3 + inox 2 (libre); 2 placas base 1.000×80×18 con junta de 20; cartelas 400×200×12; 4 M16 8.8 hef 125; colisos 18×60; mortero ≤ 5 | DET-07·A/B/C y tabla | ✔ (la placa con agujeros redondos lleva **Ø18**; filete **a6 · 2 × 80**, E70XX; chapa de cierre del tubo **200×300×10**: DET-07) |
| Dado (solo L1) | H-21 1.000 × 200, cuña de hasta 263; 2 Ø10 c/200 epoxi hef 100; picado + puente de adherencia | DET-12·F ("263") | ✔ (3,90 − 3,6375 = 0,2625) |
| Compuerta | abertura 600 × 350; placa 700 × 450 × 6; carrera 400; actuador ≥ 1.000 N IP65 con 2 finales de carrera; guías L40×40×4 + planchuela 30×5 (sep. 650); sello de 5; divisor a 39°; piernas de 194 × 350 e = 3; chapa de anclaje 200×380×10; orejas e = 8 + M12; brazos de 350×220×6 a 35° | DET-06·A/B/C/D y tabla | ✔ (vuelo del brazo 220: DET-06·A) |
| Pasarela | UPC 80 c/1,00, vuelo 1.264; cartela 250×180×12 a6; rejilla 30×30×3; UPN 80; montante 50×50×3; pasamanos 40×40×2; travesaño 30×30×2; rodapié 150×3 | DET-09·A/B/E y tabla | ✔ (soldaduras de DET-09·E: a6 · 2 × 180 al tubo, a6 · 2 × 250 al UPC y a6 perimetral UPC–tubo) |
| Elevador | Martin C248-725; MF 24×8×11⅝ in (610×203×295), paso 12 in; 0,635 m/s; H = 12,13 (12,73 entre ejes); 5,5 kW; rueda de 13 dientes, Dp 635; vientos Ø12 (3) | DET-10 (tabla) | ✔ (≈ 90 cangilones; 17,1 L equivalentes; 19,1 rpm) |
| Recepción | tolva ST-37 e = 5 + L40×40×4 c/600; reja de planchuelas 10×50 c/90 (luz 80) + Ø16 c/500; marco L50×50×5 + M12 c/300; banda 800 con variador; faldones de 600 + lecho de 160; tolvín a 56°; tapa semilla de melón 6,4; escotilla 800×800 | DET-11 (tabla, ítems 1 a 20) | ✔ (además: tambores Ø300; rodillos de impacto Ø89 c/250; bastidor de UPN 140 con anclaje químico M12; bomba con descarga Ø50) |

### 1.4 Recálculo de control de la tabla de DET-05 y DET-10

Recalculé cada valor de las tablas de la Rev E con las fórmulas de RV1 y los datos vigentes. Todos coinciden.

| Magnitud | Rev E | Recálculo | Fórmula o dato |
|---|---|---|---|
| Dp (Z = 11, p = 200) | 709,9 | 709,9 mm | p / sen(180°/Z) |
| Lazo de cadena / paletas | 76,0 m / 380 | 76,03 m / 380 | 2 · 36,90 + π · Dp |
| Wm | 74,3 kg/m | 74,31 | Q / v |
| Wc | 61 kg/m | 59,08 × 1,03 = 60,9 | paleta de 6,14 kg / 0,2 + 20,4 + 8,0, con +3 % (mismo criterio que RV1) |
| F | 33,4 kN | 33.411 N | con L = 37 m (criterio de RV1) |
| n / T | 6,46 rpm / 11,86 kN·m | 6,46 / 11,86 | v·60/(π·Dp) y F·Dp/2 |
| d mínimo del eje | 134,0 → Ø140 | 134,0 mm | flexión y torsión, Ks 1,5, τadm 40 MPa |
| C de los rodamientos | ≥ 39,2 kN | 39,15 kN | L10h 20.000 h, p = 10/3, +15 % |
| P mecánica / instalada / i | 8,02 / 11,79 kW / ≈ 225 | 8,02 / 11,79 / 224,6 | η 0,85, FS 1,25 |
| Margen de la cadena | 1,72 | 1,72 | γ = 6,5, reparto 60/40 |
| Elevador: P teórica / instalada | 2,12 / 5,46 kW | 2,12 / 5,46 | Q·H/367 · 1,75/0,85 · 1,25 |
| Impacto sobre el brazo | 46,7 N | 46,7 N | Q·√(2gh), h = 0,35 |
| Tolva: V / ángulos | 3,70 m³ / 60,8° y 66,2° | 3,698 / 60,8° y 66,2° | tronco de pirámide |
| Escalera | 2h + g = 604; ≈ 35° | 604; 35,3° | 24 × 0,177 = 4,248 ≈ 4,25 |
| Gálibos (a 0,75 del eje) | 1,92 / 1,96 | 1,924 / 1,960 | NTT − 0,35 − 4,05 |

---

## 2. Cantidades contadas en la geometría (para las listas de materiales)

| Pieza | Por línea | Total | Cómo sale | Estado |
|---|---|---|---|---|
| Compuertas guillotina | 11 | 22 | `data.py:29` | ✔ (DET-06) |
| Brazos distribuidores | 22 | 44 | 2 por compuerta | ✔ (DET-06) |
| Actuadores / guías L40 | 11 / 22 | 22 / 44 | 1 y 2 por compuerta | ✔ (largo de la guía: F-06) |
| Tramos de conducto | 14 de 2.500 + 1 de 1.000 | 30 | s = 1,27 a 37,27 | ✔ |
| Uniones bridadas (juntas) | 16 (de 1,27 a 37,27) | 32 | 15 bridas en `BRIDAS` + la de la cola | ✔ |
| Silletas UPN 100 × 800 | 16 | 32 | una por junta | ⚠ D-16 (la de s = 36,27 cae en el muro) |
| Paletas | 380 | 760 | lazo / 0,200 | ✔ |
| Cadena M224 | 2 × 76,03 m | 4 ramales | — | ✔ |
| Placas de apoyo 1.000×180×18 | 6 (muro N, T4, T3, T2, T1, muro S) | 12 | apoyos sobre H° | ✔ |
| Anclajes M16 | 24 | 48 | 4 por placa | ✔ |
| Tramos de viga carrilera | 6 (5 interiores + tramo 0) | 12 | — | ✔ (largos de corte: F-02) |
| Placas base 1.000×80×18 | 12 (2 por tramo) | 24 | una por extremo | ⚠ F-03 (extremo sobre B2) |
| Cartelas 400×200×12 | 24 | 48 | 2 por extremo | ⚠ F-03 |
| Chapas de asiento (fijo) / PTFE + inox (libre) | 6 / 6 | 12 / 12 | un extremo fijo y uno libre por tramo. Fijo en muro S (tramo 1), T1…T4 y B2 (tramo 0). Libre en T1…T4, muro N y muro S (tramo 0). | ✔ DET-08 ítems 5, 7 y 15 (chapa sobre B2: F-03) |
| Dados de H° (solo L1) | 4 (T1 a T4) | 4 | la rampa existe en los 4 tabiques interiores; los muros de cabecera están a +3,90 | ✔ (contados en la geometría) |
| Ménsulas UPC 80 + cartela | ≈ 35 | ≈ 70 | c/1,00 de s = 1,45 a 36,15, salteando compuertas y a ±250 de cada tabique | ⚠ F-01 |
| Ventanas de inspección / graseras | "1 cada 2 tramos" / "c/2 m" | — | — | ⚠ F-05 |
| Cangilones | ≈ 90 | ≈ 90 | 27,45 m / 0,3048 | ✔ |

---

## 3. Discrepancias encontradas (no resueltas por mí)

| N.º | Tema | Fuentes en conflicto | Qué pasa | Propuesta (no la apliqué) |
|---|---|---|---|---|
| **D-01** | Luces de los extremos | CL-03 dice 9,08 (sur) y 9,07 (norte). §9 repite lo mismo. | Las dos luces miden **9,075** (0 → 9,075 y 27,075 → 36,15). La diferencia viene del redondeo. Con DIMDEC = 2, AutoCAD mostraría el mismo valor en las dos. | Acotar **9,075** en ambas (cota con 3 decimales). |
| **D-02** | Largo del tramo 0 | DET-05·D dice "1.800 (tramo 0)". DET-08·A dice "1.825" y RV1 dice "1,83". | 37,975 − 36,15 = 1,825. | Usar 1.825 en DET-05 (corregir la cota). |
| **D-03** | Nivel del descanso de la escalera | Sale +1,925 de DET-09·D. ISO-13 lo dibuja en +2,025 (`s13.py:93`) y CL-03 C-C en +2,13 (`scl03.py:198`). | Las vistas esquemáticas no coinciden con el detalle. | Usar +1,925 en todas. |
| **D-04** | Plataforma de cabeza del elevador | DET-10·B mide 2,60 en X (`s10.py:100`). CL-03 C-C mide 2,20 (`scl03.py:189`). | La medida en planta no está definida. | Usar 2,60 × 2,60, como en DET-10·A y DET-10·B. |
| **D-05** | Entorno del elevador en DET-10·A | DET-10·A dibuja la plataforma exterior entre s = 38,01 y 39,80 y un muro de fosa entre s = 38,55 y 38,80 (`s10.py:25,60`). | No coincide con PL-01 y DET-11: la plataforma va de 36,325 a 38,60 y la fosa de 36,45 a 41,45 (exterior). | Redibujar DET-10·A con la geometría de PL-01 y DET-11. |
| **D-06** | Postes de la plataforma exterior | CL-03 C-C los pone en X = 7,00 · 9,00 · 13,70 · 15,70. ISO-13 los pone en X = 7,00 · 11,35 · 15,70 y s = 37,0 · 38,5. | El poste de ISO-13 en (11,35; 38,5) **cae dentro de la fosa**. No hay sección ni designación de postes. | Ver F-04 y P-07. |
| **D-07** | Largo del tope de ruedas | PL-01 lo dibuja de X = 9,45 a 13,25 (3,80). DET-11·B lo dibuja de 9,60 a 13,10 (3,50). | — | Usar 3,50 (DET-11, que es el detalle). |
| **D-08** | Ubicación del desviador | DET-10·A: s = 36,34–36,79 (lado norte). ISO-13: s = 36,85–37,35, dentro de la proyección del cuerpo. | — | Usar DET-10 en todas las vistas. |
| **D-09** | Nivel del extremo del chute | CL-03 lo dibuja en +5,25. DET-08 y DET-10 en +5,40. | — | Usar +5,40. |
| **D-10** | Viga longitudinal de madera (existente) | Solo está acotada la cara inferior, +5,76. CL-03 la dibuja de 0,19 de alto, ISO-13 de 0,30 y CT-02 hasta NTT − 0,35. | No hay sección relevada. | Dibujar desde +5,76 hasta la cara inferior de la cubierta, sin acotar la sección. Reportar como faltante de relevamiento. |
| **D-11** | Espesor del paquete de cubierta | Los gálibos usan NTT − 0,35. CT-02 y DET-12 dibujan los cabios entre NTT − 0,05 y NTT − 0,30. | — | Dibujar el paquete NTT a NTT − 0,35, que es lo que da 1,92 y 1,96. |
| **D-12** | Paso libre de la pasarela | PL-01 rotula "paso libre 0,90 m". CT-02 y DET-09 dicen 0,905. | Es una diferencia de texto. | Usar 0,905. |
| **D-13** | **RV1 entregado contra Rev E** | RV1 (docx): Q 62,21; v 0,20; paleta 370×**360**; n 5,38; i ≈ 269; C ≥ 41,69; d ≥ 139,3; 369 paletas; F 37,57 kN; Wm 86,4; Wc 67; impacto 45,3 N; elevador 5,29 kW; vaciado en 185 s. **(d)** Las bandejas van "por debajo de la estructura de la pasarela", pero en Rev E (DET-04·A) van del lado opuesto. | El RV1 que recibí es anterior al recálculo y contradice la Rev E en todos los números. | Ningún texto con números va a salir de este RV1. Ver P-04. |
| **D-14** | Sensor de nivel en el RV1 | La lista de despiece del RV1 trae "Soporte de sensor de nivel, caño Ø42, 15 unidades". | No aparece en ninguna lámina Rev E. | No lo dibujo. |
| **D-15** | Orientación del corte B-B en el model space | §6.3 pide la zona B con coordenadas (s, Z), con s creciente hacia la derecha. | Las flechas B de PL-01 miran al **oeste**, y así CL-03 muestra el norte a la **derecha**. Con s creciente a la derecha la vista quedaría **espejada** respecto del PDF y del sentido de observación. | Zona B con **s creciente hacia la izquierda**: X_cad = X0 − s·1000. Ver P-06. |
| **D-16** | Silleta y tubo en la cabecera sur | La junta de s = 36,27 queda dentro del espesor del muro sur (35,975 a 36,325). | El hueco del pasamuro empieza en +4,291, a media altura de la silleta (4,241 a 4,341). No están definidos el plano del cerramiento ni el paso del tubo y la silleta a través de la chapa (por debajo de +4,291). | Dibujar como en DET-08 y reportar. Ver P-08. |
| **D-17** | Puerta y marco del pasamuro (L1) | El hueco termina en X = 8,254 y la puerta empieza en 8,30. | Si el marco L50×50×5 va **por fuera** del hueco de 708, llega a 8,304 y se superpone **4 mm** con el marco de la puerta. Si va por dentro, no hay conflicto. | Aclarar cómo se interpreta el "hueco 708". Ver P-08. |
| **D-18** | Fin de la pasarela | La pasarela llega al eje del muro sur (s = 36,15) y la plataforma empieza en la cara exterior (36,325). | Quedan 0,175 m en el vano de la puerta sin piso definido. | Dibujar como en el PDF y reportar. |
| **D-19** | Cruce de la viga B2 con el elevador (ya lo marcaste) | B2 IPN 200 en s = 37,975, de X = 6,90 a 15,80. Cuerpo del elevador de s = 36,79 a 38,01 y X = 10,985 a 11,715. | Hay superposición física. Tampoco está definido el hueco en la rejilla de la plataforma por donde pasa el cuerpo. | **No lo resuelvo.** Dibujo la plataforma como en el PDF. Ver P-05 (afecta DET-05, DET-08 y DET-10). |

---

## 4. Faltantes (no los voy a inventar ni acotar)

| N.º | Dato que falta | Dónde se necesita | Qué voy a dibujar |
|---|---|---|---|
| F-01 | Posición exacta (s) de cada ménsula UPC 80 y montante. Solo está la regla "c/1,00, fuera de compuertas, a ±250 del eje del tabique". | PL-01, DET-09·B/C, lista de materiales | Las ménsulas sin cotas de posición individuales, o con la regla que me confirmes (P-10). |
| F-02 | Largos de corte de los tubos 300×200×10 (luz menos junta) y su posición respecto de cada placa. | DET-07, lista de materiales | Solo las luces entre ejes de apoyo. |
| F-03 | Unión del tubo (tramo 0) con la viga B2 y apoyo fijo sobre B2. | DET-05, DET-08 | Igual que en el PDF, sin detalle. |
| F-04 | Plataforma exterior: postes (sección y posición), vigas además de B2, ménsulas al muro (DET-08, ítem 6), fundaciones y baranda perimetral. | PL-01, CL-03, DET-08, ISO-13 | Rejilla, B2 y el contorno según el PDF. Postes según P-07. |
| F-05 | Cantidad y posición de las ventanas de inspección ("1 cada 2 tramos") y de las graseras ("c/2 m"). | DET-04, lista de materiales | Solo la vista del tramo tipo, como en el PDF. |
| F-06 | Largo de las guías L40 de la compuerta y de la planchuela 30×5. Lado del actuador en cada compuerta. | DET-06, PL-01 | Ver P-09. |
| F-07 | Portones del muro oeste: ancho, alto y posición. El PDF los dibuja de 3,50 m en los boxes grandes y 2,58 m en los chicos, centrados (`spl01.py:35-38`), sin cotas. | PL-01 | Igual que en el PDF, sin acotar. |
| F-08 | Columnas en los muros perimetrales: 0,20 × 0,20 en cada línea de tabique y de C1/C2. Están dibujadas en PL-01 pero no se describen. | PL-01, DET-12 | Igual que en el PDF. |
| F-09 | Sección de la viga longitudinal de madera y de los cabios y correas (existente). | CT-02, DET-12 | Ver D-10 y D-11. |
| F-10 | Recorte del cerramiento para el paso del tubo y la silleta en la cabecera sur. | DET-08 | Ver D-16. |
| F-11 | Gálibo en la puerta: dintel en +5,94 con la cara inferior de la cubierta en +6,015 (X = 9,14). Quedan 75 mm. | DET-08 | Es solo dato; no hace falta acción. |

---

## 5. Normas: verificación de escalas, formato y texto

**Limitación.** Desde este entorno la red no deja abrir los textos de IRAM ni de ISO (sitios bloqueados por el proxy). Lo que sigue se apoya en resúmenes académicos encontrados en la búsqueda, no en el texto oficial. Recomiendo que alguien con acceso a la norma confirme la tabla de escalas.

### 5.1 IRAM 4505, escalas

Según las fuentes consultadas, la serie recomendada se forma con los valores **1 · 1,25 · 2 · 2,5 · 5 · 7,5** multiplicados por 10ⁿ. Algunas fuentes agregan 1:25, 1:30 y 1:40 "en casos especiales de construcción" y clasifican 1:75 y 1:125 en un grupo de preferencia secundaria.

Fuentes: [Studocu, "Norma IRAM 4505:2002"](https://www.studocu.com/es-ar/document/universidad-nacional-de-san-martin-argentina/sistemas-de-representacion-grafica/6-clase-1-norma-iram-45052002-sobre-escalas-en-dibujo-tecnico/159266775), [SlideShare, "Escalas lineales, norma IRAM 4505"](https://es.slideshare.net/gimenezprof/01-escalas-linealesnorma-iram-4505), [Scribd, "Normas IRAM escalas"](https://www.scribd.com/document/511672779/Normas-Iram-escalas), [Prof. C. Gordillo, "Norma IRAM 4505"](https://profcarlosgordillo.blogspot.com/2016/10/norma-iram-4505.html).

| Escala Rev E | Dónde | ¿Normalizada? | Propuesta | Encaje en A3 |
|---|---|---|---|---|
| 1:75 | CT-02 | Sí (serie 7,5) | Se mantiene | — |
| 1:125 | PL-01, CL-03 | Sí (serie 1,25) | Se mantiene | — |
| **1:15** | DET-10·D (cangilón) | No | **1:10** | 295 × 203 queda en 30 × 20 mm: entra |
| **1:30** | DET-11·A | Dudosa (solo "casos especiales") | **1:25**, o mantener 1:30 si aceptás el caso especial | A 1:25 ocupa unos 225 × 175 mm: hay que reacomodar las tablas (P-11) |
| **1:150** | CL-03, vista C-C | No | **1:125** (igual que B-B) | Unos 124 × 112 mm: entra si muevo la tabla de equipos |
| **1:150** | DET-12·E | No | **1:200** | 113 mm de ancho. A 1:125 no entra en el espacio disponible (182 mm). |
| **1:300** | PL-00 (esquema) | No | **1:250** | Unos 170 mm de ancho: entra |

### 5.2 Formato, rótulo, líneas y texto

- **IRAM 4504.** Margen de encarpetado de 25 mm a la izquierda y 10 mm en los otros lados. Coincide con §8.5. Fuente: [educ.ar, "Norma IRAM"](https://www.educ.ar/app/files/repositorio/html/02/66/703a89ba-7a06-11e1-8133-ed15e3c494af/index/norma-iram.htm).
- **IRAM 4508.** Las fuentes citan un rótulo de **175 mm** de ancho. §8.5 permite hasta 185 mm. Propongo 175 mm, que cumple las dos cosas.
- **IRAM 4502 / ISO 128.** Los espesores de §8.1 (0,13 · 0,18 · 0,25 · 0,35 · 0,50 · 0,70) están todos en la serie normalizada. ✔
- **IRAM 4503 / ISO 3098.** La serie de alturas es 1,8 · 2,5 · 3,5 · 5 · 7 · 10 · 14 · 20 mm. **2,0 mm no está en la serie.** Para tablas densas propongo **1,8 mm** como mínimo absoluto, o directamente no bajar de 2,5 (P-12).
- **Cotas en metros con 3 decimales** (1,825; 0,905; 9,075; 3,918…). IRAM-OBRA con DIMDEC = 2 las redondearía. Propongo una variante **IRAM-OBRA-3** (DIMDEC = 3) para esos casos. Es un estilo más dentro de la plantilla y no cambia ningún valor.
- **Sin separador de miles.** La Rev E escribe "1.264", "2.500" y "1.000". Según §11.1, en AutoCAD van a quedar "1264", "2500" y "1000", también en los textos y las referencias.

---

## 6. Decisiones de método que necesito confirmar

1. **Conexión con AutoCAD.** En este entorno (Linux en la nube) **no hay AutoCAD** ni conversor a DWG. No puedo ejecutar comandos de AutoCAD ni simular haberlo hecho. Propongo esto:
   - Genero con `ezdxf` (ya instalado y probado) un **DXF R2018** con todo lo de §6 a §8: capas, tipos de línea, estilos, bloques con atributos, cotas asociativas, rayados, multileaders, tablas y 14 layouts con ventanas bloqueadas.
   - Genero el **CTB** `PF-IRAM-MONO.ctb`.
   - Genero un **script AutoLISP** `PF-POST.lsp` para lo que solo se puede hacer dentro de AutoCAD:
     - escalas anotativas por ventana;
     - configuración de página (`DWG To PDF.pc3`, CTB);
     - fields del rótulo;
     - FIELDEVAL, AUDIT, PURGE y OVERKILL;
     - IMAGEATTACH de las fotos;
     - sólidos 3D de ISO-13;
     - SAVEAS DWG y DWT;
     - PUBLISH a PDF;
     - ETRANSMIT;
     - el verificador de superposiciones de §12.1 en AutoLISP/ActiveX, que se corre en AutoCAD.
   - **Vos** abrís el DXF, cargás `PF-POST.lsp` y lo corrés. Si me pasás el PDF y el reporte, los reviso.
   - En paralelo, acá corro una verificación equivalente sobre el DXF, renderizo cada layout a PNG/PDF y te mando las capturas de cada fase.
2. **Orientación de la planta.** Con el norte arriba (§6.3), la planta mide unos 42 m (s de −0,175 a 41,95). A 1:125 son 336 mm verticales y **no entra en A3** (277 mm útiles). Propongo **ventana girada 90°** (VIEWTWIST) en PL-01, PL-00 y DET-11·B. Así el model space queda con el norte arriba y la lámina queda igual que el PDF, con el norte a la izquierda. Los textos y cotas del model space se rotan para leerse en papel.
3. **Detalle 1 de CT-02 y detalles en general.** Como las capas son fijas (no puedo crear capas por nivel de detalle), propongo dibujar cada vista de detalle **en su propia subzona** del model space a 1:1. Por ejemplo, A1 para el Detalle 1 de CT-02. Así una ventana de 1:75 no hereda el detalle fino de 1:25 ni sus rayados.
4. **Nombres de zonas.** Las zonas D1…D9 de §6.3 se confunden con las llamadas "D4…D11" de las láminas. Propongo nombrarlas **Z-DET04 … Z-DET12**, con sus UCS **UCS-DET04 …**. La zona **R** queda para las vistas de DET-11 y el entorno de la recepción.

---

## 7. Preguntas pendientes (necesito respuesta para la Fase 1)

| N.º | Pregunta |
|---|---|
| **P-01** | El archivo **`PLANOS_AGD-2026`** no llegó. ¿Lo subís (DWG, o mejor DXF 2018)? ¿Tiene algo propio que haya que conservar, como capas, bloques o dibujos? ¿O lo armo desde cero como `PF-REDLER-AGD_RevE.dwg`? |
| **P-02** | ¿Aprobás el método **DXF + `PF-POST.lsp`** que corrés vos en AutoCAD (§6.1)? |
| **P-03** | ¿Acepto el **código Python de la Rev E** (`fuentes/codigo_RevE/`) como fuente de coordenadas en lugar de `modelo_galpon.json`? |
| **P-04** | ¿Hay una **RV1 posterior al recálculo**, con 64,20 t/h y 0,24 m/s? La que recibí es la anterior (D-13). Si no la hay, los textos técnicos salen de las tablas de la Rev E. |
| **P-05** | **Cruce B2 – elevador** (D-19): ¿cómo lo resolvés? Opciones: cortar B2 y apoyarla sobre dos postes a cada lado del cuerpo, moverla en s, o apoyar el tramo 0 de otra forma. También necesito el **hueco en la rejilla** de la plataforma para el cuerpo del elevador. |
| **P-06** | ¿Aprobás la zona B con **s creciente hacia la izquierda** (D-15)? ¿Y la **ventana girada 90°** de las plantas (§6.2)? |
| **P-07** | **Postes de la plataforma** (D-06 y F-04): ¿qué sección y en qué posiciones van? Si no hay dato, los dibujo como en CL-03 C-C (X = 7,00 · 9,00 · 13,70 · 15,70), sin acotar. |
| **P-08** | **Cabecera sur** (D-16 y D-17): ¿el hueco de 708 × 910 es el vano libre dentro del marco L50, o el corte de la chapa con el marco por fuera? ¿Cómo pasan el tubo y la silleta de s = 36,27 a través del cerramiento? |
| **P-09** | **Lado del actuador** de cada compuerta. Propongo **hacia el norte en las 22**: hay 1,50 a 2,25 m libres hasta la brida norte, y las compuertas 3 y 8 están a solo 0,25 m de la brida sur. ¿Y el largo de las guías L40? |
| **P-10** | **Ménsulas** (F-01): ¿qué regla de posición uso? Por ejemplo: c/1,00 desde s = 1,50, corriendo a ±0,25 del eje de cada tabique y a más de X m de cada compuerta. |
| **P-11** | **Escalas** (§5.1): ¿aprobás 1:15 → 1:10, 1:30 → 1:25 (o mantener 1:30), C-C 1:150 → 1:125, DET-12·E 1:150 → 1:200 y PL-00 1:300 → 1:250? |
| **P-12** | **Texto mínimo** en tablas densas: ¿1,8 mm (serie ISO 3098) o 2,5 mm siempre? |
| **P-13** | **D-01 a D-12**: ¿aplico las propuestas de la tabla del punto 3 (9,075; 1.825; +1,925; 2,60; DET-10·A redibujado; 3,50; desviador según DET-10; +5,40; 0,905; paquete de cubierta de 0,35)? |
| **P-14** | **IMP-01** (opcional): la segunda entrega trae el "Plano de implantación general" como imagen, sin cotas en el texto. ¿Lo agrego como lámina IMP-01? Opciones: (a) la imagen insertada con rótulo, o (b) redibujado, solo si hay cotas del predio. Cualquiera de las dos pasa el legajo a "n de 15". |
