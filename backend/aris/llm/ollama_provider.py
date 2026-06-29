"""Provider de LLM usando um modelo local via Ollama (http://localhost:11434)."""

import requests
from loguru import logger

from aris.core.context import Context


class OllamaProvider:
    """Raciocínio via Ollama local, sem custo nem dependência de nuvem."""

    def __init__(self, base_url: str, model: str) -> None:
        self._url = base_url.rstrip("/") + "/api/generate"
        self._model = model

    def generate(self, prompt: str, ctx: Context) -> str:
        """Chama a API do Ollama e retorna o texto gerado."""
        try:
            resp = requests.post(
                self._url,
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["response"].strip()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro Ollama: {exc}")
            return "Desculpe, o modelo local não respondeu, senhor."
