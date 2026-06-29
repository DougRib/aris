"""Fábrica que escolhe o provider de LLM conforme a configuração."""

from aris.config import Settings
from aris.llm.base import LLMProvider
from aris.llm.gemini_provider import GeminiProvider
from aris.llm.ollama_provider import OllamaProvider


def build_provider(settings: Settings) -> LLMProvider:
    """Retorna GeminiProvider ou OllamaProvider conforme settings.aris_llm_provider."""
    if settings.aris_llm_provider == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    return GeminiProvider(settings.gemini_key, settings.gemini_model)
