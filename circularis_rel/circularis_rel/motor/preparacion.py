"""Preparación de datos (Plan §3 y §5): arma la población de un par componente/modo.

- FALLA del modo analizado → falla ("F").
- FALLA de otro modo → suspensión ("S") para el modo analizado (riesgos competitivos).
- SUSPENSION_PREVENTIVA / SUSPENSION_OTRA → suspensión.
- EN_SERVICIO → suspensión con la edad actual (Plan §3; D-002). Puede marcarse "solo pronóstico".
- Solo entran vidas validadas (las en servicio siempre son el estado actual).
- Edad desconocida (componente instalado antes del sistema): se excluye por defecto (D-028).
- Histórico clase A: vida con horas nivel E. Clase B: censura por intervalo (solo MLE).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from circularis_rel.motor.tipos import Observacion


@dataclass(frozen=True)
class VidaDatos:
    edad: float | None
    tipo_fin: str  # FALLA | SUSPENSION_PREVENTIVA | SUSPENSION_OTRA | EN_SERVICIO
    id_modo: int | None = None
    edad_conocida: bool = True
    validado: bool = True
    nivel_hora: str = "D"
    edad_inf: float | None = None  # histórico B: la falla ocurrió entre edad_inf y edad
    origen: str = "NUEVA"  # NUEVA | HIST_A | HIST_B
    reparacion_minima: bool = False  # la vida empezó con una reparación mínima (no "como nuevo")
    etiqueta: str | None = None


@dataclass
class Resumen:
    n_fallas: int = 0
    n_suspensiones: int = 0
    n_intervalo: int = 0
    n_estimadas: int = 0  # observaciones con horas nivel E
    excluidas: dict[str, int] = field(default_factory=dict)

    def excluir(self, motivo: str) -> None:
        self.excluidas[motivo] = self.excluidas.get(motivo, 0) + 1


def armar_poblacion(vidas: list[VidaDatos], id_modo: int, *, incluir_en_servicio: bool = True,
                    en_servicio_solo_pronostico: bool = False, incluir_no_validadas: bool = False,
                    excluir_reparacion_minima: bool = False) -> tuple[list[Observacion], Resumen]:
    obs: list[Observacion] = []
    r = Resumen()
    for v in vidas:
        if v.tipo_fin != "EN_SERVICIO" and not v.validado and not incluir_no_validadas:
            r.excluir("sin validar")
            continue
        if not v.edad_conocida:
            r.excluir("edad desconocida (instalado antes del sistema)")
            continue
        if v.edad is None:
            r.excluir("sin edad")
            continue
        if excluir_reparacion_minima and v.reparacion_minima:
            r.excluir("vida tras reparación mínima")
            continue
        nivel = "E" if v.origen in ("HIST_A", "HIST_B") else v.nivel_hora
        if v.tipo_fin == "EN_SERVICIO":
            if not incluir_en_servicio:
                r.excluir("en servicio (excluida por opción)")
                continue
            if v.edad <= 0:
                r.excluir("en servicio con edad 0")
                continue
            o = Observacion(v.edad, "S", nivel_hora=nivel, solo_pronostico=en_servicio_solo_pronostico, etiqueta=v.etiqueta)
        elif v.tipo_fin == "FALLA" and v.id_modo == id_modo:
            if v.edad_inf is not None:
                o = Observacion(v.edad, "I", edad_inf=v.edad_inf, nivel_hora=nivel, etiqueta=v.etiqueta)
            elif v.edad <= 0:
                r.excluir("falla con edad 0 (revisar la carga)")
                continue
            else:
                o = Observacion(v.edad, "F", nivel_hora=nivel, etiqueta=v.etiqueta)
        else:  # falla de otro modo o suspensión
            edad = v.edad_inf if v.edad_inf is not None else v.edad  # con intervalo, la parte segura
            if edad <= 0:
                r.excluir("suspensión con edad 0")
                continue
            o = Observacion(edad, "S", nivel_hora=nivel, etiqueta=v.etiqueta)
        obs.append(o)
        if not o.solo_pronostico:
            r.n_fallas += o.estado == "F"
            r.n_suspensiones += o.estado == "S"
            r.n_intervalo += o.estado == "I"
            r.n_estimadas += o.nivel_hora == "E"
    return obs, r
