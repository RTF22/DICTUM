"""Tests für OllamaProvider — HTTP-basiert, mock urllib.request."""
from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from vocix.processing.providers import ProviderConfig, ProviderError
from vocix.processing.providers.ollama_provider import OllamaProvider


def _cfg(base_url: str = "http://localhost:11434", model: str = "llama3.1:8b",
         timeout: float = 5.0) -> ProviderConfig:
    return ProviderConfig(kind="ollama", base_url=base_url, model=model, timeout=timeout)


def _http_ok(payload: dict) -> MagicMock:
    body = json.dumps(payload).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = lambda self: self
    resp.__exit__ = lambda *a: None
    return resp


def test_complete_success_returns_text():
    provider = OllamaProvider(_cfg())
    fake = _http_ok({"message": {"content": "Hallo Welt"}})
    with patch("urllib.request.urlopen", return_value=fake) as urlopen:
        result = provider.complete(system="be polite", user="hi", max_tokens=100)

    assert result == "Hallo Welt"
    req = urlopen.call_args.args[0]
    assert req.full_url == "http://localhost:11434/api/chat"
    body = json.loads(req.data.decode("utf-8"))
    assert body["model"] == "llama3.1:8b"
    assert body["stream"] is False
    assert body["messages"] == [
        {"role": "system", "content": "be polite"},
        {"role": "user", "content": "hi"},
    ]


def test_complete_strips_trailing_slash_in_base_url():
    provider = OllamaProvider(_cfg(base_url="http://localhost:11434/"))
    fake = _http_ok({"message": {"content": "ok"}})
    with patch("urllib.request.urlopen", return_value=fake) as urlopen:
        provider.complete(system="x", user="y")
    assert urlopen.call_args.args[0].full_url == "http://localhost:11434/api/chat"


def test_complete_raises_on_http_error():
    provider = OllamaProvider(_cfg())
    err = HTTPError("http://x/api/chat", 500, "Server Error", {}, io.BytesIO(b"boom"))
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(ProviderError):
            provider.complete(system="x", user="y")


def test_complete_raises_on_url_error():
    provider = OllamaProvider(_cfg())
    with patch("urllib.request.urlopen", side_effect=URLError("connection refused")):
        with pytest.raises(ProviderError):
            provider.complete(system="x", user="y")


def test_complete_raises_on_blank_content():
    provider = OllamaProvider(_cfg())
    fake = _http_ok({"message": {"content": "   "}})
    with patch("urllib.request.urlopen", return_value=fake):
        with pytest.raises(ProviderError):
            provider.complete(system="x", user="y")


def test_complete_raises_on_missing_message_field():
    provider = OllamaProvider(_cfg())
    fake = _http_ok({"foo": "bar"})
    with patch("urllib.request.urlopen", return_value=fake):
        with pytest.raises(ProviderError):
            provider.complete(system="x", user="y")


def test_construct_without_base_url_raises():
    with pytest.raises(ProviderError):
        OllamaProvider(_cfg(base_url=""))


def test_construct_without_model_raises():
    with pytest.raises(ProviderError):
        OllamaProvider(_cfg(model=""))
