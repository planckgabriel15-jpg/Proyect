"""Datos iniciales del sistema (no son datos de la planta).

Todo lo que se siembra acá es configuración o catálogo genérico, con su fuente. Los datos
de la planta (máquinas, componentes, precios, tarifas) entran por el importador.
`sembrar()` es idempotente: agrega lo que falta y no pisa lo que el jefe ya editó.
"""

from __future__ import annotations

import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from circularis_rel.datos.enums import (
    Categoria6P,
    OrigenDato,
    TipoCatalogo,
    TipoParametro,
)
from circularis_rel.datos.modelos import (
    Catalogo,
    EtapaImplementacion,
    IndicadorObjetivo,
    ModuloHabilitado,
    MotivoParada,
    Parametro,
    TipoCambio,
)

FECHA_BASE = date(2026, 10, 1)

# (clave, valor, tipo, unidad, grupo, descripción, fuente). valor None = "falta dato".
PARAMETROS: list[tuple] = [
    # Semáforo (Plan §7; D-012)
    ("semaforo.p_amarillo", 0.10, "REAL", "prob.", "semaforo", "P(falla en Δ) desde la que el componente pasa a amarillo", "Plan §7"),
    ("semaforo.p_rojo", 0.30, "REAL", "prob.", "semaforo", "P(falla en Δ) desde la que el componente pasa a rojo", "Plan §7"),
    ("semaforo.p_amarillo_clase_a", 0.05, "REAL", "prob.", "semaforo", "Umbral amarillo para máquinas de criticidad A", "Propuesta D-012, revisar en el piloto"),
    ("semaforo.p_rojo_clase_a", 0.20, "REAL", "prob.", "semaforo", "Umbral rojo para máquinas de criticidad A", "Propuesta D-012, revisar en el piloto"),
    ("semaforo.fraccion_intervalo_amarillo", 0.80, "REAL", "fracción", "semaforo", "Edad sobre intervalo recomendado que pasa a amarillo", "Plan §7"),
    ("semaforo.horizonte_dias_defecto", 14, "ENTERO", "días", "semaforo", "Horizonte Δ si no hay próxima parada programada cargada", "Plan §7 (ej. 2 semanas)"),
    ("semaforo.proxima_parada", None, "TEXTO", "fecha", "semaforo", "Fecha de la próxima parada programada (AAAA-MM-DD)", "Cargar por el jefe"),
    # Motor (Plan §5; D-005, D-006)
    ("motor.nivel_ic", 0.90, "REAL", "fracción", "motor", "Nivel de los intervalos de confianza (bilateral)", "Plan §5"),
    ("motor.min_fallas_rrx", 3, "ENTERO", "fallas", "motor", "Fallas mínimas para ajustar por RRX", "Plan §5"),
    ("motor.min_fallas_mle", 20, "ENTERO", "fallas", "motor", "Fallas desde las que el método vigente es MLE", "Plan §5"),
    ("motor.max_frac_suspensiones_rrx", 0.50, "REAL", "fracción", "motor", "Fracción de suspensiones por encima de la cual se usa MLE", "Plan §5"),
    ("motor.n_max_rba", 30, "ENTERO", "fallas", "motor", "Se aplica la corrección RBA si las fallas son menos que esto", "Plan §5"),
    ("motor.beta_aleatoria_min", 0.9, "REAL", "", "motor", "Límite inferior de la banda 'β ≈ 1'", "D-006"),
    ("motor.beta_aleatoria_max", 1.1, "REAL", "", "motor", "Límite superior de la banda 'β ≈ 1'", "D-006"),
    ("motor.beta_aleatoria_por_ic", True, "BOOL", "", "motor", "Leer 'aleatoria' también si el IC de β contiene a 1", "D-006"),
    ("motor.beta_desgaste_rapido", 4.0, "REAL", "", "motor", "β desde el que se lee desgaste rápido", "Plan §5"),
    ("motor.min_fallas_3p", 20, "ENTERO", "fallas", "motor", "Fallas mínimas para habilitar Weibull 3P", "Plan §5"),
    ("motor.flota_p_valor", 0.05, "REAL", "", "motor", "p-valor mínimo de la prueba de razón de verosimilitud para agrupar flota", "PLAN_TECNICO §7.6"),
    ("motor.bootstrap_replicas", 2000, "ENTERO", "", "motor", "Réplicas del bootstrap paramétrico de RRX", "PLAN_TECNICO §7.2"),
    ("motor.confianza_baja_desde", 3, "ENTERO", "fallas", "motor", "Fallas desde las que la confianza es BAJA", "Plan §5 (tabla); P-08"),
    ("motor.confianza_media_desde", 6, "ENTERO", "fallas", "motor", "Fallas desde las que la confianza es MEDIA", "Plan §5 (tabla); P-08"),
    ("motor.confianza_alta_desde", 20, "ENTERO", "fallas", "motor", "Fallas desde las que la confianza es ALTA", "Plan §5 (tabla)"),
    # Políticas (Plan §8)
    ("politicas.cf_cp_minimo", 2.0, "REAL", "", "politicas", "Cf/Cp mínimo para recomendar intervalo óptimo por costo", "Plan §8"),
    ("politicas.r_objetivo", 0.90, "REAL", "", "politicas", "Confiabilidad objetivo R* para seguridad o criticidad A", "Plan §8"),
    ("politicas.paso_redondeo_h", 25, "REAL", "h", "politicas", "Paso para redondear el intervalo óptimo", "Propuesta (Plan §15: 369 h → 375 h)"),
    ("politicas.anticipacion_ot_dias", 7, "ENTERO", "días", "politicas", "Anticipación con que se generan las OT preventivas", "Propuesta, configurable"),
    ("politicas.nivel_servicio_stock", 0.95, "REAL", "", "politicas", "Nivel de servicio para el stock mínimo (Poisson)", "Plan §8"),
    # Costos (Plan §12): sin valores inventados
    ("costos.tarifa_mo_ars_h", None, "REAL", "ARS/h", "costos", "Tarifa horaria de mano de obra (CCT 260/75 Rama 17)", "Cargar desde el TP N.º 2"),
    ("costos.margen_linea_ars_h", None, "REAL", "ARS/h", "costos", "Margen por hora de la línea (base del lucro cesante)", "Cargar desde el TP N.º 2"),
    ("costos.horas_parada_defecto_h", None, "REAL", "h", "costos", "Horas de parada por defecto cuando un modo no tiene historia", "Cargar por el jefe"),
    # Validación (Plan §11)
    ("validacion.eventos_sin_validar_h", 48, "ENTERO", "h", "validacion", "Horas sin validar para alertar al jefe", "Plan §7"),
    ("validacion.duplicado_aviso_min", 30, "ENTERO", "min", "validacion", "Minutos para considerar un aviso duplicado", "Plan §11"),
    ("validacion.factor_reparacion_atipica", 3.0, "REAL", "×MTTR", "validacion", "Reparación atípica si supera este múltiplo del MTTR del modo", "Plan §11"),
    ("validacion.vida_atipica_min_frac_eta", 0.05, "REAL", "×η", "validacion", "Vida atípica si es menor que esta fracción de η", "Plan §11"),
    ("validacion.vida_atipica_max_mult_eta", 3.0, "REAL", "×η", "validacion", "Vida atípica si supera este múltiplo de η", "Plan §11"),
    ("partes.dias_para_estimar", 2, "ENTERO", "días", "validacion", "Días sin parte tras el aviso para completarlo como estimado (nivel E)", "Propuesta (Plan §4: 'si sigue faltando')"),
    # Asistente (12.D)
    ("rca.repeticiones_n", 3, "ENTERO", "eventos", "asistente", "Repeticiones de un par componente/modo que sugieren análisis de causa raíz", "Propuesta, configurable"),
    ("rca.repeticiones_dias", 90, "ENTERO", "días", "asistente", "Ventana de días para contar repeticiones", "Propuesta, configurable"),
    ("rca.top_pareto", 3, "ENTERO", "pares", "asistente", "Cantidad de pares del Pareto que sugieren análisis", "Propuesta, configurable"),
    ("pareto.corte", 0.80, "REAL", "fracción", "asistente", "Línea de corte del Pareto", "Regla 80/20"),
    # Criticidad (12.C; D-020)
    ("criticidad.tp_cortes", {"Alta": 25, "Media": 20, "Baja": 15}, "JSON", "puntos", "criticidad",
     "Cortes del puntaje total (suma de 6 criterios) del TP N.º 1: ≥25 Alta, 20–24 Media, 15–19 Baja, <15 Muy baja", "TP N.º 1, análisis de prioridad"),
    ("criticidad.tp_nivel_a_clase", {"Alta": "A", "Media": "B", "Baja": "C", "Muy baja": "C"}, "JSON", "", "criticidad",
     "Equivalencia entre el nivel del TP y la clase A/B/C del sistema", "Propuesta D-020"),
    ("criticidad.pesos_plan", {"produccion": 0.30, "influencia": 0.20, "calidad": 0.15, "seguridad": 0.15, "ambiente": 0.10, "sustitucion": 0.10},
     "JSON", "", "criticidad", "Pesos de los seis criterios según el Plan §8 (variante ponderada)", "Plan §8"),
    # Sistema
    ("backup.retencion_diaria", 30, "ENTERO", "copias", "sistema", "Backups diarios que se conservan", "PLAN_TECNICO §3.8"),
    ("backup.retencion_mensual", 12, "ENTERO", "copias", "sistema", "Backups mensuales que se conservan", "PLAN_TECNICO §3.8"),
    ("backup.carpeta_externa", None, "TEXTO", "ruta", "sistema", "Disco externo o carpeta sincronizada con Google Drive", "Cargar en la instalación"),
    # Predictivo (12.G): referencia de la UNIDAD 3, editable
    ("predictivo.ultrasonido_rodamientos_db",
     [{"desde_db": 8, "hasta_db": 10, "estado": "Pre-falla o falta de lubricación", "accion": "Lubricar y retomar las lecturas"},
      {"desde_db": 10, "hasta_db": 12, "estado": "Primeros síntomas o comienzo de la falla", "accion": "Vigilar en el tiempo"},
      {"desde_db": 16, "hasta_db": None, "estado": "Falla", "accion": "Programar su reemplazo (próximo período conveniente)"},
      {"desde_db": 35, "hasta_db": 50, "estado": "Falla catastrófica", "accion": "Remover y reemplazar de inmediato"}],
     "JSON", "dB sobre la referencia", "predictivo", "Valores de referencia del ultrasonido en rodamientos (no es norma)", "UNIDAD 3, análisis de rodamientos"),
]

