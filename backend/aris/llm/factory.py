"""Fábrica que escolhe o provider de LLM conforme a configuração.

Para o Gemini, devolve o AgenteGemini (com ferramentas / function calling); para
o Ollama, o provider simples. Ambos expõem `generate`, então são intercambiáveis.
"""

from aris.config import Settings
from aris.llm.base import LLMProvider
from aris.llm.ollama_provider import OllamaProvider


def build_provider(settings: Settings) -> LLMProvider:
    """Retorna o AgenteGemini (com tools) ou o OllamaProvider conforme o .env."""
    if settings.aris_llm_provider == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)

    # Gemini com ferramentas (sub-agente): o modelo pode chamar funções reais.
    from aris.agents.gemini_agent import GeminiAgent
    from aris.agents.tools import ToolBox
    from aris.services.weather import WeatherService

    toolbox = ToolBox(WeatherService(settings.openweather_key))
    return GeminiAgent(settings.gemini_key, settings.gemini_model, toolbox.tools())
