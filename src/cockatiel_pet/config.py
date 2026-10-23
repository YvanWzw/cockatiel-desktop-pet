"""Validated configuration and atomic, best-effort persistence."""
from dataclasses import asdict, dataclass
import json
import logging
import math
import os
from pathlib import Path
import tempfile

log = logging.getLogger(__name__)


@dataclass
class Config:
    schema_version: int = 1
    pet_scale: float = 1.0
    mouse_interaction_enabled: bool = True
    paused: bool = False
    display_mode: str = "desktop"
    idle_min_seconds: float = 20
    idle_max_seconds: float = 55
    active_fps: int = 30
    idle_fps: int = 12
    audio_enabled: bool = False
    show_on_primary_monitor_only: bool = True

    @classmethod
    def validate(cls, raw):
        c = cls()
        if not isinstance(raw, dict) or type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
            return c
        bounds = {"pet_scale": (.5, 2), "idle_min_seconds": (10, 600), "idle_max_seconds": (10, 600),
                  "active_fps": (15, 60), "idle_fps": (5, 15)}
        for name, (low, high) in bounds.items():
            v = raw.get(name)
            if type(v) in (int, float) and math.isfinite(v):
                v = min(high, max(low, v))
                setattr(c, name, int(v) if name.endswith("fps") else float(v))
        c.idle_max_seconds = max(c.idle_min_seconds, c.idle_max_seconds)
        c.idle_fps = min(c.idle_fps, c.active_fps)
        if raw.get("display_mode") in ("desktop", "front", "hidden"):
            c.display_mode = raw["display_mode"]
        for name in ("mouse_interaction_enabled", "paused"):
            if type(raw.get(name)) is bool:
                setattr(c, name, raw[name])
        # Audio and multi-monitor roaming are intentionally not implemented.
        return c


def app_data_dir():
    return Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))) / "CockatielDesktopPet"


class ConfigStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else app_data_dir() / "config.json"

    def load(self):
        try:
            if self.path.stat().st_size > 65536:
                raise ValueError("Configuration too large")
            return Config.validate(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError, RecursionError):
            log.info("Missing/invalid configuration; using safe defaults")
            return Config()

    def save(self, config):
        temp = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            validated = Config.validate(asdict(config))
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, prefix="config-", suffix=".tmp", delete=False) as f:
                temp = Path(f.name)
                json.dump(asdict(validated), f, indent=2, allow_nan=False)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, self.path)
            return True
        except (OSError, ValueError):
            log.exception("Could not save configuration")
            return False
        finally:
            if temp:
                try:
                    temp.unlink(missing_ok=True)
                except OSError:
                    log.warning("Could not remove temporary configuration file")
