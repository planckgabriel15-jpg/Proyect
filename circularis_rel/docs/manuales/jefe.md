# Manual del jefe de mantenimiento (una página)

El sistema es tuyo: solo lo que validás entra en los cálculos.

## Todos los días (10 minutos)

1. **Bandeja de validación:** aprobá, devolvé (con motivo) o anulá. Las advertencias del sistema (reparación muy larga, vida rarísima, edad estimada) están resaltadas: no bloquean, son para mirar.
2. **Panel de planta:** semáforos, alertas, ranking de riesgo. Cada color dice su **confianza**: con confianza baja es orientativo; no tomes una decisión cara con tres datos.

## Todas las semanas

- **Análisis de problemas:** sugerencias automáticas (primeros del Pareto, fallas al azar con β ≈ 1, repeticiones). Abrí el análisis y seguí el PDCA.
- **Plan preventivo:** el sistema propone pasar del intervalo del fabricante al **calculado** cuando el componente tiene confianza media. Aprobalo vos; el calendario de 52 semanas (**MANT/1CMP001** y **2CMP001**) y las OT se arman solos. Revisá el diagnóstico de **sobre y sub-mantenimiento**.
- **Análisis Weibull:** método elegido, alternativa, comparación de distribuciones, histórico A/B y flota. Podés forzar un método, siempre con justificación (queda en la auditoría).

## Todos los meses

- **Tablero de comando:** cargá la facturación, las horas-hombre disponibles y lo que el sistema no puede saber. Fijá objetivos y límites (las referencias de la UNIDAD 5 son orientativas, no metas).
- **Reportes:** el PDF del mes se genera solo el día 1 (y llega por mail si hay correo configurado).

## Configuración

- **Parámetros:** umbrales del semáforo, horizonte, costos (tarifa, margen, tipo de cambio), confianza mínima de las alertas firmes, módulos habilitados. Un valor vacío es "falta dato", nunca cero.
- **Catálogos:** síntomas, modos, causas y motivos. Nada se borra: se desactiva.
- **Criticidad:** seis preguntas por máquina; la clase A/B/C endurece el semáforo y el plan.
- **Usuarios**, **Datos DEMO** (borrarlos antes de empezar), **Exportar** (todo a Excel).

**Backup:** se hace solo cada noche y se prueba la restauración cada mes. Ver `docs/BACKUP.md`.
