"""Skill de memória — resumo do histórico e liga/desliga o modo privado.

Opera sobre a ShortTermMemory compartilhada: "histórico"/"resumo" devolvem as
últimas interações; "ativar/desativar modo privado" alternam a gravação.
"""

import unicodedata

from aris.core.context import Context
from aris.memory.short_term import ShortTermMemory


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


class MemorySkill:
    """Resumo de memória e controle do modo privado."""

    name = "memory"

    def __init__(self, memory: ShortTermMemory) -> None:
        self._memory = memory

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece pedidos de histórico/resumo ou de modo privado."""
        t = _normalizar(text)
        return "modo privado" in t or any(
            g in t for g in ("historico", "resumo", "o que falamos")
        )

    def handle(self, text: str, ctx: Context) -> str:
        """Alterna modo privado ou devolve o resumo do histórico."""
        t = _normalizar(text)
        if "modo privado" in t:
            if "desativar" in t:
                self._memory.private_mode = False
                return "Modo privado desativado. Voltarei a registrar suas interações, senhor."
            self._memory.private_mode = True
            return "Modo privado ativado. Não irei registrar histórico nem anotações, senhor."
        return self._memory.obter_resumo()
