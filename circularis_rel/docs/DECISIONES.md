# Registro de decisiones

Cada entrada tiene: **qué** se decide, **por qué** y **alternativa descartada**. Las entradas **D-xxx** son decisiones de diseño y las **B-xxx** son dudas o correcciones sobre la bibliografía de la cátedra (Mgter. Leandro D. Torres, UTN-FRC).

**Estado:** el 15/10/2026 se aprobaron todas las recomendaciones de las preguntas P-00 a P-14 (ver D-025), y se pidió avanzar por todas las fases resolviendo cada duda con la opción más recomendada. Cada decisión nueva se agrega acá.

Verificación numérica previa: hecha el 15/10/2026 con Python 3.13, NumPy 2.5.4, SciPy 1.18.1, `reliability` 0.9.0, `surpyval` 0.24 y `lifelines` 0.30.3, en un entorno descartable fuera del repo.

---

## Decisiones de diseño

### D-001: El sistema vive en `circularis_rel/` dentro de este repo (depende de P-00)

- **Qué:** todo el sistema va en la subcarpeta `circularis_rel/`, con su propio `pyproject.toml`, `docs/` y `tests/`.
- **Por qué:** el repo ya contiene otro proyecto (planos del Redler AGD) y la rama de trabajo es la única a la que se puede empujar. Una subcarpeta aísla los dos proyectos y permite separarla después con `git subtree split`, conservando el historial, hacia un repo propiedad de Circularis (Plan §14).
- **Descartado:** mezclar el sistema con la raíz del repo, porque chocaría con `docs/` del otro proyecto.

### D-002: Las vidas en servicio entran al ajuste como suspensión

- **Qué:** `preparacion.armar_poblacion` incluye por defecto cada vida EN_SERVICIO como suspensión por derecha con su edad actual (Plan §3, punto 5). Existe la bandera `solo_pronostico` para excluir una vida del ajuste y usarla solo para el pronóstico. Así reproduce el test 1 el ejemplo §15, que ajusta con 7 vidas y usa la vida 8 solo para pronosticar.
- **Por qué:** ignorar las unidades sobrevivientes subestima η (Plan §3, citando a Abernethy y Meeker). El §15 es inconsistente con el §3 del propio Plan.
- **Diferencia numérica obtenida** (§15 con y sin la suspensión de 520 h):

| Ajuste | Sin la vida 8 (como §15) | Con la vida 8 como suspensión |
|---|---|---|
| RRX β | 3,422 | 3,582 |
| RRX η | 774,3 h | 781,3 h |
| RRX r² | 0,9962 | 0,9981 |
| MLE β | 4,749 | 4,928 |
| MLE η | 760,5 h | 766,6 h |

  η sube, como debe pasar al agregar una suspensión. La propiedad se prueba también con `hypothesis` para el MLE.
- **Descartado:** excluir siempre las vidas en servicio, porque contradice el §3 y sesga η hacia abajo.

### D-003: RRX es una regresión de X sobre Y, con rangos de Johnson y Benard

- **Qué:** x = ln t sobre y = ln(−ln(1−F)), con β = 1/pendiente y η = e^ordenada. Las suspensiones entran por rangos ajustados de Johnson y la F mediana sale de Benard, (i − 0,3)/(n + 0,4), con n = total de vidas.
- **Por qué:** es el método por defecto de Abernethy para muestras chicas (Plan §5) y reproduce el §15 al tercer decimal (β 3,422; η 774,3; r² 0,9962). `reliability` con `method='RRX'` da lo mismo.
- **Descartado:** RRY (Y sobre X), que da β 3,409 y η 774,8. Queda disponible solo para validación cruzada.

### D-004: El IC del MLE usa razón de verosimilitud; el IC publicado en §15 es de Fisher (depende de P-09)

