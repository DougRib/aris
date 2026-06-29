"""Testa a skill de hora/data."""

from aris.core.context import Context
from aris.skills.datetime_skill import DateTimeSkill


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


def test_reconhece_hora():
    skill = DateTimeSkill()
    assert skill.matches("que horas são", _ctx())
    assert skill.matches("que dia é hoje", _ctx())
    assert not skill.matches("abrir navegador", _ctx())


def test_responde_hora():
    skill = DateTimeSkill()
    resposta = skill.handle("que horas são", _ctx())
    assert "senhor" in resposta.lower()
