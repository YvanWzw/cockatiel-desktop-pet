"""Qt orchestration for desktop, explicit front-of-apps, and hidden modes."""
import argparse
from dataclasses import asdict
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import struct
import os
import sys
import time

from . import __version__
from .config import ConfigStore, app_data_dir

log = logging.getLogger(__name__)


def setup_logging(debug=False):
    logger = logging.getLogger("cockatiel_pet")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        folder = app_data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(folder / "desktop.log", maxBytes=256_000, backupCount=2, encoding="utf-8")
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class PetApplication:
    def __init__(self, qt, api, options):
        from PySide6.QtCore import QTimer
        from .renderer import CockatielRenderer
        from .state_machine import PetController
        from .mouse_observer import MouseObserver
        from .models import effective_scale
        from .tray import TrayController
        self.qt, self.api, self.options = qt, api, options
        self.store = ConfigStore(options.config)
        self.config = self.store.load()
        self.work, self.dpi = api.primary_display()
        self.scale = effective_scale(self.work, self.dpi, self.config.pet_scale)
        self.controller = PetController(self.work, self.scale, options.seed, self.config.idle_min_seconds,
                                        self.config.idle_max_seconds, self.config.paused)
        self.renderer, self.observer = CockatielRenderer(), MouseObserver()
        self.create_session()
        self.last_frame = time.monotonic()
        self.started = self.last_frame
        self.cpu_started = time.process_time()
        self.frames = 0
        self.states = set()
        self.modes_seen = set()
        self.available = False
        self.notified = False
        self.closing = False
        self.tray = TrayController(self.renderer.icon(), self.toggle_pause, self.fly, self.toggle_mouse, self.set_display_mode, qt.quit)
        self.animation = QTimer()
        self.animation.timeout.connect(self.frame)
        self.mouse_timer = QTimer()
        self.mouse_timer.setInterval(50)  # 20 Hz, independent of animation FPS.
        self.mouse_timer.timeout.connect(self.pointer)
        self.heartbeat = QTimer()
        self.heartbeat.setInterval(3000)
        self.heartbeat.timeout.connect(self.health)
        self.tray.menu.aboutToShow.connect(self.sync_tray)
        qt.aboutToQuit.connect(self.close)
        qt.primaryScreenChanged.connect(self.topology_changed)
        qt.screenAdded.connect(self.watch_screen)
        qt.screenRemoved.connect(self.topology_changed)
        for screen in qt.screens():
            self.watch_screen(screen)
        self.heartbeat.start()
        self.health()

    def watch_screen(self, screen):
        for signal in (screen.geometryChanged, screen.availableGeometryChanged, screen.logicalDotsPerInchChanged):
            signal.connect(self.topology_changed)
        self.topology_changed()

    def topology_changed(self, *_):
        # Tear down immediately. A changed display may invalidate child geometry.
        if self.closing:
            return
        from PySide6.QtCore import QTimer
        self.session.drop()
        self.available = False
        self.animation.stop()
        self.mouse_timer.stop()
        QTimer.singleShot(100, self.health)

    def sync_tray(self):
        from .state_machine import State
        self.tray.sync(self.config.paused, self.config.mouse_interaction_enabled, self.available,
                       self.controller.state not in (State.PERCHED, State.REACTING), self.display_mode)

    @property
    def display_mode(self):
        return "hidden" if self.options.force_hidden else self.config.display_mode

    def create_session(self):
        from .desktop_host import DesktopHost, HostSession
        from .pet_surface import PetSurface, FrontSurface, FrontHost
        self.host = FrontHost(self.api) if self.display_mode == "front" else DesktopHost(self.api)
        self.session = HostSession(self.host, FrontSurface if self.display_mode == "front" else PetSurface)

    def set_display_mode(self, mode):
        if mode not in ("desktop", "front", "hidden") or mode == self.config.display_mode:
            return
        # Destroy the old surface before changing hosting strategies. There is
        # never an automatic transition from desktop failure to front mode.
        self.session.drop()
        self.animation.stop()
        self.mouse_timer.stop()
        self.available = False
        self.observer.previous = None
        self.observer.hover_since = None
        self.config.display_mode = mode
        self.store.save(self.config)
        self.create_session()
        self.last_frame = time.monotonic()
        log.info("User selected display mode: %s", mode)
        self.health()

    def schedule(self):
        from .state_machine import State
        if not self.available or self.config.paused:
            self.animation.stop()
        else:
            moving = self.controller.state in (State.TAKEOFF, State.FLYING, State.LANDING, State.REACTING)
            fps = self.config.active_fps if moving else self.config.idle_fps
            interval = round(1000 / fps)
            if not self.animation.isActive() or self.animation.interval() != interval:
                self.animation.start(interval)
        if self.available and self.config.mouse_interaction_enabled and not self.config.paused:
            if not self.mouse_timer.isActive(): self.mouse_timer.start()
        else:
            self.mouse_timer.stop()
            self.observer.previous = None

    def health(self):
        if self.closing:
            return
        from .models import effective_scale
        try:
            work, dpi = self.api.primary_display()
            self.dpi = dpi
            scale = effective_scale(work, dpi, self.config.pet_scale)
            if work != self.work or scale != self.scale:
                self.session.drop()
                self.work, self.dpi, self.scale = work, dpi, scale
                self.controller.resize(work, scale)
            was_missing = self.session.surface is None
            if self.display_mode == "hidden":
                self.session.drop()
                self.available = False
            else:
                self.available = self.session.ensure(work)
            if self.available and was_missing:
                self.last_frame = time.monotonic()
                self.render()
        except Exception:
            log.exception("Desktop validation failed; hiding child")
            self.session.drop()
            self.available = False
        if not self.available and not self.notified and self.display_mode != "hidden":
            self.tray.unavailable(self.display_mode)
            self.notified = True
        elif self.available:
            self.notified = False
        self.schedule()
        self.sync_tray()

    def frame(self):
        if self.closing or not self.available:
            return
        try:
            if not self.session.surface or not self.session.surface.safe():
                raise RuntimeError("Wallpaper host lost")
            now = time.monotonic()
            self.controller.update(now - self.last_frame)
            self.last_frame = now
            self.render()
        except Exception:
            log.exception("Surface failure; hiding immediately")
            self.session.drop()
            self.available = False
            self.observer.previous = None
        self.schedule()

    def render(self):
        from .models import surface_origin
        self.session.surface.present(self.renderer.image(self.controller.pose(), self.scale),
                                     surface_origin(self.controller.position, self.scale))
        self.frames += 1
        self.states.add(self.controller.state.value)
        self.modes_seen.add(self.display_mode)

    def pointer(self):
        if not self.available or not self.host.alive():
            self.observer.previous = None
            return
        from .mouse_observer import PointerSample
        from .state_machine import State
        raw = self.api.pointer(self.host.binding if self.display_mode == "desktop" else None)
        if raw and self.display_mode == "front":
            raw = (raw[0], raw[1], True)  # Explicit front mode can react over apps.
        sample = PointerSample(*raw) if raw else None
        response = self.observer.observe(sample, time.monotonic(), self.controller.position, self.scale,
                                         self.controller.facing, self.config.mouse_interaction_enabled)
        self.controller.look_target = response.look
        if response.reaction and self.controller.state == State.PERCHED:
            self.controller.react(response.reaction)
            self.schedule()

    def toggle_pause(self):
        self.config.paused = not self.config.paused
        self.controller.set_paused(self.config.paused)
        self.last_frame = time.monotonic()
        self.store.save(self.config)
        if self.available:
            self.frame()  # One static frame; then stop the animation timer.
        self.schedule()
        self.sync_tray()

    def fly(self):
        if self.available and self.controller.fly_now():
            self.last_frame = time.monotonic()
            self.schedule()
            self.sync_tray()

    def toggle_mouse(self):
        self.config.mouse_interaction_enabled = not self.config.mouse_interaction_enabled
        self.observer.previous = None
        self.observer.hover_since = None
        self.controller.look_target = 0
        self.store.save(self.config)
        self.schedule()
        self.sync_tray()

    def close(self):
        if self.closing:
            return
        self.closing = True
        for timer in (self.animation, self.mouse_timer, self.heartbeat):
            timer.stop()
        elapsed = max(.001, time.monotonic() - self.started)
        cpu_percent = (time.process_time() - self.cpu_started) / elapsed * 100
        report = {"version": __version__, "windows_build": sys.getwindowsversion().build,
                  "elapsed_seconds": round(elapsed, 3), "cpu_one_core_percent": round(cpu_percent, 3),
                  "cpu_whole_machine_percent": round(cpu_percent / (os.cpu_count() or 1), 3),
                  "working_set_mib": self.api.process_memory_mib(),
                  "frames": self.frames, "states": sorted(self.states), "available_at_exit": self.available,
                  "display_mode": self.display_mode, "display_modes_seen": sorted(self.modes_seen),
                  "native_safe_at_exit": bool(self.session.surface and self.session.surface.safe()),
                  "physical_work_area": asdict(self.work), "dpi_scale": self.dpi, "artwork_scale": self.scale}
        self.session.drop()
        self.tray.close()
        self.store.save(self.config)
        if self.options.diagnostic_report:
            try:
                Path(self.options.diagnostic_report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            except OSError:
                log.exception("Could not save diagnostic report")
        log.info("Clean shutdown: frames=%d elapsed=%.1fs", self.frames, elapsed)


def main(argv=None):
    parser = argparse.ArgumentParser(description="A silent cockatiel: desktop, in front of apps, or hidden from the tray.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--debug-desktop-host", action="store_true", help="Log shell handles/classes and state transitions; never pointer samples")
    parser.add_argument("--seed", type=int, help="Repeatable behavior for diagnostics")
    parser.add_argument("--config", type=Path, help="Override configuration location")
    parser.add_argument("--diagnose", action="store_true", help="Print shell topology result and exit, without a visual child")
    parser.add_argument("--run-seconds", type=float, help="Exit automatically after this many seconds (smoke tests)")
    parser.add_argument("--diagnostic-report", type=Path, help="Write a pointer-free lifecycle/performance report at exit")
    parser.add_argument("--force-hidden", action="store_true", help="Exercise tray-only failure mode without creating a surface")
    options = parser.parse_args(argv)
    if sys.platform != "win32" or struct.calcsize("P") != 8:
        print("Cockatiel Desktop Pet supports Windows 10/11 x64 only.", file=sys.stderr)
        return 1
    from .win32 import Win32, enable_dpi_awareness
    enable_dpi_awareness()
    try:
        from PySide6.QtWidgets import QApplication, QSystemTrayIcon
        from PySide6.QtCore import QTimer
    except ImportError:
        print('Install dependencies first: python -m pip install -e ".[dev]"', file=sys.stderr)
        return 1
    setup_logging(options.debug_desktop_host)
    api = Win32()
    mutex = api.acquire_instance()
    if not mutex:
        print("Cockatiel Desktop Pet is already running. Use its system tray menu.")
        return 0
    runtime = None
    try:
        qt = QApplication([sys.argv[0]])
        qt.setApplicationName("Cockatiel Desktop Pet")
        qt.setOrganizationName("CockatielDesktopPet")
        qt.setQuitOnLastWindowClosed(False)
        if options.diagnose:
            from .desktop_host import DesktopHost
            work, dpi = api.primary_display()
            host = DesktopHost(api)
            binding = host.discover(work)
            print(json.dumps({"windows_build": sys.getwindowsversion().build, "work_area": asdict(work), "dpi_scale": dpi,
                              "host": asdict(binding) if binding else None}, indent=2))
            return 0 if binding else 2
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log.error("Windows system tray unavailable; no pet created")
            print("Windows system tray is unavailable; Cockatiel was not started.", file=sys.stderr)
            return 2
        runtime = PetApplication(qt, api, options)
        if options.run_seconds is not None:
            QTimer.singleShot(max(1, round(options.run_seconds * 1000)), qt.quit)
        return qt.exec()
    except Exception:
        log.exception("Startup failed; no floating-window fallback")
        return 1
    finally:
        if runtime:
            runtime.close()
        api.k.CloseHandle(mutex)


if __name__ == "__main__":
    raise SystemExit(main())
