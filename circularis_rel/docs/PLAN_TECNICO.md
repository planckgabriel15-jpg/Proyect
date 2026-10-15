# Plan técnico: sistema de confiabilidad Weibull para Circularis (línea T-WOOD)

**Estado:** propuesta. **No hay código de aplicación todavía.** Espera tu OK y las respuestas de la sección 12.
**Fecha:** 15/10/2026.
**Fuentes leídas completas:** `docs/plan_desarrollo.pdf` (el "Plan", 34 págs.) y la bibliografía de la cátedra del Mgter. Leandro D. Torres (UTN-FRC): UNIDAD 2 (fiabilidad, 40 diapositivas), UNIDAD 3 (tipos de mantenimiento, 53), UNIDAD 4 (TPM, 59), UNIDAD 5 (tablero de comando, costos e inventarios, 69) y UNIDAD 6 (sistemas informáticos, 33).
**Falta:** la **UNIDAD 1**, que el pedido usa para la criticidad por ponderaciones (12.C) y la definición de disponibilidad (§6). Ver pregunta P-10.

Documentos que acompañan a este plan:

- `docs/DECISIONES.md`: decisiones tomadas (D-xxx) y dudas sobre la bibliografía (B-xxx), cada una con qué, por qué y la alternativa descartada.
- `docs/plan_desarrollo.pdf`: copia del Plan, que es la especificación funcional.

---

## Índice

1. Resumen
2. Verificación previa del motor (ya hecha, sin código de aplicación)
3. Arquitectura
4. Stack y versiones
5. Esquema de base de datos
6. Módulos y responsabilidades
7. Motor de confiabilidad: diseño detallado
8. Pantallas, roles y permisos
9. Plan de pruebas
10. Fases, orden de construcción y criterios de aceptación
11. Riesgos y mitigaciones
12. Preguntas abiertas (necesito tus respuestas)
13. Convenciones del repositorio

---

## 1. Resumen

El sistema tiene tres piezas que no se mezclan:

1. **Captura** (Streamlit en el celular, la tablet y la PC): parte de turno, aviso de falla, tarjetas TPM, cierre de OT y validación.
2. **Motor de confiabilidad** (Python puro, sin Streamlit ni base de datos): Weibull, KPIs, semáforo, políticas y costos. Recibe datos y devuelve resultados. Se usa desde los servicios, la línea de comandos y los tests.
3. **Servicios y tareas**: leen la base, llaman al motor, guardan resultados con trazabilidad y corren el recálculo, las alertas, los mails y el backup.

El orden de construcción respeta el Plan: primero la captura, porque cada semana sin datos es una semana menos de historia. El motor se escribe con TDD contra los casos de la sección 9 **antes** de cualquier pantalla que lo muestre.

**Cronograma real.** Hoy es 15/10. Según el Plan, la fase 0 ya tendría que estar cerrada y el hito "datos reales en planta" es el 20/10. Propongo la replanificación de la sección 10.3: fase 0 mínima y fase 1a en paralelo, con captura en planta el **21–22/10** si recibo las planillas del TP y está la mini PC. El motor (1b) puede avanzar en paralelo porque no depende de pantallas.

---

## 2. Verificación previa del motor

Antes de planificar quise saber si los valores publicados se pueden reproducir con las librerías elegidas. Armé un entorno descartable (fuera del repo) con Python 3.13, NumPy 2.5.4, SciPy 1.18.1, `reliability` 0.9.0, `surpyval` 0.24 y `lifelines` 0.30.3, y recalculé los ejemplos. **Todas las librerías instalan e importan sin errores con NumPy 2.x.**

### 2.1 Ejemplo del Plan §15 (cuchillas AGR-001)

Datos: 300 S, 410 F, 560 F, 650 S, 690 F, 780 F, 920 F. Vida 8 (520 h, en servicio) solo para el pronóstico.

| Magnitud | Publicado | Obtenido | ¿Reproduce? |
|---|---|---|---|
| Rangos ajustados de Johnson | 1,14 / 2,29 / 3,71 / 5,14 / 6,57 | 1,14 / 2,29 / 3,71 / 5,14 / 6,57 | Sí |
| F mediana (Benard) | 11,4 / 26,8 / 46,1 / 65,4 / 84,7 % | 11,4 / 26,8 / 46,1 / 65,4 / 84,7 % | Sí |
| RRX: β, η, r² | 3,42; 774 h; 0,996 | 3,422; 774,3 h; 0,9962 | Sí (también con `reliability`, `method='RRX'`) |
| MLE: β, η | 4,75; 761 h | 4,749; 760,5 h | Sí (`reliability` y `surpyval` coinciden) |
| **IC 90 % del MLE** | **β 2,7–8,4; η 650–890** | Razón de verosimilitud: **β 2,47–7,89; η 638–924**. Matriz de Fisher: **β 2,69–8,39; η 650–890** | **Solo con Fisher.** Ver D-004 y P-09 |
| MTTF, B10, R(520) | 696 h; 401 h; 77,4 % | 695,8 h; 401,1 h; 77,41 % | Sí |
| P(falla en 80/160/240 h \| 520 h) | 14,9 / 32,0 / 49,4 % | 14,94 / 31,97 / 49,45 % | Sí |
| Vida remanente mediana / al 90 % | 243 h / 55 h | 242,6 h / 55,1 h | Sí |
| C(T) en 300/350/370/400/450/500 h | 1,62 / 1,55 / 1,54 / 1,56 / 1,62 / 1,73 | 1,615 / 1,549 / 1,544 / 1,556 / 1,618 / 1,725 | Sí |
| T* y costo hasta la falla | ≈ 370 h; 3,59 USD/h | 369,2 h (1,544 USD/h); 3,593 USD/h | Sí |
| MTBF, MTTR, Ai de la máquina | 539 h; 4,5 h; 99,2 % | 538,75 h; 4,5 h; 99,17 % | Sí |

**Hallazgo importante.** El Plan (§5) dice que el MLE usa límites de razón de verosimilitud y que la matriz de Fisher se evita con pocos datos. Pero el IC publicado en §15 (2,7–8,4 / 650–890) es exactamente el de **matriz de Fisher** con transformación logarítmica al 90 % bilateral, que es lo que `reliability` devuelve por defecto. Con razón de verosimilitud el intervalo es otro. Propuesta (D-004): el sistema usa razón de verosimilitud, como manda la regla. El test 1 verifica el IC publicado con una función de Fisher que existe **solo para validación cruzada** y verifica también los límites de razón de verosimilitud que obtuve. No ajusto el test: documento la causa.

### 2.2 Caso 2: la vida en servicio entra como suspensión

Con la suspensión de 520 h agregada (5 fallas, 3 suspensiones): RRX β = 3,582 y η = 781,3 h (r² = 0,998); MLE β = 4,93 y η = 766,6 h. **η sube (774 → 781 h), como corresponde.** Se cumple la propiedad que pediste. Queda registrado en D-002.

### 2.3 Casos de la bibliografía

| Caso | Publicado | Obtenido | Comentario |
|---|---|---|---|
| UNIDAD 2, Weibull (16, 34, 53, 75, 93, 120 h) | β ≈ 1,4; η ≈ 76 h; R(15) ≈ 90,2 % | RRX: β 1,440; η 76,1 h; R(15) = 90,8 % | Dentro de la tolerancia (±10 %, ±2 puntos). La diapositiva usa β redondeado a 1,4 y η leído del gráfico |
| UNIDAD 2, válvulas | λ = 0,04/año; F(4 meses) = 1,32 %; R(6 meses) = 0,98 | 1,324 %; 0,9802 | Sí |
| UNIDAD 2, tabla de mortalidad de motores | MTTF = 8,83 meses; F = 0,100 / 0,450 / 0,744 / 0,900 / 0,967 / 1,000 | 8,8389 meses; F idéntica | La diapositiva trunca 8,8389 a 8,83 (B-001) |

### 2.4 Rendimiento

- Importar `reliability`: 1,7 s, una sola vez por proceso.
- Ajuste MLE de 7 datos con IC: 0,11 s.
- `Fit_Everything` con todas las distribuciones: 6 s. Lo restrinjo a Weibull 2P, Weibull 3P, lognormal y exponencial.
- Tabla del valor crítico de r² (percentil 10) por Monte Carlo, n = 3…100, 20.000 réplicas por n: 0,5 s. Ejemplo: n = 5 → r²crit ≈ 0,806, así que el r² = 0,996 del §15 lo supera con holgura, como dice el Plan.

**Conclusión:** el recálculo por evento (solo el par afectado) entra en el objetivo de "segundos". El bootstrap del IC de RRX (≈ 2.000 réplicas) puede tardar unos segundos más y lo corre el proceso de tareas (sección 3.3).

---

## 3. Arquitectura

### 3.1 Vista general

```
                 Wifi de planta (red local, sin internet)
 Celular operario ─┐
 Tablet encargado ─┼──► http(s)://192.168.x.x:8501
 PC jefe/gerencia ─┘            │
                                ▼
┌──────────────────────── Mini PC de planta ─────────────────────────┐
│  Proceso 1: app Streamlit (circularis_rel.app)                     │
│     páginas por rol ─► servicios ─► datos (SQLAlchemy)             │
│                              └────► motor (Python puro)            │
│                                                                    │
│  Proceso 2: tareas (circularis_rel.tareas, APScheduler)            │
│     cola de recálculo · recálculo nocturno · alertas · mails ·     │
│     backup · prueba de restauración · partes faltantes             │
│                              └────► servicios ─► motor / datos     │
│                                                                    │
│  Archivos: datos/circularis.db (SQLite WAL) · datos/fotos/ ·       │
│            datos/backups/ · logs/                                  │
└────────────────────────────────────────────────────────────────────┘
         │ backup nocturno                │ mail (si hay SMTP)
         ▼                                ▼
  Disco externo o carpeta sincronizada   Jefe, encargado, gerencia
  con Google Drive
```

### 3.2 Capas y reglas de dependencia

| Capa | Paquete | Puede importar | No puede importar |
|---|---|---|---|
| Interfaz | `app/` | `servicios`, `motor` (solo tipos y funciones de formato), `asistente` | `datos` directamente (todo pasa por servicios) |
| Asistente (módulo 12) | `asistente/` | `servicios`, `motor` | `streamlit` en la lógica; las pantallas viven en `app/` |
| Servicios | `servicios/` | `datos`, `motor` | `streamlit` |
| Motor | `motor/` | `numpy`, `scipy`, `pandas`, `reliability`, `surpyval`, `lifelines` | `streamlit`, `sqlalchemy`, `datos`, `servicios` |
| Datos | `datos/` | `sqlalchemy`, `alembic`, `pydantic`, `openpyxl` | `streamlit`, `motor` |
| Tareas | `tareas/` | `servicios` | `streamlit` |

