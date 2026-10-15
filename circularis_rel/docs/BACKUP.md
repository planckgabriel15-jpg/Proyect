# Backup y restauración

## Qué se respalda y cuándo

| Qué | Cuándo | Dónde |
|---|---|---|
| Base de datos completa (`circularis_AAAAMMDD_HHMM.db`) | Todos los días a las 03:00 | `datos/backups/` y la carpeta externa |
| Fotos de avisos y tarjetas (`fotos_AAAAMMDD_HHMM.zip`) | Junto con la base | Ídem |
| Prueba de restauración | El día 1 de cada mes a las 04:00 | `datos/backups/ultima_prueba_restauracion.json` |

- El backup usa la API de backup en línea de SQLite: sale consistente aunque haya gente cargando datos.
- **Carpeta externa:** parámetro `backup.carpeta_externa` (Configuración › Parámetros › sistema). Puede ser un disco externo o una carpeta sincronizada por *Google Drive para escritorio*. Si no hay internet, Drive sube la copia cuando vuelve la conexión.
- **Rotación:** se conservan los últimos 30 diarios y el primero de cada mes durante 12 meses (parámetros `backup.retencion_*`).
- Si la prueba mensual falla, el jefe ve una alerta en el panel.

## Backup manual

```powershell
.venv\Scripts\circularis tareas --una-vez backup
```

## Restaurar

1. Detener los servicios: `nssm stop CircularisApp` y `nssm stop CircularisTareas`.
2. Ejecutar `.venv\Scripts\circularis restaurar C:\ruta\circularis_20261120_0300.db`. Antes de pisar nada, el comando hace un backup de la base actual en `datos/backups/antes_de_restaurar/`. También restaura las fotos del zip del mismo día.
3. Arrancar los servicios: `nssm start CircularisApp` y `nssm start CircularisTareas`.

## Prueba mensual (manual, 5 minutos)

```powershell
.venv\Scripts\circularis tareas --una-vez prueba_restauracion
type datos\backups\ultima_prueba_restauracion.json
```

Debe decir `"ok": true`: integridad `ok` y la misma cantidad de filas por tabla que el backup.

## Salida total

En cualquier momento: **Exportar** en la app, o `circularis exportar --salida todo.xlsx`. Genera un libro con una hoja por tabla. La empresa nunca queda atada al software.
