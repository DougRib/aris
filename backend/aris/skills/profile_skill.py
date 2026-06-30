"""Skill de perfil — guarda fatos/preferências do usuário sob comando.

Ex.: "lembre que eu prefiro café às 8h" → fica no perfil e passa a ser injetado
no prompt das respostas do LLM, personalizando o ARIS.
"""

import unicodedata

from aris.core.context import Context
from aris.memory.profile import UserProfile

_GATILHOS = ("lembre-se que", "lembre que", "guarde que", "guarde isso")


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


class ProfileSkill:
    """Registra fatos do usuário no perfil."""

    name = "profile"

    def __init__(self, profile: UserProfile) -> None:
        self._profile = profile

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece pedidos explícitos de memorização de preferências."""
        t = _normalizar(text)
        return any(g in t for g in _GATILHOS)

    def handle(self, text: str, ctx: Context) -> str:
        """Extrai o fato do comando (ou pergunta) e o salva no perfil."""
        fato = self._extrair_fato(text)
        if not fato:
            ctx.speak("O que devo lembrar sobre o senhor?")
            fato = (ctx.listen() or "").strip()
        if not fato:
            return "Não entendi o que devo lembrar, senhor."
        self._profile.set_fact(fato, fato)
        return "Anotado no seu perfil. Vou me lembrar disso, senhor."

    def _extrair_fato(self, text: str) -> str:
        """Pega o texto após o gatilho ('lembre que ...').

        Usa text.lower() (não a versão sem acentos) para os índices baterem com
        o texto original ao fatiar.
        """
        baixo = text.lower()
        for gatilho in _GATILHOS:
            idx = baixo.find(gatilho)
            if idx != -1:
                return text[idx + len(gatilho) :].strip(" :,-")
        return ""
