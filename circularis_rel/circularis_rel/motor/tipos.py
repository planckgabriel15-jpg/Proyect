"""Tipos de entrada y salida del motor. Sin dependencias de la base ni de la interfaz."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Estado = Literal["F", "S", "I"]  # falla, suspensión por derecha, censura por intervalo


@dataclass(frozen=True)
class Observacion:
    """Una vida de la población (tipo de componente + modo).

    - "F": falló a la edad `edad` por el modo analizado.
    - "S": suspensión por derecha a la edad `edad` (preventivo, en servicio, otro modo, retiro).
    - "I": falló entre `edad_inf` y `edad` (histórico con fecha aproximada); solo MLE.
    """

    edad: float
    estado: Estado
    edad_inf: float | None = None
    nivel_hora: Literal["M", "D", "E"] = "D"
    solo_pronostico: bool = False
    etiqueta: str | None = None

    def __post_init__(self) -> None:
        if self.edad < 0:
            raise ValueError("La edad no puede ser negativa")
        if self.estado == "I" and (self.edad_inf is None or self.edad_inf < 0 or self.edad_inf > self.edad):
            raise ValueError("La censura por intervalo necesita 0 ≤ edad_inf ≤ edad")


@dataclass(frozen=True)
class Configuracion:
    """Umbrales del motor (vienen de la tabla `parametro`; estos son los valores del Plan)."""

    nivel_ic: float = 0.90
    min_fallas_rrx: int = 3
    min_fallas_mle: int = 20
    max_frac_suspensiones_rrx: float = 0.50
    n_max_rba: int = 30
    beta_aleatoria_min: float = 0.9
    beta_aleatoria_max: float = 1.1
    beta_aleatoria_por_ic: bool = True
    beta_desgaste_rapido: float = 4.0
    confianza_baja_desde: int = 3
    confianza_media_desde: int = 6
    confianza_alta_desde: int = 20
    bootstrap_replicas: int = 2000
    semilla: int = 20261015
    comparar_distribuciones: bool = True


@dataclass
class AjusteWeibull:
    metodo: str  # WEIBAYES | RRX | MLE | MLE_RBA | NINGUNO
    beta: float | None
    eta: float | None
    gamma: float = 0.0
    beta_ic: tuple[float, float] | None = None
    eta_ic: tuple[float, float] | None = None
    metodo_ic: str = "NINGUNO"  # LR | BOOTSTRAP | CHI2 | NINGUNO
    nivel_ic: float = 0.90
    r2: float | None = None
    r2_critico: float | None = None
    ad: float | None = None
    comparacion: dict[str, dict] | None = None
    n_fallas: int = 0
    n_suspensiones: int = 0
    n_intervalo: int = 0
    confianza: str = "GRIS"
    interpretacion: str | None = None
    version_motor: str = ""
    rangos: list[tuple[float, float, float]] | None = None  # (edad, rango ajustado, F mediana)
    beta_mle_sin_corregir: float | None = None
    advertencias: list[str] = field(default_factory=list)

    @property
    def valido(self) -> bool:
        return self.beta is not None and self.eta is not None


@dataclass
class ResultadoPar:
    """Lo que el motor devuelve para un par componente/modo: el vigente y la alternativa."""

    vigente: AjusteWeibull
    alternativa: AjusteWeibull | None
    hash_datos: str
