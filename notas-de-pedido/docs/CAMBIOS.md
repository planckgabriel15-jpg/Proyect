# Cambios: qué se cambió, por qué y cómo se comprobó que producción no pierde nada

Cada cambio dice: **qué cambió**, **qué problema resolvía**, **en qué se apoya** (número de fuente de
[`REFERENCIAS.md`](REFERENCIAS.md), fricción F… o redundancia R… de [`DIAGNOSTICO.md`](DIAGNOSTICO.md)) y
**cómo se verificó** que producción y facturación siguen recibiendo lo mismo.

Regla que se respetó en todos: **nunca se elimina un dato que usa producción** (medidas, ángulos, largo, material,
calibre, color, lado de pintura, cantidad, observaciones, corte láser, tapas y boquetas) **ni facturación**
(descripción, código, cantidad). "Redundante" es solo lo que se dice dos veces en el mismo documento o un dato
calculado que se vuelve a escribir.

---

## Etapa C: grupo de empresas y catálogo unificado

### C1. Empresa como dato: una sola unión vendedor → sucursal → empresa

- **Qué cambió.** Archivo nuevo `datos/empresas.json` (las tres empresas, con logo o texto de reemplazo, colores,
  prefijo y planta; y las plantas). Cada sucursal de `sucursales.json` lleva `empresaId`. La nota guarda
  `empresaId` (la empresa que emite). Lógica nueva y pura en `src/logica/empresas.js`.
- **Problema.** El programa era de una sola empresa: logo y colores fijos en `config.json`, un solo catálogo,
  un solo taller.
- **En qué se apoya.** Pedido explícito (sirve a las tres empresas). El diseño "cada dato una vez": la empresa
  **no se elige**, sale de la sucursal del vendedor (fuentes 3 y 23: valores por defecto y no volver a cargar datos).
- **Producción no pierde nada.** La nota sigue con su sucursal y su número; solo se **agrega** `empresaId`.
  Pruebas: "grupo: tres empresas…" y "numeración por empresa y sucursal…" en `tests/grupo-empresas.test.js`.

### C2. Numeración: correlativa por sucursal (sin cambios) + identificador con prefijo

- **Qué cambió.** El número sigue siendo correlativo por sucursal (regla confirmada 5.1, **no se tocó**). Como cada
  sucursal es de una sola empresa, queda "por empresa y sucursal". Se agrega el identificador completo
  `PREFIJO-LETRA-NÚMERO` (por ejemplo `AB-C-123`), que se usa como nombre del PDF y se ve en las listas.
- **Problema.** Con tres empresas, "nota 12" podía ser de cualquiera.
- **Producción no pierde nada.** Los contadores guardados no cambian de formato (no hizo falta migrarlos).
  La hoja impresa muestra el número igual que antes. Prueba: tres empresas emitiendo intercaladas dan 1, 2 / 1, 2 / 1
  y cinco identificadores distintos.

### C3. Catálogo unificado: 51 plantillas de antes + 178 relevadas = 229

- **Qué cambió.** Se cargó en `datos/catalogo.json` todo lo publicado por las tres empresas (ver
  [`CATALOGO_GRUPO.md`](CATALOGO_GRUPO.md)). Cada plantilla dice quién la vende (`empresas`, vacío = las tres),
  dónde se hace (`fabricaEn`) y si sale de stock o se fabrica (`abastecimiento`). Lo hace una herramienta
  (`herramientas/cargar-relevamiento.js`) a partir de `docs/relevamiento/`, para que se pueda repetir.
- **Problema.** Faltaban los productos de HIPER, la reventa de Abasto y todo G-TEC.
- **En qué se apoya.** Fuentes 29, 30 y 31 (los tres sitios). **No se inventó nada**: nombres y modelos son los
  publicados; sin código de facturación → "código pendiente"; sin medidas publicadas → [A CONFIRMAR]; sin dibujo.
