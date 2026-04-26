"""Factory: ProviderConfig → konkrete LLMProvider-Instanz."""
from __future__ import annotations

from vocix.processing.providers.base import LLMProvider, ProviderConfig, ProviderError


def build_provider(config: ProviderConfig) -> LLMProvider:
    if config.kind == "anthropic":
        from vocix.processing.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(config)
    if config.kind == "openai":
        from vocix.processing.providers.openai_provider import OpenAICompatibleProvider
        return OpenAICompatibleProvider(config)
    if config.kind == "ollama":
        from vocix.processing.providers.ollama_provider import OllamaProvider
        return OllamaProvider(config)
    raise ProviderError(f"Unknown provider kind: {config.kind!r}")