# Plan §10: síntomas del aviso con íconos. "Fuga" agregado como propuesta (equipos hidráulicos).
SINTOMAS = [
    ("RUIDO", "Ruido", "🔊"),
    ("VIBRACION", "Vibración", "📳"),
    ("TEMPERATURA", "Temperatura alta", "🌡️"),
    ("NO_ARRANCA", "No arranca", "⛔"),
    ("ROTURA_VISIBLE", "Rotura visible", "💥"),
    ("FUGA", "Fuga (aceite, agua, aire)", "💧"),
    ("OTRO", "Otro", "❓"),
]

# Causas genéricas: propuesta a partir del Plan §5 (causas típicas) y del AMFE del TP N.º 1.
# Aplican a todos los tipos de componente salvo que el jefe las restrinja.
CAUSAS = [
    ("DESGASTE", "Desgaste o abrasión"),
    ("FATIGA", "Fatiga (térmica, por carga cíclica o por impacto)"),
    ("LUBRICACION", "Falta de lubricación o lubricación deficiente"),
    ("CONTAMINACION", "Suciedad, polvo o contaminación"),
    ("SOBRECARGA", "Sobrecarga"),
    ("VENTILACION", "Sobrecalentamiento por ventilación deficiente"),
    ("IMPACTO", "Impacto de material duro o cuerpo extraño"),
    ("TORQUE", "Tornillería sin torque o aflojamiento"),
    ("DESALINEACION", "Desalineación o vibración excesiva"),
    ("CORROSION", "Corrosión o humedad"),
    ("ELECTRICA", "Sobretensión o sobrecorriente"),
    ("ENVEJECIMIENTO", "Envejecimiento"),
    ("MONTAJE", "Montaje incorrecto"),
    ("CALIDAD_REPUESTO", "Calidad del repuesto"),
    ("OPERACION", "Error de operación"),
    ("TENSION_CORREA", "Tensión incorrecta de correa"),
    ("CAVITACION", "Cavitación"),
    ("DESCONOCIDA", "Desconocida"),
]

