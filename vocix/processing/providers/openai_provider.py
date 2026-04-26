"""OpenAI-kompatibler Provider — funktioniert mit OpenAI, Groq, OpenRouter,
LM Studio, llama.cpp-Server, vLLM. Steuerung via base_url-Override."""
from __future__ import annotations

import logging

from vocix.processing.providers.base import LLMProvider, ProviderConfig, ProviderError

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, config: ProviderConfig):
        if not config.api_key:
            raise ProviderError("OpenAI: API-Key fehlt")
        try:
            import openai  # type: ignore
        except ImportError as e:
            raise ProviderError(f"openai package not installed: {e}") from e

        self._config = config
        kwargs = {"api_key": config.api_key, "timeout": config.timeout}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self._client = openai.OpenAI(**kwargs)

    def complete(self, *, system: str, user: str, max_tokens: int = 1024) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as e:
            raise ProviderError(f"OpenAI API error: {e}") from e

        choices = getattr(response, "choices", None)
        if not choices:
            raise ProviderError("OpenAI: empty choices in response")
        msg = getattr(choices[0], "message", None)
        content = getattr(msg, "content", None) if msg is not None else None
        if not content or not content.strip():
            raise ProviderError("OpenAI: blank content in response")
        return content.strip()
