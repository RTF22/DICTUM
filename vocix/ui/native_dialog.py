"""Native Windows-Dialoge via Win32 MessageBoxW.

Vermeidet zusätzliche tkinter-Roots — z.B. für den About-Dialog und den
AVX-Fehler beim Modellladen, bei dem das Status-Overlay noch nicht läuft.
"""

from __future__ import annotations

import ctypes
import logging
import webbrowser
from ctypes import wintypes

logger = logging.getLogger(__name__)

# MessageBox-Flags (Win32)
_MB_OK = 0x00000000
_MB_OKCANCEL = 0x00000001
_MB_YESNO = 0x00000004
_MB_ICONERROR = 0x00000010
_MB_ICONINFORMATION = 0x00000040
_MB_SYSTEMMODAL = 0x00001000
_MB_TOPMOST = 0x00040000

_IDOK = 1
_IDYES = 6


def _message_box(title: str, body: str, flags: int) -> int:
    try:
        return int(ctypes.windll.user32.MessageBoxW(0, body, title, flags))
    except OSError as e:
        # Kein Windows / ctypes-Problem → Fallback auf stderr
        logger.warning("MessageBoxW fehlgeschlagen: %s", e)
        print(f"\n[{title}]\n{body}\n")
        return _IDOK


def show_error(title: str, body: str) -> None:
    """Modaler Fehler-Dialog mit OK-Button. Blockiert bis der User quittiert."""
    _message_box(title, body, _MB_OK | _MB_ICONERROR | _MB_TOPMOST)


def show_info_with_link(title: str, body: str) -> bool:
    """Info-Dialog mit Ja/Nein (Ja = „Browser öffnen"). Gibt True zurück bei Ja."""
    result = _message_box(title, body, _MB_YESNO | _MB_ICONINFORMATION | _MB_TOPMOST)
    return result == _IDYES


def show_info(title: str, body: str) -> None:
    """Modaler Info-Dialog mit OK-Button."""
    _message_box(title, body, _MB_OK | _MB_ICONINFORMATION | _MB_TOPMOST)


# --- TaskDialogIndirect (comctl32 v6) für Info-Dialog mit Hyperlink ---------

_TDF_ENABLE_HYPERLINKS = 0x0001
_TDCBF_OK_BUTTON = 0x0001
_TDN_HYPERLINK_CLICKED = 3
_TD_INFORMATION_ICON = 65533  # MAKEINTRESOURCEW(-3) = WORD(-3) = 0xFFFD
_S_OK = 0


class _TASKDIALOG_BUTTON(ctypes.Structure):
    _fields_ = [
        ("nButtonID", ctypes.c_int),
        ("pszButtonText", wintypes.LPCWSTR),
    ]


_PFTASKDIALOGCALLBACK = ctypes.WINFUNCTYPE(
    ctypes.c_long,  # HRESULT
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    ctypes.c_void_p,
)


class _TASKDIALOGCONFIG(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("hwndParent", wintypes.HWND),
        ("hInstance", wintypes.HINSTANCE),
        ("dwFlags", wintypes.DWORD),
        ("dwCommonButtons", wintypes.DWORD),
        ("pszWindowTitle", wintypes.LPCWSTR),
        ("hMainIcon", ctypes.c_void_p),  # union mit pszMainIcon (MAKEINTRESOURCE)
        ("pszMainInstruction", wintypes.LPCWSTR),
        ("pszContent", wintypes.LPCWSTR),
        ("cButtons", wintypes.UINT),
        ("pButtons", ctypes.POINTER(_TASKDIALOG_BUTTON)),
        ("nDefaultButton", ctypes.c_int),
        ("cRadioButtons", wintypes.UINT),
        ("pRadioButtons", ctypes.POINTER(_TASKDIALOG_BUTTON)),
        ("nDefaultRadioButton", ctypes.c_int),
        ("pszVerificationText", wintypes.LPCWSTR),
        ("pszExpandedInformation", wintypes.LPCWSTR),
        ("pszExpandedControlText", wintypes.LPCWSTR),
        ("pszCollapsedControlText", wintypes.LPCWSTR),
        ("hFooterIcon", ctypes.c_void_p),
        ("pszFooter", wintypes.LPCWSTR),
        ("pfCallback", _PFTASKDIALOGCALLBACK),
        ("lpCallbackData", ctypes.c_size_t),
        ("cxWidth", wintypes.UINT),
    ]


def _hyperlink_clicked(_hwnd, msg, _wparam, lparam, _refdata):
    if msg == _TDN_HYPERLINK_CLICKED and lparam:
        try:
            url = ctypes.wstring_at(lparam)
            webbrowser.open(url)
        except Exception as e:
            logger.warning("Hyperlink-Open fehlgeschlagen: %s", e)
    return _S_OK


# Callback-Referenz auf Modulebene halten — sonst sammelt der GC den Trampolin
# während der Dialog noch läuft.
_HYPERLINK_CALLBACK = _PFTASKDIALOGCALLBACK(_hyperlink_clicked)


def show_info_with_url(title: str, instruction: str, body: str, url: str) -> None:
    """Modaler Info-Dialog mit anklickbarer URL und einzelnem OK-Button.

    Nutzt TaskDialogIndirect (comctl32 v6, ab Windows Vista). Ein Klick auf
    den Link öffnet die URL im Standardbrowser; der Dialog bleibt offen, bis
    der User OK drückt. Fallback auf MessageBox, falls TaskDialogIndirect
    auf dem System nicht verfügbar ist.
    """
    content = f'{body}\n\n<a href="{url}">{url}</a>'
    config = _TASKDIALOGCONFIG()
    config.cbSize = ctypes.sizeof(_TASKDIALOGCONFIG)
    config.dwFlags = _TDF_ENABLE_HYPERLINKS
    config.dwCommonButtons = _TDCBF_OK_BUTTON
    config.pszWindowTitle = title
    config.hMainIcon = _TD_INFORMATION_ICON
    config.pszMainInstruction = instruction
    config.pszContent = content
    config.pfCallback = _HYPERLINK_CALLBACK

    button = ctypes.c_int(0)
    try:
        hr = ctypes.windll.comctl32.TaskDialogIndirect(
            ctypes.byref(config), ctypes.byref(button), None, None
        )
        if hr != _S_OK:
            raise OSError(f"TaskDialogIndirect HRESULT={hr:#x}")
    except (OSError, AttributeError) as e:
        logger.warning("TaskDialogIndirect fehlgeschlagen (%s) — Fallback MessageBox", e)
        _message_box(title, f"{instruction}\n\n{body}\n\n{url}",
                     _MB_OK | _MB_ICONINFORMATION | _MB_TOPMOST)
