# Fase 1: capas, estilos y bloques de la plantilla PF-IRAM-A3

Listado generado automáticamente desde `PF-IRAM-A3.dxf`.

## Capas

| Capa | Color | Espesor (mm) | Tipo de línea | Imprime | Contenido |
|---|---|---|---|---|---|
| G-MARCO | 7 | 0,70 | Continuous | Sí | Recuadro y marcas de centrado |
| G-ROTULO | 7 | 0,35 | Continuous | Sí | Rótulo, lista de materiales, tabla de revisiones |
| G-VENTANAS | 8 | 0,13 | Continuous | No | Viewports |
| G-EJES | 1 | 0,18 | ACAD_ISO04W100 | Sí | Ejes de líneas, columnas, tabiques y piezas |
| EX-HORMIGON-CORTE | 8 | 0,35 | Continuous | Sí | H° existente cortado |
| EX-HORMIGON-VISTA | 8 | 0,25 | Continuous | Sí | H° existente en vista |
| EX-MADERA | 32 | 0,25 | Continuous | Sí | Machimbre, cabios, correas y viga de madera |
| EX-CERRAMIENTO | 8 | 0,25 | Continuous | Sí | Chapa de muros y cubierta |
| EX-COLUMNAS | 8 | 0,35 | Continuous | Sí | Columnas existentes |
| EX-TERRENO | 8 | 0,18 | Continuous | Sí | Terreno natural y relleno |
| NU-REDLER-CONDUCTO | 5 | 0,50 | Continuous | Sí | Conducto, bridas, tapa y divisor |
| NU-REDLER-MECANICO | 4 | 0,35 | Continuous | Sí | Cabezal, cola, ruedas, ejes, cadena, paletas y motorreductor |
| NU-COMPUERTAS | 150 | 0,35 | Continuous | Sí | Placa guillotina, guías, pantalón, brazos y actuador |
| NU-ESTRUCT-CORTE | 1 | 0,50 | Continuous | Sí | Perfiles y chapas nuevas cortadas |
| NU-ESTRUCT-VISTA | 1 | 0,35 | Continuous | Sí | Perfiles y chapas nuevas en vista |
| NU-APOYOS | 1 | 0,35 | Continuous | Sí | Placas, asientos, PTFE, cartelas y dados |
| NU-PASARELA | 2 | 0,35 | Continuous | Sí | Ménsulas, rejilla, larguero y rodapié |
| NU-BARANDA | 2 | 0,25 | Continuous | Sí | Montantes, pasamanos y travesaños |
| NU-ESCALERA | 2 | 0,35 | Continuous | Sí | Escalera exterior y marinera |
| NU-PLATAFORMA | 2 | 0,35 | Continuous | Sí | Plataforma exterior, postes y vigas |
| NU-ELEVADOR | 1 | 0,50 | Continuous | Sí | Bota, cuerpo, cabeza, desviador y chutes |
| NU-RECEPCION | 6 | 0,50 | Continuous | Sí | Fosa, tolva, reja, banda, tapa y sumidero |
| NU-ELECTRICO | 3 | 0,25 | Continuous | Sí | Bandejas portacables y sensores |
| NU-BULONES-SOLD | 1 | 0,18 | Continuous | Sí | Bulones, anclajes y símbolos de soldadura |
| AN-OCULTO | 8 | 0,25 | ACAD_ISO02W100 | Sí | Aristas ocultas |
| AN-RAYADO-EX | 9 | 0,13 | Continuous | Sí | Rayados de elementos existentes |
| AN-RAYADO-NU | 1 | 0,13 | Continuous | Sí | Rayados de elementos nuevos |
| AN-COTAS | 3 | 0,18 | Continuous | Sí | Cotas |
| AN-NIVELES | 3 | 0,18 | Continuous | Sí | Símbolos de nivel |
| AN-REFERENCIAS | 3 | 0,18 | Continuous | Sí | Multileaders y globos |
| AN-TEXTOS | 7 | 0,25 | Continuous | Sí | Títulos de vista y notas técnicas |
| AN-CORTES-LLAMADAS | 1 | 0,18 | ACAD_ISO04W100 | Sí | Líneas de corte y llamadas de detalle (extremos 0,70) |
| AN-TABLAS | 7 | 0,25 | Continuous | Sí | Tablas y listas |
| AN-FLUJO | 1 | 0,35 | Continuous | Sí | Flechas y numeración del recorrido del producto |
| AN-IMAGENES | 7 | — | Continuous | Sí | Fotos del relevamiento |
| AN-NOPLOT | 8 | — | Continuous | No | Auxiliares, zonas y verificación |
| 3D-GALPON | 8 | 0,25 | Continuous | Sí | Sólidos ISO-13: galpón existente |
| 3D-REDLER | 5 | 0,25 | Continuous | Sí | Sólidos ISO-13: conductos, cabezales y colas |
| 3D-COMPUERTAS | 150 | 0,25 | Continuous | Sí | Sólidos ISO-13: compuertas y pantalones |
| 3D-ESTRUCT | 1 | 0,25 | Continuous | Sí | Sólidos ISO-13: viga carrilera y apoyos |
| 3D-PASARELA | 2 | 0,25 | Continuous | Sí | Sólidos ISO-13: pasarelas, plataforma y escalera |
| 3D-ELEVADOR | 1 | 0,25 | Continuous | Sí | Sólidos ISO-13: elevador, desviador y chutes |
| 3D-RECEPCION | 6 | 0,25 | Continuous | Sí | Sólidos ISO-13: fosa y tolva |

