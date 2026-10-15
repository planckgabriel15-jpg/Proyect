"""Ayuda contextual "?" [12.H, P1]: definiciones en lenguaje simple, con su fuente.

Las definiciones salen de la bibliografía de la cátedra disponible (UNIDAD 2) y del Plan §6.
La UNIDAD 1 (definiciones generales) no se recibió: las marcadas "Plan §6" se revisarán cuando llegue.
"""

from __future__ import annotations

AYUDAS: dict[str, dict[str, str]] = {
    "fiabilidad": {
        "corto": "¿Qué es R(t)?",
        "titulo": "Fiabilidad (confiabilidad) R(t)",
        "texto": "Probabilidad de que la máquina o el componente cumpla su función, sin fallar, durante un "
                 "tiempo determinado y en las condiciones dadas. R = 90 % a 400 h quiere decir que 9 de cada "
                 "10 piezas iguales llegan a las 400 h sin fallar.",
        "fuente": "UNIDAD 2, diap. 2",
    },
    "infiabilidad": {
        "corto": "¿Qué es F(t)?",
        "titulo": "Infiabilidad F(t)",
        "texto": "Probabilidad de que falle antes de un tiempo dado. Siempre F(t) + R(t) = 1.",
        "fuente": "UNIDAD 2, diap. 3–4",
    },
    "mantenibilidad": {
        "corto": "¿Qué es la mantenibilidad?",
        "titulo": "Mantenibilidad",
        "texto": "Facilidad y rapidez con que una máquina vuelve a funcionar después de una falla. "
                 "Se mide con el MTTR: cuanto más bajo, más mantenible.",
        "fuente": "Plan §6 (definición general; a verificar con la UNIDAD 1)",
    },
    "disponibilidad": {
        "corto": "¿Qué es la disponibilidad?",
        "titulo": "Disponibilidad",
        "texto": "Fracción del tiempo requerido en que la máquina estuvo en condiciones de producir. "
                 "Las horas sin demanda o de huelga no cuentan como tiempo requerido. "
                 "Inherente: Ai = MTBF / (MTBF + MTTR). Operacional: Ao = (horas requeridas − horas paradas) / horas requeridas.",
        "fuente": "Plan §6; D-007",
    },
    "mtbf": {
        "titulo": "MTBF: tiempo medio entre fallas",
        "texto": "Horas operadas divididas por la cantidad de fallas. Si una máquina operó 4.310 h y tuvo 8 fallas, "
                 "el MTBF es 539 h: en promedio, una falla cada 539 h de trabajo.",
        "fuente": "Plan §6 y §15",
    },
    "mttr": {
        "titulo": "MTTR: tiempo medio de reparación",
        "texto": "Suma de los tiempos de reparación activa dividida por la cantidad de reparaciones. "
                 "No incluye la espera del técnico o del repuesto (eso va en el MTTR total o MDT).",
        "fuente": "Plan §6",
    },
    "mdt": {
        "corto": "¿Qué es el MDT?",
        "titulo": "MDT o MTTR total: tiempo medio de parada",
        "texto": "Tiempo de máquina parada por falla, incluida la espera de técnico o repuesto, dividido por la "
                 "cantidad de fallas. Es lo que ve producción.",
        "fuente": "Plan §6 (MTTR total)",
    },
    "mttf": {
        "titulo": "MTTF: vida media hasta la falla",
        "texto": "Para piezas que se reemplazan (no se reparan): tiempo promedio que duran hasta fallar. "
                 "Con Weibull, MTTF = η·Γ(1 + 1/β).",
        "fuente": "UNIDAD 2, diap. 11–13; Plan §6",
    },
    "beta": {
        "corto": "¿Qué es β?",
        "titulo": "β, parámetro de forma de Weibull",
        "texto": "Dice cómo falla la pieza. β < 1: fallas de juventud (montaje, calidad del repuesto). "
                 "β ≈ 1: fallas al azar (cambiar antes no sirve). β > 1: desgaste (cambiar antes sí sirve).",
        "fuente": "UNIDAD 2, diap. 27; Plan §5",
    },
    "eta": {
        "corto": "¿Qué es η?",
        "titulo": "η, vida característica",
        "texto": "Edad a la que ya falló el 63,2 % de las piezas (queda el 36,8 %). La cátedra recomienda, al "
                 "llegar a η, al menos un control del equipo y revisar la planificación del preventivo.",
        "fuente": "UNIDAD 2, diap. 36–37",
    },
    "p_delta": {
        "corto": "¿Qué es P(falla)?",
        "titulo": "Probabilidad de falla en el horizonte P(Δ)",
        "texto": "Probabilidad de que el componente falle antes de la próxima parada programada (o en las próximas "
                 "dos semanas), sabiendo que llegó sano a su edad actual: P = 1 − R(edad + Δ) / R(edad). "
                 "La banda entre paréntesis sale de los extremos del intervalo de confianza de β y η.",
        "fuente": "Plan §6 y §7",
    },
    "semaforo": {
        "corto": "¿Cómo se arma el semáforo?",
        "titulo": "Semáforo",
        "texto": "Rojo: probabilidad de falla en el horizonte alta, edad mayor al intervalo recomendado o un aviso "
                 "abierto. Amarillo: probabilidad intermedia o edad mayor al 80 % del intervalo. Verde: lo demás. "
                 "Gris: todavía no hay datos suficientes. La máquina toma el peor color de sus componentes críticos. "
                 "Los umbrales se cambian en Parámetros.",
        "fuente": "Plan §7; D-012",
    },
    "confianza": {
        "corto": "¿Qué es la confianza?",
        "titulo": "Confianza del cálculo",
        "texto": "Cuántas fallas hay detrás del número. Gris: menos de 3 (no hay ajuste). Baja: de 3 a 5. "
                 "Media: de 6 a 19. Alta: 20 o más. Con confianza baja el color es orientativo: no tomes una "
                 "decisión cara solo con eso.",
        "fuente": "Plan §5; P-08",
    },
    "vida_remanente": {
        "corto": "¿Qué es la vida remanente?",
        "titulo": "Vida remanente",
        "texto": "Horas que le quedan al componente, desde su edad actual, con 50 % de probabilidad (mediana) o "
                 "con 90 % de probabilidad de llegar sin fallar.",
        "fuente": "Plan §6",
    },
    "intervalo": {
        "corto": "¿Qué es el intervalo?",
        "titulo": "Intervalo recomendado",
        "texto": "Cada cuántas horas conviene cambiar el componente de manera preventiva. Sale del plan aprobado, "
                 "del cálculo (mínimo costo por hora o confiabilidad objetivo, solo si hay desgaste, β > 1) o, si "
                 "no hay datos, del fabricante.",
        "fuente": "Plan §8",
    },
    "riesgo": {
        "corto": "¿Qué es el riesgo?",
        "titulo": "Ranking de riesgo",
        "texto": "Probabilidad de falla en el horizonte multiplicada por lo que cuesta una falla (repuesto, mano de "
                 "obra y producción perdida). Ordena dónde conviene actuar primero.",
        "fuente": "Plan §7",
    },
    "costo_falla": {
        "corto": "¿Qué son Cf y Cp?",
        "titulo": "Costo de una falla (Cf) y de un preventivo (Cp)",
        "texto": "Cp = repuesto + horas-hombre del cambio planificado × tarifa. Cf = repuesto + horas-hombre de la "
                 "reparación × tarifa + horas de parada que exceden el pulmón × margen por hora de la línea.",
        "fuente": "Plan §8; UNIDAD 5 (CTMC)",
    },
    "costo_t": {
        "corto": "¿Qué es C(T)?",
        "titulo": "Curva de costo C(T)",
        "texto": "Costo por hora de cambiar el componente cada T horas: C(T) = [Cp·R(T) + Cf·F(T)] / ∫₀ᵀ R(t) dt. "
                 "El mínimo es el intervalo óptimo T*. Solo existe si hay desgaste (β > 1) y la falla cuesta más "
                 "que el preventivo. Cerca del mínimo la curva es plana: por eso se redondea.",
        "fuente": "Plan §8",
    },
    "grafico_probabilidad": {
        "corto": "Cómo leer el papel",
        "titulo": "Gráfico de probabilidad Weibull",
        "texto": "Es el papel de Weibull de la cátedra: el tiempo va en escala logarítmica y F(t) en escala de Weibull, "
                 "así una distribución de Weibull queda como una recta. Cada punto rojo es una falla con su F(i) por "
                 "rango de Benard (las suspensiones no se dibujan pero corren los rangos). Si los puntos siguen la "
                 "recta, Weibull describe bien los datos. Cómo se lee: β es la pendiente (la guía azul del abanico "
                 "paralela a la recta); η es donde la recta corta la línea punteada del 63,2 %; y para un tiempo de "
                 "misión se sube hasta la recta y se lee F a la izquierda (R = 1 − F). Pasá el mouse por cada línea "
                 "para ver qué es.",
        "fuente": "UNIDAD 2, diap. 31–38; Plan §5",
    },
    "pareto": {
        "corto": "¿Qué es Pareto?",
        "titulo": "Diagrama de Pareto",
        "texto": "Ordena los problemas de mayor a menor y muestra el porcentaje acumulado. En general unos pocos "
                 "explican la mayor parte (regla 80/20): esos son los que conviene atacar primero.",
        "fuente": "Plan §6; UNIDAD 4 (mejoras enfocadas)",
    },
    "cinco_porques": {
        "corto": "¿Qué son los 5 porqués?",
        "titulo": "5 Porqués",
        "texto": "Partís del problema y preguntás \"¿por qué pasó?\". A la respuesta le volvés a preguntar \"¿por "
                 "qué?\", hasta llegar a una causa sobre la que se pueda actuar (la causa raíz). No siempre hacen "
                 "falta cinco.",
        "fuente": "UNIDAD 4, diap. 11",
    },
    "pdca": {
        "corto": "¿Qué es PDCA?",
        "titulo": "Ciclo PDCA",
        "texto": "Planificar (dónde, qué, quién, cómo, cuándo), Hacer (ejecutar y registrar), Chequear (comparar "
                 "el resultado con la meta) y Analizar (buscar la causa raíz con 5W+1H y 5 Porqués). Se repite "
                 "hasta que el problema deja de aparecer.",
        "fuente": "UNIDAD 4, diap. 11",
    },
    "calidad_datos": {
        "corto": "¿Qué es la calidad de datos?",
        "titulo": "Calidad de los datos",
        "texto": "Porcentaje de partes de turno cargados por el operario (no estimados por el sistema) y porcentaje "
                 "de avisos validados dentro de las 48 h. Si baja, los cálculos pierden valor.",
        "fuente": "Plan §11",
    },
    "ao": {
        "corto": "¿Qué es Ao?",
        "titulo": "Disponibilidad operacional Ao",
        "texto": "(Horas requeridas − horas paradas) / horas requeridas, desde los partes de turno. Las horas sin "
                 "demanda o de huelga no cuentan como requeridas.",
        "fuente": "Plan §6; D-007",
    },
    "CMFT": {"titulo": "CMFT: costo de mantenimiento por facturación",
             "texto": "Costo total de mantenimiento del período dividido por la facturación del período.",
             "fuente": "UNIDAD 5, diap. 16"},
    "CPCT": {"titulo": "CPCT: costo preventivo sobre costo total",
             "texto": "Muestra cuánto se usan las técnicas preventivas frente a las correctivas. Puede rondar el 20 %.",
             "fuente": "UNIDAD 5, diap. 20"},
    "HPHP": {"titulo": "HPHP: horas de paro por horas de producción",
             "texto": "Horas de paro de los equipos por averías sobre las horas empleadas en producir. "
                      "Generalmente entre 1 % y 3 %.",
             "fuente": "UNIDAD 5, diap. 21"},
    "TBMP": {"titulo": "TBMP: trabajo en mantenimiento preventivo",
             "texto": "Horas-hombre en trabajos programados de preventivo sobre las horas-hombre disponibles (personal "
                      "presente y en condiciones de trabajar).",
             "fuente": "UNIDAD 5, diap. 22"},
    "TBMC": {"titulo": "TBMC: trabajo en mantenimiento correctivo",
             "texto": "Horas-hombre en reparaciones correctivas sobre las horas-hombre disponibles.",
             "fuente": "UNIDAD 5, diap. 23"},
    "OCPM": {"titulo": "OCPM: ociosidad del personal de mantenimiento",
             "texto": "Horas-hombre disponibles menos las trabajadas, sobre las disponibles: cuánto tiempo del personal "
                      "no se ocupó. Negativo indica horas extra.",
             "fuente": "UNIDAD 5, diap. 24 y 28"},
    "CMOE": {"titulo": "CMOE: mano de obra externa",
             "texto": "Gasto en mano de obra externa (contratada) sobre la mano de obra total de los servicios (propia y "
                      "contratada) en el período.",
             "fuente": "UNIDAD 5, diap. 17"},
    "CMPP": {"titulo": "CMPP: costo de mantenimiento por producción",
             "texto": "Influencia del costo de mantenimiento en el costo final del producto. Normalmente oscila entre el 5 % "
                      "y el 6 % (referencia, no meta).",
             "fuente": "UNIDAD 5, diap. 18"},
    "CMPV": {"titulo": "CMPV: costo de mantenimiento por valor inmovilizado",
             "texto": "Costo de mantenimiento sobre el valor inmovilizado bruto de máquinas y equipos: muestra el envejecimiento "
                      "de la instalación. Puede rondar entre el 4 % y el 5 % (referencia, no meta).",
             "fuente": "UNIDAD 5, diap. 19"},
    "TBML": {"titulo": "TBML: trabajo de mantenimiento en línea",
             "texto": "Horas-hombre de mantenimiento hechas en la línea (mantenimiento autónomo) sobre las horas-hombre "
                      "disponibles.",
             "fuente": "UNIDAD 4 (TPM); PLAN_TECNICO §8.3"},
    "PETI": {"titulo": "PETI: entrenamiento interno",
             "texto": "Horas-hombre usadas en entrenamiento interno sobre las horas-hombre disponibles.",
             "fuente": "UNIDAD 5, diap. 25"},
    "CSMP": {"titulo": "CSMP: clima social, movimiento de personal",
             "texto": "Efectivo medio de los meses anteriores sobre ese efectivo más las transferencias y las renuncias "
                      "voluntarias. Cuanto más cerca de 1, menos rotación.",
             "fuente": "UNIDAD 5, diap. 26"},
    "EFMD": {"titulo": "EFMD: efectivo real",
             "texto": "Horas-hombre efectivas menos las apartadas (vacaciones, accidentes, enfermedad) sobre las efectivas. "
                      "Al lado se muestra el ausentismo (apartadas sobre efectivas).",
             "fuente": "UNIDAD 5, diap. 27–28 (B-009)"},
    "crow_amsaa": {"corto": "¿Qué es la tendencia?","titulo": "Tendencia de la máquina (Crow-AMSAA y Laplace)",
                   "texto": "Mira la máquina entera como algo que se repara: si las fallas llegan cada vez más seguido "
                            "(β > 1, Laplace positivo) se está degradando y conviene revisar su estado general; si se espacian "
                            "(β < 1), mejora. Con pocas fallas, la tendencia no es concluyente.",
                   "fuente": "Plan §5 (IEC 61710)"},
    "bayes": {"corto": "¿Qué es el bayesiano?","titulo": "Weibull bayesiano",
              "texto": "Con pocas fallas, el β de referencia entra como una creencia previa con margen de error y los datos "
                       "la corrigen. A diferencia de Weibayes, β no queda fijo. Con muchos datos se parece al ajuste común.",
              "fuente": "Plan §5 (mejora de la fase 4)"},
    "rango_benard": {"corto": "¿Qué es F(i)?","titulo": "F(i) por rango de Benard",
                     "texto": "Con pocos datos no se puede contar qué porcentaje falló: se estima. Se ordenan las fallas "
                              "de menor a mayor (i = 1, 2, …) y F(i) = (i − 0,3) / (N + 0,4), con N = cantidad de datos. "
                              "Si hay suspensiones (piezas que se sacaron o siguen andando sin fallar), i pasa a ser el "
                              "rango ajustado de Johnson, que tiene en cuenta cuántas quedaban en servicio.",
                     "fuente": "UNIDAD 2, diap. 31–34 (B-002 y B-015)"},
    "polo_beta": {"corto": "Polo y abanico de β","titulo": "Polo y abanico de β",
                  "texto": "En el borde izquierdo, a la altura del 63,2 %, está el polo. Desde ahí salen guías con "
                           "distintas pendientes y su valor de β arriba. Se busca la guía paralela a la recta de los "
                           "datos (la flecha negra) y se lee β. Es lo mismo que medir la pendiente de la recta.",
                  "fuente": "UNIDAD 2, diap. 35"},
    "lectura_mision": {"corto": "Leer R a un tiempo","titulo": "Confiabilidad para un tiempo de misión",
                       "texto": "Desde el tiempo de misión en el eje horizontal se sube hasta la recta y se va a la "
                                "izquierda: ahí se lee F(t). La confiabilidad es R(t) = 1 − F(t) = e^−(t/η)^β. Ejemplo "
                                "de la cátedra: a 15 h, F = 9,8 % y R = 90,2 %: el 90,2 % de los equipos supera las 15 h.",
                       "fuente": "UNIDAD 2, diap. 38–39"},
    "r2": {"corto": "¿Qué es r²?","titulo": "r²: qué tan recta es la nube de puntos",
           "texto": "Mide cuánto se parecen los puntos a una recta en el papel (1 = recta perfecta). Se compara con el "
                    "r² crítico: si queda por debajo, Weibull de 2 parámetros no describe bien los datos. Suele pasar "
                    "cuando se mezclan modos de falla distintos (por ejemplo, rodamiento y PLC) o hay una vida mínima γ.",
           "fuente": "Plan §5 (prueba de bondad de ajuste por r² crítico)"},
    "suspension": {"corto": "¿Qué es una suspensión?","titulo": "Suspensión (dato censurado)",
                   "texto": "Una pieza que no falló por el modo analizado: se cambió en un preventivo, falló por otra "
                            "causa o sigue andando. No es una falla, pero sí información: aguantó al menos ese tiempo. "
                            "Descartarla haría ver la pieza peor de lo que es.",
                   "fuente": "Plan §5"},
    "estado_weibull": {"corto": "Estado según β","titulo": "Estado según β (curva de la bañera)",
                       "texto": "β < 1: juventud (fallas tempranas: montaje, repuesto, arranque). β ≈ 1: estable, fallas "
                                "al azar (la edad no influye). β > 1: desgaste (el riesgo crece con la edad; vejez o "
                                "fatiga). El sistema toma β ≈ 1 entre 0,9 y 1,1, o si el intervalo de β contiene al 1.",
                       "fuente": "UNIDAD 2, diap. 27; D-006"},
    "criticidad_100": {"corto": "¿Qué es la criticidad /100?","titulo": "Criticidad sobre 100 (planilla de la empresa)",
                       "texto": "Es la ponderación de la planilla \"Listado de Máquinas y Detalle\": cada criterio de 1 a 5 "
                                "se lleva a una escala de 0 a 1 con (valor − 1) / 4 y se pondera con 30 % producción, 20 % "
                                "influencia en la planta, 15 % calidad, 15 % seguridad, 10 % ambiente y 10 % sustitución. "
                                "0 = nada crítica; 100 = todos los criterios al máximo. La Agrumadora 1 da 73,75.",
                       "fuente": "Planilla de criticidad del grupo (rev. 2, 08/07/2026); pesos del Plan §8; D-069"},
}
