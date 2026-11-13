# Diagnóstico del programa (Etapa A)

Fecha: 13/11/2026. Se revisó todo `src/`, se corrieron las 137 pruebas (pasan todas) y se usó
el programa en el navegador como lo usaría un vendedor. Este documento es la **línea base**: al
final del trabajo se vuelve a medir lo mismo (ver `docs/CAMBIOS.md`).

## a) Mapa de fricción del comercial

### Cómo se midió

Un navegador automático (`herramientas/medir-flujo.mjs antes`) recorre el flujo completo y
cuenta cada cosa que tiene que hacer el vendedor:

- **clic**: tocar un botón, una tarjeta o una muestra de color;
- **opción**: elegir un valor de una lista desplegable (abrirla y elegir);
- **campo**: escribir en una casilla (se cuentan también las teclas);
- **decisión**: acción donde hay que elegir entre alternativas (qué pieza, qué terminación…);
- **pantalla**: cada vista distinta por la que pasa.

El **tiempo** es una estimación con el modelo KLM (*Keystroke-Level Model*, Card, Moran y
Newell, 1980): 1,35 s de preparación mental por acción, 1,1 s por apuntar con el mouse, 0,2 s
por clic, 0,28 s por tecla, 0,4 s por pasar la mano entre mouse y teclado y 1,5 s para
orientarse en cada pantalla nueva (este último valor es un [SUPUESTO] propio). Es el tiempo de
un vendedor que **ya sabe** qué cargar y no se equivoca: sirve para comparar antes y después,
no como tiempo real de mostrador. No incluye mirar el dibujo ni hablar con el cliente.

Los tres casos empiezan en la pantalla de ingreso y terminan con la hoja impresa:

1. **Canaleta con tapas y boqueta**: la canaleta de la nota real (1 + 20 + 32 + 7), tapa
   izquierda soldada, tapa derecha engrampada, una boqueta rectangular de 10 × 5 a 60 cm,
   prepintada negra.
2. **Babeta a medida con corte láser**: babeta de 12 × 18, 3 m de largo, corte láser
   sinusoidal en la segunda cara, prepintada negra, 4 piezas.
3. **Artículo de reventa sin dibujo**: 2 rejillas de ventilación de 15 × 30.

### Resultado (línea base)

| Caso | Clics | Opciones | Campos | Teclas | Decisiones | Pantallas | Tiempo KLM |
|---|---|---|---|---|---|---|---|
| 1. Canaleta con tapas y boqueta | 11 | 5 | 5 | 36 | 8 | 9 | **90 s** |
| 2. Babeta a medida con láser | 10 | 3 | 7 | 43 | 6 | 9 | **88 s** |
| 3. Artículo de reventa | 9 | 2 | 4 | 39 | 4 | 9 | **70 s** |

Las 9 pantallas son siempre las mismas: ingreso → inicio → nota → asistente paso 1 (¿qué
pieza?) → paso 2 (medidas y dibujo) → paso 3 (material y cantidad) → nota → cartel de
confirmación → impresión.

### Dónde se pierde el tiempo

