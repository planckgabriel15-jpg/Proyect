# Quita el Panel de Mantenimiento instalado por Instalar.ps1.
$ErrorActionPreference = 'Continue'
$nombre = 'Panel de Mantenimiento.lnk'
foreach ($lnk in @(
        (Join-Path ([Environment]::GetFolderPath('Programs')) $nombre),
        (Join-Path ([Environment]::GetFolderPath('Desktop')) $nombre),
        (Join-Path $env:APPDATA "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\$nombre"))) {
    if (Test-Path -LiteralPath $lnk) { Remove-Item -LiteralPath $lnk -Force; Write-Host "  - Borrado: $lnk" }
}
$app = Join-Path $env:LOCALAPPDATA 'PanelMantenimiento'
if (Test-Path -LiteralPath $app) {
    $r = Read-Host '  ¿Borrar tambien los registros e informes de duplicados? (S/N) [N]'
    if ($r -match '^[sSyY]') { Remove-Item -LiteralPath $app -Recurse -Force }
    else { Remove-Item -LiteralPath (Join-Path $app 'app') -Recurse -Force -ErrorAction SilentlyContinue }
}
Write-Host ''
Write-Host '  Desinstalado. Si quedo un icono anclado en la barra de tareas: clic derecho > Desanclar.'
