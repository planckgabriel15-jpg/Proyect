// Funciones nativas de Windows que PowerShell no expone directamente.
// Se compila en tiempo de ejecución con Add-Type (Windows PowerShell 5.1 -> C# 5:
// sin interpolación de cadenas, sin "out var", sin miembros con "=>").
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class PanelNativo
{
    // ------------------------------------------------------------------ memoria
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    private class MEMORYSTATUSEX
    {
        public uint dwLength;
        public uint dwMemoryLoad;
        public ulong ullTotalPhys;
        public ulong ullAvailPhys;
        public ulong ullTotalPageFile;
        public ulong ullAvailPageFile;
        public ulong ullTotalVirtual;
        public ulong ullAvailVirtual;
        public ulong ullAvailExtendedVirtual;
        public MEMORYSTATUSEX() { dwLength = (uint)Marshal.SizeOf(typeof(MEMORYSTATUSEX)); }
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GlobalMemoryStatusEx([In, Out] MEMORYSTATUSEX m);

    /// <summary>{ total, disponible, porcentaje en uso } en bytes.</summary>
    public static ulong[] Memoria()
    {
        MEMORYSTATUSEX m = new MEMORYSTATUSEX();
        if (!GlobalMemoryStatusEx(m)) return new ulong[] { 0, 0, 0 };
        return new ulong[] { m.ullTotalPhys, m.ullAvailPhys, m.dwMemoryLoad };
    }

    // ---------------------------------------------------------------------- CPU
    [DllImport("kernel32.dll")]
    private static extern bool GetSystemTimes(out long idle, out long kernel, out long user);
    private static long pIdle, pKernel, pUser;

    /// <summary>Uso de CPU (%) desde la llamada anterior. Barato: no usa WMI ni contadores.</summary>
    public static int Cpu()
    {
        long i, k, u;
        if (!GetSystemTimes(out i, out k, out u)) return -1;
        long di = i - pIdle, dk = k - pKernel, du = u - pUser;
        pIdle = i; pKernel = k; pUser = u;
        long total = dk + du; // el tiempo de kernel ya incluye el ocioso
        if (total <= 0) return 0;
        return (int)Math.Max(0, Math.Min(100, (total - di) * 100 / total));
    }

    // ------------------------------------------------- recorte de working set
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll")]
    private static extern bool CloseHandle(IntPtr h);
    [DllImport("psapi.dll", SetLastError = true)]
    private static extern bool EmptyWorkingSet(IntPtr h);

    /// <summary>Pide a Windows que saque de la RAM las páginas que el proceso no está usando.</summary>
    public static bool RecortarMemoria(int pid)
    {
        // PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA
        IntPtr h = OpenProcess(0x0400 | 0x0100, false, pid);
        if (h == IntPtr.Zero) return false;
        try { return EmptyWorkingSet(h); }
        finally { CloseHandle(h); }
    }

    // ------------------------------------- lista "en espera" (solo administrador)
    [DllImport("ntdll.dll")]
    private static extern int NtSetSystemInformation(int infoClass, ref int info, int length);
    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool LookupPrivilegeValue(string system, string name, out long luid);
    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    private struct TOKEN_PRIVILEGES { public int Count; public long Luid; public int Attributes; }
    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool AdjustTokenPrivileges(IntPtr token, bool disableAll, ref TOKEN_PRIVILEGES state, int len, IntPtr prev, IntPtr retLen);
    [DllImport("kernel32.dll")]
    private static extern IntPtr GetCurrentProcess();

    private static bool HabilitarPrivilegio(string nombre)
    {
        IntPtr token;
        // TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY
        if (!OpenProcessToken(GetCurrentProcess(), 0x0020 | 0x0008, out token)) return false;
        try
        {
            TOKEN_PRIVILEGES tp = new TOKEN_PRIVILEGES();
            tp.Count = 1;
            tp.Attributes = 2; // SE_PRIVILEGE_ENABLED
            if (!LookupPrivilegeValue(null, nombre, out tp.Luid)) return false;
            if (!AdjustTokenPrivileges(token, false, ref tp, 0, IntPtr.Zero, IntPtr.Zero)) return false;
            return Marshal.GetLastWin32Error() == 0;
        }
        finally { CloseHandle(token); }
    }

    /// <summary>
    /// Vacía la lista de páginas "en espera" (caché de archivos), como hace RAMMap.
    /// Devuelve el NTSTATUS (0 = éxito) o -1 si no se pudo obtener el privilegio.
    /// </summary>
    public static int PurgarListaEspera()
    {
        if (!HabilitarPrivilegio("SeProfileSingleProcessPrivilege")) return -1;
        int comando = 4;                                     // MemoryPurgeStandbyList
        return NtSetSystemInformation(80, ref comando, 4);   // SystemMemoryListInformation
    }

    // ---------------------------------------------------------------- ventanas
    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lParam);
    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")]
    private static extern int GetWindowTextLength(IntPtr hWnd);
    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    /// <summary>PIDs que tienen al menos una ventana visible con título (lo que el usuario "ve").</summary>
    public static int[] PidsConVentana()
    {
        HashSet<int> pids = new HashSet<int>();
        EnumWindows(delegate (IntPtr h, IntPtr l)
        {
            if (IsWindowVisible(h) && GetWindowTextLength(h) > 0)
            {
                uint pid;
                GetWindowThreadProcessId(h, out pid);
                pids.Add((int)pid);
            }
            return true;
        }, IntPtr.Zero);
        int[] r = new int[pids.Count];
        pids.CopyTo(r);
        return r;
    }

    public static int PidPrimerPlano()
    {
        IntPtr h = GetForegroundWindow();
        if (h == IntPtr.Zero) return 0;
        uint pid;
        GetWindowThreadProcessId(h, out pid);
        return (int)pid;
    }

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    private static extern int SetCurrentProcessExplicitAppUserModelID(string appId);

    /// <summary>
    /// Identidad propia en la barra de tareas: así el botón anclado y la ventana abierta
    /// se agrupan juntos y no se mezclan con otras consolas de PowerShell.
    /// Debe coincidir con la del acceso directo que crea Instalar.ps1.
    /// </summary>
    public static void FijarIdentidadBarra(string appId)
    {
        SetCurrentProcessExplicitAppUserModelID(appId);
    }

    [DllImport("kernel32.dll")]
    private static extern IntPtr GetConsoleWindow();
    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr hWnd, int cmd);

    public static void OcultarConsola()
    {
        IntPtr h = GetConsoleWindow();
        if (h != IntPtr.Zero) ShowWindow(h, 0);
    }

    // -------------------------------------------------- papelera de reciclaje
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct SHFILEOPSTRUCT
    {
        public IntPtr hwnd;
        public uint wFunc;
        public string pFrom;
        public string pTo;
        public ushort fFlags;
        public bool fAnyOperationsAborted;
        public IntPtr hNameMappings;
        public string lpszProgressTitle;
    }
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    private static extern int SHFileOperation(ref SHFILEOPSTRUCT op);

    /// <summary>
    /// Envía un archivo a la Papelera sin mostrar diálogos de progreso ni de error.
    /// FOF_WANTNUKEWARNING hace que Windows avise si el archivo NO entra en la papelera,
    /// en lugar de borrarlo definitivamente en silencio. Devuelve 0 si salió bien.
    /// </summary>
    public static int APapelera(string ruta)
    {
        SHFILEOPSTRUCT op = new SHFILEOPSTRUCT();
        op.wFunc = 3;                     // FO_DELETE
        op.pFrom = ruta + "\0\0";         // lista terminada en doble nulo
        // FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI | FOF_WANTNUKEWARNING
        op.fFlags = (ushort)(0x0040 | 0x0010 | 0x0004 | 0x0400 | 0x4000);
        int r = SHFileOperation(ref op);
        if (r == 0 && op.fAnyOperationsAborted) return 1223; // ERROR_CANCELLED
        return r;
    }

    // ---------------------------------------------- procesos que suenan (audio)
    // Core Audio: se protege a todo proceso con una sesión de audio ACTIVA
    // (música en Spotify, llamada en Discord, etc.) aunque no tenga ventana.
    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
    private class MMDeviceEnumeratorCom { }

    [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IMMDeviceEnumerator
    {
        [PreserveSig] int EnumAudioEndpoints(int dataFlow, int stateMask, out IMMDeviceCollection devices);
    }

    [ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IMMDeviceCollection
    {
        [PreserveSig] int GetCount(out int count);
        [PreserveSig] int Item(int index, out IMMDevice device);
    }

    [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IMMDevice
    {
        [PreserveSig] int Activate(ref Guid iid, int clsCtx, IntPtr parameters, [MarshalAs(UnmanagedType.IUnknown)] out object instance);
    }

    [ComImport, Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IAudioSessionManager2
    {
        [PreserveSig] int GetAudioSessionControl(IntPtr a, int b, out IntPtr c); // heredado, sin usar
        [PreserveSig] int GetSimpleAudioVolume(IntPtr a, int b, out IntPtr c);   // heredado, sin usar
        [PreserveSig] int GetSessionEnumerator(out IAudioSessionEnumerator sessions);
    }

    [ComImport, Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IAudioSessionEnumerator
    {
        [PreserveSig] int GetCount(out int count);
        [PreserveSig] int GetSession(int index, out IAudioSessionControl2 session);
    }

    [ComImport, Guid("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IAudioSessionControl2
    {
        // IAudioSessionControl (el orden de la vtable importa; los no usados son marcadores)
        [PreserveSig] int GetState(out int state);
        [PreserveSig] int GetDisplayName(out IntPtr name);
        [PreserveSig] int SetDisplayName(IntPtr a, IntPtr b);
        [PreserveSig] int GetIconPath(out IntPtr path);
        [PreserveSig] int SetIconPath(IntPtr a, IntPtr b);
        [PreserveSig] int GetGroupingParam(out Guid g);
        [PreserveSig] int SetGroupingParam(IntPtr a, IntPtr b);
        [PreserveSig] int RegisterAudioSessionNotification(IntPtr a);
        [PreserveSig] int UnregisterAudioSessionNotification(IntPtr a);
        // IAudioSessionControl2
        [PreserveSig] int GetSessionIdentifier(out IntPtr id);
        [PreserveSig] int GetSessionInstanceIdentifier(out IntPtr id);
        [PreserveSig] int GetProcessId(out uint pid);
    }

    /// <summary>PIDs con una sesión de audio activa (reproducción o grabación). Nunca lanza.</summary>
    public static int[] PidsConAudio()
    {
        HashSet<int> pids = new HashSet<int>();
        try
        {
            IMMDeviceEnumerator en = (IMMDeviceEnumerator)new MMDeviceEnumeratorCom();
            IMMDeviceCollection col;
            if (en.EnumAudioEndpoints(2 /* eAll */, 1 /* DEVICE_STATE_ACTIVE */, out col) != 0) return new int[0];
            int n;
            col.GetCount(out n);
            Guid iid = typeof(IAudioSessionManager2).GUID;
            for (int i = 0; i < n; i++)
            {
                try
                {
                    IMMDevice dev;
                    if (col.Item(i, out dev) != 0) continue;
                    object o;
                    if (dev.Activate(ref iid, 23 /* CLSCTX_ALL */, IntPtr.Zero, out o) != 0) continue;
                    IAudioSessionManager2 mgr = (IAudioSessionManager2)o;
                    IAudioSessionEnumerator ses;
                    if (mgr.GetSessionEnumerator(out ses) != 0) continue;
                    int c;
                    ses.GetCount(out c);
                    for (int j = 0; j < c; j++)
                    {
                        IAudioSessionControl2 s;
                        if (ses.GetSession(j, out s) != 0 || s == null) continue;
                        int estado;
                        uint pid;
                        if (s.GetState(out estado) == 0 && estado == 1 /* Active */ && s.GetProcessId(out pid) >= 0 && pid != 0) // >= 0: también AUDCLNT_S_NO_SINGLE_PROCESS (sesión compartida)
                            pids.Add((int)pid);
                    }
                }
                catch { }
            }
        }
        catch { }
        int[] r = new int[pids.Count];
        pids.CopyTo(r);
        return r;
    }

    // ------------------------------------------------------- efecto de ruido
    private static readonly Random rnd = new Random();

    /// <summary>Llena un búfer BGRA con estática gris (para la capa de "nieve" del monitor).</summary>
    public static void Ruido(byte[] buf, int alfaMax)
    {
        for (int i = 0; i + 3 < buf.Length; i += 4)
        {
            byte v = (byte)rnd.Next(256);
            buf[i] = v; buf[i + 1] = v; buf[i + 2] = v;
            buf[i + 3] = (byte)rnd.Next(alfaMax);
        }
    }
}