# Motivos del parte de turno (Plan §4) ampliados con las seis grandes pérdidas (12.F; D-007).
# (código, descripción, cuenta_como_requerida, es_falla, es_setup, categoría 6P, orden)
MOTIVOS = [
    ("FALLA", "Falla", True, True, False, Categoria6P.AVERIA, 1),
    ("FALTA_MATERIAL", "Falta de material", True, False, False, None, 2),
    ("LIMPIEZA", "Limpieza", True, False, False, None, 3),
    ("PREVENTIVO", "Preventivo", True, False, False, None, 4),
    ("PREPARACION", "Preparación o ajuste (cambio de formato)", True, False, True, Categoria6P.PREPARACION_AJUSTE, 5),
    ("PARADAS_CORTAS", "Paradas cortas o espera", True, False, False, Categoria6P.VACIO_PARADAS_CORTAS, 6),
    ("CALIDAD", "Problema de calidad o reproceso", True, False, False, Categoria6P.CALIDAD_REPROCESO, 7),
    ("PUESTA_EN_MARCHA", "Puesta en marcha", True, False, False, Categoria6P.PUESTA_EN_MARCHA, 8),
    ("SIN_DEMANDA", "Sin demanda", False, False, False, None, 9),
    ("HUELGA", "Huelga o paro", False, False, False, None, 10),
    ("OTRO", "Otro", True, False, False, None, 11),
    # Parte faltante completado por el sistema (Plan §4): sin dato no se cuenta como parada (D-029).
    ("SIN_DATO", "Sin dato (parte estimado por el sistema)", False, False, False, None, 99),
]

