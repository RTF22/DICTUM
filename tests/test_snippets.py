"""Tests für die Snippet-Expansion."""
from __future__ import annotations

import json

import pytest

from vocix.snippets import SnippetExpander, _normalize_slash_phrases


@pytest.fixture
def snippets_path(tmp_path):
    return tmp_path / "snippets.json"


def write_snippets(path, mapping):
    path.write_text(json.dumps(mapping, ensure_ascii=False), encoding="utf-8")


def test_default_file_created_when_missing(snippets_path):
    SnippetExpander(path=snippets_path)
    assert snippets_path.exists()
    data = json.loads(snippets_path.read_text(encoding="utf-8"))
    assert "/sig" in data


def test_basic_expansion(snippets_path):
    write_snippets(snippets_path, {"/sig": "Signatur"})
    s = SnippetExpander(path=snippets_path)
    assert s.expand("Hallo /sig") == "Hallo Signatur"


def test_expansion_in_middle_of_text(snippets_path):
    write_snippets(snippets_path, {"/adr": "Adresse"})
    s = SnippetExpander(path=snippets_path)
    assert s.expand("siehe /adr unten") == "siehe Adresse unten"


def test_case_insensitive(snippets_path):
    write_snippets(snippets_path, {"/sig": "Sig"})
    s = SnippetExpander(path=snippets_path)
    assert s.expand("/SIG /Sig /sig") == "Sig Sig Sig"


def test_no_match_inside_word(snippets_path):
    write_snippets(snippets_path, {"/sig": "Sig"})
    s = SnippetExpander(path=snippets_path)
    # /sig ist Teil eines längeren Tokens — kein Match
    assert s.expand("test/sigplus") == "test/sigplus"


def test_longer_key_wins(snippets_path):
    write_snippets(snippets_path, {"/sig": "kurz", "/sigplus": "lang"})
    s = SnippetExpander(path=snippets_path)
    assert s.expand("/sigplus und /sig") == "lang und kurz"


def test_slash_phrase_normalisation():
    assert _normalize_slash_phrases("Schrägstrich Sig") == "/Sig"
    assert _normalize_slash_phrases("slash sig") == "/sig"


def test_expand_with_dictated_slash(snippets_path):
    write_snippets(snippets_path, {"/sig": "Signatur"})
    s = SnippetExpander(path=snippets_path)
    assert s.expand("Hallo Schrägstrich sig") == "Hallo Signatur"


def test_hot_reload(snippets_path):
    write_snippets(snippets_path, {"/sig": "alt"})
    s = SnippetExpander(path=snippets_path)
    assert s.expand("/sig") == "alt"
    # Datei ändern — mtime muss sich unterscheiden, daher kleines Sleep oder explicit set
    import os, time
    time.sleep(0.05)
    write_snippets(snippets_path, {"/sig": "neu"})
    os.utime(snippets_path, None)
    assert s.expand("/sig") == "neu"


def test_corrupt_file_yields_no_expansion(snippets_path):
    snippets_path.write_text("kaputt", encoding="utf-8")
    s = SnippetExpander(path=snippets_path)
    assert s.expand("/sig") == "/sig"


def test_empty_text_passthrough(snippets_path):
    write_snippets(snippets_path, {"/sig": "Sig"})
    s = SnippetExpander(path=snippets_path)
    assert s.expand("") == ""
