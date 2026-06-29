"""Testa o registro e a resolução de skills por prioridade de ordem."""

from dataclasses import dataclass

from aris.core.context import Context
from aris.core.registry import Registry


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


@dataclass
class _FakeSkill:
    name: str
    keyword: str

    def matches(self, text: str, ctx: Context) -> bool:
        return self.keyword in text

    def handle(self, text: str, ctx: Context) -> str:
        return f"{self.name} executou"


def test_resolve_returns_matching_skill():
    reg = Registry()
    reg.register(_FakeSkill("clima", "tempo"))
    assert reg.resolve("como esta o tempo", _ctx()).name == "clima"


def test_resolve_respects_registration_order():
    reg = Registry()
    reg.register(_FakeSkill("primeira", "abrir"))
    reg.register(_FakeSkill("segunda", "abrir"))
    assert reg.resolve("abrir algo", _ctx()).name == "primeira"


def test_resolve_returns_none_when_no_match():
    reg = Registry()
    reg.register(_FakeSkill("clima", "tempo"))
    assert reg.resolve("qualquer coisa", _ctx()) is None
