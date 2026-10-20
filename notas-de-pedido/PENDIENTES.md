# PENDIENTES – Supuestos a validar con la empresa

Todo lo de esta lista es un **SUPUESTO**: un valor provisorio para poder probar el programa.
Cada uno está en un archivo de `datos/` (se cambia sin tocar código), salvo los que dicen otra cosa.
Cuando la empresa confirme un punto, se corrige el dato y se tacha acá.

## A. Pendientes iniciales (sección 13 de la especificación)

| # | Pregunta | Qué hace hoy el programa | Dónde se cambia |
|---|---|---|---|
| 1 | ¿Tapa y boqueta van en renglón propio o como detalle del renglón de la canaleta? | **Resuelto (16/10):** las puestas en la canaleta van en el mismo renglón; las sueltas son productos aparte (ver 46 y 49) | `src/logica/accesoriosCanaleta.js` |
| 2 | ¿El ángulo por defecto es 90°? ¿Siempre se anota? | 90°. En el dibujo solo se escribe el ángulo si no es 90° | `config.json` → `anguloPorDefecto` |
| 3 | ¿Se marca siempre el lado de la pintura en prepintado? | Sí: es obligatorio en prepintado | `config.json` → `ladoPinturaObligatorio` |
| 4 | ¿Hay otras marcas de tramo además de dobladillo y aplastamiento? | Tipos: normal, dobladillo, dobladillo aplastado, pestaña de engrafe. Se agregó **corte láser** por cara | `src/logica/geometria.js` → `TIPOS_DE_TRAMO` |
| 5 | Un desarrollo de 121 o 122 cm, ¿entra en "chapa completa" o va soldado? | Límite 120: 120,1 cm ya "requiere soldar" | `config.json` → `bandas.limiteChapaCompletaCm` |
| 6 | ¿Cómo cambia el código según el tipo de elemento? Pedir la lista real de códigos | La tabla de ejemplo usa `elemento = "*"` (cualquiera). Si la tabla real trae filas por elemento, esas ganan | `datos/codigos.json` o Configuración → importar |
| 7 | Letra de terminación del galvanizado sin pintar y códigos de cincalum, inoxidable, aluminio y cobre | N = natural; CZ, IN, AL, CU | `materiales.json` |
| 8 | Código de espesor para C28, C24 y C20 | C28 = **036** (para no chocar con C27 = 04), C24 = 06, C20 = 09 | `materiales.json` → `calibres` |
| 9 | Colores de prepintado en stock | negro, rojo teja, gris, blanco, verde | `materiales.json` → `colores` |
| 10 | Medidas reales de las plantillas (americana, galponera, contramuro, limahoya, etc.) | Medidas de ejemplo (ver sección D) | `catalogo.json` |
| 11 | Fórmula de desarrollo de boquetas y caños (solape de engrafe) | Redondo: π·Ø + 1 cm. Rectangular: 2·(a+b) + 1 cm. El vendedor puede corregirlo a mano | `config.json` → `solapeEngrafeCm`; `src/logica/piezasEspeciales.js` |
| 12 | Letra de cada sucursal y último número de talonario de cada una | Letras de ejemplo (C, J, D, O, M, P, F, K, S, X). Último número = 0 | `sucursales.json` o pantalla Configuración |
| 13 | Largo máximo real de las plegadoras de la empresa | 244 cm. Más largo → aviso de empalme | `config.json` → `largoMaximoChapaCm` |

## B. Decisiones tomadas al armar el prototipo (aprobadas en el plan, falta confirmar con la empresa)

