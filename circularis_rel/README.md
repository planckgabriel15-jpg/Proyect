# circularis_rel: sistema de confiabilidad Weibull para Circularis (línea T-WOOD)

Los operarios y el encargado registran eventos desde el navegador (parte de turno, aviso de falla, cierre de OT). El jefe de mantenimiento los valida. El sistema calcula Weibull, KPIs, semáforos y plan preventivo, y los muestra en un panel. Funciona en la red local, sin internet.

- Especificación: `docs/plan_desarrollo.pdf` (el Plan).
- Diseño: `docs/PLAN_TECNICO.md`.
- Decisiones y dudas sobre la bibliografía: `docs/DECISIONES.md`.
- Formato de las planillas: `docs/plantillas/FORMATO.md`.
- Instalación en la mini PC: `docs/INSTALACION.md`.

## Estado por fase

| Fase | Estado | Qué funciona |
|---|---|---|
| 0. Preparación | **Hecha** | Base de datos con reglas y auditoría, importador de planillas, borrador del TP N.º 1, catastro y ficha PDF, QR, puesta en marcha guiada (12.A), usuarios y parámetros, datos DEMO |
| 1a. Captura | **Hecha** | Parte de turno (< 30 s), aviso de falla con QR y foto, tarjetas azul/roja/verde, bandeja del encargado, cierre de OT en 2 pasos (cierra y abre vidas), cambio preventivo, bandeja de validación con controles §11, corrección y anulación con motivo, partes faltantes y estimados, proceso de tareas (backup, prueba de restauración, nocturno), exportación total a Excel |
| 1b. Motor y KPIs | **Hecha** | Motor Weibull (Weibayes, RRX con bootstrap, MLE con censura por derecha e intervalo, RBA, IC por razón de verosimilitud), bondad de ajuste (r² crítico, AD, AICc), KPIs empíricos y Weibull, intervalo óptimo C(T), costos Cp/Cf desde parámetros, semáforo, Crow-AMSAA/Laplace, recálculo por evento y nocturno. Reproduce el Plan §15 y la UNIDAD 2; validado contra reliability, surpyval y lifelines; Monte Carlo |
| 1c. Panel (MVP) | **Hecha** | Panel de planta (tarjetas, línea en orden de proceso con semáforo, ranking de riesgo P×Cf, Pareto por horas/costo/frecuencia, tendencia mensual, calidad de datos), ficha de máquina (componentes con edad, β, η, P(Δ) con banda y vida remanente; gráfico de probabilidad; R(t) y h(t) con la edad; línea de tiempo; horas perdidas por motivo), análisis Weibull (vigente y alternativa, comparación de distribuciones, forzar método con justificación, curva C(T)), análisis de problemas (Pareto, sugerencias automáticas, 5 Porqués con PDCA y OT modificativa), tablero de comando (CMFT, CPCT, HPHP, TBMP, TBMC, OCPM), ayuda "?" en cada indicador, historia DEMO |
| 2. Piloto y extensión | **Hecha** | Pantalla del piloto (partes por semana, criterio de dos semanas con más del 90 %, uso de catálogos) y guion (`docs/guion_piloto.md`); catálogos editables; comparación "nuevos" contra "nuevos + histórico A/B"; flota (prueba de razón de verosimilitud y ajuste agrupado, por tipo o por equivalencia); alertas firmes solo con confianza media o alta (orientativas antes); criticidad guiada (TP y U1) y diagrama de cuadrantes de las fallas; puesta en marcha con criterios automáticos y enlaces |
| 3. Versión 2 | **Hecha** | Plan preventivo (aprobación del intervalo, del fabricante al calculado), calendario de 52 semanas en PDF y Excel (MANT/1CMP001-2CMP001), OT preventivas con anticipación e imprimibles (MANT/MPV001), pruebas funcionales de fallas ocultas, diagnóstico de sobre y sub-mantenimiento, repuestos (demanda en el lead time, Poisson, lote económico, stock de protección), predictivo (MANT/PMRED001, límites, tendencia, ultrasonido), tablero completo con CIT, Ishikawa/5M, 5W+1H y hoja de verificación, tabla de mortalidad y exponencial, alertas por mail (opcional), reporte PDF mensual y semanal, manuales por rol |
| 4. Mejoras | **Hecha** | Crow-AMSAA y Laplace por máquina (ficha y alerta semanal de degradación), Weibull bayesiano como comparación, TPM: RO = Dp·Di·Rv·Tq y seis grandes pérdidas (con piezas rechazadas en el parte), OEE completo, horómetro (horas medidas, nivel M), AMFE con ocurrencia calculada desde F(1 año) y NPR, revisión en t = η, bloques serie/paralelo |
| 5. Papel de Weibull y ayudas | **Hecha** | Gráfico de probabilidad como el papel de la cátedra (polo y abanico de β, línea del 63,2 % y η, lectura a un tiempo de misión), página "Papel de Weibull" para datos propios, criticidad sobre 100 de la planilla del grupo, burbujas de ayuda con el tema |

