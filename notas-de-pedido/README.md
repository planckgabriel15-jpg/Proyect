# Notas de pedido – Zinguería (prototipo)

Programa web que reemplaza la nota de pedido en papel. El vendedor:

1. completa el encabezado casi sin escribir (origen, fecha y número salen solos; la factura se pega);
2. elige la pieza de una galería (50 plantillas: canaletas, babetas, cumbreras, cenefas, perfiles, boquetas, caños, codos, sombreros…) o dibuja una a mano;
3. carga las medidas en una tabla y ve **al mismo tiempo** el dibujo 2D acotado y la pieza en 3D;
4. obtiene solo el **desarrollo**, la **banda** y el **código**;
5. elige material, calibre, color y cantidad;
6. emite e imprime (o guarda en PDF) una nota prolija para producción.

> **Para probarlo en 10 minutos:** seguí [`GUIA-PRUEBA-10-MIN.md`](GUIA-PRUEBA-10-MIN.md).
> **Lo que falta confirmar con la empresa:** [`PENDIENTES.md`](PENDIENTES.md).

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

Tiene que terminar con `# fail 0`. Hay 71 pruebas; los **16 casos obligatorios** de la especificación están en `tests/casos-obligatorios.test.js`. Las pruebas no usan el navegador: prueban la lógica (`src/logica/`), el almacenamiento (con un "navegador falso" en memoria) y los dibujos 2D.

---

## 3. Cómo está hecho (para el programador que lo mantenga)

Sin frameworks y sin "paso de compilación": HTML + CSS + JavaScript moderno (módulos ES). Lo que se escribe es lo que corre.

### Las tres capas

| Capa | Carpeta | Qué hace | Regla |
|---|---|---|---|
| Lógica | `src/logica/` | Cálculos puros: desarrollo, banda, código, geometría, corte láser, descripción, validaciones, numeración | No usa el navegador ni Three.js. Todo se prueba con `node --test` |
| Datos | `src/datos/almacenamiento.js` | **Única puerta** para guardar y leer | Nadie más usa `localStorage`. Todas sus funciones son `async` |
| Interfaz | `src/pantallas/`, `src/vistas2d/`, `src/vistas3d/`, `src/estilos/` | Pantallas, dibujos 2D (SVG) y 3D (Three.js) | Llama a la lógica y al almacenamiento; no calcula reglas de negocio |

### Archivos principales

```
index.html                     página única (las pantallas cambian con #inicio, #nota/…, #imprimir/…)
src/app.js                     arranque y elección de pantalla según la dirección
src/pantallas/
  inicio.js                    ingreso (elegir vendedor) e inicio (lista de notas de la sucursal)
  nota.js                      nota de pedido: encabezado, renglones, autoguardado, emisión
  asistente.js                 "Agregar pieza" en 3 pasos (galería → medidas y dibujo → material)
  editorTramos.js              tabla de tramos (Enter, deshacer/rehacer, atajos, corte láser)
  impresion.js                 hoja A4 para imprimir o guardar en PDF
  produccion.js                lista de notas emitidas para el taller
  configuracion.js             sucursales, último número, importar códigos, copias de seguridad
  util.js, estado.js           herramientas chicas y datos compartidos
src/vistas2d/
  perfilSvg.js                 dibujo 2D acotado del perfil (referencia oficial para fabricar)
  corteLaserSvg.js             vista de frente de la cara con corte láser
  especialSvg.js               esquemas acotados de boquetas, caños, codos, sombreros…
  dibujoAMano.js               cuadrícula con imán para dibujar el perfil
src/vistas3d/
  cargar3d.js                  carga el 3D solo si hay internet (si no, el programa sigue igual)
  escena.js                    visor 3D (girar, zoom, vistas, resaltar tramo, foto)
  extrusion.js                 piezas plegadas: cada tramo es una chapa estirada a lo largo
  piezasEspeciales3d.js        caños, boquetas, codos, ramales, sombreros, embudos, tapas
  modelo.js                    junta pieza + accesorios montados + regla del largo
  capturas.js                  fotos 3D para tarjetas e impresión (un solo dibujador)
  encuadre.js, materiales3d.js cámara y colores
src/logica/                    (ver tabla de arriba)
datos/*.json                   configuración del negocio (ver sección 4)
herramientas/generar-codigos-ejemplo.js
tests/                         pruebas automáticas
docs/ESPECIFICACION.md         la especificación original
```

