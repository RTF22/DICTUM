"""Modal zum Erfassen eines Hotkeys per Tastendruck.

Gibt einen Hotkey-String im Format der keyboard-Library zurück
(pause, f9, ctrl+shift+1). Modifier-only-Tasten werden ignoriert.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from vocix.i18n import t


_MODIFIER_KEYSYMS = {
    "Control_L", "Control_R", "Shift_L", "Shift_R",
    "Alt_L", "Alt_R", "Meta_L", "Meta_R", "Super_L", "Super_R",
}

_KEYSYM_MAP = {
    "Pause": "pause",
    "Scroll_Lock": "scroll lock",
    "Caps_Lock": "caps lock",
    "Insert": "insert", "Delete": "delete",
    "Home": "home", "End": "end",
    "Prior": "page up", "Next": "page down",
    "Up": "up", "Down": "down", "Left": "left", "Right": "right",
    "Return": "enter", "BackSpace": "backspace", "Tab": "tab",
    "space": "space",
    "App": "apps",
}


def keysym_to_hotkey(keysym: str, modifiers: set[str]) -> str | None:
    if keysym in _MODIFIER_KEYSYMS:
        return None
    if keysym.startswith("F") and keysym[1:].isdigit():
        key = keysym.lower()
    elif keysym in _KEYSYM_MAP:
        key = _KEYSYM_MAP[keysym]
    elif len(keysym) == 1:
        key = keysym.lower()
    else:
        key = keysym.lower()

    parts: list[str] = []
    for mod in ("ctrl", "alt", "shift"):
        if mod in modifiers:
            parts.append(mod)
    parts.append(key)
    return "+".join(parts)


def format_hotkey(hk: str) -> str:
    parts = []
    for p in hk.split("+"):
        if p in ("scroll lock", "caps lock", "page up", "page down"):
            parts.append(p.title())
        else:
            parts.append(p.capitalize())
    return "+".join(parts)


class HotkeyCaptureDialog:
    def __init__(self, parent: tk.Misc, *, allow_combos: bool, on_result: Callable[[str | None], None]):
        self._on_result = on_result
        self._allow_combos = allow_combos

        self._win = tk.Toplevel(parent)
        self._win.title(t("settings.button.other_key"))
        self._win.transient(parent.winfo_toplevel())
        self._win.geometry("360x140")
        self._win.resizable(False, False)
        self._win.grab_set()
        self._win.focus_force()

        ttk.Label(self._win, text=t("settings.capture.prompt"), font=("", 11)).pack(pady=(20, 4))
        ttk.Label(self._win, text=t("settings.capture.cancel_hint"), foreground="#666").pack()

        self._error_var = tk.StringVar()
        ttk.Label(self._win, textvariable=self._error_var, foreground="#c0392b").pack(pady=(8, 0))

        self._win.bind("<Key>", self._on_key)
        self._win.bind("<Escape>", lambda _e: self._finish(None))
        self._win.protocol("WM_DELETE_WINDOW", lambda: self._finish(None))

    def _on_key(self, event) -> None:
        if event.keysym == "Escape":
            return
        modifiers: set[str] = set()
        if event.state & 0x0004:
            modifiers.add("ctrl")
        if event.state & 0x0001:
            modifiers.add("shift")
        if event.state & 0x0008 or event.state & 0x0080:
            modifiers.add("alt")

        hk = keysym_to_hotkey(event.keysym, modifiers)
        if hk is None:
            return

        if not self._allow_combos and "+" in hk:
            self._error_var.set(t("settings.error.ptt_combo_not_allowed"))
            return

        self._finish(hk)

    def _finish(self, result: str | None) -> None:
        self._on_result(result)
        try:
            self._win.grab_release()
            self._win.destroy()
        except tk.TclError:
            pass
