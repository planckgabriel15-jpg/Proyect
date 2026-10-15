"""Criticidad de equipos [12.C].

Método del TP (predeterminado): seis criterios con las escalas del TP N.º 1 (análisis de
prioridad de máquinas). El puntaje es la **suma** de los seis valores y el nivel sale de los
cortes del TP: ≥ 25 Alta; 20–24 Media; 15–19 Baja; < 15 Muy baja. La clase A/B/C del sistema
se obtiene con una equivalencia configurable (D-020).

El Plan §8 habla de "seis criterios ponderados" (0,30; 0,20; 0,15; 0,15; 0,10; 0,10). El TP N.º 1
suma sin pesos. Se calculan las dos cosas; la clase sale del método del TP (D-020).

Escalas del TP N.º 1 (verificadas contra el documento):
- uso (influencia sobre la producción): 5 (>80 %), 3 (50–80 %), 1 (<50 %)
- instalación alternativa: 5 (sin alternativa ni recurso externo), 4 (recurso externo), 2 (resguardo), 1 (duplicado)
- influencia sobre el resto de la planta: 5, 4, 2, 1
- calidad del producto final: 5, 4, 2, 1
- medio ambiente: 5, 3, 1
- seguridad: 5, 3, 1
"""

from __future__ import annotations

from dataclasses import dataclass

CRITERIOS = ("uso", "alternativa", "influencia", "calidad", "ambiente", "seguridad")

ESCALAS_TP: dict[str, tuple[int, ...]] = {
    "uso": (5, 3, 1),
    "alternativa": (5, 4, 2, 1),
    "influencia": (5, 4, 2, 1),
    "calidad": (5, 4, 2, 1),
    "ambiente": (5, 3, 1),
    "seguridad": (5, 3, 1),
}

# Equivalencia con los nombres del Plan §8 para la variante ponderada.
CRITERIO_PLAN = {
    "uso": "produccion",
    "influencia": "influencia",
    "calidad": "calidad",
    "seguridad": "seguridad",
    "ambiente": "ambiente",
    "alternativa": "sustitucion",
}


@dataclass(frozen=True)
class ResultadoCriticidad:
    puntaje: float
    nivel: str
    clase: str
    puntaje_ponderado: float | None


def valores_invalidos(valores: dict[str, int], escalas: dict[str, tuple[int, ...]] = ESCALAS_TP) -> list[str]:
    errores = []
    for c in CRITERIOS:
        v = valores.get(c)
        if v is None:
            errores.append(f"falta el criterio '{c}'")
        elif v not in escalas[c]:
            errores.append(f"'{c}' = {v} no está en la escala {escalas[c]}")
    return errores


def nivel_por_cortes(puntaje: float, cortes: dict[str, float]) -> str:
    """cortes = {"Alta": 25, "Media": 20, "Baja": 15}; debajo del menor corte es "Muy baja"."""
    for nivel, minimo in sorted(cortes.items(), key=lambda kv: -kv[1]):
        if puntaje >= minimo:
            return nivel
    return "Muy baja"


def evaluar_tp(
    valores: dict[str, int],
    cortes: dict[str, float],
    nivel_a_clase: dict[str, str],
    pesos_plan: dict[str, float] | None = None,
) -> ResultadoCriticidad:
    errores = valores_invalidos(valores)
    if errores:
        raise ValueError("; ".join(errores))
    puntaje = float(sum(valores[c] for c in CRITERIOS))
    nivel = nivel_por_cortes(puntaje, cortes)
    if nivel not in nivel_a_clase:
        raise ValueError(f"El nivel '{nivel}' no tiene clase A/B/C asignada")
    ponderado = None
    if pesos_plan:
        ponderado = round(sum(valores[c] * pesos_plan[CRITERIO_PLAN[c]] for c in CRITERIOS), 4)
    return ResultadoCriticidad(puntaje=puntaje, nivel=nivel, clase=nivel_a_clase[nivel], puntaje_ponderado=ponderado)


# ---------------------------------------------------------------------------
# Criticidad guiada en pantalla [12.C]: textos de cada opción y método U1
# ---------------------------------------------------------------------------

PREGUNTAS = {
    "uso": "¿Qué porcentaje del tiempo se usa la máquina para producir?",
    "alternativa": "Si se para, ¿hay otra forma de seguir produciendo?",
    "influencia": "¿Cuánto afecta su parada al resto de la planta?",
    "calidad": "¿Cuánto influye en la calidad del producto final?",
    "ambiente": "Si falla, ¿qué impacto tiene en el medio ambiente?",
    "seguridad": "Si falla, ¿qué riesgo hay para las personas o los equipos?",
}

# Descripciones de cada nivel (pedido §12.C, que cita la UNIDAD 1; el TP N.º 1 usa las mismas categorías
# con otros puntajes en uso, ambiente y seguridad).
OPCIONES = {
    "uso": ["Más del 80 %", "Entre 50 % y 80 %", "Menos del 50 %"],
    "alternativa": ["Sin posibilidad de reemplazo", "Con recurso externo", "Con recurso en stock (resguardo)", "Equipo duplicado"],
    "influencia": ["Para toda la planta", "Importante", "Relativa", "Solo afecta al equipo"],
    "calidad": ["Decisiva", "Importante (retrabajo)", "Relativa (dentro de tolerancia)", "Nula"],
    "ambiente": ["Grave", "Relativa", "Nula"],
    "seguridad": ["Riesgo para el operario", "Riesgo para el equipo", "Relativo"],
}


def opciones(metodo: str, escalas_u1: dict[str, list[int]] | None = None) -> dict[str, list[tuple[int, str]]]:
    """(puntaje, texto) de cada opción, en el orden de la escala, para el método elegido."""
    escalas = ESCALAS_TP if metodo == "TP_6_CRITERIOS" else {k: tuple(v) for k, v in (escalas_u1 or {}).items()}
    salida = {}
    for c in CRITERIOS:
        if len(escalas[c]) != len(OPCIONES[c]):
            raise ValueError(f"La escala de '{c}' tiene {len(escalas[c])} valores y hay {len(OPCIONES[c])} opciones")
        salida[c] = list(zip(escalas[c], OPCIONES[c], strict=True))
    return salida


def clase_por_cortes(puntaje: float, cortes: dict[str, float] | None) -> str | None:
    """cortes = {"A": 22, "B": 16}: puntaje ≥ A → A; ≥ B → B; si no, C. Sin cortes, None (clase a mano)."""
    if not cortes:
        return None
    if puntaje >= cortes["A"]:
        return "A"
    return "B" if puntaje >= cortes["B"] else "C"


def evaluar_u1(valores: dict[str, int], escalas: dict[str, list[int]], cortes: dict[str, float] | None) -> ResultadoCriticidad:
    """Ponderación de la UNIDAD 1 (a verificar, P-10): suma de los seis criterios con sus escalas. La clase
    sale de los cortes configurados; si no hay cortes, queda vacía y la elige el jefe."""
    errores = valores_invalidos(valores, {k: tuple(v) for k, v in escalas.items()})
    if errores:
        raise ValueError("; ".join(errores))
    puntaje = float(sum(valores[c] for c in CRITERIOS))
    return ResultadoCriticidad(puntaje=puntaje, nivel="", clase=clase_por_cortes(puntaje, cortes) or "",
                               puntaje_ponderado=None)
