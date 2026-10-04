# Fase 2: galpón existente en el espacio modelo (proyecto VJN001)

**Estado:** terminada. Espera tu aprobación para pasar a la Fase 3 (instalación nueva).
**Generador:** `cad/build_fase2.py`, que usa `cad/pf/galpon.py`.
**Archivo:** `dwg/PLANOS_AGD-2026.dxf`. Contiene la plantilla aprobada, las zonas y el galpón existente: 379 objetos, ninguno en la capa 0, auditoría de ezdxf sin errores.

## 1. Qué se dibujó, por zona (1:1, mm, coordenadas reales)

| Zona | Vista | Lámina | Contenido existente dibujado |
|---|---|---|---|
| P | Planta general | PL-01, PL-00 | <ul><li>Cabeceras de 0,35 y muros laterales de 0,15, cortados con relleno gris.</li><li>Muro oeste interrumpido por los 5 portones (uno por box).</li><li>Tabiques T1 a T4 de 0,20. El tramo de X = 0 a 5,70, sin suplemento, va solo con contorno, como en el PDF.</li><li>24 columnas de 0,20 × 0,20 (C1, C2 y columnas de muro en cada línea de apoyo).</li><li>Ejes de los apoyos (s = 0 · 9,075 · 13,575 · 18,075 · 27,075 · 36,15), de C1, C2 y de la cumbrera (X = 11,35).</li></ul> |
| A | Corte A-A, s = 26,85, mirando al norte | CT-02 (1:75) y DET-12·A (1:100, misma geometría) | <ul><li>Losa de 0,15 y base de 0,15.</li><li>Muros laterales cortados hasta −0,35, con zapata de 0,45 × 0,15.</li><li>Cerramiento de chapa con correas de pared en +4,30 y +5,00.</li><li>Terreno a −0,20.</li><li>Tabique T2 en vista: H° hasta +3,00 y suplemento en rampa de 5,70 a 8,10, con tablas cada 0,30.</li><li>Columnas C1 y C2 hasta +5,76.</li><li>Viga longitudinal de madera, cortada.</li><li>Cubierta de chapa con correas de 120 × 50 cortadas y cabios hasta NTT − 0,35 (5,60 / 6,55 / 5,75).</li></ul> |
| B | Corte B-B quebrado, mirando al oeste | CL-03 (1:125) | <ul><li>Cabeceras cortadas con su chapa hasta la cubierta.</li><li>Tabiques cortados en X = 7,90: tope +3,825 sobre la rampa, tablas del suplemento y fundación corrida de 0,90 × 0,30.</li><li>Losa y base entre apoyos.</li><li>Cubierta cortada en el plano de L1.</li><li>Terreno exterior en el plano X = 11,35, interrumpido donde va la fosa.</li></ul> |
| C | Vista C-C desde el exterior | CL-03 | <ul><li>Fachada de la cabecera sur: H° hasta +3,90 y frontón de chapa.</li><li>Borde de la cubierta.</li><li>Columnas visibles sobre +3,90.</li><li>Terreno a −0,20.</li></ul> |
| DET12 | B — Tabique H° + machimbre | DET-12 (1:25) | <ul><li>Fundación corrida de 0,90 × 0,30, losa y base a cada lado.</li><li>Tabique con interrupción normalizada entre +0,60 y +2,70.</li><li>Suplemento con 2 tablas de 25 y núcleo de H°.</li><li>Junta en +3,00.</li><li>Armadura c/0,20.</li></ul> |
| DET12 | C — Muro perimetral | DET-12 (1:50) | <ul><li>Zapata de 0,45 × 0,15 y muro de 0,15 con interrupción entre +0,70 y +3,30.</li><li>Losa, base y terreno.</li><li>Chapa, correas del cerramiento, cubierta y cabio.</li></ul> |
| DET12 | E — Corte del suplemento | DET-12 (1:200, escala aprobada) | <ul><li>Tabique en vista: 0 a 22,70, H° hasta +3,00, rampa de 5,70 a 8,10 y suplemento hasta +3,90.</li></ul> |
| DET12 | F — Zona del dado de L1 | DET-12 (1:20) | <ul><li>Perfil existente del suplemento en rampa (de X = 7,10 a 8,70), con líneas de quiebre.</li><li>El dado es nuevo y va en la Fase 3.</li></ul> |

Las fotos de DET-12·D van en el espacio papel del layout DET-12 (Fase 4), con IMAGEATTACH de las 4 fotos de `fuentes/codigo_RevE/img/`.

