# Guion del piloto (fase 2)

**Objetivo.** Usar el sistema de verdad en pocas máquinas, corregir lo que no ande y llegar al criterio del Plan (§10): **dos semanas seguidas con más del 90 % de los partes completos**. Recién entonces se extiende al resto de la planta.

**Máquinas.** Las del Plan: EXT-001, LAV-001, ENF-001 y AGR-001. Se cambian en *Parámetros › piloto.maquinas*.

**Duración estimada.** De 3 a 4 semanas: una de arranque y al menos dos que cumplan el criterio.

## Antes de empezar (jefe)

1. Borrar los datos DEMO (*Configuración › Datos DEMO*).
2. Revisar las 4 máquinas en *Máquinas y revisión*: componentes, críticos, turnos y catastro.
3. Cargar o revisar la criticidad (*Criticidad*).
4. Imprimir y pegar los QR en cada máquina.
5. Crear los usuarios: un PIN por operario, el encargado de mantenimiento y la gerencia.
6. Cargar la tarifa de mano de obra, el margen por hora de la línea y el tipo de cambio (*Parámetros*), con su fuente.
7. Si hay registros viejos, cargarlos en la plantilla de histórico y clasificarlos en *Histórico (triage)*.

## Primer día (capacitación de 15 minutos por turno)

- Mostrar en el celular: escanear el QR, **Parte de turno** (un toque si operó todo) y **Reportar falla** (síntoma y foto).
- Cada operario carga un parte de prueba con el jefe al lado. Medir el tiempo: la meta es menos de 30 s por parte y menos de 60 s por aviso (`guion_usabilidad.md`).
- El encargado practica tomar un aviso y cerrar la OT en dos pasos.

## Rutina diaria

| Quién | Qué | Dónde |
|---|---|---|
| Operario | Parte de turno al terminar; aviso apenas pasa la falla | Celular, con el QR |
| Encargado | Tomar los avisos, cerrar las OT, completar los partes que avisa el sistema | Bandeja del encargado |
| Jefe | Validar lo cerrado (idealmente en menos de 48 h) | Bandeja de validación |

## Rutina semanal (jefe, 20 minutos)

1. **Piloto:** porcentaje de partes completos por máquina y semana. Si una máquina queda por debajo del 90 %, hablar con su turno: qué lo complica (señal, apuro, no entienden alguna opción).
2. **Uso de los catálogos:** lo que nunca se usa puede sobrar; si se carga mucho "Otro", falta una opción. Ajustar en *Catálogos* (nada se borra: se desactiva).
3. **Panel de planta:** mirar los semáforos y las alertas. Con pocas fallas todo es orientativo (confianza baja o gris): sirve para ver si los datos tienen sentido, no para decidir.
4. **Umbrales:** si el semáforo se pone rojo demasiado seguido (o nunca), revisar con el criterio del jefe los umbrales de *Parámetros › semáforo* y anotar el motivo del cambio.
5. **Histórico:** comparar en *Análisis Weibull* "solo datos nuevos" contra "nuevos + histórico A/B". Si se parecen, se puede activar `motor.semaforo_con_historico`.

## Qué anotar

Llevar una lista de incidencias (fecha, quién, qué pasó, qué se cambió). Sirve para la capacitación del resto de la planta y para el manual de cada rol.

## Criterio para pasar de fase

- Dos semanas seguidas con más del 90 % de partes completos en cada máquina del piloto (la pantalla *Piloto* lo calcula; los partes estimados por el sistema no cuentan).
- Fallas que se validan (etapa 15 de la puesta en marcha).
- Catálogos y umbrales revisados con el jefe.

## Extensión al resto de la planta

1. Repetir "Antes de empezar" con las demás máquinas (QR, revisión, criticidad).
2. Capacitar a los turnos que faltan con los operarios del piloto como referentes.
3. Mantener la rutina semanal un mes más con todas las máquinas.
