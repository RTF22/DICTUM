"""Tests für `update_state()` — atomares Read-Modify-Write auf state.json."""
from __future__ import annotations

import json
import threading

import pytest

from vocix import config as config_module


@pytest.fixture
def isolated_state(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(config_module, "STATE_FILE", state_file)
    return state_file


def test_update_state_persists(isolated_state):
    with config_module.update_state() as s:
        s["foo"] = "bar"
    assert json.loads(isolated_state.read_text(encoding="utf-8")) == {"foo": "bar"}


def test_update_state_preserves_unrelated_keys(isolated_state):
    isolated_state.write_text(json.dumps({"keep": 1}), encoding="utf-8")
    with config_module.update_state() as s:
        s["add"] = 2
    data = json.loads(isolated_state.read_text(encoding="utf-8"))
    assert data == {"keep": 1, "add": 2}


def test_concurrent_updates_do_not_lose_writes(isolated_state):
    """Zwei Threads schreiben verschiedene Keys — nach dem Join müssen beide da sein."""
    N = 50
    barrier = threading.Barrier(2)

    def writer(prefix: str):
        barrier.wait()
        for i in range(N):
            with config_module.update_state() as s:
                s[f"{prefix}_{i}"] = i

    t1 = threading.Thread(target=writer, args=("a",))
    t2 = threading.Thread(target=writer, args=("b",))
    t1.start(); t2.start()
    t1.join(); t2.join()

    data = json.loads(isolated_state.read_text(encoding="utf-8"))
    assert sum(1 for k in data if k.startswith("a_")) == N
    assert sum(1 for k in data if k.startswith("b_")) == N
