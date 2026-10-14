# Prompt para Claude Code – Sistema de Notas de Pedido de Zinguería

> **Para Claude Code:** este archivo es la especificación completa del proyecto. Leelo entero antes de escribir código. Seguí el orden de trabajo de la sección 3 y respetá las reglas de negocio de la sección 5 tal como están escritas. Todo lo marcado como **SUPUESTO** es un dato provisorio tomado de internet o inventado para poder probar: tiene que quedar en archivos de configuración, fácil de cambiar, y listado en `PENDIENTES.md`.

---

## 1. Tu rol y el objetivo

Sos un desarrollador senior que construye un **prototipo funcional** para una empresa de zinguería de Córdoba (Argentina). La empresa fabrica piezas de chapa plegada: canaletas, babetas, cumbreras, boquetas, tapas, caños, etc.

**Objetivo:** reemplazar la nota de pedido en papel (que hoy el vendedor dibuja a mano, fotografía y sube a un Drive) por un programa web donde el vendedor:

1. Completa el encabezado casi sin escribir (origen, número, fecha y factura salen solos o con un clic).
2. Elige la pieza de una galería de plantillas o dibuja una pieza especial.
3. Carga las medidas en una tabla simple y ve **al mismo tiempo** el perfil acotado en 2D y la pieza en **3D**, que se actualizan en vivo.
4. Obtiene automáticamente el **desarrollo**, la **banda de cotización** y el **código del producto**.
5. Completa material, color, calibre, largo y cantidad.
6. Imprime o guarda una nota prolija que producción entiende sin preguntar nada.

**Quién lo va a mantener:** un programador con poca experiencia. Por eso el código tiene que ser simple, sin "magia", con comentarios en español y nombres de variables en español claro (`desarrolloCm`, `calcularBanda`, `tramos`).

---

## 2. Contexto del negocio

- **10 sucursales**, unos 3 vendedores por sucursal (≈30), unas 10 personas en producción y 5 en gerencia.
- Vendedores: PC en el mostrador y celular. Taller: PC, celular e impresora.
- Internet estable, pero conviene que el programa no pierda lo cargado si se corta (borrador guardado en el navegador).
- La empresa usa cuentas de Google y Google Drive. **Destino final del sistema:** Google Apps Script + Google Sheets + Google Drive. **Este prototipo** corre en el navegador, con datos guardados localmente, pero con la capa de datos separada para poder conectarla a Apps Script después sin rehacer las pantallas (ver sección 4).

### 2.1 Ejemplo real de una nota en papel (debe poder reproducirse exacta)

```
Origen: COLON          NP Nº: xxxxx        Fecha: dd/mm/aaaa
Cliente: ________      Factura Nº: xxxxx

Descripción                                          | Código   | Cantidad
2,44 mts canaleta pp negro D60  CH 25                | CG05P60  | 1
Dibujo del perfil: tramos 1 (dobladillo con aplastamiento) + 20 + 32 + 7 = 60
```

- "2,44 mts" = largo de la pieza.
- "pp negro" = chapa prepintada color negro.
- "D60" = desarrollo 60 cm.
- "CH 25" = calibre 25 (0,50 mm).
- "CG05P60" = código: CG (chapa galvanizada) + 05 (0,5 mm) + P (prepintada) + 60 (banda de media chapa).

---

## 3. Cómo quiero que trabajes

1. **Primero un plan.** Antes de programar, mostrame un plan corto: estructura de carpetas, archivos principales y orden de las etapas. Esperá mi OK.
2. **Trabajá por etapas** (sección 10). Al terminar cada etapa:
   - corré las pruebas automáticas;
   - decime en 3 a 6 líneas qué hiciste, cómo probarlo a mano y qué quedó pendiente;
   - esperá mi OK antes de seguir.
