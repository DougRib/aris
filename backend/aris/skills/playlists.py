"""Skill de playlists — abre uma playlist do YouTube no navegador padrão.

Reconhece o nome da playlist (música/estudo/treino) no próprio comando; se não
houver, pergunta por voz. Roda no backend local, que é dono do navegador.
"""

import unicodedata
import webbrowser

from aris.core.context import Context


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


class PlaylistsSkill:
    """Toca uma das playlists configuradas abrindo a URL no navegador."""

    name = "playlists"

    def __init__(self, playlists: dict[str, str]) -> None:
        self._playlists = playlists

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece pedidos de playlist ou de tocar música."""
        t = _normalizar(text)
        return "playlist" in t or "tocar musica" in t

    def handle(self, text: str, ctx: Context) -> str:
        """Abre a playlist citada (ou perguntada) no navegador."""
        chave = self._chave_no_texto(text)
        if not chave:
            ctx.speak("Qual playlist, senhor? Música, estudo ou treino?")
            chave = self._chave_no_texto(ctx.listen() or "")
        if not chave:
            return "Não entendi qual playlist, senhor."
        webbrowser.open(self._playlists[chave])
        return f"Tocando a playlist de {chave}, senhor."

    def _chave_no_texto(self, texto: str) -> str:
        """Retorna a chave da playlist mencionada no texto, ou ''."""
        t = _normalizar(texto)
        for chave in self._playlists:
            if _normalizar(chave) in t:
                return chave
        return ""
