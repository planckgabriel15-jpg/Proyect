# Gestión de producción: cómo funciona

Documento técnico de la extensión de producción (correcciones de la nota, tiempo estándar,
agrupamiento, asignación a operarios y herramientas del jefe). El agrupamiento está
explicado aparte en [AGRUPAMIENTO.md](AGRUPAMIENTO.md). Los supuestos están en
`PENDIENTES.md`, sección H.

## 0. Lo que se encontró al revisar el código (antes de cambiar nada)

- **Stack:** HTML + CSS + JavaScript (módulos ES) sin compilación; Three.js 0.170.0 por CDN;
  dibujos 2D en SVG; datos en `localStorage` solo a través de `src/datos/almacenamiento.js`;
  configuración en `datos/*.json`; pruebas con `node --test`.
- **Vistas de la nota:** pantalla (`pantallas/nota.js`, tarjetas con miniatura 3D), impresión
  y PDF (`pantallas/impresion.js` + `estilos/impresion.css`, se imprime con el navegador). El 3D
  se dibujaba siempre (miniatura y foto en la impresión, `vistas3d/capturas.js`).
- **Contradicciones con lo pedido:**
  1. La columna **Cantidad** mostraba las **piezas** (`renglon.cantidad`), no las chapas.
  2. La impresión de una nota **emitida** mezclaba la foto guardada al emitir con datos
     calculados en vivo (empalme, pendiente), y la foto se armaba en dos lugares.
  3. En Producción e Inicio la columna "Piezas" mostraba la **cantidad de renglones**.
  4. No había roles (solo vendedor), ni operarios, máquinas, fecha de entrega o prioridad.
  5. "Producción" era solo una lista de notas emitidas (los estados quedaban para "etapa 2").
- **Decisiones** (no se pudo consultar; se eligió lo más recomendado): ver PENDIENTES.md, H.

## 1. Cantidad de chapas (REQ A1)

**Regla de la nota** (`logica/chapas.js` → `cantidadDeLaNota`):

    chapas = piezas × largo ÷ largo de la chapa (config.largoMaximoChapaCm = 244)

| Renglón | Cuenta | Cantidad |
|---|---|---|
| canaleta 2,44 m × 1 | 1 × 2,44 ÷ 2,44 | **1** |
| canaleta 1,22 m × 1 | 1 × 1,22 ÷ 2,44 | **0,5** |
| canaleta 1,50 m × 2 | 2 × 1,50 ÷ 2,44 | **1,23** |
| cumbrera 2,00 m × 8 | 8 × 2,00 ÷ 2,44 | **6,56** |
| boqueta suelta × 3 (sin largo) | por unidad | **3 u.** |

- La "chapa" de esta cuenta es la **unidad del código**: una tira de 2,44 m del ancho de la
  banda (CG05P60 = media chapa). Por eso no depende del desarrollo: ya está en el código.
- Las **piezas** siguen en `renglon.cantidad` y se ven en su propia columna ("Piezas").
- 2 decimales [SUPUESTO]. Tapas y boquetas puestas en la canaleta siguen en unidades.

**Regla más precisa (se muestra, NO se aplica):** `consumoFisico` y `explicarDiferencia`.

- *A lo largo*: los tramos se acomodan en tiras de 2,44 m (método "primero que entre, de mayor
  a menor"); los recortes no se reutilizan. Dos canaletas de 1,50 m ocupan **2 tiras** (en cada
  una sobran 0,94 m), no 1,23: **0,77 más** que la regla de la nota.
- *A lo ancho*: de una chapa de 1,22 m (menos 1 cm de despunte) salen `⌊121 ÷ desarrollo⌋`
  tiras (fórmula del estudio MTM). Un desarrollo de 33 cm da **3 tiras**, pero la banda 60 cuenta
  **2** (media chapa cada una): la banda sobreestima la chapa entera usada.
- En la tarjeta de la nota aparece "Consumo físico estimado" cuando hay diferencia, y en
  **Producción → Material** se ven las tres cifras (regla de la nota, chapas enteras según la
  banda y estimación física) para comprar con la más realista.

## 2. 3D opcional (REQ A2)

`logica/fotoCalculo.js` → `mostrar3d(renglon, nota, datos)`. Manda, en orden:
1. lo elegido en el renglón (botón "3D: sí/no/auto" de la tarjeta);
2. lo elegido en la nota ("Imagen 3D": automático / en todos / sin 3D);
3. la regla automática: **sin 3D** en productos estándar y artículos de reventa
   (`config.vista3d.gruposApagadosPorDefecto`), con 3D en el resto.

Se guarda con la nota y se respeta en la pantalla, la impresión y el PDF. Sin 3D, los
detalles pasan al lado del dibujo 2D y la hoja queda más corta. En una nota ya emitida se
puede cambiar solo la presentación con `almacenamiento.cambiarVista3d` (queda en el historial).

