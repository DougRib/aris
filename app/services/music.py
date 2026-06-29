"""Music and playlists service."""

import unicodedata
import webbrowser

from loguru import logger

from app.config import Config


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return " ".join(texto.split())


class MusicService:
    """Serviço de música/playlists"""

    @staticmethod
    def tocar_playlist(nome: str) -> str:
        """Abre playlist no navegador"""
        try:
            nome_normalizado = _normalizar(nome)
            mapa = {_normalizar(k): k for k in Config.PLAYLISTS.keys()}
            chave = mapa.get(nome_normalizado)
            if chave:
                webbrowser.open(Config.PLAYLISTS[chave])
                logger.info(f"Playlist '{chave}' aberta")
                return f"Tocando a playlist de {chave}, senhor."

            return (
                f"Não encontrei a playlist '{nome}'. Disponíveis: "
                f"{', '.join(Config.PLAYLISTS.keys())}"
            )
        except Exception as e:
            logger.error(f"Erro ao tocar playlist: {e}")
            return "Ocorreu um erro ao abrir a playlist, senhor."