Un test (`tests/test_arquitectura.py`) recorre los imports con `ast` y falla si `motor/` importa Streamlit, SQLAlchemy o cualquier módulo propio fuera del motor. Así el motor sigue siendo reutilizable si algún día se migra la interfaz, como pide el Plan §9.

### 3.3 Dos procesos

APScheduler no corre dentro de Streamlit. Streamlit re-ejecuta el script en cada interacción y por cada sesión, así que un planificador ahí adentro se duplicaría o moriría con la sesión. Por eso hay **dos procesos**, los dos instalados como servicio que arranca con la PC (pregunta P-01):

- **app:** atiende a los usuarios. Las escrituras son transacciones cortas.
- **tareas:** APScheduler con:
  - una cola de recálculo (tabla `recalculo_pendiente`) que se revisa cada 5 s;
  - el recálculo nocturno a las 02:00;
  - los resúmenes diario y semanal;
  - el backup a las 03:00;
  - la prueba de restauración mensual;
  - el control de partes faltantes al inicio de cada día.

**Recálculo por evento.** Al validar un evento, el servicio de validación guarda el cambio y, **en la misma transacción**, inserta una fila en la cola para el par (tipo de componente, modo). El proceso de tareas la toma en ≤ 5 s:

1. Hace el ajuste puntual y el IC por razón de verosimilitud (menos de 1 s).
2. Guarda el resultado y actualiza el semáforo.
3. Recién después corre el bootstrap de RRX y completa el IC.

Mientras tanto la pantalla muestra "recalculando…". El jefe ve el semáforo nuevo en segundos y la interfaz nunca se congela.

### 3.4 Concurrencia con SQLite (~15 usuarios)

Volumen esperado: decenas de escrituras por día y picos de unas 15 cargas en los cambios de turno. SQLite alcanza si se cumplen estas reglas:

- **WAL** (`PRAGMA journal_mode=WAL`): los lectores no bloquean al escritor ni el escritor a los lectores.
- `PRAGMA busy_timeout=10000`, `synchronous=NORMAL`, `foreign_keys=ON`. Se aplican en cada conexión con un *event listener* de SQLAlchemy.
- **Transacciones cortas** con `BEGIN IMMEDIATE` en las escrituras, para que dos escritores no entren en *deadlock* al subir de lectura a escritura. Ningún cálculo pesado corre dentro de una transacción.
- **Un solo engine por proceso**, compartido entre sesiones con `st.cache_resource`. La sesión de SQLAlchemy dura un request (`with Session() as s:`) y nunca se guarda en `st.session_state`.
- **Reintento** acotado (3 veces) ante `database is locked`, y un mensaje claro si igual falla ("No se pudo guardar, probá de nuevo").
- **Idempotencia** en las cargas del celular: cada formulario lleva un token de envío. Un doble toque con mala señal no genera dos partes. Además están las restricciones `UNIQUE` de la base.
- **Bloqueo optimista** en la bandeja de validación: columna `version` en `evento_falla`. Si dos personas editan el mismo evento, la segunda recibe "Este aviso fue modificado por X, recargá".

Si algún día hace falta más (multiplanta, cientos de usuarios), el cambio a PostgreSQL es de configuración: todo el acceso pasa por SQLAlchemy y los índices parciales se declaran con `sqlite_where` y `postgresql_where`.

### 3.5 Estado de sesión y autenticación

Detalle y alternativas en la pregunta P-02. Resumen de la propuesta:

- **Login** con `streamlit-authenticator` 0.4.2 (MIT) **solo** para el formulario y la cookie firmada que mantiene la sesión abierta entre recargas. Esto último es lo difícil de hacer a mano en Streamlit.
- **Usuarios y roles** viven en la tabla `usuario`, con contraseña hasheada con bcrypt. El diccionario de credenciales que necesita la librería se arma desde la base al iniciar y cuando cambia un usuario. No uso el YAML de la librería, así que el alta y la baja de usuarios quedan en la auditoría.
- **Adaptador propio** (`servicios/auth.py`): si la librería cambia su API o se abandona, se reemplaza un solo archivo.
- **Navegación por rol** con `st.navigation`: cada rol solo ve sus páginas. Además, cada servicio verifica el permiso, porque ocultar una página no alcanza.
- **Operarios:** cookie de 30 días en su celular. Pregunta P-12 sobre PIN corto.

### 3.6 Fotos, QR y HTTPS

- **Foto del aviso:** uso `st.file_uploader` con `accept=image/*`. En el celular abre directamente la cámara nativa y **funciona por HTTP**. `st.camera_input` exige contexto seguro (HTTPS) en los navegadores móviles: por HTTP en la red local no funciona. Las fotos se reducen a 1.280 px con Pillow y se guardan en `datos/fotos/AAAA/MM/`. La base guarda la ruta y las fotos entran en el backup.
- **QR plastificado:** codifica la URL `http://192.168.x.x:8501/?maq=AGR-001`. La cámara del celular la abre sin app; la página toma `st.query_params["maq"]` y deja la máquina preseleccionada. Se generan con `segno` como PDF imprimible: una hoja A4 con 8 etiquetas, código grande legible y la leyenda "Circularis · Reportar falla / Parte de turno".
- **HTTPS:** opcional, pregunta P-01. Sin HTTPS, las contraseñas viajan sin cifrar por el wifi de planta. Es un riesgo bajo en una red cerrada, pero hay que decidirlo.

### 3.7 Trazabilidad

- **Auditoría:** un *listener* `before_flush` de SQLAlchemy recorre los objetos modificados de los modelos auditados y escribe una fila por campo cambiado en `auditoria` (usuario, fecha, tabla, id, campo, valor anterior, valor nuevo, motivo, acción). El usuario y el motivo viajan en un contexto de la sesión. Si el registro está validado y no hay motivo, el flush **falla** con `MotivoRequerido`. La regla vale aunque alguien llame a la base sin pasar por la pantalla.
- **Resultados de Weibull:** guardan método, versión del motor (`motor.__version__`, semver), n de fallas, suspensiones e intervalos, nivel del IC, método del IC, conjunto de datos (solo nuevos o nuevos + histórico A/B) y un hash del vector de datos. Con eso se puede reproducir cualquier resultado.
- **Método forzado por el jefe:** queda en `resultado_weibull.forzado = true`, con justificación, y también en la auditoría.

### 3.8 Backup y salida

- **Backup diario a las 03:00:** usa la API de backup en línea de SQLite (`sqlite3.Connection.backup`), que es consistente aunque haya usuarios conectados, más un zip de las fotos. Se rota a 30 copias diarias y 12 mensuales. Se copia a un **disco externo** o a una **carpeta sincronizada por Google Drive para escritorio**. Así no hace falta integrar la API de Drive y el backup funciona sin internet: se sube cuando vuelve la conexión.
- **Restauración:** `python -m circularis_rel.tareas.restaurar <archivo>`. El script tiene su test. Además, cada mes el proceso de tareas restaura el último backup en una carpeta temporal, corre `PRAGMA integrity_check`, compara conteos de filas y deja el resultado en el panel del jefe.
- **Exportación total a Excel:** un libro con una hoja por tabla, botón en Configuración y en Reportes. La empresa nunca queda atada al software.

---

## 4. Stack y versiones

### 4.1 Versiones propuestas

Las versiones se fijan en `pyproject.toml`, con rangos compatibles, y en `requirements.lock`, con versiones exactas y hashes generados con `pip-compile`. Las del núcleo numérico ya las probé juntas (sección 2).

| Paquete | Versión | Licencia | Nota |
|---|---|---|---|
| Python | **3.12** (probado también en 3.13) | PSF | 3.12 tiene ruedas binarias maduras en Windows para todo el stack |
| numpy | 2.5.x | BSD | Probado |
| scipy | 1.18.x | BSD | Probado |
| pandas | 2.3.x | BSD | |
| reliability | 0.9.0 | **LGPL-3.0** | Probado. Se usa como librería sin modificarla, compatible con cualquier licencia del proyecto (sección 13). Un solo mantenedor: va detrás de un adaptador y se valida contra `surpyval` y contra mis fórmulas |
| surpyval | 0.24 | MIT | Probado: censura por intervalo y truncamiento |
| lifelines | 0.30.3 | MIT | Probado: Kaplan-Meier y validación cruzada |
| streamlit | 1.5x–1.66 | Apache-2.0 | Se fija la versión con la que pasen los tests de interfaz (`streamlit.testing.v1.AppTest`) |
| streamlit-authenticator | 0.4.2 | MIT | Detrás del adaptador `servicios/auth.py` |
| SQLAlchemy | 2.0.x | MIT | |
| alembic | 1.x | MIT | |
| pydantic | 2.x | MIT | Validación de formularios e importador |
| plotly | 5.x/6.x | MIT | Pantalla |
| matplotlib | 3.x | PSF | PDF |
| openpyxl | 3.1.x | MIT | |
| **PDF** | WeasyPrint 70 (Docker) **o** fpdf2 (Windows nativo) | BSD / LGPL | En Windows, WeasyPrint necesita Pango/GTK instalado aparte (MSYS2) y es frágil. Propongo fpdf2 si la instalación es nativa (pregunta P-01) |
| APScheduler | 3.10.x | MIT | Uso la serie 3.x, estable. La 4.x cambió la API |
| segno | 1.6.x | BSD | QR sin dependencias |
| Pillow | 11.x | HPND | Fotos |
| pytest, hypothesis, pytest-cov | últimas | MIT/MPL | |
| ruff | última | MIT | Lint y formato |

### 4.2 Qué uso de cada librería y qué implemento yo

