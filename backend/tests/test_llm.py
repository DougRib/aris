"""Testa a montagem do prompt e o provider Ollama (HTTP mockado)."""

from aris.core.context import Context
from aris.llm.base import build_prompt
from aris.llm.ollama_provider import OllamaProvider


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


def test_build_prompt_inclui_memoria_quando_existe():
    prompt = build_prompt("PERSONA", "memoria recente", "que horas sao")
    assert "PERSONA" in prompt
    assert "memoria recente" in prompt
    assert "que horas sao" in prompt


def test_build_prompt_omite_memoria_quando_vazia():
    prompt = build_prompt("PERSONA", "", "ola")
    assert "Histórico" not in prompt


def test_ollama_generate(monkeypatch):
    class _FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"response": "  resposta do modelo  "}

    captured = {}

    def _fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _FakeResp()

    monkeypatch.setattr("aris.llm.ollama_provider.requests.post", _fake_post)
    provider = OllamaProvider("http://localhost:11434", "llama3.1")
    out = provider.generate("meu prompt", _ctx())
    assert out == "resposta do modelo"
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["json"]["model"] == "llama3.1"
    assert captured["json"]["stream"] is False
