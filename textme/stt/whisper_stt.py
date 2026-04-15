import logging

import numpy as np
from faster_whisper import WhisperModel

from textme.config import Config
from textme.stt.base import STTEngine

logger = logging.getLogger(__name__)


class WhisperSTT(STTEngine):
    """Speech-to-Text mit faster-whisper (CTranslate2)."""

    def __init__(self, config: Config):
        self._config = config
        logger.info("Lade Whisper-Modell '%s'...", config.whisper_model)
        self._model = WhisperModel(
            config.whisper_model,
            device="cpu",
            compute_type="int8",
        )
        logger.info("Whisper-Modell geladen")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, info = self._model.transcribe(
            audio,
            language=self._config.whisper_language,
            beam_size=5,
            vad_filter=True,
        )
        text = " ".join(segment.text.strip() for segment in segments)
        logger.info("Transkription (%s, %.0f%% Konfidenz): %s",
                     info.language, info.language_probability * 100, text)
        return text