| Necesidad | Fuente | Por qué |
|---|---|---|
| Rangos de Johnson y Benard, RRX | **Propio** (unas 30 líneas, verificado) y validado contra `reliability` RRX | Necesito los rangos ajustados para mostrarlos y para el bootstrap |
| MLE 2P con censura por derecha | `reliability.Fit_Weibull_2P` (MLE), validado contra `surpyval` | |
| MLE con censura por intervalo (histórico B) | `surpyval` | `reliability` no cubre bien el intervalo |
| IC por razón de verosimilitud | **Propio** (perfil de verosimilitud con `scipy.optimize`) | `reliability` da Fisher por defecto |
| Bootstrap paramétrico de RRX | **Propio** | No existe en las librerías |
| RBA (corrección de sesgo) | **Propio**: β_RBA = β_MLE · C4^3,5, con C4 de N = n.º de fallas | Pregunta P-03 |
| Valor crítico de r² (percentil 10) | **Propio**: tabla generada por Monte Carlo con semilla fija, guardada como CSV versionado | Pregunta P-03 |
| Anderson-Darling con censura y AICc | `reliability.Fit_Everything` restringido a 4 distribuciones | |
| Weibayes | **Propio** (fórmula del Plan) | |
| Crow-AMSAA y Laplace | **Propio** (MLE con terminación por tiempo) y validado contra `reliability.Repairable_systems` | |
| Intervalo óptimo C(T) | **Propio** (`scipy.integrate.quad` + `minimize_scalar`) y validado contra `reliability.Repairable_systems.optimal_replacement_time` | Necesito la curva completa |
| Kaplan-Meier | `lifelines` | Validación y gráficos |
| Prueba de razón de verosimilitud de flota | **Propio** | |
| Poisson para el stock | `scipy.stats.poisson` | |

---

## 5. Esquema de base de datos

**Convenciones:**

- Nombres en español, `snake_case`, sin tildes.
- PK entera `id`.
- Códigos legibles (`AGR-001`) como `UNIQUE` aparte, para que renombrar no rompa claves.
- Fechas y horas guardadas como *timestamp* con zona `America/Argentina/Cordoba` y normalizadas a UTC en la base.
- Importes en pesos con su fecha. El valor en dólares se calcula con `tipo_cambio`.
- Los enumerados son `CHECK` de base y además `Enum` de Python.

Marco con **[12]** los campos agregados desde el inicio para el módulo del asistente.

### 5.1 Estructura de planta (ISO 14224: línea → máquina → posición → tipo)

**`linea`**: `id`, `codigo` UNIQUE, `nombre`.

**`activo`** (máquina)

| Campo | Tipo | Regla |
|---|---|---|
| `codigo` | texto | UNIQUE, formato `AAA-000` (AGR-001, EXT-001) |
| `nombre`, `ubicacion`, `funcion` | texto | |
| `id_linea` | FK | |
| `etapa_proceso` | enum | preprocesado, lavado, secado, formulación, extrusión, acondicionamiento |
| `orden_proceso` | entero | Para dibujar el esquema de la línea |
| `horas_promedio_dia` | real | Del listado del TP. Se usa para los partes estimados (nivel E) |
| `unidad_produccion` | enum | kg, fardos, durmientes, ninguna |
| `factor_toneladas` | real | Toneladas por unidad. Habilita la edad en toneladas |
| `criticidad_puntaje`, `criticidad_clase` (A/B/C), `criticidad_metodo` (TP / ponderación U1) | | La evaluación completa está en `criticidad_evaluacion` |
| `autonomia_pulmon_h` | real ≥ 0 | Para el lucro cesante |
| `ciclo_teorico_s` | real | Para RO y OEE (12.F). Opcional |
| [12] `numero_serie`, `fabricante`, `modelo`, `proveedor`, `fecha_instalacion` | | Catastro (UNIDAD 6, MANT/RHM001) |
| [12] `ancho_mm`, `alto_mm`, `largo_mm`, `peso_kg`, `condiciones_almacenamiento`, `caracteristicas_tecnicas`, `ruta_documentos` | | Catastro; `ruta_documentos` apunta a planos, manuales y catálogos |
| `activo` | bool | Baja lógica |

**`tipo_componente`**: `codigo` UNIQUE, `nombre` (lenguaje de planta: "cuchillas", "criba", "rulemanes"), `variable_edad` (HORAS/TONELADAS), `hh_preventiva`, `hh_correctiva`, `beta_ref` y `eta_ref` (opcionales), `fuente_ref` (texto obligatorio si hay β de referencia, porque el supuesto queda declarado), [12] `uso` (COMUN/ESPECIFICO), [12] `intervalo_fabricante` + `unidad_intervalo_fabricante`, [12] `falla_oculta` (bool), `funcion_seguridad` (bool), `intervalo_pf` (opcional, en la unidad de edad).

**`posicion_componente`**: `id_activo`, `id_tipo_componente`, `codigo` (UNIQUE por activo, p. ej. `AGR-001/CUCH`), `ubicacion`, `cantidad`, `critica` (bool: entra en el color de la máquina). **Restricción:** UNIQUE (`id_activo`, `codigo`).

**`catalogo`**: `tipo` ∈ {SINTOMA, MODO, CAUSA}, `codigo`, `descripcion`, `icono` (para el aviso con íconos), `activo`. UNIQUE (`tipo`, `codigo`).
**`catalogo_aplica`**: (`id_catalogo`, `id_tipo_componente`). Arma las **listas cerradas filtradas**: el modo y la causa deben pertenecer al tipo de componente. Se valida en el servicio y en un trigger de base.

**`motivo_parada`**: `codigo`, `descripcion`, `cuenta_como_requerida` (bool; **falso** para "sin demanda" y "huelga", ver D-007), `es_falla` (bool), [12] `categoria_6p` ∈ {AVERIA, PREPARACION_AJUSTE, VACIO_PARADAS_CORTAS, VELOCIDAD_REDUCIDA, CALIDAD_REPROCESO, PUESTA_EN_MARCHA, NULL}, `es_setup` (bool, para Dp).

**`turno`**: `codigo`, `nombre`, `hora_inicio`, `hora_fin`, `duracion_h`.
**`activo_turno`**: qué turnos son laborables para cada máquina y qué días de la semana. Sirve para detectar partes faltantes. **`feriado`**: `fecha`, `descripcion`. Pregunta P-11.

### 5.2 Captura

**`parte_turno`**

| Campo | Regla |
|---|---|
| `id_activo`, `fecha`, `id_turno` | **UNIQUE** (control "parte duplicado") |
| `horas_turno` | Duración del turno (copia de `turno.duracion_h`, editable) |
| `estado` | TODO / PARCIAL / NO_OPERO |
| `horas_no_operadas` | Múltiplo de 0,5. CHECK 0 ≤ h ≤ `horas_turno`. TODO ⇒ 0; NO_OPERO ⇒ `horas_turno` |
| `horas_operadas` | Se guarda = `horas_turno − horas_no_operadas` (CHECK de coherencia) |
| `id_motivo` | Obligatorio si `horas_no_operadas > 0` |
| `cantidad_procesada` | Opcional, en `activo.unidad_produccion` |
| `nivel_hora` | M / D / E. Los partes completados por el sistema son E |
| `origen` | OPERARIO / ESTIMADO_SISTEMA / IMPORTADO |
| `id_usuario`, `creado_en`, `token_envio` | `token_envio` es UNIQUE (idempotencia) |

**`evento_falla`**

| Campo | Regla |
|---|---|
| `id_activo` | |
| `id_posicion` | Nulo en el aviso; **obligatorio al cerrar** |
| `fecha_hora_falla` | No futura |
| `id_sintoma` | Aviso |
| `id_modo`, `id_causa` | Cierre; deben pertenecer al tipo de la posición |
| `inicio_reparacion`, `fin_reparacion`, `tiempo_espera_h`, `tiempo_reparacion_h` | Fin > inicio ≥ falla |
| `parada_total` (bool), `horas_parada` | |
| [12] `efecto` (PRODUCCION/CALIDAD/SEGURIDAD/AMBIENTE), `capacidad` (TOTAL/PARCIAL), `aparicion` (REPENTINA/PROGRESIVA) | Opcionales para el operario, obligatorios para el encargado al cerrar |
| `estado` | AVISADO → EN_REPARACION → CERRADO → VALIDADO; también DEVUELTO y ANULADO |
| `origen` | AVISO / TARJETA_ROJA / INSPECCION / PRUEBA_FUNCIONAL |
| `id_usuario_alta`, `id_usuario_cierre`, `id_usuario_validacion`, `validado_en` | |
| `observaciones` | Único texto libre |
| `version` | Bloqueo optimista |

**`orden_trabajo`**

- `numero` UNIQUE.
- `tipo` ∈ {CORRECTIVA, PREVENTIVA, INSPECCION, PRUEBA_FUNCIONAL, AUTONOMO, MODIFICATIVO}.
- `id_activo`, `id_posicion`, `id_evento` (UNIQUE si no es nulo: una OT correctiva por evento), `id_plan`.
- `fecha_programada`, `inicio_real`, `fin_real`.
- `estado` ∈ {SOLICITADA, PLANIFICADA, EN_EJECUCION, CERRADA, VALIDADA}.
- `responsable`, `hh_propias`, `hh_externas`, `costo_externo_ars`, `prioridad`.
- `accion` ∈ {REEMPLAZO, REPARACION_MINIMA, AJUSTE, INSPECCION_OK, INSPECCION_FALLA}.
- `herramientas` (texto) y `tareas` (detalle numerado en `ot_tarea`: n.º, descripción, observaciones, tiempo; formato MANT/MPV001).

**`vida_componente`**

| Campo | Regla |
|---|---|
| `id_posicion`, `fecha_instalacion`, `fecha_fin` | `fecha_fin` es nula **si y solo si** `tipo_fin = EN_SERVICIO` (CHECK) |
| `tipo_fin` | FALLA / SUSPENSION_PREVENTIVA / SUSPENSION_OTRA / EN_SERVICIO |
| `id_modo_falla` | Obligatorio si FALLA |
| `edad_horas`, `edad_toneladas` | Calculadas desde los partes y guardadas en caché (se recalculan cada noche) |
| `nivel_hora` | El peor nivel (M < D < E) de los partes que la componen |
| `edad_conocida` | Falso si el componente se instaló antes del sistema |
| `tipo_reparacion` | REEMPLAZO / REPARACION_MINIMA |
| `id_ot_apertura`, `id_ot_cierre`, `id_evento_cierre` | `id_evento_cierre` UNIQUE: **un evento cierra exactamente una vida** |
| `validado` | Verdadero cuando el evento o la OT que la cierra está validado |

**Índice parcial único:** `UNIQUE (id_posicion) WHERE tipo_fin = 'EN_SERVICIO'` garantiza **a lo sumo una vida en servicio por posición**. Se declara con `sqlite_where` y `postgresql_where`.

**Repuestos**

- **`repuesto`:** `codigo` UNIQUE, `descripcion`, `id_tipo_componente` (opcional), [12] `uso` (COMUN/ESPECIFICO), `stock_actual`, `stock_minimo_manual`, `ubicacion`, `codigo_proveedor`, `proveedor`, `lead_time_dias`, `familia_compra` (para el costo K de adquisición), [12] `intervalo_fabricante`.
- **`precio_repuesto`:** historial con `id_repuesto`, `fecha`, `precio`, `moneda` (ARS/USD).
- **`repuesto_activo`:** `id_repuesto`, `id_activo`, `cantidad_instalada`. Es la "plantilla de repuestos por máquina" MANT/RM001.
- **`consumo_repuesto`:** `id_ot`, `id_repuesto`, `cantidad`, `precio_unitario` y `moneda` copiados al consumir, `fecha`.

