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

    # Memória
    max_memoria: int = 20
    arquivo_memoria: Path = BACKEND_DIR / "data" / "memoria.json"


settings = Settings()
