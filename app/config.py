"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Classe para gerenciar configurações"""

    OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")
    GEMINI_KEY = os.getenv("GEMINI_KEY", "")
    CIDADE_PADRAO = os.getenv("CIDADE_PADRAO", "São Paulo")

    TTS_ENGINE = os.getenv("TTS_ENGINE", "edge")
    EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "pt-BR-AntonioNeural")
    EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "+0%")
    EDGE_TTS_PITCH = os.getenv("EDGE_TTS_PITCH", "+0Hz")
    EDGE_TTS_VOLUME = os.getenv("EDGE_TTS_VOLUME", "+0%")
    EDGE_TTS_ECHO_DELAY_MS = int(os.getenv("EDGE_TTS_ECHO_DELAY_MS", "0") or 0)
    EDGE_TTS_ECHO_VOLUME = int(os.getenv("EDGE_TTS_ECHO_VOLUME", "0") or 0)
    EDGE_TTS_ECHO2_DELAY_MS = int(os.getenv("EDGE_TTS_ECHO2_DELAY_MS", "0") or 0)
    EDGE_TTS_ECHO2_VOLUME = int(os.getenv("EDGE_TTS_ECHO2_VOLUME", "0") or 0)
    YOUTUBE_VOLUME_APPS = os.getenv(
        "YOUTUBE_VOLUME_APPS",
        "msedge.exe,msedgewebview2.exe,chrome.exe,brave.exe,opera.exe,firefox.exe",
    )
    INSTAGRAM_HANDLE = os.getenv("INSTAGRAM_HANDLE", "odev.douglas")
    INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID", "Facebook.InstagramBeta_8xx8rvfyw5nnt!App")
    FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "Facebook.Facebook_8xx8rvfyw5nnt!App")
    FACEBOOK_PROFILE = os.getenv("FACEBOOK_PROFILE", "")
    WORD_PATH = os.getenv("WORD_PATH", "")

    PLAYLISTS = {
        "musica": os.getenv("PLAYLIST_MUSICA", "https://www.youtube.com/watch?v=RRzGr6m2Gh0&list=PLn9Vm_vd7552r94ALUQNsetqWwkDfIDLN"),
        "estudo": os.getenv("PLAYLIST_ESTUDO", "https://www.youtube.com/watch?v=Hs5C8x6Z6VQ"),
        "treino": os.getenv("PLAYLIST_TREINO", "https://www.youtube.com/watch?v=jfKfPfyJRdk"),
    }

    ARQUIVO_NOTAS = BASE_DIR / "data/notas_aris.txt"
    ARQUIVO_MEMORIA = BASE_DIR / "data/memoria.json"
    MAX_MEMORIA = 20

    @classmethod
    def validar(cls):
        """Valida configurações necessárias"""
        erros = []
        if not cls.OPENWEATHER_KEY:
            erros.append("OPENWEATHER_KEY não configurada")
            logger.warning(
                "OpenWeather API key não encontrada - funcionalidade de clima desabilitada"
            )
        if not cls.GEMINI_KEY:
            erros.append("GEMINI_KEY não configurada")
            logger.warning("Gemini API key não encontrada - pesquisas IA desabilitadas")

        cls.ARQUIVO_NOTAS.parent.mkdir(parents=True, exist_ok=True)
        cls.ARQUIVO_MEMORIA.parent.mkdir(parents=True, exist_ok=True)

        return erros
