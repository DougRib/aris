"""Testa a skill de memória/modo privado."""

from aris.core.context import Context
from aris.memory.short_term import ShortTermMemory
from aris.skills.memory_skill import MemorySkill


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


def _mem(tmp_path) -> ShortTermMemory:
    return ShortTermMemory(max_items=5, arquivo=tmp_path / "mem.json")


def test_matches(tmp_path):
    skill = MemorySkill(_mem(tmp_path))
    assert skill.matches("me dá um resumo", _ctx())
    assert skill.matches("ativar modo privado", _ctx())
    assert not skill.matches("que horas são", _ctx())


def test_ativa_e_desativa_modo_privado(tmp_path):
    mem = _mem(tmp_path)
    skill = MemorySkill(mem)
    out = skill.handle("ativar modo privado", _ctx())
    assert mem.private_mode is True
    assert "ativado" in out.lower()
    out = skill.handle("desativar modo privado", _ctx())
    assert mem.private_mode is False
    assert "desativado" in out.lower()


def test_resumo_vazio(tmp_path):
    skill = MemorySkill(_mem(tmp_path))
    assert "registros recentes" in skill.handle("histórico", _ctx())


def test_resumo_com_conteudo(tmp_path):
    mem = _mem(tmp_path)
    mem.registrar("oi", "olá senhor")
    skill = MemorySkill(mem)
    out = skill.handle("o que falamos", _ctx())
    assert "oi" in out