**`tarjeta_tpm`** [12]: `color` (AZUL/ROJA/VERDE), `id_activo`, `id_posicion` (opcional), `id_anomalia` (lista cerrada) + `observaciones`, `foto`, `estado` (ABIERTA/RESUELTA/DERIVADA/DESCARTADA), `id_evento_generado` (las rojas generan aviso), `id_usuario`, `creada_en`.

**`adjunto`**: `entidad`, `id_entidad`, `ruta`, `tipo`, `creado_en`.

### 5.3 Confiabilidad, análisis y plan

**`resultado_weibull`**

- **Qué se analizó:** `id_tipo_componente`, `id_modo`, `alcance` (MAQUINA/FLOTA), `id_activo` (si es máquina), `ids_activos_flota` (JSON), `conjunto_datos` (NUEVOS / NUEVOS_MAS_HIST_AB), `fecha_calculo`.
- **Cuántos datos:** `n_fallas`, `n_suspensiones`, `n_intervalo`.
- **Método:** `metodo` (WEIBAYES/RRX/MLE/MLE_RBA), `forzado`, `justificacion`.
- **Parámetros:** `beta`, `eta`, `gamma`.
- **IC:** `beta_inf`, `beta_sup`, `eta_inf`, `eta_sup`, `metodo_ic` (LR/BOOTSTRAP/NINGUNO), `nivel_ic` (0,90).
- **Bondad de ajuste:** `r2`, `r2_critico`, `ad`, `comparacion` (JSON: AICc de 2P, 3P, lognormal y exponencial).
- **Lectura:** `confianza` (GRIS/BAJA/MEDIA/ALTA), `interpretacion` (MORTALIDAD_INFANTIL/ALEATORIA/DESGASTE/DESGASTE_RAPIDO).
- **Trazabilidad:** `version_motor`, `hash_datos`, `vigente` (bool).

Se guardan ambos métodos cuando aplican. Uno queda **vigente** según la regla de selección o el forzado.

**`vida_historica`**: mismos campos que `vida_componente`, más `clase_triage` (A/B/C), `fuente` (OT, factura, parte, memoria), `fecha_inf` y `fecha_sup` (límites para la censura por intervalo), `edad_inf` y `edad_sup`, `respaldo` (texto o adjunto). Va separada de las vidas nuevas.

**`estado_componente`** (foto diaria): `id_posicion`, `fecha`, `edad`, `p_falla_delta`, `delta`, `vida_rem_mediana`, `vida_rem_90`, `intervalo_vigente`, `fuente_intervalo` (FABRICANTE/CALCULADO), `semaforo`, `confianza`, `motivos` (JSON con las reglas que dispararon el color). Alimenta las tendencias y hace que el panel cargue rápido.

**`resultado_sistema`**: Crow-AMSAA por máquina (`beta`, `lambda`, IC, estadístico de Laplace U y p-valor, `n`, período).

**`amfe_item`**: `id_tipo_componente`, `id_modo`, `efecto`, `causa`, `G`, `O`, `D`, `O_calculada` (desde F(1 año)), `npr`, `ap` (AIAG-VDA: H/M/L), `acciones`, `responsable`, `fecha`.

**`criticidad_evaluacion`** [12]: `id_activo`, `metodo` (TP_6_CRITERIOS / PONDERACION_U1), `criterios` (JSON con valor y peso de cada criterio), `puntaje`, `clase`, `fecha`, `id_usuario`.

**`analisis_problema`** [12]:

- `tipo` ∈ {CINCO_PORQUES, ISHIKAWA_5M, CINCO_W_1H, HOJA_VERIFICACION}.
- Vínculos: `id_evento`, `id_activo`, `id_tipo_componente`, `id_modo`.
- `contenido` (JSON con la estructura de cada herramienta), `causa_raiz`, `accion_correctiva`, `responsable`, `fecha_compromiso`.
- `estado_pdca` ∈ {PLANIFICAR, HACER, CHEQUEAR, ACTUAR, CERRADO}.
- `id_ot_generada` (puede generar una OT, también de tipo MODIFICATIVO).
- `origen` (MANUAL / SUGERIDO_PARETO / SUGERIDO_BETA / SUGERIDO_REPETICION).

**`plan_preventivo`**: `id_posicion`, `regla` (OPTIMO_COSTO / CONFIABILIDAD_OBJETIVO / PF / FABRICANTE / PRUEBA_FUNCIONAL / NINGUNO), `intervalo`, `unidad`, `t_optimo_calculado`, `vigente_desde`, `id_resultado_weibull`.
**`intervencion_programada`**: `id_plan`, `fecha_prevista`, `ventana`, `id_ot`.

**Predictivo** [12]: `predictivo_parametro` (`id_activo`, `id_posicion`, `especialidad`, `nombre`, `unidad`, `linea_base`, `limite_alerta`, `limite_accion`, `plantilla`, p. ej. ULTRASONIDO_RODAMIENTO) y `predictivo_medicion` (`id_parametro`, `fecha`, `valor`, `equipo_medicion`, `id_usuario_controlo`).

### 5.4 Gestión, configuración y sistema

- **`parametro`:** `clave`, `valor`, `tipo`, `unidad`, `grupo`, `descripcion`, `vigente_desde`. UNIQUE (`clave`, `vigente_desde`). Para leer se toma el último valor con `vigente_desde ≤ fecha`. Ahí viven umbrales, horizontes, tarifas, márgenes, bandas, N y M del 5 Porqués, nivel de servicio, etc. **Ningún número mágico en el código.**
- **`tipo_cambio`:** `fecha` UNIQUE, `ars_por_usd`, `fuente`. Valor inicial: ARS 1.495/USD (agosto 2026, del TP), marcado como referencia editable.
- **`dato_mensual`** [12]: `periodo` (AAAA-MM), `clave` (facturación, costo de producción, valor inmovilizado bruto, HH disponibles, HH de entrenamiento, HH de ausencia, efectivo medio, transferencias, renuncias, MO contratada…), `valor`. Si falta un dato, el indicador muestra **"falta dato"**, nunca un cero.
- **`indicador_objetivo`** [12]: `codigo`, `objetivo`, `limite_inf`, `limite_sup`, `sentido` (mayor es mejor / menor es mejor), `referencia_bibliografia` (texto, mostrado como orientativo).
- **`etapa_implementacion`** [12]: `numero` (1–14), `fase` (1–3), `estado` (PENDIENTE/EN_CURSO/HECHA), `notas`, `fecha_hecha`, `marcada_por`. El criterio automático se calcula y no se guarda.
- **`modulo_habilitado`** [12]: `codigo` (12A…12H), `habilitado`. Pregunta P-06.
- **`alerta`:** `tipo`, `severidad`, `id_activo`, `id_posicion`, `mensaje`, `clave_dedup` (UNIQUE mientras esté abierta), `creada_en`, `enviada_mail_en`, `resuelta_en`, `destinatarios`.
- **`usuario`:** `usuario` UNIQUE, `nombre`, `rol` (OPERARIO/ENCARGADO/JEFE/GERENCIA), `hash_password`, `email`, `activo`. **`usuario_activo`:** las máquinas asignadas a cada operario.
- **`auditoria`:** `fecha`, `id_usuario`, `accion` (ALTA/MODIFICACION/BAJA/VALIDACION/DEVOLUCION/FORZADO_METODO/IMPORTACION/LOGIN_FALLIDO), `tabla`, `id_registro`, `campo`, `valor_anterior`, `valor_nuevo`, `motivo`.
- **`recalculo_pendiente`:** la cola. `id_tipo_componente`, `id_modo`, `alcance`, `motivo`, `creado_en`, `tomado_en`, `terminado_en`, `error`.
- **`importacion`:** `archivo`, `hoja`, `hash`, `fecha`, `filas_ok`, `filas_error`, `reporte` (JSON), `id_usuario`.

### 5.5 Reglas de negocio y dónde se aplican

| Regla | Base | Servicio |
|---|---|---|
| Una vida en servicio por posición | Índice parcial único | `servicios/ot.py` cierra y abre en la misma transacción |
| Un evento cierra exactamente una vida | `id_evento_cierre` UNIQUE + `id_evento` UNIQUE en OT | `cerrar_ot()` |
| Parte duplicado | UNIQUE (activo, fecha, turno) | Mensaje "Ya hay un parte de ese turno" |
| Horas del parte ≤ turno, pasos de 0,5 | CHECK | pydantic |
| Modo y causa coherentes con el tipo | Trigger sobre `catalogo_aplica` | Listas filtradas |
| Fechas coherentes y nada en el futuro | CHECK donde se puede | pydantic |
| Solo lo validado alimenta el cálculo | — | `motor.preparacion` recibe solo vidas `validado = true`, filtradas por el servicio |
| Corregir un validado exige motivo | — | Listener de auditoría (`MotivoRequerido`) |
| Importes con fecha y tipo de cambio | `precio_repuesto`, `tipo_cambio` | `servicios/costos.py` |

### 5.6 Cálculo de la edad de una vida

La edad es la suma de `horas_operadas` (o toneladas) de los partes de esa máquina **entre la instalación y el fin**. Para los turnos de borde (el turno en que se instaló o en que falló), las horas operadas se prorratean según la fracción del turno que cae dentro de la vida. Ejemplo: si falla a la mitad de un turno que operó todo, cuenta la mitad de sus horas. Las horas de un turno sin parte cuentan como **E** (promedio diario del listado) cuando el sistema las completa. El nivel de hora de la vida es el peor de sus partes. Ver D-009.

---

## 6. Módulos y responsabilidades