- **Qué:** el sistema calcula el IC del MLE por razón de verosimilitud (perfil, χ²(1), 90 % bilateral), como manda el Plan §5. La matriz de Fisher existe en el motor **solo** como función de validación cruzada.
- **Hallazgo:** el IC que publica el §15 (β 2,7–8,4; η 650–890) coincide exactamente con Fisher en escala logarítmica al 90 % bilateral (β 2,69–8,39; η 650–890), que es lo que devuelve `reliability` por defecto. Con razón de verosimilitud sale β 2,47–7,89 y η 638–924. El Plan pide evitar Fisher con pocos datos, así que el número publicado contradice su propia regla.
- **Test:** el test 1 verifica (a) el IC publicado con la función de Fisher y (b) el IC del sistema por LR contra los valores obtenidos. El valor publicado no se ajusta.
- **Descartado:** usar Fisher para "dar igual" que el Plan, porque contradice la regla y da intervalos demasiado estrechos con pocos datos.

### D-005: Corrección de sesgo RBA según Abernethy (depende de P-03)

- **Qué:** β_RBA = β_MLE · C4^3,5, con C4 = √(2/(N−1)) · Γ(N/2) / Γ((N−1)/2) y N = número de **fallas**. Se aplica cuando el método vigente es MLE y N < 30 (parámetro). η se re-estima con β fijo.
- **Por qué:** es la corrección que propone Abernethy (Plan §5, ref. [1]). Se implementa desde la fórmula porque ninguna librería la trae. Un test de Monte Carlo verifica que reduce el sesgo de la mediana de β.
- **Ejemplo:** §15 (5 fallas), C4 = 0,9400 → β_RBA = 3,82.
- **Descartado:** el factor (n−2)/(n−0,68) de otras fuentes, porque no es el del Plan.

### D-006: Banda para "β ≈ 1" (depende de P-04)

- **Qué:** la lectura es "aleatoria" si el IC 90 % de β contiene a 1 **o** si β ∈ [0,9; 1,1]. Los dos criterios se configuran en `parametro`. Si no: β < 1 mortalidad infantil; 1 < β ≤ 4 desgaste; β > 4 desgaste rápido.
- **Por qué:** el Plan solapa "≈ 1" con "1 a 4". Con pocos datos, el IC es el criterio honesto: no hay evidencia para distinguir β de 1.
- **Descartado:** solo la banda fija, porque con 3 fallas un β de 1,3 no se distingue de 1.

### D-007: Las horas sin demanda y de huelga no cuentan como horas requeridas para Ao

- **Qué:** cada `motivo_parada` tiene `cuenta_como_requerida`. Va **falso** para "sin demanda" y "huelga", y es editable. Ao = (requeridas − paradas)/requeridas sobre las horas requeridas así filtradas.
- **Por qué:** la definición de disponibilidad de la bibliografía, D = (TO − ΣTA)/TO, excluye huelgas y caídas de demanda. **Pendiente de verificar contra la UNIDAD 1, que no recibí (P-10).**
- **Descartado:** contar todas las horas del turno, porque castigaría a mantenimiento por la falta de pedidos.

### D-008: Costo histórico y costo de decisión se calculan por separado

- **Qué:**
  - **Costo histórico** de cada falla: con el precio, la tarifa y el tipo de cambio vigentes **a la fecha del evento**. Se usa en reportes, Pareto por costo y costo del mes.
  - **Costo de decisión** Cp/Cf: con los precios vigentes **hoy** y H_parada = MTTR total empírico del modo. Se usa para T*, el ranking y el riesgo. Ninguno de los dos se carga a mano: se derivan de los parámetros.
- **Por qué:** el Plan pide a la vez "todo importe en pesos con su fecha" (historia fiel) y "al cambiar un precio se recalculan solos el costo de fallas, el intervalo óptimo y el ranking" (decisión actual). La relación Cf/Cp es estable ante la inflación (Plan §12).
- **Descartado:** un único costo con el precio actual, porque reescribiría la historia en cada aumento.

### D-009: Edad de una vida y turnos de borde

- **Qué:** la edad es la suma de las horas operadas (o toneladas) de los partes entre la instalación y el fin. En el turno de instalación y en el de falla se prorratea según la fracción de tiempo del turno que cae dentro de la vida. El nivel de hora de la vida es el peor de sus partes (M < D < E).
- **Por qué:** sin el prorrateo, una falla a las 2 h de un turno de 8 h sumaría 8 h.
- **Descartado:** contar el turno completo, o ignorarlo.

### D-010: El cierre de OT tiene dos pasos de hasta 6 campos

- **Qué:**
  - Paso 1: posición, modo, causa, acción (reemplazo/reparación), inicio y fin.
  - Paso 2: repuestos, efecto, capacidad, aparición, espera y HH, con valores por defecto.
