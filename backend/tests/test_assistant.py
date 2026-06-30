"""Testa o AssistantEngine ponta-a-ponta (skill real + memória)."""

from aris.assistant import build_engine
from aris.config import Settings


def test_engine_responde_datetime(tmp_path):
    settings = Settings(
        _env_file=None,
        arquivo_memoria=tmp_path / "mem.json",
        profile_file=tmp_path / "profile.json",
        ollama_base_url="http://127.0.0.1:1",  # inacessível: desabilita memória vetorial no teste
    )
    engine = build_engine(settings)
    resposta = engine.handle_text("que horas são")
    assert "senhor" in resposta.lower()


def test_engine_registra_na_memoria(tmp_path):
    settings = Settings(
        _env_file=None,
        arquivo_memoria=tmp_path / "mem.json",
        profile_file=tmp_path / "profile.json",
        ollama_base_url="http://127.0.0.1:1",  # inacessível: desabilita memória vetorial no teste
    )
    engine = build_engine(settings)
    engine.handle_text("que horas são")
    assert "que horas" in engine.memory.as_prompt_context().lower()
