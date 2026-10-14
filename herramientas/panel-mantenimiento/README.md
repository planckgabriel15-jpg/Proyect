# Panel de Mantenimiento

Un botón para la barra de tareas de Windows que abre un **panel de mantenimiento al estilo del de *Five Nights at Freddy's 3***: monitor CRT verde con barrido, estática, parpadeo, glitches y sonidos. Las acciones son reales y optimizan la PC.

```
 PANEL DE MANTENIMIENTO                                  23:41
 SISTEMA: NOTEBOOK  //  USUARIO: TU-USUARIO             MODO USUARIO
 ─────────────────────────────────────────────────────────────────
 ALERTAS                 │ REINICIO DE SISTEMAS
 MEMORIA ALTA!           │ ► PROCESOS EN 2DO PLANO     REINICIANDO.. ████░░░░
                         │   MEMORIA Y DUPLICADOS                   EN ESPERA
 ESTADO DEL SISTEMA      │   OPTIMIZACION GENERAL                   EN ESPERA
 RAM   █████████░░░  78% │
 CPU   ██░░░░░░░░░░  14% │   REINICIAR TODO              REINICIANDO.. █░░░░░░░
 DISCO ███████░░░░░  61% │   SALIR
 ─────────────────────────────────────────────────────────────────
 > CERRADO: OneDrive (148.2 MB)
 > CERRADO: AdobeCollabSync (61.0 MB)█
```

| Opción del panel | Equivale en FNAF 3 a | Qué hace realmente |
|---|---|---|
| **PROCESOS EN 2DO PLANO** | *Audio Devices* | Cierra los programas que corren sin ventana visible y sin audio. **No toca lo que estás usando** (ver abajo). |
| **MEMORIA Y DUPLICADOS** | *Camera System* | Busca archivos idénticos byte a byte, manda las copias a la **Papelera** y compacta la RAM. |
| **OPTIMIZACIÓN GENERAL** | *Ventilation* | Temporales, informes de error, caché DNS, RAM, TRIM del SSD (admin) y diagnóstico de arranque. |
| **REINICIAR TODO** | *Reboot All* | Los tres en secuencia. |

> Todo el audio y el icono se sintetizaron desde cero (`recursos/generar_recursos.py`); no se usa ningún recurso del juego. El parecido es solo de estilo.

---

## Instalación (2 minutos)

**Requisitos:** Windows 10 u 11. No hay que instalar nada más: usa Windows PowerShell 5.1, que ya viene con Windows.

1. Descargá esta carpeta (`herramientas/panel-mantenimiento`) a tu PC. Si bajás el ZIP del repositorio, primero descomprimilo.
2. Doble clic en **`Instalar.bat`**.
   - Pregunta si querés que el panel abra **siempre como administrador**. Con "S" también limpia `C:\Windows\Temp`, borra la caché de Windows Update y hace TRIM al disco, pero Windows te pide permiso (UAC) cada vez que lo abrís. Con "N" igual funciona, solo se saltean esos pasos (y desde el panel podés apretar **A** para elevarlo en el momento).
3. **Anclalo a la barra de tareas** (Windows no deja que un programa se ancle solo, hay que hacerlo a mano una vez):
   - **Windows 11:** Inicio → *Todas las aplicaciones* → clic derecho en **Panel de Mantenimiento** → *Más* → *Anclar a la barra de tareas*.
   - **Windows 10:** Inicio → clic derecho en **Panel de Mantenimiento** → *Más* → *Anclar a la barra de tareas*.
   - O con el panel abierto: clic derecho en su icono de la barra → *Anclar a la barra de tareas*.

Para probarlo sin instalar: doble clic en `Abrir-sin-instalar.bat`.
Para quitarlo: `Desinstalar.bat` (y si quedó anclado, clic derecho → *Desanclar*).

### Si Windows bloquea el archivo
Si al hacer doble clic aparece **"Windows protegió su PC"** (SmartScreen), es porque el archivo vino de Internet: *Más información* → *Ejecutar de todas formas*. El instalador desbloquea el resto de los archivos (`Unblock-File`) y los accesos directos usan `-ExecutionPolicy Bypass` solo para este script, sin cambiar la política de tu sistema.

---

## Controles