## 2. Criterios de representación aplicados

- **Existente:** capas EX-* en gris (ACI 8, impresión al 60 %). Rayados en AN-RAYADO-EX (ACI 9, al 50 %).
- **Rayados:**
  - H° cortado con AR-CONC; relleno y base con EARTH; madera cortada con líneas a 0° (o a 45° en las tablas del suplemento);
  - elementos de menos de 2 mm en papel con relleno lleno: muros en planta, correas, tablas a 1:125;
  - la escala de cada rayado se ajustó a la ventana de su lámina;
  - todos los rayados son **asociativos** a su contorno y están detrás de los contornos (draworder).
- **Interrupciones:** con línea de quiebre normalizada (zigzag, ISO 128-20). La línea forma parte del contorno del rayado y se prolonga 2 mm.
- **Sin superposiciones:**
  - en vista, el tabique se dibuja sin las aristas que coinciden con la losa y los muros;
  - las líneas del tabique se interrumpen detrás de las columnas;
  - el tramo sin suplemento no repite la arista que comparte con el resto.
- **OVERKILL (Fase 6):** se va a correr sin "combinar objetos colineales que se superponen parcialmente". Así no se rompe la asociatividad de los rayados donde dos elementos distintos (por ejemplo, losa y muro) comparten un borde.

## 3. Discrepancias nuevas del PDF Rev E (no las resolví: necesito tu decisión)

| N.º | Tema | Qué dice cada fuente | Qué dibujé | Pregunta |
|---|---|---|---|---|
| **D-20** | Columnas "más allá" en el corte B-B | Las flechas de B en PL-01 miran al **oeste**, y CL-03 muestra el norte a la derecha, que es coherente con mirar al oeste. Pero CL-03 dibuja "columnas existentes (más allá)" y la viga de madera de +5,76 en cada línea de apoyo, y esos son elementos de la línea C1 (X = 9,35), que queda **detrás** del plano X = 7,90, del lado del observador. Mirando al oeste, lo que se ve más allá son las columnas del muro oeste (X = −0,075). Su altura y la fachada interior del muro oeste, con los portones, no están definidas. | No dibujé columnas ni viga "más allá" en B-B. | ¿Qué hago? **(a)** Dibujar las columnas del muro oeste hasta la cubierta, sin portones. **(b)** Dejar B-B sin elementos "más allá". **(c)** Dibujar C1 y la viga como en el PDF, aunque no se vean. Recomiendo la (b), porque es la única que no muestra algo indefinido ni algo que no se ve. |
| D-21 | Zapata del muro perimetral | CT-02: 0,45 centrada (0,15 hacia adentro y 0,15 hacia afuera). DET-12·C: 0,45 al ras de la cara interior y 0,30 hacia afuera. | Usé DET-12·C en las dos vistas, porque es el detalle. | ¿OK? |
| D-22 | Chapa del cerramiento lateral | CT-02: sobre el eje del muro. DET-12·C: 20 mm por fuera de la cara exterior, con correas de pared de 50 × 75 en +4,30 y +5,00. | Usé DET-12·C en las dos vistas. | ¿OK? |
| D-23 | Alero de la cubierta | CT-02 y DET-12·A: 0,30 desde la cara interior (0,15 fuera del muro). DET-12·C: unos 0,55. Ninguno está acotado. | Usé 0,30 en todas las vistas, sin cota. | ¿OK? |
| F-12 | Fundación de las cabeceras | No está definida. CL-03 dibuja el muro de 0,35 hasta −0,40, sin zapata. | Igual que en el PDF, sin acotar. | Si tenés el dato, pasámelo. |

## 4. Pregunta pendiente (antes de DET-05, DET-08 y DET-10): cruce B2 × elevador

Sigue abierta: la planteé en el informe de la Fase 1 con las opciones A, B y C, y recomiendo la A. **No afecta a la Fase 3** salvo en la plataforma exterior, que dejo para el final de esa fase.

## 5. Conexión con AutoCAD

Los archivos de "Design & Draft" que mandaste (`check_autocad.py`) se conectan a un AutoCAD abierto en la misma computadora Windows. Esta sesión corre en un servidor Linux en la nube y no llega a tu PC: el script devuelve `NO_PYWIN32`, porque pywin32 solo existe para Windows. Para dibujar directo en AutoCAD, la sesión tiene que correr en tu computadora: desde la app Claude Desktop, o con `claude remote-control` en la carpeta del DWG. Mientras tanto, el DXF se abre directamente en AutoCAD.