# 12.A: etapas de la UNIDAD 6 (diap. "Etapas" e "Implementación del control de mantenimiento").
# (número, fase, título, qué es, por qué importa, pantalla, criterio automático)
ETAPAS = [
    (1, 1, "Inventario de equipos", "Lista de los equipos instalados y por instalar, con su aplicación.",
     "Sin inventario no hay a qué asignarle fallas ni horas.", "Configuración › Carga inicial", "hay_activos"),
    (2, 1, "Pantallas de catastro", "Formularios para registrar los datos de cada equipo.",
     "Que todos registren lo mismo de la misma forma.", "Máquinas", "provisto"),
    (3, 1, "Datos catastrales", "Fabricante, modelo, n.º de serie, dimensiones, características y manuales de cada equipo.",
     "Hace falta para pedir repuestos y para el historial de la máquina.", "Máquinas › Ficha", "catastro_completo"),
    (4, 1, "Repuestos por equipo", "Relevamiento de repuestos y su relación con cada equipo (uso común o específico).",
     "Define el stock que hay que tener y qué se comparte entre máquinas.", "Configuración › Carga inicial", "repuestos_cargados"),
    (5, 1, "Terminología única", "Nombres únicos de componentes, modos de falla, causas y síntomas.",
     "Si cada uno llama distinto a la misma falla, no se puede analizar.", "Configuración › Catálogos", "catalogos_cargados"),
    (6, 1, "Clasificación por importancia", "Criticidad A/B/C de cada equipo.",
     "Ordena dónde poner el esfuerzo primero y qué stock tener.", "AMFE y criticidad", "criticidad_completa"),
    (7, 1, "Códigos de equipos", "Código único por máquina (AGR-001, EXT-001…), que va en el QR.",
     "Identificación sin errores desde el celular.", "Máquinas › QR", "codigos_activos"),
    (8, 1, "Códigos de mantenimiento", "Tipos de orden de trabajo: correctiva, preventiva, inspección, etc.",
     "Separa el trabajo planificado del imprevisto.", "Provisto por el sistema", "provisto"),
    (9, 1, "Hojas de registro", "Aviso de falla y cierre de OT.",
     "Es la fuente de los datos de fallas.", "Reportar falla / Cerrar OT", "provisto"),
    (10, 1, "Programa maestro de preventivo", "Qué se hace, cada cuánto y en qué máquina.",
     "Mientras no haya datos se usa la recomendación del fabricante.", "Plan preventivo", "plan_preventivo"),
    (11, 1, "Órdenes de servicio", "Emisión de OT de las actividades programadas.",
     "El sistema las emite solo, sin demoras administrativas.", "Bandeja del encargado", "provisto"),
    (12, 1, "Mano de obra trabajada y disponible", "Horas-hombre disponibles y trabajadas por mes.",
     "Sin esto no hay ratios de mano de obra (TBMP, TBMC, OCPM).", "Tablero de comando", "hh_disponibles"),
    (13, 1, "Datos de operación", "Parte de turno por máquina: horas operadas y paradas.",
     "Reemplaza al horómetro: da la edad de cada componente y la disponibilidad.", "Parte de turno", "partes_cargados"),
    (14, 1, "Códigos de ocurrencias", "Motivos de parada y síntomas de falla.",
     "Separa las paradas por falla de las demás pérdidas.", "Configuración › Catálogos", "motivos_y_sintomas"),
    (15, 2, "Control de correctivos e histórico", "Con la fase 1 estable: registrar todas las fallas, validarlas y armar el archivo histórico.",
     "Es la materia prima de Weibull. Empezar por los equipos prioritarios.", "Bandeja de validación", "eventos_validados"),
    (16, 3, "Control predictivo y alertas", "Con datos suficientes y confiables: intervalos óptimos y alertas por riesgo de falla.",
     "Las alertas firmes se habilitan por componente recién con confianza media o alta.", "Panel de planta", "confianza_media"),
]

