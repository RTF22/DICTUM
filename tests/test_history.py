"""Tests für den History-Ringpuffer."""
from __future__ import annotations

import json

import pytest

from vocix.history import History


@pytest.fixture
def history_path(tmp_path):
    return tmp_path / "history.json"


def test_add_persists_entries(history_path):
    h = History(limit=5, path=history_path)
    h.add("Hallo Welt", "clean")
    h.add("Zweiter Text", "business")

    raw = json.loads(history_path.read_text(encoding="utf-8"))
    assert len(raw) == 2
    assert raw[0]["text"] == "Hallo Welt"
    assert raw[0]["mode"] == "clean"
    assert "ts" in raw[0]


def test_entries_returns_newest_first(history_path):
    h = History(limit=5, path=history_path)
    h.add("eins", "clean")
    h.add("zwei", "business")
    entries = h.entries()
    assert [e["text"] for e in entries] == ["zwei", "eins"]


def test_ring_buffer_drops_oldest(history_path):
    h = History(limit=3, path=history_path)
    for i in range(5):
        h.add(f"text {i}", "clean")
    entries = h.entries()
    assert [e["text"] for e in entries] == ["text 4", "text 3", "text 2"]


def test_empty_text_is_ignored(history_path):
    h = History(limit=5, path=history_path)
    h.add("", "clean")
    h.add("   ", "clean")
    assert h.entries() == []


def test_clear_removes_all(history_path):
    h = History(limit=5, path=history_path)
    h.add("foo", "clean")
    h.clear()
    assert h.entries() == []
    assert json.loads(history_path.read_text(encoding="utf-8")) == []


def test_load_recovers_from_disk(history_path):
    h1 = History(limit=5, path=history_path)
    h1.add("persistiert", "rage")

    h2 = History(limit=5, path=history_path)
    entries = h2.entries()
    assert len(entries) == 1
    assert entries[0]["text"] == "persistiert"


def test_corrupt_file_yields_empty(history_path):
    history_path.write_text("nicht-json", encoding="utf-8")
    h = History(limit=5, path=history_path)
    assert h.entries() == []
