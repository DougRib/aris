"""Testa o roteamento do Orchestrator entre skills e LLM."""

from dataclasses import dataclass

from aris.core.context import Context
from aris.core.orchestrator import Orchestrator
from aris.core.registry import Registry


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


class _FakeLLM:
    def __init__(self) -> None:
        self.last_prompt = ""

    def generate(self, prompt: str, ctx: Context) -> str:
        self.last_prompt = prompt
        return "resposta-llm"


class _FakeMemory:
    def as_prompt_context(self) -> str:
        return "memoria-x"


@dataclass
class _OkSkill:
    name: str = "ok"

    def matches(self, text: str, ctx: Context) -> bool:
        return "ping" in text

    def handle(self, text: str, ctx: Context) -> str:
        return "pong"


@dataclass
class _BrokenSkill:
    name: str = "broken"

    def matches(self, text: str, ctx: Context) -> bool:
        return "quebra" in text

    def handle(self, text: str, ctx: Context) -> str:
        raise RuntimeError("falhou")


def test_roteia_para_skill():
    reg = Registry()
    reg.register(_OkSkill())
    orch = Orchestrator(reg, _FakeLLM(), _FakeMemory())
    assert orch.process("manda um ping", _ctx()) == "pong"


def test_cai_no_llm_com_memoria_injetada():
    reg = Registry()
    llm = _FakeLLM()
    orch = Orchestrator(reg, llm, _FakeMemory())
    out = orch.process("fale sobre python", _ctx())
    assert out == "resposta-llm"
    assert "memoria-x" in llm.last_prompt
    assert "fale sobre python" in llm.last_prompt


def test_excecao_de_skill_nao_propaga():
    reg = Registry()
    reg.register(_BrokenSkill())
    orch = Orchestrator(reg, _FakeLLM(), _FakeMemory())
    out = orch.process("quebra isso", _ctx())
    assert "erro" in out.lower()