- **Por qué:** el cierre necesita unos 12 datos y la regla es "ninguna pantalla de carga con más de 6 campos".
- **Descartado:** una pantalla larga con desplazamiento, porque viola la regla y es incómoda en la tablet.

### D-011: Weibayes con cero fallas

- **Qué:** con r = 0 se usa r = 1. Es la convención conservadora de Weibayes: supone que la primera falla es inminente, y el resultado es una cota inferior de η. La pantalla lo aclara.
- **Por qué:** la fórmula del Plan divide por r.
- **A verificar:** la convención está tomada de memoria técnica de Abernethy, sin la página a la vista. Queda señalada para confirmar con el libro.
- **Descartado:** no mostrar nada con 0 fallas. Mientras haya β de referencia declarado, la cota sirve.

### D-012: Umbrales del semáforo para la clase A

- **Qué:** valor inicial verde < 5 %, amarillo de 5 % a 20 % y rojo ≥ 20 %, contra 10 % y 30 % para las clases B y C. Son parámetros y se revisan al cierre del piloto.
- **Por qué:** el Plan dice "más exigentes para criticidad A" sin dar números.
- **Descartado:** dejar los mismos umbrales para todas las clases.

### D-013: Los partes de turno no pasan por la validación individual del jefe

- **Qué:** los partes entran al cálculo de la edad después de pasar los controles automáticos (Plan §11). El jefe los ve en el indicador de calidad de datos y puede corregirlos, con auditoría. Lo que exige validación es el **evento de falla** (y la OT): una vida solo entra al ajuste cuando el evento que la cierra está validado.
- **Por qué:** con decenas de partes por día, validarlos uno a uno no es sostenible. El Plan define la validación sobre los "eventos".
- **Descartado:** validar cada parte.

### D-014: Un solo motivo por parte

- **Qué:** el parte parcial lleva un motivo principal. Si hubo un aviso de falla en el turno, el motivo "falla" y sus horas vienen precargados.
- **Por qué:** más motivos superarían los 6 campos y el objetivo de 30 s.
- **Descartado:** el desglose de horas por motivo dentro del parte.

### D-015: La foto del aviso se carga con `file_uploader`, no con `camera_input`

- **Qué:** `st.file_uploader` con `accept=image/*`, que en el celular abre la cámara nativa.
- **Por qué:** `camera_input` usa `getUserMedia` y los navegadores móviles solo lo permiten en HTTPS. En la red local por HTTP no funcionaría.
- **Descartado:** `camera_input`, salvo que se habilite HTTPS (P-01c).

### D-016: Las diapositivas de la cátedra no se suben al repo

- **Qué:** `docs/bibliografia/` queda en `.gitignore`. Se cita la fuente (unidad y número de diapositiva).
- **Por qué:** el material es del Mgter. Torres y el repo tendrá licencia abierta (P-13).

### D-017: Uso del TP N.º 1 como borrador de carga

- **Qué:** el TP N.º 1 aporta la **estructura**: máquinas, función, componentes, modos de falla, criterios de criticidad y escala del AMFE. Con eso se arma `docs/plantillas/carga_inicial_borrador_TP1.xlsx`, que el jefe revisa antes de importar.
  - Los **datos de mantenimiento** del TP (TBF en días y valores G/O/D) son **ilustrativos**: fueron inventados para el TP, como aclaró el usuario. El AMFE entra con origen `TP1_ILUSTRATIVO` y la ocurrencia O se recalcula con datos reales en la fase 4.
  - Los TBF **no** se importan como histórico.
  - Los códigos MOL-001, SEC-001 y MEZ-001 se proponen siguiendo el patrón del Plan; los demás códigos y las horas por día salen del Plan.
  - La transcripción de los 7 AMFE (94 filas) está en `seeds/tp1/amfe_tp1.psv`. Se verificó que NPR = G×O×D en todas las filas.
  - Se agregó `activo.revisado_en` / `id_usuario_revision` para el criterio de salida de la fase 0 ("cargados y revisados por el jefe").
- **Descartado:** cargar los TBF del TP como histórico, porque son inventados.

### D-018: Los triggers de reglas son solo de SQLite

