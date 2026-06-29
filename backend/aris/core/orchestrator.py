"""Orchestrator — o decisor central do ARIS.

Recebe o texto do comando, pergunta ao Registry se alguma skill o reconhece;
se sim, executa a skill; se não, delega ao LLM com a memória recente injetada.
É o substituto desacoplado do antigo CommandProcessor.
"""

from loguru import logger

from aris.core.context import Context
from aris.core.registry import Registry
from aris.llm.base import PERSONA, LLMProvider, build_prompt
from aris.memory.short_term import ShortTermMemory


class Orchestrator:
    """Roteia cada comando para uma skill ou para o motor de raciocínio."""

    def __init__(self, registry: Registry, llm: LLMProvider, memory: ShortTermMemory) -> None:
        self._registry = registry
        self._llm = llm
        self._memory = memory

    def process(self, text: str, ctx: Context) -> str:
        """Processa um comando e retorna a resposta do ARIS."""
        skill = self._registry.resolve(text, ctx)
        if skill is not None:
            try:
                return skill.handle(text, ctx)
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Erro na skill '{skill.name}': {exc}")
                return "Desculpe, ocorreu um erro ao processar seu comando, senhor."

        prompt = build_prompt(PERSONA, self._memory.as_prompt_context(), text)
        return self._llm.generate(prompt, ctx)