| # | Fricción | Evidencia | A quién le pasa |
|---|---|---|---|
| F1 | **El artículo de reventa pasa por los 3 pasos** aunque solo hay que elegirlo y poner la cantidad. El paso 2 ("Medidas y dibujo") le muestra un 2D y un 3D de algo que no se fabrica | Caso 3: 9 pantallas y 70 s para 2 datos (medida y cantidad) | Todos los casos de reventa |
| F2 | **El paso 2 muestra todo junto**: 59 controles a la vista en una canaleta sin tocar nada (11 casillas, 14 listas, 34 botones) y 74 cuando tiene tapas y boqueta | Conteo de controles visibles; captura del paso 2 | Canaletas y plegados |
| F3 | La tabla de tramos tiene **8 columnas siempre visibles**: sentido, tipo, láser y observación se usan poco, pero ocupan el ancho y obligan a desplazarse a los costados (se corta en "Obs…") | Captura del paso 2 a 1366 px | Plegados |
| F4 | **La galería muestra las 51 plantillas a la vez** (55 controles). No recuerda lo que el vendedor usa siempre | Conteo en el paso 1 | Todos |
| F5 | **El material no se recuerda**: cada pieza nueva arranca en galvanizado C25 natural, aunque la anterior haya sido prepintada negra. En una nota de varios renglones del mismo material se elige de nuevo cada vez | `config.renglonPorDefecto` fijo; caso 1 y 2: 1 opción + 1 clic repetidos por renglón | Notas de 2 o más renglones |
| F6 | **El cliente se escribe entero cada vez**, aunque ya tenga notas | Campo de texto libre sin sugerencias | Clientes que vuelven |
| F7 | El resultado (desarrollo, banda, código, descripción) está **siempre abierto** al pie y le saca alto a la pantalla, sobre todo en el celular | Captura: el pie ocupa unos 80 px en PC y más en 360 px | Celular |
| F8 | Para emitir hay **dos confirmaciones seguidas** de la misma acción: el botón "Emitir nota" y el cartel "¿Emitir la nota de…?" | 1 clic + 1 decisión en los tres casos | Todos |
| F9 | Los errores de una pieza se avisan **al final**, en un cartel del navegador con la lista ("La pieza tiene problemas…"), lejos del campo que hay que corregir | `asistente.js` → `siguiente()` usa `confirm()` | Quien carga algo mal |
| F10 | En Producción el comercial ve el **tablero de todas las notas de todas las sucursales** (con datos de demostración son 500), no las suyas | Pestañas "Tablero" y "Notas emitidas" | Vendedor que quiere saber "¿está lista la de Pérez?" |
| F11 | No se puede **repetir una nota** ("lo mismo que la vez pasada"): hay que cargar renglón por renglón | Solo existe "Duplicar" renglón | Clientes que repiten |

## b) Matriz de redundancia

Regla usada: es redundante lo dicho **dos veces en el mismo documento**, o un dato derivado
que el usuario tiene que volver a escribir. No se toca ningún dato que producción use para
fabricar ni que facturación use para cobrar.

Texto real de la hoja impresa del caso 1 (antes de los cambios), para ver las repeticiones:

```
1. 2,44 mts canaleta pp negro D60 CH 25 c/ tapa izq. soldada, tapa der. engrampada y 1 boqueta | CG05P60 | 1 | 1
+ 2 tapas (izq. soldada, der. engrampada) (puesta en la canaleta) | TS60N | 2 u.
+ boqueta redonda Ø10 (puesta en la canaleta) | BQ10N | 1 u.
[dibujo 2D: 1 dobl. aplast. · 20 · 32 · 7 · flecha "pintura" · leyenda "Pintura AFUERA"]
[imagen 3D]
Tramos: 1 (dobl. aplast.) + 20 + 32 + 7 = 60
Desarrollo: 60 cm
Pintura: AFUERA
Tapa izquierda: soldada
Tapa derecha: engrampada
Boqueta 1: boqueta redonda Ø10, boca 10 cm, centro a 30 cm de la punta izquierda
[vista desde arriba: tapa izq. soldada · tapa der. engrampada · B1 Ø10 · 30 · largo 2,44 m]
[cara 3 de frente: B1 Ø10 · 16 · 30 · largo 2,44 m]
```