- **Qué:** las reglas "modo coherente con el tipo de componente", "referencia de catálogo del tipo correcto", "posición de la misma máquina" y "no borrar un validado" son triggers de SQLite. Los servicios aplican las mismas reglas.
- **Por qué:** SQLite es la base del proyecto. Migrar a PostgreSQL exige portar esos 13 triggers a PL/pgSQL (`ddl_extra.py` los concentra en un solo lugar).
- **Descartado:** escribir ya la versión PostgreSQL sin poder probarla.

### D-019: A qué tipos de componente aplica cada entrada del catálogo

- **Qué:** un MODO debe estar asignado a uno o más tipos de componente; es una lista cerrada por tipo. Una CAUSA o un SÍNTOMA sin tipos asignados aplica a todos.
- **Por qué:** los modos dependen del componente (pérdida de filo solo en cuchillas). Las causas genéricas (desgaste, lubricación, sobrecarga) valen para todos.

### D-020: Criticidad: método del TP N.º 1

- **Qué:** se usan las escalas del TP N.º 1:
  - uso 5/3/1; alternativa 5/4/2/1; influencia 5/4/2/1; calidad 5/4/2/1; ambiente 5/3/1; seguridad 5/3/1.
  - El puntaje es la **suma**, con los cortes del TP: ≥25 Alta, 20–24 Media, 15–19 Baja, <15 Muy baja.
  - La clase del sistema sale de una equivalencia configurable: Alta → A, Media → B, Baja y Muy baja → C.
  - También se calcula el puntaje ponderado del Plan §8 (0,30; 0,20; 0,15; 0,15; 0,10; 0,10), que se guarda en el detalle.
  - Se reproduce la tabla del TP (test `test_reproduce_tabla_del_tp1`).
- **Duda:** el pedido cita para la "ponderación U1" otros puntajes (uso 4/2/1; ambiente y seguridad 5/2/1). El TP los adaptó. Sin la UNIDAD 1 no se puede verificar cuál es el original, así que el método U1 queda disponible pero exige indicar la clase a mano.
- **Descartado:** usar los pesos del Plan como método principal, porque el TP, que es la fuente real de la criticidad, suma sin pesos.

### D-021: El importador aplica todo o nada, y una celda vacía no borra

- **Qué:** si hay un error en cualquier fila, no se graba nada. Simular corre exactamente lo mismo y siempre revierte. Una celda vacía no borra un dato existente. Re-importar sin cambios da "sin cambios" y no deja auditoría.
- **Por qué:** una importación a medias deja referencias rotas y es difícil de corregir. Borrar con celdas vacías es peligroso.
- **Descartado:** grabar las filas buenas y saltear las malas.

### D-022: PDF con fpdf2 y la tipografía DejaVu de matplotlib

- **Qué:** los PDF (ficha, QR, reportes) se generan con fpdf2, en Python puro, con la tipografía DejaVu que trae matplotlib.
- **Por qué:** P-01 resolvió Windows nativo, donde WeasyPrint necesita GTK/Pango instalado aparte. Así funciona sin internet y escribe todos los caracteres.
- **Descartado:** WeasyPrint.

### D-023: El importador está en `servicios/`

- **Qué:** el importador vive en `servicios/importador/`, no en `datos/`.
- **Por qué:** usa reglas de negocio (criticidad, triage, parámetros), y la capa de datos no debe depender de servicios (test de arquitectura).

### D-024: Usuarios DEMO con claves públicas

- **Qué:** la demo crea `demo.jefe`, `demo.encargado`, `demo.gerencia` y `demo.operario`, con claves conocidas. Mientras haya datos DEMO, todas las pantallas muestran un cartel rojo. "Borrar datos DEMO" los elimina fila por fila, y cada baja queda auditada.
- **Por qué:** sirven para capacitar y probar sin tocar datos reales. El cartel evita olvidarlos.

### D-025: Respuestas a las preguntas abiertas (aprobadas el 15/10/2026)

