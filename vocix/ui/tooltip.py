"""Tooltip-Helper für tkinter-Widgets.

Zeigt nach 600 ms Maus-Stillstand ein Toplevel ohne Border mit gelbem
Hintergrund neben dem Cursor. Verschwindet bei <Leave> oder <ButtonPress>.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

_DELAY_MS = 600
_BG = "#ffffe0"
_FG = "#000000"
_BORDER = "#888888"


class Tooltip:
    def __init__(self, widget: tk.Widget, text_provider: Callable[[], str]):
        self._widget = widget
        self._provider = text_provider
        self._after_id: str | None = None
        self._tip_window: tk.Toplevel | None = None
        self._label: tk.Label | None = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _schedule(self, _event=None) -> None:
        self._cancel()
        self._after_id = self._widget.after(_DELAY_MS, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            try:
                self._widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self) -> None:
        if self._tip_window is not None:
            return
        text = self._provider()
        if not text:
            return
        x = self._widget.winfo_rootx() + 16
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg=_BORDER)
        self._label = tk.Label(
            tw, text=text, justify="left", background=_BG, foreground=_FG,
            relief="flat", borderwidth=0, padx=8, pady=4, wraplength=360,
        )
        self._label.pack(padx=1, pady=1)
        self._tip_window = tw

    def _hide(self) -> None:
        if self._tip_window is not None:
            try:
                self._tip_window.destroy()
            except tk.TclError:
                pass
            self._tip_window = None
            self._label = None

    def _on_leave(self, _event=None) -> None:
        self._cancel()
        self._hide()
