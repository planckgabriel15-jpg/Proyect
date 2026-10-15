"""Listas cerradas del sistema. Se guardan como texto con CHECK en la base."""

from __future__ import annotations

from enum import StrEnum


class EtapaProceso(StrEnum):
    PREPROCESADO = "PREPROCESADO"
    LAVADO = "LAVADO"
    SECADO = "SECADO"
    FORMULACION = "FORMULACION"
    EXTRUSION = "EXTRUSION"
    ACONDICIONAMIENTO = "ACONDICIONAMIENTO"


class UnidadProduccion(StrEnum):
    KG = "KG"
    FARDOS = "FARDOS"
    DURMIENTES = "DURMIENTES"
    NINGUNA = "NINGUNA"


class ClaseCriticidad(StrEnum):
    A = "A"
    B = "B"
    C = "C"


class MetodoCriticidad(StrEnum):
    TP_6_CRITERIOS = "TP_6_CRITERIOS"
    PONDERACION_U1 = "PONDERACION_U1"


class VariableEdad(StrEnum):
    HORAS = "HORAS"
    TONELADAS = "TONELADAS"


class UsoRepuesto(StrEnum):
    COMUN = "COMUN"
    ESPECIFICO = "ESPECIFICO"


class TipoCatalogo(StrEnum):
    SINTOMA = "SINTOMA"
    MODO = "MODO"
    CAUSA = "CAUSA"


class Categoria6P(StrEnum):
    """Seis grandes pérdidas (UNIDAD 4, diap. 42–45)."""

    AVERIA = "AVERIA"
    PREPARACION_AJUSTE = "PREPARACION_AJUSTE"
    VACIO_PARADAS_CORTAS = "VACIO_PARADAS_CORTAS"
    VELOCIDAD_REDUCIDA = "VELOCIDAD_REDUCIDA"
    CALIDAD_REPROCESO = "CALIDAD_REPROCESO"
    PUESTA_EN_MARCHA = "PUESTA_EN_MARCHA"


class EstadoParte(StrEnum):
    TODO = "TODO"
    PARCIAL = "PARCIAL"
    NO_OPERO = "NO_OPERO"


class NivelHora(StrEnum):
    M = "M"  # medida (horómetro)
    D = "D"  # declarada (parte de turno)
    E = "E"  # estimada (promedio del listado)


class OrigenParte(StrEnum):
    OPERARIO = "OPERARIO"
    ESTIMADO_SISTEMA = "ESTIMADO_SISTEMA"
    IMPORTADO = "IMPORTADO"


class EstadoEvento(StrEnum):
    AVISADO = "AVISADO"
    EN_REPARACION = "EN_REPARACION"
    CERRADO = "CERRADO"
    VALIDADO = "VALIDADO"
    DEVUELTO = "DEVUELTO"
    ANULADO = "ANULADO"


class EfectoFalla(StrEnum):
    PRODUCCION = "PRODUCCION"
    CALIDAD = "CALIDAD"
    SEGURIDAD = "SEGURIDAD"
    AMBIENTE = "AMBIENTE"


class CapacidadFalla(StrEnum):
    TOTAL = "TOTAL"
    PARCIAL = "PARCIAL"


class AparicionFalla(StrEnum):
    REPENTINA = "REPENTINA"
    PROGRESIVA = "PROGRESIVA"


class OrigenEvento(StrEnum):
    AVISO = "AVISO"
    TARJETA_ROJA = "TARJETA_ROJA"
    INSPECCION = "INSPECCION"
    PRUEBA_FUNCIONAL = "PRUEBA_FUNCIONAL"


class TipoOT(StrEnum):
    CORRECTIVA = "CORRECTIVA"
    PREVENTIVA = "PREVENTIVA"
    INSPECCION = "INSPECCION"
    PRUEBA_FUNCIONAL = "PRUEBA_FUNCIONAL"
    AUTONOMO = "AUTONOMO"
    MODIFICATIVO = "MODIFICATIVO"


class EstadoOT(StrEnum):
    SOLICITADA = "SOLICITADA"
    PLANIFICADA = "PLANIFICADA"
    EN_EJECUCION = "EN_EJECUCION"
    CERRADA = "CERRADA"
    VALIDADA = "VALIDADA"


class AccionOT(StrEnum):
    REEMPLAZO = "REEMPLAZO"
    REPARACION_MINIMA = "REPARACION_MINIMA"
    AJUSTE = "AJUSTE"
    INSPECCION_OK = "INSPECCION_OK"
    INSPECCION_FALLA = "INSPECCION_FALLA"


class TipoFin(StrEnum):
    FALLA = "FALLA"
    SUSPENSION_PREVENTIVA = "SUSPENSION_PREVENTIVA"
    SUSPENSION_OTRA = "SUSPENSION_OTRA"
    EN_SERVICIO = "EN_SERVICIO"


