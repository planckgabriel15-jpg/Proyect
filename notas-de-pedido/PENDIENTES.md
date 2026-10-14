# PENDIENTES – Supuestos a validar con la empresa

Todo lo de esta lista es un **SUPUESTO**: un valor provisorio para poder probar el programa.
Cada uno está en un archivo de `datos/` (se cambia sin tocar código), salvo los que dicen otra cosa.
Cuando la empresa confirme un punto, se corrige el dato y se tacha acá.

## A. Pendientes iniciales (sección 13 de la especificación)

| # | Pregunta | Qué hace hoy el programa | Dónde se cambia |
|---|---|---|---|
| 1 | ¿Tapa y boqueta van en renglón propio o como detalle del renglón de la canaleta? | Renglón propio, con su código y cantidad, y se **vincula** a la canaleta | `src/logica/renglones.js` |
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
| 18 | **Código de piezas por unidad** (tapas, codos, ramales, sombreros, embudos, reducciones): se busca con banda `"UN"`. La tabla de ejemplo no tiene esas filas, así que salen con "código no encontrado" y se emiten marcando "código pendiente" | `config.json` → `bandaPorUnidad` |
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

## D. Catálogo: plantillas agregadas para cubrir todos los productos

Todas las medidas son de **ejemplo**: sirven para que el vendedor arranque con algo parecido y lo corrija. Producción tiene que validarlas.

- **Canaletas:** americana mediana (D25), cuadrada (D40), pecho paloma (D44), cajón pluvial (D70) y media caña Ø12,5 (pieza especial). La canaleta americana arranca con el frente inclinado.
- **Babetas:** sobre chapa sinusoidal y sobre chapa trapezoidal, las dos con **corte láser** en el ala que apoya sobre el techo (1 + 12 + 12 = 25), y babeta frontal de encuentro con muro (D26).
- **Cumbreras:** para chapa sinusoidal y para chapa trapezoidal, con corte láser en las dos alas (reemplazan a la "troquelada"); cumbrera con dobladillos (D32) y limatesa. El ángulo por defecto de las cumbreras lisas es **150°** (hay que poner el ángulo del techo).
- **Media cumbrera:** baja 15 cm por el muro y sigue 15 cm por el techo de un agua, con 120°.
- **Contramuro:** pestaña de 10 cm inclinada a 45° bajo la chapa, lado del techo 12, fondo 10, lado del muro 12 y 3 cm que entran en el muro (D47).
- **Cenefas, goteros y cierres:** gotero, cupertina o cubremuro, alféizar o vierteaguas y tapajunta.
- **Perfiles:** ángulo esquinero 5×5, U, C, Z y omega.
- **Boquetas y caños:** codo rectangular, ramal, reducción y embudo o tronera.
- **Ventilación:** sombrero chino, venturi, **canadiense** y conducto. **La forma del sombrero canadiense hay que confirmarla con producción:** no encontré una definición publicada del término. En el 3D se va a dibujar como un doble cono.

## E. Para cuando se pase a Google (Apps Script)

- La numeración tiene que hacerse en el servidor con `LockService`, que es un candado para que dos vendedores no saquen el mismo número a la vez.
- Las notas emitidas no se modifican: en Sheets conviene una hoja de solo lectura.
