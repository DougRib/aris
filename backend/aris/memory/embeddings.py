"""Cálculo de embeddings via Ollama (local), para a memória vetorial.

Gera vetores com o modelo nomic-embed-text (padrão), sem custo nem nuvem. É um
callable simples: recebe uma lista de textos e devolve uma lista de vetores. A
integração com o ChromaDB passa esses vetores explicitamente, então não
dependemos da interface (volátil) de embedding function do Chroma.
"""

import requests


class OllamaEmbeddings:
    """Gera embeddings chamando o endpoint /api/embeddings do Ollama."""

    def __init__(self, base_url: str, model: str) -> None:
        self._url = base_url.rstrip("/") + "/api/embeddings"
        self._model = model

    def __call__(self, textos: list[str]) -> list[list[float]]:
        """Retorna um vetor por texto de entrada."""
        vetores: list[list[float]] = []
        for texto in textos:
            resp = requests.post(
                self._url, json={"model": self._model, "prompt": texto}, timeout=60
            )
            resp.raise_for_status()
            vetores.append(resp.json()["embedding"])
        return vetores
