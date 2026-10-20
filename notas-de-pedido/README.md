# Notas de pedido – Abasto Soluciones (prototipo)

Programa web que reemplaza la nota de pedido en papel. El vendedor:

1. completa el encabezado casi sin escribir (origen, fecha y número salen solos; la factura se pega);
2. elige la pieza de una galería con los productos que fabrica la empresa (canaletas con sus tapas y boquetas, babetas, cumbreras, limahoya, cenefas, chapa lisa, boquetas, troneras, caños, curvas, codos, ramales, tapas y sombreros circulares o rectangulares), o dibuja una a mano;
3. carga las medidas en una tabla y ve **al mismo tiempo** el dibujo 2D acotado y la pieza en 3D **con todas sus cotas**; si prefiere, abre el **editor 3D** a pantalla completa (también en el celular) y cambia las medidas tocando las cotas, agrega tramos con "+" o borra la parte que elija;
   los plegados pueden ser **con pendiente**: se cargan las medidas de las dos puntas y el 3D muestra cómo cambia la pieza a lo largo;
4. obtiene solo el **desarrollo**, la **banda** y el **código** (de la tabla de facturación o, si el producto no está, un código genérico como CL1010N);
5. elige material, calibre, color y cantidad;
6. emite e imprime (o guarda en PDF) una nota prolija para producción.

> **Para probarlo en 10 minutos:** seguí [`GUIA-PRUEBA-10-MIN.md`](GUIA-PRUEBA-10-MIN.md).
> **Lo que falta confirmar con la empresa:** [`PENDIENTES.md`](PENDIENTES.md).

---

## Atajos de teclado

**F1** muestra en cualquier pantalla la lista de atajos disponibles en ese momento. Cada botón tiene su atajo escrito al lado.

| Dónde | Atajo | Qué hace |
|---|---|---|
| Inicio | Alt+N | Nueva nota de pedido |
| Inicio | Alt+K | Ir al buscador de notas |
| Nota | Alt+P | Agregar pieza |
| Nota | Ctrl+S | Guardar borrador |
| Nota | Ctrl+Enter | Emitir nota |
| Asistente | Alt+flecha derecha / Alt+flecha izquierda | Paso siguiente (o "Agregar a la nota") / paso anterior |
| Asistente | Esc | Cerrar el asistente |
| Tabla de tramos | Alt+T / Alt+I / Alt+B | Agregar tramo / insertar antes / borrar tramo |
| Tabla de tramos | Ctrl+Z / Ctrl+Y | Deshacer / rehacer |
| Tabla de tramos | Alt+1 / Alt+2 | Aleta al inicio / aleta al final |
| Tabla de tramos | Alt+3 / Alt+4 | Dobladillo al inicio / dobladillo al final |
| Tabla de tramos | Alt+J / Alt+M | Espejar / dibujar a mano |
| Canaleta | Alt+Q | Agregar boqueta |
| Vista 3D | Alt+0 / Alt+7 / Alt+8 / Alt+9 | Vista inicial / frente / lateral / isométrica |
| Vista 3D | Alt+C | Mostrar u ocultar las cotas |
| Vista 3D | Alt+G | Abrir el editor 3D a pantalla completa (Alt+G o Esc lo cierran) |
| Plegados | Alt+L | Con pendiente sí / no |
| Editor 3D | Supr | Borrar el tramo, la tapa o la boqueta elegida |
| Editor 3D | Alt+flecha derecha / Alt+flecha izquierda | Elegir el tramo siguiente / anterior |
| Cota en el 3D | Enter / Esc | Confirmar la medida nueva / dejarla como estaba |
| Todas | Enter | Pasar al campo siguiente |

No se usaron Alt+F, Alt+E ni Alt+D porque Chrome y Edge los usan para sus menús.

---

## 1. Cómo abrirlo (paso a paso)

### Qué hace falta

