# LLM-Provider-Abstraktion für Modi B/C

**Status:** Design approved (2026-04-26)
**Scope:** Alternativen zu Anthropic für Business- und Rage-Modus — OpenAI-kompatible APIs und lokale Ollama-Modelle, konfigurierbar im Settings-Dialog.

## Motivation

Modi Business und Rage hängen heute hart am Anthropic-API-Key. Ohne Key fallen sie still auf Clean zurück. Nutzer, die keinen Claude-Zugang haben oder lokal arbeiten wollen (Datenschutz, Offline, Kosten), haben keine Option außer „Clean". Wir öffnen den Stack für andere Cloud-Anbieter und lokale Modelle.

## Anforderungen

- Drei Provider-Typen: Anthropic (bestehend), OpenAI-kompatibel (deckt OpenAI, Groq, Together, OpenRouter, LM Studio, llama.cpp-Server, vLLM), Ollama (lokal).
- Default-Provider global wählbar; pro Modus optional überschreibbar.
- Konfiguration im Settings-Dialog (neuer Tab „KI-Provider"). State-Persistenz wie bisher in `%APPDATA%/VOCIX/state.json`.
- API-Keys im Klartext in `state.json` (konsistent mit bestehendem `anthropic_api_key`). Keyring ist Out-of-Scope für dieses Design.
- Provider-Fehler → Clean-Fallback + sichtbares Toast-Overlay (orange/rot).
- Bestehende Anthropic-Konfigurationen funktionieren ohne Nutzeraktion auch in zukünftigen Versionen weiter (nicht-destruktive, dauerhafte Migration).
- Alle neuen Strings i18n (DE/EN).

## Out-of-Scope

- Windows Credential Manager / Keyring-Integration (separates Folge-Ticket).
- Provider-Ketten als Fallback (z. B. „erst Ollama, dann Anthropic, dann Clean"). YAGNI.
- Streaming-Antworten.
- Mehrere benannte Instanzen pro Provider-Typ (das State-Schema lässt es offen, UI bleibt erstmal bei drei festen Slots).
- Modell-Auto-Discovery vom Provider (Modell ist Textfeld).

## Architektur

Zwei Schichten, klar getrennt:

### Schicht 1: Provider (`vocix/processing/providers/`)

Neue abstrakte Klasse `LLMProvider` mit einer Methode:

```python
class LLMProvider(ABC):
    @abstractmethod
    def complete(self, *, system: str, user: str, max_tokens: int, timeout: float) -> str:
        """Sendet system+user an das Modell, liefert Text-Completion.
        Raises ProviderError bei jedem Fehler."""

    @property
    @abstractmethod
    def display_name(self) -> str: ...
```

Drei Implementierungen:

- **`AnthropicProvider`** — Logik aus heutigem `claude_base.py` extrahiert. Nutzt `anthropic.Anthropic.messages.create`. Keine neue Dependency.
- **`OpenAICompatibleProvider`** — neue Dependency `openai>=1.0` (~1 MB im Bundle). Nutzt `chat.completions.create` mit `base_url`-Override. Bei leerem `base_url` → OpenAI-Default.
- **`OllamaProvider`** — keine SDK, stdlib `urllib.request` POST auf `{base_url}/api/chat` mit `{"model":..., "messages":[...], "stream": false}`. Kein Bundle-Mehrgewicht.

Alle drei mappen ihre nativen Fehler (HTTP-Fehler, Timeout, Auth-Fehler, leerer Content, Non-Text-Block) auf eine einheitliche `ProviderError(message: str)`.

### Schicht 2: Modus-Processor

Bisheriger `ClaudeProcessor` wird zu `LLMBackedProcessor` umbenannt und generalisiert:

- Hält keine Provider-Instanz mehr direkt — löst pro `process()`-Aufruf den passenden Provider via `Config.llm_provider_for(mode)` auf.
- Bei `ProviderError`: ruft `CleanProcessor.process()` und triggert den optional gesetzten Fallback-Callback (`on_fallback(reason: str)`) für das Toast-Overlay.

`BusinessProcessor` und `RageProcessor` bleiben dünne Subclasses, die Name + Prompt-Key + Mode-Bezeichner durchreichen. Public-Interface (`TextProcessor.process(text) → str`) ändert sich nicht.

## State-Format

Neue Sektion `llm` in `state.json`:

```json
{
  "llm": {
    "default": "anthropic",
    "business": null,
    "rage": null,
    "providers": {
      "anthropic": {
        "api_key": "sk-ant-...",
        "model": "claude-sonnet-4-20250514",
        "timeout": 15.0
      },
      "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key": "sk-...",
        "model": "gpt-4o",
        "timeout": 15.0
      },
      "ollama": {
        "base_url": "http://localhost:11434",
        "model": "llama3.1:8b",
        "timeout": 30.0
      }
    }
  }
}
```

- `default`: Provider-ID (`"anthropic" | "openai" | "ollama"`). Wird genutzt, wenn der Mode-Override `null` ist.
- `business` / `rage`: `null` (= Default benutzen) oder eine Provider-ID.
- `providers`: Drei feste Slots. Schema bleibt erweiterbar — spätere benannte Instanzen ändern das Format nicht.

### Config-API

`Config` bekommt:

- `llm_provider_for(mode: str) → ProviderConfig` — löst Override + Default + Slot-Lookup auf.
- `llm_resolve(slot_id: str) → ProviderConfig` — liefert die Config für einen Slot, inklusive Migration-Fallback (siehe unten).

### Env-Overrides

Für Headless-/CI-Setups:

- `VOCIX_LLM_DEFAULT`, `VOCIX_LLM_BUSINESS`, `VOCIX_LLM_RAGE`
- Pro Slot: `VOCIX_LLM_<SLOT>_API_KEY`, `_MODEL`, `_BASE_URL`, `_TIMEOUT`

Priorität wie bisher: state.json > env > Default.

## Migration alter Anthropic-Konfiguration

Nicht-destruktiv und permanent — die Logik bleibt dauerhaft im Code, kein „migrate-once-and-delete":

1. **Lesen:** Beim Auflösen des Slots `anthropic` prüft `llm_resolve`, ob `llm.providers.anthropic.api_key` leer ist *und* das alte Top-Level-Feld `anthropic_api_key` gesetzt ist. Wenn ja, werden die Alt-Felder (`anthropic_api_key`, `anthropic_model`, `anthropic_timeout`) als Quelle genommen.
2. **Default-Provider:** Wenn `llm.default` fehlt und ein Alt-Key vorhanden ist, wird implizit `"anthropic"` zurückgegeben.
3. **Schreiben:** Die alten Top-Level-Keys werden *nie* automatisch gelöscht. Erst wenn der User im neuen Settings-Tab speichert, schreibt der Save-Pfad das neue `llm.*`-Schema *und* räumt die alten Top-Level-Keys aus `state.json`.
4. **Erstkontakt-Hinweis:** Beim ersten Start nach Update mit erkanntem Alt-Key zeigt VOCIX ein orangenes Overlay (i18n): *„Neu: VOCIX unterstützt jetzt mehrere KI-Provider. Deine bestehende Claude-Konfiguration läuft unverändert. Settings → KI-Provider zum Erweitern."* Persistiert via `state.json`-Flag `llm_migration_seen: true`, damit der Hinweis nur einmal erscheint.

Damit sind drei Szenarien abgedeckt:

- User aktualisiert und tut nichts → läuft ewig auf den Alt-Feldern, kein Schaden.
- User öffnet Tab und speichert (auch ohne Änderung) → saubere Migration, Alt-Felder weg.
- User überspringt mehrere Versionen → Resolution-Logik ist rückwärtskompatibel und bleibt im Code.

## Settings-Dialog — Tab „KI-Provider"

Drei Bereiche untereinander:

**A) Modus-Zuordnung** (oben)
- Default-Provider: Dropdown (Anthropic / OpenAI-kompatibel / Ollama)
- Business: Dropdown (Default benutzen / Anthropic / OpenAI-kompatibel / Ollama)
- Rage: Dropdown (Default benutzen / Anthropic / OpenAI-kompatibel / Ollama)

**B) Provider-Konfiguration** — drei Karten, je Slot:
- **Anthropic:** API-Key (Password-Field), Modell (Text), Timeout (Sek), Test-Button
- **OpenAI-kompatibel:** Base-URL, API-Key (Password-Field), Modell (Text), Timeout, Test-Button
- **Ollama:** Base-URL, Modell (Text), Timeout, Test-Button

