"""Tests für vocix.wakeword — Threshold/Cooldown ohne reale Audio-Hardware."""
from __future__ import annotations

import threading
import time

import pytest

from vocix import wakeword


def test_is_available_returns_bool():
    assert isinstance(wakeword.is_available(), bool)


def test_handle_scores_below_threshold_no_trigger():
    triggered = []
    listener = wakeword.WakeWordListener(
        on_detect=lambda: triggered.append(time.monotonic()),
        threshold=0.5,
        cooldown=0.0,
    )
    listener._handle_scores({"hey_jarvis_v0.1": 0.3})
    assert triggered == []


def test_handle_scores_above_threshold_triggers():
    triggered = []
    listener = wakeword.WakeWordListener(
        on_detect=lambda: triggered.append(1),
        threshold=0.5,
        cooldown=0.0,
    )
    listener._handle_scores({"hey_jarvis_v0.1": 0.9})
    assert triggered == [1]


def test_cooldown_suppresses_repeat_triggers():
    triggered = []
    listener = wakeword.WakeWordListener(
        on_detect=lambda: triggered.append(1),
        threshold=0.5,
        cooldown=10.0,
    )
    listener._handle_scores({"x": 0.9})
    listener._handle_scores({"x": 0.95})
    listener._handle_scores({"x": 0.99})
    assert triggered == [1]


def test_cooldown_elapsed_allows_new_trigger():
    triggered = []
    listener = wakeword.WakeWordListener(
        on_detect=lambda: triggered.append(1),
        threshold=0.5,
        cooldown=0.05,
    )
    listener._handle_scores({"x": 0.9})
    time.sleep(0.1)
    listener._handle_scores({"x": 0.9})
    assert triggered == [1, 1]


def test_empty_scores_no_trigger():
    triggered = []
    listener = wakeword.WakeWordListener(
        on_detect=lambda: triggered.append(1),
        threshold=0.5,
    )
    listener._handle_scores({})
    assert triggered == []


def test_callback_exception_does_not_propagate():
    def boom():
        raise RuntimeError("kaboom")

    listener = wakeword.WakeWordListener(on_detect=boom, threshold=0.5, cooldown=0.0)
    # Soll nicht durchschlagen — der Run-Loop muss weiterlaufen können.
    listener._handle_scores({"x": 0.9})


def test_start_without_dependency_raises_runtimeerror(monkeypatch):
    monkeypatch.setattr(wakeword, "AVAILABLE", False)
    listener = wakeword.WakeWordListener(on_detect=lambda: None)
    with pytest.raises(RuntimeError):
        listener.start()


def test_stop_is_idempotent():
    listener = wakeword.WakeWordListener(on_detect=lambda: None)
    listener.stop()  # nichts läuft — sollte einfach durchgehen
    listener.stop()


def test_is_running_initial_false():
    listener = wakeword.WakeWordListener(on_detect=lambda: None)
    assert listener.is_running is False
