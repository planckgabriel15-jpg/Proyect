"""Formato de las planillas de importación (P-05). Una sola definición para generar las
plantillas vacías, leerlas y documentarlas (`docs/plantillas/FORMATO.md`).

Convenciones del libro:
- Fila 1: encabezados (no se cambian). Fila 2: ayuda (se ignora al leer). Datos desde la fila 3.
- Las columnas con asterisco en la ayuda son obligatorias.
- La clave natural es el código: re-importar actualiza y no duplica.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from circularis_rel.datos.enums import (
    ClaseTriage,
    EtapaProceso,
    MetodoCriticidad,
    Moneda,
    OrigenDato,
    TipoFin,
    UnidadProduccion,
    UsoRepuesto,
    VariableEdad,
)

SI_NO = ("SI", "NO")


@dataclass(frozen=True)
class Columna:
    nombre: str
    tipo: str  # texto | entero | real | fecha | hora | bool | lista | codigos
    obligatoria: bool = False
    ayuda: str = ""
    opciones: tuple[str, ...] = ()
    minimo: float | None = None
    maximo: float | None = None


@dataclass(frozen=True)
class Hoja:
    nombre: str
    descripcion: str
    columnas: tuple[Columna, ...] = field(default_factory=tuple)

    def columna(self, nombre: str) -> Columna:
        return next(c for c in self.columnas if c.nombre == nombre)


def _op(enum_cls) -> tuple[str, ...]:
    return tuple(m.value for m in enum_cls)


C = Columna

HOJAS_CARGA_INICIAL: tuple[Hoja, ...] = (
    Hoja("lineas", "Líneas de producción.", (
        C("codigo", "texto", True, "Código único, p. ej. TWOOD"),
        C("nombre", "texto", True, "Nombre de la línea"),
    )),
    Hoja("turnos", "Turnos de trabajo.", (
        C("codigo", "texto", True, "Código único, p. ej. M"),
        C("nombre", "texto", True, "Mañana, Tarde…"),
        C("hora_inicio", "hora", True, "HH:MM"),
        C("hora_fin", "hora", True, "HH:MM"),
        C("duracion_h", "real", True, "Horas del turno", minimo=0.5, maximo=24),
    )),
    Hoja("tipos_componente", "Tipos de componente, en lenguaje de planta.", (
        C("codigo", "texto", True, "Código único, p. ej. CUCHILLAS"),
        C("nombre", "texto", True, "Cuchillas, criba, rulemanes…"),
        C("variable_edad", "lista", False, "Cómo se mide la edad (por defecto HORAS)", _op(VariableEdad)),
        C("hh_preventiva", "real", False, "Horas-hombre de un cambio preventivo", minimo=0),
        C("hh_correctiva", "real", False, "Horas-hombre de una reparación correctiva", minimo=0),
        C("beta_ref", "real", False, "β de referencia (opcional, exige fuente_ref)", minimo=0.01),
        C("eta_ref", "real", False, "η de referencia (opcional)", minimo=0.01),
        C("fuente_ref", "texto", False, "De dónde sale el β de referencia"),
        C("uso", "lista", False, "Uso común o específico", _op(UsoRepuesto)),
        C("intervalo_fabricante", "real", False, "Intervalo de cambio recomendado por el fabricante", minimo=0),
        C("unidad_intervalo_fabricante", "lista", False, "Unidad del intervalo del fabricante", _op(VariableEdad)),
        C("falla_oculta", "bool", False, "SI si es de seguridad o respaldo (válvula de seguridad, detector, UPS…)", SI_NO),
        C("funcion_seguridad", "bool", False, "SI si protege a personas o a la planta", SI_NO),
        C("intervalo_pf", "real", False, "Intervalo P-F conocido (misma unidad que la edad)", minimo=0),
        C("origen", "lista", False, "JEFE si lo cargó el jefe; TP1_ILUSTRATIVO si viene del TP", _op(OrigenDato)),
    )),
    Hoja("maquinas", "Máquinas con su catastro (UNIDAD 6, MANT/RHM001).", (
        C("codigo", "texto", True, "Código del QR, p. ej. AGR-001"),
        C("nombre", "texto", True, "Nombre de la máquina"),
        C("linea", "texto", True, "Código de la línea"),
        C("etapa_proceso", "lista", True, "Etapa del proceso", _op(EtapaProceso)),
        C("orden_proceso", "entero", False, "Orden en el esquema de la línea", minimo=0),
        C("ubicacion", "texto", False, "Sector de la planta"),
        C("funcion", "texto", False, "Qué hace la máquina"),
        C("horas_promedio_dia", "real", False, "Horas de operación promedio por día", minimo=0, maximo=24),
        C("unidad_produccion", "lista", False, "Unidad de la cantidad procesada", _op(UnidadProduccion)),
        C("factor_toneladas", "real", False, "Toneladas por unidad (para la edad en toneladas)", minimo=0),
        C("autonomia_pulmon_h", "real", False, "Horas que la línea aguanta con esta máquina parada", minimo=0),
        C("ciclo_teorico_s", "real", False, "Tiempo de ciclo teórico en segundos (para RO/OEE)", minimo=0),
        C("numero_serie", "texto"), C("fabricante", "texto"), C("modelo", "texto"), C("proveedor", "texto"),
        C("fecha_instalacion", "fecha", False, "DD/MM/AAAA"),
        C("ancho_mm", "real", minimo=0), C("alto_mm", "real", minimo=0), C("largo_mm", "real", minimo=0),
        C("peso_kg", "real", minimo=0),
        C("condiciones_almacenamiento", "texto"), C("caracteristicas_tecnicas", "texto"),
        C("ruta_documentos", "texto", False, "Carpeta con planos, manuales y catálogos"),
    )),
    Hoja("maquina_turnos", "Qué turnos trabaja cada máquina.", (
        C("maquina", "texto", True, "Código de la máquina"),
        C("turno", "texto", True, "Código del turno"),
        C("dias", "texto", False, "Días de la semana (1=lunes … 7=domingo), p. ej. 1,2,3,4,5"),
    )),
    Hoja("posiciones", "Posiciones de componente en cada máquina.", (
        C("maquina", "texto", True, "Código de la máquina"),
        C("codigo", "texto", True, "Código de la posición dentro de la máquina, p. ej. CUCH"),
        C("tipo_componente", "texto", True, "Código del tipo de componente"),
        C("ubicacion", "texto", False, "Dónde está en la máquina"),
        C("cantidad", "entero", False, "Cantidad por máquina (por defecto 1)", minimo=1),
        C("critica", "bool", False, "SI si su estado define el color de la máquina", SI_NO),
    )),
    Hoja("sintomas", "Síntomas del aviso de falla.", (
        C("codigo", "texto", True), C("descripcion", "texto", True), C("icono", "texto", False, "Emoji opcional"),
    )),
    Hoja("modos", "Modos de falla (lista cerrada por tipo de componente).", (
        C("codigo", "texto", True),
        C("descripcion", "texto", True),
        C("tipos_componente", "codigos", True, "Códigos de tipo de componente separados por coma"),
        C("origen", "lista", False, "JEFE o TP1_ILUSTRATIVO", _op(OrigenDato)),
    )),
    Hoja("causas", "Causas de falla.", (
        C("codigo", "texto", True),
        C("descripcion", "texto", True),
        C("tipos_componente", "codigos", False, "Vacío = aplica a todos"),
        C("origen", "lista", False, "JEFE o TP1_ILUSTRATIVO", _op(OrigenDato)),
    )),
    Hoja("repuestos", "Repuestos (UNIDAD 6, MANT/RM001).", (
        C("codigo", "texto", True), C("descripcion", "texto", True),
        C("tipo_componente", "texto", False, "Código del tipo de componente que reemplaza"),
        C("uso", "lista", False, "", _op(UsoRepuesto)),
        C("stock_actual", "real", minimo=0), C("stock_minimo", "real", minimo=0),
        C("ubicacion", "texto"), C("codigo_proveedor", "texto"), C("proveedor", "texto"),
        C("lead_time_dias", "real", minimo=0), C("familia_compra", "texto"),
        C("intervalo_fabricante", "real", minimo=0),
        C("precio", "real", False, "Precio unitario (exige fecha_precio)", minimo=0),
        C("moneda", "lista", False, "ARS por defecto", _op(Moneda)),
        C("fecha_precio", "fecha", False, "DD/MM/AAAA"),
    )),
    Hoja("repuestos_por_maquina", "Qué repuestos usa cada máquina.", (
        C("maquina", "texto", True), C("repuesto", "texto", True),
        C("cantidad_instalada", "real", minimo=0),
    )),
    Hoja("criticidad", "Criticidad por máquina (método del TP: escalas del TP N.º 1).", (
        C("maquina", "texto", True),
        C("metodo", "lista", False, "Por defecto TP_6_CRITERIOS", _op(MetodoCriticidad)),
        C("uso", "entero", True, "5 / 3 / 1"),
        C("alternativa", "entero", True, "5 / 4 / 2 / 1"),
        C("influencia", "entero", True, "5 / 4 / 2 / 1"),
        C("calidad", "entero", True, "5 / 4 / 2 / 1"),
        C("ambiente", "entero", True, "5 / 3 / 1"),
        C("seguridad", "entero", True, "5 / 3 / 1"),
        C("clase", "lista", False, "Vacío = la calcula el sistema", ("A", "B", "C")),
        C("fecha", "fecha", False, "Fecha de la evaluación"),
    )),
    Hoja("amfe", "AMFE por máquina y componente.", (
        C("maquina", "texto", False, "Código de la máquina (vacío = vale para todas)"),
        C("tipo_componente", "texto", True), C("modo", "texto", True, "Código del modo de falla"),
        C("requerimiento", "texto"), C("efecto", "texto"), C("causa", "texto"),
        C("control_prevencion", "texto"), C("control_deteccion", "texto"),
        C("g", "entero", True, "Gravedad 1–10", minimo=1, maximo=10),
        C("o", "entero", True, "Ocurrencia 1–10", minimo=1, maximo=10),
        C("d", "entero", True, "Detección 1–10", minimo=1, maximo=10),
        C("acciones", "texto"), C("responsable", "texto"),
        C("origen", "lista", False, "JEFE o TP1_ILUSTRATIVO", _op(OrigenDato)),
    )),
    Hoja("parametros_costos", "Parámetros de costos con fecha de vigencia.", (
        C("clave", "lista", True, "Parámetro", ("costos.tarifa_mo_ars_h", "costos.margen_linea_ars_h", "costos.horas_parada_defecto_h")),
        C("valor", "real", True, "", minimo=0),
        C("vigente_desde", "fecha", True, "DD/MM/AAAA"),
    )),
    Hoja("tipos_cambio", "Tipo de cambio por fecha.", (
        C("fecha", "fecha", True, "DD/MM/AAAA"),
        C("ars_por_usd", "real", True, "Pesos por dólar", minimo=0.0001),
        C("fuente", "texto"),
    )),
)

HOJA_HISTORICO = Hoja("historico", "Histórico de cambios y fallas, clasificado por triage A/B/C (Plan §11).", (
    C("maquina", "texto", True),
    C("posicion", "texto", False, "Código de la posición (vacío = componente no identificado → clase C)"),
    C("tipo_fin", "lista", True, "Cómo terminó la vida", tuple(t for t in _op(TipoFin) if t != "EN_SERVICIO")),
    C("modo", "texto", False, "Código del modo de falla (obligatorio para FALLA de clase A)"),
    C("fecha_instalacion", "fecha", False, "DD/MM/AAAA"),
    C("fecha_fin", "fecha", False, "Fecha real del cambio o falla"),
    C("fecha_fin_desde", "fecha", False, "Si la fecha es aproximada: desde"),
    C("fecha_fin_hasta", "fecha", False, "Si la fecha es aproximada: hasta"),
    C("edad_horas", "real", False, "Horas operadas, si se conocen", minimo=0),
    C("edad_desde_h", "real", False, "Si la edad es aproximada: desde", minimo=0),
    C("edad_hasta_h", "real", False, "Si la edad es aproximada: hasta", minimo=0),
    C("clase", "lista", False, "A, B o C. Vacío = la propone el sistema", _op(ClaseTriage)),
    C("fuente", "texto", True, "OT, factura, parte, memoria del encargado…"),
    C("respaldo", "texto", False, "N.º de OT, factura o parte (obligatorio para clase A)"),
    C("descripcion_original", "texto", False, "Texto tal como figura en el registro original"),
    C("observaciones", "texto"),
))

ORDEN_CARGA = tuple(h.nombre for h in HOJAS_CARGA_INICIAL)
