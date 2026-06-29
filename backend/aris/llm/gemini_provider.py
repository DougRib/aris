"""Provider de LLM usando Google Gemini (nuvem).

Nota: usa o SDK google.generativeai (legado, mantido na Fase 0 por paridade
com o ARIS atual). Migração para google.genai prevista para fase posterior.
"""

import google.generativeai as genai
from loguru import logger

from aris.core.context import Context


class GeminiProvider:
    """Raciocínio via Gemini, mantendo uma sessão de chat por execução."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self._chat = self._model.start_chat(history=[])

    def generate(self, prompt: str, ctx: Context) -> str:
        """Envia o prompt ao Gemini e retorna o texto da resposta."""
        try:
            resposta = self._chat.send_message(prompt)
            return resposta.text
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro Gemini: {exc}")
            return "Desculpe, não consegui processar sua pergunta no momento."
