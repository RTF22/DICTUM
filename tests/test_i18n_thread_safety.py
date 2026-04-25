"""Thread-Safety-Test für i18n — parallele set_language + t() ohne Torn Reads."""
from __future__ import annotations

import threading

from vocix import i18n


def test_parallel_set_and_read_never_returns_none():
    """Während Thread A wild zwischen de/en wechselt, darf t() in Thread B
    weder crashen noch None liefern.
    """
    i18n.set_language("de")
    stop = threading.Event()
    errors: list[Exception] = []
    observed: list[str] = []

    def flipper():
        while not stop.is_set():
            i18n.set_language("de")
            i18n.set_language("en")

    def reader():
        try:
            for _ in range(2000):
                val = i18n.t("mode.clean")
                observed.append(val)
                assert isinstance(val, str) and val != ""
        except Exception as e:
            errors.append(e)

    flip = threading.Thread(target=flipper)
    read = threading.Thread(target=reader)
    flip.start(); read.start()
    read.join()
    stop.set()
    flip.join()

    assert not errors, f"Reader saw errors: {errors}"
    # Beide Sprachen sollten irgendwann aufgetaucht sein
    assert any("A:" in v for v in observed)  # mode.clean = "A: Clean"


def test_set_language_rejects_unknown():
    before = i18n.get_language()
    i18n.set_language("fr")
    assert i18n.get_language() == before
