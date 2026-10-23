from dataclasses import asdict
import json
from cockatiel_pet.config import Config, ConfigStore


def test_defaults_missing_malformed_and_unknown_schema(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    assert store.load() == Config()
    for text in ("broken", "[]", "null", '{"schema_version":2}', '{"schema_version":true}'):
        store.path.write_text(text)
        assert store.load() == Config()


def test_bounds_types_and_no_audio_or_multi_monitor():
    c = Config.validate({"schema_version":1, "pet_scale":999, "idle_min_seconds":100, "idle_max_seconds":2,
                         "active_fps":1, "idle_fps":999, "paused":"false", "mouse_interaction_enabled":False,
                         "audio_enabled":True, "show_on_primary_monitor_only":False})
    assert c.pet_scale == 2 and c.idle_max_seconds == c.idle_min_seconds == 100
    assert c.active_fps == c.idle_fps == 15
    assert not c.paused and not c.mouse_interaction_enabled and not c.audio_enabled
    assert c.show_on_primary_monitor_only
    assert Config.validate({"schema_version":1, "pet_scale":float("nan"), "active_fps":True}) == Config()


def test_atomic_roundtrip_and_no_temporary_files(tmp_path):
    store = ConfigStore(tmp_path / "folder" / "config.json")
    c = Config(paused=True, pet_scale=1.25)
    assert store.save(c)
    assert store.load() == c
    assert list(store.path.parent.glob("*.tmp")) == []
    assert json.loads(store.path.read_text()) == asdict(c)


def test_unwritable_path_is_nonfatal(tmp_path):
    file = tmp_path / "file"
    file.write_text("obstruct parent")
    assert not ConfigStore(file / "config.json").save(Config())


def test_display_modes_persist_and_unknown_modes_use_desktop(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    for mode in ("desktop", "front", "hidden"):
        c = Config(display_mode=mode)
        assert store.save(c)
        assert store.load().display_mode == mode
    assert Config.validate({"schema_version":1,"display_mode":"unexpected"}).display_mode == "desktop"