3. **Lenguaje simple.** Explicame en español rioplatense, sin tecnicismos innecesarios. Si usás una palabra técnica, explicala en una línea.
4. **No inventes reglas de negocio.** Si algo no está en este documento, preguntame. Si necesitás un valor para avanzar, ponelo en configuración, marcalo como `SUPUESTO` y agregalo a `PENDIENTES.md`.
5. **Commits chicos** con mensajes en español, si el proyecto usa git.
6. **No agregues dependencias** que no estén en la sección 4 sin preguntarme.

---

## 4. Tecnología (simple a propósito)

| Pieza | Decisión | Por qué |
|---|---|---|
| Lenguaje | HTML + CSS + JavaScript moderno (módulos ES) | Lo sabe cualquier programador web y funciona igual dentro de Apps Script |
| Framework | **Ninguno** (sin React, sin Vue, sin paso de compilación) | Menos cosas que aprender y mantener |
| 3D | **Three.js** desde CDN con *import map*, versión fija (por ejemplo `https://cdn.jsdelivr.net/npm/three@0.17x.x/...`), más `OrbitControls` | Es la librería 3D web más usada y documentada |
| Dibujo 2D acotado | SVG generado por código | Se imprime nítido y es fácil de leer |
| Datos (prototipo) | `localStorage` del navegador detrás de un módulo `almacenamiento.js` | Permite probar sin servidor |
| Configuración | Archivos JSON en `/datos` | El negocio los puede cambiar sin tocar código |
| Impresión | CSS de impresión (`@media print`, hoja A4) + `window.print()`; desde ahí se guarda como PDF | Sin librerías extra |
| Pruebas | `node --test` sobre los módulos de cálculo, que no deben depender del navegador | Viene incluido con Node |
| Servidor local | `npx serve .` o `python -m http.server` | Los módulos ES necesitan servirse por http |

**Regla de arquitectura:** separar en tres capas para poder migrar a Apps Script:

- `src/logica/` → cálculos puros (desarrollo, banda, código, geometría). Sin DOM, sin Three.js. Probados con `node --test`.
- `src/datos/almacenamiento.js` → única puerta para guardar y leer (notas, contadores, configuración). Hoy usa `localStorage`; mañana se reemplaza por llamadas a Apps Script (`google.script.run`) sin tocar el resto. Todas sus funciones son asíncronas (`async`) desde el principio.
- `src/pantallas/` y `src/vistas3d/` → interfaz.

---

## 5. Reglas de negocio confirmadas (no cambiar sin consultar)

### 5.1 Encabezado

- **Origen** = sucursal donde trabaja el vendedor. Viene precargada por defecto, con un selector para cambiarla si ese día trabaja en otra.
- **Número de nota (NP)**: correlativo **por sucursal**. En la nota se muestra **solo el número**, porque la sucursal ya figura en grande arriba. Cada sucursal tiene un "último número usado" configurable, para continuar desde el talonario de papel.
- **Fecha**: automática (fecha del día, formato dd/mm/aaaa).
- **Número de factura**: por ahora el vendedor lo pega a mano. Es obligatorio para emitir la nota.
- **Cliente**: texto libre, obligatorio.

### 5.2 Desarrollo

- **Desarrollo = suma simple de las medidas exteriores de todos los tramos, en centímetros.** No se descuenta nada por pliegue.
- Los dobladillos también suman. Ejemplo: 1 + 20 + 32 + 7 = **60**.
- Las medidas que se cargan son siempre **exteriores**. Mostrá un recordatorio visible: "Cargá medidas EXTERIORES".

### 5.3 Banda de cotización (chapa de 1,22 × 2,44 m; el 1,22 se usa para el desarrollo)

| Desarrollo (cm) | Banda | Número en el código |
|---|---|---|
| 0 < D ≤ 30 | 1/4 de chapa | 30 |
| 30 < D ≤ 60 | 1/2 chapa | 60 |
| 60 < D ≤ 120 | chapa completa | 120 |
| D > 120 | no entra | sin código + aviso **"Requiere soldar piezas"** |

- Si el desarrollo pasa el límite, **aunque sea por 0,1 cm**, sube a la banda siguiente.
- `SUPUESTO`: el límite superior es 120 aunque la chapa mida 122. Dejalo como parámetro `limiteChapaCompletaCm: 120` en `datos/config.json`.