- **Producción no pierde nada.** Las 51 plantillas anteriores conservan id y medidas (la herramienta solo les agrega
  los tres campos nuevos y palabras para el buscador). Pruebas: "catálogo: cada plantilla dice quién la vende…" y
  "productos relevados: llevan su fuente y NO se les inventó código, medida ni dibujo".

### C4. Cada vendedor ve el catálogo de su empresa; "Ver todo el grupo" muestra el resto

- **Qué cambió.** La galería del asistente muestra solo las plantillas de la empresa que emite; un interruptor
  (que queda recordado) muestra las de las tres. Lo que es de otra empresa lleva una etiqueta. Los grupos de
  artículos (sin dibujo) aparecen plegados con la cantidad entre paréntesis y se abren con un toque o al buscar.
  Si la búsqueda no encuentra nada en la empresa pero sí en el grupo, lo dice.
- **Problema.** Con 229 plantillas la galería entera era imposible de recorrer (F4 del diagnóstico: ya con 51
  había 55 controles a la vista).
- **En qué se apoya.** Ley de Hick (fuente 16), divulgación progresiva (fuente 2) y reconocer en vez de recordar
  (fuente 7).
- **Producción no pierde nada.** Es solo qué se muestra: el renglón que se crea es el mismo. Prueba: "catálogo
  filtrado…".

### C5. Buscador: varias palabras, modelos, marca y palabras del mostrador

- **Qué cambió.** Antes buscaba el texto entero dentro de "nombre + palabras clave". Ahora cada palabra se busca
  por separado y en cualquier orden, también dentro de los modelos y la marca ("extractor 150", "durlock").
- **Problema.** El vendedor tenía que saber cómo se llama la plantilla; el cliente pide "algo para la gotera"
  o "un extractor de 150" (pedido de la etapa D: buscador con el vocabulario del mostrador). Las palabras cargadas
  son un punto de partida [SUPUESTO] a validar con los vendedores.
- **Compatibilidad.** Buscar una sola palabra da lo mismo que antes (la prueba "buscador de plantillas" de siempre
  sigue pasando). Prueba nueva: "buscador: varias palabras en cualquier orden…".

### C6. Dos tipos de renglón nuevos: pieza metalmecánica a medida y servicio

- **Qué cambió.** `tipoPieza` admite `metalmecanica` (descripción, medidas, material, espesor en mm, procesos y
  plano opcional) y `servicio` (alcance, unidad y lugar; cantidad con decimales). Los parámetros de una plantilla
  pueden ser de texto libre o de varias casillas. Límites publicados por G-TEC como control: lo que la planta no
  puede hacer **no se deja emitir** (por ejemplo, corte láser de más de 20 mm).
- **Problema.** G-TEC no vende perfiles por tramos: sus trabajos no entraban en ningún tipo.
- **En qué se apoya.** Fuentes 20 a 23 (configuradores de venta y Lantek: pieza = geometría o plano + material +
  espesor + cantidad + procesos) y fuente 29 (límites de G-TEC). Poka-yoke (fuente 17): el error se frena al cargar.
- **Producción no pierde nada.** Los renglones plegados, especiales y artículos se calculan igual (los 16 casos
  obligatorios y las pruebas de siempre pasan sin cambios). Los calibres C30–C20 no se tocaron: los espesores en
  mm son una lista aparte (`materiales.json` → `industriales`). Pruebas: "pieza metalmecánica a medida…",
  "servicio…", "tipos de renglón…".

### C7. Productos sin código de facturación: "código pendiente", nunca un código inventado

- **Qué cambió.** Las plantillas relevadas nacen con `codigoPendiente`. No se busca en la tabla ni se arma un
  código genérico. Cuando administración tenga el código lo escribe en `catalogo.json` (`codigo`), en la plantilla
  o en cada modelo, y el aviso desaparece solo.
- **Problema.** Sin esto, o el renglón no se podía emitir, o tomaba un código de otra cosa.
- **Facturación no pierde nada.** El aviso "Código pendiente: lo completa administración" ya existía y sale en la
  nota y en la hoja. Pruebas: "código cargado en el catálogo…" y la adaptación de la prueba del catálogo (abajo).

