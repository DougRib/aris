"""Provider de LLM usando Google Gemini via o SDK unificado `google-genai`.

Substitui o pacote legado `google-generativeai` (descontinuado pelo Google).
Cada chamada é stateless: o Orchestrator já monta o prompt completo
(persona + perfil + memória/RAG + histórico), então não mantemos sessão de chat.
"""

from google import genai
from loguru import logger

from aris.core.context import Context


class GeminiProvider:
    """Raciocínio via Gemini (Google AI Studio / Gemini Developer API)."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._model = model
        # Sem chave, o provider fica inerte (responde com aviso) em vez de quebrar.
        self._client = genai.Client(api_key=api_key) if api_key else None

    def generate(self, prompt: str, ctx: Context) -> str:
        """Gera a resposta do ARIS para o prompt fornecido."""
        if self._client is None:
            return "Serviço de IA não configurado. Defina GEMINI_KEY no .env, senhor."
        try:
            resp = self._client.models.generate_content(model=self._model, contents=prompt)
            return (resp.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro Gemini: {exc}")
            return "Desculpe, não consegui processar sua pergunta no momento."
