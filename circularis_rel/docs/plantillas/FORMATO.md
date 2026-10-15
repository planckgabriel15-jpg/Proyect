# Formato de las planillas de importación

Generado por `scripts/generar_plantillas.py` desde `circularis_rel/servicios/importador/esquema.py`. No editar a mano.

## Reglas generales

- **Fila 1:** encabezados. No se cambian. **Fila 2:** ayuda, que se ignora al leer. Los datos empiezan en la **fila 3**.
- Columnas obligatorias: encabezado en rojo y "* obligatoria" en la ayuda.
- La clave es el **código**: re-importar el mismo libro actualiza lo que cambió y no duplica.
- Una celda vacía **no borra** un dato existente. Para borrar se edita en el sistema, y queda auditado.
- Fechas `DD/MM/AAAA`, horas `HH:MM`, números con coma o punto decimal. SI/NO para las casillas.
- **Todo o nada:** si hay un error en cualquier fila no se graba nada y el reporte indica hoja, fila y columna.
- Conviene usar primero **Simular**: hace todas las validaciones y no graba.
- Se pueden importar solo algunas hojas: las ausentes se ignoran.

## Archivos

| Archivo | Uso |
|---|---|
| `carga_inicial.xlsx` | Plantilla vacía de la carga inicial |
| `historico.xlsx` | Plantilla vacía del histórico con triage A/B/C |
| `carga_inicial_borrador_TP1.xlsx` | Borrador precargado con el Plan y el TP N.º 1. **Revisar antes de importar** (ver hoja LEEME) |

## Hoja `lineas` (carga_inicial.xlsx)

Líneas de producción.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `codigo` | texto | sí | Código único, p. ej. TWOOD |
| `nombre` | texto | sí | Nombre de la línea |

## Hoja `turnos` (carga_inicial.xlsx)

Turnos de trabajo.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `codigo` | texto | sí | Código único, p. ej. M |
| `nombre` | texto | sí | Mañana, Tarde… |
| `hora_inicio` | hora | sí | HH:MM |
| `hora_fin` | hora | sí | HH:MM |
| `duracion_h` | real | sí | Horas del turno (rango 0.5 a 24) |

## Hoja `tipos_componente` (carga_inicial.xlsx)

Tipos de componente, en lenguaje de planta.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `codigo` | texto | sí | Código único, p. ej. CUCHILLAS |
| `nombre` | texto | sí | Cuchillas, criba, rulemanes… |
| `variable_edad` | lista |  | Cómo se mide la edad (por defecto HORAS). Valores: `HORAS`, `TONELADAS` |
| `hh_preventiva` | real |  | Horas-hombre de un cambio preventivo (rango 0 a ∞) |
| `hh_correctiva` | real |  | Horas-hombre de una reparación correctiva (rango 0 a ∞) |
| `beta_ref` | real |  | β de referencia (opcional, exige fuente_ref) (rango 0.01 a ∞) |
| `eta_ref` | real |  | η de referencia (opcional) (rango 0.01 a ∞) |
| `fuente_ref` | texto |  | De dónde sale el β de referencia |
| `uso` | lista |  | Uso común o específico. Valores: `COMUN`, `ESPECIFICO` |
| `intervalo_fabricante` | real |  | Intervalo de cambio recomendado por el fabricante (rango 0 a ∞) |
| `unidad_intervalo_fabricante` | lista |  | Unidad del intervalo del fabricante. Valores: `HORAS`, `TONELADAS` |
| `falla_oculta` | bool |  | SI si es de seguridad o respaldo (válvula de seguridad, detector, UPS…). Valores: `SI`, `NO` |
| `funcion_seguridad` | bool |  | SI si protege a personas o a la planta. Valores: `SI`, `NO` |
| `intervalo_pf` | real |  | Intervalo P-F conocido (misma unidad que la edad) (rango 0 a ∞) |
| `origen` | lista |  | JEFE si lo cargó el jefe; TP1_ILUSTRATIVO si viene del TP. Valores: `JEFE`, `PROPUESTA`, `TP1_ILUSTRATIVO`, `IMPORTACION`, `DEMO` |

## Hoja `maquinas` (carga_inicial.xlsx)

