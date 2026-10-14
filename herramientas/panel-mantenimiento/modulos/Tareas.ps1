# Tareas de mantenimiento. Este archivo se carga en un runspace de trabajo separado
# de la interfaz: así la animación no se congela mientras se escanea el disco.
# Se comunica con la interfaz solo a través de $sync (hashtable sincronizada):
#   $sync.Cola       -> mensajes hacia la UI (log, progreso, preguntas, fin)
#   $sync.Respuesta  -> respuesta del usuario a una pregunta ($true / $false)
#   $sync.Cancelar   -> el usuario pidió cancelar
#   $sync.Config     -> config.json ya parseado
#   $sync.ArchivoLog -> ruta del log del día
# Compatible con Windows PowerShell 5.1 (viene con Windows 10/11).

Set-StrictMode -Off
$ErrorActionPreference = 'Continue'

# ============================================================ comunicación

function Send-Mensaje([hashtable]$Mensaje) {
    $sync.Cola.Enqueue($Mensaje)
}

function Write-Panel([string]$Texto, [string]$Nivel = 'info') {
    Send-Mensaje @{ Tipo = 'log'; Texto = $Texto; Nivel = $Nivel }
    try {
        $linea = '{0:yyyy-MM-dd HH:mm:ss} [{1}] {2}' -f (Get-Date), $Nivel.ToUpper(), $Texto
        [System.IO.File]::AppendAllText($sync.ArchivoLog, $linea + [Environment]::NewLine, [System.Text.Encoding]::UTF8)
    } catch { }
}

function Set-Progreso([double]$Valor) {
    Send-Mensaje @{ Tipo = 'progreso'; Valor = [int][Math]::Max(0, [Math]::Min(100, $Valor)) }
}

function Test-Cancelado { return [bool]$sync.Cancelar }

function Request-Confirmacion([string]$Titulo, [string[]]$Lineas) {
    if (-not $sync.Config.confirmarAntesDeActuar) { return $true }
    $sync.Respuesta = $null
    Send-Mensaje @{ Tipo = 'pregunta'; Titulo = $Titulo; Lineas = $Lineas }
    while ($null -eq $sync.Respuesta) {
        if (Test-Cancelado) { return $false }
        Start-Sleep -Milliseconds 100
    }
    $r = [bool]$sync.Respuesta
    $sync.Respuesta = $null
    return $r
}

function Format-Bytes([double]$Bytes) {
    $neg = $Bytes -lt 0
    $b = [Math]::Abs($Bytes)
    if ($b -ge 1GB) { $s = '{0:N2} GB' -f ($b / 1GB) }
    elseif ($b -ge 1MB) { $s = '{0:N1} MB' -f ($b / 1MB) }
    elseif ($b -ge 1KB) { $s = '{0:N0} KB' -f ($b / 1KB) }
    else { $s = '{0:N0} B' -f $b }
    if ($neg) { return '-' + $s }
    return $s
}

function Format-Corto([string]$Texto, [int]$Max = 52) {
    if ($Texto.Length -le $Max) { return $Texto }
    $mitad = [int](($Max - 3) / 2)
    return $Texto.Substring(0, $mitad) + '...' + $Texto.Substring($Texto.Length - ($Max - 3 - $mitad))
}

