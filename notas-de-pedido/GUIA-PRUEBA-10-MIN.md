# Guía de prueba de 10 minutos (para un vendedor)

Objetivo: cargar la nota real de la empresa en el programa, con tapas y boqueta en la canaleta, sumar un par de productos más, emitirla e imprimirla. Si algo no sale como dice acá, anotalo en la última sección.

> Antes de empezar, alguien tiene que haber abierto el programa siguiendo la sección 1 del `README.md`.
> En cualquier momento, **F1** muestra los atajos de teclado.

---

## Minuto 0–1: entrar

1. Elegí tu nombre de la lista (por ejemplo **Ana Ejemplo**, de Colón) y tocá **Entrar**.
2. Arriba vas a ver el logo, tu nombre y **Sucursal de hoy: Colón**. Si hoy estás en otra, tocá **Cambiar sucursal de hoy**.

## Minuto 1–2: nota nueva

3. Tocá **Nueva nota de pedido** (o apretá **Alt+N**).
4. Escribí el **Cliente** (inventado, por ejemplo "Cliente de Prueba").
5. Pegá un **Factura Nº** inventado (por ejemplo "A-0001-00000123").
6. Fijate que el **NP Nº** dice "se asigna al emitir" y que la fecha es la de hoy.

## Minuto 2–5: la canaleta de la nota real, con tapas y boqueta

7. Tocá **Agregar pieza** (**Alt+P**) y elegí **Canaleta (ejemplo de nota real)**.
8. Mirá la tabla: 1 (dobl. aplastado) + 20 + 32 + 7. Al lado está el **dibujo 2D** acotado y abajo el **3D**.
9. Comprobá que abajo diga **Desarrollo D = 60 cm · Banda 1/2 chapa (60)**.
10. Probá **Alt+T** (agrega un tramo) y **Ctrl+Z** (lo deshace).
11. Debajo de la tabla, en **Tapas y boquetas de la canaleta**, poné **Tapa izquierda: soldada** y **Tapa derecha: engrampada**.
12. Tocá **Agregar boqueta** (**Alt+Q**), elegí la forma **rectangular**, lados **10** y **5**, y posición **60**. En el 2D aparece la vista desde arriba con la boqueta acotada a 60 cm. En el 3D (vista **Lateral**, **Alt+8**) se ve la boqueta abajo y las tapas en las puntas.
13. Pasá al paso 3 (**Alt+flecha derecha**). Elegí **Terminación: Prepintada**, el color **negro** y **Pintura afuera**.
14. Comprobá: **Código CG05P60** y la descripción "2,44 mts canaleta pp negro D60 CH 25 c/ tapa izq. soldada, tapa der. engrampada y 1 boqueta".
15. Tocá **Agregar a la nota** (**Alt+flecha derecha**).

## Minuto 5–8: más productos

16. **Tapa suelta:** **Alt+P**, buscá "tapa" y elegí **Tapa suelta de canaleta**. Arriba, en **Copiar perfil de**, elegí el renglón 1. Fijate que el código sale **TS60N (genérico)**. Agregala.
17. **Sombrero rectangular:** **Alt+P**, buscá "sombrero" y elegí **Sombrero H**. Cambiá la forma a **rectangular**. El código sale **SHR2010Z (genérico)**. Agregalo.
18. **Chapa lisa:** **Alt+P**, elegí **Chapa lisa (corte a medida)**, poné el largo **0,10** (el tramo ya es 10), y en el paso 3 elegí prepintada **negra**. El código tiene que ser **CL1010N**, igual al ejemplo de la empresa. Agregala.
19. **Corte láser (opcional):** elegí **Cumbrera sinusoidal 20×20 (corte láser)**. En el 3D se ve el borde ondulado. Si cambiás la medida del tramo 2 a **3**, sale el aviso "la cara con corte láser mide 3 cm; el mínimo es 3,6 cm".

## Minuto 8–10: emitir, imprimir y buscar

20. Tocá **Emitir nota** (**Ctrl+Enter**) y aceptá. Se asigna el **NP Nº 1** (o el siguiente de tu sucursal) y se abre la hoja para imprimir.
21. Revisá la hoja: el logo y la sucursal en grande arriba a la izquierda; NP, fecha y factura a la derecha; la tabla **Descripción | Código | Cantidad**; y debajo de la canaleta, el detalle de tapas y boqueta con la vista desde arriba.
22. Tocá **Imprimir / Guardar PDF** y elegí **Guardar como PDF**. Abajo de cada hoja tiene que decir tu nombre, la hora y "Página 1 de …".
23. Andá a **Producción** (menú de arriba), escribí el nombre del cliente en el buscador y tocá **Abrir e imprimir**.

## Extra (si sobra tiempo)

- **Dibujar a mano** (**Alt+M**) en una **Pieza especial libre**: marcá 3 o 4 puntos y tocá **Usar este dibujo**.
- **Agregar rápido** sobre una babeta: aleta al final (**Alt+2**), dobladillo al inicio (**Alt+3**), espejar (**Alt+J**).
- **Celular:** abrilo en el celular. En el paso 2 vas a ver las pestañas **Medidas / 2D / 3D**.
- **Configuración** (clave `zingueria2026`): poné el último número de Colón en **4520** y emití una nota: tiene que salir la **4521**.

---

## Anotá acá lo que no anduvo o lo que cambiarías

| Paso | Qué pasó | Qué esperabas |
|---|---|---|
| | | |
| | | |
