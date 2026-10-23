"""64-bit-safe Win32 bindings. No hooks, input injection, or Explorer changes."""
import ctypes as C
from ctypes import wintypes as W
import os
import sys
from .models import Point, Rect
from .desktop_host import WindowInfo

WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOOLWINDOW = 0x80
WS_EX_NOACTIVATE = 0x08000000
WS_EX_APPWINDOW = 0x40000
EX_REQUIRED = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE


class Win32:
    def __init__(self):
        if sys.platform != "win32":
            raise OSError("Cockatiel Desktop Pet requires Windows 10/11 x64.")
        self.u = C.WinDLL("user32", use_last_error=True)
        self.k = C.WinDLL("kernel32", use_last_error=True)
        self.g = C.WinDLL("gdi32", use_last_error=True)
        self.ENUM = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
        self.WNDPROC = C.WINFUNCTYPE(C.c_ssize_t, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
        def bind(lib, name, restype, *args):
            f = getattr(lib, name)
            f.restype, f.argtypes = restype, list(args)
            return f
        self.bind = bind
        for name in ("IsWindow", "IsWindowVisible", "DestroyWindow"):
            bind(self.u, name, W.BOOL, W.HWND)
        bind(self.u, "FindWindowW", W.HWND, W.LPCWSTR, W.LPCWSTR)
        bind(self.u, "GetShellWindow", W.HWND)
        bind(self.u, "GetClassNameW", C.c_int, W.HWND, W.LPWSTR, C.c_int)
        bind(self.u, "EnumWindows", W.BOOL, self.ENUM, W.LPARAM)
        bind(self.u, "GetWindow", W.HWND, W.HWND, W.UINT)
        bind(self.u, "GetParent", W.HWND, W.HWND)
        bind(self.u, "GetAncestor", W.HWND, W.HWND, W.UINT)
        bind(self.u, "GetWindowThreadProcessId", W.DWORD, W.HWND, C.POINTER(W.DWORD))
        bind(self.u, "GetWindowRect", W.BOOL, W.HWND, C.POINTER(W.RECT))
        bind(self.u, "ScreenToClient", W.BOOL, W.HWND, C.POINTER(W.POINT))
        bind(self.u, "GetCursorPos", W.BOOL, C.POINTER(W.POINT))
        bind(self.u, "WindowFromPoint", W.HWND, W.POINT)
        bind(self.u, "GetAsyncKeyState", C.c_short, C.c_int)
        bind(self.u, "GetSystemMetrics", C.c_int, C.c_int)
        bind(self.u, "SendMessageTimeoutW", C.c_ssize_t, W.HWND, W.UINT, W.WPARAM, W.LPARAM, W.UINT, W.UINT, C.POINTER(C.c_size_t))
        bind(self.u, "GetWindowLongPtrW", C.c_ssize_t, W.HWND, C.c_int)
        bind(self.u, "SetWindowLongPtrW", C.c_ssize_t, W.HWND, C.c_int, C.c_ssize_t)
        bind(self.u, "SetWindowPos", W.BOOL, W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT)
        bind(self.u, "ShowWindow", W.BOOL, W.HWND, C.c_int)
        bind(self.u, "DefWindowProcW", C.c_ssize_t, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
        bind(self.u, "GetDC", W.HDC, W.HWND)
        bind(self.u, "ReleaseDC", C.c_int, W.HWND, W.HDC)
        bind(self.k, "GetModuleHandleW", W.HMODULE, W.LPCWSTR)
        bind(self.k, "OpenProcess", W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
        bind(self.k, "QueryFullProcessImageNameW", W.BOOL, W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD))
        bind(self.k, "CloseHandle", W.BOOL, W.HANDLE)
        bind(self.k, "CreateMutexW", W.HANDLE, C.c_void_p, W.BOOL, W.LPCWSTR)

    def is_window(self, hwnd):
        return bool(self.u.IsWindow(hwnd))

    def pid(self, hwnd):
        value = W.DWORD()
        self.u.GetWindowThreadProcessId(hwnd, C.byref(value))
        return value.value

    def cls(self, hwnd):
        value = C.create_unicode_buffer(256)
        self.u.GetClassNameW(hwnd, value, len(value))
        return value.value

    def shell_pid(self):
        shell = self.u.GetShellWindow()
        if not shell or self.cls(shell) not in {"Progman", "WorkerW"}:
            return 0
        pid = self.pid(shell)
        handle = self.k.OpenProcess(0x1000, False, pid)
        if not handle:
            return 0
        try:
            size = W.DWORD(32768)
            name = C.create_unicode_buffer(size.value)
            if not self.k.QueryFullProcessImageNameW(handle, 0, name, C.byref(size)):
                return 0
            return pid if os.path.basename(name.value).lower() == "explorer.exe" else 0
        finally:
            self.k.CloseHandle(handle)

    def snapshot(self):
        windows = []
        shell_pid = self.shell_pid()
        def add(hwnd, parent=0, depth=0):
            if depth > 16 or len(windows) > 8192:
                return
            rect = W.RECT()
            if self.u.GetWindowRect(hwnd, C.byref(rect)):
                windows.append(WindowInfo(int(hwnd), self.cls(hwnd), self.pid(hwnd), parent,
                                          Rect(rect.left, rect.top, rect.right, rect.bottom), bool(self.u.IsWindowVisible(hwnd))))
            if self.pid(hwnd) != shell_pid:
                return  # Only shell descendants are relevant; never walk app controls.
            child = self.u.GetWindow(hwnd, 5)  # GW_CHILD, then actual sibling z-order
            seen = set()
            while child and child not in seen:
                seen.add(child)
                add(child, int(hwnd), depth + 1)
                child = self.u.GetWindow(child, 2)  # GW_HWNDNEXT
        @self.ENUM
        def enum(hwnd, _):
            add(hwnd)
            return True
        if not self.u.EnumWindows(enum, 0):
            raise C.WinError(C.get_last_error())
        return windows

    def request_worker(self):
        progman = self.u.FindWindowW("Progman", None)
        if progman and self.pid(progman) == self.shell_pid():
            result = C.c_size_t()
            # Classic shell and newer raised-desktop variants. All calls are
            # bounded; success still requires topology/visibility validation.
            for wparam, lparam in ((0, 0), (0xD, 0), (0xD, 1)):
                self.u.SendMessageTimeoutW(progman, 0x052C, wparam, lparam, 0x0002 | 0x0020, 250, C.byref(result))

    def screen_to_client(self, hwnd, p):
        point = W.POINT(round(p.x), round(p.y))
        if not self.u.ScreenToClient(hwnd, C.byref(point)):
            raise C.WinError(C.get_last_error())
        return Point(point.x, point.y)

    def primary_display(self):
        class MONITORINFO(C.Structure):
            _fields_ = [("cbSize", W.DWORD), ("rcMonitor", W.RECT), ("rcWork", W.RECT), ("dwFlags", W.DWORD)]
        self.bind(self.u, "MonitorFromPoint", W.HMONITOR, W.POINT, W.DWORD)
        self.bind(self.u, "GetMonitorInfoW", W.BOOL, W.HMONITOR, C.POINTER(MONITORINFO))
        monitor = self.u.MonitorFromPoint(W.POINT(0, 0), 1)  # MONITOR_DEFAULTTOPRIMARY
        info = MONITORINFO()
        info.cbSize = C.sizeof(info)
        if not self.u.GetMonitorInfoW(monitor, C.byref(info)):
            raise C.WinError(C.get_last_error())
        r = info.rcWork
        # GetDpiForMonitor reports effective monitor DPI when PMv2 is active.
        dpi = W.UINT(96)
        try:
            shcore = C.WinDLL("shcore", use_last_error=True)
            f = self.bind(shcore, "GetDpiForMonitor", C.c_long, W.HMONITOR, C.c_int, C.POINTER(W.UINT), C.POINTER(W.UINT))
            dy = W.UINT()
            if f(monitor, 0, C.byref(dpi), C.byref(dy)) != 0:
                dpi.value = 96
        except (OSError, AttributeError):
            pass
        return Rect(r.left, r.top, r.right, r.bottom), dpi.value / 96

    def pointer(self, binding):
        p = W.POINT()
        if not self.u.GetCursorPos(C.byref(p)):
            return None
        # Track the physical primary button, including Windows swapped buttons.
        vk = 0x02 if self.u.GetSystemMetrics(23) else 0x01
        down = bool(self.u.GetAsyncKeyState(vk) & 0x8000)
        hit = self.u.WindowFromPoint(p)
        exposed = False
        if hit and binding and self.pid(hit) == binding.pid:
            # Strict whitelist and verified ancestry. Popups/Start/taskbar denied.
            if self.cls(hit) in {"Progman", "WorkerW", "SHELLDLL_DefView", "SysListView32"}:
                root = int(self.u.GetAncestor(hit, 2) or 0)
                icon_root = int(self.u.GetAncestor(binding.icon, 2) or 0)
                exposed = bool(root and icon_root and root in {binding.root, icon_root})
        return Point(p.x, p.y), down, exposed

    def acquire_instance(self):
        handle = self.k.CreateMutexW(None, False, "Local\\CockatielDesktopPet-v1")
        if not handle:
            raise C.WinError(C.get_last_error())
        if C.get_last_error() == 183:
            self.k.CloseHandle(handle)
            return None
        return handle

    def process_memory_mib(self):
        class COUNTERS(C.Structure):
            _fields_ = [("cb", W.DWORD), ("faults", W.DWORD)] + [(name, C.c_size_t) for name in
                ("peak_working", "working", "peak_paged", "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile", "private")]
        current = self.bind(self.k, "GetCurrentProcess", W.HANDLE)
        info = self.bind(self.k, "K32GetProcessMemoryInfo", W.BOOL, W.HANDLE, C.POINTER(COUNTERS), W.DWORD)
        counters = COUNTERS()
        counters.cb = C.sizeof(counters)
        if info(current(), C.byref(counters), counters.cb):
            return round(counters.working / 1024 ** 2, 2)
        return None


def enable_dpi_awareness():
    """Call before QApplication/any HWND. Failure is harmless if manifest set it."""
    if sys.platform == "win32":
        u = C.WinDLL("user32", use_last_error=True)
        try:
            u.SetProcessDpiAwarenessContext.argtypes = [C.c_void_p]
            u.SetProcessDpiAwarenessContext.restype = W.BOOL
            u.SetProcessDpiAwarenessContext(C.c_void_p(-4))  # PMv2
        except AttributeError:
            pass
