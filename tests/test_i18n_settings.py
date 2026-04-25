import json
from pathlib import Path

REQUIRED_KEYS = [
    "settings.title",
    "settings.tab.basics", "settings.tab.advanced", "settings.tab.expert",
    "settings.button.ok", "settings.button.cancel", "settings.button.apply",
    "settings.button.test", "settings.button.browse", "settings.button.other_key",
    "settings.button.reset", "settings.button.open_config_dir",
    "settings.field.input_language", "settings.field.output_language",
    "settings.field.whisper_model", "settings.field.acceleration",
    "settings.field.api_key", "settings.field.default_mode",
    "settings.field.hotkey_record", "settings.field.hotkey_mode_a",
    "settings.field.hotkey_mode_b", "settings.field.hotkey_mode_c",
    "settings.field.model_dir", "settings.field.log_file", "settings.field.log_level",
    "settings.field.overlay_seconds", "settings.field.rdp_mode",
    "settings.field.clipboard_delay", "settings.field.paste_delay",
    "settings.field.silence_threshold", "settings.field.min_duration",
    "settings.field.whisper_language_override", "settings.field.sample_rate",
    "settings.field.anthropic_model", "settings.field.anthropic_timeout",
    "settings.tooltip.input_language", "settings.tooltip.output_language",
    "settings.tooltip.whisper_model", "settings.tooltip.acceleration",
    "settings.tooltip.api_key", "settings.tooltip.default_mode",
    "settings.tooltip.hotkey_record", "settings.tooltip.rdp_mode",
    "settings.tooltip.silence_threshold", "settings.tooltip.sample_rate",
    "settings.help.whisper_model.title", "settings.help.whisper_model.body",
    "settings.help.acceleration.title", "settings.help.acceleration.body",
    "settings.help.api_key.title", "settings.help.api_key.body",
    "settings.help.rdp_mode.title", "settings.help.rdp_mode.body",
    "settings.help.silence_threshold.title", "settings.help.silence_threshold.body",
    "settings.help.sample_rate.title", "settings.help.sample_rate.body",
    "settings.help.whisper_language_override.title",
    "settings.help.whisper_language_override.body",
    "settings.help.anthropic_model.title", "settings.help.anthropic_model.body",
    "settings.status.api_valid", "settings.status.api_invalid", "settings.status.api_unchecked",
    "settings.status.api_locked",
    "settings.error.duplicate_hotkey", "settings.error.ptt_combo_not_allowed",
    "settings.error.path_missing", "settings.confirm.factory_reset",
    "settings.lang.de", "settings.lang.en", "settings.lang.other",
    "settings.output.input_lang", "settings.output.english",
    "settings.modifier.none", "settings.modifier.ctrl", "settings.modifier.ctrl_shift",
    "settings.modifier.ctrl_alt", "settings.modifier.alt_shift",
    "settings.capture.prompt", "settings.capture.cancel_hint",
    "tray.settings",
]


def _flatten(d, prefix=""):
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from _flatten(v, path)
        else:
            yield path


def _load(name):
    p = Path(__file__).resolve().parent.parent / "vocix" / "locales" / name
    return set(_flatten(json.loads(p.read_text(encoding="utf-8"))))


def test_de_has_all_settings_keys():
    keys = _load("de.json")
    missing = [k for k in REQUIRED_KEYS if k not in keys]
    assert not missing, f"Missing in de.json: {missing}"


def test_en_has_all_settings_keys():
    keys = _load("en.json")
    missing = [k for k in REQUIRED_KEYS if k not in keys]
    assert not missing, f"Missing in en.json: {missing}"