## Pendiente de verificar (no se inventó nada)

Todo lo que sigue funciona, pero depende de un dato o una fuente que el proyecto no tiene. Está marcado "a verificar" o "propuesta" en la pantalla y en `docs/DECISIONES.md`:

| Qué | Dónde se ajusta | Referencia |
|---|---|---|
| Escalas y cortes de la ponderación U1 de criticidad (no se recibió la UNIDAD 1) | Parámetros › criticidad | P-10, D-051 |
| Definición de disponibilidad D = (TO − ΣTA)/TO (UNIDAD 1) | — | D-007 |
| Tabla de prioridad de acción AIAG-VDA del AMFE (se carga a mano) | AMFE | B-018 |
| Cortes F(1 año) → ocurrencia O del AMFE (la escala del TP es cualitativa) | Parámetros › amfe.escala_ocurrencia | D-064 |
| Grilla exacta de MANT/1CMP001 y 2CMP001 (en las diapositivas es imagen) | — | B-017 |
| Ejemplos resueltos de Abernethy e IEC 61649 para validar el motor | — | test `xfail` |
| Umbrales propuestos: semáforo de clase A, sobre/sub-mantenimiento, piloto, sugerencias de análisis | Parámetros | D-012, D-057, D-050, D-042 |
| Costos reales: tarifa de mano de obra, margen por hora de la línea, tipo de cambio, K y b de inventarios | Parámetros › costos y políticas | Plan §12 |

**Antes de usar el sistema en serio:** borrar los datos DEMO (Configuración › Datos DEMO).

## Uso rápido (desarrollo)

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.lock
uv pip install --python .venv/bin/python --no-deps -e .

