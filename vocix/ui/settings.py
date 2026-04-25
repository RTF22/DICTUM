"""Zentraler Einstellungsdialog fuer VOCIX.

Drei Tabs (Basics/Erweitert/Expert) mit allen Config-Feldern. Schreibt
nach state.json ueber VocixApp.apply_settings, das die Reload-Schritte
(Whisper, Hotkeys, i18n, Tray) orchestriert.
"""

from __future__ import annotations

import logging
import tkinter as tk
from dataclasses import replace
from tkinter import ttk
from typing import Callable

from vocix.config import Config
from vocix.i18n import t

logger = logging.getLogger(__name__)


class SettingsDialog:
    def __init__(
        self,
        parent: tk.Misc,
        *,
        config: Config,
        on_apply: Callable[[Config], None],
    ):
        self._original = config
        self._draft = replace(config)
        self._on_apply_cb = on_apply

        self._win = tk.Toplevel(parent)
        self._win.title(t("settings.title"))
        self._win.geometry("640x540")
        self._win.transient(parent.winfo_toplevel())
        self._win.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._win.grab_set()

        self.notebook = ttk.Notebook(self._win)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self._tab_basics = ttk.Frame(self.notebook, padding=12)
        self._tab_advanced = ttk.Frame(self.notebook, padding=12)
        self._tab_expert = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self._tab_basics, text=t("settings.tab.basics"))
        self.notebook.add(self._tab_advanced, text=t("settings.tab.advanced"))
        self.notebook.add(self._tab_expert, text=t("settings.tab.expert"))

        self._build_basics(self._tab_basics)
        self._build_advanced(self._tab_advanced)
        self._build_expert(self._tab_expert)

        self._error_var = tk.StringVar()
        ttk.Label(self._win, textvariable=self._error_var, foreground="#c0392b").pack(
            anchor="w", padx=12
        )

        btn_bar = ttk.Frame(self._win)
        btn_bar.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_bar, text=t("settings.button.ok"), command=self._on_ok).pack(side="right", padx=4)
        ttk.Button(btn_bar, text=t("settings.button.cancel"), command=self._on_cancel).pack(side="right", padx=4)
        self._apply_btn = ttk.Button(btn_bar, text=t("settings.button.apply"), command=self._on_apply)
        self._apply_btn.pack(side="right", padx=4)

    def _build_basics(self, frame: ttk.Frame) -> None:
        pass

    def _build_advanced(self, frame: ttk.Frame) -> None:
        pass

    def _build_expert(self, frame: ttk.Frame) -> None:
        pass

    def _validate(self) -> bool:
        self._error_var.set("")
        return True

    def _on_apply(self) -> None:
        if not self._validate():
            return
        self._on_apply_cb(replace(self._draft))

    def _on_ok(self) -> None:
        if not self._validate():
            return
        self._on_apply_cb(replace(self._draft))
        self.destroy()

    def _on_cancel(self) -> None:
        self.destroy()

    def destroy(self) -> None:
        try:
            self._win.grab_release()
            self._win.destroy()
        except tk.TclError:
            pass
