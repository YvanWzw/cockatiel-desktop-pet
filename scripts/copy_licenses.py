"""Include all license/notice metadata shipped by our redistributable wheels."""
import argparse
import importlib.metadata
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    python_license = next((p for p in (Path(sys.base_prefix)/"LICENSE.txt", Path(sys.base_prefix)/"LICENSE_PYTHON.txt", Path(sys.base_prefix)/"LICENSE") if p.is_file()), None)
    if not python_license:
        raise RuntimeError("Python distribution license was not found")
    args.output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(python_license, args.output/"PYTHON-LICENSE.txt")
    bundled = Path(__file__).resolve().parents[1] / "licenses"
    if bundled.is_dir():
        shutil.copytree(bundled, args.output, dirs_exist_ok=True)
    for name in ("PySide6-Essentials", "shiboken6", "pyinstaller"):
        dist = importlib.metadata.distribution(name)
        copied = 0
        for file in dist.files or []:
            if any(token in file.name.lower() for token in ("license", "copying", "notice")):
                source = Path(dist.locate_file(file))
                if source.is_file():
                    target = args.output / name / file
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
                    copied += 1
        if not copied:
            raise RuntimeError(f"No license files found for {name}")


if __name__ == "__main__":
    main()
