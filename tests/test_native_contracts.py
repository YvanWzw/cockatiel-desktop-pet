"""Exercise native safety gates through fakes; no Explorer or input required."""
from types import SimpleNamespace
import ctypes as C
from ctypes import wintypes as W
import pytest
from cockatiel_pet.win32 import Win32, WS_CHILD, WS_POPUP, EX_REQUIRED, WS_EX_APPWINDOW
from cockatiel_pet.pet_surface import PetSurface, FrontSurface
from cockatiel_pet.desktop_host import HostBinding


@pytest.mark.parametrize("style,ex,parent,expected", [
    (WS_CHILD,EX_REQUIRED,500,True),
    (WS_CHILD,EX_REQUIRED | 0x8,500,False),  # Reject the native topmost bit.
    (WS_CHILD,EX_REQUIRED | WS_EX_APPWINDOW,500,False),
    (WS_CHILD | WS_POPUP,EX_REQUIRED,500,False),
    (0,EX_REQUIRED,500,False),
    (WS_CHILD,EX_REQUIRED & ~0x20,500,False),
    (WS_CHILD,EX_REQUIRED,0,False),
])
def test_surface_requires_child_pass_through_noactivation_and_verified_parent(style,ex,parent,expected):
    u = SimpleNamespace(IsWindow=lambda _:True, GetParent=lambda _:parent,
                        GetWindowLongPtrW=lambda _, index: style if index == -16 else ex)
    surface = object.__new__(PetSurface)
    surface.hwnd = 2**40 + 123
    surface.api = SimpleNamespace(u=u)
    surface.host = SimpleNamespace(alive=lambda:True, binding=SimpleNamespace(hwnd=500))
    assert surface.safe() is expected
    surface.host.alive = lambda:False
    assert not surface.safe()


@pytest.mark.parametrize("cls,root,pid,exposed", [
    ("SysListView32",100,7,True), ("SHELLDLL_DefView",100,7,True),
    ("WorkerW",100,7,True), ("Chrome_WidgetWin_1",100,99,False),
    ("#32768",100,7,False), ("Shell_TrayWnd",100,7,False),
    ("WorkerW",900,7,False), ("SHELLDLL_DefView",900,7,False),
    ("Windows.UI.Core.CoreWindow",100,7,False), ("WorkerW",0,7,False),
])
def test_native_desktop_hit_whitelist_and_ancestry(cls,root,pid,exposed):
    api = object.__new__(Win32)
    def cursor(pointer):
        p = C.cast(pointer,C.POINTER(W.POINT)).contents
        p.x,p.y = 123,456
        return True
    api.u = SimpleNamespace(GetCursorPos=cursor, GetSystemMetrics=lambda _:0,
                            GetAsyncKeyState=lambda _:1, WindowFromPoint=lambda _:777,
                            GetAncestor=lambda hwnd,_:100 if hwnd==101 else root)
    api.pid = lambda _:pid
    api.cls = lambda _:cls
    _,down,desktop = api.pointer(HostBinding(102,101,100,7))
    assert desktop is exposed
    assert not down  # The low async-key bit must never be interpreted as held.


def test_swapped_buttons_use_high_bit():
    api = object.__new__(Win32)
    requested = []
    def key(vk):
        requested.append(vk)
        return -32768
    api.u = SimpleNamespace(GetCursorPos=lambda _:True, GetSystemMetrics=lambda _:1,
                            GetAsyncKeyState=key, WindowFromPoint=lambda _:0)
    _,down,exposed = api.pointer(None)
    assert down and not exposed and requested == [2]


@pytest.mark.parametrize("style,ex,parent,expected", [
    (WS_POPUP,EX_REQUIRED | 0x8,0,True),
    (WS_POPUP,EX_REQUIRED,0,False),
    (WS_CHILD,EX_REQUIRED | 0x8,500,False),
    (WS_POPUP,(EX_REQUIRED | 0x8) & ~0x20,0,False),
    (WS_POPUP,(EX_REQUIRED | 0x8) & ~0x08000000,0,False),
    (WS_POPUP,EX_REQUIRED | 0x8 | WS_EX_APPWINDOW,0,False),
])
def test_explicit_front_mode_is_topmost_pass_through_and_nonactivating(style,ex,parent,expected):
    u = SimpleNamespace(GetParent=lambda _:parent,GetWindowLongPtrW=lambda _,index:style if index==-16 else ex)
    surface = object.__new__(FrontSurface)
    surface.hwnd = 123
    surface.api = SimpleNamespace(u=u,is_window=lambda _:True)
    assert surface.safe() is expected
