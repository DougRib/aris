"""Gateway WebSocket: ponto único onde clientes conversam com o AssistantEngine."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger

from aris.api.events import ArisSaid
from aris.assistant import AssistantEngine, build_engine
from aris.config import settings


def create_app(engine: AssistantEngine | None = None) -> FastAPI:
    """Cria a app FastAPI. Aceita um engine injetado (útil em testes)."""
    app = FastAPI(title="ARIS", version="0.1.0")
    app.state.engine = engine or build_engine(settings)

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        logger.info("Cliente conectado ao /ws")
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "command_text":
                    resposta = app.state.engine.handle_text(data.get("text", ""))
                    await websocket.send_json(ArisSaid(text=resposta).model_dump())
        except WebSocketDisconnect:
            logger.info("Cliente desconectado do /ws")

    return app


app = create_app()
