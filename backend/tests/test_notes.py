"""Testa a skill de notas (arquivo temporário)."""

from aris.core.context import Context
from aris.skills.notes import NotesSkill


def _ctx(resposta_voz: str = "", private: bool = False) -> Context:
    ctx = Context(speak=lambda _t: None, listen=lambda **_k: resposta_voz)
    ctx.private_mode = private
    return ctx


def test_matches():
    skill = NotesSkill("x.txt")
    assert skill.matches("anotar comprar pão", _ctx())
    assert not skill.matches("que horas são", _ctx())


def test_grava_nota_inline(tmp_path):
    arquivo = tmp_path / "notas.txt"
    skill = NotesSkill(arquivo)
    out = skill.handle("anotar comprar pão", _ctx())
    assert "sucesso" in out
    assert "comprar pão" in arquivo.read_text(encoding="utf-8")


def test_modo_privado_nao_grava(tmp_path):
    arquivo = tmp_path / "notas.txt"
    skill = NotesSkill(arquivo)
    out = skill.handle("anotar segredo", _ctx(private=True))
    assert "privado" in out.lower()
    assert not arquivo.exists()


def test_pega_nota_por_voz_quando_sem_inline(tmp_path):
    arquivo = tmp_path / "notas.txt"
    skill = NotesSkill(arquivo)
    skill.handle("anotar", _ctx(resposta_voz="ligar para o médico"))
    assert "ligar para o médico" in arquivo.read_text(encoding="utf-8")