### C8. La nota se reparte sola entre plantas

- **Qué cambió.** Cada trabajo de producción lleva `planta`. Regla: lo que se fabrica a pedido va a la planta que
  lo hace (aunque la nota la emita otra empresa del grupo); lo de stock y la reventa de otras marcas lo prepara el
  depósito de la empresa que emite. Si la nota tiene renglones de más de una planta, la pantalla de la nota lo avisa
  y la hoja impresa dice quién hace cada renglón. La máquina del modelo de tiempos se pasa a la equivalente de
  esa planta (`reemplazaA` o mismo tipo en `produccion.json`).
- **Problema.** Un solo taller para todo.
- **Producción no pierde nada.** En una nota de Abasto con productos de Abasto, planta y máquina son las de siempre.
  Prueba decisiva: **las 500 notas de la demo de Abasto y sus registros de producción salen idénticos** a antes
  del cambio (se comparó la huella de las notas y de los registros generados con la versión anterior y con la
  nueva: `90506c94a397` y `44fc3a505689` en las dos). Pruebas: "planta de cada renglón…", "máquina equivalente…",
  "producción: los trabajos llevan planta…".

### C9. Producción por planta

- **Qué cambió.** El jefe elige planta al ingresar (o "todas") y la puede cambiar arriba en Producción. Tablero,
  lotes, asignación, operarios, material e indicadores muestran solo esa planta. El operario ve la suya.
  No se arma un lote con trabajos de dos plantas.
- **Producción no pierde nada.** Mirando "Taller de plegado de Abasto" se ve lo mismo que antes. Al guardar
  operarios de una planta, los de las otras no se tocan.

### C10. Tiempos de lo nuevo

- **Qué cambió.** Servicio vendido por hora: el tiempo es el vendido (1 h = 60 min, sin suplementos ni preparación).
  Servicios por pieza, metro o trabajo completo y piezas metalmecánicas: dos filas nuevas en "Productos sin perfil"
  (15 min + 10 min por unidad, **[SUPUESTO]**, editables en Producción → Parámetros). Artículos de grupos nuevos:
  el tiempo de "artículos" (buscar y preparar).
- **Producción no pierde nada.** Ningún tiempo existente cambió (la prueba del ejemplo EJ1 = 931,196 s y las de
  tiempos pasan sin tocar). Si el jefe había editado la tabla, sus valores mandan y las filas nuevas se suman.

### C11. Logo y encabezado de la empresa que emite

- **Qué cambió.** Menú, pantalla de ingreso y hoja impresa usan el logo de la empresa (la hoja, la de la empresa
  **que emitió la nota**, no la de quien la mira). HIPER y G-TEC todavía no tienen archivo de logo: se muestra su
  nombre en un recuadro, configurable. Se quitó `marca` de `config.json`: logo y colores están una sola vez.
- **Producción no pierde nada.** La hoja de Abasto se ve igual, con el nombre de la empresa al lado del logo.

### C12. Hoja impresa sin recuadro vacío

- **Qué cambió.** Artículos, servicios y piezas con plano no llevan el recuadro "producto de catálogo: sin dibujo".
- **Problema.** Media hoja gastada en un dibujo que no dice nada (R del diagnóstico: información sin contenido).
- **Producción no pierde nada.** Descripción, código, cantidad y avisos siguen; solo se va el recuadro.

### C13. Cantidad de un servicio con su unidad

- **Qué cambió.** "2,5 h", "30 m", "10 u." en vez de "2.5 u.".
- **Facturación no pierde nada.** Es el mismo número; solo se escribe con coma y con la unidad elegida.

### C14. Error que ya estaba: la palabra "null" arriba del tablero

- **Qué cambió.** Cuando no había alertas, el tablero de producción escribía "null". Corregido.

### Migración (versión de datos 3)

`almacenamiento.migrarDatos` corre una sola vez al abrir el programa. **Solo agrega campos**:

