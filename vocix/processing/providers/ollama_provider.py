"""Ollama-Provider — HTTP-basiert, kein SDK, stdlib urllib.

API: POST {base_url}/api/chat mit JSON {model, messages, stream:false}.
Antwort: {"message": {"role": "assistant", "content": "..."}, ...}.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from vocix.processing.providers.base import LLMProvider, ProviderConfig, ProviderError

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, config: ProviderConfig):
        if not config.base_url:
            raise ProviderError("Ollama: base_url fehlt")
        if not config.model:
            raise ProviderError("Ollama: model fehlt")
        self._config = config
        self._endpoint = config.base_url.rstrip("/") + "/api/chat"

    def complete(self, *, system: str, user: str, max_tokens: int = 1024) -> str:
        body = json.dumps({
            "model": self._config.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"num_predict": max_tokens},
        }).encode("utf-8")

        req = urllib.request.Request(
            self._endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise ProviderError(f"Ollama HTTP {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise ProviderError(f"Ollama connection error: {e.reason}") from e
        except (TimeoutError, OSError) as e:
            raise ProviderError(f"Ollama I/O error: {e}") from e
        except json.JSONDecodeError as e:
            raise ProviderError(f"Ollama: invalid JSON response: {e}") from e

        msg = payload.get("message")
        if not isinstance(msg, dict):
            raise ProviderError("Ollama: missing 'message' in response")
        content = msg.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Ollama: blank content")
        return content.strip()
