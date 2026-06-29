"""Notes management."""

from datetime import datetime

from loguru import logger

from app.config import Config
from app.managers.memory import MemoryManager


class NotesManager:
    """Gerenciador de notas"""

    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager

    def registrar_nota(self, texto: str) -> str:
        """Registra uma nova nota"""
        if self.memory.modo_privado:
            return "Modo privado ativo, não vou registrar essa anotação, senhor."

        try:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            linha = f"[{timestamp}] {texto}\n"

            with open(Config.ARQUIVO_NOTAS, "a", encoding="utf-8") as f:
                f.write(linha)

            logger.info(f"Nota registrada: {texto[:50]}...")
            return "Anotação registrada com sucesso, senhor."
        except Exception as e:
            logger.error(f"Erro ao registrar nota: {e}")
            return f"Desculpe, ocorreu um erro ao registrar a nota: {str(e)}"
