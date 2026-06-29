"""Memory management with persistence."""

import json
from collections import deque
from datetime import datetime
from threading import Lock

from loguru import logger

from app.config import Config


class MemoryManager:
    """Gerenciador de memória com persistência"""

    def __init__(self):
        self.memoria = deque(maxlen=Config.MAX_MEMORIA)
        self.modo_privado = False
        self.lock = Lock()
        self.carregar_memoria()

    def registrar(self, entrada: str, resposta: str):
        """Registra interação na memória"""
        if self.modo_privado:
            return

        with self.lock:
            item = {
                "timestamp": datetime.now().isoformat(),
                "hora": datetime.now().strftime("%H:%M"),
                "entrada": entrada,
                "resposta": resposta,
            }
            self.memoria.append(item)
            logger.debug(f"Memória registrada: {entrada[:50]}...")

    def obter_resumo(self) -> str:
        """Retorna resumo das interações"""
        with self.lock:
            if not self.memoria:
                return "Ainda não tenho registros recentes, senhor."

            linhas = []
            for m in self.memoria:
                linhas.append(
                    f"[{m['hora']}] Você: {m['entrada']}\n           Eu: {m['resposta']}"
                )

            return "Aqui está um resumo das nossas últimas interações:\n" + "\n".join(
                linhas
            )

    def ativar_modo_privado(self) -> str:
        """Ativa modo privado"""
        self.modo_privado = True
        logger.info("Modo privado ativado")
        return "Modo privado ativado. Não irei registrar histórico nem anotações."

    def desativar_modo_privado(self) -> str:
        """Desativa modo privado"""
        self.modo_privado = False
        logger.info("Modo privado desativado")
        return "Modo privado desativado. Voltarei a registrar suas interações."

    def salvar_memoria(self):
        """Salva memória em arquivo JSON"""
        if self.modo_privado:
            return

        try:
            with self.lock:
                dados = {
                    "ultima_atualizacao": datetime.now().isoformat(),
                    "memoria": list(self.memoria),
                }
                with open(Config.ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
                    json.dump(dados, f, ensure_ascii=False, indent=2)
                logger.debug("Memória salva em arquivo")
        except Exception as e:
            logger.error(f"Erro ao salvar memória: {e}")

    def carregar_memoria(self):
        """Carrega memória do arquivo"""
        try:
            if Config.ARQUIVO_MEMORIA.exists():
                with open(Config.ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.memoria = deque(
                        dados.get("memoria", []), maxlen=Config.MAX_MEMORIA
                    )
                logger.info(f"Memória carregada: {len(self.memoria)} itens")
        except Exception as e:
            logger.error(f"Erro ao carregar memória: {e}")
