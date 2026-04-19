import logging
import sys
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

from vocix.config import Config
from vocix.i18n import t
from vocix.stt.base import STTEngine
from vocix.ui import native_dialog

logger = logging.getLogger(__name__)


class WhisperSTT(STTEngine):
    """Speech-to-Text mit faster-whisper (CTranslate2)."""

    def __init__(self, config: Config):
        self._config = config
        model_dir = Path(config.whisper_model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Lade Whisper-Modell '%s' (Verzeichnis: %s)...",
                     config.whisper_model, model_dir)
        try:
            self._model = WhisperModel(
                config.whisper_model,
                device="cpu",
                compute_type="int8",
                download_root=str(model_dir),
            )
        except Exception as e:
            # CTranslate2 crasht auf pre-AVX-CPUs mit RuntimeError, OSError oder
            # segfault-nahen Fehlern. Statt kommentarlos wegzusterben: klarer
            # Dialog + sauberer Exit. Overlay/Tray laufen beim Modellladen noch
            # nicht, also direkt Win32-MessageBox.
            logger.critical("Whisper-Modell konnte nicht geladen werden: %s", e, exc_info=True)
            native_dialog.show_error(
                t("error.cpu_unsupported_title"),
                t("error.cpu_unsupported_body", details=str(e)[:200]),
            )
            sys.exit(1)
        logger.info("Whisper-Modell geladen")

    def transcribe(self, audio: np.ndarray) -> str:
        kwargs = {
            "language": self._config.whisper_language,
            "beam_size": 5,
            "vad_filter": True,
        }
        if self._config.translate_to_english:
            kwargs["task"] = "translate"
        segments, info = self._model.transcribe(audio, **kwargs)
        text = " ".join(segment.text.strip() for segment in segments)
        task = kwargs.get("task", "transcribe")
        logger.info("Transkription (task=%s, source=%s, %.0f%% Konfidenz): %s",
                     task, info.language, info.language_probability * 100, text)
        return text
