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
        from vocix.ui.tooltip import Tooltip
        from vocix.ui.help_popup import HelpButton
        from vocix.stt.whisper_stt import cuda_available

        for col, weight in ((0, 0), (1, 1), (2, 0), (3, 0)):
            frame.columnconfigure(col, weight=weight)

        row = 0

        # Eingabesprache
        lbl = ttk.Label(frame, text=t("settings.field.input_language"))
        lbl.grid(row=row, column=0, sticky="w", pady=4)
        self._var_input_lang = tk.StringVar(value=self._draft.language)
        sub = ttk.Frame(frame)
        sub.grid(row=row, column=1, sticky="w")
        ttk.Radiobutton(sub, text=t("settings.lang.de"), value="de",
                        variable=self._var_input_lang,
                        command=self._on_input_lang_changed).pack(side="left")
        ttk.Radiobutton(sub, text=t("settings.lang.en"), value="en",
                        variable=self._var_input_lang,
                        command=self._on_input_lang_changed).pack(side="left", padx=(8, 0))
        self._other_lang_combo = ttk.Combobox(
            sub, state="readonly", width=10,
            values=("fr", "es", "it", "nl", "pl", "pt", "tr", "ru", "ja", "zh"),
        )
        self._other_lang_combo.pack(side="left", padx=(8, 0))
        self._other_lang_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_other_lang_picked())
        Tooltip(lbl, lambda: t("settings.tooltip.input_language"))
        row += 1

        # Ausgabesprache
        ttk.Label(frame, text=t("settings.field.output_language")).grid(row=row, column=0, sticky="w", pady=4)
        self._var_output_lang = tk.StringVar(
            value="english" if self._draft.translate_to_english else "input"
        )
        out_combo = ttk.Combobox(frame, state="readonly", width=24, textvariable=self._var_output_lang,
                                 values=("input", "english"))
        out_combo.grid(row=row, column=1, sticky="w")
        out_combo.bind("<<ComboboxSelected>>",
                       lambda _e: setattr(self._draft, "translate_to_english",
                                          self._var_output_lang.get() == "english"))
        Tooltip(out_combo, lambda: t("settings.tooltip.output_language"))
        row += 1

        # Whisper-Modell
        ttk.Label(frame, text=t("settings.field.whisper_model")).grid(row=row, column=0, sticky="w", pady=4)
        self._var_whisper_model = tk.StringVar(value=self._draft.whisper_model)
        wm = ttk.Combobox(frame, state="readonly", width=24, textvariable=self._var_whisper_model,
                          values=("tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"))
        wm.grid(row=row, column=1, sticky="w")
        wm.bind("<<ComboboxSelected>>",
                lambda _e: setattr(self._draft, "whisper_model", self._var_whisper_model.get()))
        Tooltip(wm, lambda: t("settings.tooltip.whisper_model"))
        HelpButton(frame,
                   title_provider=lambda: t("settings.help.whisper_model.title"),
                   body_provider=lambda: t("settings.help.whisper_model.body")
                   ).grid(row=row, column=2, padx=4)
        row += 1

        # Beschleunigung
        ttk.Label(frame, text=t("settings.field.acceleration")).grid(row=row, column=0, sticky="w", pady=4)
        self._var_acceleration = tk.StringVar(value=self._draft.whisper_acceleration)
        accel_frame = ttk.Frame(frame)
        accel_frame.grid(row=row, column=1, sticky="w")
        gpu_ok = cuda_available()
        for value, label in (("auto", "Auto"), ("gpu", "GPU"), ("cpu", "CPU")):
            rb = ttk.Radiobutton(accel_frame, text=label, value=value,
                                 variable=self._var_acceleration,
                                 command=lambda: setattr(self._draft,
                                                         "whisper_acceleration",
                                                         self._var_acceleration.get()))
            rb.pack(side="left", padx=4)
            if value == "gpu" and not gpu_ok:
                rb.state(["disabled"])
        Tooltip(accel_frame, lambda: t("settings.tooltip.acceleration"))
        HelpButton(frame,
                   title_provider=lambda: t("settings.help.acceleration.title"),
                   body_provider=lambda: t("settings.help.acceleration.body")
                   ).grid(row=row, column=2, padx=4)
        row += 1

        # API-Key
        ttk.Label(frame, text=t("settings.field.api_key")).grid(row=row, column=0, sticky="w", pady=4)
        self._var_api_key = tk.StringVar(value=self._draft.anthropic_api_key)
        self._api_entry = ttk.Entry(frame, textvariable=self._var_api_key, show="*", width=30)
        self._api_entry.grid(row=row, column=1, sticky="ew")
        ttk.Button(frame, text=t("settings.button.test"), command=self._on_test_api).grid(
            row=row, column=2, padx=4)
        self._var_api_status = tk.StringVar(value=t("settings.status.api_unchecked"))
        ttk.Label(frame, textvariable=self._var_api_status).grid(row=row, column=3, sticky="w")
        Tooltip(self._api_entry, lambda: t("settings.tooltip.api_key"))
        row += 1

        # Default Mode
        ttk.Label(frame, text=t("settings.field.default_mode")).grid(row=row, column=0, sticky="w", pady=4)
        self._var_default_mode = tk.StringVar(value=self._draft.default_mode)
        self._mode_combo = ttk.Combobox(frame, state="readonly", width=24, textvariable=self._var_default_mode)
        self._update_mode_combo_values()
        self._mode_combo.grid(row=row, column=1, sticky="w")
        self._mode_combo.bind("<<ComboboxSelected>>",
                              lambda _e: setattr(self._draft, "default_mode", self._var_default_mode.get()))
        Tooltip(self._mode_combo, lambda: t("settings.tooltip.default_mode"))
        row += 1

        # Hotkeys
        self._hotkey_vars: dict[str, tk.StringVar] = {}
        self._hotkey_widgets: dict[str, tuple] = {}
        for attr, label_key, allow_combo in (
            ("hotkey_record", "settings.field.hotkey_record", False),
            ("hotkey_mode_a", "settings.field.hotkey_mode_a", True),
            ("hotkey_mode_b", "settings.field.hotkey_mode_b", True),
            ("hotkey_mode_c", "settings.field.hotkey_mode_c", True),
        ):
            ttk.Label(frame, text=t(label_key)).grid(row=row, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=getattr(self._draft, attr))
            self._hotkey_vars[attr] = var
            picks = (("pause", "scroll lock", "f7", "f8", "f9", "f10", "f11", "f12", "insert", "apps")
                     if not allow_combo else
                     ("ctrl+shift+1", "ctrl+shift+2", "ctrl+shift+3",
                      "ctrl+alt+1", "ctrl+alt+2", "ctrl+alt+3"))
            cb = ttk.Combobox(frame, textvariable=var, values=picks, width=24)
            cb.grid(row=row, column=1, sticky="w")
            cb.bind("<<ComboboxSelected>>",
                    lambda _e, a=attr, v=var: self._on_hotkey_changed(a, v.get()))
            cb.bind("<FocusOut>",
                    lambda _e, a=attr, v=var: self._on_hotkey_changed(a, v.get()))
            btn = ttk.Button(frame, text=t("settings.button.other_key"),
                             command=lambda a=attr, c=allow_combo: self._capture_hotkey(a, c))
            btn.grid(row=row, column=2, padx=4)
            self._hotkey_widgets[attr] = (cb, btn)
            if attr == "hotkey_record":
                Tooltip(cb, lambda: t("settings.tooltip.hotkey_record"))
            row += 1

        self._refresh_api_gated_widgets()

    def _on_input_lang_changed(self) -> None:
        v = self._var_input_lang.get()
        if v in ("de", "en"):
            self._draft.language = v
            self._other_lang_combo.set("")

    def _on_other_lang_picked(self) -> None:
        v = self._other_lang_combo.get()
        if v:
            self._draft.language = v
            self._var_input_lang.set("")

    def _update_mode_combo_values(self) -> None:
        valid = bool(self._draft.anthropic_api_key) and self._key_validated()
        self._mode_combo["values"] = ("clean", "business", "rage") if valid else ("clean",)
        if not valid and self._var_default_mode.get() != "clean":
            self._var_default_mode.set("clean")
            self._draft.default_mode = "clean"

    def _key_validated(self) -> bool:
        from vocix.config import load_state
        return bool(load_state().get("anthropic_key_validated"))

    def _refresh_api_gated_widgets(self) -> None:
        valid = bool(self._draft.anthropic_api_key) and self._key_validated()
        for attr in ("hotkey_mode_b", "hotkey_mode_c"):
            cb, btn = self._hotkey_widgets[attr]
            state = ["!disabled"] if valid else ["disabled"]
            cb.state(state)
            btn.state(state)
        self._update_mode_combo_values()

    def _on_hotkey_changed(self, attr: str, value: str) -> None:
        setattr(self._draft, attr, value.strip())
        self._validate()

    def _capture_hotkey(self, attr: str, allow_combos: bool) -> None:
        from vocix.ui.hotkey_capture import HotkeyCaptureDialog

        def done(hk):
            if hk:
                self._hotkey_vars[attr].set(hk)
                self._on_hotkey_changed(attr, hk)

        HotkeyCaptureDialog(self._win, allow_combos=allow_combos, on_result=done)

    def _on_test_api(self) -> None:
        # Implementation in Task 10
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