.venv/bin/circularis inicializar                 # crea la base y los datos iniciales
.venv/bin/circularis demo cargar                 # datos ficticios con historia, para probar (cartel rojo)
.venv/bin/circularis importar docs/plantillas/carga_inicial_borrador_TP1.xlsx --simular
.venv/bin/circularis app                         # http://localhost:8501
```

Usuarios DEMO: `demo.jefe` / `demo-jefe-2026`, `demo.operario` / PIN `1234` (ver `circularis demo cargar`).

## Cómo probar la fase 5

```bash
.venv/bin/circularis app                          # demo.jefe / demo-jefe-2026
.venv/bin/python -m pytest tests/asistente/test_papel_weibull.py tests/servicios/test_criticidad.py -v
```

- **Papel de Weibull** (menú Panel): viene con el ejemplo de la UNIDAD 2 (diap. 33–38): β ≈ 1,44, η ≈ 76 h y R(15 h) ≈ 90,8 %. Pegá tus tiempos desde Excel; si están en días, elegí "días" y cargá las horas por día.
- **Ficha de máquina** y **Análisis Weibull:** el mismo papel con los datos del componente, con la lectura en la edad actual. Pasá el mouse por las guías del abanico, el polo y la línea del 63,2 %.
- **Criticidad:** al evaluar una máquina aparece la criticidad sobre 100, como en la planilla del grupo.

## Cómo probar la fase 4

```bash
.venv/bin/circularis demo cargar
.venv/bin/circularis app                          # demo.jefe / demo-jefe-2026 (habilitar 12F y 12H en Parámetros › Módulos)
.venv/bin/circularis tareas --una-vez tendencias  # Crow-AMSAA y Laplace de cada máquina
.venv/bin/python -m pytest tests/servicios/test_fase4.py tests/motor/test_bayes.py -v
```

- **TPM y OEE:** la extrusora DEMO tiene cantidades y rechazos ficticios: Dp, Di, Rv, Tq y RO, y el gráfico de las seis grandes pérdidas.
- **Ficha de máquina › Tendencia de la máquina:** fallas acumuladas contra horas operadas con la curva de Crow-AMSAA y la prueba de Laplace.
- **Análisis Weibull › Weibull bayesiano:** el β de referencia como previa, al lado del método vigente.
- **AMFE:** la O calculada de las cuchillas (F de un año de uso) al lado de la O del TP; NPR y AP a mano.
- **Herramientas › Bloques serie y paralelo:** precargar con los componentes críticos de una máquina.

## Cómo probar la fase 3

```bash
.venv/bin/circularis demo cargar
.venv/bin/circularis app                          # demo.jefe / demo-jefe-2026
.venv/bin/circularis tareas --una-vez plan        # reprograma el calendario y genera las OT
.venv/bin/python -m pytest tests/servicios/test_fase3.py tests/asistente tests/motor/test_tendencia.py -v
```

- En **Parámetros › Módulos**, habilitar 12E, 12G y 12H para ver el tablero completo, el predictivo y las herramientas.
- **Plan preventivo:** aprobar el intervalo calculado de las cuchillas (≈ 425 h, óptimo por costo); en *Calendario* aparece la grilla y se descargan el PDF y el Excel; en *Órdenes de trabajo*, la OT imprimible (MANT/MPV001). Para la válvula de seguridad, aprobar una prueba funcional cada 30 días.
- **Repuestos:** demanda esperada en el lead time y stock mínimo de cada repuesto. Cargar K y b en Parámetros (grupo políticas) para ver el lote económico.
- **Predictivo:** agregar un parámetro de ultrasonido con línea base 30 dB y cargar mediciones (38, 41, 47): alerta, vigilar y OT de inspección.
- **Análisis de problemas › Nuevo análisis:** Ishikawa (con su espina de pescado), 5W+1H u hoja de verificación (precargada con los avisos).
- **Reportes:** PDF del mes. Manuales por rol en `docs/manuales/`.

## Cómo probar la fase 2

```bash
.venv/bin/circularis demo cargar
.venv/bin/circularis app                 # demo.jefe / demo-jefe-2026
.venv/bin/python -m pytest tests/servicios/test_fase2.py -v
```

- **Piloto:** con la demo, las tres máquinas cumplen el criterio (100 % de partes). En una base real, cargar `piloto.maquinas` en Parámetros.
- **Panel de planta › Alertas de riesgo:** las dos alertas de la demo son orientativas (confianza baja o gris). Bajando `alertas.confianza_firme` a BAJA pasan a firmes en el próximo recálculo.
- **Análisis Weibull:** elegir "DEMO-AGR-001 · Rulemanes"; abajo, la sección **Flota** con la prueba de razón de verosimilitud (p > 0,05: se pueden agrupar) y el ajuste de los rulemanes de las dos máquinas.
- **Criticidad:** responder las seis preguntas de una máquina; con "Ponderación UNIDAD 1" la clase se elige a mano hasta cargar `criticidad.u1_cortes`.
- **Catálogos:** agregar un síntoma o desactivar uno; nada se borra.
- **Puesta en marcha:** cada etapa con su control y un enlace a la pantalla.

## Cómo probar la fase 1c

```bash
.venv/bin/circularis demo cargar        # catálogo + unos dos años y medio de historia ficticia + recálculo (~5 s)
.venv/bin/circularis app                # entrar como demo.jefe / demo-jefe-2026
.venv/bin/python -m pytest tests/servicios/test_panel.py tests/asistente tests/app -v
```

Qué mirar con la demo:

- **Panel de planta:** DEMO-AGR-001 en rojo (cuchillas con 15 % de probabilidad de falla en el horizonte y edad mayor al intervalo) y DEMO-EXT-001 en rojo (husillo con Weibayes; la válvula queda gris por edad desconocida). Ranking de riesgo en pesos y Pareto de horas de parada.
- **Ficha de máquina:** el gráfico de probabilidad de las cuchillas (β ≈ 3,6, desgaste) y las curvas R(t) y h(t) con la edad actual.
- **Análisis de problemas:** la sugerencia de los rulemanes de la agrumadora (β cerca de 1, fallas al azar, confianza media): "Iniciar 5 Porqués", completar los porqués y la acción, generar la OT modificativa y avanzar el PDCA.
- **Tablero:** los ratios que el sistema puede calcular solo (CPCT, HPHP) y "falta dato" en los que necesitan la facturación o las horas-hombre disponibles hasta que el jefe las carga.
- **Gerencia** (`demo.gerencia` / `demo-gerencia-2026`) entra directo al panel; el **operario** ve la ficha sin costos.

## Cómo probar la fase 1b

```bash
printf "edad,estado\n300,S\n410,F\n560,F\n650,S\n690,F\n780,F\n920,F\n" > plan15.csv
.venv/bin/circularis weibull plan15.csv --edad 520 --delta 160   # β 3,42; η 774; P = 32 %
.venv/bin/python -m pytest tests/motor -v                          # casos de referencia de la sección 13
MC_REPLICAS=2000 .venv/bin/python -m pytest -m lento               # Monte Carlo exhaustivo (lento)
```

Con el proceso de tareas andando, al validar un aviso el par se recalcula en segundos (cola) y cada noche se recalcula todo.

## Cómo probar la fase 1a

1. `circularis demo cargar` y `circularis iniciar-captura`. Levantar `circularis app` y, en otra consola, `circularis tareas`.
2. Desde el celular, entrar como `demo.operario` (PIN 1234): *Reportar falla* y después *Parte de turno*.
3. Como `demo.encargado`: *Bandeja del encargado* → *Cerrar OT* (2 pasos).
4. Como `demo.jefe`: *Bandeja de validación* → *Aprobar*. Probar *Corregir un aviso ya validado* (pide motivo).
5. `circularis tareas --una-vez backup` y `--una-vez prueba_restauracion` (ver `docs/BACKUP.md`).
6. Prueba con operarios reales: `docs/guion_usabilidad.md`.

## Cómo probar la fase 0

1. `circularis inicializar` y después `circularis crear-usuario jefe "Nombre" JEFE`.
2. Entrar a la app como jefe. En **Puesta en marcha**, descargar el *Borrador con datos del TP N.º 1*.
3. Revisarlo en Excel: confirmar los códigos, cargar los turnos, la autonomía de pulmón, el catastro y los repuestos.
4. En **Carga de planillas**: primero *Simular* y después *Importar*.
5. En **Máquinas y revisión**: completar el catastro, marcar las posiciones críticas y *Marcar como revisada* cada máquina.
6. Imprimir las **etiquetas QR** y plastificarlas.

Criterio de salida: las 10 máquinas del listado y sus componentes cargados y revisados por el jefe (`circularis revision`).

## Tests

```bash
.venv/bin/python -m pytest            # rápidos (excluye Monte Carlo largo)
.venv/bin/python -m pytest -m lento   # exhaustivos
.venv/bin/ruff check circularis_rel tests scripts
```

## Estructura

```
circularis_rel/
  app/         páginas Streamlit por rol (inicio.py + paginas/)
  servicios/   auth, permisos, parámetros, importador, catastro, QR, PDF, demo
  motor/       confiabilidad (sin Streamlit ni base de datos)
  asistente/   módulo 12: puesta en marcha, criticidad, ayudas
  datos/       modelos, auditoría, semillas, migraciones
  tareas/      procesos programados
scripts/       borrador TP1, plantillas, migración inicial
seeds/tp1/     transcripción del AMFE del TP N.º 1 (valores ilustrativos)
tests/
docs/
```

Licencia: Apache-2.0. Propiedad de Circularis.