| Dato | Antes | Después |
|---|---|---|
| `nota.empresaId` | no existía | la empresa de la sucursal de la nota (las notas viejas son de Abasto) |
| `renglon.fabricaEn`, `renglon.abastecimiento` | no existían | los del catálogo para esa plantilla |
| Sucursales editadas en Configuración | sin `empresaId` | se completa y se suman las de HIPER y G-TEC, sin pisar lo editado |
| Número, cliente, descripción, código, cantidad, foto del cálculo | — | **no se tocan** |

Prueba: "migración (versión 3)…" compara la foto de una nota emitida antes y después (idéntica) y confirma que la
segunda corrida no escribe nada. Aunque no se migre, la empresa y la planta salen bien (se resuelven por la
sucursal y el catálogo).

### Pruebas que ya existían y hubo que adaptar

Todas las demás pasan sin cambios. Estas cuatro medían, justamente, el dato que se pidió cambiar:

| Prueba | Qué afirmaba | Qué afirma ahora | Por qué |
|---|---|---|---|
| "vendedores numerados" (`catalogo-y-especiales`) | 30 vendedores | 36 | Se sumaron 3 de HIPER y 3 de G-TEC |
| "cargar datos base" (`codigos-y-almacenamiento`) | 10 sucursales, 30 vendedores | 12 y 36, y que 10 siguen siendo de Abasto | Se sumaron las sucursales de HIPER y G-TEC |
| "catálogo: ids únicos, grupos existentes…" | `tipoPieza` es `plegada` o `especial` | también `metalmecanica` o `servicio` | Los dos tipos de renglón pedidos |
| "catálogo: cada plantilla da un renglón sin errores y con código" | todas dan un código | las que no tienen código de facturación dan **"código pendiente"** (y ningún código); las "a medida" se prueban aparte porque nacen con datos por completar | No inventar códigos |

La prueba de la demo ("50 notas por local") no se tocó: sigue pidiendo 50 por cada sucursal y ahora son 12.

---

## Etapa D: rediseño para el comercial

Cada idea del pedido se **evaluó**; las que no se justificaban se descartaron y está dicho por qué (al final).

### D1. Asistente de 2 pasos: una sola ficha para medidas, material y cantidad

- **Qué cambió.** Antes: 1) galería, 2) medidas y dibujo, 3) material y cantidad. Ahora: 1) galería y 2) **la pieza**,
  con largo y cantidad arriba, la tabla de medidas, el material y el dibujo 2D en la misma pantalla.
  "Agregar a la nota" está siempre a la vista (Ctrl+Enter).
- **Problema.** F1 y F2 del diagnóstico: el artículo de reventa pasaba por 3 pantallas para elegir un modelo y una
  cantidad; el material estaba escondido en otro paso.
- **En qué se apoya.** Fuente 8 (los asistentes por pasos sirven para tareas que se hacen pocas veces; molestan a
  quien la repite todo el día), fuente 4 (formularios: lo relacionado junto), fuente 9 (aceleradores para el experto).
- **Producción no pierde nada.** El renglón que se guarda tiene exactamente los mismos campos (medidas, ángulos,
  largo, material, calibre, terminación, color, lado de pintura, cantidad, observaciones, accesorios, cortes,
  empalme, pendiente). Las pruebas de cálculo, tiempos y agrupamiento no se tocaron y pasan.
  Una pieza a medio cargar guardada en el viejo "paso 3" se abre en la ficha.

### D2. Lo que se usa poco está plegado, con su resumen a la vista