| # | Supuesto | Dónde se cambia |
|---|---|---|
| 14 | **Dobladillo en el primer tramo:** el giro de 180° va en la unión con el segundo tramo. En cualquier otro lugar, en la unión con el tramo anterior | `src/logica/geometria.js` → `giroEnTramo` |
| 15 | **Descripción del material sin pintar:** se usa la abreviatura del material ("galv", "cincalum", "inox", "alum", "cobre"). Ej.: "2,44 mts canaleta galv D60 CH 25" | `materiales.json` → `abreviatura` |
| 16 | **Clave de Configuración del prototipo:** `zingueria2026` | `config.json` → `claveConfiguracion` |
| 17 | **Descripción de piezas especiales:** se arma con su texto y medidas, por ejemplo "boqueta redonda Ø10 galv D32,4 CH 25" o "codo 90° Ø10 4 gajos galv CH 25" (sin "D" cuando va por unidad) | `catalogo.json` → `textoDescripcion` |
| 18 | **Código de piezas por unidad** (tapas, curvas, ramales, sombreros, troneras): **reemplazado (16/10)** por el código genérico (ver 44) | `catalogo.json` → `codigoGenerico` |
| 19 | **Valores con los que arranca una pieza nueva:** largo 2,44 m, galvanizado, C25, natural, pintura afuera | `config.json` → `renglonPorDefecto` |
| 20 | **Desarrollo de la canaleta media caña:** π·Ø/2 + dobladillo + pestaña | `src/logica/piezasEspeciales.js` |
| 21 | **Tapa sin vincular:** no se puede emitir, porque producción necesita el perfil de la canaleta | `src/logica/calculoRenglon.js` |

## C. Corte láser (pedido del área comercial durante la Etapa A)

La empresa **no** hace el corte láser: lo manda a hacer afuera y vuelve.

| # | Regla o supuesto | Estado | Dónde se cambia |
|---|---|---|---|
| 22 | La cara (tramo) con corte láser tiene que medir **al menos 3,6 cm**. Si mide menos, sale un **aviso** (no bloquea) | Pedido por la empresa | `config.json` → `corteLaser.anchoMinimoCaraCm` |
| 23 | La **altura de onda** tiene que ser de al menos **3,6 cm**. Si es menor, sale un **aviso** (no bloquea) | Pedido por la empresa. **¿Tiene que ser aviso o error que bloquea?** | `config.json` → `corteLaser.alturaMinimaOndaCm` |
| 24 | Con una onda de 3,6 cm sobre una cara de 3,6 cm, el corte "se come" toda la cara: el programa avisa si la onda es igual o más alta que la cara. **¿El ancho mínimo de 3,6 cm se mide antes o después de la onda?** | SUPUESTO | `src/logica/corteLaser.js` |
| 25 | Valores por defecto de la onda: sinusoidal con altura 3,6 cm y valles cada 7,6 cm; trapezoidal con altura 3,6 cm y valles cada 20 cm. **Pedir las medidas de las chapas que se usan en Córdoba** | SUPUESTO | `config.json` → `corteLaser.valoresPorDefecto` |
| 26 | Forma del trapecio: cresta 30 %, flancos 15 % cada uno y valle 40 % del paso | SUPUESTO | `config.json` → `corteLaser.proporcionesTrapecio` |
| 27 | La descripción agrega "c/ corte láser sinusoidal" para que se vea que hay un trabajo tercerizado | SUPUESTO | `src/logica/descripcion.js` |
| 28 | El corte va en el **borde libre** de la cara. ¿Puede ir en una cara del medio (que no tiene borde libre)? | A confirmar | — |
| 29 | ¿El corte láser cambia el código del producto o se factura aparte? | A confirmar | `datos/codigos.json` |

## D. Catálogo

El 16/10 el catálogo se limitó a los productos que fabrica la empresa (ver puntos 42 y 43). Todas las medidas por defecto con la marca "medidas de ejemplo" las tiene que validar producción. Las cumbreras lisas arrancan con **150°**: hay que poner el ángulo del techo.

## E. Decisiones de pantallas (Etapas B a F)

