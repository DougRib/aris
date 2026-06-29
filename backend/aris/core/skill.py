"""Skill — o contrato que toda habilidade do ARIS implementa.

Substitui a cadeia if/elif do antigo CommandProcessor: cada habilidade vira
uma classe isolada que diz se reconhece o texto (matches) e o executa (handle).
"""

from typing import Protocol, runtime_checkable

from aris.core.context import Context


@runtime_checkable
class Skill(Protocol):
    """Toda skill tem um nome e sabe reconhecer e tratar um comando."""

    name: str

    def matches(self, text: str, ctx: Context) -> bool:
        """Retorna True se esta skill deve tratar o texto."""
        ...

    def handle(self, text: str, ctx: Context) -> str:
        """Executa a ação e retorna a resposta falada ao usuário."""
        ...
