from cockatiel_pet.desktop_host import WindowInfo as W, choose_host, DesktopHost, HostSession
from cockatiel_pet.models import Rect

WORK = Rect(0, 0, 1920, 1040)


def classic():
    return [W(90, "Application", 99, 0, WORK), W(1, "Progman", 7, 0, WORK),
            W(2, "SHELLDLL_DefView", 7, 1, WORK), W(3, "SysListView32", 7, 2, WORK),
            W(4, "WorkerW", 7, 0, WORK)]


def test_classic_and_nested_hosts():
    assert choose_host(classic(), 7, WORK).hwnd == 4
    nested = classic()[:4] + [W(4, "WorkerW", 7, 1, WORK)]
    assert choose_host(nested, 7, WORK).hwnd == 4


def test_no_foreign_hidden_small_above_or_icon_host():
    base = classic()
    for bad in [W(4, "WorkerW", 8, 0, WORK), W(4, "WorkerW", 7, 0, WORK, False),
                W(4, "WorkerW", 7, 0, Rect(0, 0, 800, 600))]:
        assert choose_host(base[:-1] + [bad], 7, WORK) is None
    assert choose_host([base[-1]] + base[:-1], 7, WORK) is None
    assert choose_host([W(1, "WorkerW", 7, 0, WORK), base[2]], 7, WORK) is None
    assert choose_host(base + [W(100, "UnknownApp", 8, 0, WORK)], 7, WORK) is None


class FakeAPI:
    def __init__(self):
        self.windows = classic()
    def shell_pid(self): return 7
    def snapshot(self): return self.windows
    def request_worker(self): pass
    def is_window(self, hwnd): return any(w.hwnd == hwnd for w in self.windows)
    def pid(self, hwnd): return next((w.pid for w in self.windows if w.hwnd == hwnd), 0)


class FakeSurface:
    def __init__(self, host):
        self.closed = False
        self.visible = False
    def safe(self): return True
    def close(self): self.closed, self.visible = True, False


def test_loss_hides_before_rediscovery_and_recovers_hidden():
    api = FakeAPI()
    session = HostSession(DesktopHost(api), FakeSurface)
    assert session.ensure(WORK)
    old = session.surface
    old.visible = True
    api.windows = []
    assert not session.ensure(WORK)
    assert old.closed and not old.visible and session.surface is None
    api.windows = classic()
    assert session.ensure(WORK)
    assert session.surface is not old and not session.surface.visible


def test_failed_attachment_never_keeps_a_surface():
    class Unsafe(FakeSurface):
        def safe(self): return False
    session = HostSession(DesktopHost(FakeAPI()), Unsafe)
    assert not session.ensure(WORK)
    assert session.surface is None


def test_handle_reuse_and_layer_reorder_invalidate_binding():
    api = FakeAPI()
    host = DesktopHost(api)
    host.discover(WORK)
    api.windows = classic()[:-1] + [W(4, "WorkerW", 88, 0, WORK)]
    assert not host.alive()
    api.windows = [classic()[-1]] + classic()[:-1]
    assert not host.validate(WORK)
