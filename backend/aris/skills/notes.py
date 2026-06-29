"""Skill de notas — anexa uma anotação com data/hora a um arquivo de texto.

Aceita a nota no próprio comando ("anotar comprar pão") ou, sem ela, pergunta
por voz. Respeita o modo privado: não grava nada quando ctx.private_mode é True.
"""

from datetime import datetime
from pathlib import Path

from loguru import logger

from aris.core.context import Context


class NotesSkill:
    """Registra anotações em data/notas_aris.txt (append-only)."""

    name = "notes"

    def __init__(self, arquivo: Path) -> None:
        self._arquivo = Path(arquivo)

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece pedidos de anotação."""
        t = text.lower()
        return "anotar" in t or "registrar nota" in t

    def handle(self, text: str, ctx: Context) -> str:
        """Grava a anotação, exceto em modo privado."""
        if ctx.private_mode:
            return "Modo privado ativo, não vou registrar essa anotação, senhor."

        nota = self._nota_do_texto(text)
        if not nota:
            ctx.speak("O que deseja anotar, senhor?")
            nota = (ctx.listen() or "").strip()
        if not nota:
            return "Não consegui ouvir o conteúdo da anotação, senhor."

        try:
            self._arquivo.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            with open(self._arquivo, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {nota}\n")
            return "Anotação registrada com sucesso, senhor."
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao registrar nota: {exc}")
            return "Desculpe, ocorreu um erro ao registrar a nota, senhor."

    def _nota_do_texto(self, text: str) -> str:
        """Extrai a nota inline após 'anotar' ou 'registrar nota'."""
        baixo = text.lower()
        for gatilho in ("registrar nota", "anotar"):
            if gatilho in baixo:
                idx = baixo.index(gatilho) + len(gatilho)
                return text[idx:].strip(" :,-")
        return ""
