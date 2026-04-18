**🌐 [English](REBRANDING.md) · [Deutsch](REBRANDING.de.md)**

# Rebranding: DICTUM → VOCIX

**TL;DR:** The project was called **DICTUM** up to v0.9.1. Since v1.0.0 (April 2026) it is called **VOCIX**. The code is identical — only the names changed.

## Why the switch?

"DICTUM" is a real Latin word ("statement", "maxim") and therefore attackable in trademark law. **VOCIX** is a pure coined word (from *VOice Capture & Intelligent eXpression*) — neutral-technical, no Google hits in the tech space, a clean mark for a possible commercial future.

The switch came early: at 4 releases and a single user. Later it would have grown exponentially more expensive.

## What does it mean for you as a new user?

**Nothing, except:** download `VOCIX-v1.0.0-win-x64.zip` and launch `VOCIX.exe`. Everything else is the same — push-to-talk with `F9`, three modes, system tray.

## What does it mean for existing DICTUM users?

If you still have a `DICTUM` version installed:

1. The **auto-update check** will announce v1.0.0 automatically on next launch (GitHub redirects forward the API call).
2. Download the new ZIP and extract it.
3. If a `.env` exists, replace `DICTUM_` with `VOCIX_`. Example:
   ```ini
   # Before
   DICTUM_HOTKEY_RECORD=f9
   # After
   VOCIX_HOTKEY_RECORD=f9
   ```
4. Optional: copy the `models/` folder from the old installation into the new `VOCIX/` folder to avoid re-downloading the 500 MB Whisper model.

Old state files under `%APPDATA%/TextME/` can be deleted — the new path is `%APPDATA%/VOCIX/`.

## What changed exactly?

| Old (DICTUM) | New (VOCIX) |
|---|---|
| Python package `dictum/` | `vocix/` |
| Entry point `python -m dictum.main` | `python -m vocix.main` |
| Env-var prefix `DICTUM_*` | `VOCIX_*` |
| Exe name `DICTUM.exe` | `VOCIX.exe` |
| State dir `%APPDATA%/TextME/` | `%APPDATA%/VOCIX/` |
| Log file `dictum.log` | `vocix.log` |
| GitHub repo `RTF22/DICTUM` | `RTF22/VOCIX` |
| Release asset `DICTUM-vX.Y.Z-win-x64.zip` | `VOCIX-vX.Y.Z-win-x64.zip` |

The old GitHub releases (`v0.8.x`, `v0.9.x`) stay as *DICTUM* builds — that is proper history, not baggage. Only from v1.0.0 onward does the new name apply.

## Functionality

Unchanged. The rebranding fixed **no** bug, added no feature and brought no performance change. It is pure relabelling.

The architecture, the three modes (Clean/Business/Rage), the auto-update check, push-to-talk — all identical to v0.9.1.
