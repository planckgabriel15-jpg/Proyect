# Manual del encargado de mantenimiento (una página)

## Todos los días

1. **Bandeja del encargado:** avisos abiertos ordenados por criticidad de la máquina. Tocá **Tomar** para empezar la reparación (se crea la OT).
2. **Cerrar OT** en dos pasos:
   - Paso 1: componente, modo de falla, causa, inicio y fin de la reparación.
   - Paso 2: horas-hombre, repuestos usados, si fue reemplazo o reparación mínima, y la clasificación de la falla (efecto, total o parcial, repentina o progresiva). Lo que no sabés queda con el valor por defecto.
   - Al cerrar, el componente nuevo empieza su vida en cero. El jefe valida después.
3. **Partes faltantes:** el sistema te avisa a la mañana qué partes de ayer faltan. Completalos o pedíselos al operario; si nadie los carga, a los dos días se estiman (y cuentan como estimados).

## Cambios planificados

- **Plan preventivo › Órdenes de trabajo:** las OT preventivas se generan solas una semana antes. Imprimí la OT (formato **MANT/MPV001**), hacé el trabajo y registralo en **Cambio preventivo**: la OT planificada se cierra sola.
- **Pruebas funcionales** (válvulas de seguridad, detectores, alarmas): registrá si **actuó** o **no actuó**. Si no actuó, queda el aviso de falla para repararla. Una falla oculta solo se ve cuando se prueba.
- **Predictivo** (si está habilitado): cargá las mediciones (vibración, temperatura, ultrasonido). Fuera de límite, el sistema avisa y, sobre el de acción, genera una OT de inspección.

## Repuestos

En **Repuestos** ves el stock contra la demanda esperada en el plazo de entrega y el mínimo recomendado. Después de cada conteo físico, cargá el stock real con el motivo.

## Análisis de problemas

Si una falla se repite, abrí un **5 Porqués** (o Ishikawa, 5W+1H, hoja de verificación) desde **Análisis de problemas**. La acción puede convertirse en una OT de mejora (modificativo).
