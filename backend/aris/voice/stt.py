"""Reconhecimento de voz (STT) — interface e implementação Google Speech.

Porta a lógica do ARIS legado: usa a biblioteca SpeechRecognition com a API
gratuita do Google, em PT-BR. O import é tardio para que importar este módulo
não exija o microfone nem as libs de áudio (útil em testes).
"""

import importlib
import sys
import types
from typing import Protocol

from loguru import logger


def _ensure_distutils() -> None:
    """Versões antigas do SpeechRecognition importam distutils.version (removido no py3.12+)."""
    if "distutils.version" in sys.modules:
        return
    try:
        distutils_version = importlib.import_module("setuptools._distutils.version")
    except Exception:
        return
    distutils = types.ModuleType("distutils")
    version = types.ModuleType("distutils.version")
    version.LooseVersion = distutils_version.LooseVersion  # type: ignore[attr-defined]
    distutils.version = version  # type: ignore[attr-defined]
    sys.modules.setdefault("distutils", distutils)
    sys.modules.setdefault("distutils.version", version)


class SpeechToText(Protocol):
    """Qualquer reconhecedor de fala que devolva texto a partir do microfone."""

    def calibrate(self) -> None:
        """Ajusta o reconhecedor ao ruído ambiente (uma vez, no início)."""
        ...

    def listen(self, timeout: float = 5, phrase_time_limit: float = 6) -> str:
        """Captura uma fala e retorna o texto reconhecido (ou '' em falha/silêncio)."""
        ...


class GoogleSTT:
    """STT via API gratuita do Google Speech (online), em PT-BR por padrão."""

    def __init__(self, language: str = "pt-BR") -> None:
        _ensure_distutils()
        import speech_recognition as sr  # import tardio (precisa de PyAudio)

        self._sr = sr
        self._recognizer = sr.Recognizer()
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.5
        self._recognizer.phrase_threshold = 0.3
        self._recognizer.non_speaking_duration = 0.3
        self._language = language

    def calibrate(self) -> None:
        """Calibra o nível de ruído ambiente do microfone."""
        try:
            with self._sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.8)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Não foi possível calibrar o microfone: {exc}")

    def listen(self, timeout: float = 5, phrase_time_limit: float = 6) -> str:
        """Ouve o microfone e devolve o texto em minúsculas, ou '' em silêncio/erro."""
        try:
            with self._sr.Microphone() as source:
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
            return self._recognizer.recognize_google(audio, language=self._language).lower()
        except self._sr.WaitTimeoutError:
            return ""
        except self._sr.UnknownValueError:
            return ""
        except self._sr.RequestError as exc:
            logger.error(f"Erro na API de STT: {exc}")
            return ""
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao ouvir: {exc}")
            return ""
