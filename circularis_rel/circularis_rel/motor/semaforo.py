"""Semáforo por componente y por máquina (Plan §7; D-012).

Rojo: P(Δ) ≥ umbral rojo, o edad > intervalo vigente, o OT correctiva abierta.
Amarillo: P(Δ) ≥ umbral amarillo, o edad > 80 % del intervalo.
Verde: P(Δ) < umbral amarillo y edad < intervalo.
Gris: sin ajuste (datos insuficientes): solo KPIs empíricos. Si hay intervalo (del fabricante), la regla de
edad igual aplica. Con confianza baja nunca hay un color "duro": se informa la confianza y la banda.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ORDEN = {"GRIS": 0, "VERDE": 1, "AMARILLO": 2, "ROJO": 3}


@dataclass(frozen=True)
class Umbrales:
    p_amarillo: float = 0.10
    p_rojo: float = 0.30
    p_amarillo_a: float = 0.05
    p_rojo_a: float = 0.20
    fraccion_intervalo: float = 0.80


UMBRALES_PLAN = Umbrales()


@dataclass
class Color:
    color: str
    motivos: list[str] = field(default_factory=list)
    confianza: str = "GRIS"
    duro: bool = False  # True solo con confianza media o alta

    @property
    def etiqueta(self) -> str:
        if self.color == "GRIS":
            return "Datos insuficientes"
        return f"{self.color.capitalize()} · confianza {self.confianza.lower()}"


def color_componente(p_delta: float | None, edad: float | None, intervalo: float | None, ot_abierta: bool,
                     confianza: str, clase: str | None, u: Umbrales = UMBRALES_PLAN, delta: float | None = None) -> Color:
    amarillo, rojo = (u.p_amarillo_a, u.p_rojo_a) if clase == "A" else (u.p_amarillo, u.p_rojo)
    motivos: list[str] = []
    nivel = "GRIS" if p_delta is None else "VERDE"
    if p_delta is not None:
        horizonte = f" en {delta:.0f} h" if delta else ""
        if p_delta >= rojo:
            nivel = "ROJO"
            motivos.append(f"{p_delta:.0%} de probabilidad de falla{horizonte} (umbral {rojo:.0%})")
        elif p_delta >= amarillo:
            nivel = "AMARILLO"
            motivos.append(f"{p_delta:.0%} de probabilidad de falla{horizonte} (umbral {amarillo:.0%})")
    if intervalo and edad is not None:
        if edad > intervalo:
            nivel = "ROJO"
            motivos.append(f"Edad {edad:.0f}, mayor al intervalo recomendado ({intervalo:.0f})")
        elif edad > u.fraccion_intervalo * intervalo and ORDEN[nivel] < ORDEN["AMARILLO"]:
            nivel = "AMARILLO"
            motivos.append(f"Edad {edad:.0f}, más del {u.fraccion_intervalo:.0%} del intervalo ({intervalo:.0f})")
    if ot_abierta:
        nivel = "ROJO"
        motivos.append("OT correctiva abierta")
    return Color(nivel, motivos, confianza, duro=confianza in ("MEDIA", "ALTA"))


def color_maquina(colores_criticos: list[Color]) -> Color:
    """La máquina toma el peor color de sus componentes críticos."""
    if not colores_criticos:
        return Color("GRIS", ["Sin componentes críticos marcados"])
    peor = max(colores_criticos, key=lambda c: ORDEN[c.color])
    return Color(peor.color, list(peor.motivos), peor.confianza, peor.duro)
