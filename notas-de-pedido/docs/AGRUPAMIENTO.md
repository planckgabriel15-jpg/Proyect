# Agrupamiento de notas por operaciones: por qué así

Justificación corta del método que usa la pestaña **Producción → Lotes (agrupar)**
(`src/logica/agrupamiento.js`). Objetivo: hacer el **setup** (preparación de la máquina)
una sola vez para varios renglones de distintas notas, **sin demorar ninguna entrega
urgente** y con un método que el jefe de producción entienda y pueda corregir a mano.

## 1. Qué dice la bibliografía

| Tema | Qué aporta | Fuente |
|---|---|---|
| Tecnología de grupos (TG) y familias de piezas | Agrupar ítems por atributos parecidos, de modo que las piezas con procesos parecidos formen familias. Hay tres formas clásicas de armar familias: inspección visual, clasificación y codificación (por ejemplo Opitz) y análisis del flujo de producción (Burbidge, a partir de las hojas de ruta). El análisis de flujo reduce los tiempos de setup y los stocks intermedios. | Burbidge, J. L. (1989). *Production Flow Analysis for Planning Group Technology*. Clarendon Press ([ficha](https://blackwells.co.uk/bookshop/product/Production-Flow-Analysis-for-Planning-Group-Technology-by-John-L-Burbidge/9780198564591)); apuntes de TG de la HKUST ([enlace](https://ieda.ust.hk/dfaculty/ajay/courses/ieem513/GT/GT.html)) y de Montana State, basados en Groover ([enlace](https://www.montana.edu/dsobek/teaching/ime471/lectures/Lecture%2013%20-%20Cellural%20Manufacturing%20and%20Group%20Technology%20-%20Ch%2018.pdf)) |
| Coeficientes de similitud | McAuley (1972) propuso el coeficiente de Jaccard combinado con agrupamiento jerárquico (enlace simple) para formar grupos; Jaccard es el más usado y el más estable. Ningún coeficiente gana en todas las medidas, así que conviene uno simple y explicable. | McAuley, J. (1972). *Machine grouping for efficient production*. Production Engineering 51(2), 53-57 (citado en [arXiv 1702.07266](https://arxiv.org/pdf/1702.07266)); Sarker (1996), comparación de coeficientes ([LSU](https://repository.lsu.edu/mechanical_engineering_pubs/2139)); definición de Jaccard para piezas ([Univ. de Miskolc](https://ojs.uni-miskolc.hu/index.php/psaie/article/download/3856/2769/15656)) |
| TG en plegado de chapa | Agrupar piezas que comparten setup de plegado lo reduce. En producción de mucha variedad y poco volumen es difícil armar grupos grandes, por eso se juntan varias categorías de producto: en dos plegadoras el setup bajó de 841 s a 680 s. | Estudio de Hitachi en *Int. J. of Automation Technology* (2025), [Fuji Press](https://www.fujipress.jp/?p=15569); Gupta y Bourne, planificación de setups de plegado por familia ([ISR UMD](https://isr.umd.edu/node/1329)) |
| Setups que dependen de la secuencia | Hay más de 300 trabajos sobre programación con setups; se distingue entre problemas con lotes (familias) y sin lotes, y entre setups que dependen o no de la secuencia. En chapa, el orden de los trabajos cambia mucho el setup total. | Allahverdi, A., Ng, C. T., Cheng, T. C. E., Kovalyov, M. Y. (2008). *A survey of scheduling problems with setup times or costs*. EJOR 187(3), 985-1032 ([PolyU](https://research.polyu.edu.hk/en/publications/a-survey-of-scheduling-problems-with-setup-times-or-costs/)); tesis de la Univ. de Vaasa sobre cambios de herramental en chapa ([Osuva](https://osuva.uwasa.fi/handle/11111/7258)) |
| Familias y fecha de entrega | Sin setups, ordenar por fecha de entrega (regla EDD) minimiza el atraso máximo; con familias, hay un óptimo en el que dentro de cada familia los trabajos siguen el orden de entrega (Monma y Potts, 1989). Agrupar tiene "doble filo" para las entregas. | Baker, *Scheduling job families with setups and due dates* ([CORE](https://core.ac.uk/download/207955009.pdf)); Düzgit y otros, asignación de entregas con setups de familia ([Bilgi](https://openaccess.bilgi.edu.tr/items/25298baf-3c3e-4a12-9fab-1c1b1c47659e/full)) |
| Tamaño de lote | Wagner-Whitin da el lote óptimo para demanda conocida con costo fijo de setup, pero supone un solo ítem y capacidad infinita; para un taller con mucha variedad hacen falta extensiones. | [Wikipedia: Dynamic lot-size model](https://wikipedia.com/wiki/Dynamic_lot_size_model) |
| SMED | Separar el setup interno (máquina parada) del externo (mientras trabaja), pasar interno a externo y simplificar lo que queda. Caso Toyota: cambio de prensa de 4 h a menos de 3 min en varios pasos. | Shingo, S. (1985). *A Revolution in Manufacturing: The SMED System*; resumen en [Wikipedia](https://en.wikipedia.org/wiki/Single-minute_exchange_of_die) |

## 2. Qué se eligió (y por qué)

1. **Familias por atributos (TG por clasificación)** en lugar de por ruta: en la zinguería
   casi todo pasa por guillotina y plegadora, así que la ruta no distingue; lo que cambia el
   setup es el **perfil** (programa de plegadora), el **desarrollo** (tope de la guillotina),
   el **material y calibre** (qué chapa traer y qué matriz usar) y el **herramental**.
   Todos esos datos ya están en la nota: no hace falta cargar nada nuevo.
2. **Similitud = coeficiente ponderado de coincidencias** (Σ peso × coincide ÷ Σ peso),
   una generalización del Jaccard / "simple matching" de la TG. El jefe elige qué criterios
   cuentan, con qué peso y con qué tolerancia (desarrollo ± mm, largo ± cm), y el **nivel de
   similitud mínimo** (por defecto 60 %).
3. **Enlace completo**: un trabajo entra a un lote solo si se parece a **todos** los
   integrantes (no solo al primero). Así un lote no se "estira" con trabajos cada vez más
   distintos (el problema clásico del enlace simple).
4. **Recorrido en orden de urgencia y entrega (EDD)** con restricciones: misma máquina,
   entregas dentro de una ventana de días, urgentes solo con urgentes, tope de minutos y de
   renglones por lote. Cada trabajo va al lote donde **más setup ahorra**.
5. **Secuencia por "vecino más cercano"** dentro del lote: el siguiente es el que más setup
   ahorra respecto del anterior, porque el ahorro se da entre trabajos **consecutivos**
   (setup dependiente de la secuencia).
6. **Ahorro por componente del setup** del modelo MTM (`tiempos.js`): chapa (mismo
   material), guillotina (mismo espesor y desarrollo), plegadora + control de primera pieza +
   interpretación (mismo perfil) y herramental (mismo herramental). El traslado y atado del
   lote **no** se ahorra. Por eso el ahorro es honesto aunque el parecido sea parcial (por
   ejemplo, mismo material pero otro perfil ahorra solo la chapa).
7. **Protección de urgentes**: se simula la cola (por máquina, en orden de urgencia y
   entrega) con y sin lotes; si alguna urgente terminaría más tarde con los lotes, se sacan
   de su lote los trabajos que la "empujan" (lotes que van antes y tienen entrega posterior).
   Se repite hasta que ninguna urgente se atrase.
8. **El jefe manda**: aceptar, mover un renglón a otro lote, dividir, sacar o deshacer
   un lote, y "deshacer último cambio".

Con los datos de demostración (hoy = 28/10/2026, 237 renglones pendientes): **35 lotes**,
ahorro de **583 min (9 h 43 min)** = 16 % del tiempo total y 56 % del setup.

## 3. Qué se descartó

| Alternativa | Por qué no (por ahora) |
|---|---|
| Programación matemática (MILP) o metaheurísticas (tabú, genéticos) para lotes y secuencia | Necesitan solver o mucho cálculo, son difíciles de explicar al jefe y de corregir a mano, y los tiempos de entrada todavía son [SUPUESTO]: optimizar fino sobre datos sin validar no rinde. |
| Agrupamiento jerárquico completo (dendrograma) o k-medias | Hay que elegir el corte o la cantidad de grupos, y no respetan restricciones (entregas, urgentes, máquina, tope por lote). El método por líder con enlace completo da grupos parecidos y sí las respeta. |
| Análisis de flujo de producción (Burbidge) o códigos tipo Opitz | Están pensados para formar **celdas** de máquinas a largo plazo, no para el día a día; además casi todas las piezas comparten ruta. |
| Lote económico (EOQ / Wagner-Whitin) | Es para fabricar contra stock con demanda prevista; acá se fabrica contra pedido con fecha. Queda como mejora para productos estándar que se podrían hacer para stock (sección 5). |
| Secuencia óptima (problema del viajante) dentro del lote | Con lotes de hasta 15 renglones el vecino más cercano queda muy cerca y se explica en una línea. |

## 4. Limitaciones

- El setup ahorrado sale de parámetros [A VALIDAR] (setup de plegadora, de guillotina, cambio
  de herramental): hasta cronometrarlos el ahorro es una estimación.
- No se tiene en cuenta que el último trabajo de un lote deje la máquina preparada para el
  primero del lote siguiente (estimación conservadora).
- La verificación de urgentes usa una cola simple por máquina; no reemplaza la mirada del jefe.

## 5. Mejoras posibles

- SMED: medir qué parte del setup se puede hacer con la máquina andando (preparar la chapa y
  el programa del lote siguiente) y bajar el parámetro correspondiente.
- Fabricar para stock los productos estándar que más se repiten (lote económico).
- Encadenar lotes entre sí (lote siguiente que arranque con el mismo herramental).