### Cómo fluye un cálculo

`calcularRenglon(renglon, datos)` (en `src/logica/calculoRenglon.js`) hace todo en orden: **desarrollo** (suma de tramos, o fórmula en piezas especiales) → **banda** (`banda.js`) → **código** (lo **busca** en la tabla, `codigos.js`) → **descripción** (`descripcion.js`) → **errores y avisos** (`validaciones.js`, `corteLaser.js`). El panel de resultados del asistente, las tarjetas de la nota y la impresión usan esa misma función.

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

> Después de tocar un `.json`, recargá la página. Si algo deja de andar, seguramente quedó una coma de más o de menos: los JSON son muy estrictos.

**Cómo es una plantilla plegada:** `perfil.direccionInicial` es hacia dónde arranca el tramo 1 (`"arriba"`, `"abajo"`, `"izquierda"`, `"derecha"` o grados). Cada tramo tiene `medidaCm`, `anguloPliegue` (ángulo interior: 90 = escuadra), `sentido` (`izquierda` = gira antihorario, `derecha` = horario), `tipo` (`normal`, `dobladillo`, `dobladillo_aplastado` o `pestana_engrafe`) y `corteLaser` (`null` o `{ "tipo": "sinusoidal", "alturaOndaCm": 3.6, "separacionVallesCm": 7.6 }`).

**Cómo es una plantilla especial:** `calculoDesarrollo` es uno de `perimetroRedondo`, `perimetroRectangular`, `mediaCana` o `unidad`; `generador3d` es el nombre del dibujo 3D (ver `GENERADORES` en `piezasEspeciales3d.js`); `parametros` es la lista de medidas que se piden; `textoDescripcion` lleva `{nombreDelParametro}` para armar la descripción, por ejemplo `"codo {anguloGrados}° Ø{diametroCm}"`.

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

- Nota de pedido real de la empresa: reglas de desarrollo, banda y código, y el ejemplo CG05P60.
- Catálogo online de la empresa: [plegados y cortes](https://abastosoluciones.com.ar/7-plegados-y-cortes), [zinguería para techos](https://abastosoluciones.com.ar/4-zingueria-para-techos) y [caños, codos y curvas](https://abastosoluciones.com.ar/6-canos-codos-y-curvas).
- Tiendas de zinguería en Mercado Libre, con calibres, babetas, cumbreras, canaletas y venturi: [Rapimetal](https://www.mercadolibre.com.ar/tienda/rapimetal), [GEA Zinguería](https://www.mercadolibre.com.ar/pagina/geazingueria), [grampas en pulgadas](https://www.mercadolibre.com.ar/tienda/zingueriagea/clips) y [listado de cenefas](https://listado.mercadolibre.com.ar/cenefa).
- [Tapa de canaleta izquierda (Easy)](https://www.easy.com.ar/tapa-moldura-d-embut-ch-gv-nº30-15-cm-iz/p).
- [Guía Leroy Merlin de canalones](https://biblioteca.org.ar/libros/210136.pdf) y [tabla de chapas de la UNCuyo](https://aulaabierta.ingenieria.uncuyo.edu.ar/mod/resource/view.php?id=6819).
- Documentación de Three.js: [ExtrudeGeometry](https://threejs.org/docs/pages/ExtrudeGeometry.html) y [OrbitControls](https://threejs.org/docs/#examples/en/controls/OrbitControls).
