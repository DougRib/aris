"""AssistantEngine — liga núcleo, memória, LLM e skills num motor headless.

Este é o "cérebro" sem UI. Clientes (WebSocket, voz, futuramente câmera) chamam
handle_text() e recebem a resposta do ARIS. build_engine() faz a montagem
(composition root) registrando todas as skills disponíveis.
"""

from loguru import logger

from aris.config import Settings
from aris.core.context import Context
from aris.core.orchestrator import Orchestrator
from aris.core.registry import Registry
from aris.llm.factory import build_provider
from aris.memory.short_term import ShortTermMemory
from aris.skills.datetime_skill import DateTimeSkill


class AssistantEngine:
    """Motor headless: recebe texto, processa e devolve a resposta do ARIS."""

    def __init__(self, orchestrator: Orchestrator, memory: ShortTermMemory) -> None:
        self._orchestrator = orchestrator
        self.memory = memory

    def handle_text(self, text: str) -> str:
        """Processa um comando em texto e registra a interação na memória."""
        # Em Fase 0 sem voz, speak/listen são no-ops; skills de diálogo entram no Plano 2.
        ctx = Context(speak=lambda _t: None, listen=lambda **_k: "")
        ctx.private_mode = self.memory.private_mode
        resposta = self._orchestrator.process(text, ctx)
        self.memory.registrar(text, resposta)
        return resposta


def build_engine(settings: Settings) -> AssistantEngine:
    """Composition root: monta o motor com skills registradas por prioridade."""
    registry = Registry()
    registry.register(DateTimeSkill())
    # Plano 2 registra aqui: apps, volume, weather, playlists, notes, memory_skill.

    memory = ShortTermMemory(max_items=settings.max_memoria, arquivo=settings.arquivo_memoria)
    llm = build_provider(settings)
    orchestrator = Orchestrator(registry, llm, memory)
    logger.info(f"AssistantEngine pronto (LLM: {settings.aris_llm_provider})")
    return AssistantEngine(orchestrator, memory)
