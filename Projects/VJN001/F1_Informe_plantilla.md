# Fase 1: plantilla PF-IRAM-A3 (proyecto VJN001)

**Estado:** terminada. Espera tu aprobación para pasar a la Fase 2 (galpón existente).
**Generador:** `cad/build_fase1.py`. Todo se regenera con `python3 cad/build_fase1.py`.

## 1. Archivos entregados (`Projects/VJN001/`)

| Archivo | Qué es |
|---|---|
| `dwg/PF-IRAM-A3.dxf` | Plantilla. Trae variables, tipos de línea, 43 capas, 3 estilos de texto, 3 de cota, 2 de multileader, bloques con atributos y el layout A3 vacío con su configuración de impresión. Se guarda como `.dwt` con `PF-GUARDAR-DWT`. |
| `dwg/PLANOS_AGD-2026.dxf` | Base del legajo. Es la plantilla más las zonas y los UCS del espacio modelo (§6.3), con el primer layout PL-00. Sobre este archivo se dibujan las fases 2 a 5. |
| `dwg/PF-IRAM-MONO.ctb` | Tabla de estilos de trazado monocroma: todo en negro, espesor del objeto. ACI 8 (existente) sale gris al 60 %, ACI 9 (rayado existente) gris al 50 % y ACI 10 (recorrido del producto) en rojo. |
| `dwg/PF-POST.lsp` | Post-proceso en AutoCAD: variables, estilo de tabla, configuración de página, campos del rótulo, informe de anotatividad y guardado del .dwt. |
| `F1_capas_estilos_bloques.md` | Listado completo de capas, tipos de línea, estilos, bloques y zonas, generado desde el DXF. |
| `png/F1_rotulo.png` | Rótulo IRAM 4508 completo (300 dpi), con la lista de materiales apilada encima. |
| `png/F1_lamina_A3_muestra.png` | Lámina A3 de muestra (PL-01): recuadro, marcas de centrado, rótulo y lista de materiales. |
| `png/F1_bloques_y_lineas.png` | Catálogo de los bloques de anotación y muestra de los tipos y espesores de línea. |

## 2. Qué contiene la plantilla

- **Unidades y variables (§6.2):**
  - el DXF ya guarda: INSUNITS 4, LUNITS 2, LUPREC 0, AUNITS 0, AUPREC 1, MEASUREMENT 1, LTSCALE 1, PSLTSCALE 1, CELTSCALE 1, DIMASSOC 2, DIMDSEP «,», LWDISPLAY 1 y PLINEGEN 1;
  - `PF-VARIABLES` fija en AutoCAD: MSLTSCALE 1, ANNOAUTOSCALE 4, FIELDEVAL 31 y HPASSOC 1 (el formato DXF no las guarda).
- **Capas:** las 36 de §8.2 con color, espesor, tipo de línea, impresión y descripción exactos. Además, 7 subcapas `3D-*` para ISO-13. La capa 0 queda solo para el contenido de los bloques.
- **Texto:** IRAM (anotativo), IRAM-N e IRAM-NEGRITA, todos con isocpeur.ttf, ancho 1,0 e inclinación 0°.
- **Cotas:**
  - IRAM-OBRA: m con 2 decimales, trazo oblicuo de 2 mm;
  - IRAM-OBRA-3: m con 3 decimales, para 9,075; 1,825; 0,905; 3,918;
  - IRAM-MEC: mm sin decimales, flecha llena de 2,5 mm;
  - las tres son anotativas, con texto de 2,5 sobre la línea, DIMEXO 1,5, DIMEXE 2, DIMGAP 1, DIMDLI 7 y coma decimal.
- **Multileaders:**
  - IRAM-REF: punto de 1 mm y quiebre horizontal de 3 mm;
  - IRAM-GLOBO: globo de Ø 6 mm.