DESVENTAJAS_INFORMATIZAR = [
    "Hay que entrenar bien a quien carga los datos: un dato mal cargado arruina el análisis.",
    "Los supervisores tienen que participar más: validar lo que entra y leer los reportes que salen.",
    "Si se altera el proyecto del sistema se puede perder el acervo histórico: por eso hay backup diario y exportación total a Excel.",
    "Al principio cuesta más tiempo y plata que llevarlo a mano; el beneficio llega con los meses de datos.",
]

# P-06: activos por defecto 12.A, 12.B, 12.C, 12.D, tarjetas y ayudas; el resto habilitable.
MODULOS = [
    ("12A", "Puesta en marcha guiada", True),
    ("12B", "Catastro y repuestos por máquina", True),
    ("12C", "Clasificación de equipos y de fallas", True),
    ("12D", "Herramientas de análisis de problemas", True),
    ("12E", "Tablero de comando completo", False),
    ("12F_TJ", "Tarjetas azul/roja/verde", True),
    ("12F", "TPM y OEE completo", False),
    ("12G", "Mantenimiento planeado y predictivo", False),
    ("12H_AY", "Ayuda contextual", True),
    ("12H", "Fiabilidad de sistemas y herramientas didácticas", False),
]

# Referencias orientativas de la UNIDAD 5 (no son metas: objetivo y límites quedan vacíos).
INDICADORES = [
    ("CMFT", False, None), ("CMOE", False, None),
    ("CMPP", False, "Normalmente entre 5 % y 6 % (UNIDAD 5)"),
    ("CMPV", False, "Puede rondar entre 4 % y 5 % (UNIDAD 5)"),
    ("CPCT", True, "Puede oscilar el 20 % (UNIDAD 5)"),
    ("HPHP", False, "Generalmente entre 1 % y 3 % (UNIDAD 5)"),
    ("TBMP", True, None), ("TBMC", False, None), ("TBML", False, None),
    ("OCPM", False, None), ("PETI", True, None), ("CSMP", True, None), ("EFMD", True, None),
]