| Pregunta | Resolución |
|---|---|
| P-00 | Subcarpeta `circularis_rel/` en esta rama; se migra a un repo de Circularis a la entrega con `git subtree split` |
| P-01 | Windows nativo con dos servicios (NSSM): app y tareas. Sin SMTP confirmado: las alertas funcionan en el panel y por mail solo si se carga SMTP en `.env`. HTTP en el piloto |
| P-02 | `streamlit-authenticator` para el formulario y la cookie; usuarios en la base; WAL + BEGIN IMMEDIATE; proceso de tareas separado |
| P-03 | RBA desde la fórmula de Abernethy (C4^3,5); r² crítico por Monte Carlo con semilla fija |
| P-04 | "Aleatoria" si el IC de β contiene a 1 o β ∈ [0,9; 1,1]; las vidas en servicio entran como suspensión |
| P-05 | Formato de `docs/plantillas/FORMATO.md` |
| P-06 | Activos por defecto: 12.A, 12.B, 12.C, 12.D, tarjetas y ayudas; el resto se habilita en Configuración |
| P-07 | Demo ficticia con prefijo DEMO- y cartel rojo; guion de usabilidad con 3 operarios |
| P-08 | Confianza por la tabla del Plan: 5 fallas → BAJA |
| P-09 | IC del MLE por razón de verosimilitud; Fisher solo para validación cruzada |
| P-10 | Sin UNIDAD 1: los puntajes U1 quedan "a verificar" |
| P-11 | Turnos sin definir: se cargan en la hoja `turnos`. La demo usa mañana 6–14 y tarde 14–22 (ficticios) |
| P-12 | PIN de 4 a 6 dígitos para operarios; contraseña de 8 o más caracteres para el resto; cookie de 30 días |
| P-13 | Licencia Apache-2.0 |
| P-14 | Código, tablas y commits en español, sin tildes en los identificadores |

### D-026: Las vidas se cierran al cerrar la OT, no al validar

- **Qué:** cuando el encargado cierra la OT, el sistema cierra la vida (FALLA o suspensión) y abre la siguiente desde el fin de la reparación. La vida cerrada queda con `validado = False`. El jefe valida → `validado = True`, y recién ahí entra al ajuste y se encola el recálculo.
  - Devolver y volver a cerrar rehace la vida, sin duplicar.
  - Anular reabre la vida anterior, salvo que ya haya otro cambio posterior del mismo componente.
- **Por qué:** físicamente el componente nuevo ya está instalado. Si se esperara la validación, mientras tanto no habría "una vida en servicio" coherente. El filtro de calidad del Plan se respeta igual: solo lo validado entra al cálculo.
- **Descartado:** abrir y cerrar vidas recién al validar.

### D-027: Reparación mínima

- **Qué:** si la acción es "Reparación" (no reemplazo), la falla igual cierra la vida con la edad a la falla, y la vida siguiente queda marcada `tipo_reparacion = REPARACION_MINIMA`.
- **Por qué:** Weibull supone "como nuevo" (renovación). Con la marca, el motor puede excluir o separar esas vidas, y a nivel máquina se usa Crow-AMSAA (sistema reparable, Plan §5).

### D-028: Componentes instalados antes del sistema

- **Qué:** al "Iniciar captura", o en la primera falla, cada posición sin vida recibe una vida en servicio con `edad_conocida = False`. Su primera falla no entra al ajuste por defecto (Plan §5: edad desconocida → excluida, o por intervalo). Desde la segunda vida, la edad es real.

### D-029: Partes estimados y el motivo "Sin dato"

- **Qué:** un parte que sigue faltando pasados `partes.dias_para_estimar` días (2 por defecto) se completa con horas promedio por día ÷ turnos de ese día, con nivel E y origen ESTIMADO_SISTEMA.
  - Las horas no operadas de ese parte llevan el motivo SIN_DATO, que **no cuenta como tiempo requerido**: la falta de información no castiga la disponibilidad.
  - Si después el operario carga el parte, reemplaza al estimado.
  - Sin horas promedio cargadas, no se inventa nada: el parte queda faltante.
- **Descartado:** contar las horas estimadas no operadas como parada.

### D-030: Edad: campos derivados fuera de la auditoría

- **Qué:** `edad_horas`, `edad_toneladas` y `nivel_hora` de la vida se recalculan solos desde los partes y no se auditan, así que recalcularlos no exige motivo.
- **Por qué:** lo que se audita es su fuente: los partes y los eventos.

### D-031: Login y recarga de la página