| Tecla | Acción |
|---|---|
| ↑ ↓ (o W / S) | Elegir sistema |
| Enter / Espacio / clic | Reiniciar el sistema elegido |
| 1 · 2 · 3 · 4 | Atajo directo a cada opción |
| C | Cancelar lo que se está ejecutando |
| M | Silenciar o activar el sonido |
| A | Reabrir como administrador |
| Esc | Apagar el panel (con animación de apagado CRT) |

Antes de cerrar procesos o mover archivos, el panel **muestra la lista y pregunta** (`[S] SÍ / [N] NO`). Si preferís que no pregunte, poné `"confirmarAntesDeActuar": false` en `config.json`.

---

## Cómo funciona cada sistema (y por qué es seguro)

### 1. Procesos en segundo plano
Se considera que **estás usando** un proceso, y por lo tanto nunca se cierra, si cumple cualquiera de estas condiciones:

| Protección | Cómo se detecta |
|---|---|
| Tiene una **ventana visible** (aunque esté minimizada o en otro escritorio virtual) | `EnumWindows` + `IsWindowVisible` |
| Es la ventana en **primer plano** | `GetForegroundWindow` |
| Está **reproduciendo o grabando audio** (música de fondo, una llamada de Discord, etc.) | API Core Audio de Windows: sesiones en estado *Active* (`IAudioSessionControl2::GetProcessId`) |
| Es **hijo de algo que estás usando** (pestañas de Chrome, extensiones de VS Code, un `node` lanzado desde la terminal) | Árbol de procesos, verificando que el padre sea anterior al hijo para no confundir PIDs reciclados |
| Es parte de **Windows** | Todo lo que corre desde `C:\Windows`, más una lista de procesos del shell (`explorer`, `dwm`, `ctfmon`…) |
| Es **antivirus, driver o utilidad del fabricante** | Rutas protegidas (`\Realtek\`, `\NVIDIA Corporation\`, `\Lenovo\`, `\ESET\`…) y nombres protegidos (touchpad, audio, gráficos) |
| Es **Steam/Epic, una VPN o un gestor de contraseñas** | Lista `procesos.protegidos` de `config.json` (acepta comodines: `PowerToys*`) |
| Usa **menos de 5 MB** | No vale la pena cerrarlo (`memoriaMinimaMB`) |
| Pertenece a **otro usuario o sesión** | Solo se revisa tu sesión |

El resto (por ejemplo OneDrive, actualizadores, el Teams o el Discord minimizados a la bandeja sin una llamada) se ofrece para cerrar. Si algo que usás aparece en la lista, decí **N** y agregalo a `procesos.protegidos`.

### 2. Memoria y duplicados
**Duplicados.** Revisa Descargas, Escritorio, Documentos, Imágenes, Videos y Música (configurable). Un archivo es duplicado solo si es **idéntico byte a byte**, comparado en tres etapas para que sea rápido:
1. mismo tamaño;
2. mismo SHA-256 de los primeros 64 KB;
3. mismo **SHA-256 completo**.

De cada grupo se **conserva uno**: el que no tiene nombre de copia (`foto (1).jpg`, `doc - copia.pdf`, `Copia de…`) y, si empatan, el más antiguo. Los demás van a la **Papelera de reciclaje**, así que se pueden restaurar. Justo antes de mover cada uno se vuelve a comprobar que el original siga existiendo. Además:
- se guarda la lista completa en `%LOCALAPPDATA%\PanelMantenimiento\registros\duplicados_FECHA.csv`;
- se saltean las carpetas que son proyectos (`.git`), `node_modules`, `AppData`, los archivos ocultos o de sistema y los archivos de OneDrive que están **solo en la nube** (no se descargan para compararlos);
- si un archivo no entra en la Papelera porque es enorme, Windows avisa en vez de borrarlo para siempre (`FOF_WANTNUKEWARNING`).

**Memoria.** A cada proceso se le pide a Windows que saque de la RAM las páginas que no está usando (`EmptyWorkingSet`). Para ser honestos: Windows ya administra bien la memoria, y Microsoft documenta esta función como pensada sobre todo para pruebas y ajuste. El efecto es inmediato y visible (sube la RAM disponible), pero temporal: las páginas que un programa vuelva a necesitar se recargan, casi siempre desde la memoria en espera, sin tocar el disco. Sirve para "hacer lugar" antes de abrir algo pesado, no es una mejora permanente. Con `memoria.purgarListaEnEspera: true` y modo administrador, además vacía la caché en espera, como el botón *Empty Standby List* de RAMMap de Sysinternals. Por defecto está apagado, porque esa caché acelera la apertura de programas.

### 3. Optimización general
| Paso | Detalle | ¿Admin? |
|---|---|---|
| Temporales del usuario (`%TEMP%`) | Solo archivos de más de 1 día; los que están en uso se dejan | No |
| Temporales de Windows (`C:\Windows\Temp`) | Igual criterio | Sí |
| Informes de error y volcados | `WER\ReportArchive`, `WER\ReportQueue`, `CrashDumps` | Parcial |
| Caché de Optimización de distribución | Descargas de Windows Update ya aplicadas (`Delete-DeliveryOptimizationCache`) | Sí |
| Caché DNS | `ipconfig /flushdns` | No |
| Compactar RAM | Ver arriba | No |
| TRIM del SSD | `Optimize-Volume -ReTrim`. En un disco mecánico solo avisa, salvo `desfragmentarHDD: true` | Sí |
| Diagnóstico | Cuántos programas arrancan con Windows y qué plan de energía está activo | No |

Al final muestra cuánto espacio se liberó en `C:`.

**Qué NO hace, a propósito:** no toca el registro, no desactiva servicios, no vacía la Papelera (ahí están los duplicados recuperables), no borra cachés de navegadores ni Prefetch, y no cambia el plan de energía (en una notebook afecta la batería). Esos "trucos" suelen no mejorar nada o romper algo.

---

## Configuración (`config.json`)

Después de instalar, el archivo que se usa está en `%LOCALAPPDATA%\PanelMantenimiento\app\config.json`. Si reinstalás, se conserva.

| Clave | Para qué sirve |
|---|---|
| `sonido.activado` / `volumen` / `ambiente` | Sonido general, volumen de 0 a 1 y zumbido de fondo |
| `confirmarAntesDeActuar` | Preguntar antes de cerrar procesos o mover duplicados |
| `procesos.protegidos` | Nombres que nunca se cierran (sin `.exe`, aceptan `*`) |
| `procesos.rutasProtegidas` | Fragmentos de ruta protegidos (aceptan `%VARIABLES%`) |
| `procesos.memoriaMinimaMB` | Ignorar procesos más chicos que esto |
| `duplicados.carpetas` | `{Descargas}`, `{Escritorio}`, `{Documentos}`, `{Imagenes}`, `{Videos}`, `{Musica}` o rutas propias (`D:\\Fotos`) |
| `duplicados.tamanoMinimoKB` | Ignorar archivos más chicos |
| `duplicados.omitirRepositoriosYProyectos` | Saltear carpetas que tienen `.git` o `.svn` |
| `duplicados.carpetasExcluidas` / `extensionesExcluidas` | Exclusiones |
| `memoria.purgarListaEnEspera` | Vaciar la caché en espera (admin) |
| `general.*` | Activar o desactivar cada paso; `diasMinimosTemporales` |

Los registros de cada sesión quedan en `%LOCALAPPDATA%\PanelMantenimiento\registros\`.

---

## Estructura

```
panel-mantenimiento/
├── PanelMantenimiento.ps1   interfaz WPF: animación CRT, sonido, menú y diálogos
├── modulos/
│   ├── Tareas.ps1           lógica de los 3 sistemas (corre en un hilo aparte)
│   └── Nativo.cs            llamadas a Windows: ventanas, audio, RAM, Papelera, CPU
├── recursos/
│   ├── sonidos/*.wav        efectos sintetizados (encendido, tic, ok, error, ambiente…)
│   ├── icono.ico
│   └── generar_recursos.py  regenera sonidos e icono (Python + numpy + Pillow)
├── config.json
├── Instalar.bat / .ps1      copia a %LOCALAPPDATA% y crea accesos directos
├── Desinstalar.bat / .ps1
└── Abrir-sin-instalar.bat
```

**Detalles técnicos**
- **Interfaz.** WPF nativo desde PowerShell. Las tareas corren en un *runspace* separado y se comunican con la interfaz mediante una cola sincronizada, así la animación nunca se congela mientras se escanea el disco.
- **Efectos CRT.** Encendido y apagado en dos fases (línea horizontal que se expande y se contrae), líneas de barrido, banda que baja, nieve generada en tiempo real, viñeta, brillo de fósforo (`DropShadowEffect`), parpadeo, sacudidas en los errores y texto que se escribe solo. La animación se pausa cuando la ventana está minimizada.
- **Taskbar.** El acceso directo y el proceso comparten un `AppUserModelID` propio (`Planck.PanelMantenimiento`). Así el botón anclado y la ventana abierta se agrupan juntos y no se mezclan con otras ventanas de PowerShell.

### Qué se verificó y qué no
Se desarrolló en un entorno Linux, por lo que **no se pudo abrir la ventana en Windows** antes de publicarlo. Sí se verificó:
- que los 4 scripts `.ps1` pasan el parser de PowerShell sin errores y no usan sintaxis exclusiva de PowerShell 7;
- que el código C# (`Nativo.cs` y el del instalador) compila en modo C# 5, que es el compilador de Windows PowerShell 5.1;
- que el XAML es válido y contiene todos los elementos que usa el script;
- con pruebas sobre un árbol de carpetas de ejemplo, que el detector de duplicados encuentra las copias reales, conserva el original, **no** marca un archivo que solo difiere en el último byte y saltea `.git` y `node_modules`; también que la limpieza de temporales respeta los archivos recientes y que una falla dentro de una tarea se informa como ERROR sin colgar el panel.

Si algo no arranca, aparece un mensaje con el error. El detalle queda en `%LOCALAPPDATA%\PanelMantenimiento\registros\`.

---

## Fuentes

- Maintenance Panel de FNAF 3, con las opciones *Audio Devices*, *Camera System*, *Ventilation* y *Reboot All*: [Five Nights at Freddy's 3, Fnafapedia](https://fnafapedia.fandom.com/wiki/Five_Nights_at_Freddy%27s_3?oldid=4280) · [Five Nights at Freddy's 3 tips (Christian Today)](https://www.christiantoday.com/trends/five-nights-at-freddys-3-tips-and-cheats)
- `EmptyWorkingSet`, permisos que necesita y uso "para pruebas y ajuste": [Microsoft Learn: EmptyWorkingSet](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-emptyworkingset) · [Working Set Information](https://msdn.microsoft.com/en-us/windows/desktop/ms687398)
- Papelera con `SHFileOperation`, `FOF_ALLOWUNDO` y `FOF_WANTNUKEWARNING`: [SHFILEOPSTRUCT](https://learn.microsoft.com/windows/win32/api/shellapi/ns-shellapi-shfileopstructa) · [SHFileOperation](https://learn.microsoft.com/windows/win32/api/shellapi/nf-shellapi-shfileoperationa) · [ejemplo de la advertencia (CodeGuru)](https://forums.codeguru.com/showthread.php?p=2155247)
- Detección de audio activo y el caso `AUDCLNT_S_NO_SINGLE_PROCESS`: [IAudioSessionControl2::GetProcessId](https://learn.microsoft.com/en-us/windows/win32/api/audiopolicy/nf-audiopolicy-iaudiosessioncontrol2-getprocessid) · [IAudioSessionControl2](https://learn.microsoft.com/en-us/windows/desktop/api/audiopolicy/nn-audiopolicy-iaudiosessioncontrol2)
- AppUserModelID en accesos directos y agrupación en la barra de tareas: [Application User Model IDs](https://learn.microsoft.com/windows/win32/shell/appids) · [System.AppUserModel.ID](https://learn.microsoft.com/windows/win32/properties/props-system-appusermodel-id) · [Windows Installer Team: soporte de la barra de tareas](https://learn.microsoft.com/en-us/archive/blogs/windows_installer_team/windows-7-taskbar-support-with-the-msishortcutproperty-table)
- Otras APIs y cmdlets usados: [Optimize-Volume](https://learn.microsoft.com/en-us/powershell/module/storage/optimize-volume) · [Delete-DeliveryOptimizationCache](https://learn.microsoft.com/en-us/powershell/module/deliveryoptimization/delete-deliveryoptimizationcache) · [RAMMap (Sysinternals)](https://learn.microsoft.com/en-us/sysinternals/downloads/rammap) · [Políticas de ejecución de PowerShell](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies)
