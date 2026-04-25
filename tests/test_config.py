"""Tests für Config — Persistenz des translate_to_english-Flags."""
from __future__ import annotations

import json

import pytest

from vocix import config as config_module


@pytest.fixture
def isolated_state(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(config_module, "STATE_FILE", state_file)
    return state_file


def test_translate_default_is_false():
    cfg = config_module.Config()
    assert cfg.translate_to_english is False


def test_save_and_load_translate_flag(isolated_state):
    config_module.save_state({"translate_to_english": True})

    state = config_module.load_state()
    assert state["translate_to_english"] is True


def test_config_load_reads_translate_flag_from_state(isolated_state, tmp_path, monkeypatch):
    isolated_state.parent.mkdir(parents=True, exist_ok=True)
    isolated_state.write_text(
        json.dumps({"translate_to_english": True}), encoding="utf-8"
    )

    cfg = config_module.Config.load(env_file=tmp_path / "does-not-exist.env")
    assert cfg.translate_to_english is True


def test_config_load_defaults_when_flag_missing(isolated_state, tmp_path):
    isolated_state.parent.mkdir(parents=True, exist_ok=True)
    isolated_state.write_text(json.dumps({"language": "de"}), encoding="utf-8")

    cfg = config_module.Config.load(env_file=tmp_path / "does-not-exist.env")
    assert cfg.translate_to_english is False
