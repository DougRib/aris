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
from aris.services.volume import VolumeService
from aris.services.weather import WeatherService
from aris.skills.apps import AppsSkill
from aris.skills.datetime_skill import DateTimeSkill
from aris.skills.memory_skill import MemorySkill
from aris.skills.notes import NotesSkill
from aris.skills.playlists import PlaylistsSkill
from aris.skills.volume import VolumeSkill
from aris.skills.weather import WeatherSkill


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
    memory = ShortTermMemory(max_items=settings.max_memoria, arquivo=settings.arquivo_memoria)

    registry = Registry()
    registry.register(DateTimeSkill())
    registry.register(WeatherSkill(WeatherService(settings.openweather_key), settings.cidade_padrao))
    registry.register(PlaylistsSkill(settings.playlists))
    registry.register(NotesSkill(settings.arquivo_notas))
    registry.register(MemorySkill(memory))
    registry.register(
        AppsSkill(settings.word_path, settings.instagram_handle, settings.facebook_profile)
    )
    registry.register(VolumeSkill(VolumeService(settings.youtube_volume_apps)))

    llm = build_provider(settings)
    orchestrator = Orchestrator(registry, llm, memory)
    logger.info(f"AssistantEngine pronto (LLM: {settings.aris_llm_provider})")
    return AssistantEngine(orchestrator, memory)