Máquinas con su catastro (UNIDAD 6, MANT/RHM001).

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `codigo` | texto | sí | Código del QR, p. ej. AGR-001 |
| `nombre` | texto | sí | Nombre de la máquina |
| `linea` | texto | sí | Código de la línea |
| `etapa_proceso` | lista | sí | Etapa del proceso. Valores: `PREPROCESADO`, `LAVADO`, `SECADO`, `FORMULACION`, `EXTRUSION`, `ACONDICIONAMIENTO` |
| `orden_proceso` | entero |  | Orden en el esquema de la línea (rango 0 a ∞) |
| `ubicacion` | texto |  | Sector de la planta |
| `funcion` | texto |  | Qué hace la máquina |
| `horas_promedio_dia` | real |  | Horas de operación promedio por día (rango 0 a 24) |
| `unidad_produccion` | lista |  | Unidad de la cantidad procesada. Valores: `KG`, `FARDOS`, `DURMIENTES`, `NINGUNA` |
| `factor_toneladas` | real |  | Toneladas por unidad (para la edad en toneladas) (rango 0 a ∞) |
| `autonomia_pulmon_h` | real |  | Horas que la línea aguanta con esta máquina parada (rango 0 a ∞) |
| `ciclo_teorico_s` | real |  | Tiempo de ciclo teórico en segundos (para RO/OEE) (rango 0 a ∞) |
| `numero_serie` | texto |  |  |
| `fabricante` | texto |  |  |
| `modelo` | texto |  |  |
| `proveedor` | texto |  |  |
| `fecha_instalacion` | fecha |  | DD/MM/AAAA |
| `ancho_mm` | real |  |  (rango 0 a ∞) |
| `alto_mm` | real |  |  (rango 0 a ∞) |
| `largo_mm` | real |  |  (rango 0 a ∞) |
| `peso_kg` | real |  |  (rango 0 a ∞) |
| `condiciones_almacenamiento` | texto |  |  |
| `caracteristicas_tecnicas` | texto |  |  |
| `ruta_documentos` | texto |  | Carpeta con planos, manuales y catálogos |

## Hoja `maquina_turnos` (carga_inicial.xlsx)

Qué turnos trabaja cada máquina.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `maquina` | texto | sí | Código de la máquina |
| `turno` | texto | sí | Código del turno |
| `dias` | texto |  | Días de la semana (1=lunes … 7=domingo), p. ej. 1,2,3,4,5 |

## Hoja `posiciones` (carga_inicial.xlsx)

Posiciones de componente en cada máquina.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `maquina` | texto | sí | Código de la máquina |
| `codigo` | texto | sí | Código de la posición dentro de la máquina, p. ej. CUCH |
| `tipo_componente` | texto | sí | Código del tipo de componente |
| `ubicacion` | texto |  | Dónde está en la máquina |
| `cantidad` | entero |  | Cantidad por máquina (por defecto 1) (rango 1 a ∞) |
| `critica` | bool |  | SI si su estado define el color de la máquina. Valores: `SI`, `NO` |

## Hoja `sintomas` (carga_inicial.xlsx)

Síntomas del aviso de falla.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `codigo` | texto | sí |  |
| `descripcion` | texto | sí |  |
| `icono` | texto |  | Emoji opcional |

## Hoja `modos` (carga_inicial.xlsx)

Modos de falla (lista cerrada por tipo de componente).

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `codigo` | texto | sí |  |
| `descripcion` | texto | sí |  |
| `tipos_componente` | codigos | sí | Códigos de tipo de componente separados por coma |
| `origen` | lista |  | JEFE o TP1_ILUSTRATIVO. Valores: `JEFE`, `PROPUESTA`, `TP1_ILUSTRATIVO`, `IMPORTACION`, `DEMO` |

## Hoja `causas` (carga_inicial.xlsx)

Causas de falla.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `codigo` | texto | sí |  |
| `descripcion` | texto | sí |  |
| `tipos_componente` | codigos |  | Vacío = aplica a todos |
| `origen` | lista |  | JEFE o TP1_ILUSTRATIVO. Valores: `JEFE`, `PROPUESTA`, `TP1_ILUSTRATIVO`, `IMPORTACION`, `DEMO` |

## Hoja `repuestos` (carga_inicial.xlsx)

Repuestos (UNIDAD 6, MANT/RM001).

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `codigo` | texto | sí |  |
| `descripcion` | texto | sí |  |
| `tipo_componente` | texto |  | Código del tipo de componente que reemplaza |
| `uso` | lista |  | Valores: `COMUN`, `ESPECIFICO` |
| `stock_actual` | real |  |  (rango 0 a ∞) |
| `stock_minimo` | real |  |  (rango 0 a ∞) |
| `ubicacion` | texto |  |  |
| `codigo_proveedor` | texto |  |  |
| `proveedor` | texto |  |  |
| `lead_time_dias` | real |  |  (rango 0 a ∞) |
| `familia_compra` | texto |  |  |
| `intervalo_fabricante` | real |  |  (rango 0 a ∞) |
| `precio` | real |  | Precio unitario (exige fecha_precio) (rango 0 a ∞) |
| `moneda` | lista |  | ARS por defecto. Valores: `ARS`, `USD` |
| `fecha_precio` | fecha |  | DD/MM/AAAA |

## Hoja `repuestos_por_maquina` (carga_inicial.xlsx)

Qué repuestos usa cada máquina.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `maquina` | texto | sí |  |
| `repuesto` | texto | sí |  |
| `cantidad_instalada` | real |  |  (rango 0 a ∞) |

## Hoja `criticidad` (carga_inicial.xlsx)

