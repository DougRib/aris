"""Skill de hora e data — responde 'que horas são' e 'que dia é hoje'."""

from datetime import datetime

from aris.core.context import Context
from aris.utils.dates import format_date_pt_br


class DateTimeSkill:
    """Informa a hora atual ou a data de hoje."""

    name = "datetime"

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece perguntas sobre hora ou data."""
        t = text.lower()
        return any(g in t for g in ("que horas", "horas", "que dia", "data de hoje"))

    def handle(self, text: str, ctx: Context) -> str:
        """Responde com a hora ou a data conforme o pedido."""
        t = text.lower()
        if "dia" in t or "data" in t:
            return f"Hoje é {format_date_pt_br(datetime.now())}, senhor."
        return f"Agora são {datetime.now().strftime('%H:%M')}, senhor."
