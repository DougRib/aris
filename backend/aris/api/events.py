"""Schemas dos eventos trocados pelo WebSocket entre clientes e o núcleo."""

from pydantic import BaseModel


class CommandText(BaseModel):
    """Comando em texto vindo de um cliente (ex.: input do frontend)."""

    type: str = "command_text"
    text: str


class ArisSaid(BaseModel):
    """Resposta do ARIS enviada de volta ao cliente."""

    type: str = "aris_said"
    text: str
