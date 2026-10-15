# Registro de decisiones

Cada entrada tiene: **qué** se decide, **por qué** y **alternativa descartada**. Las entradas **D-xxx** son decisiones de diseño y las **B-xxx** son dudas o correcciones sobre la bibliografía de la cátedra (Mgter. Leandro D. Torres, UTN-FRC).

**Estado:** todas están **propuestas** hasta tu OK al `PLAN_TECNICO.md`. Las que dependen de una pregunta abierta lo indican (P-xx).

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
