from vocix.ui.hotkey_capture import keysym_to_hotkey, format_hotkey


def test_keysym_to_hotkey_single_key():
    assert keysym_to_hotkey("Pause", set()) == "pause"
    assert keysym_to_hotkey("F9", set()) == "f9"
    assert keysym_to_hotkey("Scroll_Lock", set()) == "scroll lock"


def test_keysym_to_hotkey_with_modifiers():
    assert keysym_to_hotkey("1", {"ctrl", "shift"}) == "ctrl+shift+1"
    assert keysym_to_hotkey("F4", {"alt"}) == "alt+f4"


def test_keysym_to_hotkey_ignores_pure_modifier():
    assert keysym_to_hotkey("Control_L", set()) is None
    assert keysym_to_hotkey("Shift_R", set()) is None


def test_format_hotkey_human_readable():
    assert format_hotkey("ctrl+shift+1") == "Ctrl+Shift+1"
    assert format_hotkey("pause") == "Pause"
