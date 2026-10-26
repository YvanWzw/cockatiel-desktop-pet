"""Check the packaged front window's actual native hit result, without input."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import subprocess
import tempfile
import time
from cockatiel_pet.win32 import Win32, enable_dpi_awareness, EX_REQUIRED


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=Path("dist/CockatielDesktopPet/CockatielDesktopPet.exe"))
    parser.add_argument("--output", type=Path, default=Path("work/front-hit.json"))
    args = parser.parse_args()
    enable_dpi_awareness()
    api = Win32()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cockatiel-hit-", dir=args.output.parent) as temp:
        folder = Path(temp).resolve()
        config = folder / "config.json"
        config.write_text(json.dumps({"schema_version":1,"display_mode":"front"}))
        process = subprocess.Popen([str(args.exe.resolve()),"--config",str(config),"--run-seconds","4"],creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            time.sleep(1.5)
            front = next(w for w in api.snapshot() if w.pid == process.pid and w.cls.startswith("CockatielFrontSurface_"))
            _, scale = api.primary_display()
            # This is an opaque pixel inside the front-facing bird's face,
            # not a transparent corner. No cursor movement or click is sent.
            from cockatiel_pet.renderer import CockatielRenderer,Pose
            assert CockatielRenderer().image(Pose(paused=True)).pixelColor(140,85).alpha()>128
            point = W.POINT(round(front.rect.left + 140*scale), round(front.rect.top + 85*scale))
            hit = api.u.WindowFromPoint(point)
            ex = api.u.GetWindowLongPtrW(front.hwnd,-20)
            assert front.visible and ex & (EX_REQUIRED | 8) == EX_REQUIRED | 8
            assert hit and hit != front.hwnd and api.pid(hit) != process.pid, "Front window intercepted native hit testing"
            report = {"topmost_and_noactivate_styles":True,"visible_native_window":True,
                      "opaque_bird_pixel_hit_passed_to_another_process":True,"synthetic_input_used":False,
                      "manual_click_acceptance":"not yet verified"}
            assert process.wait(timeout=10) == 0
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