- Una computadora con **Chrome o Edge** (recomendados para imprimir con "Página X de Y").
- **Internet**, para que se vea el 3D (Three.js se baja de internet). Sin internet funciona todo menos el 3D.
- Uno de estos dos programas, solo para "servir" la página:
  - **Node.js** 20 o más nuevo (https://nodejs.org), o
  - **Python 3** (en Linux y Mac suele venir instalado).

> ¿Por qué un "servidor"? El navegador no deja cargar los archivos del programa con doble clic en `index.html`: necesita que se los entregue un servidor, aunque sea uno local en tu misma PC.

### Pasos

1. Abrí una terminal (en Windows: "Símbolo del sistema" o "PowerShell").
2. Entrá a la carpeta del programa:
   ```bash
   cd notas-de-pedido
   ```
3. Arrancá el servidor (elegí **uno**):
   ```bash
   npx serve .                  # con Node.js  → abre en http://localhost:3000
   python3 -m http.server 8000  # con Python   → abre en http://localhost:8000
   ```
4. Abrí en el navegador la dirección que aparece en la terminal.
5. Elegí tu nombre de la lista y tocá **Entrar**.

Para cerrarlo, en la terminal apretá `Ctrl + C`.

### Usarlo desde el celular

Con la PC y el celular en el mismo wifi, en el celular abrí `http://IP-DE-LA-PC:8000`. La IP de la PC se ve con `ipconfig` en Windows o con `ip addr` en Linux. Ojo: el celular guarda **sus propias** notas (ver "Dónde se guardan los datos").

---

## 2. Cómo correr las pruebas automáticas

```bash
cd notas-de-pedido
npm test          # es lo mismo que:  node --test
```

Tiene que terminar con `# fail 0`. Hay 101 pruebas; los **16 casos obligatorios** de la especificación están en `tests/casos-obligatorios.test.js`. Las pruebas no usan el navegador: prueban la lógica (`src/logica/`), el almacenamiento (con un "navegador falso" en memoria) y los dibujos 2D.

---

## 3. Cómo está hecho (para el programador que lo mantenga)

Sin frameworks y sin "paso de compilación": HTML + CSS + JavaScript moderno (módulos ES). Lo que se escribe es lo que corre.

### Las tres capas

| Capa | Carpeta | Qué hace | Regla |
|---|---|---|---|
| Lógica | `src/logica/` | Cálculos puros: desarrollo, banda, código, geometría, cotas, pendiente, corte láser, descripción, validaciones, numeración | No usa el navegador ni Three.js. Todo se prueba con `node --test` |
| Datos | `src/datos/almacenamiento.js` | **Única puerta** para guardar y leer | Nadie más usa `localStorage`. Todas sus funciones son `async` |
| Interfaz | `src/pantallas/`, `src/vistas2d/`, `src/vistas3d/`, `src/estilos/` | Pantallas, dibujos 2D (SVG) y 3D (Three.js) | Llama a la lógica y al almacenamiento; no calcula reglas de negocio |

### Archivos principales

```
index.html                     página única (las pantallas cambian con #inicio, #nota/…, #imprimir/…)
src/app.js                     arranque y elección de pantalla según la dirección
.
recursos/logo.png              logo oficial de Abasto Soluciones
src/pantallas/
  atajos.js                    atajos de teclado (F1 muestra la lista)
  inicio.js                    ingreso (elegir vendedor) e inicio (lista de notas de la sucursal)
  nota.js                      nota de pedido: encabezado, renglones, autoguardado, emisión
  asistente.js                 "Agregar pieza" en 3 pasos (galería → medidas y dibujo → material)
  editorTramos.js              tabla de tramos (Enter, deshacer/rehacer, atajos, corte láser, columnas de la punta final)
  editor3d.js                  editor 3D a pantalla completa: herramientas, propiedades de la parte elegida, resumen
  impresion.js                 hoja A4 para imprimir o guardar en PDF
  produccion.js                lista de notas emitidas para el taller
  configuracion.js             sucursales, último número, importar códigos, copias de seguridad
  util.js, estado.js           herramientas chicas y datos compartidos
src/vistas2d/
  perfilSvg.js                 dibujo 2D acotado del perfil (referencia oficial para fabricar)
  corteLaserSvg.js             vista de frente de la cara con corte láser
  especialSvg.js               esquemas acotados de boquetas, caños, codos, sombreros…
  plantaCanaletaSvg.js         vista desde arriba de la canaleta con tapas y boquetas acotadas
  pendienteSvg.js              vista de costado de un plegado con pendiente (alturas exageradas)
  dibujoAMano.js               cuadrícula con imán para dibujar el perfil
src/vistas3d/
  cargar3d.js                  carga el 3D solo si hay internet (si no, el programa sigue igual)
  escena.js                    visor 3D (girar, zoom, vistas, resaltar, cotas que se editan en el lugar, foto)
  cotas3d.js                   líneas de cota y textos del 3D (perfil, ángulos, largo, boquetas, piezas especiales)
  extrusion.js                 piezas plegadas: cada tramo es una chapa estirada a lo largo (o, con pendiente, de un perfil al otro)
  piezasEspeciales3d.js        caños, boquetas, codos, ramales, sombreros, troneras, tapas
  modelo.js                    junta pieza + tapas y boquetas puestas + regla del largo
  capturas.js                  fotos 3D para tarjetas e impresión (un solo dibujador)
  encuadre.js, materiales3d.js cámara y colores
src/logica/                    (ver tabla de arriba)
datos/*.json                   configuración del negocio (ver sección 4)
herramientas/generar-codigos-ejemplo.js
tests/                         pruebas automáticas
docs/ESPECIFICACION.md         la especificación original
```

### Cómo fluye un cálculo

`calcularRenglon(renglon, datos)` (en `src/logica/calculoRenglon.js`) hace todo en orden: **desarrollo** (suma de tramos; con pendiente, el mayor de las dos puntas; o fórmula en piezas especiales) → **banda** (`banda.js`) → **código** (lo **busca** en la tabla, `codigos.js`) → **descripción** (`descripcion.js`) → **errores y avisos** (`validaciones.js`, `corteLaser.js`). El panel de resultados del asistente, las tarjetas de la nota y la impresión usan esa misma función.

---

## 4. Cómo cambiar cosas sin programar (archivos de `datos/`)

| Quiero… | Archivo | Qué tocar |
|---|---|---|
| Cambiar los límites de banda (30/60/120) | `config.json` | `bandas` |
| Cambiar el largo máximo (aviso de empalme) | `config.json` | `largoMaximoChapaCm` |
| Cambiar los mínimos del corte láser (3,6 cm) | `config.json` | `corteLaser.anchoMinimoCaraCm`, `corteLaser.alturaMinimaOndaCm` |
| Cambiar el solape de caños y boquetas | `config.json` | `solapeEngrafeCm` |
| Cambiar la clave de Configuración | `config.json` | `claveConfiguracion` |
| Agregar un color de prepintado | `materiales.json` | copiar una línea de `colores` y cambiar `id`, `nombre` y `hex` |
| Cambiar el código de espesor de un calibre | `materiales.json` | `calibres` → `codigoEspesor` |
| Agregar una pieza a la galería | `catalogo.json` | copiar una plantilla parecida, cambiarle el `id` (único) y las medidas |
| Poner la lista real de códigos | pantalla **Configuración → Códigos → Importar** (CSV o JSON), o reemplazar `codigos.json` | columnas `elemento, material, espesor, terminacion, banda, codigo` |
| Agregar un término al glosario ("?") | `glosario.json` | copiar una línea |
| Cambiar el logo | `recursos/logo.png` | reemplazar el archivo con el mismo nombre (o poner otro y cambiar `marca.logo` en `config.json`) |
| Poner los nombres reales de los vendedores | `vendedores.json` | cambiar `nombre` (hoy "Vendedor 1", "Vendedor 2"…) |
| Cambiar las opciones del lado de la pintura | `config.json` | `ladosPintura` (afuera, adentro, los dos lados) |
| Poner los colores de la empresa | `config.json` | `marca` → `colorPrincipal`, `colorPrincipalOscuro`, `colorAcento` |
| Cambiar cómo se arma el código genérico | `catalogo.json` y `materiales.json` | `codigoGenerico` de cada producto (siglas y medidas) y `letraCodigoGenerico` de colores y materiales |

> Después de tocar un `.json`, recargá la página. Si algo deja de andar, seguramente quedó una coma de más o de menos: los JSON son muy estrictos.

**Cómo es una plantilla plegada:** `perfil.direccionInicial` es hacia dónde arranca el tramo 1 (`"arriba"`, `"abajo"`, `"izquierda"`, `"derecha"` o grados). Cada tramo tiene `medidaCm`, `anguloPliegue` (ángulo interior: 90 = escuadra), `sentido` (`izquierda` = gira antihorario, `derecha` = horario), `tipo` (`normal`, `dobladillo`, `dobladillo_aplastado` o `pestana_engrafe`) y `corteLaser` (`null` o `{ "tipo": "sinusoidal", "alturaOndaCm": 3.6, "separacionVallesCm": 7.6 }`).

**Canaletas con tapas y boquetas:** las plantillas con `"admiteAccesorios": true` muestran, debajo de la tabla, la tapa izquierda y la derecha (ninguna, soldada o engrampada) y las boquetas (forma redonda, cuadrada o rectangular, medida, largo de la boca y posición desde la punta izquierda). Todo queda en el mismo renglón de la canaleta.

**Código genérico:** `"codigoGenerico": { "siglas": "CL", "medidas": ["tramo1", "largoCm"] }` arma CL + 10 + 10 + letra (N si es prepintada negra). Las medidas pueden ser un parámetro (`diametroCm`), `tramo1`, `largoCm` o `desarrolloPerfil`. Con `siglasPorForma` y `medidasPorForma` cambian según la forma elegida. Primero siempre se busca en la tabla una fila para ese elemento.

**Cómo es una plantilla especial:** `calculoDesarrollo` es uno de `perimetroRedondo`, `perimetroRectangular`, `perimetroSegunForma`, `mediaCana` o `unidad`; `generador3d` es el nombre del dibujo 3D (ver `GENERADORES` en `piezasEspeciales3d.js`); `parametros` es la lista de medidas que se piden; `textoDescripcion` lleva `{nombreDelParametro}` para armar la descripción, por ejemplo `"codo {anguloGrados}° Ø{diametroCm}"`.

---

## 5. Dónde se guardan los datos (importante en el prototipo)

El prototipo guarda las notas **en el navegador de cada equipo** (localStorage). Eso quiere decir que:

- cada PC o celular tiene **sus propias** notas y su **propia** numeración;
- si se borran los datos del navegador, se pierden las notas: en **Configuración → Datos** se puede bajar una copia de seguridad;
- los borradores se guardan solos cada 5 segundos, y también la pieza que se está cargando. Si se corta la luz o internet, al volver a abrir la nota aparece "Quedó una pieza sin terminar → Recuperarla".

Esto se resuelve en la versión con Google (ver "Próximos pasos").

---

## 6. Problemas comunes

| Problema | Solución |
|---|---|
| La página queda en blanco o dice "No se pudieron cargar los datos" | La abriste con doble clic. Usá el servidor (sección 1) |
| No aparece el 3D | No hay internet, o el navegador bloquea WebGL. El resto funciona igual y el 2D es la referencia oficial |
| No sale "Página X de Y" al imprimir | Imprimí desde Chrome o Edge (Firefox no muestra esos pies de página) |
| La impresión sale con encabezados del navegador (fecha, dirección) | En la ventana de impresión, "Más opciones" → destildá "Encabezados y pies de página" |
| Se cambió la tabla de códigos y una nota vieja muestra otro código | No pasa: al emitir, la nota guarda una "foto" de su descripción y su código |

---

## 7. Próximos pasos (fuera del alcance de este prototipo)

1. **Conexión a Google Apps Script + Sheets + Drive.** Reemplazar el interior de `src/datos/almacenamiento.js` por llamadas a `google.script.run` (cada función ya es `async`, así que las pantallas no cambian). Las notas van a una hoja de Sheets y el PDF a una carpeta de Drive, nombrado con la letra de la sucursal y el número.
2. **Numeración segura entre varios vendedores:** el número se asigna en el servidor con `LockService`, un candado para que dos vendedores que emiten a la vez no saquen el mismo número.
3. **Ingreso con la cuenta de Google** de la empresa, en lugar de elegir el nombre de una lista.
4. **Estados de producción:** pendiente, en producción, terminado y entregado.
5. **Integración con el sistema de facturación**, para traer la factura y los códigos automáticamente.
6. **Trabajo sin internet con sincronización** posterior.

---

## 8. Fuentes de los datos de ejemplo

Todas las fuentes están en la sección 14 de `docs/ESPECIFICACION.md` y cada plantilla tiene su campo `referencia` en `datos/catalogo.json`. Las principales:

- Nota de pedido real de la empresa: reglas de desarrollo, banda y código, y el ejemplo CG05P60. Ejemplo de código genérico (CL1010N): área comercial.
- Productos que fabrica la empresa: [plegados y cortes](https://abastosoluciones.com.ar/7-plegados-y-cortes), [zinguería para techos](https://abastosoluciones.com.ar/4-zingueria-para-techos), [caños, codos y curvas](https://abastosoluciones.com.ar/6-canos-codos-y-curvas), [sombreros](https://abastosoluciones.com.ar/30-sombreros) y [productos marca Abasto](https://abastosoluciones.com.ar/brand/4-abasto). Se relevaron con un buscador web porque el sitio no se pudo abrir directo desde el entorno de desarrollo.
- Artículos de reventa (ronda 5): [zinguería](https://abastosoluciones.com.ar/3-zingueria), [línea gas](https://abastosoluciones.com.ar/5-linea-gas), [cenefa punta de lis](https://abastosoluciones.com.ar/zingueria/81-cenefa-punta-de-lis-2-mt.html) y [embudo colector moldura](https://abastosoluciones.com.ar/zingueria/84-embudo-colector-moldura.html).
- Tiendas de zinguería en Mercado Libre, con calibres, babetas, cumbreras, canaletas y venturi: [Rapimetal](https://www.mercadolibre.com.ar/tienda/rapimetal), [GEA Zinguería](https://www.mercadolibre.com.ar/pagina/geazingueria), [grampas en pulgadas](https://www.mercadolibre.com.ar/tienda/zingueriagea/clips) y [listado de cenefas](https://listado.mercadolibre.com.ar/cenefa).
- [Tapa de canaleta izquierda (Easy)](https://www.easy.com.ar/tapa-moldura-d-embut-ch-gv-nº30-15-cm-iz/p).
- [Guía Leroy Merlin de canalones](https://biblioteca.org.ar/libros/210136.pdf) y [tabla de chapas de la UNCuyo](https://aulaabierta.ingenieria.uncuyo.edu.ar/mod/resource/view.php?id=6819).
- Documentación de Three.js: [ExtrudeGeometry](https://threejs.org/docs/pages/ExtrudeGeometry.html), [OrbitControls](https://threejs.org/docs/#examples/en/controls/OrbitControls) y [OrthographicCamera](https://threejs.org/docs/#api/en/cameras/OrthographicCamera) (vistas de frente y lateral sin perspectiva).
- Editor 3D y plegados con pendiente (chapa entre dos perfiles): [Autodesk Inventor – Lofted Flange](https://help.autodesk.com/cloudhelp/2026/ENU/Inventor-Help/files/GUID-B6271A15-FD68-4672-9461-C86F8D55DA87.htm), [Inventor – lofted flange de plegadora](https://help.autodesk.com/cloudhelp/2014/ENU/Inventor/files/GUID-85FE3FCA-16B6-4310-B900-925291A73FA1.htm), [Onshape – Sheet Metal Loft](https://cad.onshape.com/help/es/Content/PartStudio/sheet_metal_loft.htm) y [Onshape – Loft (misma cantidad de vértices en los dos perfiles)](https://cad.onshape.com/help/Content/loft.htm?cshid=loft).
- Pendientes de canaletas como referencia (no se aplicó ningún mínimo): [Victorian Building Authority – Box Gutters (1:200 a 1:40)](https://www.bpc.vic.gov.au/__data/assets/pdf_file/0009/22005/Plumbing_RP-02_Box-Gutters_CURRENT_01-Aug-2023.pdf) y [BRANZ – Internal gutter design](https://prod.branz.co.nz/documents/3986/BU556-Internal-gutter-design.pdf).