| # | Supuesto o decisión | Dónde se cambia |
|---|---|---|
| 30 | **Tapa izquierda / derecha:** la izquierda va en la punta donde arranca la canaleta, mirándola de frente desde afuera; la derecha, en la otra punta. ¿Así lo entienden en el taller? | `src/vistas3d/modelo.js` → `montarAccesorios` |
| 31 | **Posición de la boqueta:** ver punto 47 | `accesoriosCanaleta.js` |
| 32 | **Sentido del pliegue:** "izquierda" = gira en sentido antihorario mirando el dibujo; "derecha" = horario | `src/logica/geometria.js` |
| 33 | **Cara de afuera y de adentro** (para la pintura): afuera es el lado convexo del perfil (por fuera de la U). En perfiles en Z, donde no hay un lado claro, se toma el lado izquierdo del recorrido | `geometria.js` → `ladoExteriorDelPerfil` |
| 34 | Se puede **agregar a la nota una pieza con errores**: el programa avisa y no deja **emitir** hasta corregirla | `src/pantallas/asistente.js` |
| 35 | **Prototipo:** cada PC o celular guarda sus propias notas y su propia numeración (localStorage). Para probar la numeración por sucursal hay que usar siempre el mismo equipo. Se resuelve al pasar a Google | `src/datos/almacenamiento.js` |
| 36 | **Ingreso sin contraseña:** se elige el nombre de una lista (prototipo) | `src/pantallas/inicio.js` |
| 37 | Las **formas 3D** de las piezas especiales (codos, ramales, sombreros, embudos) son **aproximadas**: son una ayuda visual. La referencia para fabricar es el esquema 2D con sus medidas | `src/vistas3d/piezasEspeciales3d.js` |
| 38 | Al **emitir**, cada renglón guarda una "foto" de su descripción y su código, para que la nota impresa no cambie si después cambia la tabla de códigos | `src/pantallas/nota.js` |
| 39 | Los **borradores** se guardan solos cada **5 segundos**, también la pieza a medio cargar | `config.json` → `autoguardadoSegundos` |
| 40 | Las **notas emitidas** no se pueden modificar ni borrar. Si hay un error, ¿se anula y se hace otra? (falta definir el procedimiento de anulación) | A definir |

## F. Cambios pedidos el 16/10/2026 (logo, catálogo, códigos, tapas y boquetas)

| # | Supuesto o decisión | Dónde se cambia |
|---|---|---|
| 41 | **Logo y colores de Abasto Soluciones:** **resuelto (ronda 5)**. Se usa el logo que mandó la empresa (`recursos/logo.png`) y los colores se tomaron del logo: azul **#0054a6** (principal), azul oscuro #003d7a y rojo **#fe222c** (acento). Si el manual de marca tiene otros valores exactos, se cambian en un solo lugar | `recursos/logo.png` y `config.json` → `marca` |
| 42 | **Catálogo limitado a lo que la empresa publica que fabrica:** plegados y cortes (babetas, cumbreras, 1/2 cumbrera, limahoya, troneras, boquetas), zinguería para techos (babeta sinusoidal y trapezoidal, cenefa o perimetral), caños, codos y curvas (caño redondo de chapa N°25 o inoxidable 0,5 mm, caño rectangular, curva articulada, ramal 45° y 90°, codo rectangular vertical) y sombreros (no estándar, H, salamandra o canadiense, tipo Spiro). Se agregaron canaleta, tapa suelta y chapa lisa (corte a medida). **Confirmar que no falte ni sobre nada** | `datos/catalogo.json` |
| 43 | ~~Quedaron fuera las cenefas decorativas, artesanías, línea gas y soportes.~~ **Cambiado (ronda 5):** se agregaron todos, ver punto 53 | `datos/catalogo.json` |
| 44 | **Código genérico** para los productos que no están en la tabla de facturación: siglas + medidas importantes + letra. Ejemplos: chapa lisa 10x10 negra → **CL1010N**; curva articulada Ø10 90° galvanizada → CA1090Z; sombrero H rectangular 20x10 → SHR2010Z; tapa suelta de una canaleta D60 negra → TS60N. Si la tabla real trae una fila para ese elemento, manda la tabla. **Confirmar siglas y letras** | `catalogo.json` → `codigoGenerico`; `materiales.json` → `letraCodigoGenerico` |
| 45 | **Letra del código genérico:** en prepintado, la del color (negro N, rojo teja R, gris G, blanco B, verde V). Sin pintar, la del material (galvanizado **Z**, cincalum C, inoxidable I, aluminio A, cobre U) | `materiales.json` |
| 46 | **Tapas y boquetas puestas en la canaleta:** van en el **mismo renglón** de la canaleta. La descripción suma "c/ 2 tapas soldadas y 1 boqueta" y la hoja impresa lleva el detalle y una vista desde arriba con las posiciones. **Resuelto (ronda 5):** además del código de la canaleta se agregan los códigos de la tapa y de la boqueta (ver punto 52) | `src/logica/accesoriosCanaleta.js` |
| 47 | La **posición de la boqueta** se mide desde la punta izquierda de la canaleta hasta el **centro** de la boqueta | `accesoriosCanaleta.js` |
| 48 | **Tapa engrampada y tapa soldada:** en el 3D, la soldada lleva la pestaña hacia adentro y la engrampada la lleva abrazando por afuera (solo para que se vea la diferencia) | `src/vistas3d/modelo.js` |
| 49 | **Tapa suelta y boqueta suelta** son productos aparte. La tapa suelta copia el perfil de una canaleta de la nota o de una plantilla | `catalogo.json` |
| 50 | **Sombreros circulares o rectangulares.** Las formas 3D del sombrero H, el canadiense o salamandra y el tipo Spiro son aproximadas. Marcar "aprobado" en los sombreros a medida **no hace falta** (respuesta de la empresa, ronda 5). El "sombrerete aprobado" de la línea gas está como artículo de catálogo (punto 53) | `catalogo.json`, `piezasEspeciales3d.js` |
| 51 | **Atajos de teclado:** se evitaron Alt+F, Alt+E y Alt+D porque el navegador los usa para sus menús. F1 muestra la lista | `src/pantallas/atajos.js` y cada pantalla |

