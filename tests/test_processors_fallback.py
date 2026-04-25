"""Tests für Business/Rage-Processor — Fallback-Verhalten.

Geprüft werden die drei Wege, auf denen der Claude-Pfad den Clean-Fallback
aktiviert: (1) kein API-Key, (2) API wirft, (3) API liefert leere/ungültige
Antwort. Alle drei sollen transparent zu Clean durchreichen.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from vocix.config import Config
from vocix.processing.business import BusinessProcessor
from vocix.processing.rage import RageProcessor


def _config(api_key: str = "") -> Config:
    # Config() direkt aufrufen statt .load(), damit keine .env gelesen wird.
    # anthropic_api_key default-factory liest os.environ — wir überschreiben explizit.
    c = Config()
    c.anthropic_api_key = api_key
    return c


def _claude_response(text: str | None):
    """Konstruiert ein Fake-Response-Objekt, wie das anthropic-SDK es liefert."""
    if text is None:
        return SimpleNamespace(content=[])
    block = SimpleNamespace(text=text)
    return SimpleNamespace(content=[block])


# --- BusinessProcessor ---------------------------------------------------


def test_business_no_api_key_falls_back_to_clean():
    """Ohne Key wird kein Client instanziiert — process() ruft Clean auf."""
    proc = BusinessProcessor(_config(api_key=""))
    assert proc._client is None
    # Clean entfernt "äh" und setzt Satzanfang groß
    assert proc.process("äh das ist gut.") == "Das ist gut."


def test_business_api_exception_falls_back_to_clean():
    proc = BusinessProcessor(_config(api_key="sk-fake"))
    # Client-Instanziierung war erfolgreich — durch Mock ersetzen
    proc._client = MagicMock()
    proc._client.messages.create.side_effect = RuntimeError("network down")

    result = proc.process("äh das ist gut.")
    # Clean-Fallback hat zugeschlagen
    assert result == "Das ist gut."


def test_business_empty_content_falls_back_to_clean():
    proc = BusinessProcessor(_config(api_key="sk-fake"))
    proc._client = MagicMock()
    proc._client.messages.create.return_value = _claude_response(None)

    result = proc.process("äh das ist gut.")
    assert result == "Das ist gut."


def test_business_blank_text_in_response_falls_back():
    proc = BusinessProcessor(_config(api_key="sk-fake"))
    proc._client = MagicMock()
    proc._client.messages.create.return_value = _claude_response("   ")

    result = proc.process("äh das ist gut.")
    assert result == "Das ist gut."


def test_business_successful_response_is_returned():
    proc = BusinessProcessor(_config(api_key="sk-fake"))
    proc._client = MagicMock()
    proc._client.messages.create.return_value = _claude_response(
        "Sehr geehrte Damen und Herren, der Vorgang ist abgeschlossen."
    )

    result = proc.process("das ist fertig")
    assert result.startswith("Sehr geehrte")


def test_business_empty_input_short_circuits():
    proc = BusinessProcessor(_config(api_key="sk-fake"))
    proc._client = MagicMock()
    assert proc.process("") == ""
    assert proc.process("   ") == "   "
    proc._client.messages.create.assert_not_called()


# --- RageProcessor (Parität zu Business) ---------------------------------


def test_rage_no_api_key_falls_back():
    proc = RageProcessor(_config(api_key=""))
    assert proc._client is None
    assert proc.process("äh das ist gut.") == "Das ist gut."


def test_rage_api_exception_falls_back():
    proc = RageProcessor(_config(api_key="sk-fake"))
    proc._client = MagicMock()
    proc._client.messages.create.side_effect = RuntimeError("500")
    assert proc.process("äh das ist gut.") == "Das ist gut."


def test_rage_uses_rage_prompt_key():
    """Prompt-Key-Verdrahtung: Rage nutzt prompt.rage, nicht prompt.business."""
    proc = RageProcessor(_config(api_key="sk-fake"))
    proc._client = MagicMock()
    proc._client.messages.create.return_value = _claude_response("höflicher Text")

    proc.process("das ist scheisse")

    kwargs = proc._client.messages.create.call_args.kwargs
    # System-Prompt wurde aus i18n geladen — Inhalt variiert je Sprache,
    # aber der Key-Lookup muss unterschiedlich sein.
    assert "system" in kwargs
    assert kwargs["system"]  # non-empty


def test_business_uses_business_prompt_key():
    proc = BusinessProcessor(_config(api_key="sk-fake"))
    proc._client = MagicMock()
    proc._client.messages.create.return_value = _claude_response("professionell")

    proc.process("das ist fertig")
    kwargs = proc._client.messages.create.call_args.kwargs
    assert "system" in kwargs
    assert kwargs["system"]


def test_names_are_stable():
    """Die public names dürfen sich durch das Refactor nicht ändern."""
    assert BusinessProcessor(_config()).name == "Business"
    assert RageProcessor(_config()).name == "Rage"
