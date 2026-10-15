"""Matriz de permisos (Plan §2, PLAN_TECNICO §8.1). Cada servicio la verifica: ocultar una
página no alcanza."""

from __future__ import annotations

from enum import StrEnum

from circularis_rel.datos.enums import Rol


class Accion(StrEnum):
    CARGAR_PARTE = "CARGAR_PARTE"
    CREAR_AVISO = "CREAR_AVISO"
    CREAR_TARJETA = "CREAR_TARJETA"
    CERRAR_OT = "CERRAR_OT"
    GESTIONAR_REPUESTOS = "GESTIONAR_REPUESTOS"
    VALIDAR_EVENTO = "VALIDAR_EVENTO"
    CORREGIR_VALIDADO = "CORREGIR_VALIDADO"
    CONFIGURAR = "CONFIGURAR"  # umbrales, métodos, costos, catálogos, usuarios, importación
    VER_FICHA = "VER_FICHA"
    VER_COSTOS = "VER_COSTOS"
    VER_PANEL_GERENCIAL = "VER_PANEL_GERENCIAL"
    EXPORTAR = "EXPORTAR"
    PUESTA_EN_MARCHA = "PUESTA_EN_MARCHA"
    REVISAR_CARGA = "REVISAR_CARGA"
    CARGAR_ANALISIS = "CARGAR_ANALISIS"
    VER_TABLERO = "VER_TABLERO"


_O, _E, _J, _G = Rol.OPERARIO, Rol.ENCARGADO, Rol.JEFE, Rol.GERENCIA

MATRIZ: dict[Accion, frozenset[Rol]] = {
    Accion.CARGAR_PARTE: frozenset({_O, _E, _J}),  # operario: solo sus máquinas
    Accion.CREAR_AVISO: frozenset({_O, _E, _J}),  # operario: solo sus máquinas
    Accion.CREAR_TARJETA: frozenset({_O, _E, _J}),
    Accion.CERRAR_OT: frozenset({_E, _J}),
    Accion.GESTIONAR_REPUESTOS: frozenset({_E, _J}),
    Accion.VALIDAR_EVENTO: frozenset({_J}),
    Accion.CORREGIR_VALIDADO: frozenset({_J}),  # con motivo y auditoría
    Accion.CONFIGURAR: frozenset({_J}),
    Accion.VER_FICHA: frozenset({_O, _E, _J, _G}),  # operario: sin costos
    Accion.VER_COSTOS: frozenset({_J, _G}),
    Accion.VER_PANEL_GERENCIAL: frozenset({_J, _G}),
    Accion.EXPORTAR: frozenset({_E, _J, _G}),
    Accion.PUESTA_EN_MARCHA: frozenset({_J}),
    Accion.REVISAR_CARGA: frozenset({_J}),
    Accion.CARGAR_ANALISIS: frozenset({_E, _J}),
    Accion.VER_TABLERO: frozenset({_J, _G}),
}

# Acciones que el operario solo puede hacer sobre las máquinas asignadas.
RESTRINGIDAS_A_SUS_MAQUINAS = frozenset({Accion.CARGAR_PARTE, Accion.CREAR_AVISO, Accion.CREAR_TARJETA})


class PermisoDenegado(PermissionError):
    pass


def puede(rol: Rol | str, accion: Accion, *, maquina_asignada: bool | None = None) -> bool:
    rol = Rol(rol)
    if rol not in MATRIZ[accion]:
        return False
    return not (rol == Rol.OPERARIO and accion in RESTRINGIDAS_A_SUS_MAQUINAS and maquina_asignada is False)


def requerir(rol: Rol | str, accion: Accion, *, maquina_asignada: bool | None = None) -> None:
    if not puede(rol, accion, maquina_asignada=maquina_asignada):
        raise PermisoDenegado(f"El rol {Rol(rol).value} no puede {accion.value.lower().replace('_', ' ')}")
