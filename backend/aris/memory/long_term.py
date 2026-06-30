"""Memória de longo prazo (vetorial) com ChromaDB.

Guarda interações como embeddings (gerados via Ollama) e recupera as mais
relevantes para a consulta atual (RAG), que o Orchestrator injeta no prompt do
LLM. Os vetores são passados explicitamente ao Chroma — não usamos a embedding
function dele. Degrada com elegância: se Ollama/ChromaDB não estiverem
disponíveis, `build_long_term` devolve None e o assistente segue sem ela.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from loguru import logger

from aris.config import Settings

# Função que transforma textos em vetores (ex.: OllamaEmbeddings).
Embedder = Callable[[list[str]], list[list[float]]]


class LongTermMemory:
    """Coleção vetorial de memórias, com gravação e busca semântica."""

    def __init__(self, collection: Any, embed: Embedder) -> None:
        self._collection = collection
        self._embed = embed

    def remember(self, text: str, metadata: dict[str, str] | None = None) -> None:
        """Indexa um texto na memória de longo prazo."""
        if not text or not text.strip():
            return
        try:
            vetor = self._embed([text])[0]
            kwargs: dict[str, Any] = {
                "ids": [str(uuid.uuid4())],
                "documents": [text],
                "embeddings": [vetor],
            }
            if metadata:
                kwargs["metadatas"] = [metadata]
            self._collection.add(**kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao gravar memória de longo prazo: {exc}")

    def recall(self, query: str, k: int = 3) -> list[str]:
        """Retorna os k textos mais relevantes para a consulta (ou [])."""
        if not query or not query.strip():
            return []
        try:
            vetor = self._embed([query])[0]
            res = self._collection.query(query_embeddings=[vetor], n_results=k)
            docs = res.get("documents") or []
            return list(docs[0]) if docs else []
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao recuperar memória de longo prazo: {exc}")
            return []


def build_long_term(settings: Settings) -> LongTermMemory | None:
    """Monta a memória vetorial (ChromaDB persistente + embeddings Ollama)."""
    # Sem Ollama acessível não há como gerar embeddings: desabilita de forma limpa.
    try:
        import requests

        requests.get(settings.ollama_base_url.rstrip("/") + "/api/tags", timeout=2)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Ollama indisponível ({exc}); memória vetorial desabilitada.")
        return None

    try:
        import chromadb

        from aris.memory.embeddings import OllamaEmbeddings

        client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        # embedding_function=None: fornecemos os vetores explicitamente.
        collection = client.get_or_create_collection("aris_memoria", embedding_function=None)
        embed = OllamaEmbeddings(settings.ollama_base_url, settings.ollama_embed_model)
        logger.info("Memória de longo prazo (ChromaDB) pronta.")
        return LongTermMemory(collection, embed)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Memória vetorial indisponível: {exc}")
        return None
