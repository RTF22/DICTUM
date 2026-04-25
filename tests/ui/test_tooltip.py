import tkinter as tk

import pytest

from vocix.ui.tooltip import Tooltip


@pytest.fixture
def root():
    try:
        r = tk.Tk()
    except tk.TclError:
        pytest.skip("Kein Display verfügbar")
    r.withdraw()
    yield r
    r.destroy()


def test_tooltip_shows_after_delay(root):
    label = tk.Label(root, text="hover me")
    label.pack()
    tip = Tooltip(label, text_provider=lambda: "Hilfetext")
    tip._show()
    assert tip._tip_window is not None
    assert tip._tip_window.winfo_exists()
    tip._hide()
    assert tip._tip_window is None


def test_tooltip_hide_destroys_window(root):
    label = tk.Label(root)
    tip = Tooltip(label, text_provider=lambda: "x")
    tip._show()
    tw = tip._tip_window
    tip._hide()
    assert not tw.winfo_exists()


def test_tooltip_uses_provider_each_time(root):
    label = tk.Label(root)
    calls = {"n": 0}

    def provider():
        calls["n"] += 1
        return f"call {calls['n']}"

    tip = Tooltip(label, text_provider=provider)
    tip._show()
    text1 = tip._label.cget("text")
    tip._hide()
    tip._show()
    text2 = tip._label.cget("text")
    assert text1 == "call 1"
    assert text2 == "call 2"