### 5.4 Código del producto

- Estructura confirmada: **material + espesor + terminación + banda**. Ejemplo: `CG` + `05` + `P` + `60` = `CG05P60`.
- Los códigos reales **ya existen en el sistema de facturación**. El programa **no arma el código letra por letra**: lo **busca** en una tabla (`datos/codigos.json`) con las columnas `elemento`, `material`, `espesor`, `terminacion`, `banda` y `codigo`.
- Si no encuentra la combinación, muestra el aviso "Código no encontrado: avisar a administración" y no deja emitir la nota hasta que se corrija o se marque como "código pendiente".
- El tipo de elemento **también cambia el código**, pero todavía no sabemos cómo. `SUPUESTO`: en la tabla de ejemplo la columna `elemento` vale `"*"` (cualquiera). Cuando llegue la lista real, se reemplaza el archivo.
- Generá la tabla de ejemplo con un script `herramientas/generar-codigos-ejemplo.js` que combine materiales × espesores × terminaciones × bandas con el patrón confirmado. Tiene que incluir, sí o sí, `CG05P60`.

### 5.5 Renglones y piezas

- Una nota tiene **uno o varios renglones**. Cada renglón es una pieza con su propio dibujo, largo, material, calibre, color, desarrollo, código y cantidad.
- Un pedido puede incluir canaleta + tapa (izquierda o derecha) + boqueta. `SUPUESTO` (pendiente de confirmar): cada una es un renglón propio, con su código y cantidad, y la tapa y la boqueta se pueden **vincular** al renglón de la canaleta ("accesorio de renglón 1"). Además, en el 3D de la canaleta se ven montadas en su posición.
- En chapa **prepintada** se indica de qué lado va la pintura: "pintura afuera" o "pintura adentro". Así producción no pliega al revés.

### 5.6 Avisos (no bloquean, salvo que se indique)

- Desarrollo > 120 cm: "Requiere soldar". Bloquea el código.
- Largo de pieza > 244 cm: "Supera el largo de la chapa (2,44 m): requiere empalme". `SUPUESTO`: 244 cm según el largo de la chapa y una referencia de taller con plegadora de 244 cm. Configurable.
- Tramo con medida 0 o vacía, o ángulo fuera de rango: error que bloquea.
- Código no encontrado: bloquea la emisión (ver 5.4).

---

## 6. Modelo de la pieza dibujada (perfil por tramos)

El perfil se arma con **tramos rectos conectados**. Cada tramo tiene:

| Campo | Qué es | Valores |
|---|---|---|
| `medidaCm` | Largo exterior del tramo | número > 0. Aceptar coma decimal ("2,5") |
| `anguloPliegue` | Ángulo **interior** entre el tramo anterior y este | 1° a 179°. 90 = escuadra. Por defecto 90 (`SUPUESTO` pendiente de confirmar) |
| `sentido` | Hacia dónde dobla respecto del tramo anterior | `izquierda` / `derecha` |
| `tipo` | Clase de tramo | `normal`, `dobladillo` (doblez de 180° abierto), `dobladillo_aplastado` (doblez de 180° cerrado), `pestana_engrafe` |
| `observacion` | Texto libre corto | opcional |

- El primer tramo no tiene ángulo; tiene `direccionInicial` (arriba, abajo, izquierda o derecha, o un ángulo en grados).
- `dobladillo` y `dobladillo_aplastado` fijan el giro en 180° (vuelve sobre el tramo anterior). En el dibujo se separan con una luz visual chica (3 mm en el abierto, casi 0 en el aplastado), solo para que se vean; esa luz **no** suma al desarrollo.
- **Cálculo de la geometría** (en `src/logica/geometria.js`, puro y probado): se parte de (0,0) con la dirección inicial. Para cada tramo, la dirección gira `180 − anguloPliegue` grados hacia el `sentido` indicado, y se avanza `medidaCm`. El resultado es la lista de puntos 2D del perfil.
- La pieza tiene además: `largoCm`, `ladoPintura` (si es prepintada), `troquelado` (por ejemplo, cumbrera que copia la onda sinusoidal o trapezoidal) y `observacionesGenerales`.