## Tipos de línea

| Nombre | Patrón (mm, a escala de papel) |
|---|---|
| ACAD_ISO02W100 | 12,0, -3,0 (ISO dash __ __ __ __ __ __ __ __ __ __ __ __ __) |
| ACAD_ISO04W100 | 24,0, -3,0, 0,0, -3,0 (ISO long-dash dot ____ . ____ . ____ . ____ . _) |

## Estilos de texto

| Estilo | Fuente | Ancho | Inclinación | Anotativo | Uso |
|---|---|---|---|---|---|
| IRAM | isocpeur.ttf | 1,0 | 0° | Sí | textos, cotas y referencias en el espacio modelo |
| IRAM-N | isocpeur.ttf | 1,0 | 0° | No | contenido de bloques y espacio papel |
| IRAM-NEGRITA | isocpeur.ttf (negrita) | 1,0 | 0° | No | encabezados de tabla, títulos de vista y del rótulo |

Alturas en papel: 2,5 (cotas, referencias, tablas) · 3,5 (títulos de vista) · 5 (título del rótulo) · 7 (código de lámina). Mínimo 2,5 mm en todo el legajo.

## Estilos de cota (anotativos)

| Estilo | Unidad mostrada | Decimales | Extremo | Texto | DIMEXO / DIMEXE / DIMGAP / DIMDLI |
|---|---|---|---|---|---|
| IRAM-OBRA | m (DIMLFAC 0,001) | 2 | trazo oblicuo 2 mm | 2,5 sobre la línea, alineado | 1,5 / 2 / 1 / 7 |
| IRAM-OBRA-3 | m (DIMLFAC 0,001) | 3 | trazo oblicuo 2 mm | ídem | ídem |
| IRAM-MEC | mm | 0 | flecha cerrada llena 2,5 mm | ídem | ídem |

Separador decimal: coma (DIMDSEP). Ángulos en grados enteros. Texto que no entra: afuera con leader (DIMATFIT 3, DIMTMOVE 1).

## Estilos de multileader (anotativos)

| Estilo | Contenido | Texto | Extremo | Quiebre |
|---|---|---|---|---|
| IRAM-REF | MTEXT | IRAM 2,5 | punto de 1 mm | horizontal de 3 mm |
| IRAM-GLOBO | bloque GLOBO (Ø 6 con número) | 2,5 | punto de 1 mm | sin quiebre |

