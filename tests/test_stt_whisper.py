"""Tests für WhisperSTT — verifiziert task-kwarg für Translate-Modus."""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest


@pytest.fixture
def whisper_stub(monkeypatch):
    """Ersetzt faster_whisper durch ein Stub-Modul, das WhisperModel als MagicMock liefert."""
    captured = {}

    class _FakeModel:
        def __init__(self, *args, **kwargs):
            captured["init_args"] = args
            captured["init_kwargs"] = kwargs
            self.transcribe = MagicMock()
            self.transcribe.return_value = (
                iter([SimpleNamespace(text="hello world")]),
                SimpleNamespace(language="de", language_probability=0.95),
            )
            captured["model"] = self

    fake_module = types.ModuleType("faster_whisper")
    fake_module.WhisperModel = _FakeModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_module)

    # whisper_stt ggf. schon importiert → neu laden, damit die gepatchte
    # WhisperModel-Klasse greift.
    sys.modules.pop("vocix.stt.whisper_stt", None)
    return captured


def _make_config(translate: bool, tmp_path) -> "Config":
    from vocix.config import Config
    cfg = Config()
    cfg.whisper_model_dir = str(tmp_path)
    cfg.translate_to_english = translate
    return cfg


def test_transcribe_without_translate_omits_task_kwarg(whisper_stub, tmp_path):
    from vocix.stt.whisper_stt import WhisperSTT

    cfg = _make_config(translate=False, tmp_path=tmp_path)
    stt = WhisperSTT(cfg)
    stt.transcribe(np.zeros(16000, dtype=np.float32))

    kwargs = whisper_stub["model"].transcribe.call_args.kwargs
    assert "task" not in kwargs
    assert kwargs["language"] == cfg.whisper_language


def test_transcribe_with_translate_sets_task_translate(whisper_stub, tmp_path):
    from vocix.stt.whisper_stt import WhisperSTT

    cfg = _make_config(translate=True, tmp_path=tmp_path)
    stt = WhisperSTT(cfg)
    stt.transcribe(np.zeros(16000, dtype=np.float32))

    kwargs = whisper_stub["model"].transcribe.call_args.kwargs
    assert kwargs.get("task") == "translate"
    assert kwargs["language"] == cfg.whisper_language


def test_resolve_device_cpu_forced(monkeypatch):
    sys.modules.pop("vocix.stt.whisper_stt", None)
    from vocix.stt.whisper_stt import _resolve_device

    device, compute = _resolve_device("cpu")
    assert device == "cpu"
    assert compute == "int8"


def test_resolve_device_gpu_forced(monkeypatch):
    sys.modules.pop("vocix.stt.whisper_stt", None)
    from vocix.stt.whisper_stt import _resolve_device

    device, compute = _resolve_device("gpu")
    assert device == "cuda"
    assert compute == "float16"


def test_resolve_device_auto_falls_back_to_cpu_without_cuda(monkeypatch):
    sys.modules.pop("vocix.stt.whisper_stt", None)
    import vocix.stt.whisper_stt as mod

    monkeypatch.setattr(mod, "cuda_available", lambda: False)
    device, compute = mod._resolve_device("auto")
    assert device == "cpu"
    assert compute == "int8"


def test_resolve_device_auto_picks_cuda_when_available(monkeypatch):
    sys.modules.pop("vocix.stt.whisper_stt", None)
    import vocix.stt.whisper_stt as mod

    monkeypatch.setattr(mod, "cuda_available", lambda: True)
    device, compute = mod._resolve_device("auto")
    assert device == "cuda"
    assert compute == "float16"


def test_whisper_init_passes_device_and_compute_type(whisper_stub, tmp_path, monkeypatch):
    import vocix.stt.whisper_stt as mod
    monkeypatch.setattr(mod, "cuda_available", lambda: False)

    cfg = _make_config(translate=False, tmp_path=tmp_path)
    cfg.whisper_acceleration = "cpu"
    mod.WhisperSTT(cfg)

    init_kwargs = whisper_stub["init_kwargs"]
    assert init_kwargs["device"] == "cpu"
    assert init_kwargs["compute_type"] == "int8"