- **Qué:** con la cookie, recargar la página mantiene la sesión. Se entra al Inicio del rol y no a la subpágina que estaba abierta. Esto no afecta el flujo del QR, que abre la raíz con `?maq=`.
- **Por qué:** el componente que escribe la cookie tiene que dibujarse en la corrida del login. Vaciarlo o forzar otra corrida (`st.rerun`) impide guardar la cookie.

### D-032: Fotos

- **Qué:** las fotos se reducen a 1.280 px (JPEG) y se guardan en `datos/fotos/AAAA/MM/`; la base guarda la ruta relativa. Entran en el backup como zip.

### D-033: Banda de incertidumbre de P(falla en Δ)

- **Qué:** la banda que se muestra junto a P(Δ) es el mínimo y el máximo de P(Δ) evaluada en las cuatro esquinas (β_inf/β_sup × η_inf/η_sup) del IC del modo dominante, combinada con los demás modos.
- **Por qué:** es simple, rápido y conservador.
- **Descartado:** el contorno de verosimilitud conjunto (χ²₂) propuesto en el PLAN_TECNICO §7.3. Es más exacto pero más lento; queda como mejora.

### D-034: Cobertura del IC por razón de verosimilitud con muy pocas fallas

- **Hallazgo (Monte Carlo, `pytest -m lento`):** con 10 o más fallas, el IC 90 % por razón de verosimilitud cubre el valor real en 86–94 % de los casos, como pide el §13.8. Con **5 fallas cubre ~83–86 %**: el método es asintótico.
- **Decisión:** se mantiene la razón de verosimilitud, que es lo que pide el Plan. En ese rango de fallas el método vigente es RRX con bootstrap y la etiqueta ya es "confianza baja", sin colores "duros". El test exhaustivo exige 86–94 % desde 10 fallas y al menos 80 % por debajo.
- **No se inventa una corrección:** el factor de corrección para muestras chicas de los límites LR de Abernethy no se pudo verificar sin el libro.

### D-035: RBA también en la alternativa MLE

- **Qué:** cuando el MLE es la alternativa de control (con RRX vigente), igual se le aplica la RBA si hay menos de 30 fallas, y se guarda el β del MLE sin corregir.
- **Ejemplo §15:** el "MLE de control β ≈ 4,75" del Plan es ese valor sin corregir; con RBA da 3,82.

### D-036: Weibull 3P solo en la tabla de comparación

- **Qué:** Weibull 3P se ajusta y se muestra en la comparación de distribuciones (AICc, AD), pero nunca es el método vigente automático. Para que lo sea, el jefe tiene que forzarlo con una justificación física y tener al menos 20 fallas (Plan §5).

### D-037: Intervalo para el semáforo

- **Qué:** el intervalo se toma en este orden:
  1. el **plan preventivo aprobado** (fase 3);
  2. si no hay, el **calculado**: T* redondeado, o R* para clase A o seguridad, o P-F/2, siempre que haya Weibull de desgaste y costos completos;
  3. si no, la **recomendación del fabricante**.

  La pantalla indica de dónde sale. Así reproduce el §15: semáforo rojo con edad 520 h > 375 h recomendado.

### D-038: La fecha base de los parámetros es 01/01/2000

- **Qué:** los valores iniciales de `parametro` valen desde 01/01/2000.
- **Por qué:** antes se sembraban "desde el 01/10/2026", y un valor cargado por el jefe con fecha anterior (por ejemplo, la tarifa de enero) quedaba tapado por el valor base vacío. Lo detectó un test de costos.

### D-039: Edad desconocida en el semáforo

- **Qué:** si la vida en servicio empezó antes del sistema (edad desconocida), el semáforo no calcula P(Δ) con una edad falsa. Queda gris, salvo que haya una OT abierta, y lo explica en los motivos.

---

## Dudas y correcciones sobre la bibliografía

### B-001: UNIDAD 2, diapositiva 13 (MTTF de motores)

- **Duda:** la diapositiva dice MTTF = 8,83, pero el cálculo exacto da 1.591/180 = 8,8389.
- **Decisión:** es un truncamiento. El test acepta 8,84 ± 0,02. En esa tabla, la columna λ(t) = n(t)/N(t−1) (p. ej. 63/162 = 0,389) se implementa así.

### B-002: UNIDAD 2, diapositivas 31–32 (posición de rangos)

