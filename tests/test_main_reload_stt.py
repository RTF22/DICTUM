"""Tests für VocixApp._reload_stt — Worker-Thread, Lock, Exception-Pfad, State.

Konstruiert eine minimale Harness mit Mocks statt VocixApp.__init__ aufzurufen
(letzteres lädt Whisper, baut Tray, hooked Hotkeys — viel zu schwer für Unit).
"""
from __future__ import annotations

import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from vocix import main as main_module
from vocix.config import Config


def _make_harness(monkeypatch, tmp_path, *, model="small", acceleration="auto"):
    """Liefert ein VocixApp-Stand-In, das nur _reload_stt-Bedürfnisse erfüllt."""
    cfg = Config()
    cfg.whisper_model_dir = str(tmp_path)
    cfg.whisper_model = model
    cfg.whisper_acceleration = acceleration

    overlay = MagicMock()
    tray = MagicMock()
    initial_stt = MagicMock(name="initial_stt")

    app = SimpleNamespace(
        _config=cfg,
        _stt=initial_stt,
        _stt_reload_lock=threading.Lock(),
        _overlay=overlay,
        _tray=tray,
    )
    # Bind die echte _reload_stt-Methode aus der Klasse an die Harness.
    app._reload_stt = main_module.VocixApp._reload_stt.__get__(app)
    return app, overlay, tray, initial_stt


def _wait_for_lock_release(lock: threading.Lock, timeout: float = 2.0) -> None:
    """Pollt bis Lock frei ist (Worker fertig). Kein sleep-loop ohne Bedingung."""
    deadline = threading.Event()
    threading.Timer(timeout, deadline.set).start()
    while lock.locked() and not deadline.is_set():
        deadline.wait(0.01)
    assert not lock.locked(), "Worker hat Lock nicht freigegeben"


def test_reload_success_persists_state_and_swaps_stt(monkeypatch, tmp_path):
    app, overlay, tray, initial_stt = _make_harness(monkeypatch, tmp_path)

    new_stt = MagicMock(name="new_stt")
    new_stt.device = "cpu"
    fake_state: dict = {}

    class _FakeStateCM:
        def __enter__(self):
            return fake_state
        def __exit__(self, *a):
            return False

    with patch.object(main_module, "WhisperSTT", return_value=new_stt), \
         patch.object(main_module, "update_state", return_value=_FakeStateCM()):
        app._reload_stt(model="medium")
        _wait_for_lock_release(app._stt_reload_lock)

    assert app._stt is new_stt
    assert app._config.whisper_model == "medium"
    assert fake_state == {"whisper_model": "medium", "whisper_acceleration": "auto"}
    tray.update_whisper_settings.assert_called_once_with(model="medium", acceleration="auto")
    # Erfolgs-Toast: zwei Calls (initial "loading…" via show, dann "loaded" via show_temporary)
    overlay.show.assert_called_once()
    assert overlay.show_temporary.call_count == 1


def test_reload_exception_keeps_state_unchanged(monkeypatch, tmp_path):
    app, overlay, tray, initial_stt = _make_harness(monkeypatch, tmp_path, model="small")

    fake_state: dict = {}

    class _FakeStateCM:
        def __enter__(self):
            return fake_state
        def __exit__(self, *a):
            return False

    with patch.object(main_module, "WhisperSTT", side_effect=RuntimeError("OOM")), \
         patch.object(main_module, "update_state", return_value=_FakeStateCM()):
        app._reload_stt(model="large-v3")
        _wait_for_lock_release(app._stt_reload_lock)

    # State unverändert
    assert app._stt is initial_stt
    assert app._config.whisper_model == "small"
    assert fake_state == {}
    tray.update_whisper_settings.assert_not_called()
    # Fehler-Toast wurde gezeigt
    overlay.show_temporary.assert_called_once()
    args = overlay.show_temporary.call_args
    assert "small" in args.args[0] or "small" in str(args)  # active-model im Toast


def test_reload_lock_rejects_concurrent_reload(monkeypatch, tmp_path):
    app, overlay, tray, _ = _make_harness(monkeypatch, tmp_path)

    started = threading.Event()
    can_finish = threading.Event()

    def _slow_whisper_init(*args, **kwargs):
        started.set()
        can_finish.wait(timeout=2)
        m = MagicMock()
        m.device = "cpu"
        return m

    class _FakeStateCM:
        def __enter__(self):
            return {}
        def __exit__(self, *a):
            return False

    with patch.object(main_module, "WhisperSTT", side_effect=_slow_whisper_init), \
         patch.object(main_module, "update_state", return_value=_FakeStateCM()):
        app._reload_stt(model="medium")
        assert started.wait(timeout=2), "Erster Worker hat WhisperSTT nicht aufgerufen"

        # Zweiter Reload während erster noch hängt: muss "busy"-Toast zeigen
        overlay.show_temporary.reset_mock()
        app._reload_stt(model="large-v3")
        # Worker läuft async — kurz warten bis er den Lock testet
        for _ in range(50):
            if overlay.show_temporary.called:
                break
            threading.Event().wait(0.01)

        assert overlay.show_temporary.called, "Busy-Toast nicht gezeigt"
        toast_arg = overlay.show_temporary.call_args.args[0]
        # Der busy-Text ist die i18n von overlay.model_reload_busy
        assert toast_arg, "Toast ohne Inhalt"

        can_finish.set()
        _wait_for_lock_release(app._stt_reload_lock)


def test_reload_releases_lock_on_exception(monkeypatch, tmp_path):
    """Selbst wenn Whisper-Konstruktor wirft, muss der Lock im finally freigegeben sein."""
    app, *_ = _make_harness(monkeypatch, tmp_path)

    with patch.object(main_module, "WhisperSTT", side_effect=RuntimeError("boom")):
        app._reload_stt(model="tiny")
        _wait_for_lock_release(app._stt_reload_lock)

    assert not app._stt_reload_lock.locked()
