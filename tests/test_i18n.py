"""Unit-Tests für vocix.i18n — Lookup, Fallback, Interpolation, Sprachwechsel."""

import importlib

import pytest


@pytest.fixture
def i18n(monkeypatch):
    """Liefert ein frisch geladenes i18n-Modul mit DE als Startsprache."""
    import vocix.i18n as mod
    importlib.reload(mod)
    mod.set_language("de")
    return mod


def test_known_key_de(i18n):
    assert i18n.t("tray.quit") == "Beenden"


def test_language_switch(i18n):
    i18n.set_language("en")
    assert i18n.t("tray.quit") == "Quit"
    assert i18n.get_language() == "en"


def test_unknown_language_ignored(i18n):
    i18n.set_language("fr")
    assert i18n.get_language() == "de"


def test_interpolation(i18n):
    result = i18n.t("tray.update_available", version="1.2.3")
    assert "1.2.3" in result


def test_missing_key_returns_key(i18n):
    assert i18n.t("does.not.exist") == "does.not.exist"


def test_fallback_to_english(i18n, monkeypatch):
    # Simuliere fehlenden Key in DE, aber vorhanden in EN
    i18n._translations["de"] = {}
    i18n._translations["en"] = {"tray.quit": "Quit"}
    assert i18n.t("tray.quit") == "Quit"


def test_available_languages(i18n):
    langs = i18n.available_languages()
    assert "de" in langs
    assert "en" in langs


def test_whisper_code_matches_language(i18n):
    i18n.set_language("en")
    assert i18n.whisper_code() == "en"
    i18n.set_language("de")
    assert i18n.whisper_code() == "de"
