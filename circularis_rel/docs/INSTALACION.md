# Instalación en la mini PC (Windows, una página)

**Requisitos:** PC o mini PC siempre encendida, conectada por cable al router, con Windows 10/11 y una dirección IP fija en la red local (por ejemplo 192.168.0.10).

## 1. Instalar

1. Instalar **Python 3.12** (python.org) y tildar "Add to PATH".
2. Copiar la carpeta `circularis_rel` en `C:\Circularis\circularis_rel`.
3. Abrir PowerShell en esa carpeta y ejecutar:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\pip install --require-hashes -r requirements.lock
.venv\Scripts\pip install --no-deps -e .
copy .env.example .env      # y completar: CIRCULARIS_URL_BASE, CIRCULARIS_CLAVE_COOKIE, carpeta de datos
.venv\Scripts\circularis inicializar
.venv\Scripts\circularis crear-usuario jefe "Nombre del jefe" JEFE
```

## 2. Arranque automático: dos servicios de Windows

Se usa NSSM (nssm.cc), que convierte cualquier programa en servicio de Windows.

```powershell
nssm install CircularisApp    C:\Circularis\circularis_rel\.venv\Scripts\circularis.exe app
nssm set     CircularisApp    AppDirectory C:\Circularis\circularis_rel
nssm install CircularisTareas C:\Circularis\circularis_rel\.venv\Scripts\circularis.exe tareas
nssm set     CircularisTareas AppDirectory C:\Circularis\circularis_rel
nssm start CircularisApp
nssm start CircularisTareas
```

El servicio de tareas hace, solo:

| Cuándo | Qué |
|---|---|
| Cada 5 s | Recalcula lo que se acaba de validar |
| 02:00 | Partes estimados, edades, recálculo completo y alertas de riesgo |
| 02:30 | Reprograma el calendario preventivo y genera las OT que entran en la anticipación |
| 03:00 | Backup (y el día 1, a las 04:00, prueba de restauración) |
| 06:30 y 06:45 | Partes faltantes; edad sobre el intervalo, stock bajo y avisos sin validar |
| Cada 10 min | Mails inmediatos (riesgo firme, predictivo sobre el límite de acción, backup) |
| 07:00 | Mail con el resumen diario de las demás alertas |
| Lunes 07:30 | Resumen semanal en PDF para el jefe y la gerencia |
| Día 1, 07:15 | Reporte mensual en PDF (queda en `datos/reportes` y se manda por mail) |

Cualquiera se puede correr a mano: `circularis tareas --una-vez plan` (o `alertas_diarias`, `mails`, `reporte_mensual`…).

### Correo (opcional)

Sin correo el sistema funciona igual: las alertas quedan en el panel. Para mandar mails, completar en `.env`
`SMTP_SERVIDOR`, `SMTP_PUERTO` (587 con STARTTLS o 465 con SSL), `SMTP_USUARIO`, `SMTP_CLAVE` y `SMTP_REMITENTE`, y
cargar el mail de cada usuario en **Usuarios**. Las alertas orientativas (confianza baja) nunca se mandan.

## 3. Red y acceso

- En el firewall de Windows, permitir el puerto **8501** solo para la red local (perfil "Privado").
- En cada celular y tablet: abrir `http://192.168.0.10:8501` y "Agregar a pantalla de inicio".
- Imprimir las etiquetas QR (Máquinas y revisión → *Etiquetas QR*). Apuntan a `CIRCULARIS_URL_BASE`.
- No usar Streamlit Community Cloud: sus apps son públicas.

## 4. Backup

Se configura en Parámetros → `backup.carpeta_externa`: un disco externo o una carpeta sincronizada por Google Drive para escritorio. El procedimiento completo de backup y restauración está en `docs/BACKUP.md` (fase 1a).
