"""Tests für build_provider — Slot-ID → konkrete LLMProvider-Instanz."""
from __future__ import annotations

import pytest

from vocix.processing.providers import ProviderConfig, ProviderError, build_provider
from vocix.processing.providers.anthropic_provider import AnthropicProvider
from vocix.processing.providers.openai_provider import OpenAICompatibleProvider
from vocix.processing.providers.ollama_provider import OllamaProvider


def test_build_anthropic():
    cfg = ProviderConfig(kind="anthropic", api_key="sk-ant-x", model="claude-test")
    p = build_provider(cfg)
    assert isinstance(p, AnthropicProvider)


def test_build_openai():
    cfg = ProviderConfig(kind="openai", api_key="sk-x", model="gpt-4o-mini")
    p = build_provider(cfg)
    assert isinstance(p, OpenAICompatibleProvider)


def test_build_ollama():
    cfg = ProviderConfig(kind="ollama", base_url="http://localhost:11434", model="llama3.1:8b")
    p = build_provider(cfg)
    assert isinstance(p, OllamaProvider)


def test_build_unknown_kind_raises():
    cfg = ProviderConfig(kind="gemini", api_key="x", model="y")
    with pytest.raises(ProviderError):
        build_provider(cfg)
