"""Orchestrator — o decisor central do ARIS.

Recebe o texto do comando, pergunta ao Registry se alguma skill o reconhece;
se sim, executa a skill; se não, delega ao LLM com a memória recente injetada.
É o substituto desacoplado do antigo CommandProcessor.
"""

from loguru import logger

from aris.core.context import Context
from aris.core.registry import Registry
from aris.llm.base import PERSONA, LLMProvider, build_prompt
from aris.memory.long_term import LongTermMemory
from aris.memory.profile import UserProfile
from aris.memory.short_term import ShortTermMemory


class Orchestrator:
    """Roteia cada comando para uma skill ou para o motor de raciocínio.

    No caminho do LLM, enriquece o prompt com o perfil do usuário e as memórias
    de longo prazo relevantes (RAG), além do histórico recente.
    """

    def __init__(
        self,
        registry: Registry,
        llm: LLMProvider,
        memory: ShortTermMemory,
        long_term: LongTermMemory | None = None,
        profile: UserProfile | None = None,
        recall_k: int = 3,
    ) -> None:
        self._registry = registry
        self._llm = llm
        self._memory = memory
        self._long_term = long_term
        self._profile = profile
        self._recall_k = recall_k

    def process(self, text: str, ctx: Context) -> str:
        """Processa um comando e retorna a resposta do ARIS."""
        skill = self._registry.resolve(text, ctx)
        if skill is not None:
            try:
                return skill.handle(text, ctx)
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Erro na skill '{skill.name}': {exc}")
                return "Desculpe, ocorreu um erro ao processar seu comando, senhor."

        recall_ctx = ""
        if self._long_term is not None:
            recall_ctx = "\n".join(self._long_term.recall(text, self._recall_k))
        profile_ctx = self._profile.as_prompt_context() if self._profile is not None else ""
        prompt = build_prompt(
            PERSONA,
            self._memory.as_prompt_context(),
            text,
            profile_context=profile_ctx,
            recall_context=recall_ctx,
        )
        return self._llm.generate(prompt, ctx)
