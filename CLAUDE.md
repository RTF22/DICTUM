# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projekt

TextME — Lokale Windows-11-Sprachdiktion mit globalem Hotkey. Nimmt Sprache auf, transkribiert mit faster-whisper, transformiert je nach Modus (Clean/Business/Rage), fügt Text systemweit an Cursorposition ein.

## Ausführen

```bash
# Setup (einmalig)
pip install -r requirements.txt

# .env anlegen mit ANTHROPIC_API_KEY (für Modus B/C)
cp .env.example .env

# Starten
python -m textme.main
```

Erfordert Mikrofon. Beim ersten Start wird das Whisper-Modell heruntergeladen (~500MB für "small").

## Architektur

Datenfluss: `Hotkey → AudioRecorder → WhisperSTT → TextProcessor → TextInjector → Ctrl+V`

- **audio/recorder.py** — sounddevice-basierte Aufnahme mit Stille-/Mindestlängen-Erkennung
- **stt/base.py + whisper_stt.py** — Abstrakte STT-Schnittstelle, faster-whisper Implementierung
- **processing/base.py** — Abstrakte Prozessor-Schnittstelle; Modi in clean.py (lokal/regex), business.py und rage.py (Claude API mit Fallback auf Clean)
- **output/injector.py** — Clipboard-basierte systemweite Texteinfügung (einzige zuverlässige Methode für Umlaute in allen Apps)
- **ui/overlay.py** — tkinter Status-Overlay in eigenem Thread
- **ui/tray.py** — pystray System Tray mit Moduswechsel
- **config.py** — Zentrale Konfiguration, lädt .env

## Wichtige Design-Entscheidungen

- Texteinfügung über Clipboard+Ctrl+V statt pyautogui.write() — einzige Methode die Umlaute und Sonderzeichen in allen Windows-Apps unterstützt
- STT und TextProcessor sind über ABCs austauschbar — neue Engines/Modi können ohne Änderung am Bestandscode registriert werden
- Modus B/C nutzen Claude API, fallen automatisch auf Modus A zurück wenn kein API-Key vorhanden
- Push-to-Talk Pipeline läuft in separatem Thread damit der Hotkey-Handler nicht blockiert

## Hotkeys

- `Ctrl+Shift+Space` — Push-to-Talk (halten = aufnehmen, loslassen = verarbeiten)
- `Ctrl+Shift+1/2/3` — Moduswechsel Clean/Business/Rage