- **Duda:** la diapositiva propone tres fórmulas según N:
  - N > 50: F = nᵢ/N por clases (falta aclarar que es acumulada);
  - 20 < N < 50: rango medio i/(N+1);
  - N < 20: Benard.
- **Decisión:** el sistema usa siempre Benard con rangos ajustados de Johnson, como manda el Plan. Para N grande el método vigente pasa a ser MLE, que no usa rangos. La fórmula de rango medio no se usa.

### B-003: UNIDAD 4, diapositivas 31–32 (Dp y Di)

- **Duda:** la diapositiva 31 define Dp = TF/(TF + TAP) y la 32 escribe TR = TF − TAP y Di = (TR − TAI)/TR. Si TR = TF − TAP, las dos definiciones no encajan: en Dp, TF + TAP sería el tiempo total, y en Di el tiempo requerido quedaría descontado dos veces del setup.
- **Decisión:** lectura coherente con RO = Dp·Di·Rv·Tq:
  - TT = tiempo total requerido según el parte (excluidas las horas que no cuentan, D-007);
  - TAP = setup;
  - TR = TT − TAP;
  - Dp = TR/TT = TR/(TR + TAP);
  - Di = (TR − TAI)/TR.

  Así, Dp·Di = (TT − TAP − TAI)/TT, que es la fracción de tiempo realmente disponible. La definición se muestra en pantalla.
- **Descartado:** copiar la diapositiva literal, porque da un RO incoherente.

### B-004: UNIDAD 4, diapositiva 33 (relación de velocidad)

- **Duda:** la diapositiva define Rv = TCR/TCT (ciclo real sobre teórico). Como el ciclo real suele ser mayor que el teórico, Rv > 1 y RO podría superar el 100 %.
- **Decisión:** se usa la forma estándar Rv = TCT/TCR ≤ 1 y se muestra la definición en pantalla.

### B-005: UNIDAD 4, diapositivas 33 y 34 (tasa de calidad)

- **Duda:** la diapositiva 33 define Tq = NPB/NPTR, con NPTR = piezas *teóricamente realizables*. La 34 la describe como "piezas buenas obtenidas / piezas realizadas". Con NPTR teórico, la pérdida de velocidad se contaría dos veces (en Rv y en Tq).
- **Decisión:** Tq = (piezas realizadas − desechadas o retrabajadas) / piezas realizadas, como en el OEE estándar y en la diapositiva 34.

### B-006: UNIDAD 4, diapositivas 42–45 (orden de las seis grandes pérdidas)

- **Duda:** la lista de la diapositiva 42 pone "tiempo en vacío y paradas cortas" en el 3.º lugar y "velocidad reducida" en el 4.º. La tabla de las diapositivas 43–45 los invierte.
- **Decisión:** el catálogo usa nombres y no números.

### B-007: UNIDAD 5, diapositivas 67–68 (stock de protección)

- **Fórmula:** Sp = H·√(c·d), verificada en la imagen de la diapositiva.
- **Observación:** la tabla de H coincide con el cuantil de la normal estándar z(1 − riesgo), con pequeñas diferencias de redondeo:

| Riesgo | H (tabla) | z exacto |
|---|---|---|
| 10 % | 1,29 | 1,2816 |
| 9 % | 1,35 | 1,3408 |
| 8 % | 1,41 | 1,4051 |

  √(c·d) supone varianza de la demanda igual a la media (Poisson).
- **Decisión:** H se calcula como Φ⁻¹(1 − riesgo) y la tabla de la cátedra se muestra como referencia. Para el **stock mínimo** del Plan se usa Poisson exacto, que es más correcto con demandas bajas (fracciones de unidad en el lead time). El Sp de la cátedra se muestra al lado para que el reporte "hable el mismo idioma".

### B-008: UNIDAD 5, diapositivas 47–62 (lote económico)

- **Verificado:** Ca = K·D/q; C_alm = ½·q·b·p; CTE = K·n + ½·q·b·P; q_e = √(2·K·D/(b·p)); K = gastos de compras del período / n.º de órdenes (ejemplo: $7.000/35 = $200).
- **Decisión:** se implementa tal cual.

### B-009: UNIDAD 5, diapositivas 27 y 28 (EFMP / EFMD y la tabla de índices)

