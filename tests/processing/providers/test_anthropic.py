"""Tests für AnthropicProvider — mock anthropic SDK."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from vocix.processing.providers import ProviderConfig, ProviderError
from vocix.processing.providers.anthropic_provider import AnthropicProvider


def _cfg(api_key: str = "sk-ant-fake", model: str = "claude-test", timeout: float = 5.0) -> ProviderConfig:
    return ProviderConfig(kind="anthropic", api_key=api_key, model=model, timeout=timeout)


def _response(text: str | None) -> SimpleNamespace:
    if text is None:
        return SimpleNamespace(content=[])
    return SimpleNamespace(content=[SimpleNamespace(text=text)])


def test_complete_success_returns_text():
    provider = AnthropicProvider(_cfg())
    provider._client = MagicMock()
    provider._client.messages.create.return_value = _response("Hallo Welt")

    result = provider.complete(system="be polite", user="hi")

    assert result == "Hallo Welt"
    kwargs = provider._client.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-test"
    assert kwargs["system"] == "be polite"
    assert kwargs["messages"] == [{"role": "user", "content": "hi"}]


def test_complete_raises_provider_error_on_api_exception():
    provider = AnthropicProvider(_cfg())
    provider._client = MagicMock()
    provider._client.messages.create.side_effect = RuntimeError("network down")

    with pytest.raises(ProviderError):
        provider.complete(system="x", user="y")


def test_complete_raises_on_empty_content():
    provider = AnthropicProvider(_cfg())
    provider._client = MagicMock()
    provider._client.messages.create.return_value = _response(None)

    with pytest.raises(ProviderError):
        provider.complete(system="x", user="y")


def test_complete_raises_on_blank_text():
    provider = AnthropicProvider(_cfg())
    provider._client = MagicMock()
    provider._client.messages.create.return_value = _response("   ")

    with pytest.raises(ProviderError):
        provider.complete(system="x", user="y")


def test_complete_raises_on_non_text_block():
    provider = AnthropicProvider(_cfg())
    provider._client = MagicMock()
    block_without_text = SimpleNamespace()  # kein .text-Attribut
    provider._client.messages.create.return_value = SimpleNamespace(content=[block_without_text])

    with pytest.raises(ProviderError):
        provider.complete(system="x", user="y")


def test_construct_without_key_raises():
    with pytest.raises(ProviderError):
        AnthropicProvider(_cfg(api_key=""))


def test_construct_without_anthropic_package_raises():
    with patch.dict("sys.modules", {"anthropic": None}):
        with pytest.raises(ProviderError):
            AnthropicProvider(_cfg())
