"""AgenteGemini — LLM com function calling (uso automático de ferramentas).

Mantém a interface LLMProvider (`generate`), então entra no lugar do
GeminiProvider simples no Orchestrator (drop-in). A diferença: além de responder,
o Gemini pode decidir CHAMAR as ferramentas da ToolBox por conta própria; o SDK
executa a função e devolve a resposta final já com o resultado embutido.
"""

from typing import Any

from google import genai
from google.genai import types
from loguru import logger

from aris.core.context import Context


class GeminiAgent:
    """Gemini com ferramentas: responde e/ou chama funções reais."""

    def __init__(self, api_key: str, model: str, tools: list[Any]) -> None:
        self._model = model
        self._tools = tools
        self._client = genai.Client(api_key=api_key) if api_key else None

    def generate(self, prompt: str, ctx: Context) -> str:
        """Gera a resposta; o modelo pode chamar ferramentas automaticamente."""
        if self._client is None:
            return "Serviço de IA não configurado. Defina GEMINI_KEY no .env, senhor."
        try:
            resp = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                # tools = funções Python; o SDK faz o "automatic function calling".
                # A system_instruction deixa claro que ele TAMBÉM responde perguntas
                # gerais — sem isso, o modelo se prende às ferramentas e recusa o resto.
                config=types.GenerateContentConfig(
                    tools=self._tools,
                    system_instruction=(
                        "Você é o ÁRIS, assistente pessoal em português. Responda "
                        "normalmente usando seu conhecimento geral e converse. Quando "
                        "ajudar, use as ferramentas disponíveis (clima, data/hora). "
                        "NUNCA diga que só sabe usar ferramentas — você também responde "
                        "perguntas gerais. Trate o usuário por 'senhor' e seja conciso."
                    ),
                ),
            )
            return (resp.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro Gemini (agente): {exc}")
            return "Desculpe, não consegui processar sua pergunta no momento."
