"""Milestone A: bounded native proof, opaque then transparent pass-through.

No synthetic input, focus changes, Explorer restarts, or application control.
Run from an installed editable package: python scripts/desktop_probe.py.
"""
import argparse
import json
import logging
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPainter, QColor
from cockatiel_pet.win32 import Win32, enable_dpi_awareness
from cockatiel_pet.desktop_host import DesktopHost, HostSession
from cockatiel_pet.pet_surface import PetSurface
from cockatiel_pet.models import Point


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=8)
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    enable_dpi_awareness()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    api = Win32()
    work, dpi = api.primary_display()
    session = HostSession(DesktopHost(api), PetSurface)
    report = {"work": repr(work), "dpi": dpi, "attached": False, "presented": False}
    try:
        report["attached"] = session.ensure(work)
        if not report["attached"]:
            print(json.dumps(report))
            return 2
        start = time.monotonic()
        foreground = api.bind(api.u, "GetForegroundWindow", __import__('ctypes').wintypes.HWND)
        before = foreground()
        def frame():
            try:
                image = QImage(180, 140, QImage.Format.Format_ARGB32_Premultiplied)
                image.fill(QColor("#f4c95b") if time.monotonic() - start < 2 else Qt.GlobalColor.transparent)
                p = QPainter(image)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor("#edb341"))
                p.drawEllipse(50, 25, 80, 90)
                p.end()
                session.surface.present(image, Point(work.right - 300, work.bottom - 230))
                report.update(presented=True, safe=session.surface.safe(), foreground_unchanged=before == foreground())
            except (OSError, RuntimeError) as exc:
                report["error"] = str(exc)
                session.drop()
                app.quit()
        timer = QTimer()
        timer.timeout.connect(frame)
        timer.start(100)
        QTimer.singleShot(args.seconds * 1000, app.quit)
        app.exec()
    finally:
        session.drop()
    print(json.dumps(report))
    return 0 if report.get("presented") and report.get("safe") else 2


if __name__ == "__main__":
    raise SystemExit(main())
