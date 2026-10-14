<#
    Instala el Panel de Mantenimiento para el usuario actual (no requiere administrador):
      - copia el programa a %LOCALAPPDATA%\PanelMantenimiento\app
      - crea accesos directos en el Menú Inicio y el Escritorio, con icono propio
      - les asigna una identidad de barra de tareas para poder anclarlo
#>
param(
    [switch]$ComoAdministrador,   # el acceso directo pedirá permisos de admin al abrir
    [switch]$SinPreguntas
)
$ErrorActionPreference = 'Stop'
$Origen = Split-Path -Parent $MyInvocation.MyCommand.Path
$Destino = Join-Path $env:LOCALAPPDATA 'PanelMantenimiento\app'
$AppId = 'Planck.PanelMantenimiento'
$NombreAcceso = 'Panel de Mantenimiento.lnk'

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text;

public static class AccesoDirecto
{
    [ComImport, Guid("00021401-0000-0000-C000-000000000046")]
    private class CShellLink { }

    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("000214F9-0000-0000-C000-000000000046")]
    private interface IShellLinkW
    {
        void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder f, int cch, IntPtr fd, uint flags);
        void GetIDList(out IntPtr pidl);
        void SetIDList(IntPtr pidl);
        void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int cch);
        void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string s);
        void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int cch);
        void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string s);
        void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int cch);
        void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string s);
        void GetHotkey(out short k);
        void SetHotkey(short k);
        void GetShowCmd(out int c);
        void SetShowCmd(int c);
        void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int cch, out int i);
        void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string s, int i);
        void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string s, int r);
        void Resolve(IntPtr hwnd, int flags);
        void SetPath([MarshalAs(UnmanagedType.LPWStr)] string s);
    }

    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("45E2B4AE-B1C3-11D0-B92F-00A0C90312E1")]
    private interface IShellLinkDataList
    {
        void AddDataBlock(IntPtr block);
        void CopyDataBlock(uint sig, out IntPtr block);
        void RemoveDataBlock(uint sig);
        void GetFlags(out uint flags);
        void SetFlags(uint flags);
    }

    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    private struct PROPERTYKEY { public Guid fmtid; public uint pid; }

    [StructLayout(LayoutKind.Sequential)]
    private struct PROPVARIANT { public ushort vt; public ushort r1; public ushort r2; public ushort r3; public IntPtr p; public IntPtr p2; }

    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")]
    private interface IPropertyStore
    {
        void GetCount(out uint c);
        void GetAt(uint i, out PROPERTYKEY k);
        void GetValue(ref PROPERTYKEY k, IntPtr v);
        void SetValue(ref PROPERTYKEY k, ref PROPVARIANT v);
        void Commit();
    }

    public static void Crear(string lnk, string destino, string args, string carpeta, string icono,
                             string descripcion, string appId, bool comoAdmin)
    {
        IShellLinkW link = (IShellLinkW)new CShellLink();
        link.SetPath(destino);
        link.SetArguments(args);
        link.SetWorkingDirectory(carpeta);
        link.SetIconLocation(icono, 0);
        link.SetDescription(descripcion);
        link.SetShowCmd(7); // minimizado: evita el destello de la consola

        // System.AppUserModel.ID
        IPropertyStore ps = (IPropertyStore)link;
        PROPERTYKEY k = new PROPERTYKEY();
        k.fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3");
        k.pid = 5;
        PROPVARIANT v = new PROPVARIANT();
        v.vt = 31; // VT_LPWSTR
        v.p = Marshal.StringToCoTaskMemUni(appId);
        try { ps.SetValue(ref k, ref v); ps.Commit(); }
        finally { Marshal.FreeCoTaskMem(v.p); }

        if (comoAdmin)
        {
            IShellLinkDataList dl = (IShellLinkDataList)link;
            uint flags;
            dl.GetFlags(out flags);
            dl.SetFlags(flags | 0x00002000); // SLDF_RUNAS_USER
        }
        ((IPersistFile)link).Save(lnk, true);
    }
}
'@ -Language CSharp

Write-Host ''
Write-Host '  ==== PANEL DE MANTENIMIENTO :: INSTALACION ====' -ForegroundColor Green
Write-Host ''

# 1) Copiar el programa (si ya había un config.json, se respeta el del usuario)
[void](New-Item -ItemType Directory -Path $Destino -Force)
$configPrevio = $null
$cfgDestino = Join-Path $Destino 'config.json'
if (Test-Path -LiteralPath $cfgDestino) { $configPrevio = [IO.File]::ReadAllBytes($cfgDestino) }
foreach ($item in 'PanelMantenimiento.ps1', 'config.json', 'modulos', 'recursos') {
    Copy-Item -LiteralPath (Join-Path $Origen $item) -Destination $Destino -Recurse -Force
}
if ($configPrevio) {
    [IO.File]::WriteAllBytes($cfgDestino, $configPrevio)
    Write-Host '  - Se conservo tu config.json anterior.'
}
Get-ChildItem -LiteralPath $Destino -Recurse -File | Unblock-File
Write-Host "  - Programa copiado en: $Destino"

# 2) ¿Siempre como administrador?
if (-not $SinPreguntas -and -not $ComoAdministrador) {
    Write-Host ''
    Write-Host '  Como ADMINISTRADOR el panel puede ademas: limpiar C:\Windows\Temp, la cache de'
    Write-Host '  Windows Update y hacer TRIM al disco. A cambio, Windows pedira permiso (UAC) cada vez.'
    $r = Read-Host '  ¿Abrir siempre como administrador? (S/N) [N]'
    $ComoAdministrador = ($r -match '^[sSyY]')
}

# 3) Accesos directos
$ps = Join-Path $env:windir 'System32\WindowsPowerShell\v1.0\powershell.exe'
$script = Join-Path $Destino 'PanelMantenimiento.ps1'
$argumentos = '-NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $script
$icono = Join-Path $Destino 'recursos\icono.ico'
$descripcion = 'Cierra procesos en segundo plano, borra duplicados, libera memoria y optimiza la PC.'
$lugares = @(
    (Join-Path ([Environment]::GetFolderPath('Programs')) $NombreAcceso),
    (Join-Path ([Environment]::GetFolderPath('Desktop')) $NombreAcceso)
)
foreach ($lnk in $lugares) {
    [AccesoDirecto]::Crear($lnk, $ps, $argumentos, $Destino, $icono, $descripcion, $AppId, [bool]$ComoAdministrador)
    Write-Host "  - Acceso directo: $lnk"
}

Write-Host ''
Write-Host '  LISTO. Para ponerlo en la BARRA DE TAREAS:' -ForegroundColor Green
Write-Host '    Windows 11: Inicio > Todas las aplicaciones > clic derecho en "Panel de Mantenimiento"'
Write-Host '                > Mas > Anclar a la barra de tareas.'
Write-Host '    Windows 10: Inicio > clic derecho en "Panel de Mantenimiento" > Mas > Anclar a la barra de tareas.'
Write-Host '    (o abrilo y hace clic derecho en su icono de la barra > Anclar a la barra de tareas)'
Write-Host ''
if (-not $SinPreguntas) {
    $r = Read-Host '  ¿Abrir el panel ahora? (S/N) [S]'
    if ($r -notmatch '^[nN]') { Start-Process -FilePath $lugares[0] }
}
