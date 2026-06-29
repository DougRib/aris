"""Gateway WebSocket: ponto único onde clientes conversam com o ARIS.

Aceita comandos de texto (command_text) e controla o laço de voz
(start_voice/stop_voice). Os eventos do laço de voz (estado, transcrições,
respostas) são transmitidos a todos os clientes conectados — a ponte entre a
thread de voz e o loop assíncrono usa run_coroutine_threadsafe.
"""

from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger

from aris.api.events import ArisSaid
from aris.assistant import AssistantEngine, build_engine
from aris.config import settings


class ConnectionManager:
    """Mantém os clientes WebSocket conectados e transmite eventos a todos."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def remember_loop(self) -> None:
        """Guarda o event loop atual para enviar eventos vindos de outras threads."""
        self._loop = asyncio.get_running_loop()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    async def broadcast(self, msg: dict) -> None:
        """Envia a mensagem a todos os clientes, descartando os que caíram."""
        for ws in list(self._clients):
            try:
                await ws.send_json(msg)
            except Exception:  # noqa: BLE001
                self._clients.discard(ws)

    def emit_threadsafe(self, msg: dict[str, str]) -> None:
        """Chamado da thread de voz: agenda o broadcast no loop assíncrono."""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(msg), self._loop)


def _build_voice_loop(engine: AssistantEngine, manager: ConnectionManager):
    """Monta o laço de voz (best-effort: se o áudio falhar, a voz fica desabilitada)."""
    try:
        from aris.voice.loop import VoiceLoop
        from aris.voice.stt import GoogleSTT
        from aris.voice.tts import build_tts

        stt = GoogleSTT(settings.idioma_stt)
        tts = build_tts(settings)
        return VoiceLoop(engine, stt, tts, manager.emit_threadsafe)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Voz indisponível: {exc}")
        return None


def create_app(engine: AssistantEngine | None = None) -> FastAPI:
    """Cria a app FastAPI. Aceita um engine injetado (útil em testes)."""
    app = FastAPI(title="ARIS", version="0.1.0")
    engine = engine or build_engine(settings)
    manager = ConnectionManager()
    voice = _build_voice_loop(engine, manager)
    app.state.engine = engine
    app.state.voice = voice

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await manager.connect(websocket)
        manager.remember_loop()
        logger.info("Cliente conectado ao /ws")
        try:
            while True:
                data = await websocket.receive_json()
                tipo = data.get("type")
                if tipo == "command_text":
                    resposta = engine.handle_text(data.get("text", ""))
                    await websocket.send_json(ArisSaid(text=resposta).model_dump())
                elif tipo == "start_voice":
                    if voice:
                        voice.start()
                        await websocket.send_json({"type": "state", "state": "starting"})
                    else:
                        await websocket.send_json({"type": "state", "state": "voice_unavailable"})
                elif tipo == "stop_voice":
                    if voice:
                        voice.stop()
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            logger.info("Cliente desconectado do /ws")

    return app


app = create_app()