Criticidad por máquina (método del TP: escalas del TP N.º 1).

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `maquina` | texto | sí |  |
| `metodo` | lista |  | Por defecto TP_6_CRITERIOS. Valores: `TP_6_CRITERIOS`, `PONDERACION_U1` |
| `uso` | entero | sí | 5 / 3 / 1 |
| `alternativa` | entero | sí | 5 / 4 / 2 / 1 |
| `influencia` | entero | sí | 5 / 4 / 2 / 1 |
| `calidad` | entero | sí | 5 / 4 / 2 / 1 |
| `ambiente` | entero | sí | 5 / 3 / 1 |
| `seguridad` | entero | sí | 5 / 3 / 1 |
| `clase` | lista |  | Vacío = la calcula el sistema. Valores: `A`, `B`, `C` |
| `fecha` | fecha |  | Fecha de la evaluación |

## Hoja `amfe` (carga_inicial.xlsx)

AMFE por máquina y componente.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `maquina` | texto |  | Código de la máquina (vacío = vale para todas) |
| `tipo_componente` | texto | sí |  |
| `modo` | texto | sí | Código del modo de falla |
| `requerimiento` | texto |  |  |
| `efecto` | texto |  |  |
| `causa` | texto |  |  |
| `control_prevencion` | texto |  |  |
| `control_deteccion` | texto |  |  |
| `g` | entero | sí | Gravedad 1–10 (rango 1 a 10) |
| `o` | entero | sí | Ocurrencia 1–10 (rango 1 a 10) |
| `d` | entero | sí | Detección 1–10 (rango 1 a 10) |
| `acciones` | texto |  |  |
| `responsable` | texto |  |  |
| `origen` | lista |  | JEFE o TP1_ILUSTRATIVO. Valores: `JEFE`, `PROPUESTA`, `TP1_ILUSTRATIVO`, `IMPORTACION`, `DEMO` |

## Hoja `parametros_costos` (carga_inicial.xlsx)

Parámetros de costos con fecha de vigencia.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `clave` | lista | sí | Parámetro. Valores: `costos.tarifa_mo_ars_h`, `costos.margen_linea_ars_h`, `costos.horas_parada_defecto_h` |
| `valor` | real | sí |  (rango 0 a ∞) |
| `vigente_desde` | fecha | sí | DD/MM/AAAA |

## Hoja `tipos_cambio` (carga_inicial.xlsx)

Tipo de cambio por fecha.

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `fecha` | fecha | sí | DD/MM/AAAA |
| `ars_por_usd` | real | sí | Pesos por dólar (rango 0.0001 a ∞) |
| `fuente` | texto |  |  |

## Hoja `historico` (historico.xlsx)

Histórico de cambios y fallas, clasificado por triage A/B/C (Plan §11).

| Columna | Tipo | Obligatoria | Ayuda / valores |
|---|---|---|---|
| `maquina` | texto | sí |  |
| `posicion` | texto |  | Código de la posición (vacío = componente no identificado → clase C) |
| `tipo_fin` | lista | sí | Cómo terminó la vida. Valores: `FALLA`, `SUSPENSION_PREVENTIVA`, `SUSPENSION_OTRA` |
| `modo` | texto |  | Código del modo de falla (obligatorio para FALLA de clase A) |
| `fecha_instalacion` | fecha |  | DD/MM/AAAA |
| `fecha_fin` | fecha |  | Fecha real del cambio o falla |
| `fecha_fin_desde` | fecha |  | Si la fecha es aproximada: desde |
| `fecha_fin_hasta` | fecha |  | Si la fecha es aproximada: hasta |
| `edad_horas` | real |  | Horas operadas, si se conocen (rango 0 a ∞) |
| `edad_desde_h` | real |  | Si la edad es aproximada: desde (rango 0 a ∞) |
| `edad_hasta_h` | real |  | Si la edad es aproximada: hasta (rango 0 a ∞) |
| `clase` | lista |  | A, B o C. Vacío = la propone el sistema. Valores: `A`, `B`, `C` |
| `fuente` | texto | sí | OT, factura, parte, memoria del encargado… |
| `respaldo` | texto |  | N.º de OT, factura o parte (obligatorio para clase A) |
| `descripcion_original` | texto |  | Texto tal como figura en el registro original |
| `observaciones` | texto |  |  |

## Triage del histórico

| Clase | Requisitos | Uso en el cálculo |
|---|---|---|
| A, confiable | posición, `fecha_fin` real, `respaldo` (OT, factura, parte) y `modo` si es FALLA | Vida con horas de nivel E |
| B, parcial | posición y rango de fecha (`fecha_fin_desde`/`hasta`) o de edad (`edad_desde_h`/`hasta`) | Censura por intervalo, solo MLE |
| C, no usable | cualquier otro caso | Fuera del ajuste; solo Pareto cualitativo |

Si `clase` queda vacía, el sistema la propone. Si se indica una clase que no cumple los requisitos, es error. Las fechas con espaciado regular (por ejemplo cada 30 días) generan la advertencia "posibles valores reconstruidos".