class TipoReparacion(StrEnum):
    REEMPLAZO = "REEMPLAZO"
    REPARACION_MINIMA = "REPARACION_MINIMA"


class Moneda(StrEnum):
    ARS = "ARS"
    USD = "USD"


class ColorTarjeta(StrEnum):
    AZUL = "AZUL"
    ROJA = "ROJA"
    VERDE = "VERDE"


class EstadoTarjeta(StrEnum):
    ABIERTA = "ABIERTA"
    RESUELTA = "RESUELTA"
    DERIVADA = "DERIVADA"
    DESCARTADA = "DESCARTADA"


class ClaseTriage(StrEnum):
    A = "A"  # confiable, con respaldo
    B = "B"  # parcial, fecha aproximada -> censura por intervalo
    C = "C"  # no usable -> solo Pareto cualitativo


class Alcance(StrEnum):
    MAQUINA = "MAQUINA"
    FLOTA = "FLOTA"


class ConjuntoDatos(StrEnum):
    NUEVOS = "NUEVOS"
    NUEVOS_MAS_HIST_AB = "NUEVOS_MAS_HIST_AB"


class MetodoWeibull(StrEnum):
    WEIBAYES = "WEIBAYES"
    RRX = "RRX"
    MLE = "MLE"
    MLE_RBA = "MLE_RBA"


class MetodoIC(StrEnum):
    LR = "LR"
    BOOTSTRAP = "BOOTSTRAP"
    NINGUNO = "NINGUNO"


class Confianza(StrEnum):
    GRIS = "GRIS"
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class Interpretacion(StrEnum):
    MORTALIDAD_INFANTIL = "MORTALIDAD_INFANTIL"
    ALEATORIA = "ALEATORIA"
    DESGASTE = "DESGASTE"
    DESGASTE_RAPIDO = "DESGASTE_RAPIDO"


class Semaforo(StrEnum):
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    ROJO = "ROJO"
    GRIS = "GRIS"


class FuenteIntervalo(StrEnum):
    FABRICANTE = "FABRICANTE"
    CALCULADO = "CALCULADO"
    NINGUNO = "NINGUNO"


class ReglaPlan(StrEnum):
    OPTIMO_COSTO = "OPTIMO_COSTO"
    CONFIABILIDAD_OBJETIVO = "CONFIABILIDAD_OBJETIVO"
    PF = "PF"
    FABRICANTE = "FABRICANTE"
    PRUEBA_FUNCIONAL = "PRUEBA_FUNCIONAL"
    NINGUNO = "NINGUNO"


class TipoAnalisis(StrEnum):
    CINCO_PORQUES = "CINCO_PORQUES"
    ISHIKAWA_5M = "ISHIKAWA_5M"
    CINCO_W_1H = "CINCO_W_1H"
    HOJA_VERIFICACION = "HOJA_VERIFICACION"


class EstadoPDCA(StrEnum):
    PLANIFICAR = "PLANIFICAR"
    HACER = "HACER"
    CHEQUEAR = "CHEQUEAR"
    ACTUAR = "ACTUAR"
    CERRADO = "CERRADO"


class OrigenAnalisis(StrEnum):
    MANUAL = "MANUAL"
    SUGERIDO_PARETO = "SUGERIDO_PARETO"
    SUGERIDO_BETA = "SUGERIDO_BETA"
    SUGERIDO_REPETICION = "SUGERIDO_REPETICION"


class Rol(StrEnum):
    OPERARIO = "OPERARIO"
    ENCARGADO = "ENCARGADO"
    JEFE = "JEFE"
    GERENCIA = "GERENCIA"


class AccionAuditoria(StrEnum):
    ALTA = "ALTA"
    MODIFICACION = "MODIFICACION"
    BAJA = "BAJA"
    VALIDACION = "VALIDACION"
    DEVOLUCION = "DEVOLUCION"
    FORZADO_METODO = "FORZADO_METODO"
    IMPORTACION = "IMPORTACION"
    REVISION = "REVISION"
    LOGIN_FALLIDO = "LOGIN_FALLIDO"


class EstadoEtapa(StrEnum):
    PENDIENTE = "PENDIENTE"
    EN_CURSO = "EN_CURSO"
    HECHA = "HECHA"


class TipoParametro(StrEnum):
    ENTERO = "ENTERO"
    REAL = "REAL"
    TEXTO = "TEXTO"
    BOOL = "BOOL"
    JSON = "JSON"


class OrigenDato(StrEnum):
    """De dónde viene un dato de catálogo o del AMFE."""

    JEFE = "JEFE"
    PROPUESTA = "PROPUESTA"  # propuesta inicial del sistema: revisar con el jefe
    TP1_ILUSTRATIVO = "TP1_ILUSTRATIVO"  # tomado del TP N.º 1 (datos ilustrativos): revisar
    IMPORTACION = "IMPORTACION"
    DEMO = "DEMO"