- **Tabla:** IRAM-TABLA (la crea `PF-ESTILO-TABLA`, ver punto 4).
- **Bloques anotativos:**
  - NIVEL-CORTE, NIVEL-CORTE-IZQ y NIVEL-PLANTA;
  - CORTE, LLAMADA-DETALLE y TITULO-VISTA;
  - NORTE, EJE, FLUJO y PASO-RECORRIDO;
  - GLOBO, que es el contenido del multileader.
- **Rótulo y lista de materiales:**
  - ROTULO-A3 (no anotativo), de 175 × 89,5 mm, con la tabla de revisiones integrada;
  - LISTA-MATERIALES (encabezado) y LM-FILA (fila con 7 atributos), que crecen hacia arriba.
- **Formato A3 (IRAM 4504):**
  - recuadro con márgenes de 25 / 10 / 10 / 10 mm y espesor 0,70;
  - 4 marcas de centrado, desde el borde de la hoja hasta 5 mm dentro del recuadro (la de abajo coincide con el pliegue a A4 en x = 210);
  - configuración de página: DWG To PDF.pc3, papel ISO full bleed A3, 1:1, PF-IRAM-MONO.ctb, imprimir con espesores.
- **Zonas del espacio modelo (§6.3):**
  - rectángulos en AN-NOPLOT y UCS con nombre: UCS-P, UCS-A, UCS-B, UCS-C, UCS-R y UCS-DET04 a UCS-DET12;
  - la zona B tiene el eje X invertido, así que s crece hacia la izquierda, como aprobaste;
  - DET-11 se dibuja en la zona R.

## 3. Rótulo (IRAM 4508), campos

Encabezado · Sistema · TÍTULO (5 mm, hasta 2 líneas) · SUBTÍTULO (2,5 mm, hasta 2 líneas) · INTEGRANTES · ARCHIVO (`PLANOS_AGD-2026.dwg`) · DIBUJÓ (Gabriel Planckensteiner) · VERIFICÓ (Ing. R. Bonaiuti) · TUTOR EXTERNO (C. D. Solera (AGD)) · N.º PROYECTO (VJN001) · ESCALA(S) · FECHA (03/10/2026) · IMPRESIÓN · CÓDIGO (7 mm) · LÁMINA "n de 14" · REV. E · UNIDAD "m / mm — cotas en m salvo indicación" · símbolo del método ISO E (primer diedro) · tabla de revisiones con la fila "E — 03/10/2026 — Emisión tercera entrega — G. Planckensteiner".

`PF-CAMPOS` convierte en campos de AutoCAD dos de esos valores:
- CÓDIGO pasa a mostrar el nombre del layout (`%<\AcVar ctab>%`);
- IMPRESIÓN pasa a mostrar la fecha de trazado (`%<\AcVar PlotDate \f "dd/MM/yyyy">%`).

Todas las filas del rótulo cumplen la separación mínima de 1,5 mm entre textos. Por eso el rótulo es más alto que el del PDF (89,5 mm contra 40 mm).

## 4. Lo que hay que correr en AutoCAD

Esta sesión no tiene AutoCAD, así que **no probé `PF-POST.lsp`**. Verifiqué que los paréntesis cierren y que el DXF pase la auditoría de ezdxf sin errores. Los pasos son:

1. Copiar a una carpeta: `PLANOS_AGD-2026.dxf`, `PF-IRAM-A3.dxf`, `PF-IRAM-MONO.ctb` y `PF-POST.lsp`.
2. Abrir `PF-IRAM-A3.dxf`, cargar con APPLOAD `PF-POST.lsp` y escribir `PF-FASE1`. Después `PF-GUARDAR-DWT`, que guarda `PF-IRAM-A3.dwt`.
3. Abrir `PLANOS_AGD-2026.dxf`, escribir `PF-FASE1` y guardar como `PLANOS_AGD-2026.dwg` en la carpeta del DWG original. Antes conviene renombrar el original a `PLANOS_AGD-2026_anterior.dwg` si tiene algo que quieras conservar.
4. Mandarme el texto que imprime `PF-FASE1` (F2 en AutoCAD), sobre todo el informe de anotatividad.