def _valor_texto(valor, tipo: str) -> str | None:
    if valor is None:
        return None
    if tipo == "JSON":
        return json.dumps(valor, ensure_ascii=False)
    if tipo == "BOOL":
        return "1" if valor else "0"
    return str(valor)


def sembrar(s: Session) -> dict[str, int]:
    """Agrega los datos iniciales que falten. Devuelve cuántos agregó por grupo."""
    agregados = {"parametros": 0, "sintomas": 0, "causas": 0, "motivos": 0, "etapas": 0, "modulos": 0, "indicadores": 0}

    existentes = set(s.scalars(select(Parametro.clave)))
    for clave, valor, tipo, unidad, grupo, desc, fuente in PARAMETROS:
        if clave not in existentes:
            s.add(Parametro(clave=clave, valor=_valor_texto(valor, tipo), tipo=TipoParametro(tipo),
                            unidad=unidad, grupo=grupo, descripcion=desc, fuente=fuente,
                            vigente_desde=FECHA_BASE))
            agregados["parametros"] += 1

    cats = {(c.tipo, c.codigo) for c in s.scalars(select(Catalogo))}
    for codigo, desc, icono in SINTOMAS:
        if (TipoCatalogo.SINTOMA, codigo) not in cats:
            s.add(Catalogo(tipo=TipoCatalogo.SINTOMA, codigo=codigo, descripcion=desc, icono=icono,
                           origen=OrigenDato.PROPUESTA))
            agregados["sintomas"] += 1
    for codigo, desc in CAUSAS:
        if (TipoCatalogo.CAUSA, codigo) not in cats:
            s.add(Catalogo(tipo=TipoCatalogo.CAUSA, codigo=codigo, descripcion=desc, origen=OrigenDato.PROPUESTA))
            agregados["causas"] += 1

    motivos = set(s.scalars(select(MotivoParada.codigo)))
    for codigo, desc, req, falla, setup, cat, orden in MOTIVOS:
        if codigo not in motivos:
            s.add(MotivoParada(codigo=codigo, descripcion=desc, cuenta_como_requerida=req, es_falla=falla,
                               es_setup=setup, categoria_6p=cat, orden=orden))
            agregados["motivos"] += 1

    etapas = set(s.scalars(select(EtapaImplementacion.numero)))
    for numero, fase, titulo, que, por_que, pantalla, criterio in ETAPAS:
        if numero not in etapas:
            s.add(EtapaImplementacion(numero=numero, fase=fase, titulo=titulo, que_es=que, por_que=por_que,
                                      pantalla=pantalla, criterio=criterio))
            agregados["etapas"] += 1

    modulos = set(s.scalars(select(ModuloHabilitado.codigo)))
    for codigo, nombre, hab in MODULOS:
        if codigo not in modulos:
            s.add(ModuloHabilitado(codigo=codigo, nombre=nombre, habilitado=hab))
            agregados["modulos"] += 1

    indicadores = set(s.scalars(select(IndicadorObjetivo.codigo)))
    for codigo, mayor, ref in INDICADORES:
        if codigo not in indicadores:
            s.add(IndicadorObjetivo(codigo=codigo, mayor_es_mejor=mayor, referencia_bibliografia=ref))
            agregados["indicadores"] += 1

    if s.scalar(select(TipoCambio.id).limit(1)) is None:
        s.add(TipoCambio(fecha=date(2026, 8, 1), ars_por_usd=1495.0,
                         fuente="Referencia del TP N.º 2 (agosto 2026). Actualizar con el valor del día."))
    return agregados
