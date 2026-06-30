"""Testa a skill de perfil (memorizar preferências do usuário)."""

from aris.core.context import Context
from aris.memory.profile import UserProfile
from aris.skills.profile_skill import ProfileSkill


def _ctx(resposta_voz: str = "") -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: resposta_voz)


def test_matches(tmp_path):
    skill = ProfileSkill(UserProfile(tmp_path / "p.json"))
    assert skill.matches("lembre que eu prefiro café às 8h", _ctx())
    assert skill.matches("guarde que eu trabalho com Python", _ctx())
    assert not skill.matches("que horas são", _ctx())


def test_guarda_fato_inline(tmp_path):
    profile = UserProfile(tmp_path / "p.json")
    skill = ProfileSkill(profile)
    out = skill.handle("lembre que eu prefiro café às 8h", _ctx())
    assert "perfil" in out.lower()
    assert "café às 8h" in profile.as_prompt_context()


def test_pega_fato_por_voz(tmp_path):
    profile = UserProfile(tmp_path / "p.json")
    skill = ProfileSkill(profile)
    skill.handle("guarde isso", _ctx(resposta_voz="moro em Lisboa"))
    assert "moro em Lisboa" in profile.as_prompt_context()