## 3. Auditoría de datos duplicados (REQ A3)

| # | Duplicado o recalculado | Cómo quedó (una sola fuente) |
|---|---|---|
| 1 | La foto de lo facturado (`renglon.calculado`) se armaba en `nota.js` y otra vez, distinta, en `impresion.js` | Una sola función `fotoDelCalculo()`; la impresión usa `datosDelRenglon()` |
| 2 | La impresión de una nota emitida tomaba empalme y pendiente en vivo (podían cambiar) | La foto guarda `empalmeTexto` y `pendienteTexto`; las fotos viejas se completan una vez (`migrarDatos`) |
| 3 | "Cantidad" mostraba piezas; las chapas no estaban | `cantidadDeLaNota()` (en la foto al emitir); piezas en su columna |
| 4 | Columna "Piezas" = cantidad de renglones (Producción e Inicio) | Renombrada "Renglones"; las piezas se suman aparte |
| 5 | Medida de la chapa: 244 en config, 122 solo en un comentario, 1220 y despunte en la planilla MTM | `config.largoMaximoChapaCm` y `config.anchoChapaCm` (+ `cantidadDeChapas.margenEscuadreCm`); el modelo de tiempos los lee de ahí |
| 6 | Valores calculados de la planilla (suplemento total, tiempo por golpe de guillotina, desarrollo máximo, ciclo manual, largo máximo, tiempos de detalles) | No se copian al JSON: `prepararModelo()` los calcula; los detalles guardan su fórmula de parámetros |
| 7 | Espesor del material en la planilla MTM y en `materiales.json` | El peso y el ciclo usan el espesor del calibre de `materiales.json`; la fila MTM solo aporta densidad, recubrimiento, Rm y factores |
| 8 | Estado de la nota (pendiente…demorada) | No se guarda: se calcula de los renglones (`estadoDeNota`) |
| 9 | Fecha de entrega y prioridad | Solo en la nota (lo pedido por el cliente). El jefe cambia el **orden** de la cola y la **fecha programada**, que son otra cosa |
| 10 | Tiempo estándar del renglón | Se calcula en vivo; se **congela** al marcar HECHA (con el ahorro del lote) para medir el desvío contra lo que se estimaba en ese momento. Es un registro histórico, no un duplicado |
| — | Se mantiene a propósito: el renglón copia de la plantilla `elemento`, `textoDescripcion`, `usaLargo`, `codigoGenerico` | Así una nota no cambia si mañana se edita el catálogo |

## 4. Tiempo estándar (REQ B)

**Modelo**: réplica exacta de la hoja CALCULO de la planilla "Modelo MTM Zinguería"
(`logica/tiempos.js`), probada contra los tres ejemplos (EJ1 931,2 s; EJ2 2.085,1 s;
EJ3 4.076,1 s, también las horas-hombre):

    T_nota = T_pedido·(1+S) + Σ ítems [ T_setup·(1+S) + Q · T_std_pieza ]
    T_std_pieza = T_manual·(1+S) + T_máquina·(1 + S·k_máq)
    T_manual = corte (por chapa y por tira) + carga y descarga + golpes·posicionado·f_pleg·k_2op
             + volteos·f_manip·k_2op + desplazamiento lateral + control + detalles + depósito
    T_máquina = guillotina + golpes · ciclo de plegadora(material) · f_pleg

Ajustes respecto de la fórmula pedida (justificados en el informe MTM, sección 8): el corte
se reparte por chapa y por tira; el pliegue se separa en golpes, volteos y factor por tipo
(cierre 180° = 2 golpes, inverso = volteo); máquina y manual van por separado; con dos
operarios hay factor de coordinación y las horas-hombre se cuentan aparte. Además, el
setup se separa en **componentes** para saber cuáles se ahorran al agrupar.

**Parámetros** (`datos/tiempos-mtm.json`, generado con `herramientas/importar-modelo-mtm.py`):
cada uno con clave, valor, unidad, descripción, fuente, confianza, estado (DATO / [SUPUESTO] /
[A VALIDAR]) y grupo. Se editan en **Producción → Parámetros de tiempos** (o se importa el CSV
de la hoja PARAMETROS_API). Ningún número del negocio está en el código.

**Lectura del renglón** (`logica/tiemposRenglon.js`, parámetros `q_…` [SUPUESTO]):
- pliegues del dibujo: SIMPLE (90° ± 1°), ANGULO, CIERRE180 (dobladillo), INVERSO (gira al revés
  que el anterior);
- ESTANDAR si es producto estándar o el perfil del catálogo sin cambios; si no, ESPECIAL; con
  pendiente, ESPECIAL;
- detalles: TAPA por tapa; boqueta = ENCASTRE + SOLDADURA; corte = ENCASTRE (+ SOLDADURA si lleva
  pared); empalme = 4 REMACHE + SELLADO por unión;