**C) Test-Button** sendet eine 1-Token-Completion (System: „You are a test.", User: „ping") im Background-Thread. Zeigt neben dem Button ✓ (grün) oder gekürzte Fehlermeldung (rot). UI bleibt während des Tests bedienbar.

**Persistenz:** Speichern beim globalen „Übernehmen"-Button des Dialogs (gleiches Muster wie andere Tabs). Live-Wechsel ohne Neustart — beim nächsten `process()`-Call wird die neue Config gelesen und ein neuer Provider instanziiert.

## i18n-Strings (neu)

Minimal-Set in `vocix/locales/de.json` und `en.json`:

- `provider.anthropic.name`, `provider.openai.name`, `provider.ollama.name`
- `provider.test.success`, `provider.test.error`, `provider.test.in_progress`
- `provider.fallback.toast` (mit Platzhalter `{mode}`, z. B. „{mode} nicht verfügbar — Cleanmodus aktiv" / „{mode} unavailable — using Clean mode")
- `settings.llm.title`, `settings.llm.default`, `settings.llm.business_override`, `settings.llm.rage_override`, `settings.llm.use_default`
- `settings.llm.api_key`, `settings.llm.base_url`, `settings.llm.model`, `settings.llm.timeout`, `settings.llm.test_button`
- `migration.llm.headline` (Erstkontakt-Overlay)