```
circularis_rel/
  pyproject.toml, requirements.lock, alembic.ini, README.md, LICENSE
  circularis_rel/
    config.py                 rutas, URL de base, zona horaria (lee .env)
    app/
      inicio.py               punto de entrada: login + st.navigation por rol
      componentes/            botones grandes, selector 0,5 h, tarjeta de semáforo, ayuda "?"
      operario_inicio.py      (1)
      reportar_falla.py       (2)
      parte_turno.py          (3)
      tarjeta_tpm.py          [12.F]
      bandeja_encargado.py    (4)
      cerrar_ot.py            (5)
      ficha_maquina.py        (6)
      bandeja_validacion.py   (7)
      panel_planta.py         (8)
      analisis_weibull.py     (9)
      plan_preventivo.py      (10)
      repuestos.py            (11)
      amfe_criticidad.py      (12)
      reportes.py             (13)
      configuracion.py        (14)
      puesta_en_marcha.py     [12.A]
      analisis_problemas.py   [12.D]
      tablero_comando.py      [12.E]
      predictivo.py           [12.G]
      ayuda.py                [12.H]
    servicios/
      auth.py permisos.py registro.py validacion.py ot.py vidas.py
      repuestos.py costos.py recalculo.py semaforo.py alertas.py
      reportes.py exportacion.py importador.py auditoria.py calidad_datos.py
    motor/
      __init__.py             __version__
      tipos.py                dataclasses de entrada/salida (sin dependencias)
      preparacion.py weibull.py bondad.py kpis.py politicas.py
      sistemas.py costos.py interpretacion.py
      tablas/ccc_p10.csv      valor crítico de r², generado por scripts/generar_ccc.py
    asistente/
      etapas.py criticidad.py rca.py tablero.py tpm.py predictivo.py
      sobre_sub_mant.py inventarios.py ayudas.py (textos de la ayuda contextual)
    datos/
      modelos.py db.py auditoria_listener.py
      migraciones/ (alembic)
      importador/ plantillas.py validadores.py
    tareas/
      worker.py recalculo.py nocturno.py mails.py backup.py restaurar.py partes_faltantes.py
  scripts/                    generar_ccc.py, generar_plantillas.py, generar_qr.py, cargar_demo.py
  seeds/                      dataset ficticio (cada registro con nombre "DEMO-…")
  tests/
  docs/
```

### 6.1 Funciones públicas del motor

Tipos y firmas aproximadas, para que se vea el contrato:

```python
# motor/tipos.py
@dataclass(frozen=True)
class Observacion:            # una vida
    edad: float               # horas o toneladas
    estado: Literal["F", "S", "I"]   # falla, suspensión por derecha, intervalo
    edad_inf: float | None = None    # solo si estado == "I"
    nivel_hora: Literal["M", "D", "E"] = "D"
    solo_pronostico: bool = False    # ver D-002

@dataclass(frozen=True)
class AjusteWeibull:
    metodo: str; beta: float; eta: float; gamma: float
    beta_ic: tuple[float, float] | None; eta_ic: tuple[float, float] | None
    metodo_ic: str; nivel_ic: float
    r2: float | None; r2_critico: float | None; ad: float | None
    comparacion: dict[str, float] | None
    n_fallas: int; n_suspensiones: int; n_intervalo: int
    confianza: Literal["GRIS", "BAJA", "MEDIA", "ALTA"]
    interpretacion: str; version_motor: str
    rangos: list[tuple[float, float, float]] | None   # edad, rango ajustado, F mediana

# motor/preparacion.py
def armar_poblacion(vidas, tipo_componente, modo, *, incluir_en_servicio=True,
                    tratar_edad_desconocida="excluir") -> list[Observacion]

# motor/weibull.py
def seleccionar_metodo(obs, beta_ref=None, config=...) -> str
def ajustar(obs, metodo=None, beta_ref=None, config=...) -> AjusteWeibull
def ajustar_weibayes(obs, beta_ref) -> AjusteWeibull
def ajustar_rrx(obs, ic="bootstrap", n_boot=2000, semilla=...) -> AjusteWeibull
def ajustar_mle(obs, rba=None, ic="lr") -> AjusteWeibull
def prueba_flota(grupos: dict[str, list[Observacion]]) -> ResultadoLR

# motor/kpis.py
def mtbf(horas_operadas, n_fallas); def mttr(...); def ai(...); def ao(...); def oee(...)
def confiabilidad(t, beta, eta, gamma=0); def tasa_falla(...); def mttf(...); def b_vida(p, ...)
def prob_condicional(a, delta, ...); def vida_remanente(a, q, ...)
def confiabilidad_serie(lista_r); def confiabilidad_paralelo(...); def mixta(arbol)

# motor/politicas.py
def costo_por_hora(T, cp, cf, beta, eta) ; def curva_costo(...) ; def intervalo_optimo(...)
def intervalo_confiabilidad(r_obj, beta, eta) ; def intervalo_pf(pf)
def recomendar_politica(ajuste, cp, cf, critico, seguridad, pf) -> Recomendacion
def stock_minimo_poisson(demanda_lt, nivel_servicio) ; def lote_economico(K, D, b, p)
def stock_proteccion_catedra(riesgo, c, d)

# motor/sistemas.py
def crow_amsaa(tiempos_falla, T_fin) ; def laplace(tiempos_falla, T_fin)

# motor/costos.py
def cp(p_rep, hh_prev, t_mo) ; def cf(p_rep, hh_corr, t_mo, h_parada, a_pulmon, m_linea, d_sec)
def desglose_ctmc(...) -> {CDMC: {MODM, CR, CM, CH}, CLC: {CO, CI, CDRP}}
def cit(cfj, cv, cfn, cfa)
```

El motor no conoce la base. Los servicios arman las listas, llaman al motor y guardan el resultado.

---

## 7. Motor de confiabilidad: diseño detallado

### 7.1 Preparación (`preparacion.py`)

- **Población:** (tipo de componente, modo). En cada vida, el `tipo_fin` se traduce así:
  - **FALLA** del modo analizado → **F**.
  - **FALLA** de otro modo → **S** (riesgos competitivos).
  - **SUSPENSION_PREVENTIVA** y **SUSPENSION_OTRA** → **S**.
  - **EN_SERVICIO** → **S** con su edad actual (Plan §3, D-002). Una bandera permite marcarla como "solo pronóstico".
- **Edad desconocida:** se excluye por defecto. Opción: censura por intervalo [edad mínima conocida, cota superior por factura], que fuerza MLE.
- **Histórico:** clase A → vida con nivel E; clase B → intervalo (solo MLE); clase C → no entra. El conjunto NUEVOS o NUEVOS + HIST_AB es un parámetro explícito.
- **Variable de edad:** la del tipo de componente (horas o toneladas).
- **Salida:** las observaciones más los metadatos (n por estado, nivel de hora dominante, cuántas son E).

### 7.2 Selección del método

| Situación | Método vigente | También se guarda |
|---|---|---|
| 0–2 fallas, con β de referencia | Weibayes, η = [Σ tᵢ^β / r]^(1/β). Con r = 0 se usa r = 1 (convención de Abernethy, cota conservadora; D-011) | — |
| 0–2 fallas, sin β de referencia | Ninguno: GRIS, solo KPIs empíricos | — |
| 3–19 fallas, suspensiones ≤ 50 %, sin intervalos | RRX (Johnson + Benard) con IC por bootstrap paramétrico | MLE (control) |
| ≥ 20 fallas, o suspensiones > 50 %, o algún intervalo | MLE, con RBA si n < 30 (n = fallas, D-005) y IC por razón de verosimilitud | RRX si no hay intervalos |
| Forzado por el jefe | El elegido, con justificación | Ambos |

Los umbrales (3, 20, 50 %, 30) son parámetros.

**RRX:** regresión de x = ln t sobre y = ln(−ln(1 − F)), con β = 1/pendiente y η = exp(ordenada). Es la convención de Abernethy y reproduce el §15.

**Bootstrap de RRX:**

1. Simula B muestras de la Weibull ajustada con el **mismo patrón de censura**: cada unidad que fue suspendida en cᵢ se observa como min(Tᵢ, cᵢ).
2. Reajusta RRX en cada muestra.
3. Toma los percentiles 5 y 95.

B = 2.000, con semilla fija para que el resultado sea reproducible.

### 7.3 IC por razón de verosimilitud

Perfil de verosimilitud de cada parámetro con χ²(1) al 90 % (umbral ΔlogL = 1,353), por `brentq` sobre el perfil. Para las magnitudes derivadas que se muestran en el panel (B10, P(falla en Δ)), la banda sale del contorno de verosimilitud conjunto con χ²(2): se evalúa la magnitud sobre unos 200 puntos del contorno y se toman el mínimo y el máximo. Eso es lo que dibuja la "banda de incertidumbre".

### 7.4 Bondad de ajuste

- **r² contra r²crit (P10).** La tabla `ccc_p10.csv` se genera por Monte Carlo (sección 2.4): n de fallas de 3 a 100 e interpolación en ln n. Si r² < r²crit, el resultado lleva la advertencia "la recta no ajusta bien: posible mezcla de modos o γ > 0".
- **Anderson-Darling y AICc** desde `reliability` (`Fit_Everything` restringido a 2P, 3P, lognormal y exponencial).
- **Weibull 3P:** solo se habilita si se cumplen las tres condiciones: ≥ 20 fallas, el jefe declaró una justificación física y la curvatura es evidente (r² mejora y AICc baja por lo menos 2). Si no, γ = 0.

### 7.5 Etiqueta de confianza e interpretación de β

- **Confianza por n.º de fallas:** 0–2 GRIS; 3–5 BAJA; 6–19 MEDIA; ≥ 20 ALTA. Ver la contradicción del §15 en la pregunta P-08.
- **Interpretación:** si el IC de β incluye a 1, o β cae en la banda [0,9; 1,1], la lectura es **aleatoria** (D-006). Si no: β < 1 mortalidad infantil; 1 < β ≤ 4 desgaste; β > 4 desgaste rápido. Cada lectura lleva su recomendación de planta.
- **Regla visual:** con confianza BAJA, el color siempre se muestra con borde punteado, la leyenda "confianza baja" y la banda de P(falla). Nunca hay un rojo o un verde "duro".

### 7.6 Flota

Prueba de razón de verosimilitud: LR = 2(Σ logLᵢ − logL_agrupado), que sigue χ² con 2(k − 1) grados de libertad. Se agrupa si p > 0,05 (parámetro). Solo entran posiciones que el jefe marcó como **equivalentes** (tabla `equivalencia_componente`). Nada se agrupa por el nombre. AGR-001/002 y ENF-001/002 no se agrupan salvo que el jefe declare equivalentes esas posiciones.

### 7.7 Sistema reparable (fase 4, el diseño queda listo)

Crow-AMSAA con terminación por tiempo: β̂ = n / Σ ln(T/tᵢ) y λ̂ = n / T^β̂. Prueba de Laplace: U = [Σtᵢ/n − T/2] / [T·√(1/(12n))]. β > 1 con U significativo dispara la alerta semanal de "degradación".

### 7.8 KPIs

Fórmulas exactas del Plan §6 (sección 6.1). Definiciones operativas:

- **MTBF** = horas operadas (de los partes) ÷ n.º de fallas validadas de la máquina en el período.
- **MTTR** = Σ tiempo de reparación activa ÷ n.º de reparaciones.
- **MTTR total** = Σ horas de parada ÷ n.º de fallas.
- **Ai** = MTBF / (MTBF + MTTR).
- **Ao** = (horas requeridas − horas paradas) / horas requeridas. Las horas requeridas son Σ `horas_turno` de los partes, **menos** las horas con motivo `cuenta_como_requerida = falso` (sin demanda, huelga; D-007).
- **OEE** = disponibilidad × rendimiento × calidad. Solo se calcula si hay cantidad procesada y ciclo teórico; si no, "falta dato".
- **Costo de fallas** = Σ Cf histórico de los eventos validados (sección 7.10).

Cada KPI basado en Weibull devuelve `(valor, banda, confianza)`.

### 7.9 Semáforo

| Color | Condición (umbrales en `parametro`, más exigentes para clase A) |
|---|---|
| Rojo | P(Δ) ≥ 30 %, **o** edad > intervalo vigente, **o** OT correctiva abierta en la posición |
| Amarillo | 10 % ≤ P(Δ) < 30 %, **o** edad > 80 % del intervalo |
| Verde | P(Δ) < 10 % **y** edad < intervalo |
| Gris | Sin ajuste (confianza GRIS): solo KPIs empíricos. Con intervalo de fabricante, la regla de edad sigue aplicando y se muestra como "por fabricante" |

- **Δ:** horas de operación hasta la próxima parada programada (parámetro de fecha) convertidas con el ritmo real de la máquina. Si no hay parada cargada, se usan 2 semanas.
- **Máquina:** toma el peor color de sus posiciones `critica = true`. La OT correctiva abierta pinta rojo aunque no haya Weibull.
- **Intervalo vigente:** el T* redondeado según el paso de redondeo (parámetro, p. ej. 25 h; §15: 369 → 375) o alineado con paradas. Si no hay ajuste, el del fabricante (12.G).
- **Faltante:** los umbrales concretos para la clase A no están en el Plan. Propongo 5 % / 20 % como valor inicial a revisar en el piloto (parámetro, D-012).

### 7.10 Costos

`Cp = P_rep + HH_prev · T_MO` y `Cf = P_rep + HH_corr · T_MO + max(0; H_parada − A_pulmón) · M_línea + D_sec`.

Hay **dos usos** distintos (D-008):

1. **Costo histórico** de cada falla: con el precio y la tarifa vigentes a la fecha del evento, en pesos, y convertido a dólares con el tipo de cambio de esa fecha. Se usa en los reportes, el Pareto por costo y el costo de fallas del mes.
2. **Costo de decisión** Cp/Cf de cada tipo y modo: con los precios vigentes hoy y H_parada = MTTR total empírico del modo (o un valor por defecto). Se usa para T*, el ranking y el riesgo. Cuando cambia un precio o la tarifa, se recalcula solo.

**Desglose CTMC = CDMC + CLC** (UNIDAD 3):

- CDMC = MODM (HH × tarifa) + CR (repuestos) + CM (insumos) + CH (herramental).
- CLC = CO (margen × horas de parada no amortiguadas por el pulmón) + CI (incumplimiento) + CDRP (deterioro de la producción).

CM, CH, CI y CDRP son opcionales; si no se cargan valen 0 y se muestra "no cargado".

---

## 8. Pantallas, roles y permisos

### 8.1 Matriz de permisos (Plan §2)

| Acción | Operario | Encargado | Jefe | Gerencia |
|---|---|---|---|---|
| Cargar parte de turno | Sí (sus máquinas) | Sí | Sí | No |
| Crear aviso de falla / tarjeta TPM | Sí (sus máquinas) | Sí | Sí | No |
| Cerrar OT, repuestos | No | Sí | Sí | No |
| Validar, devolver, corregir validado (con motivo) | No | No | Sí | No |
| Configurar umbrales, métodos, costos, usuarios, catálogos | No | No | Sí | No |
| Ver ficha de máquina | Sí (sin costos) | Sí | Sí | Sí |
| Ver costos y panel gerencial | No | No | Sí | Sí |
| Exportar y reportes | No | Sí | Sí | Sí |
| Puesta en marcha, análisis de problemas, tablero, predictivo [12] | No | Ver y cargar análisis | Todo | Ver tablero |

La matriz se implementa como datos en `servicios/permisos.py`, con un test que recorre todos los pares (rol, acción).

### 8.2 Pantallas

| # | Pantalla | Rol | Campos de carga (máx. 6) |
|---|---|---|---|
| 1 | Inicio operario | Operario | Dos botones grandes ("Reportar falla", "Parte de turno"), tarjeta TPM y el estado de sus máquinas |
| 2 | Reportar falla | Operario | Máquina (QR o última usada), síntoma (íconos), ¿paró la máquina? (sí/no), hora (por defecto ahora), foto (opcional), observación (opcional) = **6** |
| 3 | Parte de turno | Operario | Máquina, fecha y turno (automáticos y editables), estado (3 botones), horas no operadas (pasos de 0,5), motivo, cantidad = **6** |
| — | Tarjeta TPM [12.F] | Operario | Color (3 botones), máquina, anomalía (lista), posición (opcional), foto, observación = **6** |
| 4 | Bandeja del encargado | Encargado | Avisos abiertos por prioridad, OT del día, partes faltantes, tarjetas rojas |
| 5 | Cerrar OT | Encargado | **Dos pasos** de ≤ 6 campos. Paso 1: posición (tocando el esquema), modo, causa, acción (reemplazo/reparación), inicio, fin. Paso 2: repuestos, efecto, capacidad, aparición, espera, HH |
| 6 | Ficha de máquina | Todos | Vista de máquina del Plan §7 + catastro (12.B) + historial |
| 7 | Bandeja de validación | Jefe | Aprobar / corregir (con motivo) / devolver, con las advertencias resaltadas |
| 8 | Panel de planta | Jefe, gerencia | Vista de planta del Plan §7 |
| 9 | Análisis Weibull | Jefe | Selector de tipo y modo, método, comparación de distribuciones, histórico sí/no |
| 10 | Plan preventivo y calendario | Jefe | Curva C(T), intervalos, calendario de 52 semanas [12.G], OT a generar |
| 11 | Repuestos | Jefe, encargado | Stock frente a demanda esperada, lote económico, stock de protección |
| 12 | AMFE y criticidad | Jefe | Matriz, O actualizada, NPR y AP, criticidad guiada [12.C] |
| 13 | Reportes | Jefe, gerencia | PDF mensual, ficha PDF (MANT/RHM001), Excel |
| 14 | Configuración | Jefe | Catálogos, usuarios, costos, umbrales, módulos, backup, importador |
| — | Puesta en marcha [12.A] | Jefe | Las 14 etapas en 3 fases, con progreso |
| — | Análisis de problemas [12.D] | Jefe, encargado | Pareto, 5 Porqués, Ishikawa 5M, 5W+1H |
| — | Tablero de comando [12.E] | Jefe, gerencia | Ratios con objetivo y límites |
| — | Predictivo [12.G] | Jefe, encargado | Parámetros, mediciones, tendencia |
| — | Ayuda [12.H] | Todos | Definiciones; también como "?" junto a cada KPI |

**Cierre de OT en dos pasos.** El Plan pide no más de 6 campos por pantalla y el cierre necesita unos 12. Lo parto en dos pasos y el paso 2 se completa con valores por defecto (D-010).

**Usabilidad:**

- CSS propio: botones ≥ 48 px, tipografía base de 18 px, alto contraste.
- Turno por defecto según la hora; última máquina usada recordada en la sesión.
- El parte en estado "Operó todo" se guarda con **un toque más** (Guardar).
- Si hubo un aviso en ese turno, el motivo "falla" y sus horas vienen precargados.

Las metas de 60 s y 30 s se verifican con el guion de la sección 9.13.

### 8.3 Asistente de implementación (módulo 12), por prioridad

| Pieza | Prioridad | Fase | Qué entrega |
|---|---|---|---|
| 12.A Puesta en marcha | P1 | 0 (mínima) → 2 (completa) | Las 14 etapas de la UNIDAD 6 en 3 fases. Cada una con qué es, por qué importa, pantalla, estado, criterio verificable y plantilla Excel. Barra global. Avisos sobre las desventajas de informatizar (UNIDAD 6). Bloqueo de "alertas firmes" por componente hasta alcanzar la confianza |
| 12.B Catastro y repuestos por máquina | P1 | 0 | Campos de MANT/RHM001 y MANT/RM001 sobre `activo` y `repuesto`. Ficha PDF con historial |
| 12.C Criticidad guiada y clasificación de fallas | P1 | 2 (las 3 listas en 1a) | Método TP (por defecto) o ponderación U1, con cortes A/B/C configurables. Diagrama de cuadrantes repentina/progresiva × total/parcial |
| 12.C Fallas ocultas | P2 | 3 | Pruebas funcionales periódicas. Esos componentes quedan fuera de "sin eventos = todo bien" |
| 12.D Pareto y 5 Porqués | P1 | 1c | Sugerencia automática: top del Pareto, β ≈ 1 con confianza ≥ media, o ≥ N repeticiones en M días |
| 12.D Ishikawa 5M, 5W+1H, hoja de verificación | P2 | 3 | Espina de pescado en SVG |
| 12.E Tablero (costo y ratios básicos) | P1 | 1c | CMFT, CPCT, HPHP, TBMP, TBMC, OCPM |
| 12.E Tablero completo, CIT y curva de equilibrio | P2 | 3 | CMOE, CMPP, CMPV, TBML, PETI, CSMP, EFMP |
| 12.F Tarjetas azul/roja/verde | P1 liviano | 1a | |
| 12.F RO, 6 grandes pérdidas, checklist autónomo, PDCA, setup | P2 | 4 | |
| 12.G Calendario de 52 semanas, OT imprimible, predictivo, ultrasonido, fabricante → calculado, sobre/sub-mantenimiento | P2 | 3 | |
| 12.H Ayuda contextual "?" | P1 | 1c | |
| 12.H Tabla de mortalidad y exponencial | P2 | 3 | |
| 12.H Bloques serie/paralelo, revisión en t = η, inventarios | P3/P2 | 3–4 | |

Fórmulas del módulo 12 verificadas contra la bibliografía (detalle y dudas en `DECISIONES.md`):