- empalme: cada tramo de chapa se corta y pliega aparte, con un solo setup;
- caños: redondo = curvado + engrafe; rectangular = 3 pliegues + 2 cierres + engrafe (EJ3);
- productos sin perfil (boquetas sueltas, sombreros, codos, artículos): tiempo por grupo del
  catálogo (`productosSinPerfil`, editable).

**Tiempo estimado y real**: el estándar se ve en la nota (por renglón y total) y en producción;
al marcar HECHA se guardan el estándar (congelado) y el real, y la pestaña Parámetros muestra
el desvío por nota con semáforo (±5 % / ±10 %) y sugiere `p_eficiencia` para recalibrar.

## 5. Asignación, tiempo real y eficiencia (REQ D)

- **Registro de producción** separado de la nota (la nota emitida no se toca): por renglón,
  operario, día, turno, lote, HECHA con hora, eventos del cronómetro, estándar congelado,
  real y de dónde salió el real; más el historial (trazabilidad).
- **HECHA** guarda la hora sola. **Iniciar / Pausar / Reanudar** son opcionales.
- **Limitación de la casilla sola**: sin cronómetro, el real se estima desde la HECHA anterior
  del mismo operario ese día (o el inicio del turno). Incluye pausas, esperas, consultas y
  tareas no registradas; si se marcan varias juntas, la primera se lleva todo el tiempo. Por eso
  la pantalla del operario lo avisa, la eficiencia muestra qué parte salió "por casilla" y la
  recalibración recomienda usar el cronómetro.
- **Eficiencia** = estándar de lo terminado ÷ real, por operario, día, semana o mes, con
  evolución. La pantalla advierte que no debe usarse como único criterio.
- **Roles**: comercial (carga notas; mira el tablero), jefe de producción (todo producción; clave
  fija del prototipo) y operario (sus trabajos). No es seguridad real: en la versión con Google
  los roles salen de la cuenta.

## 6. Herramientas del jefe (REQ E): qué se hizo y qué no

Priorizado por valor ÷ esfuerzo. **Hechas** (todas usan los mismos datos, sin tablas nuevas):

| Herramienta | Dónde |
|---|---|
| Tablero de estados con filtros y contadores | Producción → Tablero |
| Alertas de riesgo (vencidas, programadas después de la entrega, en riesgo, urgentes sin asignar, sobrecarga) | Tablero |
| Prioridades: arrastrar filas (computadora) o ↑ ↓ (celular) | Tablero |
| Reprogramar día y operario, asignación automática | Asignación |
| Capacidad diaria por operario y por máquina | Asignación |
| Material consolidado (con la regla de chapas de A1) | Material |
| KPIs (entregas a tiempo, eficiencia, pendiente, demoradas, ahorro por lotes, incidencias, desvío) | Indicadores |
| Registro de retrabajos, demoras e incidentes con causa | Incidencias (y botón "Problema" del operario) |
| Hoja de ruta imprimible por operario y día o por lote | Asignación → "hoja" / `#hoja-ruta/…` |
| Exportar a Excel (CSV en español) y PDF (imprimir) | Indicadores, Material, Operarios, Incidencias, Parámetros |
| Historial y trazabilidad por nota | Tablero → Detalle |

**Propuestas para más adelante** (no se hicieron para no sumar complejidad que hoy no se usa):
diagrama de Gantt por máquina; aviso al vendedor cuando su nota está lista (correo o
WhatsApp, en la versión con Google); código QR en la hoja de ruta para marcar HECHA desde el
celular; recalibración automática por regresión cuando haya 30 notas o más; stock de
productos estándar; mantenimiento preventivo de máquinas.

## 7. Datos de demostración (REQ F)

`logica/demo.js`: 50 notas emitidas por cada uno de los 10 locales, semilla fija
(20261028), marcadas `demo: true`, número propio (`D-C001`), sin usar los contadores. Mezcla:
~45 % productos de siempre con la misma medida (familias), ~35 % variantes, ~20 % distintos.
Las viejas quedan terminadas con un tiempo real simulado (ritmo propio de cada operario), las
del medio a medias y las nuevas pendientes. Se cargan y se borran desde **Producción → Datos de
demostración** (borra solo lo marcado demo).

Resumen con hoy = 28/10/2026: **500 notas, 1.017 renglones, 0 con error; 269,4 h de tiempo
estándar en total; 32 min por nota en promedio** (mediana 27 min, 90 % por debajo de 58 min,
máximo 2 h 27 min). Distribución: 27 notas de 0 a 10 min, 140 de 10 a 20, 204 de 20 a 40, 83 de
40 a 60, 43 de 60 a 120 y 3 de más de 120. Con los 237 renglones pendientes se forman **35
lotes**, con un ahorro de setup de **583 min (9 h 43 min)**: 16 % del tiempo total y 56 % del setup.
Ocupan unos 2 MB del navegador (el límite es de unos 5 MB).