| # | Dato | Dónde aparece hoy | Quién lo necesita | Verificado | Decisión |
|---|---|---|---|---|---|
| R1 | **Desarrollo** | Descripción ("D60"), lista de detalles ("Desarrollo: 60 cm") y final del texto de tramos ("= 60"): **3 veces** | Facturación (banda y código), producción (ancho de la tira) | Sí: `impresion.js` arma las tres | **Una vez**: queda en la descripción. Se muestra aparte solo si no está ahí (pieza con pendiente o desarrollo corregido a mano) |
| R2 | **Medidas de los tramos** | Cotas del 2D y texto "Tramos: 1 + 20 + 32 + 7" | Producción | Sí | **Una vez**: el 2D acotado es la referencia. Se elimina el texto. El tipo de tramo (dobladillo aplastado, engrafe) ya está escrito en el 2D junto a la cota |
| R3 | **Lado de la pintura** | Flecha "pintura" del 2D, leyenda del 2D ("Pintura AFUERA") y detalle "Pintura: AFUERA": **3 veces**. Además "2 caras" en la descripción cuando va de los dos lados | Producción (para no plegar al revés) | Sí: `perfilSvg.js` y `impresion.js` | **Una vez**, en la ficha de material junto al 2D ("Pintura AFUERA") más la flecha del dibujo, que no es texto sino la marca sobre la chapa. Se quitan la leyenda y el detalle |
| R4 | **Material, color y calibre** | Solo en la descripción ("pp negro", "CH 25") y en el código | Producción y facturación | Sí | **Mantener** en la descripción (es lo facturado) y agregar una **ficha de material** clara junto al 2D, pedida por el punto 6 del encargo. Para que no sea una repetición de la descripción dentro del bloque de fabricación, la ficha dice lo que la descripción abrevia: material completo, espesor en mm y lado de pintura |
| R5 | **Imagen 3D** | Repite la forma del 2D | Nadie la necesita para fabricar (ayuda visual) | Sí: ya es opcional por nota y por renglón | **Mantener opcional** (regla ya existente: apagada en productos estándar) |
| R6 | **Tapas** | Descripción ("c/ tapa izq. soldada…"), fila con código propio ("+ 2 tapas (izq. soldada, der. engrampada)"), detalles ("Tapa izquierda: soldada", "Tapa derecha: engrampada") y vista desde arriba: **4 veces** | Producción (qué tapa y cómo va), facturación (código y cantidad) | Sí | Facturación: queda la **fila con código**. Fabricación: queda la **vista desde arriba**. Se eliminan las líneas de detalle. La descripción **no se toca** (es la foto de lo facturado y una regla confirmada), pero se anota en PENDIENTES que repite lo de las filas |
| R7 | **Boquetas** | Descripción ("y 1 boqueta"), fila con código, detalle ("Boqueta 1: boqueta redonda Ø10, boca 10 cm, centro a 30 cm…"), vista desde arriba y cara de frente: **5 veces** | Producción y facturación | Sí | Igual que R6. El detalle queda **solo con lo que el dibujo no dice** (largo de la boca; altura y corrimiento si va en la tapa) |
| R8 | **Cortes** | Descripción ("c/ corte Ø10"), detalle ("Corte 1: …") y cara de frente | Producción | Sí: `cortes.js → detalleDeCortes` | Igual: queda la **cara acotada**; el detalle solo si lleva pared (alto y lado), que el dibujo no muestra |
| R9 | **Largo de la pieza** | Descripción ("2,44 mts") y dentro de cada vista extra ("largo 2,44 m" en la planta y en cada cara) | Producción | Sí | **Mantener en la descripción** y en **una** vista. En las demás se quita |
| R10 | **Piezas y Cantidad (chapas)** | Dos columnas | Producción (piezas), facturación (chapas) | Sí | **Mantener las dos**: no son el mismo dato (4 piezas de 1,22 m = 2 chapas). Se aclara el título: "Piezas" y "Cantidad (chapas)" |
| R11 | **Código pendiente** | Columna Código ("PENDIENTE") y detalle "CÓDIGO PENDIENTE: lo completa administración" | Administración | Sí | **Una vez**, en la columna: "PENDIENTE" |
| R12 | **Código genérico** | Código en la columna, detalle "Código genérico: confirmarlo con administración" y aviso | Administración | Sí | **Una vez**, en la columna: el código con la marca "(genérico)" |
| R13 | **Fecha** | Encabezado ("Fecha") y pie ("Emitida: 13/11/2026 12:52") | Todos | Sí | Encabezado: la **fecha**. Pie: solo la **hora** de emisión junto al vendedor |
| R14 | **Vendedor** | Solo en el pie | Producción (a quién preguntar) | Sí: no se repite | **Mantener** |
| R15 | **Aviso de empalme** | Descripción ("empalme 2,44 + 0,56"), detalle "Empalme: …" y aviso "Supera el largo de la chapa" | Producción | Sí | **Una vez**: la descripción. Se quitan el detalle y el aviso cuando el empalme ya está resuelto |
| R16 | **Tarjeta del renglón en la nota** | Miniatura + descripción + código + códigos extra + piezas + chapas + tiempo estándar + consumo físico + 4 botones | Comercial: descripción, código y cantidad. Producción: tiempo | Sí | Para el comercial: **descripción, código y cantidad**. El tiempo estándar y el consumo físico pasan a "ver cálculo" (y siguen en Producción) |
| R17 | **Panel de resultados del asistente** | Desarrollo, banda, código y descripción siempre abiertos | Comercial (para controlar) | Sí | **Una línea compacta** con "ver cálculo" |
| R18 | **Banda** | Panel de resultados ("1/2 chapa (60)") y dentro del código (…60) | Facturación | Sí | Queda dentro de "ver cálculo" |
| R19 | **Datos que se vuelven a escribir** | Material, calibre, terminación y color en cada renglón; cliente en cada nota | Comercial | Sí | **Recordar** el último material usado por el vendedor y **sugerir** clientes de notas anteriores |
| R20 | **Medida de la boqueta** | Se carga una vez, pero la forma por defecto (redonda Ø10) obliga a cambiar 1 lista y 2 campos si es rectangular | Comercial | Sí | Mantener: no es redundancia. Se recuerda la última forma usada |

