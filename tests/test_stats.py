"""Tests für die Stats-Aggregation."""
from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from vocix.stats import Stats, _word_count


@pytest.fixture
def stats_path(tmp_path):
    return tmp_path / "stats.json"


def test_word_count_handles_unicode():
    assert _word_count("Hallo Welt mit Ümlaut") == 4
    assert _word_count("") == 0
    assert _word_count("eins.") == 1


def test_record_increments_today(stats_path):
    s = Stats(path=stats_path)
    s.record("Hallo Welt", "clean")
    today = s.today()
    assert today["dictations"] == 1
    assert today["words"] == 2
    assert today["chars"] == len("Hallo Welt")
    assert today["modes"] == {"clean": 1}


def test_record_aggregates_modes(stats_path):
    s = Stats(path=stats_path)
    s.record("a b c", "clean")
    s.record("d e", "business")
    s.record("f", "business")
    today = s.today()
    assert today["dictations"] == 3
    assert today["words"] == 6
    assert today["modes"] == {"clean": 1, "business": 2}


def test_persistence_across_instances(stats_path):
    s1 = Stats(path=stats_path)
    s1.record("eins zwei", "clean")
    s2 = Stats(path=stats_path)
    assert s2.today()["words"] == 2


def test_reset_clears_data(stats_path):
    s = Stats(path=stats_path)
    s.record("foo bar", "clean")
    s.reset()
    assert s.total()["dictations"] == 0
    assert json.loads(stats_path.read_text(encoding="utf-8")) == {}


def test_week_excludes_older_days(stats_path):
    s = Stats(path=stats_path)
    old_day = (date.today() - timedelta(days=30)).isoformat()
    s._data[old_day] = {"words": 100, "chars": 500, "dictations": 5, "modes": {"clean": 5}}
    s.record("heute test", "clean")
    week = s.week()
    assert week["dictations"] == 1
    assert week["words"] == 2
    total = s.total()
    assert total["dictations"] == 6
    assert total["words"] == 102


def test_estimated_minutes_saved():
    assert Stats.estimated_minutes_saved(0) == 0
    assert Stats.estimated_minutes_saved(200) == pytest.approx(1.0)
    assert Stats.estimated_minutes_saved(1000) == pytest.approx(5.0)


def test_corrupt_file_yields_empty(stats_path):
    stats_path.write_text("kaputt", encoding="utf-8")
    s = Stats(path=stats_path)
    assert s.total()["dictations"] == 0
