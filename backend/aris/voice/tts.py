"""Síntese de voz (TTS) — interface, EdgeTTS (online) e pyttsx3 (offline).

Porta o backend de voz do ARIS legado: o EdgeTTS sintetiza para MP3 com a voz
neural do Edge e reproduz via MCI (winmm), com eco/reverb opcional. Se o Edge
não estiver disponível (sem internet/lib), usa-se o pyttsx3 offline.
"""

from __future__ import annotations

import asyncio
import ctypes
import sys
import threading
import time
from pathlib import Path
from typing import Protocol

from loguru import logger

from aris.config import Settings

_TTS_DIR = Path(__file__).resolve().parents[1] / "data" / "tts"


class TextToSpeech(Protocol):
    """Qualquer sintetizador que fale um texto. Retorna True se conseguiu."""

    def speak(self, text: str) -> bool:
        """Sintetiza e reproduz o texto. True em sucesso."""
        ...


class EdgeTTS:
    """Voz neural do Microsoft Edge (online), reproduzida via MCI no Windows."""

    def __init__(
        self,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
        echo_delay_ms: int = 0,
        echo_volume: int = 0,
        echo2_delay_ms: int = 0,
        echo2_volume: int = 0,
    ) -> None:
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        self.echo_delay_ms = max(0, int(echo_delay_ms or 0))
        self.echo_volume = min(1000, max(0, int(echo_volume or 0)))
        self.echo2_delay_ms = max(0, int(echo2_delay_ms or 0))
        self.echo2_volume = min(1000, max(0, int(echo2_volume or 0)))
        self._edge_tts = None
        self._mci = None
        self._ready = False

        try:
            import edge_tts  # import tardio
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Edge TTS indisponível: {exc}")
            return

        if sys.platform.startswith("win"):
            try:
                self._mci = ctypes.windll.winmm.mciSendStringW
            except Exception:  # noqa: BLE001
                self._mci = None

        self._edge_tts = edge_tts
        self._ready = True
        _TTS_DIR.mkdir(parents=True, exist_ok=True)

    def is_ready(self) -> bool:
        """True se o Edge TTS pôde ser inicializado."""
        return self._ready

    def speak(self, text: str) -> bool:
        """Sintetiza o texto em MP3 e o reproduz; remove o arquivo ao final."""
        if not self._ready:
            return False
        if not text or not text.strip():
            return True
        arquivo = _TTS_DIR / f"edge_{time.time_ns()}.mp3"
        try:
            self._sintetizar(text, arquivo)
            return self._reproduzir(arquivo)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro Edge TTS: {exc}")
            return False
        finally:
            try:
                arquivo.unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass

    def _sintetizar(self, text: str, arquivo: Path) -> None:
        async def _run() -> None:
            communicate = self._edge_tts.Communicate(  # type: ignore[union-attr]
                text=text, voice=self.voice, rate=self.rate, volume=self.volume, pitch=self.pitch
            )
            await communicate.save(str(arquivo))

        asyncio.run(_run())

    def _reproduzir(self, arquivo: Path) -> bool:
        if not self._mci:
            logger.error("Reprodução MCI indisponível (não-Windows).")
            return False
        alias = f"edge_{time.time_ns()}"
        try:
            self._mci(f'open "{arquivo}" type mpegvideo alias {alias}', None, 0, None)
            self._agendar_eco(arquivo, alias, self.echo_delay_ms, self.echo_volume, 1)
            self._agendar_eco(arquivo, alias, self.echo2_delay_ms, self.echo2_volume, 2)
            self._mci(f"play {alias} wait", None, 0, None)
            self._mci(f"close {alias}", None, 0, None)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao reproduzir áudio (MCI): {exc}")
            try:
                self._mci(f"close {alias}", None, 0, None)
            except Exception:  # noqa: BLE001
                pass
            return False

    def _agendar_eco(self, arquivo: Path, alias: str, delay_ms: int, volume: int, idx: int) -> None:
        """Toca uma cópia atrasada e mais baixa do áudio, criando o efeito de eco."""
        if not delay_ms or not volume:
            return
        echo_alias = f"{alias}_echo_{idx}"
        try:
            self._mci(f'open "{arquivo}" type mpegvideo alias {echo_alias}', None, 0, None)  # type: ignore[misc]
            self._mci(f"setaudio {echo_alias} volume to {volume}", None, 0, None)  # type: ignore[misc]
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Eco indisponível: {exc}")
            return

        def _tocar() -> None:
            time.sleep(delay_ms / 1000)
            try:
                self._mci(f"play {echo_alias} wait", None, 0, None)  # type: ignore[misc]
            finally:
                try:
                    self._mci(f"close {echo_alias}", None, 0, None)  # type: ignore[misc]
                except Exception:  # noqa: BLE001
                    pass

        threading.Thread(target=_tocar, daemon=True).start()


class Pyttsx3TTS:
    """Voz offline do sistema (fallback), via pyttsx3."""

    def __init__(self, rate: int = 180) -> None:
        import pyttsx3  # import tardio

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)

    def speak(self, text: str) -> bool:
        """Fala o texto usando o motor TTS do sistema."""
        try:
            self._engine.say(text)
            self._engine.runAndWait()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro pyttsx3: {exc}")
            return False


def build_tts(settings: Settings) -> TextToSpeech:
    """Escolhe o backend de TTS: Edge (se pronto) com fallback pyttsx3."""
    if settings.tts_engine.lower() == "edge":
        edge = EdgeTTS(
            voice=settings.edge_tts_voice,
            rate=settings.edge_tts_rate,
            pitch=settings.edge_tts_pitch,
            volume=settings.edge_tts_volume,
            echo_delay_ms=settings.edge_tts_echo_delay_ms,
            echo_volume=settings.edge_tts_echo_volume,
            echo2_delay_ms=settings.edge_tts_echo2_delay_ms,
            echo2_volume=settings.edge_tts_echo2_volume,
        )
        if edge.is_ready():
            return edge
        logger.warning("Edge TTS indisponível; usando pyttsx3.")
    return Pyttsx3TTS()