function Test-EsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    return (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-EspacioLibre {
    try { return (New-Object System.IO.DriveInfo($env:SystemDrive)).AvailableFreeSpace } catch { return 0 }
}

# Peor estado entre varios: error > cancelado > ok
function Join-Estado([string[]]$Estados) {
    if ($Estados -contains 'error') { return 'error' }
    if ($Estados -contains 'cancelado') { return 'cancelado' }
    return 'ok'
}

# ============================================== 1) PROCESOS EN SEGUNDO PLANO

# Procesos del sistema o del shell: nunca se cierran (además de todo lo que está en C:\Windows).
$script:ProtegidosBase = @(
    'System', 'Idle', 'Registry', 'smss', 'csrss', 'wininit', 'winlogon', 'services', 'lsass', 'lsaiso',
    'svchost', 'dwm', 'explorer', 'sihost', 'fontdrvhost', 'ctfmon', 'taskhostw', 'RuntimeBroker',
    'ShellExperienceHost', 'StartMenuExperienceHost', 'ShellHost', 'SearchHost', 'SearchApp', 'SearchUI',
    'SearchIndexer', 'TextInputHost', 'LockApp', 'SecurityHealthSystray', 'SecurityHealthService',
    'smartscreen', 'ApplicationFrameHost', 'SystemSettings', 'audiodg', 'conhost', 'OpenConsole',
    'WindowsTerminal', 'powershell', 'pwsh', 'powershell_ise', 'cmd', 'wsl', 'wslhost', 'wslservice',
    'ssh-agent', 'dllhost', 'MsMpEng', 'NisSrv', 'MpDefenderCoreService', 'Taskmgr', 'userinit',
    'WUDFHost', 'spoolsv', 'msiexec', 'TrustedInstaller', 'TiWorker', 'MoUsoCoreWorker', 'setup',
    'Magnify', 'Narrator', 'osk', 'nvda', 'ctfmon', 'IMEDICTUPDATE', 'ChsIME', 'InputPersonalization'
)

# Procesos "contenedor": tener ventana no implica que sus hijos sean algo que el usuario usa.
$script:Shells = @(
    'explorer', 'svchost', 'sihost', 'services', 'wininit', 'winlogon', 'userinit', 'RuntimeBroker',
    'ApplicationFrameHost', 'dllhost', 'taskhostw', 'ShellHost', 'StartMenuExperienceHost',
    'ShellExperienceHost', 'smss', 'csrss', 'System'
)

function Test-Patron([string]$Nombre, [object[]]$Patrones) {
    foreach ($p in $Patrones) { if ($Nombre -like [string]$p) { return $true } }
    return $false
}

function Get-RutasProtegidas {
    $rutas = New-Object System.Collections.Generic.List[string]
    $rutas.Add(($env:windir.TrimEnd('\') + '\'))
    foreach ($r in @($sync.Config.procesos.rutasProtegidas)) {
        if ($r) { $rutas.Add([Environment]::ExpandEnvironmentVariables([string]$r)) }
    }
    return $rutas
}

function Get-CandidatosProcesos {
    $cfg = $sync.Config.procesos
    $sesion = (Get-Process -Id $PID).SessionId
    $todos = @(Get-CimInstance -ClassName Win32_Process -Filter "SessionId = $sesion" -ErrorAction Stop)

    $porPid = @{}
    $hijos = @{}
    foreach ($p in $todos) {
        $porPid[[int]$p.ProcessId] = $p
        $padre = [int]$p.ParentProcessId
        if (-not $hijos.ContainsKey($padre)) { $hijos[$padre] = New-Object System.Collections.Generic.List[int] }
        $hijos[$padre].Add([int]$p.ProcessId)
    }

    $patronesUsuario = @($cfg.protegidos)
    $rutasProtegidas = Get-RutasProtegidas
    $protegido = New-Object 'System.Collections.Generic.HashSet[int]'

    # El padre es real solo si nació antes que el hijo (Windows recicla los PID).
    $padreValido = {
        param($p)
        $pp = $porPid[[int]$p.ParentProcessId]
        if ($null -eq $pp) { return $null }
        if ($pp.CreationDate -and $p.CreationDate -and $pp.CreationDate -gt $p.CreationDate) { return $null }
        return $pp
    }

    # --- Anclas: lo que el usuario está usando de verdad
    $anclas = New-Object 'System.Collections.Generic.HashSet[int]'
    foreach ($id in [PanelNativo]::PidsConVentana()) { [void]$anclas.Add($id) }
    $fg = [PanelNativo]::PidPrimerPlano(); if ($fg) { [void]$anclas.Add($fg) }
    $conAudio = @([PanelNativo]::PidsConAudio())
    foreach ($id in $conAudio) { [void]$anclas.Add($id) }
    [void]$anclas.Add($PID)

    # Los ancestros de un proceso que suena o del propio panel también se protegen
    # (p. ej. el Discord.exe principal de una llamada que sale por un subproceso).
    foreach ($id in @($conAudio + $PID)) {
        $p = $porPid[[int]$id]; $n = 0
        while ($p -and $n -lt 64) {
            [void]$protegido.Add([int]$p.ProcessId)
            $p = & $padreValido $p; $n++
        }
    }

    # Raíces cuya descendencia se protege: anclas + protegidos por nombre, salvo shells.
    $cola = New-Object System.Collections.Generic.Queue[int]
    foreach ($p in $todos) {
        $base = [IO.Path]::GetFileNameWithoutExtension([string]$p.Name)
        $id = [int]$p.ProcessId
        $porNombre = (Test-Patron $base $script:ProtegidosBase) -or (Test-Patron $base $patronesUsuario)
        if ($anclas.Contains($id) -or $porNombre) {
            [void]$protegido.Add($id)
            if (-not (Test-Patron $base $script:Shells)) { $cola.Enqueue($id) }
        }
    }
    while ($cola.Count -gt 0) {
        $id = $cola.Dequeue()
        if (-not $hijos.ContainsKey($id)) { continue }
        foreach ($h in $hijos[$id]) {
            $ph = $porPid[$h]
            if ($null -eq (& $padreValido $ph)) { continue }
            if ($protegido.Add($h)) { $cola.Enqueue($h) }
        }
    }

    $minimo = [double]$cfg.memoriaMinimaMB * 1MB
    $candidatos = New-Object System.Collections.Generic.List[object]
    foreach ($p in $todos) {
        $id = [int]$p.ProcessId
        if ($id -le 4 -or $protegido.Contains($id)) { continue }
        $ruta = [string]$p.ExecutablePath
        if (-not $ruta) { continue }  # sin ruta = proceso de otro usuario o protegido: no tocar
        $rutaProtegida = $false
        foreach ($r in $rutasProtegidas) {
            if ($ruta.IndexOf($r, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $rutaProtegida = $true; break }
        }
        if ($rutaProtegida) { continue }
        if ([double]$p.WorkingSetSize -lt $minimo) { continue }
        $candidatos.Add([pscustomobject]@{
            Id      = $id
            Nombre  = [IO.Path]::GetFileNameWithoutExtension([string]$p.Name)
            Ruta    = $ruta
            Memoria = [double]$p.WorkingSetSize
            Inicio  = $p.CreationDate
        })
    }
    return , $candidatos
}

function Invoke-CerrarProcesos {
    Write-Panel 'ESCANEANDO PROCESOS EN SEGUNDO PLANO...'
    Set-Progreso 5
    $lista = @(Get-CandidatosProcesos | ForEach-Object { $_ } | Sort-Object Memoria -Descending)
    Set-Progreso 25
    if ($lista.Count -eq 0) {
        Write-Panel 'NO HAY PROCESOS EN SEGUNDO PLANO PARA CERRAR.' 'ok'
        return 'ok'
    }
    $total = ($lista | Measure-Object Memoria -Sum).Sum
    Write-Panel ('{0} PROCESOS SIN VENTANA NI AUDIO ({1}).' -f $lista.Count, (Format-Bytes $total))

    $lineas = New-Object System.Collections.Generic.List[string]
    foreach ($c in ($lista | Select-Object -First 12)) {
        $lineas.Add(('{0,-34} {1,10}' -f (Format-Corto $c.Nombre 34), (Format-Bytes $c.Memoria)))
    }
    if ($lista.Count -gt 12) { $lineas.Add(('... Y {0} MAS' -f ($lista.Count - 12))) }
    if (-not (Request-Confirmacion ('¿CERRAR {0} PROCESOS ({1})?' -f $lista.Count, (Format-Bytes $total)) $lineas)) {
        Write-Panel 'CIERRE DE PROCESOS CANCELADO.' 'warn'
        return 'cancelado'
    }

    $cerrados = 0; $liberado = 0; $fallos = 0; $i = 0
    foreach ($c in $lista) {
        if (Test-Cancelado) { Write-Panel 'CANCELADO POR EL USUARIO.' 'warn'; return 'cancelado' }
        $i++
        Set-Progreso (25 + 75 * $i / $lista.Count)
        try {
            $vivo = Get-Process -Id $c.Id -ErrorAction Stop
            # Mismo PID pero otro programa (PID reciclado): no tocar.
            if ($vivo.ProcessName -ne $c.Nombre -or ($c.Inicio -and $vivo.StartTime -and [Math]::Abs(($vivo.StartTime - $c.Inicio).TotalSeconds) -gt 2)) { continue }
            Stop-Process -Id $c.Id -Force -ErrorAction Stop
            $cerrados++; $liberado += $c.Memoria
            Write-Panel ('CERRADO: {0} ({1})' -f $c.Nombre, (Format-Bytes $c.Memoria))
        } catch [Microsoft.PowerShell.Commands.ProcessCommandException] {
            # ya había terminado (p. ej. cerramos a su padre)
        } catch {
            $fallos++
            Write-Panel ('NO SE PUDO CERRAR {0}: {1}' -f $c.Nombre, $_.Exception.Message) 'warn'
        }
        Start-Sleep -Milliseconds 40
    }
    Write-Panel ('PROCESOS CERRADOS: {0}  //  RAM LIBERADA: ~{1}' -f $cerrados, (Format-Bytes $liberado)) 'ok'
    if ($cerrados -eq 0 -and $fallos -gt 0) { return 'error' }
    return 'ok'
}

# ===================================================== 2) MEMORIA Y DUPLICADOS

function Invoke-LiberarMemoria([double]$Desde = 0, [double]$Hasta = 100) {
    $antes = [PanelNativo]::Memoria()
    Write-Panel ('RAM DISPONIBLE: {0} DE {1}' -f (Format-Bytes $antes[1]), (Format-Bytes $antes[0]))
    Write-Panel 'COMPACTANDO MEMORIA DE LOS PROCESOS...'
    $procs = @(Get-Process)
    $ok = 0; $i = 0
    foreach ($p in $procs) {
        if (Test-Cancelado) { return 'cancelado' }
        $i++
        if ($i % 10 -eq 0) { Set-Progreso ($Desde + ($Hasta - $Desde) * 0.9 * $i / $procs.Count) }
        if ([PanelNativo]::RecortarMemoria($p.Id)) { $ok++ }
    }
    if ($sync.Config.memoria.purgarListaEnEspera) {
        if (Test-EsAdmin) {
            $r = [PanelNativo]::PurgarListaEspera()
            if ($r -eq 0) { Write-Panel 'LISTA EN ESPERA (CACHE) VACIADA.' }
            else { Write-Panel ('NO SE PUDO VACIAR LA LISTA EN ESPERA (CODIGO {0}).' -f $r) 'warn' }
        } else {
            Write-Panel 'VACIAR LA CACHE EN ESPERA REQUIERE ADMINISTRADOR: OMITIDO.' 'warn'
        }
    }
    Start-Sleep -Milliseconds 800
    $despues = [PanelNativo]::Memoria()
    Set-Progreso $Hasta
    Write-Panel ('MEMORIA COMPACTADA EN {0} PROCESOS. DISPONIBLE: {1} -> {2} ({3})' -f $ok, (Format-Bytes $antes[1]), (Format-Bytes $despues[1]), (Format-Bytes ([double]$despues[1] - [double]$antes[1]))) 'ok'
    return 'ok'
}

function Resolve-Carpeta([string]$Token) {
    switch ($Token) {
        '{Descargas}' {
            try {
                $k = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
                $v = (Get-ItemProperty -Path $k -Name '{374DE290-123F-4565-9164-39C4925E467B}' -ErrorAction Stop).'{374DE290-123F-4565-9164-39C4925E467B}'
                if ($v) { return $v }
            } catch { }
            return (Join-Path $env:USERPROFILE 'Downloads')
        }
        '{Escritorio}' { return [Environment]::GetFolderPath('Desktop') }
        '{Documentos}' { return [Environment]::GetFolderPath('MyDocuments') }
        '{Imagenes}' { return [Environment]::GetFolderPath('MyPictures') }
        '{Videos}' { return [Environment]::GetFolderPath('MyVideos') }
        '{Musica}' { return [Environment]::GetFolderPath('MyMusic') }
        default { return [Environment]::ExpandEnvironmentVariables($Token) }
    }
}

function Get-CarpetasDuplicados {
    $rutas = New-Object System.Collections.Generic.List[string]
    foreach ($t in @($sync.Config.duplicados.carpetas)) {
        $r = Resolve-Carpeta ([string]$t)
        if ($r -and (Test-Path -LiteralPath $r -PathType Container)) {
            $r = (Resolve-Path -LiteralPath $r).ProviderPath.TrimEnd('\', '/')
            if (-not ($rutas -contains $r)) { $rutas.Add($r) }
        }
    }
    # Si una carpeta está dentro de otra, se escanea una sola vez.
    $final = New-Object System.Collections.Generic.List[string]
    foreach ($r in $rutas) {
        $anidada = $false
        foreach ($o in $rutas) {
            if ($o -ne $r -and $r.StartsWith($o + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { $anidada = $true; break }
        }
        if (-not $anidada) { $final.Add($r) }
    }
    return , $final
}

function Get-ArchivosEscaneables([string]$Raiz, [System.Collections.Generic.List[System.IO.FileInfo]]$Salida) {
    $cfg = $sync.Config.duplicados
    $excluidas = @($cfg.carpetasExcluidas)
    $extExcluidas = @($cfg.extensionesExcluidas | ForEach-Object { ([string]$_).ToLowerInvariant() })
    $minimo = [long]([double]$cfg.tamanoMinimoKB * 1KB)
    $omitirProyectos = [bool]$cfg.omitirRepositoriosYProyectos
    # Oculto(2) | Sistema(4) | ReparsePoint(0x400) | Offline(0x1000) | RecallOnOpen(0x40000) | RecallOnDataAccess(0x400000)
    $mascaraArchivo = 0x2 -bor 0x4 -bor 0x400 -bor 0x1000 -bor 0x40000 -bor 0x400000
    $mascaraCarpeta = 0x2 -bor 0x4 -bor 0x400

    $pila = New-Object System.Collections.Generic.Stack[string]
    $pila.Push($Raiz)
    while ($pila.Count -gt 0) {
        if (Test-Cancelado) { return }
        $dir = New-Object System.IO.DirectoryInfo($pila.Pop())
        try { $subs = $dir.GetDirectories() } catch { continue }
        # Una carpeta con .git es un proyecto: sus "duplicados" suelen ser intencionales.
        if ($omitirProyectos -and ($subs | Where-Object { $_.Name -eq '.git' -or $_.Name -eq '.svn' })) { continue }
        foreach ($s in $subs) {
            if (([int]$s.Attributes -band $mascaraCarpeta) -ne 0) { continue }
            if (Test-Patron $s.Name $excluidas) { continue }
            $pila.Push($s.FullName)
        }
        try { $archivos = $dir.GetFiles() } catch { continue }
        foreach ($f in $archivos) {
            if (([int]$f.Attributes -band $mascaraArchivo) -ne 0) { continue }
            if ($f.Length -lt $minimo) { continue }
            if ($extExcluidas -contains $f.Extension.ToLowerInvariant()) { continue }
            $Salida.Add($f)
        }
    }
}

$script:Sha = [System.Security.Cryptography.SHA256]::Create()

function Get-Huella([string]$Ruta, [long]$MaxBytes = -1) {
    $fs = $null
    try {
        $fs = New-Object System.IO.FileStream($Ruta, [IO.FileMode]::Open, [IO.FileAccess]::Read, ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete), 1MB)
        if ($MaxBytes -gt 0) {
            $buf = New-Object byte[] $MaxBytes
            $leidos = 0
            while ($leidos -lt $MaxBytes) {
                $n = $fs.Read($buf, $leidos, $MaxBytes - $leidos)
                if ($n -le 0) { break }
                $leidos += $n
            }
            $h = $script:Sha.ComputeHash($buf, 0, $leidos)
        } else {
            $h = $script:Sha.ComputeHash($fs)
        }
        return [BitConverter]::ToString($h).Replace('-', '')
    } catch {
        return $null
    } finally {
        if ($fs) { $fs.Dispose() }
    }
}

# Agrupa una lista de archivos por una clave; devuelve solo los grupos con 2 o más.
function Group-PorClave($Archivos, [scriptblock]$Clave) {
    $grupos = @{}
    foreach ($f in $Archivos) {
        $k = & $Clave $f
        if ($null -eq $k) { continue }
        if (-not $grupos.ContainsKey($k)) { $grupos[$k] = New-Object System.Collections.Generic.List[object] }
        $grupos[$k].Add($f)
    }
    $r = New-Object System.Collections.Generic.List[object]
    foreach ($g in $grupos.Values) { if ($g.Count -gt 1) { $r.Add($g) } }
    return , $r
}

# Cuál conservar: el que no parece copia ("(1)", "- copia", "Copy of"...), luego el más antiguo.
function Select-Original($Grupo) {
    $patronCopia = '(?i)(\s\(\d+\)|\s-\s(copia|copy)(\s\(\d+\))?|[\s_-](copia|copy)\d*|^(copia de|copy of)\s)'
    return $Grupo | Sort-Object `
        @{ Expression = { if ([IO.Path]::GetFileNameWithoutExtension($_.Name) -match $patronCopia) { 1 } else { 0 } } }, `
        @{ Expression = { $_.CreationTimeUtc } }, `
        @{ Expression = { $_.FullName.Length } } | Select-Object -First 1
}

function Invoke-Duplicados([double]$Desde = 0, [double]$Hasta = 100) {
    $carpetas = Get-CarpetasDuplicados
    if ($carpetas.Count -eq 0) { Write-Panel 'NO HAY CARPETAS PARA REVISAR.' 'warn'; return 'ok' }
    $rango = $Hasta - $Desde
    $archivos = New-Object System.Collections.Generic.List[System.IO.FileInfo]
    $i = 0
    foreach ($c in $carpetas) {
        $i++
        Write-Panel ('ESCANEANDO: {0}' -f (Format-Corto $c 60))
        Get-ArchivosEscaneables $c $archivos
        if (Test-Cancelado) { Write-Panel 'CANCELADO POR EL USUARIO.' 'warn'; return 'cancelado' }
        Set-Progreso ($Desde + $rango * 0.15 * $i / $carpetas.Count)
    }
    # Por si una misma carpeta llegó por dos caminos (enlaces, rutas repetidas): cada archivo una vez.
    $vistos = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $unicos = New-Object System.Collections.Generic.List[System.IO.FileInfo]
    foreach ($f in $archivos) { if ($vistos.Add($f.FullName)) { $unicos.Add($f) } }
    $archivos = $unicos
    Write-Panel ('{0} ARCHIVOS ANALIZADOS.' -f $archivos.Count)

    # 1) mismo tamaño  2) misma huella de los primeros 64 KB  3) mismo SHA-256 completo
    $porTamano = Group-PorClave $archivos { param($f) $f.Length }
    $sospechosos = 0; foreach ($g in $porTamano) { $sospechosos += $g.Count }
    Write-Panel ('{0} ARCHIVOS CON TAMANO REPETIDO. COMPARANDO CONTENIDO...' -f $sospechosos)

    $grupos = New-Object System.Collections.Generic.List[object]
    $hechos = 0
    foreach ($g in $porTamano) {
        if (Test-Cancelado) { Write-Panel 'CANCELADO POR EL USUARIO.' 'warn'; return 'cancelado' }
        $porParcial = Group-PorClave $g { param($f) Get-Huella $f.FullName 65536 }
        foreach ($gp in $porParcial) {
            if ($gp[0].Length -le 65536) { $grupos.Add($gp); continue }  # la huella parcial ya es total
            foreach ($gc in (Group-PorClave $gp { param($f) Get-Huella $f.FullName })) { $grupos.Add($gc) }
        }
        $hechos += $g.Count
        Set-Progreso ($Desde + $rango * (0.15 + 0.6 * $hechos / [Math]::Max(1, $sospechosos)))
    }

    if ($grupos.Count -eq 0) {
        Write-Panel 'NO SE ENCONTRARON ARCHIVOS DUPLICADOS.' 'ok'
        Set-Progreso $Hasta
        return 'ok'
    }

    $aBorrar = New-Object System.Collections.Generic.List[object]
    foreach ($g in $grupos) {
        $orig = Select-Original $g
        foreach ($f in $g) {
            if ($f.FullName -ne $orig.FullName) { $aBorrar.Add([pscustomobject]@{ Archivo = $f; Original = $orig }) }
        }
    }
    $total = 0.0; foreach ($d in $aBorrar) { $total += $d.Archivo.Length }

    # Informe CSV para poder revisar (y recuperar desde la Papelera) lo que se movió.
    $informe = Join-Path (Split-Path $sync.ArchivoLog) ('duplicados_{0:yyyyMMdd_HHmmss}.csv' -f (Get-Date))
    try {
        $aBorrar | ForEach-Object {
            [pscustomobject]@{ Duplicado = $_.Archivo.FullName; Conservado = $_.Original.FullName; Bytes = $_.Archivo.Length }
        } | Export-Csv -LiteralPath $informe -NoTypeInformation -Encoding UTF8 -Delimiter ';'
    } catch { $informe = $null }

    $lineas = New-Object System.Collections.Generic.List[string]
    foreach ($d in ($aBorrar | Sort-Object { $_.Archivo.Length } -Descending | Select-Object -First 10)) {
        $lineas.Add(('{0,9}  {1}' -f (Format-Bytes $d.Archivo.Length), (Format-Corto $d.Archivo.FullName 54)))
    }
    if ($aBorrar.Count -gt 10) { $lineas.Add(('... Y {0} MAS' -f ($aBorrar.Count - 10))) }
    $lineas.Add('')
    $lineas.Add('SE CONSERVA SIEMPRE UNA COPIA. LO DEMAS VA A LA PAPELERA.')
    if ($informe) { $lineas.Add(('LISTA COMPLETA: {0}' -f (Format-Corto $informe 54))) }

    if (-not (Request-Confirmacion ('¿MOVER {0} DUPLICADOS ({1}) A LA PAPELERA?' -f $aBorrar.Count, (Format-Bytes $total)) $lineas)) {
        Write-Panel 'BORRADO DE DUPLICADOS CANCELADO.' 'warn'
        return 'cancelado'
    }

    $movidos = 0; $recuperado = 0.0; $fallos = 0; $i = 0
    foreach ($d in $aBorrar) {
        if (Test-Cancelado) { Write-Panel 'CANCELADO POR EL USUARIO.' 'warn'; return 'cancelado' }
        $i++
        Set-Progreso ($Desde + $rango * (0.75 + 0.25 * $i / $aBorrar.Count))
        # Re-verificar justo antes: que ambos sigan existiendo y sean idénticos.
        $d.Archivo.Refresh(); $d.Original.Refresh()
        if (-not $d.Archivo.Exists -or -not $d.Original.Exists -or $d.Archivo.Length -ne $d.Original.Length) { continue }
        $r = [PanelNativo]::APapelera($d.Archivo.FullName)
        if ($r -eq 0) {
            $movidos++; $recuperado += $d.Archivo.Length
        } else {
            $fallos++
            Write-Panel ('NO SE PUDO MOVER {0} (CODIGO {1})' -f $d.Archivo.Name, $r) 'warn'
        }
    }
    Write-Panel ('DUPLICADOS A LA PAPELERA: {0}  //  ESPACIO: {1}' -f $movidos, (Format-Bytes $recuperado)) 'ok'
    Write-Panel 'EL ESPACIO SE LIBERA DEL TODO AL VACIAR LA PAPELERA.'
    if ($movidos -eq 0 -and $fallos -gt 0) { return 'error' }
    return 'ok'
}

function Invoke-MemoriaYDuplicados {
    $e1 = Invoke-Duplicados 0 70
    if ($e1 -eq 'cancelado' -and (Test-Cancelado)) { return 'cancelado' }
    $e2 = Invoke-LiberarMemoria 70 100
    return (Join-Estado @($e1, $e2))
}

# ===================================================== 3) OPTIMIZACIÓN GENERAL

function Remove-ArchivosViejos([string]$Carpeta, [int]$Dias) {
    $res = @{ Bytes = 0.0; Cantidad = 0 }
    if (-not $Carpeta -or -not (Test-Path -LiteralPath $Carpeta)) { return $res }
    $limite = (Get-Date).AddDays(-$Dias)
    $archivos = @(Get-ChildItem -LiteralPath $Carpeta -Recurse -Force -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $limite -and (([int]$_.Attributes -band 0x400) -eq 0) })
    foreach ($f in $archivos) {
        if (Test-Cancelado) { break }
        try {
            $len = $f.Length
            Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop
            $res.Bytes += $len; $res.Cantidad++
        } catch { }  # en uso por algún programa: se deja
    }
    # Carpetas que quedaron vacías (de la más profunda a la menos).
    Get-ChildItem -LiteralPath $Carpeta -Recurse -Force -Directory -ErrorAction SilentlyContinue |
        Sort-Object { $_.FullName.Length } -Descending |
        ForEach-Object {
            try {
                if (-not (Get-ChildItem -LiteralPath $_.FullName -Force -ErrorAction Stop | Select-Object -First 1)) {
                    Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop
                }
            } catch { }
        }
    return $res
}

function Invoke-OptimizacionGeneral {
    $cfg = $sync.Config.general
    $admin = Test-EsAdmin
    $libreAntes = Get-EspacioLibre
    $dias = [int]$cfg.diasMinimosTemporales
    $estados = New-Object System.Collections.Generic.List[string]
    if (-not $admin) { Write-Panel 'MODO USUARIO: LOS PASOS DE ADMINISTRADOR SE OMITEN (TECLA A).' 'warn' }

    if ($cfg.limpiarTemporales) {
        Write-Panel 'LIMPIANDO ARCHIVOS TEMPORALES...'
        $r = Remove-ArchivosViejos $env:TEMP $dias
        Write-Panel ('TEMP DE USUARIO: {0} ARCHIVOS, {1}' -f $r.Cantidad, (Format-Bytes $r.Bytes))
        if ($admin) {
            $r = Remove-ArchivosViejos (Join-Path $env:windir 'Temp') $dias
            Write-Panel ('TEMP DE WINDOWS: {0} ARCHIVOS, {1}' -f $r.Cantidad, (Format-Bytes $r.Bytes))
        }
    }
    Set-Progreso 20
    if (Test-Cancelado) { return 'cancelado' }

    if ($cfg.limpiarInformesDeError) {
        $total = 0.0
        foreach ($c in @(
                (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\WER\ReportArchive'),
                (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\WER\ReportQueue'),
                (Join-Path $env:LOCALAPPDATA 'CrashDumps'))) {
            $total += (Remove-ArchivosViejos $c 0).Bytes
        }
        if ($admin) {
            foreach ($c in @(
                    (Join-Path $env:ProgramData 'Microsoft\Windows\WER\ReportArchive'),
                    (Join-Path $env:ProgramData 'Microsoft\Windows\WER\ReportQueue'))) {
                $total += (Remove-ArchivosViejos $c 0).Bytes
            }
        }
        Write-Panel ('INFORMES DE ERROR Y VOLCADOS: {0}' -f (Format-Bytes $total))
    }
    Set-Progreso 35

    if ($admin -and (Get-Command Delete-DeliveryOptimizationCache -ErrorAction SilentlyContinue)) {
        try {
            Delete-DeliveryOptimizationCache -Force -ErrorAction Stop | Out-Null
            Write-Panel 'CACHE DE OPTIMIZACION DE DISTRIBUCION (WINDOWS UPDATE) VACIADA.'
        } catch { Write-Panel ('CACHE DE ACTUALIZACIONES: {0}' -f $_.Exception.Message) 'warn' }
    }
    Set-Progreso 45

    if ($cfg.vaciarCacheDNS) {
        try {
            & "$env:windir\System32\ipconfig.exe" /flushdns | Out-Null
            Write-Panel 'CACHE DNS VACIADA.'
        } catch { Write-Panel 'NO SE PUDO VACIAR LA CACHE DNS.' 'warn' }
    }
    Set-Progreso 50
    if (Test-Cancelado) { return 'cancelado' }

    $estados.Add((Invoke-LiberarMemoria 50 70))

    if ($cfg.optimizarDisco) {
        if ($admin) {
            $letra = $env:SystemDrive.Substring(0, 1)
            try {
                Write-Panel ('OPTIMIZANDO UNIDAD {0}: (TRIM)...' -f $letra)
                Optimize-Volume -DriveLetter $letra -ReTrim -ErrorAction Stop
                Write-Panel 'TRIM COMPLETADO (SSD).'
            } catch {
                if ($cfg.desfragmentarHDD) {
                    Write-Panel 'DISCO MECANICO: DESFRAGMENTANDO (PUEDE TARDAR)...' 'warn'
                    try { Optimize-Volume -DriveLetter $letra -Defrag -ErrorAction Stop; Write-Panel 'DESFRAGMENTACION COMPLETA.' }
                    catch { Write-Panel ('OPTIMIZAR DISCO: {0}' -f $_.Exception.Message) 'warn' }
                } else {
                    Write-Panel 'EL DISCO NO ADMITE TRIM (HDD). DESFRAGMENTAR: VER config.json.' 'warn'
                }
            }
        } else {
            Write-Panel 'OPTIMIZAR DISCO REQUIERE ADMINISTRADOR: OMITIDO.' 'warn'
        }
    }
    Set-Progreso 90

    # Diagnóstico: lo que más pesa en el arranque no se puede "optimizar" desde acá sin riesgo.
    try {
        $inicio = @(Get-CimInstance -ClassName Win32_StartupCommand -ErrorAction Stop)
        if ($inicio.Count -gt 0) {
            Write-Panel ('{0} PROGRAMAS ARRANCAN CON WINDOWS. REVISALOS EN ADMINISTRADOR DE TAREAS > INICIO.' -f $inicio.Count)
        }
    } catch { }
    try {
        $plan = (& "$env:windir\System32\powercfg.exe" /getactivescheme) -join ' '
        if ($plan -match '\(([^)]+)\)') { Write-Panel ('PLAN DE ENERGIA ACTIVO: {0}' -f $Matches[1].ToUpper()) }
    } catch { }

    $libreDespues = Get-EspacioLibre
    Set-Progreso 100
    Write-Panel ('ESPACIO LIBRE EN {0} {1} -> {2} ({3})' -f $env:SystemDrive, (Format-Bytes $libreAntes), (Format-Bytes $libreDespues), (Format-Bytes ($libreDespues - $libreAntes))) 'ok'
    return (Join-Estado $estados)
}

# ================================================================= despacho

function Invoke-Tarea([string]$Id) {
    $sync.Cancelar = $false
    Send-Mensaje @{ Tipo = 'inicio'; Id = $Id }
    $estado = 'error'
    try {
        $salida = switch ($Id) {
            'procesos' { Invoke-CerrarProcesos }
            'memoria' { Invoke-MemoriaYDuplicados }
            'general' { Invoke-OptimizacionGeneral }
        }
        # La última cadena devuelta es el estado (por si algo más escribió en la salida).
        $estado = @($salida | Where-Object { $_ -is [string] })[-1]
        if (-not $estado) { $estado = 'error' }
    } catch {
        Write-Panel ('FALLA: {0}' -f $_.Exception.Message) 'error'
        $estado = 'error'
    }
    Send-Mensaje @{ Tipo = 'fin'; Id = $Id; Estado = $estado }
    return $estado
}

function Invoke-Secuencia([string[]]$Ids) {
    foreach ($id in $Ids) {
        $e = Invoke-Tarea $id
        if ($e -eq 'cancelado' -and $sync.Cancelar) { break }
    }
    Send-Mensaje @{ Tipo = 'terminado' }
}
