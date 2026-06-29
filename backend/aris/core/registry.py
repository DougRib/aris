"""Registry — guarda as skills e resolve qual trata cada comando.

A ordem de registro define a prioridade: a primeira skill cujo matches()
retorna True vence. Skills mais específicas devem ser registradas antes.
"""

from aris.core.context import Context
from aris.core.skill import Skill


class Registry:
    """Coleção ordenada de skills com resolução por prioridade."""

    def __init__(self) -> None:
        self._skills: list[Skill] = []

    def register(self, skill: Skill) -> None:
        """Adiciona uma skill ao fim da lista (menor prioridade que as anteriores)."""
        self._skills.append(skill)

    def resolve(self, text: str, ctx: Context) -> Skill | None:
        """Retorna a primeira skill que reconhece o texto, ou None."""
        for skill in self._skills:
            if skill.matches(text, ctx):
                return skill
        return None
