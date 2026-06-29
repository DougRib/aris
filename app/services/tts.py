"""Text-to-speech backends."""

from __future__ import annotations

import asyncio
import ctypes
import sys
import threading
import time
from pathlib import Path

from loguru import logger


class EdgeTTS:
    """Edge TTS backend (online)."""

    def __init__(
        self,
        voice: str,
        rate: str,
        pitch: str,
        volume: str,
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
        self.echo_volume = int(echo_volume or 0)
        self.echo2_delay_ms = max(0, int(echo2_delay_ms or 0))
        self.echo2_volume = int(echo2_volume or 0)
        if self.echo_volume < 0:
            self.echo_volume = 0
        elif self.echo_volume > 1000:
            self.echo_volume = 1000
        if self.echo2_volume < 0:
            self.echo2_volume = 0
        elif self.echo2_volume > 1000:
            self.echo2_volume = 1000
        self._edge_tts = None
        self._playsound = None
        self._ready = False
        self._mci = None

        try:
            import edge_tts  # type: ignore
        except Exception as exc:
            logger.warning(f"Edge TTS nao disponivel: {exc}")
            return

        if sys.platform.startswith("win"):
            try:
                self._mci = ctypes.windll.winmm.mciSendStringW
            except Exception:
                self._mci = None
        else:
            try:
                from playsound import playsound  # type: ignore
            except Exception as exc:
                logger.warning(f"Playsound nao disponivel: {exc}")
                return
            self._playsound = playsound

        self._edge_tts = edge_tts
        self._ready = True

        base_dir = Path(__file__).resolve().parents[2]
        self.output_dir = base_dir / "data/tts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def is_ready(self) -> bool:
        return self._ready

    def speak(self, text: str) -> bool:
        if not self._ready:
            return False
        if not text or not text.strip():
            return True

        filename = self.output_dir / f"edge_{time.time_ns()}.mp3"
        try:
            self._run_tts(text, filename)
            return self._play_audio(filename)
        except Exception as exc:
            logger.error(f"Erro Edge TTS: {exc}")
            return False
        finally:
            try:
                filename.unlink(missing_ok=True)
            except Exception:
                pass

    def _run_tts(self, text: str, filename: Path) -> None:
        async def _sintetizar():
            communicate = self._edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch,
            )
            await communicate.save(str(filename))

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            new_loop = asyncio.new_event_loop()
            try:
                new_loop.run_until_complete(_sintetizar())
            finally:
                new_loop.close()
        else:
            asyncio.run(_sintetizar())

    def _play_audio(self, filename: Path) -> bool:
        if self._mci:
            alias = f"edge_{time.time_ns()}"
            try:
                self._mci(f'open "{filename}" type mpegvideo alias {alias}', None, 0, None)

                def _schedule_echo(delay_ms: int, volume: int, index: int) -> None:
                    if not delay_ms or not volume:
                        return
                    echo_alias = f"{alias}_echo_{index}"
                    try:
                        self._mci(
                            f'open "{filename}" type mpegvideo alias {echo_alias}',
                            None,
                            0,
                            None,
                        )
                        self._mci(
                            f"setaudio {echo_alias} volume to {volume}",
                            None,
                            0,
                            None,
                        )
                    except Exception as exc:
                        logger.warning(f"Echo indisponivel: {exc}")
                        try:
                            self._mci(f"close {echo_alias}", None, 0, None)
                        except Exception:
                            pass
                        return

                    def _play_echo():
                        time.sleep(delay_ms / 1000)
                        try:
                            self._mci(f"play {echo_alias} wait", None, 0, None)
                        finally:
                            try:
                                self._mci(f"close {echo_alias}", None, 0, None)
                            except Exception:
                                pass

                    threading.Thread(target=_play_echo, daemon=True).start()

                _schedule_echo(self.echo_delay_ms, self.echo_volume, 1)
                _schedule_echo(self.echo2_delay_ms, self.echo2_volume, 2)
                self._mci(f"play {alias} wait", None, 0, None)
                self._mci(f"close {alias}", None, 0, None)
                return True
            except Exception as exc:
                logger.error(f"Erro ao reproduzir audio (MCI): {exc}")
                try:
                    self._mci(f"close {alias}", None, 0, None)
                except Exception:
                    pass
                return False

        if self._playsound:
            self._playsound(str(filename))
            return True

        logger.error("Nenhum metodo de reproducao de audio disponivel.")
        return False
