"""Test the shipped GUI executable, duplicate launch, hidden mode and pause.

No synthetic input or Explorer manipulation. A pet is visible behind desktop
icons for about 25 seconds if a compatible shell host is available.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=Path("dist/CockatielDesktopPet/CockatielDesktopPet.exe"))
    parser.add_argument("--output", type=Path, default=Path("work/bundle-smoke.json"))
    args = parser.parse_args()
    exe = args.exe.resolve(strict=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {}
    with tempfile.TemporaryDirectory(prefix="cockatiel-bundle-", dir=args.output.parent) as temp:
        folder = Path(temp).resolve()
        config = folder / "config.json"
        config.write_text(json.dumps({"schema_version":1, "idle_min_seconds":10, "idle_max_seconds":10}))
        active_report = folder / "active.json"
        duplicate_report = folder / "duplicate.json"
        base = [str(exe), "--config", str(config), "--seed", "42"]
        process = subprocess.Popen(base + ["--run-seconds","25","--diagnostic-report",str(active_report)], creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            time.sleep(2)
            duplicate = subprocess.run(base+["--run-seconds","1","--diagnostic-report",str(duplicate_report)], timeout=12, creationflags=subprocess.CREATE_NO_WINDOW)
            assert duplicate.returncode == 0 and not duplicate_report.exists(), "Duplicate launch created a second runtime"
            assert process.wait(timeout=35) == 0, "Packaged active run failed"
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        report["active"] = json.loads(active_report.read_text())
        assert report["active"]["available_at_exit"] and report["active"]["native_safe_at_exit"], "No compatible native host"
        assert {"perched","takeoff","flying","landing"}.issubset(report["active"]["states"]), "Autonomous cycle did not complete"
        report["single_instance"] = True
        for name, flags, cfg in (("hidden",[],{"display_mode":"hidden"}), ("front",[],{"display_mode":"front"}), ("paused",[],{"paused":True})):
            config.write_text(json.dumps({"schema_version":1, **cfg}))
            output = folder / f"{name}.json"
            result = subprocess.run(base + flags + ["--run-seconds","3","--diagnostic-report",str(output)], timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
            assert result.returncode == 0, f"Packaged {name} run failed"
            report[name] = json.loads(output.read_text())
        assert report["hidden"]["frames"] == 0 and not report["hidden"]["native_safe_at_exit"], "Hidden mode created a visual child"
        assert report["front"]["display_mode"] == "front" and report["front"]["native_safe_at_exit"], "Front mode failed"
        assert report["paused"]["states"] == ["paused"] and report["paused"]["frames"] <= 3, "Paused mode repainted continuously"
    report["manual_visual_acceptance"] = "not yet verified"
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
