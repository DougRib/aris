"""Skill de volume — aumenta/diminui o volume do sistema ou do YouTube.

Interpreta direção (aumentar/diminuir) e alvo (sistema ou navegador/YouTube)
e delega ao VolumeService.
"""

import unicodedata

from aris.core.context import Context
from aris.services.volume import VolumeService

_SUBIR = ("aumentar", "subir", "mais")
_DESCER = ("baixar", "diminuir", "reduzir", "menos")


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


class VolumeSkill:
    """Controle de volume do sistema e do YouTube por voz/texto."""

    name = "volume"

    def __init__(self, service: VolumeService) -> None:
        self._service = service

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece comandos de volume (sistema ou YouTube)."""
        t = _normalizar(text)
        tem_direcao = any(w in t for w in _SUBIR + _DESCER)
        eh_youtube = "youtube" in t or "you tube" in t
        return "volume" in t or (eh_youtube and tem_direcao)

    def handle(self, text: str, ctx: Context) -> str:
        """Ajusta o volume conforme direção e alvo do comando."""
        t = _normalizar(text)
        subir = any(w in t for w in _SUBIR)
        descer = any(w in t for w in _DESCER)
        if not (subir or descer):
            return "Deseja aumentar ou diminuir o volume, senhor?"

        eh_youtube = "youtube" in t or "you tube" in t
        if eh_youtube:
            return self._service.aumentar_youtube() if subir else self._service.diminuir_youtube()
        return self._service.aumentar() if subir else self._service.diminuir()