## Estilo de tabla

IRAM-TABLA: texto 2,5 mm (IRAM-N), encabezado 2,5 mm en negrita (IRAM-NEGRITA), márgenes de celda 1 mm, borde exterior 0,35 e interiores 0,18. Lo crea `PF-ESTILO-TABLA` en AutoCAD porque el DXF no puede definir estilos de tabla.

## Rayados (IRAM 4502-50)

| Material | Patrón | Capa |
|---|---|---|
| Hormigón | AR-CONC | AN-RAYADO-EX / AN-RAYADO-NU |
| Acero cortado | ANSI31, 2 mm en papel; relleno negro si la chapa mide menos de 2 mm en papel | AN-RAYADO-NU |
| Madera | AR-RSHKE | AN-RAYADO-EX |
| Terreno | EARTH | AN-RAYADO-EX |
| Rejilla | NET | AN-RAYADO-NU |
| Material a granel | AR-SAND | AN-RAYADO-NU |

## Bloques

| Bloque | Anotativo | Atributos |
|---|---|---|
| GLOBO | No | N |
| NIVEL-CORTE | Sí | COTA, DESC |
| NIVEL-CORTE-IZQ | Sí | COTA, DESC |
| NIVEL-PLANTA | Sí | COTA |
| CORTE | Sí | LETRA, LAMINA |
| LLAMADA-DETALLE | Sí | DETALLE, LAMINA |
| TITULO-VISTA | Sí | LETRA, TITULO, ESCALA |
| NORTE | Sí | N |
| EJE | Sí | EJE |
| FLUJO | Sí | — |
| PASO-RECORRIDO | Sí | N |
| ROTULO-A3 | No | CODIGO, LAMINA, REV, UNIDAD, UNIDAD_NOTA, ESCALA, FECHA, IMPRESION, DIBUJO, VERIFICO, TUTOR, NPROYECTO, INTEGRANTES, ARCHIVO, TITULO, SUBTITULO, ENCABEZADO, SISTEMA, REV1_REV, REV1_FECHA, REV1_DESCRIPCION, REV1_DIBUJO |
| LISTA-MATERIALES | No | — |
| LM-FILA | No | POS, CANT, DENOM, MAT, DIM, PESO, OBS |

## Zonas del espacio modelo (§6.3)

| Zona | UCS | Origen (mm) | Eje X | Contenido |
|---|---|---|---|---|
| P | UCS-P | (0, 0) | (1, 0) | Planta general (X, −s) |
| A | UCS-A | (0, 60000) | (1, 0) | Corte A-A, s = 26,85, mirando al norte (X, Z) |
| B | UCS-B | (110000, 60000) | (-1, 0) | Corte B-B quebrado, mirando al oeste (s creciente hacia la izquierda, Z) |
| C | UCS-C | (120000, 60000) | (1, 0) | Vista C-C desde el exterior (X, Z) |
| R | UCS-R | (120000, 0) | (1, 0) | Recepción: vistas de DET-11 |
| DET04 | UCS-DET04 | (0, 120000) | (1, 0) | Detalles de DET-04 |
| DET05 | UCS-DET05 | (0, 150000) | (1, 0) | Detalles de DET-05 |
| DET06 | UCS-DET06 | (0, 180000) | (1, 0) | Detalles de DET-06 |
| DET07 | UCS-DET07 | (0, 210000) | (1, 0) | Detalles de DET-07 |
| DET08 | UCS-DET08 | (0, 240000) | (1, 0) | Detalles de DET-08 |
| DET09 | UCS-DET09 | (0, 270000) | (1, 0) | Detalles de DET-09 |
| DET10 | UCS-DET10 | (0, 300000) | (1, 0) | Detalles de DET-10 |
| DET12 | UCS-DET12 | (0, 360000) | (1, 0) | Detalles de DET-12 |
