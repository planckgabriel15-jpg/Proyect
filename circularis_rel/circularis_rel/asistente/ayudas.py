"""Ayuda contextual "?" [12.H, P1]: definiciones en lenguaje simple, con su fuente.

Las definiciones salen de la bibliografía de la cátedra disponible (UNIDAD 2) y del Plan §6.
La UNIDAD 1 (definiciones generales) no se recibió: las marcadas "Plan §6" se revisarán cuando llegue.
"""

from __future__ import annotations

AYUDAS: dict[str, dict[str, str]] = {
    "fiabilidad": {
        "titulo": "Fiabilidad (confiabilidad) R(t)",
        "texto": "Probabilidad de que la máquina o el componente cumpla su función, sin fallar, durante un "
                 "tiempo determinado y en las condiciones dadas. R = 90 % a 400 h quiere decir que 9 de cada "
                 "10 piezas iguales llegan a las 400 h sin fallar.",
        "fuente": "UNIDAD 2, diap. 2",
    },
    "infiabilidad": {
        "titulo": "Infiabilidad F(t)",
        "texto": "Probabilidad de que falle antes de un tiempo dado. Siempre F(t) + R(t) = 1.",
        "fuente": "UNIDAD 2, diap. 3–4",
    },
    "mantenibilidad": {
        "titulo": "Mantenibilidad",
        "texto": "Facilidad y rapidez con que una máquina vuelve a funcionar después de una falla. "
                 "Se mide con el MTTR: cuanto más bajo, más mantenible.",
        "fuente": "Plan §6 (definición general; a verificar con la UNIDAD 1)",
    },
    "disponibilidad": {
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
        "titulo": "β, parámetro de forma de Weibull",
        "texto": "Dice cómo falla la pieza. β < 1: fallas de juventud (montaje, calidad del repuesto). "
                 "β ≈ 1: fallas al azar (cambiar antes no sirve). β > 1: desgaste (cambiar antes sí sirve).",
        "fuente": "UNIDAD 2, diap. 27; Plan §5",
    },
    "eta": {
        "titulo": "η, vida característica",
        "texto": "Edad a la que ya falló el 63,2 % de las piezas (queda el 36,8 %). La cátedra recomienda, al "
                 "llegar a η, al menos un control del equipo y revisar la planificación del preventivo.",
        "fuente": "UNIDAD 2, diap. 36–37",
    },
    "p_delta": {
        "titulo": "Probabilidad de falla en el horizonte P(Δ)",
        "texto": "Probabilidad de que el componente falle antes de la próxima parada programada (o en las próximas "
                 "dos semanas), sabiendo que llegó sano a su edad actual: P = 1 − R(edad + Δ) / R(edad). "
                 "La banda entre paréntesis sale de los extremos del intervalo de confianza de β y η.",
        "fuente": "Plan §6 y §7",
    },
    "semaforo": {
        "titulo": "Semáforo",
        "texto": "Rojo: probabilidad de falla en el horizonte alta, edad mayor al intervalo recomendado o un aviso "
                 "abierto. Amarillo: probabilidad intermedia o edad mayor al 80 % del intervalo. Verde: lo demás. "
                 "Gris: todavía no hay datos suficientes. La máquina toma el peor color de sus componentes críticos. "
                 "Los umbrales se cambian en Parámetros.",
        "fuente": "Plan §7; D-012",
    },
    "confianza": {
        "titulo": "Confianza del cálculo",
        "texto": "Cuántas fallas hay detrás del número. Gris: menos de 3 (no hay ajuste). Baja: de 3 a 5. "
                 "Media: de 6 a 19. Alta: 20 o más. Con confianza baja el color es orientativo: no tomes una "
                 "decisión cara solo con eso.",
        "fuente": "Plan §5; P-08",
    },
    "vida_remanente": {
        "titulo": "Vida remanente",
        "texto": "Horas que le quedan al componente, desde su edad actual, con 50 % de probabilidad (mediana) o "
                 "con 90 % de probabilidad de llegar sin fallar.",
        "fuente": "Plan §6",
    },
    "intervalo": {
        "titulo": "Intervalo recomendado",
        "texto": "Cada cuántas horas conviene cambiar el componente de manera preventiva. Sale del plan aprobado, "
                 "del cálculo (mínimo costo por hora o confiabilidad objetivo, solo si hay desgaste, β > 1) o, si "
                 "no hay datos, del fabricante.",
        "fuente": "Plan §8",
    },
    "riesgo": {
        "titulo": "Ranking de riesgo",
        "texto": "Probabilidad de falla en el horizonte multiplicada por lo que cuesta una falla (repuesto, mano de "
                 "obra y producción perdida). Ordena dónde conviene actuar primero.",
        "fuente": "Plan §7",
    },
    "costo_falla": {
        "titulo": "Costo de una falla (Cf) y de un preventivo (Cp)",
        "texto": "Cp = repuesto + horas-hombre del cambio planificado × tarifa. Cf = repuesto + horas-hombre de la "
                 "reparación × tarifa + horas de parada que exceden el pulmón × margen por hora de la línea.",
        "fuente": "Plan §8; UNIDAD 5 (CTMC)",
    },
    "costo_t": {
        "titulo": "Curva de costo C(T)",
        "texto": "Costo por hora de cambiar el componente cada T horas: C(T) = [Cp·R(T) + Cf·F(T)] / ∫₀ᵀ R(t) dt. "
                 "El mínimo es el intervalo óptimo T*. Solo existe si hay desgaste (β > 1) y la falla cuesta más "
                 "que el preventivo. Cerca del mínimo la curva es plana: por eso se redondea.",
        "fuente": "Plan §8",
    },
    "grafico_probabilidad": {
        "titulo": "Gráfico de probabilidad Weibull",
        "texto": "Cada punto es una falla (las suspensiones no se dibujan pero corren los rangos). Si los puntos "
                 "siguen la recta, Weibull describe bien los datos. La pendiente de la recta es β.",
        "fuente": "UNIDAD 2; Plan §5",
    },
    "pareto": {
        "titulo": "Diagrama de Pareto",
        "texto": "Ordena los problemas de mayor a menor y muestra el porcentaje acumulado. En general unos pocos "
                 "explican la mayor parte (regla 80/20): esos son los que conviene atacar primero.",
        "fuente": "Plan §6; UNIDAD 4 (mejoras enfocadas)",
    },
    "cinco_porques": {
        "titulo": "5 Porqués",
        "texto": "Partís del problema y preguntás \"¿por qué pasó?\". A la respuesta le volvés a preguntar \"¿por "
                 "qué?\", hasta llegar a una causa sobre la que se pueda actuar (la causa raíz). No siempre hacen "
                 "falta cinco.",
        "fuente": "UNIDAD 4, diap. 11",
    },
    "pdca": {
        "titulo": "Ciclo PDCA",
        "texto": "Planificar (dónde, qué, quién, cómo, cuándo), Hacer (ejecutar y registrar), Chequear (comparar "
                 "el resultado con la meta) y Analizar (buscar la causa raíz con 5W+1H y 5 Porqués). Se repite "
                 "hasta que el problema deja de aparecer.",
        "fuente": "UNIDAD 4, diap. 11",
    },
    "calidad_datos": {
        "titulo": "Calidad de los datos",
        "texto": "Porcentaje de partes de turno cargados por el operario (no estimados por el sistema) y porcentaje "
                 "de avisos validados dentro de las 48 h. Si baja, los cálculos pierden valor.",
        "fuente": "Plan §11",
    },
    "ao": {
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
    "crow_amsaa": {"titulo": "Tendencia de la máquina (Crow-AMSAA y Laplace)",
                   "texto": "Mira la máquina entera como algo que se repara: si las fallas llegan cada vez más seguido "
                            "(β > 1, Laplace positivo) se está degradando y conviene revisar su estado general; si se espacian "
                            "(β < 1), mejora. Con pocas fallas, la tendencia no es concluyente.",
                   "fuente": "Plan §5 (IEC 61710)"},
    "bayes": {"titulo": "Weibull bayesiano",
              "texto": "Con pocas fallas, el β de referencia entra como una creencia previa con margen de error y los datos "
                       "la corrigen. A diferencia de Weibayes, β no queda fijo. Con muchos datos se parece al ajuste común.",
              "fuente": "Plan §5 (mejora de la fase 4)"},
}