## F2. Cambios pedidos en la ronda 5 (16/10/2026)

| # | Supuesto o decisión | Dónde se cambia |
|---|---|---|
| 52 | **Códigos extra de la canaleta:** cada tapa y cada boqueta puesta en la canaleta suma su propio código en la nota (aunque la tapa vaya soldada), con el **mismo código que el producto suelto**: tapa → TS + desarrollo + letra (ej. **TS60N**); boqueta → BQ + forma + medidas + letra (ej. **BQR105N**). Cantidad = tapas (o boquetas) × cantidad de canaletas. Si las dos tapas son iguales en código, van en una sola línea ("2 tapas (izq. soldada, der. engrampada)"). En la hoja impresa salen como filas aparte debajo de la canaleta | `src/logica/calculoRenglon.js` → `codigosDeAccesorios` |
| 53 | **Catálogo completo del sitio:** se sumó el grupo **Artículos de catálogo (reventa)** con cenefa punta de lis (CPL), flor de lis (CFL) y piña (CPI), rejillas de ventilación (RV + medida), conducto pasapared (CPP), puerta con marco (PM), cerradura (CRP), puerta y marco de gabinete (PMG), sombrerete aprobado (SAP + Ø), caño enlozado (CE + Ø), balde (BA), palangana (PA), regadera (RE), soportes de canaleta (SPA, SPH, SPM) y de caño rectangular (SPR), embudo colector moldura (ECM), colector recto (COL510) y compriband (CB). **No piden material ni calibre** (se venden hechos); el código no lleva letra. Medidas y modelos tomados de los títulos del sitio: **confirmar** | `datos/catalogo.json` (generador `articulo`) |
| 54 | **Caños y boquetas de cualquier forma:** el caño quedó en un solo producto con forma **redonda, cuadrada o rectangular** (códigos CN, CNC, CNR + medidas + largo + letra; ej. CN10100Z = Ø10 × 1 m galvanizado). La boqueta suelta y la de la canaleta también pueden ser redondas, cuadradas o rectangulares | `catalogo.json` → `cano`, `boqueta_suelta` |
| 55 | **Prepintado de un lado o de los dos:** se puede elegir pintura afuera, adentro o **de los dos lados**. En la descripción se agrega "2 caras" (ej. "2,44 mts babeta 15x15 pp negro 2 caras D30 CH 25"); en el 2D salen las flechas de los dos lados y en el 3D las dos caras van pintadas. **Confirmar cómo lo escribe la empresa** ("2 caras", "doble faz"…) | `config.json` → `ladosPintura`; `src/logica/descripcion.js` |
| 56 | **Vendedores numerados:** se sacaron los nombres de ejemplo; quedan **Vendedor 1 a Vendedor 30** (3 por sucursal). Se cambian por los reales en el archivo | `datos/vendedores.json` |
| 57 | **3D más grande en la nota impresa:** la captura se hace a 760×520 píxeles y ocupa media hoja (hasta 75 mm de alto), al lado del 2D | `src/pantallas/impresion.js`, `src/estilos/impresion.css` |

## F3. Editor 3D y plegados con pendiente (ronda 6, 20/10/2026)

