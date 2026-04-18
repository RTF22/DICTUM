# Auto-Update-Check — Design

**Status:** Approved
**Datum:** 2026-04-18
**Autor:** Jens Fricke (mit Claude)

## Ziel

TextME soll beim Start automatisch prüfen, ob ein neueres GitHub-Release im Repo `RTF22/DICTUM` verfügbar ist, den User dezent benachrichtigen und die Release-Seite im Browser öffnen, wenn er das Update herunterladen möchte.

## Scope

**In Scope:**
- Prüfung gegen GitHub Releases API beim App-Start (im Hintergrund-Thread)
- Manueller Trigger „Nach Updates suchen…" im Tray-Menü
- System-Tray-Toast + persistenter Menüeintrag bei verfügbarem Update
- „Diese Version überspringen" pro Version (verhindert wiederholte Benachrichtigungen)
- Klick auf Update-Eintrag öffnet Release-Seite im Default-Browser

**Out of Scope:**
- Automatischer Download oder Auto-Install
- Periodische Checks zur Laufzeit
- Berücksichtigung von Pre-Releases (GitHub `/releases/latest` liefert ohnehin nur stable)

## Architektur

```
main.py  ──►  UpdateChecker (Daemon-Thread)  ──►  GitHub API
                                                     │
                                                     ▼
                                                 UpdateInfo
                                                     │
                                 Callback ──────────┘
                                     │
                                     ▼
                              Tray (Toast + Menü-Eintrag)
                                     │
                          Klick ─────┤
                                     ▼
                              webbrowser.open(url)
```

Dataflow:

1. `main.py` initialisiert Tray und ruft `UpdateChecker.check_async(callback)` auf
2. Daemon-Thread führt HTTPS-GET an GitHub aus, parst JSON
3. Bei neuerer Version (und `version != skip_update_version`) → Callback ins Tray
4. Tray baut Menü neu (mit `🔔 Update {version} verfügbar`) und zeigt Toast
5. User klickt Eintrag → Browser öffnet `html_url` des Release

## Module

### `dictum/updater.py` (neu)

```python
@dataclass
class UpdateInfo:
    version: str      # z.B. "0.9.0" (ohne v-Prefix, normalisiert)
    url: str          # GitHub html_url des Release
    notes: str        # body (Release-Notes, für mögliches späteres Detail-Popup)

def check_latest(current_version: str, skip_version: str | None) -> UpdateInfo | None:
    """
    GET https://api.github.com/repos/RTF22/DICTUM/releases/latest
    Headers: User-Agent: TextME/{current_version}
    Timeout: 5s
    Returns:
      UpdateInfo wenn latest > current UND latest != skip_version
      None in allen anderen Fällen (inkl. Netzwerkfehler)
    """

def check_async(current_version, skip_version, on_update_found: Callable[[UpdateInfo], None]) -> None:
    """Startet Daemon-Thread, ruft on_update_found nur bei Erfolg mit Update."""

def _parse_version(tag: str) -> tuple[int, int, int]:
    """'v0.9.0' → (0,9,0); '0.9.0' → (0,9,0); bei Parse-Fehler ValueError."""
```

**Dependencies:** Nur stdlib (`urllib.request`, `json`, `threading`, `logging`, `dataclasses`). Kein `packaging`-Paket nötig, da Tag-Format `vMAJOR.MINOR.PATCH` konsistent ist.

### `dictum/config.py` (erweitern)

- Neues Feld `skip_update_version: str | None = None`
- Persistenz: Falls heute noch keine persistente State-Datei existiert, neue Datei `%APPDATA%/TextME/state.json` (nur für User-State wie übersprungene Versionen); die bestehende `.env`-basierte `Config` bleibt unverändert für Startup-Konfiguration.

### `dictum/ui/tray.py` (erweitern)

**Neue State-Felder:**
- `self._update_info: UpdateInfo | None = None`

**Neue Methoden:**
- `set_update_available(info: UpdateInfo)` — Callback für Updater, speichert Info, rebuildet Menü, zeigt Toast via `self._icon.notify(...)`
- `_on_open_release()` — `webbrowser.open(self._update_info.url)`
- `_on_skip_version()` — Speichert Version in State, setzt `_update_info = None`, rebuildet Menü
- `_on_manual_check()` — Blockiert kurz, ruft `check_latest` synchron auf, zeigt Toast mit Ergebnis („Update verfügbar" / „Aktuell" / „Fehler beim Prüfen")

**Menü-Änderungen:**
- Dynamisch sichtbar, wenn `_update_info` gesetzt:
  - `🔔 Update {version} verfügbar` → `_on_open_release`
  - `  Diese Version überspringen` → `_on_skip_version`
  - Trenner
- Immer sichtbar:
  - `Nach Updates suchen…` → `_on_manual_check`

### `dictum/main.py` (erweitern)

Nach Tray-Init:
```python
from . import updater, __version__
updater.check_async(
    current_version=__version__,
    skip_version=config.skip_update_version,
    on_update_found=tray.set_update_available,
)
```

## Fehlerbehandlung

| Fehler | Verhalten Auto-Check | Verhalten Manuell |
|---|---|---|
| Timeout / URLError | `logging.warning`, silent | Toast: „Update-Prüfung fehlgeschlagen" |
| HTTP 404 / 5xx | `logging.warning`, silent | Toast: „Update-Prüfung fehlgeschlagen" |
| JSON-Parse-Fehler | `logging.warning`, silent | Toast: „Update-Prüfung fehlgeschlagen" |
| Tag-Format unerwartet | `_parse_version` raises → None | dito |
| Latest == current | None | Toast: „Du bist auf der aktuellsten Version" |
| Latest < current (dev) | None | Toast: „Du bist auf der aktuellsten Version" |
| Latest == skip_version | None | ignoriert skip und zeigt Update (Manual = expliziter User-Wunsch) |

## Testing

**Unit-Tests** in `tests/test_updater.py`:
- `_parse_version` mit `v0.9.0`, `0.9.0`, `v1.2.3`, Fehlerfälle
- `check_latest` Happy Path (Mock `urllib.request.urlopen`)
- `check_latest` mit `latest == current` → None
- `check_latest` mit `skip_version == latest` → None
- `check_latest` mit Timeout → None
- `check_latest` mit malformed JSON → None

**Manuelle Smoke-Tests:**
1. Start mit `__version__ = "0.0.1"` → Toast + Menüeintrag erscheinen
2. Klick auf Menüeintrag → Browser öffnet korrekte Release-Seite
3. „Diese Version überspringen" → Menüeintrag verschwindet; Neustart zeigt keinen Toast
4. Offline-Start → kein Toast, kein Fehler, App läuft normal
5. „Nach Updates suchen…" bei aktueller Version → Toast „Du bist auf der aktuellsten Version"
6. „Nach Updates suchen…" offline → Toast „Update-Prüfung fehlgeschlagen"

## Offene Punkte

Keine — alle Design-Fragen sind geklärt.