- **Ratios (UNIDAD 5):** CMFT = CTMN/FETP; CMOE = CMOC/(CMOC + CMOP); CMPP; CMPV; CPCT = Cprev/(Cprev + Ccorr); HPHP; TBMP = HHMP/HHDP; TBMC = HHMC/HHDP; OCPM = (HHDP − HHTM)/HHDP; PETI = HHEI/HHDP; CSMP = EMMM/(EMMM + NOTR + NODV); EFMD = (HHEF − HHAF)/HHEF (B-009). TBML = HHML/HHDP es de la UNIDAD 4.
- **Referencias orientativas de la UNIDAD 5:** CMPP 5–6 %, CMPV 4–5 %, CPCT ~20 %, HPHP 1–3 %; costo de mantenimiento 6–12 % del costo del producto.
- **CIT = CFJ + CV + CFN + CFA** (UNIDAD 5).
- **Inventarios (UNIDAD 5):** Ca = K·D/q; C_alm = ½·q·b·p; q_e = √(2KD/(b·p)); Sp = H·√(c·d), con la tabla de H (ver B-007).
- **TPM (UNIDAD 4):** Dp, Di, Tq, Rv y RO, con las correcciones B-003, B-004 y B-005.
- **Ultrasonido en rodamientos (UNIDAD 3):** +8–10 dB lubricar; +10–12 dB vigilar; +16 dB programar reemplazo; +35–50 dB reemplazar de inmediato. Verificado contra la diapositiva y editable.

---

## 9. Plan de pruebas

Estructura: `tests/motor/`, `tests/servicios/`, `tests/datos/`, `tests/app/` (con `AppTest` de Streamlit) y `tests/asistente/`. Hay dos marcas:

- `@pytest.mark.lento`: Monte Carlo exhaustivo.
- `@pytest.mark.referencia`: casos publicados.

La CI (o `make test` local) corre todo menos `lento` en menos de 2 minutos. Las réplicas de Monte Carlo se configuran con la variable `MC_REPLICAS` (por defecto 300; exhaustivo 5.000).

| # | Prueba | Archivo | Criterio |
|---|---|---|---|
| 1 | §15 cuchillas AGR-001, vida 8 como "solo pronóstico" | `test_referencia_plan15.py` | Todos los valores de la sección 13.1 del pedido con su tolerancia. IC MLE publicado verificado con Fisher (validación cruzada); IC del sistema (LR) = β 2,47–7,89, η 638–924 (±1 %). Semáforo ROJO por las dos reglas; confianza según P-08 |
| 2 | §15 con la vida en servicio como suspensión | `test_vida_en_servicio.py` | η(caso 2) ≥ η(caso 1). Valores obtenidos documentados en D-002 |
| 3 | Weibull de la UNIDAD 2 | `test_referencia_unidad2.py` | Benard 10,9 / 26,4 / 42,1 / 57,9 / 73,6 / 89,1 %; β y η ±10 %; R(15) ±2 puntos |
| 4 | Exponencial de válvulas | idem | λ = 0,04; F(1/3 año) = 1,32 %; R(1/2 año) ≈ 0,98 |
| 5 | Tabla de mortalidad de motores | idem | MTTF 8,84 ± 0,02; F acumulada exacta a 3 decimales |
| 6 | Casos de `reliability` (documentación) | `test_referencia_libreria.py` | ±1 %. Abernethy e IEC 61649 quedan `xfail` con motivo "texto no disponible" hasta conseguirlos (no invento datos) |
| 7 | Validación cruzada | `test_validacion_cruzada.py` | El mismo dataset en el motor, `reliability`, `surpyval` y `lifelines` (KM). Diferencias dentro de lo explicable (documentadas) |
| 8 | Monte Carlo | `test_montecarlo.py` | Combinaciones de β ∈ {0,7; 1; 2; 3,5; 6}, n ∈ {5, 10, 20, 50} y censura ∈ {0, 30, 60 %}. Sesgo de β del MLE + RBA acotado; cobertura del IC al 90 % entre 86 y 94 % (en modo rápido, banda más ancha según el error binomial de las réplicas) |
| 9 | Preparación, casos borde | `test_preparacion.py` | Vida abierta, preventivo, otro modo, parte faltante (E), corrección de un validado, reemplazo tras OT, edad en horas y en toneladas, prorrateo de bordes, edad desconocida, histórico A/B/C |
| 10 | KPIs contra planilla | `test_kpis.py` + `tests/datos/kpis_esperados.xlsx` | Igualdad exacta (con tolerancia de redondeo de punto flotante) |
| 11 | Ratios del módulo 12 | `test_ratios.py` | Un caso numérico por indicador: CMFT, CPCT, HPHP, TBMP, TBMC, OCPM, RO, CIT, EOQ, Sp |
| 12 | Propiedades | `test_propiedades.py` (`hypothesis`) | F monótona; R + F = 1; β invariante y η escalado ×k; P(Δ\|a) ∈ [0, 1]; agregar una suspensión no reduce η del MLE |
| 13 | Usabilidad | `docs/guion_usabilidad.md` (manual) | Aviso < 60 s y parte < 30 s, sin ayuda, con 3 operarios reales |
| + | Reglas de base | `test_restricciones.py` | Índice parcial, UNIQUE, CHECK y triggers: se intenta violar cada regla y debe fallar |
| + | Auditoría | `test_auditoria.py` | Toda modificación deja su fila. Un validado sin motivo da `MotivoRequerido` |
| + | Permisos | `test_permisos.py` | Matriz completa |
| + | Importador | `test_importador.py` | Validación por fila; re-importar no duplica (idempotente) |
| + | Backup y restauración | `test_backup.py` | Backup → restaurar → conteos iguales → `integrity_check` = ok |
| + | Arquitectura | `test_arquitectura.py` | El motor no importa Streamlit ni SQLAlchemy |

---

## 10. Fases, orden de construcción y criterios de aceptación

### 10.1 Fases

| Fase | Entregables | Criterio para pasar |
|---|---|---|
| **0. Preparación** | Repo y entorno (`pyproject`, lock, ruff, pytest); modelos y migración inicial; listener de auditoría; `parametro` con valores iniciales; catálogos semilla (síntomas, motivos con su categoría de pérdida; modos y causas desde el AMFE del TP); **importador** con plantillas Excel y reporte de errores; QR imprimibles; triage del histórico iniciado (plantilla y pantalla de clasificación); **12.A mínima** (lista de etapas con estado manual) y **12.B** (catastro en `activo`, repuestos por máquina); dataset DEMO ficticio | Las 10 máquinas del listado y sus componentes cargados y **revisados por el jefe** (checklist firmado en la pantalla) |
| **1a. Captura** | Login por rol; inicio operario; parte de turno; aviso de falla con QR y foto; **tarjetas azul/roja/verde**; bandeja del encargado; cierre de OT (cierra y abre vidas); bandeja de validación con los controles automáticos del Plan §11; partes faltantes (aviso + completado E); proceso de tareas con backup nocturno y prueba de restauración; exportación total a Excel | Operarios del piloto cargan partes y avisos desde el celular **sin ayuda** |
| **1b. Motor y KPIs** | `preparacion`, `weibull` (Weibayes, RRX + bootstrap, MLE + RBA + LR), `bondad`, `kpis`, `politicas` (C(T)), `costos`; recálculo por evento y nocturno; `resultado_weibull`, `estado_componente`; **pruebas 1–12 en verde** | El motor reproduce los casos de referencia dentro de la tolerancia |
| **1c. Panel (MVP)** | Panel de planta y de máquina; semáforo; ranking de riesgo; gráfico de probabilidad con IC; R(t) y h(t) con la edad marcada; línea de tiempo; horas perdidas por motivo; **Pareto + 5 Porqués con sugerencia (12.D)**; **tablero básico (12.E)**; **ayudas "?" (12.H)**; indicador de calidad de datos por máquina | El jefe interpreta el panel sin asistencia |
| **2. Piloto y extensión** | Uso real en EXT-001, LAV-001, ENF-001 y AGR-001; ajuste de umbrales y catálogos con el jefe; histórico A/B cargado y comparación "nuevos" contra "nuevos + histórico"; extensión al resto; **12.A completo** (criterios automáticos, plantillas, bloqueo de alertas firmes); **criticidad guiada 12.C** | Dos semanas con > 90 % de partes completos |
| **3. Versión 2 y entrega** | Plan preventivo con curva C(T), intervalo redondo, ahorro frente a correr hasta la falla; calendario y OT preventivas; repuestos (Poisson, EOQ, Sp); alertas por mail; PDF mensual; manuales y capacitación; **12.E completo**; **12.G** (52 semanas MANT/1CMP001-2CMP001, MANT/MPV001, predictivo MANT/PMRED001, ultrasonido, fabricante → calculado, sobre/sub-mantenimiento); fallas ocultas; Ishikawa y 5W+1H; tabla de mortalidad | El jefe opera el sistema de forma autónoma |
| **4. Mejoras** | Crow-AMSAA y Laplace en el panel; Weibull bayesiano; OEE/TPM completo (12.F); horómetros (nivel M); AMFE con O automática; 12.H (bloques, revisión en η) | Según la madurez de los datos |

Al cierre de cada fase: tests en verde, `README` actualizado, commit con un mensaje claro y un resumen corto de qué funciona y cómo probarlo.

### 10.2 Orden interno de construcción (fases 0 y 1a)

1. `pyproject`, estructura, ruff, pytest, `test_arquitectura`.
2. Modelos y migración inicial; reglas de base con sus tests.
3. Listener de auditoría y sus tests.
4. Parámetros y catálogos semilla; plantillas Excel; importador idempotente con tests.
5. Dataset DEMO; QR.
6. Autenticación y permisos; esqueleto de navegación por rol.
7. Parte de turno → aviso → tarjetas → bandeja del encargado → cierre de OT (vidas) → bandeja de validación con los controles.
8. Proceso de tareas: backup y restauración, partes faltantes.
9. Exportación a Excel.

### 10.3 Replanificación (hoy 15/10/2026)

| Bloque | Plan original | Propuesta | Condición |
|---|---|---|---|
| Fase 0 | 7–13/10 | 16–19/10 | Tu OK + planillas del TP (listado, componentes, criticidad, AMFE) |
| Fase 1a | 14–20/10 | 17–21/10 (en paralelo con el final de la fase 0) | Mini PC y wifi disponibles para la prueba en planta |
| **Hito: datos reales en planta** | 20/10 | **21–22/10** | Si la mini PC no está, plan B: notebook del jefe como servidor temporal |
| Fase 1b | 21–27/10 | 21–27/10 (sin cambios; el motor ya tiene la verificación previa) | |
| Fase 1c, MVP | 28/10–3/11 | 28/10–3/11 | |
| Fases 2 y 3 | 4/11–1/12 | Sin cambios | |