| # | Supuesto o decisión | Dónde se cambia |
|---|---|---|
| 58 | **Cotas en el 3D:** mientras se edita la pieza, el 3D muestra todas las cotas: la medida de cada tramo (del lado de afuera de la pieza, como en un plano), el ángulo de cada pliegue (también los de 90°), el largo, la posición de cada boqueta y el cartel de cada tapa. En las piezas especiales, las medidas principales (Ø, lados, largo, alto, boca, pestaña…) y el resto en una ficha en la esquina. Si dos textos se pisan, se esconde el menos importante y vuelve a aparecer al acercarse con el zoom | `src/vistas3d/cotas3d.js`, `src/logica/cotas.js` |
| 59 | **Editar en el 3D (estilo CAD simplificado):** tocar una cota la convierte en un campo; Enter confirma y Esc cancela (como la edición de cotas de los programas de CAD). Los cambios pasan por la tabla de tramos, así **Deshacer** también deshace lo hecho en el 3D. El 2D sigue siendo la referencia para fabricar | `src/vistas3d/escena.js`, `src/pantallas/asistente.js` |
| 60 | **Editor 3D a pantalla completa** (botón "Editar en 3D", Alt+G): tocar una cara elige el tramo (o la tapa, o la boqueta) y al costado aparecen sus datos; "+" en las puntas libres agrega un tramo de 10 cm a 90° (después se le cambia la medida); "Borrar lo elegido" (Supr) quita esa parte. En el **celular** las herramientas van en una fila que se desliza, el panel de datos va abajo y se pliega, y las cotas y los "+" son más grandes para el dedo | `src/pantallas/editor3d.js` |
| 61 | **Vista inicial "desde la punta":** en las piezas largas (una canaleta de 2,44 m con un perfil de 30 cm) la vista isométrica deja el perfil chiquito y las cotas no se leen; por eso el 3D arranca mirando desde la punta derecha. **Frente y Lateral** ahora son **sin perspectiva** (como un plano) | `src/vistas3d/escena.js`, `encuadre.js` |
| 62 | **Plegado con pendiente** (botón "Con pendiente", Alt+L): la pieza cambia de perfil de la punta izquierda (inicio) a la derecha (final), por ejemplo una canaleta más honda hacia la bajada. Se hizo como el *lofted flange* de Inventor y el *sheet metal loft* de Onshape (chapa entre dos perfiles): **los dos perfiles tienen los mismos tramos, en el mismo orden, con el mismo tipo y sentido**; cambia la medida y el ángulo de cada tramo. Los dos perfiles se dibujan desde el mismo punto de arranque (el borde de arriba queda a nivel y el fondo baja). **Confirmar que así trabaja el taller** | `src/logica/pendiente.js` |
| 63 | **Desarrollo con pendiente = el mayor de las dos puntas** (es el ancho de chapa que hace falta). La banda y el código salen de ese desarrollo. La descripción agrega "con pendiente D60 a D65". **Confirmar cómo se cotiza y cómo se escribe** | `src/logica/calculoRenglon.js`, `descripcion.js` |
| 64 | **Pendiente informada, no exigida:** se muestra cuánto baja el fondo, en mm por metro y como relación (ej. "baja 5 cm en 2,44 m (20,5 mm/m · 1:49)"). Como referencia, la guía de canaletas de la autoridad de plomería de Victoria (Australia) lista pendientes de 1:200 a 1:40, pero **no se agregó ningún mínimo** porque la empresa no lo pidió | `src/logica/pendiente.js` |
| 65 | **Tapas de una canaleta con pendiente:** la tapa derecha lleva el perfil final, así que factura con su propio código (ej. TS60Z a la izquierda y TS65Z a la derecha) | `src/logica/calculoRenglon.js` |
| 66 | Con pendiente, el **corte láser** se dibuja en el 2D pero en el 3D el borde queda recto, y el **dibujo a mano** reemplaza el perfil (la punta final vuelve a ser igual al inicio) | `src/vistas3d/extrusion.js` |

## G. Para cuando se pase a Google (Apps Script)

- La numeración tiene que hacerse en el servidor con `LockService`, que es un candado para que dos vendedores no saquen el mismo número a la vez.
- Las notas emitidas no se modifican: en Sheets conviene una hoja de solo lectura.
