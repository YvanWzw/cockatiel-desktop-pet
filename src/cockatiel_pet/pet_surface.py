"""Native layered surfaces; Qt only paints into an offscreen QImage.

The native HWND is born hidden with its verified shell parent. It is never a
top-level Qt window, so Qt flag changes cannot recreate an unsafe overlay.
FrontSurface is a separate, explicitly selected mode added at the user's request.
"""
import ctypes as C
from ctypes import wintypes as W
import logging
from .win32 import WS_CHILD, WS_POPUP, EX_REQUIRED, WS_EX_APPWINDOW
from .models import Point

log = logging.getLogger(__name__)


class PetSurface:
    class_prefix = "CockatielWallpaperChild"
    window_style = WS_CHILD
    extended_style = EX_REQUIRED

    @property
    def native_parent(self):
        return self.host.binding.hwnd

    def client_origin(self, origin):
        return self.api.screen_to_client(self.native_parent, origin)

    def __init__(self, host):
        self.host, self.api = host, host.api
        self.hwnd = 0
        self.dc = self.bitmap = self.old_bitmap = 0
        self.bits = C.c_void_p()
        self.size = (0, 0)
        try:
            self._register()
            if not host.alive():
                raise RuntimeError("Desktop host vanished")
            self.hwnd = self.create(self.extended_style, self.class_name, "Cockatiel Desktop Pet", self.window_style,
                                    0, 0, 1, 1, self.native_parent, None, self.instance, None)
            if not self.hwnd:
                raise C.WinError(C.get_last_error())
            if not self.safe():
                raise RuntimeError("Unsafe native child; destroyed")
        except Exception:
            self.close()
            raise

    def _register(self):
        api = self.api
        class WNDCLASS(C.Structure):
            _fields_ = [("style", W.UINT), ("lpfnWndProc", api.WNDPROC), ("cbClsExtra", C.c_int),
                        ("cbWndExtra", C.c_int), ("hInstance", W.HINSTANCE), ("hIcon", W.HICON),
                        ("hCursor", W.HANDLE), ("hbrBackground", W.HBRUSH), ("lpszMenuName", W.LPCWSTR), ("lpszClassName", W.LPCWSTR)]
        @api.WNDPROC
        def proc(hwnd, message, wparam, lparam):
            if message == 0x0084:  # WM_NCHITTEST: extra defense, styles do pass-through.
                return -1
            if message == 0x0021:  # WM_MOUSEACTIVATE
                return 3  # MA_NOACTIVATE, do not eat the click.
            if message == 0x0082 and hwnd == self.hwnd:  # WM_NCDESTROY
                self.hwnd = 0
            return api.u.DefWindowProcW(hwnd, message, wparam, lparam)
        self.proc = proc  # Keep callback alive for the entire HWND lifetime.
        self.instance = api.k.GetModuleHandleW(None)
        self.class_name = f"{self.class_prefix}_{id(self):x}"
        wc = WNDCLASS()
        wc.lpfnWndProc, wc.hInstance, wc.lpszClassName = proc, self.instance, self.class_name
        api.bind(api.u, "RegisterClassW", W.ATOM, C.POINTER(WNDCLASS))
        api.bind(api.u, "UnregisterClassW", W.BOOL, W.LPCWSTR, W.HINSTANCE)
        if not api.u.RegisterClassW(C.byref(wc)):
            raise C.WinError(C.get_last_error())
        self.create = api.bind(api.u, "CreateWindowExW", W.HWND, W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD,
                               C.c_int, C.c_int, C.c_int, C.c_int, W.HWND, W.HMENU, W.HINSTANCE, C.c_void_p)
        api.bind(api.g, "CreateCompatibleDC", W.HDC, W.HDC)
        api.bind(api.g, "DeleteDC", W.BOOL, W.HDC)
        api.bind(api.g, "SelectObject", W.HANDLE, W.HDC, W.HANDLE)
        api.bind(api.g, "DeleteObject", W.BOOL, W.HANDLE)
        api.bind(api.g, "CreateDIBSection", W.HBITMAP, W.HDC, C.c_void_p, W.UINT, C.POINTER(C.c_void_p), W.HANDLE, W.DWORD)
        api.bind(api.u, "UpdateLayeredWindow", W.BOOL, W.HWND, W.HDC, C.POINTER(W.POINT), C.POINTER(W.SIZE),
                 W.HDC, C.POINTER(W.POINT), W.DWORD, C.c_void_p, W.DWORD)

    def safe(self):
        if not self.hwnd or not self.host.alive():
            return False
        u = self.api.u
        style = u.GetWindowLongPtrW(self.hwnd, -16)
        ex = u.GetWindowLongPtrW(self.hwnd, -20)
        return bool(u.IsWindow(self.hwnd) and u.GetParent(self.hwnd) == self.host.binding.hwnd
                    and style & WS_CHILD and not style & WS_POPUP
                    and ex & EX_REQUIRED == EX_REQUIRED and not ex & (0x8 | WS_EX_APPWINDOW))

    def hide(self):
        if self.hwnd and self.api.is_window(self.hwnd):
            self.api.u.ShowWindow(self.hwnd, 0)

    def _release_bitmap(self):
        if self.dc:
            if self.old_bitmap:
                self.api.g.SelectObject(self.dc, self.old_bitmap)
            if self.bitmap:
                self.api.g.DeleteObject(self.bitmap)
            self.api.g.DeleteDC(self.dc)
        self.dc = self.bitmap = self.old_bitmap = 0
        self.bits = C.c_void_p()
        self.size = (0, 0)

    def _buffer(self, width, height):
        if self.size == (width, height):
            return
        self._release_bitmap()
        class HEADER(C.Structure):
            _fields_ = [("size", W.DWORD), ("width", W.LONG), ("height", W.LONG), ("planes", W.WORD),
                        ("bitcount", W.WORD), ("compression", W.DWORD), ("image_size", W.DWORD),
                        ("xppm", W.LONG), ("yppm", W.LONG), ("used", W.DWORD), ("important", W.DWORD)]
        header = HEADER(C.sizeof(HEADER), width, -height, 1, 32, 0, 0, 0, 0, 0, 0)
        self.dc = self.api.g.CreateCompatibleDC(None)
        if not self.dc:
            raise C.WinError(C.get_last_error())
        self.bitmap = self.api.g.CreateDIBSection(self.dc, C.byref(header), 0, C.byref(self.bits), None, 0)
        if not self.bitmap or not self.bits:
            self._release_bitmap()
            raise C.WinError(C.get_last_error())
        self.old_bitmap = self.api.g.SelectObject(self.dc, self.bitmap)
        self.size = (width, height)

    def present(self, image, origin: Point):
        if not self.safe():
            self.hide()
            raise RuntimeError("Desktop child lost verified parent")
        width, height = image.width(), image.height()
        self._buffer(width, height)
        # Format_ARGB32_Premultiplied is little-endian BGRA, matching the DIB.
        C.memmove(self.bits, image.constBits().tobytes(), width * height * 4)
        client = self.client_origin(origin)
        # SetWindowPos takes parent-client coordinates for child windows.
        # NOACTIVATE | NOZORDER. Styles are set at creation, so FRAMECHANGED is
        # unnecessary on each animation frame. Never change top-level z-order.
        if not self.api.u.SetWindowPos(self.hwnd, None, round(client.x), round(client.y), width, height, 0x10 | 0x4):
            self.hide()
            raise C.WinError(C.get_last_error())
        src, size = W.POINT(0, 0), W.SIZE(width, height)
        # pptDst omitted: retain the position set in parent-client coordinates.
        blend = (C.c_ubyte * 4)(0, 0, 255, 1)  # AC_SRC_OVER, per-pixel alpha
        if not self.api.u.UpdateLayeredWindow(self.hwnd, None, None, C.byref(size), self.dc, C.byref(src), 0, blend, 2):
            self.hide()
            raise C.WinError(C.get_last_error())
        if not self.safe():
            self.hide()
            raise RuntimeError("Desktop host changed during presentation")
        self.api.u.ShowWindow(self.hwnd, 4)  # SW_SHOWNOACTIVATE

    def close(self):
        self.hide()
        if self.hwnd and self.api.is_window(self.hwnd):
            self.api.u.DestroyWindow(self.hwnd)
        self.hwnd = 0
        self._release_bitmap()
        if hasattr(self, "class_name"):
            self.api.u.UnregisterClassW(self.class_name, self.instance)


class FrontHost:
    """Explicit user-selected front mode is independent of Explorer hosting."""
    def __init__(self, api):
        self.api = api

    def alive(self):
        return True

    def validate(self, work):
        return True

    def discover(self, work):
        return True


class FrontSurface(PetSurface):
    """Opt-in topmost mode requested by the user after the original spec.

    Never used as an automatic desktop-host fallback. Same small transparent,
    mouse-through surface and rendering buffer; never activates or takes input.
    """
    class_prefix = "CockatielFrontSurface"
    window_style = WS_POPUP
    extended_style = EX_REQUIRED | 0x8  # WS_EX_TOPMOST, only in explicit front mode.

    @property
    def native_parent(self):
        return None

    def client_origin(self, origin):
        return origin  # Top-level positions use physical screen coordinates.

    def safe(self):
        if not self.hwnd or not self.api.is_window(self.hwnd):
            return False
        u = self.api.u
        style = u.GetWindowLongPtrW(self.hwnd, -16)
        ex = u.GetWindowLongPtrW(self.hwnd, -20)
        return bool(not u.GetParent(self.hwnd) and style & WS_POPUP and not style & WS_CHILD
                    and ex & self.extended_style == self.extended_style and not ex & WS_EX_APPWINDOW)