Si el plazo del TP es anterior al 1/12, el documento académico cierra con el MVP y los primeros resultados del piloto. La fase 3 queda como continuidad documentada.

---

## 11. Riesgos y mitigaciones

Además de los riesgos del Plan §16, que siguen vigentes:

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| El cronograma ya está comprimido: el hito del 20/10 no se llega a cumplir completo | Alta | Alto | Priorizar la 1a; plan B con la notebook del jefe; la planilla impresa del Plan §16 como respaldo |
| Contradicciones del Plan (IC publicado con Fisher; confianza "media" con 5 fallas) | Ya ocurrió | Medio | Documentadas (D-004, P-08, P-09). Los tests verifican ambas cosas, sin ajustar valores publicados |
| Falta la UNIDAD 1 | Ya ocurrió | Medio | Los puntajes de la criticidad guiada quedan editables y marcados "a verificar" hasta recibirla (P-10) |
| `st.camera_input` no funciona por HTTP en el celular | Alta si se usara | Medio | Uso `file_uploader`, que abre la cámara nativa (sección 3.6) |
| WeasyPrint frágil en Windows nativo | Media | Medio | fpdf2 si no hay Docker (P-01) |
| APScheduler dentro de Streamlit (duplicado o muerto) | Alta si se hiciera | Alto | Proceso de tareas separado (sección 3.3) |
| `database is locked` en los picos | Baja | Medio | WAL, `busy_timeout`, `BEGIN IMMEDIATE`, transacciones cortas, reintentos (sección 3.4) |
| `reliability` con un solo mantenedor y API que puede cambiar | Media | Medio | Versión fijada, adaptador, validación cruzada con `surpyval` y con mis fórmulas; lo crítico (RRX, LR, Weibayes, C(T)) es propio |
| Turnos de borde y partes faltantes distorsionan la edad | Media | Medio | Prorrateo documentado (D-009), nivel E visible, comparación con y sin E |
| Operarios con guantes y contraseñas | Alta | Alto | Cookie de 30 días; PIN corto opcional (P-12) |
| Sobre-confianza en resultados con pocos datos | Alta | Alto | Etiqueta obligatoria, banda, borde punteado, bloqueo de alertas firmes hasta MEDIA (12.A) |
| Derechos de autor de la bibliografía | Media | Bajo | Las diapositivas **no** se suben al repo (`docs/bibliografia/` en `.gitignore`); se citan |

---

## 12. Preguntas abiertas

En cada una va **mi recomendación**, para que puedas contestar "OK" o corregir.

**P-00. Repositorio.** Este repo hoy contiene otro proyecto (planos del Redler AGD) y el Plan §14 pide un repositorio propiedad de Circularis. **Recomiendo:** desarrollar en la subcarpeta `circularis_rel/` de esta rama, que es la única a la que puedo empujar, y a la entrega migrarla con su historial a un repo de Circularis (`git subtree split`). ¿O preferís que lo arme en un repo nuevo desde ya?

**P-01. Servidor, SMTP y HTTPS.**
- (a) ¿La mini PC es Windows? **Recomiendo Windows nativo** con dos servicios (NSSM: app y tareas). Es lo más simple para que lo mantenga el jefe. Docker Desktop en Windows suma una capa (WSL2) que puede fallar al arrancar. Si va Docker, uso `docker compose` con dos servicios y WeasyPrint; si va nativo, fpdf2.
- (b) ¿Hay una cuenta SMTP (Gmail de la empresa con contraseña de aplicación, o el servidor de correo propio)? Sin SMTP todo funciona y las alertas quedan solo en el panel.
- (c) ¿Querés HTTPS en la red local? Con certificado autofirmado los celulares muestran una advertencia una vez. Sin HTTPS las contraseñas viajan sin cifrar por el wifi. **Recomiendo:** HTTP en el piloto y evaluar HTTPS en la fase 3.

**P-02. Autenticación y concurrencia.** Propuesta de las secciones 3.4 y 3.5: `streamlit-authenticator` solo para el login y la cookie, con usuarios y roles en la base y el adaptador propio; SQLite en WAL con las reglas de la sección 3.4; proceso de tareas separado. Alternativa descartada: login propio con cookies vía `extra-streamlit-components`. Es más código propio para resolver lo mismo. ¿OK?

**P-03. RBA y valor crítico de correlación.**
- **RBA:** la implemento desde la fórmula de Abernethy, β_RBA = β_MLE · C4^3,5 con C4 = √(2/(N−1)) · Γ(N/2)/Γ((N−1)/2) y N = n.º de fallas, citada en el docstring. Agrego un test de Monte Carlo que muestra que reduce el sesgo de la mediana. Para el §15 daría 4,75 → 3,82.
- **r² crítico (P10):** lo genero por Monte Carlo con semilla fija (sección 2.4) y lo guardo como CSV versionado. No tengo la tabla impresa del libro para compararla: si la conseguís, agrego un test contra 3 o 4 valores.

¿OK?

**P-04. β ≈ 1 y vidas en servicio.**
- **Banda:** "aleatoria" si el IC 90 % de β contiene a 1 **o** si β ∈ [0,9; 1,1] (los dos criterios configurables). Con pocos datos, el criterio del IC es el más honesto.
- **Vidas en servicio:** entran **siempre** como suspensión (Plan §3). El test 1 pasa la vida 8 como "solo pronóstico" para reproducir el §15.

¿OK?

**P-05. Plantillas Excel.** Propongo un libro `carga_inicial.xlsx` con las hojas `lineas`, `maquinas`, `tipos_componente`, `posiciones`, `catalogo_sintomas`, `catalogo_modos`, `catalogo_causas`, `modo_aplica_tipo`, `repuestos`, `repuestos_por_maquina`, `criticidad`, `amfe` y `parametros_costos`, más un libro aparte `historico.xlsx` (vida, fecha o rango, horas o rango, tipo de fin, modo, clase A/B/C, fuente, respaldo). Cada hoja lleva encabezados fijos, una fila de ayuda y listas desplegables (validación de datos de Excel). La clave natural es el código, por eso re-importar actualiza y no duplica. Hay modo "simular" que muestra qué cambiaría antes de grabar. **Necesito las planillas reales del TP** (listado de máquinas, detalle de componentes, criticidad, AMFE y TRI-001 WEIBULL) para ajustar las columnas. ¿Me las pasás?

**P-06. Módulo 12 por defecto.** Propuesta: **12.A, 12.B, 12.C, 12.D y 12.H (ayudas) activos**; **12.E, 12.F (salvo las tarjetas, que van activas), 12.G y el resto de 12.H** habilitables en Configuración. ¿OK?

**P-07. Usabilidad y datos de demo.**
- **Demo:** un dataset ficticio con prefijo `DEMO-` en cada código, banner rojo "DATOS FICTICIOS" en todas las pantallas mientras haya datos DEMO, y botón para borrarlos. Incluye el caso §15 tal cual.
- **Usabilidad:** guion con 3 operarios reales y 2 tareas cronometradas (aviso y parte), sin ayuda, con su propio celular, en la máquina. Antes, una prueba de pasillo con 2 personas de oficina. Registro en la planilla del guion; se itera hasta cumplir 60 s y 30 s.

¿OK?

**P-08. Confianza del §15: "baja" o "media".** La tabla del Plan dice que 3–5 fallas = **baja**. El §15 tiene 5 fallas y dice "baja-media" en un lugar y "confianza media" en otro, y tu caso de prueba 1 pide "media". **Recomiendo** seguir la tabla (5 fallas → BAJA), con el umbral configurable. El test 1 verifica BAJA y documenta la discrepancia. Si preferís "media", la regla tendría que contar algo distinto de las fallas (por ejemplo, fallas + suspensiones = 7 → media), y eso cambia todas las etiquetas. ¿Cuál?

**P-09. IC del MLE del §15.** Ver la sección 2.1: lo publicado es Fisher, no razón de verosimilitud. **Recomiendo:** el sistema usa LR (regla del Plan); el test verifica lo publicado con Fisher como validación cruzada; lo dejo documentado en D-004. ¿OK?

**P-10. UNIDAD 1.** El pedido cita la UNIDAD 1 para la criticidad por ponderaciones y la definición D = (TO − ΣTA)/TO. No me llegó. ¿Me la pasás? Sin ella, los puntajes de 12.C quedan como los escribiste, editables y con la marca "a verificar". Tampoco encontré en las unidades 2–6 el diagrama de Ishikawa/5M ni el diagrama de cuatro cuadrantes; si están en la UNIDAD 1, los tomo de ahí.

**P-11. Turnos y calendario.** ¿Cuántos turnos hay, con qué horarios, y qué máquinas trabajan en cada uno? El listado dice 8 h/día en agrumadoras, mezcladora y extrusora; 6 h en cuba y secadora; 4 h en moledora, trituradora y enfardadoras. ¿Son un turno de 8 h con la máquina parada parte del turno, o turnos más cortos? ¿Qué días se trabaja? Esto define cuándo falta un parte.

**P-12. Login de operarios.** **Recomiendo:** usuario + PIN de 4–6 dígitos para el rol operario (teclado numérico grande) y contraseña completa para encargado, jefe y gerencia, con la cookie de 30 días. ¿OK?

**P-13. Licencia.** **Recomiendo Apache-2.0**: es permisiva como MIT y además trae una concesión explícita de patentes y una cláusula de marcas. Es compatible con `reliability` (LGPL-3.0) usada como librería sin modificar. ¿O preferís MIT?

**P-14. Idioma del código.** Identificadores, tablas y commits en **español sin tildes** (el dominio y las tablas del Plan ya están en español). ¿OK?

---

## 13. Convenciones del repositorio

- Python 3.12; `ruff` para lint y formato; tipado en el motor y los servicios.
- Commits en español, en imperativo, con el prefijo de la fase (p. ej. `Fase 1a: parte de turno con estado y motivo`).
- `docs/DECISIONES.md` se actualiza en el mismo commit que la decisión.
- Configuración por `.env` (`CIRCULARIS_DB_URL`, `CIRCULARIS_DATA_DIR`, `SMTP_*`). Nunca hay credenciales en el repo.
- `docs/bibliografia/` queda en `.gitignore`: las diapositivas son del Mgter. Torres y se citan, no se redistribuyen.
- Referencias bibliográficas del Plan §17: se mantienen **tal cual**, con la advertencia del Plan: "citadas de memoria técnica, sin consulta en línea en esta versión; conviene verificar ediciones al incluirlas en el TP". No agrego valores de β de referencia ni referencias nuevas.