- **Duda:** la diapositiva 27 llama al índice "Efectivo real o efectivo medio diario", pero su fórmula EFMP = HHAF/HHEF mide horas apartadas (vacaciones, accidentes, enfermedad) sobre horas efectivas, es decir, el ausentismo. La tabla de la diapositiva 28 lo escribe como **EFMD = (HHEF − HHAF)/HHEF**, que sí corresponde al nombre (valores 0,73–0,97).
- **Decisión:** se muestra EFMD = (HHEF − HHAF)/HHEF como "Efectivo real" y, al lado, el ausentismo = HHAF/HHEF, cada uno con su fórmula a la vista.
- **Además:** la tabla de la diapositiva 28 trae dos índices que no se definen en el texto: OAPM = HHSA/HHDP y PERC = TBMP/CMFT. No se implementan hasta tener su definición. También muestra valores negativos de OCPM (horas trabajadas mayores que las disponibles, es decir, horas extra). El sistema no los recorta a cero y los marca como "horas extra".

### B-010: UNIDAD 6, diapositivas 20–28 (plantillas)

- **Duda:** el texto de la plantilla de repuestos (diap. 23) trae "cantidad en stock" y no "costo"; el formulario MANT/RM001 (diap. 28) trae "costo" y no "cantidad en stock". En el registro de máquina pasa algo parecido: "condiciones de almacenamiento" está en el texto (diap. 21) y no en el formulario MANT/RHM001; "planos de referencia, manuales/catálogos" está en el formulario y no en el texto.
- **Decisión:** se toma la **unión** de los campos.

### B-011: UNIDAD 2, diapositiva 37 (revisión en t = η)

- **Qué dice:** "para un tiempo de funcionamiento igual al valor de η conviene realizar por lo menos un control del equipo y de la planificación del preventivo".
- **Decisión:** se implementa como sugerencia configurable en la ficha (12.H).

### B-012: UNIDAD 2, diapositivas 33–38 (ejemplo de Weibull)

- **Duda:** la diapositiva redondea β = 1,4 y lee η = 76 en el gráfico, y con eso R(15) = 90,2 %. Con RRX exacto da β = 1,440, η = 76,1 y R(15) = 90,8 %.
- **Decisión:** la diferencia viene del ajuste gráfico y entra en la tolerancia pedida (±10 % y ±2 puntos).

### B-013: Fuente del CTMC

- **Verificado:** la estructura CTMC = CDMC + CLC, con CDMC = MODM + CR + CM + CH y CLC = CO + CI + CDRP, está en la **UNIDAD 3** (mantenimiento correctivo, cálculo de costos). Ahí también están las fallas ocultas, el mantenimiento modificativo, el predictivo por ultrasonido (tabla de dB verificada) y el sobre/sub-mantenimiento.

### B-014: Contenido citado que no encontré en las unidades 2 a 6

- **Faltan:**
  - la criticidad por ponderaciones (porcentaje de uso, instalación alternativa, influencia, calidad, ambiente, seguridad);
  - la definición D = (TO − ΣTA)/TO;
  - la clasificación de fallas por efecto, capacidad y forma de aparición, y el diagrama de cuatro cuadrantes;
  - el diagrama de Ishikawa/5M.
- **Probable fuente:** la UNIDAD 1, que no recibí. La UNIDAD 4 solo menciona "5W + 1H + 5 ¿Por qué?" dentro del ciclo PDCA (diap. 11).
- **Decisión:** los puntajes del pedido se cargan editables y marcados "a verificar" hasta recibir la UNIDAD 1 (P-10).

### B-015: UNIDAD 2, diapositiva 34 (rangos medianos)

- **Duda:** la tabla de la diapositiva (10,91 / 26,44 / 42,14 / 57,86 / 73,56 / 89,10 %) son **rangos medianos exactos**: la mediana de la distribución beta(i, n − i + 1). No es la aproximación de Benard que dice usar. La propia diapositiva calcula con Benard 26,5 / 42,1 / 57,8 / 73,4 / 89 %.
- **Decisión:** el motor usa Benard (Plan §5). Existe `rango_mediano_exacto()` para validar. El test 3 verifica la tabla publicada con los rangos exactos y que Benard no se aparte más de 0,25 puntos.

