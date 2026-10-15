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

El servicio de tareas existe desde la fase 1a: hace el backup nocturno, el recálculo y las alertas.

## 3. Red y acceso

- En el firewall de Windows, permitir el puerto **8501** solo para la red local (perfil "Privado").
- En cada celular y tablet: abrir `http://192.168.0.10:8501` y "Agregar a pantalla de inicio".
- Imprimir las etiquetas QR (Máquinas y revisión → *Etiquetas QR*). Apuntan a `CIRCULARIS_URL_BASE`.
- No usar Streamlit Community Cloud: sus apps son públicas.

## 4. Backup

Se configura en Parámetros → `backup.carpeta_externa`: un disco externo o una carpeta sincronizada por Google Drive para escritorio. El procedimiento completo de backup y restauración está en `docs/BACKUP.md` (fase 1a).
