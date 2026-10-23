"""Exercise the real native child and app lifecycle without synthetic input.

Run with the pet closed: python scripts/smoke_windows.py --output work/smoke.json
The unavailable-host segment is simulated; Explorer is never restarted.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import sys

from cockatiel_pet.win32 import Win32, enable_dpi_awareness
from cockatiel_pet.state_machine import State


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("work/native-smoke.json"))
    args = parser.parse_args()
    enable_dpi_awareness()
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from cockatiel_pet.app import PetApplication, setup_logging
    setup_logging(True)
    qt = QApplication([])
    qt.setQuitOnLastWindowClosed(False)
    api = Win32()
    mutex = api.acquire_instance()
    if not mutex:
        print("Close the running pet before the smoke test.")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    checks, errors = [], []
    # Diagnostic geometry/foreground snapshots only; never store pointer samples.
    foreground = api.bind(api.u, "GetForegroundWindow", W.HWND)
    active = api.bind(api.u, "GetActiveWindow", W.HWND)
    with tempfile.TemporaryDirectory(prefix="cockatiel-smoke-", dir=args.output.parent) as temp:
        options = SimpleNamespace(config=Path(temp)/"config.json", seed=42, force_hidden=False, diagnostic_report=args.output)
        runtime = PetApplication(qt, api, options)
        def check(name, predicate):
            try:
                assert predicate(), name
                checks.append(name)
            except Exception as exc:
                errors.append(str(exc))
                qt.quit()
        def action(fn):
            def run():
                try: fn()
                except Exception as exc:
                    errors.append(repr(exc))
                    qt.quit()
            return run
        check("native child attached and safe", lambda: runtime.available and runtime.session.surface.safe())
        if not errors:
            QTimer.singleShot(200, action(runtime.fly))
            QTimer.singleShot(850, lambda: check("manual flight reached flying", lambda: runtime.controller.state == State.FLYING))
            QTimer.singleShot(900, action(runtime.toggle_pause))
            QTimer.singleShot(1200, lambda: check("paused flight settled with branch", lambda: runtime.controller.state == State.PAUSED and runtime.controller.branch_alpha == 1 and not runtime.animation.isActive() and not runtime.mouse_timer.isActive()))
            QTimer.singleShot(1400, action(runtime.toggle_pause))
            QTimer.singleShot(1500, action(runtime.fly))
            QTimer.singleShot(10600, lambda: check("complete takeoff flight landing cycle", lambda: {"perched","takeoff","flying","landing","paused"}.issubset(runtime.states)))
            snapshot, request = api.snapshot, api.request_worker
            def lose_host():
                api.snapshot = lambda: []
                api.request_worker = lambda: None
                runtime.health()
                check("unavailable host destroyed drawing child", lambda: not runtime.available and runtime.session.surface is None)
            def restore_host():
                api.snapshot, api.request_worker = snapshot, request
                runtime.health()
                check("host recovery recreated safe child", lambda: runtime.available and runtime.session.surface.safe())
            QTimer.singleShot(10800, action(lose_host))
            QTimer.singleShot(11300, action(restore_host))
            QTimer.singleShot(11600, action(runtime.toggle_mouse))
            QTimer.singleShot(11800, lambda: check("interaction toggle persisted", lambda: not runtime.store.load().mouse_interaction_enabled and not runtime.mouse_timer.isActive()))
            QTimer.singleShot(12000, action(runtime.toggle_mouse))
            QTimer.singleShot(12200, lambda: check("pet did not activate a window", lambda: not active() and api.pid(foreground()) != __import__('os').getpid()))
            QTimer.singleShot(12300, action(runtime.tray.modes["front"].trigger))
            QTimer.singleShot(12600, lambda: check("tray front mode created safe topmost mouse-through surface", lambda: runtime.display_mode == "front" and runtime.available and runtime.session.surface.safe() and runtime.store.load().display_mode == "front"))
            QTimer.singleShot(12800, action(runtime.tray.modes["hidden"].trigger))
            QTimer.singleShot(13100, lambda: check("tray hidden mode destroyed surface and stopped painting", lambda: runtime.display_mode == "hidden" and runtime.session.surface is None and not runtime.animation.isActive() and runtime.store.load().display_mode == "hidden"))
            QTimer.singleShot(13300, action(runtime.tray.modes["front"].trigger))
            QTimer.singleShot(13600, action(runtime.tray.modes["desktop"].trigger))
            QTimer.singleShot(13900, lambda: check("tray returned to verified desktop child", lambda: runtime.display_mode == "desktop" and runtime.available and runtime.session.surface.safe() and not active()))
            QTimer.singleShot(14100, qt.quit)
            qt.exec()
        runtime.close()
        check("quit destroyed child and timers", lambda: runtime.session.surface is None and not runtime.heartbeat.isActive() and not runtime.animation.isActive())
    api.k.CloseHandle(mutex)
    report = json.loads(args.output.read_text()) if args.output.exists() else {}
    report.update(checks=checks, errors=errors, real_explorer_restart_tested=False, visual_click_through_manually_verified=False)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
