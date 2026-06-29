"""Configuração central do ARIS, carregada de variáveis de ambiente (.env).

Substitui a antiga classe Config baseada em os.getenv por pydantic-settings,
que valida tipos e centraliza os valores padrão num único lugar.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py vive em backend/aris/ → BACKEND_DIR = backend/, ROOT_DIR = raiz do repo.
# Há UM único .env, na raiz do repositório (com as secrets), compartilhado pelo backend.
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Todas as configurações do ARIS. Nomes de campo casam com env vars (case-insensitive)."""

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    # APIs externas
    gemini_key: str = ""
    openweather_key: str = ""

    # Motor de raciocínio (LLM)
    aris_llm_provider: str = "gemini"  # "gemini" | "ollama"
    gemini_model: str = "gemini-2.5-flash"  # model id do Gemini (ver genai.list_models)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Localização
    cidade_padrao: str = "São Paulo"

    # Abrir apps / redes sociais
    word_path: str = ""  # caminho do WINWORD.EXE, se a detecção automática falhar
    instagram_handle: str = ""
    facebook_profile: str = ""

    # Volume por-app (navegadores onde o YouTube toca)
    youtube_volume_apps: str = (
        "msedge.exe,msedgewebview2.exe,chrome.exe,brave.exe,opera.exe,firefox.exe"
    )

    # Voz — reconhecimento (STT)
    idioma_stt: str = "pt-BR"

    # Voz — síntese (TTS)
    tts_engine: str = "edge"  # "edge" | "pyttsx3"
    edge_tts_voice: str = "pt-BR-AntonioNeural"
    edge_tts_rate: str = "+0%"
    edge_tts_pitch: str = "+0Hz"
    edge_tts_volume: str = "+0%"
    # Eco/reverb opcional (0 = desligado)
    edge_tts_echo_delay_ms: int = 0
    edge_tts_echo_volume: int = 0
    edge_tts_echo2_delay_ms: int = 0
    edge_tts_echo2_volume: int = 0

    # Memória e notas
    max_memoria: int = 20
    arquivo_memoria: Path = BACKEND_DIR / "data" / "memoria.json"
    arquivo_notas: Path = BACKEND_DIR / "data" / "notas_aris.txt"

    # Playlists (YouTube) — abertas no navegador padrão
    playlist_musica: str = (
        "https://www.youtube.com/watch?v=RRzGr6m2Gh0&list=PLn9Vm_vd7552r94ALUQNsetqWwkDfIDLN"
    )
    playlist_estudo: str = "https://www.youtube.com/watch?v=Hs5C8x6Z6VQ"
    playlist_treino: str = "https://www.youtube.com/watch?v=jfKfPfyJRdk"

    @property
    def playlists(self) -> dict[str, str]:
        """Mapa nome→URL das playlists disponíveis."""
        return {
            "musica": self.playlist_musica,
            "estudo": self.playlist_estudo,
            "treino": self.playlist_treino,
        }


settings = Settings()