Datos que **no** son redundantes y se mantienen tal cual: ángulos (solo en el 2D), cantidad,
observaciones, corte láser (su vista de frente es la única que muestra la onda), fecha de
entrega y prioridad (las usa producción), NP, factura y cliente.

## c) Qué le sobra y qué le falta al comercial

**Le sobra (hoy lo ve y no lo necesita para armar la nota):**

1. El tiempo estándar de fabricación en cada tarjeta y el "consumo físico estimado": son
   datos de producción.
2. En la tabla de tramos: las columnas de sentido, tipo, láser y observación en todos los
   renglones, aunque casi siempre valen lo mismo.
3. "El tramo 1 arranca hacia", los botones de aleta y dobladillo, espejar y dibujar a mano:
   sirven para piezas a medida, no para una canaleta del catálogo a la que se le cambia una
   medida.
4. Tapas, boquetas, cortes, empalme y pendiente abiertos a la vez en el paso 2.
5. En Producción: el tablero de todas las sucursales. Las otras 8 pestañas ya están ocultas
   para el comercial.
6. El 2D y el 3D de un artículo de reventa.
7. El cartel de confirmación de la emisión cuando no hay ningún aviso.

**Le falta:**

1. Una forma **rápida** de agregar un producto del catálogo: elegir, poner largo y cantidad,
   y agregar (sin pasar por 3 pantallas).
2. Que el programa **recuerde** su material, calibre y color habituales.
3. **Recientes y frecuentes**: los 5 o 6 productos que vende todos los días, arriba de todo.
4. Buscar con las **palabras del cliente** ("zinguería para la canaleta", "desagüe",
   "caño de bajada", "remate"), no solo con el nombre de la plantilla.
5. **Autocompletar el cliente** con los de notas anteriores.
6. **Repetir una nota** entera.
7. Ver el **estado de sus notas** (pendiente, en curso, lista) sin entrar a Producción.
8. Los **errores al lado del campo**, apenas ocurren, y saber exactamente qué falta para
   poder emitir.
9. Elegir la **empresa** del grupo con la que vende (hoy todo es Abasto) y ver los productos
   de HIPER y de G-TEC.
10. Cargar algo que **no es chapa plegada**: una pieza metalmecánica a medida o un servicio.

## Hipótesis del encargo: resultado de la verificación

| Hipótesis | ¿Se confirmó? |
|---|---|
| El desarrollo aparece en la descripción y otra vez en los detalles | Sí, y una tercera vez al final del texto de tramos (R1) |
| "Tramos" repite las cotas del 2D | Sí (R2) |
| "Pintura" repite "pp negro" / "2 caras" y las flechas del 2D | En parte: el **lado** se repite 3 veces (R3); el **color** solo está en la descripción (R4) |
| El 3D repite el 2D | Sí, pero ya era opcional (R5) |
| Tapas, boquetas y cortes figuran como texto, como filas con código y como vistas extra | Sí: entre 3 y 5 veces (R6, R7, R8) |
| "Piezas" y "Cantidad" conviven en columnas separadas | Sí, pero **no es redundancia**: son datos distintos (R10) |
| "Código pendiente" y "código genérico" salen en la columna y como aviso | Sí (R11, R12) |
| Fecha y vendedor se repiten entre encabezado y pie | La fecha sí (R13); el vendedor no (R14) |
| La tarjeta de la nota y el asistente muestran todo siempre | Sí (R16, R17, R18, F2, F3) |
