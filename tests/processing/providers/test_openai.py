"""Tests für OpenAICompatibleProvider — mock openai SDK."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from vocix.processing.providers import ProviderConfig, ProviderError
from vocix.processing.providers.openai_provider import OpenAICompatibleProvider


def _cfg(api_key: str = "sk-fake", base_url: str = "", model: str = "gpt-4o-mini",
         timeout: float = 5.0) -> ProviderConfig:
    return ProviderConfig(kind="openai", api_key=api_key, base_url=base_url, model=model, timeout=timeout)


def _response(text: str | None) -> SimpleNamespace:
    if text is None:
        return SimpleNamespace(choices=[])
    msg = SimpleNamespace(content=text)
    choice = SimpleNamespace(message=msg)
    return SimpleNamespace(choices=[choice])


def test_complete_success_returns_text():
    provider = OpenAICompatibleProvider(_cfg())
    provider._client = MagicMock()
    provider._client.chat.completions.create.return_value = _response("Hallo Welt")

    result = provider.complete(system="be polite", user="hi", max_tokens=100)

    assert result == "Hallo Welt"
    kwargs = provider._client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["max_tokens"] == 100
    assert kwargs["messages"] == [
        {"role": "system", "content": "be polite"},
        {"role": "user", "content": "hi"},
    ]


def test_complete_raises_on_api_exception():
    provider = OpenAICompatibleProvider(_cfg())
    provider._client = MagicMock()
    provider._client.chat.completions.create.side_effect = RuntimeError("401")

    with pytest.raises(ProviderError):
        provider.complete(system="x", user="y")


def test_complete_raises_on_empty_choices():
    provider = OpenAICompatibleProvider(_cfg())
    provider._client = MagicMock()
    provider._client.chat.completions.create.return_value = _response(None)

    with pytest.raises(ProviderError):
        provider.complete(system="x", user="y")


def test_complete_raises_on_blank_content():
    provider = OpenAICompatibleProvider(_cfg())
    provider._client = MagicMock()
    provider._client.chat.completions.create.return_value = _response("   ")

    with pytest.raises(ProviderError):
        provider.complete(system="x", user="y")


def test_construct_passes_base_url_when_set():
    """base_url leer → openai-Default; base_url gesetzt → custom-endpoint."""
    fake_openai_class = MagicMock()
    with patch.dict("sys.modules", {"openai": SimpleNamespace(OpenAI=fake_openai_class)}):
        OpenAICompatibleProvider(_cfg(base_url="https://api.groq.com/openai/v1"))
    kwargs = fake_openai_class.call_args.kwargs
    assert kwargs["base_url"] == "https://api.groq.com/openai/v1"
    assert kwargs["api_key"] == "sk-fake"


def test_construct_omits_base_url_when_empty():
    fake_openai_class = MagicMock()
    with patch.dict("sys.modules", {"openai": SimpleNamespace(OpenAI=fake_openai_class)}):
        OpenAICompatibleProvider(_cfg(base_url=""))
    kwargs = fake_openai_class.call_args.kwargs
    assert "base_url" not in kwargs or kwargs.get("base_url") in (None, "")


def test_construct_without_key_raises():
    with pytest.raises(ProviderError):
        OpenAICompatibleProvider(_cfg(api_key=""))
