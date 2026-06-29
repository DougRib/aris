"""Contrato comum dos providers de LLM e a montagem do prompt da persona.

A persona do ÁRIS fica centralizada aqui (antes estava espalhada em strings),
e build_prompt injeta a memória de curto prazo no contexto do modelo.
"""

from typing import Protocol

from aris.core.context import Context

PERSONA = (
    "Você é o ÁRIS, assistente de IA pessoal avançado.\n"
    "- Seja direto, educado e profissional.\n"
    "- Use no máximo 40 palavras.\n"
    '- Trate o usuário por "senhor".\n'
    "- Se não souber, admita."
)


class LLMProvider(Protocol):
    """Qualquer motor de raciocínio que gere texto a partir de um prompt."""

    def generate(self, prompt: str, ctx: Context) -> str:
        """Gera a resposta do ARIS para o prompt fornecido."""
        ...


def build_prompt(persona: str, memory_context: str, question: str) -> str:
    """Monta o prompt final: persona + (histórico, se houver) + pergunta."""
    parts = [persona]
    if memory_context:
        parts.append(f"Histórico recente:\n{memory_context}")
    parts.append(f"Pergunta: {question}")
    return "\n\n".join(parts)
