# Guía de prueba de 10 minutos (para un vendedor)

Objetivo: cargar la nota real de la empresa en el programa, con tapas y boqueta en la canaleta, sumar un par de productos más (también de HIPER y de G-TEC), emitirla e imprimirla. Si algo no sale como dice acá, anotalo en la última sección.

> Antes de empezar, alguien tiene que haber abierto el programa siguiendo la sección 1 del `README.md`.
> En cualquier momento, **F1** muestra los atajos de teclado.

---

## Minuto 0–1: entrar

1. En **Comercial**, elegí tu usuario de la lista (por ejemplo **Vendedor 1**, en "Abasto · Colón") y tocá **Entrar**. Los vendedores están agrupados por empresa: el de HIPER y el de G-TEC entran igual y ven el logo y el catálogo de su empresa.
2. Arriba vas a ver el logo de tu empresa, tu usuario y **Sucursal de hoy: Colón**. Si hoy estás en otra sucursal de tu empresa, tocá **Cambiar sucursal de hoy**.

## Minuto 1–2: nota nueva

3. Tocá **Nueva nota de pedido** (o apretá **Alt+N**).
4. Escribí el **Cliente** (inventado, por ejemplo "Cliente de Prueba"). La próxima vez, al escribir las primeras letras, el programa te lo va a sugerir.
5. Pegá un **Factura Nº** inventado (por ejemplo "A-0001-00000123"). El número de la nota se asigna al emitir.
6. Debajo hay una línea plegada, **Entrega … · prioridad normal · 3D automático**: abrila solo si el cliente pidió una fecha o es urgente.

## Minuto 2–5: la canaleta de la nota real, con tapas y boqueta

7. Tocá **Agregar pieza** (**Alt+P**) y elegí **Canaleta (ejemplo de nota real)**.
8. Ahora todo está en **una sola pantalla**: arriba el **largo** y la **cantidad**; a la izquierda la tabla (1 + 20 + 32 + 7) y el **material**; a la derecha el **dibujo 2D** acotado y el **3D**.
9. Al pie dice la descripción y el código. Tocá **ver cálculo**: tiene que decir **D = 60 cm · Banda 1/2 chapa (60)**.
10. Tocá **Ver todas las columnas y herramientas** (aparecen sentido, tipo, láser y observación). Probá **Alt+T** (agrega un tramo) y **Ctrl+Z** (lo deshace).
11. En **Material**, tocá **Prepintada**, el color **negro** y **Pintura afuera**.
12. Abrí **Tapas y boquetas: ninguna**. Poné **Tapa izquierda: soldada** y **Tapa derecha: engrampada** (son botones).
13. Tocá **Agregar boqueta** (**Alt+Q**), elegí la forma **rectangular**, lados **10** y **5**, y posición **60**. En el 2D aparece la vista desde arriba con la boqueta acotada a 60 cm.
14. Comprobá al pie: **Código CG05P60** y la descripción "2,44 mts canaleta pp negro D60 CH 25 c/ tapa izq. soldada, tapa der. engrampada y 1 boqueta". En **ver cálculo** están los **códigos extra**: **TS60N × 2** (las tapas) y **BQR105N × 1** (la boqueta).
15. Borrá el largo: al lado del campo aparece **"Falta el largo de la pieza"**. Volvé a poner **2,44** y tocá **Agregar a la nota** (**Ctrl+Enter**).

## Minuto 5–8: más productos

16. **Lo recuerda:** **Alt+P**. Arriba de la galería aparece **Lo último que usaste** (la canaleta). Buscá "babeta" y elegí **Babeta 15×15**: ya viene **prepintada negra** ("Igual que la pieza anterior de esta nota"). Agregala.
17. **Cantidad en la tarjeta:** en la babeta, cambiá la cantidad a **4** directamente en la tarjeta: dice "= 4 chapa(s)". En **ver cálculo** están el desarrollo y el tiempo de fabricación.
18. **Chapa lisa:** **Alt+P**, elegí **Chapa lisa (corte a medida)** y poné el largo **0,10** (el tramo ya es 10). El código tiene que ser **CL1010N (genérico)**, igual al ejemplo de la empresa. Agregala.
19. **Artículo de catálogo:** **Alt+P**, buscá "rejilla" y elegí **Rejilla de ventilación**. Es una ficha corta: medida y cantidad, sin dibujo ni material. Con la medida 15x30 el código sale **RV1530**. Agregala.
20. **Producto de HIPER:** **Alt+P**, buscá "extractor 150". Aparece **Extractores eólicos** (5 modelos). Elegí el de 150. Sale con **código PENDIENTE** (todavía no hay código de facturación cargado): se puede emitir igual.
21. **Servicio de G-TEC:** **Alt+P**, buscá "laser" y tildá **Ver todo el grupo**. Elegí **Corte láser de chapa**, escribí el alcance ("20 piezas según plano"), cantidad **2,5** (horas). Si en espesor ponés **25**, avisa que el láser llega a 20 mm y no deja emitir: poné **3**. Agregalo. En la nota dice que **se reparte sola**: ese renglón lo hace la planta de G-TEC.

## Minuto 8–10: emitir, imprimir y buscar

