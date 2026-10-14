<#
    PANEL DE MANTENIMIENTO
    Panel estilo "monitor de mantenimiento" (homenaje a FNAF 3) que de verdad optimiza Windows:
      1. PROCESOS EN 2DO PLANO  -> cierra procesos sin ventana ni audio (no toca lo que estás usando)
      2. MEMORIA Y DUPLICADOS   -> manda archivos duplicados a la Papelera y compacta la RAM
      3. OPTIMIZACIÓN GENERAL   -> temporales, informes de error, DNS, RAM, TRIM del disco
      4. REINICIAR TODO         -> los tres en secuencia

    Requiere Windows 10/11 con Windows PowerShell 5.1 (ya viene instalado).
    Se ejecuta desde el acceso directo que crea Instalar.bat.
#>
param()

$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$EsteScript = $MyInvocation.MyCommand.Path

# WPF necesita un hilo STA (powershell.exe 5.1 lo es por defecto; pwsh 7 puede no serlo).
if ([Threading.Thread]::CurrentThread.ApartmentState -ne 'STA') {
    Start-Process -FilePath "$env:windir\System32\WindowsPowerShell\v1.0\powershell.exe" `
        -ArgumentList @('-NoProfile', '-STA', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', "`"$EsteScript`"")
    exit
}

# Una sola instancia a la vez.
$instanciaNueva = $false
$script:mutex = New-Object System.Threading.Mutex($true, 'Local\PanelMantenimientoFNAF3', [ref]$instanciaNueva)
if (-not $instanciaNueva) { exit }

Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase
$DirRegistros = Join-Path $env:LOCALAPPDATA 'PanelMantenimiento\registros'
[void](New-Item -ItemType Directory -Path $DirRegistros -Force)
$ArchivoLog = Join-Path $DirRegistros ('{0:yyyy-MM-dd}.log' -f (Get-Date))

function Show-ErrorFatal([string]$Texto) {
    try { [IO.File]::AppendAllText($ArchivoLog, ('{0:yyyy-MM-dd HH:mm:ss} [FATAL] {1}{2}' -f (Get-Date), $Texto, [Environment]::NewLine)) } catch { }
    [void][System.Windows.MessageBox]::Show("El panel no pudo iniciar:`n`n$Texto`n`nRegistro: $ArchivoLog", 'Panel de Mantenimiento', 'OK', 'Error')
}

