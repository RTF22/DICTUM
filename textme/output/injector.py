import logging
import time

import keyboard
import pyperclip

logger = logging.getLogger(__name__)


class TextInjector:
    """Fügt Text an der aktuellen Cursorposition ein (systemweit).

    Methode: Zwischenablage sichern → Text kopieren → Ctrl+V → Zwischenablage wiederherstellen.
    Dies ist die einzige Methode, die zuverlässig in allen Windows-Anwendungen
    funktioniert, einschließlich Umlaute und Sonderzeichen.
    """

    def inject(self, text: str) -> None:
        if not text.strip():
            logger.warning("Leerer Text, nichts einzufügen")
            return

        # Aktuelle Zwischenablage sichern
        try:
            original_clipboard = pyperclip.paste()
        except pyperclip.PyperclipException:
            original_clipboard = ""

        try:
            # Text in Zwischenablage
            pyperclip.copy(text)
            # Kurze Pause damit die Zwischenablage bereit ist
            time.sleep(0.05)
            # Ctrl+V senden
            keyboard.send("ctrl+v")
            # Pause damit die Anwendung den Paste verarbeiten kann
            time.sleep(0.1)
            logger.info("Text eingefügt (%d Zeichen)", len(text))
        except Exception as e:
            logger.error("Fehler beim Einfügen: %s", e)
            raise
        finally:
            # Zwischenablage wiederherstellen
            time.sleep(0.05)
            try:
                pyperclip.copy(original_clipboard)
            except pyperclip.PyperclipException:
                pass