---

## 7. Catálogo de piezas (datos de ejemplo tomados de internet)

Cargá esto en `datos/catalogo.json`. **Todas las medidas por defecto son `SUPUESTO`**: sirven para que el vendedor arranque con algo parecido y modifique. Producción tiene que validarlas.

### 7.1 Piezas plegadas (perfil por tramos → 3D por extrusión a lo largo del `largoCm`)

| Plantilla | Tramos por defecto (cm, ángulo interior, tipo) | Desarrollo | Referencia |
|---|---|---|---|
| Canaleta (ejemplo de nota real) | 1 dobladillo aplastado → 20 → 32 → 7, ángulos 90 | 60 | Nota real de la empresa |
| Canaleta americana chica | `SUPUESTO`: 1 dobl. aplastado → 8 → 9 (ángulo 100) → 10 → 5 | 33 | Desarrollos típicos de canaleta: 16, 25 y 33 cm |
| Canaleta galponera | `SUPUESTO`: 2 dobl. → 15 → 25 → 15 → 3 | 60 | Familia "galponera" (canaleta de gran sección para galpones) |
| Canaleta contramuro | `SUPUESTO`: 10 → 12 → 10 → 12 → 3 | 47 | Producto de mercado "contramuro" |
| Canaleta cuadrada / pecho paloma | `SUPUESTO`, a definir con producción | — | Modelos de mercado |
| Babeta ele 15×15 | 15 → 15 | 30 | Producto de mercado "babeta L 15×15" |
| Babeta ele 20×20 | 20 → 20 | 40 | Producto de mercado "babeta L 20×20" |
| Babeta cierre lateral 15×10 | 15 → 10 | 25 | Producto de mercado |
| Babeta sobre chapa (sinusoidal / trapezoidal / lisa) | `SUPUESTO`: 1 dobl. → 12 → 10 (ángulo 100) → 2 | 25 | Catálogo de la empresa y mercado |
| Cumbrera lisa 15×15 / 20×20 | 15 → 15 (o 20 → 20), ángulo = ángulo del techo, editable | 30 / 40 | Producto de mercado; variante troquelada para sinusoidal o trapezoidal |
| Media cumbrera | `SUPUESTO`: 15 → 15 (ángulo 120) | 30 | Catálogo de la empresa |
| Limahoya | `SUPUESTO`: 1 dobl. → 25 → 25 (ángulo 150) → 1 dobl. | 52 | Catálogo de la empresa |
| Cenefa lisa / alero | `SUPUESTO`: 1 dobl. → 20 → 3 | 24 | Catálogo de la empresa (las cenefas decorativas troqueladas son reventa: solo texto) |
| **Pieza especial libre** | Arranca vacía; el vendedor agrega tramos | suma | — |

### 7.2 Piezas especiales (3D paramétrico, no por extrusión)

Cada una tiene su formulario de parámetros y su generador 3D. Su desarrollo se calcula con una fórmula marcada `SUPUESTO` y el vendedor puede corregirlo a mano (queda registrado que fue manual).

