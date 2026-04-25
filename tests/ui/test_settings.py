import tkinter as tk
from dataclasses import replace

import pytest

from vocix.config import Config
from vocix.ui.settings import SettingsDialog


@pytest.fixture
def root():
    try:
        r = tk.Tk()
    except tk.TclError:
        pytest.skip("Kein Display verfuegbar")
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def base_config():
    return Config(language="de", whisper_model="small", whisper_acceleration="auto")


def test_dialog_opens_with_three_tabs(root, base_config):
    dlg = SettingsDialog(root, config=base_config, on_apply=lambda c: None)
    assert dlg.notebook is not None
    assert len(dlg.notebook.tabs()) == 3
    dlg.destroy()


def test_dialog_cancel_calls_no_apply(root, base_config):
    called = {"n": 0}
    dlg = SettingsDialog(root, config=base_config, on_apply=lambda c: called.update(n=called["n"] + 1))
    dlg._on_cancel()
    assert called["n"] == 0


def test_dialog_apply_calls_callback_with_config_copy(root, base_config):
    received = []
    dlg = SettingsDialog(root, config=base_config, on_apply=lambda c: received.append(c))
    dlg._on_apply()
    assert len(received) == 1
    assert received[0] is not base_config
    assert received[0].language == "de"
    dlg.destroy()
