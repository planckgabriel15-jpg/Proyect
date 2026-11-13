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
