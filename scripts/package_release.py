"""Archive the complete runtime folder and clean source tree; include checksums."""
import argparse
import hashlib
from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=root.parent)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    bundle = root / "dist" / "CockatielDesktopPet"
    if not (bundle / "CockatielDesktopPet.exe").is_file():
        raise RuntimeError("Run scripts/build_windows.ps1 first")
    packages = (("CockatielDesktopPet-Windows-x64.zip", bundle, "CockatielDesktopPet", False),
                ("CockatielDesktopPet-source.zip", root, "CockatielDesktopPet-source", True))
    checksums = []
    for name, source, prefix, is_source in packages:
        output = args.output / name
        with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for file in sorted(source.rglob("*")):
                relative = file.relative_to(source)
                if not file.is_file():
                    continue
                if is_source and any(part in {"work","dist","build",".venv","__pycache__",".pytest_cache",".git"} or part.endswith(".egg-info") for part in relative.parts):
                    continue
                if file.suffix == ".pyc":
                    continue
                archive.write(file,Path(prefix)/relative)
        with zipfile.ZipFile(output) as archive:
            if archive.testzip() is not None:
                raise RuntimeError(f"Corrupt archive: {output}")
        with output.open("rb") as stream:
            digest = hashlib.file_digest(stream,"sha256").hexdigest()
        checksums.append(f"{digest}  {name}")
        print(f"{output}: {output.stat().st_size:,} bytes")
    (args.output/"SHA256SUMS.txt").write_text("\n".join(checksums)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
