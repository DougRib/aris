"""Testa o carregamento de configuração tipada."""

from aris.config import Settings


def test_settings_defaults():
    s = Settings(_env_file=None)
    assert s.aris_llm_provider == "gemini"
    assert s.ollama_base_url == "http://localhost:11434"
    assert s.cidade_padrao == "São Paulo"
    assert s.max_memoria == 20


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("ARIS_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("GEMINI_KEY", "abc123")
    s = Settings(_env_file=None)
    assert s.aris_llm_provider == "ollama"
    assert s.gemini_key == "abc123"
