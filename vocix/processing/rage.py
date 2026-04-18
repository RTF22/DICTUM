import logging

from vocix.config import Config
from vocix.i18n import t
from vocix.processing.base import TextProcessor
from vocix.processing.clean import CleanProcessor

logger = logging.getLogger(__name__)


class RageProcessor(TextProcessor):
    """Modus C: Deeskalation — aggressiv → höflich (Claude API)."""

    def __init__(self, config: Config):
        self._config = config
        self._fallback = CleanProcessor()
        self._client = None

        if config.anthropic_api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=config.anthropic_api_key,
                    timeout=config.anthropic_timeout,
                )
            except ImportError:
                logger.warning("anthropic-Paket nicht installiert, Fallback auf Clean-Modus")
        else:
            logger.warning("Kein ANTHROPIC_API_KEY gesetzt, Rage-Modus nutzt Clean-Fallback")

    @property
    def name(self) -> str:
        return "Rage"

    def process(self, text: str) -> str:
        if not text.strip():
            return text

        if self._client is None:
            logger.info("Rage-Fallback auf Clean-Modus")
            return self._fallback.process(text)

        try:
            response = self._client.messages.create(
                model=self._config.anthropic_model,
                max_tokens=1024,
                system=t("prompt.rage"),
                messages=[{"role": "user", "content": text}],
            )
            result = response.content[0].text.strip()
            logger.info("Rage-Transformation erfolgreich")
            return result
        except Exception as e:
            logger.error("Claude API Fehler: %s — Fallback auf Clean", e)
            return self._fallback.process(text)
