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
| 1c. Panel (MVP) | Pendiente | |
| 2. Piloto y extensión | Pendiente | |
| 3. Versión 2 | Pendiente | |
| 4. Mejoras | Pendiente | |

## Uso rápido (desarrollo)

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.lock
uv pip install --python .venv/bin/python --no-deps -e .

.venv/bin/circularis inicializar                 # crea la base y los datos iniciales
.venv/bin/circularis demo cargar                 # datos ficticios para probar (cartel rojo)
.venv/bin/circularis importar docs/plantillas/carga_inicial_borrador_TP1.xlsx --simular
.venv/bin/circularis app                         # http://localhost:8501
```

Usuarios DEMO: `demo.jefe` / `demo-jefe-2026`, `demo.operario` / PIN `1234` (ver `circularis demo cargar`).

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