| Pieza | Parámetros | Desarrollo (`SUPUESTO`) |
|---|---|---|
| Tapa de canaleta (izquierda o derecha) | Copia el perfil de la canaleta vinculada + pestaña de apoyo (cm) | Se cotiza por unidad; mostrar el perfil |
| Boqueta redonda | Ø del caño (3", 4", 5", 6" ≈ 7,5 / 10 / 12,5 / 15 cm), largo de la boca, pestaña, posición desde el extremo de la canaleta | π·Ø + solape de engrafe (parámetro, por defecto 1 cm) |
| Boqueta rectangular | Lados a×b (por ejemplo 10×5, 7,5×10), largo, pestaña, posición | 2·(a+b) + solape |
| Caño de bajada redondo / rectangular | Ø o a×b, largo | igual que la boqueta |
| Codo / curva | Ø, ángulo (45° o 90°), cantidad de gajos | Cotización por unidad |
| Ramal | Ø, ángulo (45° o 90°) | Cotización por unidad |
| Sombrero (chino o venturi) | Ø del caño (4", 6", 8"…) | Cotización por unidad |
| Embudo / tronera | Boca superior a×b, salida Ø, alto | Cotización por unidad |
| Reducción | Ø mayor → Ø menor | Cotización por unidad |

### 7.3 Materiales, calibres y colores (`datos/materiales.json`)

| Material | Código | Terminaciones |
|---|---|---|
| Chapa galvanizada | CG | `N` natural (`SUPUESTO`, la letra no está confirmada), `P` prepintada (confirmada) |
| Cincalum | `SUPUESTO` CZ | N |
| Acero inoxidable | `SUPUESTO` IN | N |
| Aluminio | `SUPUESTO` AL | N |
| Cobre | `SUPUESTO` CU | N |

| Calibre | Espesor (mm) | Código de espesor | Fuente |
|---|---|---|---|
| C30 | 0,30 | 03 | Informe del rubro; publicaciones de mercado |
| C28 | 0,36 | `SUPUESTO` 036 o 04 | Publicaciones de un taller porteño |
| C27 | 0,40 | 04 | Informe del rubro |
| C25 | 0,50 | 05 (confirmado) | Nota real e informe del rubro |
| C24 | ≈0,55–0,60 | `SUPUESTO` 06 | Tabla de chapas de la UNCuyo |
| C22 | 0,70 | 07 | Informe del rubro |
| C20 | ≈0,90 | `SUPUESTO` 09 | Tabla de chapas de la UNCuyo |

**Colores de prepintado (`SUPUESTO`, a confirmar con el stock real):** negro, rojo teja, gris, blanco y verde. Cada color tiene un valor hexadecimal para pintarlo en 3D. La cara no pintada se muestra gris claro.

### 7.4 Sucursales de ejemplo (`datos/sucursales.json`)

Colón, Juan B. Justo, Donato Álvarez, O'Higgins, Monseñor Pablo Cabrera, Parque Ferreyra, Francisco de Arteaga, Carlos Paz – Cárcano, Carlos Paz – San Martín y "Sucursal 10 (a definir)".

Cada una tiene `id`, `nombre`, `letra` (`SUPUESTO`: letras de ejemplo; las reales se usan para el nombre del archivo en Drive) y `ultimoNumeroNP` (arranca en 0, editable).

Vendedores de ejemplo: 3 por sucursal, con nombre ficticio y sucursal habitual. En el prototipo, el "ingreso" es elegir el vendedor de una lista. En la versión con Google será la cuenta de la empresa.

---

## 8. Pantallas y experiencia de uso

**Principios:** pocos clics, botones grandes, todo en español, sin jerga. Que funcione con mouse y con el dedo en el celular (diseño adaptable desde 360 px de ancho). Contraste alto. Cada término de zinguería tiene un ícono "?" con una explicación de una línea (glosario en `datos/glosario.json`).

### 8.1 Inicio

- Arriba: vendedor y sucursal actual, con un botón "Cambiar sucursal de hoy".
- Botón grande **"Nueva nota de pedido"**.
- Lista de las notas de la sucursal, con buscador por cliente, número o factura y filtro por fecha.
- Estados: borrador / emitida.

### 8.2 Nota de pedido

- **Encabezado:** origen y NP (el número se asigna al **emitir**, no al abrir, para no quemar números), fecha, factura y cliente.
- **Renglones:** tarjetas con una miniatura 3D, la descripción armada automáticamente (por ejemplo "2,44 mts canaleta pp negro D60 CH 25"), el código y la cantidad. Cada tarjeta tiene botones para editar, duplicar y eliminar (con confirmación).
- Botón **"Agregar pieza"** que abre el asistente.
- Botones **"Guardar borrador"** y **"Emitir nota"**. Emitir valida todo, asigna el número y abre la vista de impresión.
- Guardado automático del borrador cada pocos segundos.

### 8.3 Asistente "Agregar pieza" (3 pasos, con barra de progreso)

**Paso 1 – ¿Qué pieza?** Galería de tarjetas con una miniatura de cada plantilla, agrupadas en: Canaletas, Babetas, Cumbreras y limahoyas, Boquetas y caños, Tapas, Ventilación y "Pieza especial a medida". Tiene un buscador por nombre.

**Paso 2 – Medidas y dibujo.** Pantalla dividida (en celular, con pestañas "Medidas", "2D" y "3D"):

- **Tabla de tramos:** una fila por tramo con medida, ángulo, sentido, tipo y observación.
  - Enter pasa al campo siguiente.
  - `inputmode="decimal"` para que aparezca el teclado numérico en el celular.
  - Botones "Agregar tramo", "Insertar antes", "Borrar tramo", y deshacer/rehacer.
- **Dibujo 2D acotado (SVG):** el perfil en escala, con la medida escrita sobre cada tramo, el ángulo en cada pliegue si no es 90, el dobladillo marcado ("dobl." o "dobl. aplastado") y una flecha indicando el lado pintado. Al pasar el mouse o tocar un tramo de la tabla, se resalta en 2D y en 3D (y viceversa).
- **Dibujo a mano (opcional):** en el 2D, clic o toque para agregar puntos sobre una cuadrícula con imán a 1 cm y a ángulos de 15°. El programa convierte los puntos en tramos (medida y ángulo) y los muestra en la tabla para corregir.
- **Vista 3D (Three.js):** la pieza extruida al largo indicado, con rotación por arrastre, zoom, botón "Vista inicial" y vistas rápidas (frente, lateral, isométrica). Los colores siguen al material: galvanizado gris metálico; prepintado con el color en la cara pintada y gris en la otra. Si el renglón tiene tapa o boqueta vinculadas, se ven montadas. Los dobladillos se ven como pliegues de 180°. Una regla o etiqueta indica el largo.
- **Largo de la pieza** en metros (acepta "2,44").
- **Panel de resultados, siempre visible:** Desarrollo **D = 60 cm** · Banda **1/2 chapa (60)** · Código **CG05P60** (o el aviso que corresponda). Se actualiza en vivo.

**Paso 3 – Material y cantidad:** material, calibre, terminación, color (solo si es prepintada), lado de la pintura, cantidad y observaciones. Muestra el código final y un resumen. Botón "Agregar a la nota".

### 8.4 Vista de impresión (A4 vertical)

Respeta el esquema de la nota en papel:

- Sucursal en grande arriba a la izquierda; NP, fecha y factura a la derecha; cliente.
- Tabla con Descripción | Código | Cantidad.
- Debajo de cada renglón: el **dibujo 2D acotado** (la referencia oficial para fabricar), una **imagen 3D chica** como ayuda visual (captura del canvas con `preserveDrawingBuffer: true`) y las observaciones.
- Pie de página: vendedor, fecha y hora de emisión, y "Página X de Y".
- Si una pieza no entra, pasa a la página siguiente sin cortarse.
- Debe verse bien en blanco y negro: los colores no pueden ser la única forma de transmitir información.

### 8.5 Lista para producción

- Notas emitidas, con filtros por sucursal y fecha y búsqueda por número o cliente.
- Botón para abrir e imprimir cada nota.
- (Etapa 2, no ahora: estados "pendiente / en producción / terminado / entregado".)

### 8.6 Configuración (pantalla simple, protegida con una clave fija de prototipo)

Permite editar sucursales y último número por sucursal, y ver las tablas de códigos, materiales y plantillas. También permite importar `codigos.json` o un CSV desde archivo, para cuando llegue la lista real del sistema de facturación.

---

## 9. Estructura de carpetas sugerida

```
/
├─ index.html
├─ README.md               ← cómo ejecutar, probar y modificar (en lenguaje simple)
├─ PENDIENTES.md           ← lista de todos los SUPUESTOS a validar con la empresa
├─ datos/
│  ├─ config.json          ← límites (bandas, largo máximo, solape de engrafe…)
│  ├─ sucursales.json
│  ├─ vendedores.json
│  ├─ materiales.json
│  ├─ catalogo.json        ← plantillas de piezas
│  ├─ codigos.json         ← tabla de códigos (de ejemplo)
│  └─ glosario.json
├─ src/
│  ├─ logica/              ← puro, sin navegador: desarrollo, banda, código, geometría, numeración, formato de descripción, validaciones
│  ├─ datos/almacenamiento.js
│  ├─ pantallas/           ← inicio, nota, asistente, impresión, producción, configuración
│  ├─ vistas2d/            ← SVG acotado
│  ├─ vistas3d/            ← escena, extrusión de perfiles, piezas especiales
│  └─ estilos/
├─ herramientas/generar-codigos-ejemplo.js
└─ tests/                  ← node --test
```

---

## 10. Etapas de trabajo (mostrame el resultado de cada una)

| Etapa | Qué se construye | Cómo sé que está bien |
|---|---|---|
| A | Estructura, archivos de datos de ejemplo, `src/logica` completo y pruebas | `node --test` en verde con todos los casos de la sección 11 |
| B | Paso 2 del asistente: tabla de tramos y dibujo 2D acotado, con resultados en vivo | Reproduzco la canaleta de la nota real y da D60, CG05P60 |
| C | Vista 3D de piezas plegadas (extrusión) sincronizada con la tabla | Veo la canaleta en 3D, la giro, y al tocar un tramo se resalta |
| D | Piezas especiales 3D (tapa, boqueta, caño, codo, sombrero, embudo) y vínculo con la canaleta | La canaleta muestra su tapa izquierda y su boqueta en la posición cargada |
| E | Nota completa: encabezado, renglones, borrador, emisión con numeración por sucursal, vista de impresión A4 | Imprimo a PDF una nota igual a la de papel, pero prolija |
| F | Inicio, búsqueda, lista para producción y configuración | Encuentro una nota por cliente; producción la abre e imprime |
| G | README, `PENDIENTES.md` y una guía de prueba de 10 minutos para un vendedor | Alguien sin experiencia lo ejecuta siguiendo el README |

**Fuera de alcance ahora (dejalo anotado en el README como "próximos pasos"):** conexión a Apps Script + Sheets + Drive, ingreso con Google, estados de producción, integración con facturación y trabajo sin internet con sincronización.

---

## 11. Casos de prueba obligatorios (automáticos)

| # | Entrada | Resultado esperado |
|---|---|---|
| 1 | Tramos 1 (dobl. aplastado), 20, 32, 7 | Desarrollo 60 |
| 2 | Desarrollo 60, galvanizado prepintado, C25 | Banda 60, código `CG05P60` |
| 3 | Desarrollo 20 | Banda 30 |
| 4 | Desarrollo 30 | Banda 30 |
| 5 | Desarrollo 30,1 | Banda 60 |
| 6 | Desarrollo 60,5 | Banda 120 |
| 7 | Desarrollo 120 | Banda 120 |
| 8 | Desarrollo 120,1 | Sin banda, aviso "Requiere soldar" |
| 9 | Medida "2,5" (coma) | Se interpreta 2,5 |
| 10 | Tramo con medida 0 | Error de validación |
| 11 | Largo 2,45 m | Aviso de empalme (no bloquea) |
| 12 | Combinación sin código en la tabla | Aviso "Código no encontrado" y emisión bloqueada |
| 13 | Dos notas emitidas en Colón y una en O'Higgins | Colón 1 y 2; O'Higgins 1 (los contadores son independientes) |
| 14 | Último número de Colón configurado en 4520 | Próxima nota de Colón: 4521 |
| 15 | Geometría: 10 hacia arriba, luego 10 con ángulo 90 a la derecha | Puntos (0,0) → (0,10) → (10,10) |
| 16 | Descripción automática | "2,44 mts canaleta pp negro D60 CH 25" |

---

## 12. Lo que NO tenés que hacer

- No agregues frameworks ni paso de compilación.
- No armes códigos de producto por concatenación como fuente de verdad: siempre se busca en la tabla.
- No descuentes nada por pliegue en el desarrollo.
- No escondas los supuestos: cada uno va a configuración y a `PENDIENTES.md`.
- No pongas datos reales de clientes en los ejemplos.
- No uses `localStorage` directamente fuera de `almacenamiento.js`.

---

## 13. PENDIENTES iniciales (copiar a `PENDIENTES.md`)

1. ¿Tapa y boqueta van en renglón propio o como detalle del renglón de la canaleta?
2. ¿El ángulo por defecto es 90°? ¿Siempre se anota?
3. ¿Se marca siempre el lado de la pintura en prepintado?
4. ¿Hay otras marcas de tramo además de dobladillo y aplastamiento (pestaña para engrafar, tapa izquierda o derecha)?
5. Un desarrollo de 121 o 122 cm, ¿entra en "chapa completa" o va soldado?
6. ¿Cómo cambia el código según el tipo de elemento? Pedir la lista real de códigos.
7. Letra de terminación para galvanizado sin pintar, y códigos de cincalum, inoxidable, aluminio y cobre.
8. Código de espesor para C28, C24 y C20.
9. Colores de prepintado disponibles en stock.
10. Medidas reales de las plantillas (canaleta americana, galponera, contramuro, limahoya, etc.).
11. Fórmula de desarrollo de boquetas y caños (solape de engrafe).
12. Letra de cada sucursal y último número de talonario de cada una.
13. Largo máximo real de las plegadoras de la empresa.

---

## 14. Fuentes de los datos de ejemplo

- Nota de pedido real de la empresa y respuestas del área comercial (reglas de las secciones 5.1 a 5.4).
- Informe "Proceso productivo de la zinguería y la chapa" (6/10/2026): calibres C30, C27, C25 y C22, materiales, piezas típicas y largo máximo de plegado de 244 cm en un taller de referencia.
- Catálogo online de la empresa – Plegados y cortes (babetas, cumbreras, media cumbrera, limahoya, troneras, boquetas): https://abastosoluciones.com.ar/7-plegados-y-cortes
- Catálogo online de la empresa – Zinguería para techos (babeta sinusoidal y trapezoidal, cenefas): https://abastosoluciones.com.ar/4-zingueria-para-techos
- Catálogo online de la empresa – Caños, codos y curvas (caños de chapa N°30 y N°25, rectangulares, curvas, ramales de 45° y 90°, inoxidable 0,5 mm): https://abastosoluciones.com.ar/6-canos-codos-y-curvas
- Tienda Rapimetal en Mercado Libre (calibres C25 = 0,50 mm, C28 = 0,36 mm y C30 = 0,30 mm; babetas, cumbreras lisas 15×15 y 20×20; grampa para caño rectangular 10×5): https://www.mercadolibre.com.ar/tienda/rapimetal
- Listados de cenefas y babetas L 15×15 y 20×20 en prepintado negro C25: https://listado.mercadolibre.com.ar/cenefa
- Tienda GEA Zinguería (canaleta media caña, cuadrada, pecho paloma y contramuro; venturi de 8" = 20 cm): https://www.mercadolibre.com.ar/pagina/geazingueria
- Grampas de caño en pulgadas (3" = 7,5 cm, 4" = 10 cm, 5" = 12,5 cm, 6" = 15 cm…): https://www.mercadolibre.com.ar/tienda/zingueriagea/clips
- Guía Leroy Merlin: desarrollos de canalón de 16, 25 y 33 cm según la superficie del techo: https://biblioteca.org.ar/libros/210136.pdf
- Tabla de chapas de acero, Facultad de Ingeniería – UNCuyo (espesores por calibre): https://aulaabierta.ingenieria.uncuyo.edu.ar/mod/resource/view.php?id=6819
- Documentación de Three.js – ExtrudeGeometry: https://threejs.org/docs/pages/ExtrudeGeometry.html
