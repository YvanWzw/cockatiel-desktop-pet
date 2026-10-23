"""Conservative shell topology verification, independent of ctypes and Qt.

Only an Explorer wallpaper WorkerW behind the icon view is accepted. A HWND
by itself is insufficient. Unknown shell layouts stay hidden.
"""
from dataclasses import dataclass
import logging
from .models import Rect

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    cls: str
    pid: int
    parent: int
    rect: Rect
    visible: bool = True


@dataclass(frozen=True)
class HostBinding:
    hwnd: int
    icon: int
    root: int
    pid: int


def root_of(hwnd, by_id):
    seen = set()
    while hwnd in by_id and by_id[hwnd].parent:
        if hwnd in seen:
            return 0
        seen.add(hwnd)
        hwnd = by_id[hwnd].parent
    return hwnd


def choose_host(windows: list[WindowInfo], shell_pid: int, work: Rect) -> HostBinding | None:
    """Enumeration order is front-to-back, with descendants in sibling order."""
    by_id = {w.hwnd: w for w in windows}
    order = {w.hwnd: i for i, w in enumerate(windows)}
    icons = [w for w in windows if w.cls == "SHELLDLL_DefView" and w.pid == shell_pid and w.visible and w.rect.covers(work)]
    for candidate in windows:
        if candidate.cls != "WorkerW" or candidate.pid != shell_pid or not candidate.visible or not candidate.rect.covers(work):
            continue
        root = root_of(candidate.hwnd, by_id)
        if root not in by_id or by_id[root].cls not in {"Progman", "WorkerW"} or by_id[root].pid != shell_pid:
            continue
        # Wallpaper hosts must never contain the icon view.
        def within(hwnd, ancestor):
            seen = set()
            while hwnd in by_id and hwnd not in seen:
                if hwnd == ancestor:
                    return True
                seen.add(hwnd)
                hwnd = by_id[hwnd].parent
            return False
        if any(within(icon.hwnd, candidate.hwnd) for icon in icons):
            continue
        for icon in icons:
            icon_root = root_of(icon.hwnd, by_id)
            if icon_root not in by_id or by_id[icon_root].cls not in {"Progman", "WorkerW"} or by_id[icon_root].pid != shell_pid:
                continue
            # Classic: a separate wallpaper WorkerW below the icon root.
            classic = not candidate.parent and root != icon_root and order[root] > order[icon_root]
            # Newer shell: sibling wallpaper worker below DefView inside Progman.
            nested = root == icon_root and candidate.parent == icon.parent and order[candidate.hwnd] > order[icon.hwnd]
            if not (classic or nested):
                continue
            # A visible ordinary top-level application below this shell root
            # would make this layout ambiguous. Do not display anything there.
            if any(w.visible and not w.parent and order[w.hwnd] > order[root]
                   and w.cls not in {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"}
                   for w in windows):
                continue
            return HostBinding(candidate.hwnd, icon.hwnd, root, shell_pid)
    return None


class DesktopHost:
    def __init__(self, api):
        self.api = api
        self.binding = None

    def discover(self, work: Rect) -> HostBinding | None:
        self.binding = None
        pid = self.api.shell_pid()
        if not pid:
            return None
        windows = self.api.snapshot()
        found = choose_host(windows, pid, work)
        if not found:
            self.api.request_worker()
            windows = self.api.snapshot()
            found = choose_host(windows, pid, work)
        for w in windows:
            log.debug("shell scan hwnd=%#x class=%s pid=%d parent=%#x visible=%s rect=%s", w.hwnd, w.cls, w.pid, w.parent, w.visible, w.rect)
        self.binding = found
        log.info("Desktop host %s", found or "unavailable; hidden")
        return found

    def alive(self):
        b = self.binding
        return bool(b and self.api.is_window(b.hwnd) and self.api.is_window(b.icon)
                    and self.api.pid(b.hwnd) == b.pid and self.api.pid(b.icon) == b.pid)

    def validate(self, work):
        if not self.alive():
            return False
        return choose_host(self.api.snapshot(), self.api.shell_pid(), work) == self.binding


class HostSession:
    """Owns surface lifetime: destroy first, rediscover second, show last."""
    def __init__(self, host, factory):
        self.host = host
        self.factory = factory
        self.surface = None

    def drop(self):
        if self.surface:
            self.surface.close()
            self.surface = None

    def ensure(self, work):
        if self.surface and self.host.validate(work) and self.surface.safe():
            return True
        self.drop()
        if not self.host.discover(work):
            return False
        try:
            surface = self.factory(self.host)
            self.surface = surface
            if not surface.safe() or not self.host.validate(work):
                self.drop()
                return False
            return True  # Surface remains hidden until first successful present.
        except (OSError, RuntimeError):
            log.exception("Desktop surface creation failed; hidden")
            self.drop()
            return False
