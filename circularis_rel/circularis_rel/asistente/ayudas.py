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
}
