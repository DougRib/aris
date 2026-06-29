"""VoiceLoop — o laço always-active de voz do ARIS.

Roda numa thread de fundo: ouve o microfone (STT), processa o comando pelo
engine (com speak/listen reais, então skills interativas funcionam) e fala a
resposta (TTS). A cada passo emite eventos (estado, transcrição, resposta) por
um callback, que o gateway WebSocket repassa aos clientes (HUD).
"""

from collections.abc import Callable
from threading import Event, Thread

from loguru import logger

from aris.assistant import AssistantEngine
from aris.core.context import Context
from aris.voice.stt import SpeechToText
from aris.voice.tts import TextToSpeech

# Um evento é um dict simples: {"type": ..., ...}. O gateway o serializa em JSON.
EventEmitter = Callable[[dict[str, str]], None]

_SAIDA = ("desligar", "encerrar", "sair", "tchau")


class VoiceLoop:
    """Laço de voz always-active, executado numa thread daemon."""

    def __init__(
        self,
        engine: AssistantEngine,
        stt: SpeechToText,
        tts: TextToSpeech,
        on_event: EventEmitter,
    ) -> None:
        self._engine = engine
        self._stt = stt
        self._tts = tts
        self._emit = on_event
        self._running = Event()
        self._thread: Thread | None = None

    def is_running(self) -> bool:
        return self._running.is_set()

    def start(self) -> None:
        """Inicia o laço numa thread (idempotente)."""
        if self._thread and self._thread.is_alive():
            return
        self._running.set()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Sinaliza o encerramento do laço."""
        self._running.clear()

    # --- callbacks de contexto (usados também pelas skills interativas) ---

    def _falar(self, texto: str) -> None:
        if not texto:
            return
        self._emit({"type": "state", "state": "speaking"})
        self._emit({"type": "aris_said", "text": texto})
        self._tts.speak(texto)

    def _ouvir(self, timeout: float = 5, phrase_time_limit: float = 6, **_ignore: object) -> str:
        self._emit({"type": "state", "state": "listening"})
        texto = self._stt.listen(timeout=timeout, phrase_time_limit=phrase_time_limit)
        if texto:
            self._emit({"type": "user_said", "text": texto})
        return texto

    # --- laço ---

    def _run(self) -> None:
        try:
            self._stt.calibrate()
            ctx = Context(speak=self._falar, listen=self._ouvir)
            self._falar("Olá, senhor. ARIS online e pronto para ajudar.")
            while self._running.is_set():
                self._emit({"type": "state", "state": "idle"})
                if not self._step(ctx):
                    break
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro no laço de voz: {exc}")
        finally:
            self._running.clear()
            self._emit({"type": "state", "state": "stopped"})

    def _step(self, ctx: Context) -> bool:
        """Uma rodada ouvir→processar→falar. Retorna False para encerrar o laço."""
        texto = self._ouvir()
        if not texto:
            return True
        if any(p in texto for p in _SAIDA):
            self._falar("Encerrando. Até mais, senhor.")
            return False
        self._emit({"type": "state", "state": "processing"})
        resposta = self._engine.process(texto, ctx)
        if resposta:
            self._falar(resposta)
        return True