Si trabajás desde una sesión local con AutoCAD abierto, esa sesión puede correr estos pasos por COM.

## 5. Decisiones que tomé (dentro de lo pedido)

| Tema | Qué hice | Por qué |
|---|---|---|
| Fuente | isocpeur.ttf en lugar de isocp.shx | §13 pide exportar el PDF "con fuentes como texto". Las fuentes SHX se exportan como geometría y las TrueType como texto. Las dos están en §8.3. |
| Nombres de tipos de línea | `ACAD_ISO02W100` y `ACAD_ISO04W100` | Son los nombres reales de acadiso.lin para ISO02W100 e ISO04W100. |
| Gris de lo existente | CTB: ACI 8 al 60 % y ACI 9 al 50 % | §11.1 pide lo existente en gris, y el rayado existente al 50 %. |
| Rojo del recorrido | Los bloques FLUJO y PASO-RECORRIDO dibujan en ACI 10 y el CTB imprime ese color en rojo | Con un CTB monocromo, el color 1 (rojo de la capa AN-FLUJO) se imprimiría negro, porque lo comparten muchas capas. |
| Texto mínimo | 2,5 mm en todo el legajo, también en las tablas | Respeta tu mínimo y la serie de ISO 3098 (2,0 mm no está en la serie). |
| Ancho del rótulo | 175 mm | Es el ancho que citan las fuentes de IRAM 4508 y cumple el máximo de 185 mm. |
| Lista de materiales | Bloques LISTA-MATERIALES y LM-FILA de 175 mm (Pos 9 · Cant 11 · Denominación 35 · Material/norma 29 · Dimensiones/designación 38 · Peso unit. (kg) 22 · Observaciones 31) | Así queda alineada con el rótulo y crece hacia arriba, como pide IRAM 4508. |
| Control de anchos de texto | Mido los textos con la fuente del render de control (DejaVu Sans), que es más ancha que ISOCPEUR | Si no hay superposición en el render, tampoco la hay en AutoCAD. |
| Bloques de piezas | COMPUERTA, SILLETA, PLACA-APOYO, etc. se crean en la Fase 3 | Son geometría de la instalación nueva, no de la plantilla. |

## 6. Pregunta pendiente: cruce B2 × elevador (antes de DET-05, DET-08 y DET-10)

Ya definiste que el tramo 0 del tubo apoya en la placa del muro sur (s = 36,15) y en la viga B2 (s = 37,975), con luz 1,825. El problema es este:

- La viga B2 de la plataforma exterior es un IPN 200 que corre de oeste a este en s = 37,975, de X = 6,90 a 15,80.
- El cuerpo del elevador (730 × 1.220) sube atravesando la plataforma y ocupa de s = 36,79 a 38,01 y de X = 10,985 a 11,715.
- Por lo tanto, **B2 pasa por adentro del cuerpo del elevador en 0,73 m**. Además, la rejilla de la plataforma necesita un hueco para el cuerpo, y el Rev E no lo define.

¿Cuál de estas soluciones dibujo?

| Opción | Qué cambia | Efecto sobre el resto |
|---|---|---|
| **A (recomendada)** | B2 se corta en dos tramos: X = 6,90–10,90 y 11,80–15,80. Cada extremo interior apoya en un poste nuevo, a cada lado del elevador. | El apoyo de L1 (X = 7,90) y el de L2 (X = 14,80) quedan igual. No cambia ninguna cota del Redler. |
| B | B2 se corre al sur, a s ≈ 38,10, fuera del elevador. | La luz del tramo 0 pasa de 1,825 a ≈ 1,95 m. Cambian DET-05, DET-07 y DET-08, y hay que verificar de nuevo el tubo. |
| C | Se corre el elevador. | Cambia toda la recepción: fosa, chutes y DET-10 y DET-11. |

Si elegís **A**, dibujo el hueco de la rejilla de 0,83 × 1,32 m (cuerpo + 50 mm por lado) con un marco L 50×50×5. Si preferís otra holgura, decime cuál.
