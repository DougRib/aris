"""Testa a memória de longo prazo com ChromaDB efêmero e embedding fake.

Usa um embedding bag-of-words determinístico (sem Ollama), suficiente para a
busca semântica encontrar o documento que compartilha palavras com a consulta.
Os vetores são passados explicitamente ao Chroma (embedding_function=None).
"""

import uuid

import chromadb

from aris.memory.long_term import LongTermMemory


def _bag_of_words(textos: list[str]) -> list[list[float]]:
    """Embedding fake: conta palavras em baldes fixos (dim 64)."""
    saida = []
    for texto in textos:
        vec = [0.0] * 64
        for palavra in texto.lower().split():
            vec[hash(palavra) % 64] += 1.0
        saida.append(vec)
    return saida


def _mem() -> LongTermMemory:
    client = chromadb.Client()  # efêmero, em memória
    coll = client.create_collection(name=f"mem_{uuid.uuid4().hex}", embedding_function=None)
    return LongTermMemory(coll, _bag_of_words)


def test_remember_e_recall_encontra_documento_relevante():
    m = _mem()
    m.remember("o usuário prefere café às oito horas da manhã")
    m.remember("o gato dorme no sofá da sala o dia inteiro")
    res = m.recall("quando o usuário costuma tomar café", k=1)
    assert res
    assert "café" in res[0]


def test_recall_vazio_quando_sem_dados():
    assert _mem().recall("qualquer coisa") == []


def test_remember_ignora_texto_vazio():
    m = _mem()
    m.remember("   ")
    assert m.recall("café") == []