- **Qué cambió.** Tapas y boquetas, cortes en la chapa y "más opciones" (con pendiente, desarrollo a mano,
  observaciones) son secciones plegadas. El título dice lo que tienen adentro ("Tapas y boquetas: tapa izq. soldada y
  1 boqueta", "Cortes en la chapa: ninguno") y se abren solas si ya tienen algo cargado, con un error adentro o al
  usar su atajo (Alt+Q, Alt+R, Alt+L). El empalme sigue apareciendo solo cuando la pieza supera la chapa.
- **Problema.** F2: 59 controles a la vista en una canaleta sin tocar nada.
- **En qué se apoya.** Divulgación progresiva (fuente 2) y ley de Hick (fuente 16).
- **Producción no pierde nada.** Nada se quitó: está a un toque. El resumen evita que algo cargado quede escondido.

### D3. Tabla de tramos en "vista simple"

- **Qué cambió.** Para una pieza del catálogo la tabla muestra N°, medida y ángulo. Sentido, tipo, láser,
  observación, "arranca hacia", aletas, dobladillos, espejar y dibujar a mano aparecen con "Ver todas las columnas y
  herramientas" (se recuerda la elección del vendedor). Se pasa sola a la tabla completa al **agregar un tramo** y
  arranca completa si la pieza tiene corte láser u observaciones o es una pieza libre (sin tramos).
- **Problema.** F3: 8 columnas siempre visibles para cambiar una medida.
- **Producción no pierde nada.** Las columnas ocultas conservan su valor; el tipo de tramo además está escrito en el
  2D. Nunca se oculta una columna que tenga algo cargado fuera de lo común (láser u observación).
- **Costo reconocido.** Cargar un corte láser pide un toque más (ver la medición del caso 2).

### D4. El material no se vuelve a cargar

- **Qué cambió.** Una pieza nueva arranca con el material, calibre, terminación, color y lado de pintura de la
  **pieza anterior de la misma nota**; si la nota está vacía, con los últimos que usó el vendedor. Un cartel chico lo
  avisa ("Igual que la pieza anterior de esta nota. Si es otro, cambialo acá"). También se recuerda la última
  boqueta (forma y medidas, no la posición).
- **Problema.** F5 y R19/R20: cada pieza arrancaba en galvanizado C25 natural.
- **En qué se apoya.** Fuente 3 (valores por defecto: la mayoría los deja como están, por eso tienen que ser los
  más probables) y fuente 15 (reducir la carga de memoria).
- **Riesgo y cómo se cubre.** Un valor por defecto equivocado se puede pasar por alto (fuente 6, "slips"). Por eso
  el material está **a la vista en la misma ficha**, con el aviso de dónde salió, y figura en la descripción del pie.
  Si el material recordado ya no existe en `materiales.json`, no se usa.
- **Producción no pierde nada.** Son los mismos campos del renglón, con otro valor inicial. Prueba: "preferencias:
  se recuerda el último material…".

### D5. Lo último y lo más usado, arriba de la galería

- **Qué cambió.** Sin texto en el buscador, la galería empieza con "Lo último que usaste" y "Lo que más usás"
  (hasta 6 cada una, por vendedor, solo de lo que puede ver).
- **Problema.** F4: la galería no recordaba nada.
- **En qué se apoya.** Fuente 7 (reconocer es más fácil que recordar) y fuente 9 (aceleradores).
- **Prueba.** "preferencias: recientes… y frecuentes…".

### D6. Cliente con sugerencias

- **Qué cambió.** Al escribir el cliente se ofrecen los de notas anteriores de la empresa (los más recientes
  primero). Se puede escribir uno nuevo igual.
- **Problema.** F6. **En qué se apoya.** Fuente 11 (autocompletar: menos tipeo y menos variantes del mismo nombre).
- **Producción no pierde nada.** El cliente sigue siendo texto libre. Prueba: "clientes conocidos…".

### D7. Repetir una nota

- **Qué cambió.** Botón "Repetir" en la lista de notas y en la hoja: arma una nota **nueva** con el mismo cliente
  y las mismas piezas. No copia número, factura, fecha de entrega ni prioridad (son de cada pedido), ni la foto del
  cálculo (se calcula con los códigos de hoy).
- **Problema.** F11. **Prueba.** "repetir una nota…": la original queda idéntica y la copia tarda y se agrupa igual.

### D8. Lo que falta se marca en su lugar; no se puede emitir lo que no se puede fabricar

- **Qué cambió.** (a) En la ficha, cada problema aparece **al lado del campo** y en una lista corta al pie que
  lleva al campo con un toque. (b) Ya no hay cartel "La pieza tiene problemas… ¿Agregarla igual?": la pieza se
  agrega y queda marcada en la nota con "Falta: … [Corregir]". (c) Al emitir, lo que falta se marca en el encabezado
  y en una lista que lleva a cada renglón. (d) Emitir sigue **bloqueado** mientras haya un error (regla sin cambios),
  incluidos los límites de planta de G-TEC.
- **Problema.** F9: los errores aparecían al final, en un cartel del navegador, lejos del dato.
- **En qué se apoya.** Fuentes 5, 13 y 14 (el mensaje junto al campo, diciendo qué falta y cómo se arregla) y
  fuente 17 (poka-yoke).
- **Producción no pierde nada.** `validarNota` no se tocó; la lista nueva (`faltantesDeNota`) da los mismos
  errores con su lugar. Prueba: "faltantes: dicen DÓNDE se corrige…".

### D9. Hoja impresa: cada dato una sola vez

- **Qué cambió.** El contenido de la hoja lo arma un módulo nuevo y puro (`logica/hojaImpresa.js`), que se prueba
  sin navegador. Tabla de lo que se quitó y dónde quedó cada dato:

| Dato | Antes | Ahora (una vez) | ¿Producción lo sigue viendo? |
|---|---|---|---|
| Desarrollo (R1) | Descripción, "Desarrollo: 60 cm" y "= 60" | Descripción ("D60") | Sí. Si se corrigió a mano, queda el aviso |
| Medidas de tramos (R2) | Cotas del 2D y texto "Tramos: 1 + 20 + 32 + 7" | Cotas del 2D | Sí: el 2D es la referencia oficial |
| Lado de pintura (R3) | Leyenda del 2D, detalle y flecha | **Ficha de material** + flecha en el dibujo | Sí, más visible (recuadro junto al 2D) |
| Material, calibre, color (R4) | Solo abreviados en la descripción | Descripción + **ficha** con el nombre completo y el espesor en mm | Sí, mejor que antes |
| Tapas (R6) | Descripción, fila con código, 2 líneas de detalle y vista desde arriba | Fila con código (factura) + vista desde arriba (fabrica) | Sí. Pestaña especial o tapa a medida: siguen escritas |
| Boquetas (R7) | Descripción, fila con código, detalle largo, vista desde arriba y cara | Fila con código + vista desde arriba (tamaño y posición a lo largo) + cara (posición a través) + nota con la **boca** | Sí: cada cota una vez |
| Cortes (R8) | Descripción, detalle y cara | Cara acotada; nota solo si lleva **pared** | Sí |
| Corte láser | Texto y vista de frente | Vista de frente (onda y valles) | Sí |
| Largo (R9) | Descripción y en cada vista extra | Descripción + una vista | Sí |
| Código pendiente / genérico (R11, R12) | Columna, detalle y aviso | Columna: "PENDIENTE" o "CL1010N (genérico)" | Sí |
| Fecha (R13) | Encabezado y pie | Encabezado; en el pie, la **hora** | Sí |
| Empalme (R15) | Descripción, detalle y aviso | Descripción ("empalme 2,44 + 0,56") | Sí |
| Recuadro "sin dibujo" de un artículo | Media hoja | No se imprime | No lo necesitaba |

- **Se agregó** (no estaba y producción lo usa): **entrega comprometida** y **URGENTE** en el encabezado, si se
  cargaron; y qué planta hace cada renglón cuando la nota se reparte.
- **No se tocó:** la descripción (es la "foto" de lo facturado y una regla confirmada), las columnas Piezas y
  Cantidad (R10: no son el mismo dato; el título ahora dice "Cantidad (chapas)"), los ángulos, las observaciones,
  el vendedor y el 3D opcional.
- **Única superposición que queda**, pedida en el encargo: material, calibre y color figuran abreviados en la
  descripción y completos en la ficha junto al 2D. También la descripción nombra tapas y boquetas que después tienen
  su fila con código: es la regla confirmada de la descripción; anotado en `PENDIENTES.md` (punto 119).
- **Cómo se verificó.** Prueba "hoja impresa: ningún dato aparece dos veces": arma la hoja del caso 1 con sus
  dibujos, cuenta cuántas veces aparece cada dato en la zona de fabricación (una) y comprueba que **los 18 datos
  que antes se imprimían siguen estando**. Otras dos pruebas cubren código pendiente, genérico, empalme, cortes con
  pared, láser, observaciones, tapa a medida y que una nota emitida sigue mostrando su foto aunque cambie la tabla
  de códigos. Se imprimió a PDF en A4 y se revisó en blanco y negro (todo es texto y línea negra; el color no lleva
  información).

### D10. Resultado en una línea, con "ver cálculo"

- **Qué cambió.** Al pie de la ficha: la descripción y el código. Desarrollo, fórmula, banda, códigos de tapas y
  boquetas y avisos están en "ver cálculo". En la tarjeta del renglón: descripción, código y cantidad; el tiempo
  estándar y el consumo físico de chapa pasaron a "ver cálculo" (y siguen en Producción).
- **Problema.** F7, R16, R17 y R18. **Producción no pierde nada:** los cálculos son los mismos; solo cambia dónde se ven.

### D11. Cantidad editable en la tarjeta y botones en vez de listas cortas

- **Qué cambió.** La cantidad se cambia en la tarjeta del renglón sin abrir la pieza. Terminación, lado de pintura y
  tipo de tapa son botones (2 o 3 opciones a la vista) en lugar de listas desplegables.
- **En qué se apoya.** Fuente 12 (las listas desplegables son el último recurso con pocas opciones).

### D12. Emitir: confirmación en la página y la impresión se abre sola

- **Qué cambió.** "Emitir nota" muestra, en la misma pantalla, "Vas a emitir la nota Nº 124 de Colón. Después no
  se puede modificar", con los avisos y el botón "Emitir e imprimir" (Ctrl+Enter dos veces). Al emitir, la hoja se
  abre con la ventana de impresión ya abierta.
- **Se evaluó quitar la confirmación** (F8) y se **mantuvo**: emitir asigna el número correlativo y no se deshace
  (fuente 15: las acciones irreversibles se confirman). Lo que se quitó es el cartel del navegador, que no decía el
  número ni dejaba ver la nota, y el clic de "Imprimir".

### D13. El comercial ve el estado de sus notas

- **Qué cambió.** La lista de Inicio muestra el estado de producción de cada nota emitida (pendiente, programada,
  en curso, hecha, demorada). En Producción, el comercial ve "Estado de mis notas" (solo las suyas; puede tildar
  "ver también las de otros vendedores") y "Notas emitidas". El jefe y el operario no cambian.
- **Problema.** F10: con la demo, el comercial veía un tablero de 500 notas de todas las sucursales.

### D14. El 3D se carga cuando se pide

- **Qué cambió.** El 3D del asistente se baja al abrir su panel (abierto por defecto en pantallas anchas, cerrado en
  el celular; se recuerda) o el editor 3D. Un artículo o un servicio nunca lo cargan. El 3D sigue siendo opcional por
  nota y por renglón, como antes.
- **Producción no pierde nada.** El 2D acotado es la referencia oficial y está siempre.

### Ideas evaluadas y descartadas (o achicadas)

| Idea | Decisión | Por qué |
|---|---|---|
| Edición de todo en la tarjeta del renglón, sin asistente | **Solo la cantidad** | Medidas y tramos necesitan el dibujo al lado para no equivocarse; en la tarjeta no hay lugar |
| Quitar la confirmación de emitir | **Se mantiene**, en la página | Emitir no se deshace |
| Agregar un artículo directo desde la galería, sin ficha | **Descartado por ahora** | Casi todos tienen modelo o medida para elegir; saltear la ficha haría cargar un modelo equivocado |
| Abrir "Tapas y boquetas" siempre en las canaletas | **Descartado** | Vuelve a los 59 controles; un toque lo abre y el resumen dice qué tiene |
| Quitar la columna "Piezas" | **Descartado** | No es el mismo dato que "Cantidad (chapas)" (R10) |
| Sacar tapas y boquetas de la descripción | **No se hace sin la empresa** | La descripción es una regla confirmada y la foto de lo facturado |
| Guardar el archivo del plano | **Solo el nombre o enlace** | El navegador da unos 5 MB para todo |

---

## Etapa E: mediciones antes y después

Mismos tres casos y mismos datos que en el diagnóstico, con la misma herramienta
(`node herramientas/medir-flujo.mjs despues`) y el mismo modelo de tiempo (KLM, fuente 18;
"orientarse en una pantalla nueva" = 1,5 s es [SUPUESTO]). Vendedor que entra por primera vez, sin nada recordado.
**Son estimaciones de modelo, no cronometraje con vendedores**: sirven para comparar, no como tiempo real.

| Caso | | Clics | Listas | Campos | Teclas | Decisiones | Pantallas | Tiempo estimado |
|---|---|---|---|---|---|---|---|---|
| 1. Canaleta con tapas y boqueta | antes | 11 | 5 | 5 | 36 | 8 | 9 | 90 s |
| | después | 13 | 2 | 5 | 36 | 8 | 7 | **80 s (−11 %)** |
| 2. Babeta a medida con corte láser | antes | 10 | 3 | 7 | 43 | 6 | 9 | 88 s |
| | después | 10 | 2 | 7 | 43 | 6 | 7 | **81 s (−8 %)** |
| 3. Artículo de reventa sin dibujo | antes | 9 | 2 | 4 | 39 | 4 | 9 | 70 s |
| | después | 7 | 2 | 4 | 39 | 4 | 7 | **62 s (−11 %)** |

Lectura honesta: la **primera** vez la mejora es chica (8 a 11 %): salen dos pantallas, el clic de imprimir y varias
listas, pero se suma un toque para abrir "Tapas y boquetas" (caso 1) y otro para ver la columna del láser (caso 2).
La mejora grande está en lo que el programa **ahora recuerda**, que antes no existía:

| Situación (caso 1) | Clics | Listas | Campos | Teclas | Pantallas | Tiempo estimado |
|---|---|---|---|---|---|---|
| Segunda nota del día: pieza en "lo último que usaste", material y boqueta recordados, cliente sugerido | 11 | 0 | 3 | 20 | 6 | **54 s** |
| "Repetir" la nota de la vez pasada (solo se carga la factura nueva) | 3 | 0 | 1 | 15 | 3 | **20 s** |

(Estas dos no incluyen elegir el vendedor al entrar, unos 8 s que se hacen una vez por día; "antes" esa misma
segunda nota costaba los 90 s completos menos esos 8.)

**Controles a la vista** (campos, listas, casillas y botones; mismo método de conteo):

| Pantalla | Antes | Después |
|---|---|---|
| Galería | 55 (51 plantillas, todas) | 43 (de 219 plantillas de Abasto se ven 40; el resto, en 8 grupos plegados o por el buscador) |
| Canaleta sin tocar nada | 59 (medidas) + 37 (material) en dos pantallas | **38 en una sola** |
| Canaleta con 2 tapas, boqueta y prepintada | 74 + 37 | 68 en una sola |
| Artículo de reventa | 2 pantallas | **12 en una** |

**Pruebas automáticas:** 137 al empezar → **166** (29 nuevas). Los 16 casos obligatorios de la especificación pasan
sin cambios. Pruebas nuevas pedidas: empresa y numeración, catálogo filtrado, tipos de renglón, migración y "ningún
dato aparece dos veces en la hoja impresa" (`tests/grupo-empresas.test.js` y `tests/rediseno-comercial.test.js`).

**Revisado a mano en el navegador** (Chromium automático, sin errores de consola): los tres roles; nota con
canaleta + artículo de HIPER + servicio de G-TEC; hoja impresa a PDF en A4; celular de 360 px de ancho (sin
desplazamiento horizontal); F1; producción con la demo de 600 notas en las tres plantas (tablero, lotes,
asignación automática, operarios, material, indicadores, vista del operario y hoja de ruta).