try {
    if (-not ('PanelNativo' -as [type])) {
        Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $Raiz 'modulos\Nativo.cs'))) -Language CSharp
    }
    [PanelNativo]::OcultarConsola()
    [PanelNativo]::FijarIdentidadBarra('Planck.PanelMantenimiento')
    $Config = [IO.File]::ReadAllText((Join-Path $Raiz 'config.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json
} catch {
    Show-ErrorFatal $_.Exception.Message
    exit 1
}

$EsAdmin = (New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# =============================================================== trabajo de fondo

$sync = [hashtable]::Synchronized(@{})
$sync.Cola = New-Object 'System.Collections.Concurrent.ConcurrentQueue[object]'
$sync.Respuesta = $null
$sync.Cancelar = $false
$sync.Config = $Config
$sync.ArchivoLog = $ArchivoLog

$script:rs = [runspacefactory]::CreateRunspace()
$script:rs.ApartmentState = 'STA'   # las operaciones de shell (Papelera) prefieren STA
$script:rs.ThreadOptions = 'ReuseThread'
$script:rs.Open()
$script:rs.SessionStateProxy.SetVariable('sync', $sync)
$init = [PowerShell]::Create()
$init.Runspace = $script:rs
# Se pasa el contenido (no la ruta) para no depender de la política de ejecución del runspace.
[void]$init.AddScript([IO.File]::ReadAllText((Join-Path $Raiz 'modulos\Tareas.ps1'), [Text.Encoding]::UTF8), $false)
[void]$init.Invoke()
if ($init.Streams.Error.Count -gt 0) { Show-ErrorFatal ('Tareas.ps1: ' + $init.Streams.Error[0].ToString()); exit 1 }
$init.Dispose()
$script:trabajo = $null

# ======================================================================= XAML

[xml]$xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Panel de Mantenimiento" Width="1040" Height="680"
        WindowStyle="None" AllowsTransparency="False" Background="#FF0A0B0A"
        ResizeMode="NoResize" WindowStartupLocation="CenterScreen"
        FontFamily="Consolas, Lucida Console, Courier New" UseLayoutRounding="True"
        TextOptions.TextFormattingMode="Display" ShowInTaskbar="True">
  <Border x:Name="Bisel" CornerRadius="34" Padding="26" BorderThickness="3">
    <Border.Background>
      <LinearGradientBrush StartPoint="0,0" EndPoint="0,1">
        <GradientStop Color="#FF2A2D2A" Offset="0"/>
        <GradientStop Color="#FF151715" Offset="0.5"/>
        <GradientStop Color="#FF0D0E0D" Offset="1"/>
      </LinearGradientBrush>
    </Border.Background>
    <Border.BorderBrush>
      <LinearGradientBrush StartPoint="0,0" EndPoint="0,1">
        <GradientStop Color="#FF4A4F4A" Offset="0"/>
        <GradientStop Color="#FF1A1C1A" Offset="1"/>
      </LinearGradientBrush>
    </Border.BorderBrush>
    <Grid>
      <!-- LED de encendido en el bisel -->
      <Ellipse x:Name="Led" Width="9" Height="9" Fill="#FF2BFF5A" HorizontalAlignment="Right" VerticalAlignment="Bottom" Margin="0,0,6,-20">
        <Ellipse.Effect><DropShadowEffect Color="#FF2BFF5A" BlurRadius="10" ShadowDepth="0"/></Ellipse.Effect>
      </Ellipse>
      <Grid x:Name="Pantalla" RenderTransformOrigin="0.5,0.5">
        <Grid.RenderTransform><ScaleTransform x:Name="EscalaCRT" ScaleX="0" ScaleY="0.01"/></Grid.RenderTransform>
        <Rectangle>
          <Rectangle.Fill>
            <RadialGradientBrush Center="0.5,0.5" GradientOrigin="0.5,0.5" RadiusX="0.75" RadiusY="0.75">
              <GradientStop Color="#FF0C2412" Offset="0"/>
              <GradientStop Color="#FF061209" Offset="0.6"/>
              <GradientStop Color="#FF010402" Offset="1"/>
            </RadialGradientBrush>
          </Rectangle.Fill>
        </Rectangle>

        <Grid x:Name="Contenido" Margin="40,28,40,22" Opacity="0">
          <Grid.RenderTransform><TranslateTransform x:Name="Sacudida"/></Grid.RenderTransform>
          <Grid.Effect><DropShadowEffect Color="#FF6CFF7E" BlurRadius="9" ShadowDepth="0" Opacity="0.8"/></Grid.Effect>
          <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
          </Grid.RowDefinitions>

          <Grid x:Name="Cabecera" Grid.Row="0" Background="Transparent">
            <TextBlock x:Name="Titulo" Text="PANEL DE MANTENIMIENTO" FontSize="34" FontWeight="Bold" Foreground="#FFC8FFCC"/>
            <StackPanel HorizontalAlignment="Right" VerticalAlignment="Center">
              <TextBlock x:Name="Reloj" Text="--:--" FontSize="26" Foreground="#FFC8FFCC" HorizontalAlignment="Right"/>
              <TextBlock x:Name="Modo" Text="" FontSize="13" HorizontalAlignment="Right"/>
            </StackPanel>
          </Grid>
          <TextBlock x:Name="Subtitulo" Grid.Row="1" FontSize="14" Foreground="#FF5FA868" Margin="2,2,0,10"/>
          <Rectangle Grid.Row="2" Height="2" Fill="#995FA868" Margin="0,0,0,16"/>

          <Grid Grid.Row="3">
            <Grid.ColumnDefinitions>
              <ColumnDefinition Width="300"/>
              <ColumnDefinition Width="28"/>
              <ColumnDefinition Width="*"/>
            </Grid.ColumnDefinitions>
            <StackPanel Grid.Column="0">
              <TextBlock Text="ALERTAS" FontSize="15" Foreground="#FF5FA868" Margin="0,0,0,6"/>
              <StackPanel x:Name="Alertas" MinHeight="110"/>
              <TextBlock Text="ESTADO DEL SISTEMA" FontSize="15" Foreground="#FF5FA868" Margin="0,18,0,6"/>
              <TextBlock x:Name="Estadisticas" FontSize="15" Foreground="#FFB4FFBC" LineHeight="22"/>
            </StackPanel>
            <Rectangle Grid.Column="1" Width="2" Fill="#555FA868" HorizontalAlignment="Center"/>
            <StackPanel Grid.Column="2" Margin="12,0,0,0">
              <TextBlock Text="REINICIO DE SISTEMAS" FontSize="15" Foreground="#FF5FA868" Margin="0,0,0,8"/>
              <StackPanel x:Name="Menu"/>
              <TextBlock x:Name="Descripcion" FontSize="14" Foreground="#FF5FA868" Margin="40,12,0,0" TextWrapping="Wrap"/>
            </StackPanel>
          </Grid>

          <Border Grid.Row="4" BorderBrush="#665FA868" BorderThickness="0,2,0,0" Margin="0,12,0,6" Padding="0,8,0,0">
            <StackPanel x:Name="Registro" Height="158" ClipToBounds="True"/>
          </Border>
          <TextBlock x:Name="Ayuda" Grid.Row="5" FontSize="13" Foreground="#FF4F8F57"
                     Text="&#x2191;&#x2193; ELEGIR   ENTER REINICIAR   C CANCELAR   M SONIDO   A ADMIN   ESC SALIR"/>
        </Grid>

        <!-- Capas de efecto CRT (no reciben clics) -->
        <Image x:Name="Ruido" Stretch="Fill" Opacity="0.06" IsHitTestVisible="False" RenderOptions.BitmapScalingMode="NearestNeighbor"/>
        <Rectangle IsHitTestVisible="False">
          <Rectangle.Fill>
            <DrawingBrush TileMode="Tile" Viewport="0,0,4,4" ViewportUnits="Absolute" Viewbox="0,0,4,4" ViewboxUnits="Absolute">
              <DrawingBrush.Drawing>
                <DrawingGroup>
                  <GeometryDrawing Brush="#00000000"><GeometryDrawing.Geometry><RectangleGeometry Rect="0,0,4,4"/></GeometryDrawing.Geometry></GeometryDrawing>
                  <GeometryDrawing Brush="#55000000"><GeometryDrawing.Geometry><RectangleGeometry Rect="0,0,4,2"/></GeometryDrawing.Geometry></GeometryDrawing>
                </DrawingGroup>
              </DrawingBrush.Drawing>
            </DrawingBrush>
          </Rectangle.Fill>
        </Rectangle>
        <Rectangle x:Name="Banda" Height="140" VerticalAlignment="Top" IsHitTestVisible="False">
          <Rectangle.RenderTransform><TranslateTransform x:Name="BandaY" Y="-140"/></Rectangle.RenderTransform>
          <Rectangle.Fill>
            <LinearGradientBrush StartPoint="0,0" EndPoint="0,1">
              <GradientStop Color="#00B4FFBC" Offset="0"/>
              <GradientStop Color="#14B4FFBC" Offset="0.5"/>
              <GradientStop Color="#00B4FFBC" Offset="1"/>
            </LinearGradientBrush>
          </Rectangle.Fill>
        </Rectangle>
        <Rectangle IsHitTestVisible="False">
          <Rectangle.Fill>
            <RadialGradientBrush Center="0.5,0.5" GradientOrigin="0.5,0.5" RadiusX="0.72" RadiusY="0.72">
              <GradientStop Color="#00000000" Offset="0.55"/>
              <GradientStop Color="#C0000000" Offset="1"/>
            </RadialGradientBrush>
          </Rectangle.Fill>
        </Rectangle>
        <Rectangle x:Name="Destello" Fill="#FFE8FFEA" Opacity="0" IsHitTestVisible="False"/>

        <!-- Diálogo de confirmación -->
        <Border x:Name="Dialogo" Visibility="Collapsed" Width="720" HorizontalAlignment="Center" VerticalAlignment="Center"
                Background="#F2030A05" BorderBrush="#FFFFC34D" BorderThickness="2" Padding="26,20">
          <Border.Effect><DropShadowEffect Color="#FFFFC34D" BlurRadius="18" ShadowDepth="0" Opacity="0.6"/></Border.Effect>
          <StackPanel>
            <TextBlock x:Name="DialogoTitulo" FontSize="22" FontWeight="Bold" Foreground="#FFFFC34D" TextWrapping="Wrap"/>
            <Rectangle Height="2" Fill="#66FFC34D" Margin="0,10,0,10"/>
            <TextBlock x:Name="DialogoTexto" FontSize="14" Foreground="#FFB4FFBC" LineHeight="19"/>
            <StackPanel Orientation="Horizontal" HorizontalAlignment="Center" Margin="0,18,0,0">
              <Border x:Name="BotonSi" BorderBrush="#FFB4FFBC" BorderThickness="2" Padding="22,6" Margin="0,0,30,0" Cursor="Hand" Background="#01000000">
                <TextBlock Text="[S] SI, PROCEDER" FontSize="18" Foreground="#FFB4FFBC"/>
              </Border>
              <Border x:Name="BotonNo" BorderBrush="#FFFF3B3B" BorderThickness="2" Padding="22,6" Cursor="Hand" Background="#01000000">
                <TextBlock Text="[N] NO" FontSize="18" Foreground="#FFFF3B3B"/>
              </Border>
            </StackPanel>
          </StackPanel>
        </Border>
      </Grid>
    </Grid>
  </Border>
</Window>
'@

$ventana = [Windows.Markup.XamlReader]::Load((New-Object System.Xml.XmlNodeReader $xaml))
foreach ($n in 'Bisel', 'Led', 'Pantalla', 'EscalaCRT', 'Contenido', 'Sacudida', 'Cabecera', 'Reloj', 'Modo', 'Subtitulo',
    'Alertas', 'Estadisticas', 'Menu', 'Descripcion', 'Registro', 'Ruido', 'BandaY', 'Destello',
    'Dialogo', 'DialogoTitulo', 'DialogoTexto', 'BotonSi', 'BotonNo') {
    Set-Variable -Name $n -Value $ventana.FindName($n) -Scope Script
}
try { $ventana.Icon = [Windows.Media.Imaging.BitmapFrame]::Create((New-Object Uri (Join-Path $Raiz 'recursos\icono.ico'))) } catch { }

# ===================================================================== colores

function New-Pincel([string]$Hex) {
    $b = New-Object Windows.Media.SolidColorBrush ([Windows.Media.ColorConverter]::ConvertFromString($Hex))
    $b.Freeze()
    return $b
}
$C = @{
    Verde    = New-Pincel '#FFB4FFBC'
    Brillo   = New-Pincel '#FFE4FFE6'
    Tenue    = New-Pincel '#FF5FA868'
    Oscuro   = New-Pincel '#FF2F5A35'
    Rojo     = New-Pincel '#FFFF3B3B'
    Ambar    = New-Pincel '#FFFFC34D'
    SelFondo = New-Pincel '#2A6CFF7E'
    Nada     = New-Pincel '#01000000'
}

$Subtitulo.Text = ('SISTEMA: {0}   //   USUARIO: {1}   //   v1.0' -f $env:COMPUTERNAME, $env:USERNAME).ToUpper()
if ($EsAdmin) { $Modo.Text = 'MODO ADMINISTRADOR'; $Modo.Foreground = $C.Ambar }
else { $Modo.Text = 'MODO USUARIO'; $Modo.Foreground = $C.Tenue }

# ======================================================================= sonido

$DirSonidos = Join-Path $Raiz 'recursos\sonidos'
$script:silencio = -not [bool]$Config.sonido.activado
$script:volumen = [double]$Config.sonido.volumen
$script:reproductores = New-Object System.Collections.ArrayList
$script:ambiente = $null

function Play-Sonido([string]$Nombre, [double]$Vol = 1.0) {
    if ($script:silencio) { return }
    try {
        $mp = New-Object System.Windows.Media.MediaPlayer
        $mp.Volume = [Math]::Min(1.0, $script:volumen * $Vol)
        $mp.Open((New-Object Uri (Join-Path $DirSonidos "$Nombre.wav")))
        $mp.Play()
        [void]$script:reproductores.Add(@{ P = $mp; T = [DateTime]::Now })
    } catch { }
}

function Start-Ambiente {
    if ($script:silencio -or -not $Config.sonido.ambiente) { return }
    try {
        if (-not $script:ambiente) {
            $script:ambiente = New-Object System.Windows.Media.MediaPlayer
            $script:ambiente.Open((New-Object Uri (Join-Path $DirSonidos 'ambiente.wav')))
            $script:ambiente.Add_MediaEnded({ $script:ambiente.Position = [TimeSpan]::Zero; $script:ambiente.Play() })
        }
        $script:ambiente.Volume = $script:volumen * 0.35
        $script:ambiente.Play()
    } catch { }
}

function Stop-Ambiente { if ($script:ambiente) { try { $script:ambiente.Pause() } catch { } } }

# ================================================================ programador
# Pequeña cola de eventos con demora, procesada por el temporizador de animación.

$script:eventos = New-Object System.Collections.ArrayList
function Invoke-Luego([int]$Ms, [scriptblock]$Accion) {
    [void]$script:eventos.Add(@{ Cuando = [DateTime]::Now.AddMilliseconds($Ms); Accion = $Accion })
}

function Start-Animacion($Objeto, $Propiedad, [double]$Hasta, [int]$Ms, [int]$DemoraMs = 0) {
    $a = New-Object System.Windows.Media.Animation.DoubleAnimation
    $a.To = $Hasta
    $a.Duration = New-Object System.Windows.Duration ([TimeSpan]::FromMilliseconds($Ms))
    $a.BeginTime = [TimeSpan]::FromMilliseconds($DemoraMs)
    $Objeto.BeginAnimation($Propiedad, $a)
}

# ========================================================================= menú

$script:items = @(
    @{ Id = 'procesos'; Texto = 'PROCESOS EN 2DO PLANO'; Desc = 'CIERRA PROGRAMAS QUE CORREN SIN VENTANA NI AUDIO. NO TOCA LO QUE ESTAS USANDO, EL SISTEMA NI LOS DRIVERS.' }
    @{ Id = 'memoria'; Texto = 'MEMORIA Y DUPLICADOS'; Desc = 'BUSCA ARCHIVOS IDENTICOS (SHA-256) EN TUS CARPETAS, MANDA LAS COPIAS A LA PAPELERA Y COMPACTA LA RAM.' }
    @{ Id = 'general'; Texto = 'OPTIMIZACION GENERAL'; Desc = 'BORRA TEMPORALES E INFORMES DE ERROR, VACIA LA CACHE DNS, COMPACTA LA RAM Y HACE TRIM AL DISCO (ADMIN).' }
    @{ Id = 'todo'; Texto = 'REINICIAR TODO'; Desc = 'EJECUTA LOS TRES SISTEMAS EN SECUENCIA.' }
    @{ Id = 'salir'; Texto = 'SALIR'; Desc = 'APAGA EL PANEL.' }
)
$script:sel = 0
$script:sobreItem = $false
$script:todoActivo = $false
$script:todoHechos = 0
$script:itemActual = $null

for ($i = 0; $i -lt $script:items.Count; $i++) {
    $it = $script:items[$i]
    $borde = New-Object Windows.Controls.Border
    $borde.Padding = '6,5,6,5'
    $borde.Background = $C.Nada
    $borde.Cursor = 'Hand'
    $borde.Tag = $i
    $borde.Opacity = 0
    if ($it.Id -eq 'todo') { $borde.Margin = '0,26,0,0' } elseif ($it.Id -eq 'salir') { $borde.Margin = '0,8,0,0' } else { $borde.Margin = '0,2,0,2' }
    $g = New-Object Windows.Controls.Grid
    foreach ($ancho in 36, 0, 300) {
        $cd = New-Object Windows.Controls.ColumnDefinition
        if ($ancho -eq 0) { $cd.Width = New-Object Windows.GridLength(1, 'Star') } else { $cd.Width = New-Object Windows.GridLength($ancho) }
        $g.ColumnDefinitions.Add($cd)
    }
    $marca = New-Object Windows.Controls.TextBlock -Property @{ Text = ''; FontSize = 26; Foreground = $C.Brillo }
    $txt = New-Object Windows.Controls.TextBlock -Property @{ Text = $it.Texto; FontSize = 26; Foreground = $C.Verde }
    $est = New-Object Windows.Controls.TextBlock -Property @{ Text = ''; FontSize = 18; Foreground = $C.Tenue; HorizontalAlignment = 'Right'; VerticalAlignment = 'Center' }
    [Windows.Controls.Grid]::SetColumn($txt, 1)
    [Windows.Controls.Grid]::SetColumn($est, 2)
    [void]$g.Children.Add($marca); [void]$g.Children.Add($txt); [void]$g.Children.Add($est)
    $borde.Child = $g
    $it.Borde = $borde; $it.Marca = $marca; $it.Etiqueta = $txt; $it.Estado = $est
    $it.Fase = 'listo'; $it.Progreso = 0
    if ($it.Id -ne 'salir') { $est.Text = 'LISTO' }

    $borde.Add_MouseEnter({ param($s, $e) $script:sobreItem = $true; if ($script:sel -ne [int]$s.Tag -and -not $script:esperandoRespuesta) { Select-Item ([int]$s.Tag) } })
    $borde.Add_MouseLeave({ $script:sobreItem = $false })
    $borde.Add_MouseLeftButtonUp({ param($s, $e) if (-not $script:esperandoRespuesta) { Invoke-Item ([int]$s.Tag) } })
    [void]$Menu.Children.Add($borde)
}

function Update-Seleccion {
    for ($i = 0; $i -lt $script:items.Count; $i++) {
        $it = $script:items[$i]
        if ($i -eq $script:sel) {
            $it.Borde.Background = $C.SelFondo
            $it.Etiqueta.Foreground = $C.Brillo
        } else {
            $it.Borde.Background = $C.Nada
            $it.Etiqueta.Foreground = $C.Verde
            $it.Marca.Text = ''
        }
    }
    $Descripcion.Text = $script:items[$script:sel].Desc
}

function Select-Item([int]$Indice) {
    $n = $script:items.Count
    $script:sel = (($Indice % $n) + $n) % $n
    Play-Sonido 'mover' 0.8
    Update-Seleccion
}

function Invoke-Item([int]$Indice) {
    $script:sel = $Indice
    Update-Seleccion
    $it = $script:items[$Indice]
    switch ($it.Id) {
        'salir' { Close-Panel }
        'todo' { Start-Trabajo @('procesos', 'memoria', 'general') }
        default { Start-Trabajo @($it.Id) }
    }
}

function Get-Item([string]$Id) { foreach ($it in $script:items) { if ($it.Id -eq $Id) { return $it } } }

# ====================================================================== registro

$script:colaLog = New-Object System.Collections.Queue
$script:lineaActual = $null
$script:lineaTexto = ''
$script:lineaPos = 0

function Add-Log([string]$Texto, [string]$Nivel = 'info') {
    $color = switch ($Nivel) { 'ok' { $C.Brillo } 'warn' { $C.Ambar } 'error' { $C.Rojo } default { $C.Verde } }
    $script:colaLog.Enqueue(@{ Texto = '> ' + $Texto.ToUpper(); Color = $color })
}

function Update-Registro {
    # Efecto máquina de escribir; si hay muchas líneas en espera, se acelera.
    $paso = 3
    if ($script:colaLog.Count -gt 6) { $paso = 400 } elseif ($script:colaLog.Count -gt 2) { $paso = 8 }
    if ($null -eq $script:lineaActual) {
        if ($script:colaLog.Count -eq 0) { return }
        $l = $script:colaLog.Dequeue()
        $tb = New-Object Windows.Controls.TextBlock -Property @{ FontSize = 14; Foreground = $l.Color; TextTrimming = 'CharacterEllipsis' }
        [void]$Registro.Children.Add($tb)
        while ($Registro.Children.Count -gt 8) { $Registro.Children.RemoveAt(0) }
        $script:lineaActual = $tb; $script:lineaTexto = $l.Texto; $script:lineaPos = 0
    }
    $script:lineaPos = [Math]::Min($script:lineaTexto.Length, $script:lineaPos + $paso)
    $cursor = ''
    if ($script:lineaPos -lt $script:lineaTexto.Length) { $cursor = [char]0x2588 }
    $script:lineaActual.Text = $script:lineaTexto.Substring(0, $script:lineaPos) + $cursor
    if ($script:lineaPos -ge $script:lineaTexto.Length) { $script:lineaActual = $null }
}

# ==================================================================== diálogo

$script:esperandoRespuesta = $false
function Show-Pregunta([string]$Titulo, [string[]]$Lineas) {
    $DialogoTitulo.Text = $Titulo
    $DialogoTexto.Text = ($Lineas -join "`n")
    $Dialogo.Visibility = 'Visible'
    $Dialogo.Opacity = 0
    Start-Animacion $Dialogo ([Windows.UIElement]::OpacityProperty) 1 160
    $script:esperandoRespuesta = $true
    Play-Sonido 'alerta'
    Start-Glitch 6
}

function Send-Respuesta([bool]$Si) {
    if (-not $script:esperandoRespuesta) { return }
    $script:esperandoRespuesta = $false
    $Dialogo.Visibility = 'Collapsed'
    $sync.Respuesta = $Si
    if ($Si) { Play-Sonido 'seleccionar' } else { Play-Sonido 'mover' }
}
$BotonSi.Add_MouseLeftButtonUp({ Send-Respuesta $true })
$BotonNo.Add_MouseLeftButtonUp({ Send-Respuesta $false })

# ===================================================================== trabajo

function Start-Trabajo([string[]]$Ids) {
    if ($script:trabajo) {
        Play-Sonido 'error' 0.7
        Add-Log 'SISTEMA OCUPADO: ESPERA A QUE TERMINE EL REINICIO ACTUAL (C = CANCELAR).' 'warn'
        return
    }
    Play-Sonido 'seleccionar'
    $script:todoActivo = ($Ids.Count -gt 1)
    $script:todoHechos = 0
    foreach ($id in $Ids) {
        $it = Get-Item $id
        $it.Fase = 'espera'; $it.Progreso = 0; $it.Estado.Text = 'EN ESPERA'; $it.Estado.Foreground = $C.Tenue
    }
    if ($script:todoActivo) { $t = Get-Item 'todo'; $t.Fase = 'corriendo'; $t.Progreso = 0 }
    $sync.Cancelar = $false
    $sync.Respuesta = $null
    $ps = [PowerShell]::Create()
    $ps.Runspace = $script:rs
    [void]$ps.AddCommand('Invoke-Secuencia').AddParameter('Ids', [string[]]$Ids)
    $script:trabajo = @{ PS = $ps; H = $ps.BeginInvoke() }
}

function Stop-Trabajo {
    if (-not $script:trabajo) { return }
    $sync.Cancelar = $true
    if ($script:esperandoRespuesta) { Send-Respuesta $false }
    Add-Log 'CANCELANDO...' 'warn'
    Play-Sonido 'estatica'
}

function Complete-Trabajo {
    $ps = $script:trabajo.PS
    try { [void]$ps.EndInvoke($script:trabajo.H) } catch { Add-Log ('FALLA INTERNA: ' + $_.Exception.Message) 'error' }
    foreach ($e in $ps.Streams.Error) { Add-Log ('ERROR: ' + $e.ToString()) 'error' }
    $ps.Dispose()
    $script:trabajo = $null
    foreach ($it in $script:items) {
        if ($it.Fase -eq 'espera') { $it.Fase = 'listo'; $it.Estado.Text = 'LISTO'; $it.Estado.Foreground = $C.Tenue }
    }
    if ($script:todoActivo) {
        $t = Get-Item 'todo'
        $fases = @('procesos', 'memoria', 'general' | ForEach-Object { (Get-Item $_).Fase })
        if ($fases -contains 'error') { Set-Fin $t 'error' }
        elseif ($fases -contains 'cancelado' -or $fases -contains 'listo') { Set-Fin $t 'cancelado' }
        else { Set-Fin $t 'ok' }
        $script:todoActivo = $false
    }
    Update-Alertas
}

function Set-Fin($Item, [string]$Estado) {
    $Item.Fase = $Estado
    switch ($Estado) {
        'ok' { $Item.Estado.Text = 'OK'; $Item.Estado.Foreground = $C.Brillo; $script:alertasTareas.Remove($Item.Id) }
        'cancelado' { $Item.Estado.Text = 'CANCELADO'; $Item.Estado.Foreground = $C.Ambar }
        default {
            $Item.Estado.Text = 'ERROR'; $Item.Estado.Foreground = $C.Rojo
            $script:alertasTareas[$Item.Id] = $Item.Texto + ' ERROR'
        }
    }
}

function Receive-Mensajes {
    $m = $null
    while ($sync.Cola.TryDequeue([ref]$m)) {
        switch ($m.Tipo) {
            'log' { Add-Log $m.Texto $m.Nivel }
            'inicio' {
                $it = Get-Item $m.Id
                $it.Fase = 'corriendo'; $it.Progreso = 0; $it.Estado.Foreground = $C.Ambar
                $script:itemActual = $it
                Add-Log ('REINICIANDO: ' + $it.Texto) 'ok'
                Start-Glitch 4
            }
            'progreso' { if ($script:itemActual) { $script:itemActual.Progreso = $m.Valor } }
            'pregunta' { Show-Pregunta $m.Titulo $m.Lineas }
            'fin' {
                $it = Get-Item $m.Id
                Set-Fin $it $m.Estado
                $script:itemActual = $null
                $script:todoHechos++
                switch ($m.Estado) {
                    'ok' { Play-Sonido 'ok' }
                    'cancelado' { Play-Sonido 'estatica' }
                    default { Play-Sonido 'error'; Start-Glitch 14 }
                }
                Update-Alertas
            }
            'terminado' { }
        }
    }
}

# ============================================================ alertas y estado

$script:alertasTareas = @{}
$script:alertas = @()
$script:numProcesos = 0

function Get-Barra([double]$Pct, [int]$Ancho = 12) {
    $n = [int][Math]::Round([Math]::Max(0, [Math]::Min(100, $Pct)) * $Ancho / 100)
    return ([string][char]0x2588 * $n) + ([string][char]0x2591 * ($Ancho - $n))
}

function Update-Estadisticas {
    $m = [PanelNativo]::Memoria()
    $ram = [int]$m[2]
    $cpu = [PanelNativo]::Cpu()
    $disco = New-Object IO.DriveInfo($env:SystemDrive)
    $libre = $disco.AvailableFreeSpace
    $usoDisco = 100 - [int](100.0 * $libre / [Math]::Max(1, $disco.TotalSize))
    if ($script:numProcesos -eq 0 -or $script:frame % 180 -eq 0) { $script:numProcesos = @(Get-Process).Count }
    $Estadisticas.Text = (@(
            ('RAM   {0} {1,3}%' -f (Get-Barra $ram), $ram),
            ('CPU   {0} {1,3}%' -f (Get-Barra $cpu), $cpu),
            ('DISCO {0} {1,3}%' -f (Get-Barra $usoDisco), $usoDisco),
            ('      {0:N1} GB LIBRES EN {1}' -f ($libre / 1GB), $env:SystemDrive),
            ('RAM   {0:N1} / {1:N1} GB' -f (($m[0] - $m[1]) / 1GB), ($m[0] / 1GB)),
            ('PROCESOS ACTIVOS: {0}' -f $script:numProcesos)
        ) -join "`n")
    $script:ram = $ram; $script:cpu = $cpu; $script:usoDisco = $usoDisco
}

function Update-Alertas {
    $lista = New-Object System.Collections.ArrayList
    if ($script:ram -ge 88) { [void]$lista.Add(@{ T = 'MEMORIA CRITICA'; C = $C.Rojo; P = $true }) }
    elseif ($script:ram -ge 75) { [void]$lista.Add(@{ T = 'MEMORIA ALTA'; C = $C.Ambar; P = $false }) }
    if ($script:cpu -ge 90) { [void]$lista.Add(@{ T = 'CPU SATURADA'; C = $C.Rojo; P = $true }) }
    if ($script:usoDisco -ge 92) { [void]$lista.Add(@{ T = 'DISCO CASI LLENO'; C = $C.Rojo; P = $true }) }
    elseif ($script:usoDisco -ge 85) { [void]$lista.Add(@{ T = 'POCO ESPACIO EN DISCO'; C = $C.Ambar; P = $false }) }
    foreach ($t in $script:alertasTareas.Values) { [void]$lista.Add(@{ T = $t; C = $C.Rojo; P = $true }) }
    $Alertas.Children.Clear()
    if ($lista.Count -eq 0) {
        [void]$Alertas.Children.Add((New-Object Windows.Controls.TextBlock -Property @{ Text = 'SIN ALERTAS'; FontSize = 18; Foreground = $C.Oscuro }))
    }
    foreach ($a in $lista) {
        $tb = New-Object Windows.Controls.TextBlock -Property @{ Text = $a.T + '!'; FontSize = 18; FontWeight = 'Bold'; Foreground = $a.C; Margin = '0,0,0,4'; TextWrapping = 'Wrap' }
        $tb.Tag = $a.P
        [void]$Alertas.Children.Add($tb)
    }
}

# ================================================================== animación

$script:rnd = New-Object Random
$script:frame = 0
$script:glitch = 0
$script:anchoRuido = 200; $script:altoRuido = 130
$script:bufRuido = New-Object byte[] ($script:anchoRuido * $script:altoRuido * 4)
$script:bmpRuido = New-Object Windows.Media.Imaging.WriteableBitmap($script:anchoRuido, $script:altoRuido, 96, 96, [Windows.Media.PixelFormats]::Bgra32, $null)
$script:rectRuido = New-Object Windows.Int32Rect(0, 0, $script:anchoRuido, $script:altoRuido)
$Ruido.Source = $script:bmpRuido

function Start-Glitch([int]$Frames) { $script:glitch = [Math]::Max($script:glitch, $Frames) }

function Update-Frame {
    if ($ventana.WindowState -eq 'Minimized') { Receive-Mensajes; if ($script:trabajo -and $script:trabajo.H.IsCompleted) { Complete-Trabajo }; return }
    $script:frame++
    $f = $script:frame
    $r = $script:rnd

    # Eventos programados
    if ($script:eventos.Count -gt 0) {
        $ahora = [DateTime]::Now
        foreach ($ev in @($script:eventos)) {
            if ($ev.Cuando -le $ahora) { $script:eventos.Remove($ev); & $ev.Accion }
        }
    }

    Receive-Mensajes
    if ($script:trabajo -and $script:trabajo.H.IsCompleted) { Receive-Mensajes; Complete-Trabajo }

    # Nieve del monitor
    if ($f % 2 -eq 0) {
        [PanelNativo]::Ruido($script:bufRuido, 255)
        $script:bmpRuido.WritePixels($script:rectRuido, $script:bufRuido, $script:anchoRuido * 4, 0)
    }

    # Banda de barrido que baja
    $alto = $Pantalla.ActualHeight
    $y = $BandaY.Y + 2.5
    if ($y -gt $alto) { $y = -140 }
    $BandaY.Y = $y

    # Parpadeo y glitches
    if ($script:glitch -gt 0) {
        $script:glitch--
        $Sacudida.X = $r.Next(-7, 8)
        $Ruido.Opacity = 0.18 + $r.NextDouble() * 0.2
        $Contenido.Opacity = 0.7 + $r.NextDouble() * 0.3
        if ($script:glitch -eq 0) { $Sacudida.X = 0; $Ruido.Opacity = 0.06 }
    } elseif ($script:arrancado) {
        if ($f % 3 -eq 0) { $Contenido.Opacity = 0.94 + $r.NextDouble() * 0.06 }
        if ($r.Next(900) -eq 0) { Start-Glitch 3 }
    }

    # Cursor de selección y alertas que parpadean
    if ($f % 14 -eq 0) {
        $visible = (($f / 14) % 2) -eq 0
        $it = $script:items[$script:sel]
        if ($visible) { $it.Marca.Text = [string][char]0x25BA } else { $it.Marca.Text = '' }
        foreach ($tb in $Alertas.Children) { if ($tb.Tag -eq $true) { if ($visible) { $tb.Opacity = 1 } else { $tb.Opacity = 0.25 } } }
        if ($script:esperandoRespuesta) { if ($visible) { $Dialogo.BorderBrush = $C.Ambar } else { $Dialogo.BorderBrush = $C.Rojo } }
    }

    # Ítems reiniciándose: puntos + barra + tic
    if ($f % 8 -eq 0) {
        $puntos = '.' * [int](($f / 8) % 4)
        foreach ($it in $script:items) {
            if ($it.Fase -ne 'corriendo') { continue }
            $p = $it.Progreso
            if ($it.Id -eq 'todo' -and $script:itemActual) { $p = ($script:todoHechos * 100 + $script:itemActual.Progreso) / 3 }
            elseif ($it.Id -eq 'todo') { $p = $script:todoHechos * 100 / 3 }
            $it.Estado.Text = ('REINICIANDO{0,-3} {1}' -f $puntos, (Get-Barra $p 8))
        }
    }
    if ($script:trabajo -and -not $script:esperandoRespuesta -and $f % 22 -eq 0) { Play-Sonido 'tic' 0.6 }

    Update-Registro

    if ($f % 60 -eq 0) {
        $Reloj.Text = (Get-Date).ToString('HH:mm')
        Update-Estadisticas
        Update-Alertas
        # Libera reproductores de efectos ya terminados
        foreach ($rp in @($script:reproductores)) {
            if (([DateTime]::Now - $rp.T).TotalSeconds -gt 3) { try { $rp.P.Close() } catch { }; $script:reproductores.Remove($rp) }
        }
    }
}

# ============================================================ encendido / apagado

$script:arrancado = $false
$script:cerrando = $false

function Start-Encendido {
    Play-Sonido 'encendido'
    Start-Animacion $EscalaCRT ([Windows.Media.ScaleTransform]::ScaleXProperty) 1 170
    Start-Animacion $EscalaCRT ([Windows.Media.ScaleTransform]::ScaleYProperty) 1 230 170
    $Destello.Opacity = 0.9
    Start-Animacion $Destello ([Windows.UIElement]::OpacityProperty) 0 650 200
    Invoke-Luego 380 { $Contenido.Opacity = 1; Start-Glitch 8 }
    $t = 520
    for ($i = 0; $i -lt $script:items.Count; $i++) {
        $idx = $i
        Invoke-Luego $t ([scriptblock]::Create("`$script:items[$idx].Borde.Opacity = 1; Play-Sonido 'tic'"))
        $t += 130
    }
    Invoke-Luego ($t + 100) {
        $script:arrancado = $true
        Update-Seleccion
        Update-Estadisticas
        Update-Alertas
        $Reloj.Text = (Get-Date).ToString('HH:mm')
        Add-Log 'PANEL DE MANTENIMIENTO EN LINEA.' 'ok'
        if ($EsAdmin) { Add-Log 'PRIVILEGIOS DE ADMINISTRADOR: TODOS LOS PASOS DISPONIBLES.' }
        else { Add-Log 'MODO USUARIO. ALGUNOS PASOS REQUIEREN ADMIN (TECLA A).' 'warn' }
        Add-Log 'SELECCIONA UN SISTEMA PARA REINICIAR.'
        Start-Ambiente
    }
}

function Close-Panel {
    if ($script:cerrando) { return }
    $script:cerrando = $true
    if ($script:trabajo) { Stop-Trabajo }
    Stop-Ambiente
    Play-Sonido 'apagado'
    $Destello.Opacity = 0.7
    Start-Animacion $Destello ([Windows.UIElement]::OpacityProperty) 0 200
    Start-Animacion $EscalaCRT ([Windows.Media.ScaleTransform]::ScaleYProperty) 0.008 160
    Start-Animacion $EscalaCRT ([Windows.Media.ScaleTransform]::ScaleXProperty) 0 160 170
    Start-Animacion $Led ([Windows.UIElement]::OpacityProperty) 0.15 300 200
    Invoke-Luego 700 { $ventana.Close() }
}

function Restart-ComoAdmin {
    if ($EsAdmin) { Add-Log 'YA ESTAS EN MODO ADMINISTRADOR.'; return }
    if ($script:trabajo) { Add-Log 'ESPERA A QUE TERMINE EL REINICIO ACTUAL.' 'warn'; Play-Sonido 'error' 0.6; return }
    try {
        $script:mutex.ReleaseMutex(); $script:mutex.Dispose(); $script:mutex = $null
        Start-Process -FilePath "$env:windir\System32\WindowsPowerShell\v1.0\powershell.exe" -Verb RunAs `
            -ArgumentList @('-NoProfile', '-STA', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', "`"$EsteScript`"")
        Close-Panel
    } catch {
        $nuevo = $false
        $script:mutex = New-Object System.Threading.Mutex($true, 'Local\PanelMantenimientoFNAF3', [ref]$nuevo)
        Add-Log 'ELEVACION CANCELADA.' 'warn'
        Play-Sonido 'error' 0.6
    }
}

# ===================================================================== eventos

$ventana.Add_KeyDown({
        param($s, $e)
        if ($script:cerrando -or -not $script:arrancado) { return }
        $k = $e.Key.ToString()
        if ($script:esperandoRespuesta) {
            if ($k -in 'S', 'Y', 'Return', 'Enter') { Send-Respuesta $true }
            elseif ($k -in 'N', 'Escape') { Send-Respuesta $false }
            return
        }
        switch ($k) {
            { $_ -in 'Up', 'W' } { Select-Item ($script:sel - 1) }
            { $_ -in 'Down', 'S' } { Select-Item ($script:sel + 1) }
            { $_ -in 'Return', 'Enter', 'Space' } { Invoke-Item $script:sel }
            'C' { Stop-Trabajo }
            'A' { Restart-ComoAdmin }
            'M' {
                $script:silencio = -not $script:silencio
                if ($script:silencio) { Stop-Ambiente; Add-Log 'SONIDO DESACTIVADO.' }
                else { Start-Ambiente; Play-Sonido 'seleccionar'; Add-Log 'SONIDO ACTIVADO.' }
            }
            'Escape' { Close-Panel }
            { $_ -in 'D1', 'NumPad1' } { Invoke-Item 0 }
            { $_ -in 'D2', 'NumPad2' } { Invoke-Item 1 }
            { $_ -in 'D3', 'NumPad3' } { Invoke-Item 2 }
            { $_ -in 'D4', 'NumPad4' } { Invoke-Item 3 }
        }
        $e.Handled = $true
    })

# Arrastrar la ventana desde cualquier parte que no sea un botón.
$Bisel.Add_MouseLeftButtonDown({
        param($s, $e)
        if (-not $script:sobreItem -and -not $script:esperandoRespuesta) { try { $ventana.DragMove() } catch { } }
    })

$Pantalla.Add_SizeChanged({
        $Pantalla.Clip = New-Object Windows.Media.RectangleGeometry((New-Object Windows.Rect(0, 0, $Pantalla.ActualWidth, $Pantalla.ActualHeight)), 22, 22)
    })

$script:temporizador = New-Object Windows.Threading.DispatcherTimer
$script:temporizador.Interval = [TimeSpan]::FromMilliseconds(33)
$script:errorFrameMostrado = $false
$script:temporizador.Add_Tick({
        try { Update-Frame }
        catch {
            if (-not $script:errorFrameMostrado) {
                $script:errorFrameMostrado = $true
                try { [IO.File]::AppendAllText($ArchivoLog, ('{0:yyyy-MM-dd HH:mm:ss} [UI] {1}{2}' -f (Get-Date), $_.ToString(), [Environment]::NewLine)) } catch { }
            }
        }
    })

$ventana.Add_ContentRendered({
        $script:temporizador.Start()
        [void][PanelNativo]::Cpu()   # primera muestra de CPU
        Start-Encendido
    })

$ventana.Add_Closed({
        $script:temporizador.Stop()
        $sync.Cancelar = $true
        $sync.Respuesta = $false
        if ($script:trabajo) { try { $script:trabajo.PS.Stop() } catch { } }
        try { $script:rs.Close(); $script:rs.Dispose() } catch { }
        if ($script:ambiente) { try { $script:ambiente.Close() } catch { } }
        if ($script:mutex) { try { $script:mutex.ReleaseMutex(); $script:mutex.Dispose() } catch { } }
    })

[void]$ventana.ShowDialog()
