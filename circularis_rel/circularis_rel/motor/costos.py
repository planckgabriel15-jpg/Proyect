"""Modelo de costos (Plan §12) con la estructura de la cátedra (UNIDAD 3 y 5).

Cp = P_rep + HH_prev·T_MO                                   (el preventivo se hace en parada programada)
Cf = P_rep + HH_corr·T_MO + max(0; H_parada − A_pulmón)·M_línea + D_sec

Desglose CTMC = CDMC + CLC (UNIDAD 3): CDMC = MODM + CR + CM + CH; CLC = CO + CI + CDRP.
Costo total de mantenimiento CIT = CFJ + CV + CFN + CFA (UNIDAD 5).
"""

from __future__ import annotations

from dataclasses import dataclass


def cp(precio_repuesto: float, hh_preventiva: float, tarifa_mo: float) -> float:
    return precio_repuesto + hh_preventiva * tarifa_mo


def lucro_cesante(horas_parada: float, autonomia_pulmon: float, margen_hora: float) -> float:
    """Si la parada no supera la autonomía del pulmón, no hay lucro cesante (Plan §12)."""
    return max(0.0, horas_parada - (autonomia_pulmon or 0.0)) * margen_hora


def cf(precio_repuesto: float, hh_correctiva: float, tarifa_mo: float, horas_parada: float,
       autonomia_pulmon: float, margen_hora: float, danos_secundarios: float = 0.0) -> float:
    return (precio_repuesto + hh_correctiva * tarifa_mo
            + lucro_cesante(horas_parada, autonomia_pulmon, margen_hora) + danos_secundarios)


@dataclass(frozen=True)
class DesgloseCTMC:
    """Costo total de la política de mantenimiento correctivo (UNIDAD 3)."""

    modm: float  # mano de obra de mantenimiento = HH × tarifa
    cr: float  # repuestos
    cm: float = 0.0  # insumos
    ch: float = 0.0  # herramental
    co: float = 0.0  # costo de oportunidad (lucro cesante)
    ci: float = 0.0  # incumplimiento
    cdrp: float = 0.0  # deterioro de la producción

    @property
    def cdmc(self) -> float:
        return self.modm + self.cr + self.cm + self.ch

    @property
    def clc(self) -> float:
        return self.co + self.ci + self.cdrp

    @property
    def ctmc(self) -> float:
        return self.cdmc + self.clc


def cit(fijos: float, variables: float, financieros: float, por_falla: float) -> float:
    """CIT = CFJ + CV + CFN + CFA (UNIDAD 5)."""
    return fijos + variables + financieros + por_falla


def a_dolares(pesos: float, ars_por_usd: float) -> float:
    return pesos / ars_por_usd
