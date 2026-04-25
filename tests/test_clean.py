"""Tests für CleanProcessor — Füllwort-Entfernung und Satzbereinigung."""
from __future__ import annotations

import pytest

from vocix.processing.clean import CleanProcessor


@pytest.fixture
def clean():
    return CleanProcessor()


def test_name(clean):
    assert clean.name == "Clean"


def test_empty_string(clean):
    assert clean.process("") == ""


def test_whitespace_only(clean):
    # Input nur aus Whitespace → TextProcessor.process gibt Text unverändert zurück
    # (early-return, bevor Normalisierung greift)
    assert clean.process("   ") == "   "


def test_removes_single_filler(clean):
    assert clean.process("Ich ähm denke das ist gut.") == "Ich denke das ist gut."


def test_removes_multiple_fillers(clean):
    result = clean.process("Also äh ich denke halt sozusagen das ist gut.")
    # alle Füller raus, Satzanfang groß, keine Doppel-Leerzeichen
    assert "äh" not in result.lower()
    assert "also" not in result.lower()
    assert "halt" not in result.lower()
    assert "sozusagen" not in result.lower()
    assert "  " not in result
    assert result.startswith("Ich")


def test_removes_multiword_phrase(clean):
    # „im Grunde genommen" als Phrase, nicht Wort-für-Wort
    result = clean.process("Das ist im Grunde genommen korrekt.")
    assert "grunde" not in result.lower()
    assert result == "Das ist korrekt."


def test_capitalises_first_letter(clean):
    assert clean.process("äh das ist gut.") == "Das ist gut."


def test_capitalises_after_punctuation(clean):
    assert clean.process("das ist gut. das auch.") == "Das ist gut. Das auch."


def test_strips_leading_comma(clean):
    # Füllwort vor dem eigentlichen Satz hinterlässt führendes Komma
    assert clean.process("Eigentlich, das ist gut.") == "Das ist gut."


def test_collapses_double_commas(clean):
    assert clean.process("Das ist, halt, gut.") == "Das ist, gut."


def test_no_space_before_punctuation(clean):
    assert clean.process("Das ist gut , oder ?") == "Das ist gut, oder?"


def test_preserves_newlines(clean):
    result = clean.process("Erste Zeile.\nZweite Zeile.")
    assert "\n" in result
    assert result.count("\n") == 1


def test_only_fillers_collapses_punctuation(clean):
    # Nur Füller + Satzzeichen: Füller fliegen raus, übrig bleibt Satzzeichen-Gerüst.
    # (Kein "leer"-Garantie — die Regex-Kette kappt nur führende Zeichen pro Zeile.)
    result = clean.process("Äh, hm, also.")
    assert all(f not in result.lower() for f in ("äh", "hm", "also"))


def test_preserves_content_words(clean):
    text = "Der Vertrag wird morgen unterzeichnet."
    # Keine Füller im Satz, soll unverändert durchgehen (modulo Satzanfang)
    assert clean.process(text) == text