## Tests

- `tests/processing/providers/test_anthropic.py` — Mock-anthropic-Client: Erfolg, Auth-Fehler, Timeout, leerer Content, Non-Text-Block. Erwartet `ProviderError` oder String.
- `tests/processing/providers/test_openai.py` — Mock-OpenAI-Client (`base_url`-Variation testen): Erfolg, Auth, Timeout, leerer Content.
- `tests/processing/providers/test_ollama.py` — Mock-`urllib.request`: Erfolg, HTTP-Fehler, Timeout, leerer Content.
- `tests/processing/test_llm_backed.py` — Integration: Mock-Provider raised `ProviderError` → `LLMBackedProcessor.process()` ruft `CleanProcessor.process()` *und* den Fallback-Callback. Per-Mode-Override-Resolution (Override gesetzt → Override-Provider; Override `null` → Default).
- `tests/test_config_migration.py` — Resolution mit Alt-Feldern: leeres `llm.providers.anthropic` + gesetztes `anthropic_api_key` liefert die Alt-Werte. Save-Pfad schreibt neues Schema *und* räumt Alt-Felder.
- Bestehende `BusinessProcessor`/`RageProcessor`-Tests werden auf den neuen Datenpfad angepasst, Public-Interface bleibt grün.

## Risiken & Trade-offs

- **`openai`-Dependency** vergrößert das Bundle um ~1 MB. Akzeptabel — das ist der einzige Adapter, der mit OpenAI-kompatiblen Endpoints zuverlässig spricht. Eine Eigenimplementierung über `urllib` würde Auth-Header, Retry-Verhalten und Edge-Cases (Streaming-Off-Header etc.) duplizieren.
- **Klartext-Keys in state.json** ist bereits Status quo, aber bei drei Slots steigen die Auswirkungen eines Lecks. Mitigation: Folge-Ticket „Keyring-Härtung" (Out-of-Scope).
- **Modell-Textfeld statt Dropdown** kann zu Tippfehlern führen. Mitigation: Test-Button macht Tippfehler sofort sichtbar.
- **Drei-Slot-Schema** verhindert parallele Nutzung mehrerer OpenAI-kompatibler Endpoints (z. B. OpenAI + Groq gleichzeitig). Mitigation: Schema ist erweiterbar — bei realem Bedarf später ohne Breaking Change auf benannte Instanzen erweiterbar.

## Datei-Layout

Neu:
```
vocix/processing/providers/
    __init__.py              # exportiert ProviderError, build_provider(config)
    base.py                  # LLMProvider, ProviderError
    anthropic_provider.py
    openai_provider.py
    ollama_provider.py
docs/superpowers/specs/2026-04-26-llm-provider-abstraction-design.md
```

Geändert:
```
vocix/processing/claude_base.py   → llm_backed.py (umbenannt + generalisiert)
vocix/processing/business.py      # nutzt LLMBackedProcessor
vocix/processing/rage.py          # nutzt LLMBackedProcessor
vocix/config.py                   # neue llm-Sektion + Helper + Migration-Resolution
vocix/ui/settings_dialog.py       # neuer Tab „KI-Provider"
vocix/locales/de.json             # neue Keys
vocix/locales/en.json             # neue Keys
requirements.txt                  # +openai>=1.0
```
