"""Anthropic-Provider — kapselt anthropic.Anthropic.messages.create."""
from __future__ import annotations

import logging

from vocix.processing.providers.base import LLMProvider, ProviderConfig, ProviderError

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    def __init__(self, config: ProviderConfig):
        if not config.api_key:
            raise ProviderError("Anthropic: API-Key fehlt")
        try:
            import anthropic  # type: ignore
        except ImportError as e:
            raise ProviderError(f"anthropic package not installed: {e}") from e

        self._config = config
        self._client = anthropic.Anthropic(api_key=config.api_key, timeout=config.timeout)

    def complete(self, *, system: str, user: str, max_tokens: int = 1024) -> str:
        try:
            response = self._client.messages.create(
                model=self._config.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as e:
            raise ProviderError(f"Anthropic API error: {e}") from e

        content = getattr(response, "content", None)
        if not content or not hasattr(content[0], "text"):
            raise ProviderError("Anthropic: empty or non-text response")
        text = content[0].text.strip()
        if not text:
            raise ProviderError("Anthropic: blank text in response")
        return text