22. Borrá el cliente y tocá **Emitir nota** (**Ctrl+Enter**): marca en rojo lo que falta, en su lugar. Volvé a escribirlo.
23. Tocá **Emitir nota** otra vez: aparece "Vas a emitir la nota Nº 1 de Colón. Después no se puede modificar". Tocá **Emitir e imprimir** (**Ctrl+Enter** de nuevo): se abre la hoja con la ventana de impresión.
24. Revisá la hoja: logo y sucursal en grande; NP, fecha y factura a la derecha; la tabla **Descripción | Código | Piezas | Cantidad (chapas)**; debajo de la canaleta, las filas de las tapas y la boqueta con sus códigos; al lado del 2D, la **ficha de material** (material, calibre, color y **Pintura AFUERA**); y la vista desde arriba con las posiciones. **Cada dato tiene que estar una sola vez.** Abajo: tu usuario, la hora y "Página 1 de …".
25. Volvé a **Inicio**: la nota figura con su estado de producción (**Pendiente**). Tocá **Repetir**: se arma una nota nueva con el mismo cliente y las mismas piezas; solo falta la factura.

## Extra: editor 3D y pendiente

- **Cotas en el 3D:** en una canaleta, tocá la cota **32** del 3D, escribí **33** y Enter: el desarrollo pasa a **61** y la tabla también. **Ctrl+Z** lo deshace.
- **Editor 3D:** tocá **Editar en 3D** (**Alt+G**). Tocá una cara de la pieza: a la derecha aparecen sus datos. Tocá el **+** de una punta para agregar un tramo, escribí la medida y Enter. Elegí un tramo y apretá **Supr** para borrarlo. **Frente** (**Alt+7**) muestra el perfil como un plano. **Listo** (**Esc**) vuelve al asistente.
- **Con pendiente:** en la canaleta abrí **Más opciones** y tocá **Con pendiente** (o apretá **Alt+L**). En la tabla aparecen las columnas **Final**: poné **25** en el tramo 2. Tiene que decir **D = 65**, la descripción "… con pendiente D60 a D65", y en el 2D se ven las dos puntas y la **vista de costado** con "baja 5 cm en 2,44 m (20,5 mm/m · 1:49)". En el 3D la canaleta se va haciendo más honda.
- **En el celular:** abrí la pestaña **3D** y tocá **Editar en 3D**. Girá con un dedo, hacé zoom con dos y tocá una cota para cambiarla. El panel **Propiedades** de abajo se abre y se cierra tocándolo.

## Extra: productos estándar, cortes, boquetas, tapas y empalme

- **Estándar de la plegadora:** en la galería, el primer grupo es "Productos estándar de la empresa (plegadora)". La **Canaleta Hiper** tiene que dar **D = 32,9** y la **Cumbrera D30 CH30**, **D = 30**.
- **Boqueta que corta la chapa:** en una canaleta agregá una boqueta (**Alt+Q**). En el 3D, girando para mirar desde abajo, se ve el agujero en el fondo. En **Tipo** probá **tronera**: el código extra pasa a ser TR…
- **Boqueta en la tapa:** en **Tapas y boquetas** poné **Tapa derecha: soldada** y en la boqueta elegí **Dónde va: en la tapa derecha**. Si no entra, el programa lo avisa: bajá la **altura del centro**.
- **Tapa a medida:** en la tapa izquierda marcá **Tapa a medida** y cambiá el frente de 20 a **12**: dice "La tapa entra en la canaleta" y el código de esa tapa pasa a **TS52**. Si ponés un fondo de **40**, avisa que no entra.
- **Corte con pared:** **Alt+R** agrega un corte en el fondo. Poné la posición y una pared de **3 cm**: la descripción dice "c/ corte Ø10 c/ pared 3 cm" y en el 2D aparece la cara con el corte acotado.
- **Empalme:** poné el largo en **3**: aparece el panel **Empalme** con **2,44 + 0,56**. Tocá **Partes iguales** (**1,50 + 1,50**). En el editor 3D tocá la cota "chapa 1" y escribí **2**: la otra pasa sola a **1,00**.

## Extra (si sobra tiempo)

- **Dibujar a mano** (**Alt+M**) en una **Pieza especial libre** (arranca con la tabla completa): marcá 3 o 4 puntos y tocá **Usar este dibujo**.
- **Agregar rápido** sobre una babeta (con **Ver todas las columnas y herramientas**): aleta al final (**Alt+2**), dobladillo al inicio (**Alt+3**), espejar (**Alt+J**).
- **Celular:** abrilo en el celular. En la ficha de la pieza vas a ver las pestañas **Datos / 2D / 3D** (el 3D se carga recién al abrirlo).
- **Jefe de producción** (clave `jefe2026`): al entrar elegí la **planta** (taller de Abasto, HIPER, G-TEC o todas). En **Datos de demostración** cargá las 600 notas de ejemplo y mirá el tablero de cada planta.
- **Pieza metalmecánica** (entrando como vendedor de G-TEC): **Pieza metalmecánica a medida**, con descripción, medidas, material, espesor en mm, procesos y el nombre del plano.
- **Configuración** (clave `zingueria2026`): poné el último número de Colón en **4520** y emití una nota: tiene que salir la **4521**.

---

## Anotá acá lo que no anduvo o lo que cambiarías

| Paso | Qué pasó | Qué esperabas |
|---|---|---|
| | | |
| | | |
