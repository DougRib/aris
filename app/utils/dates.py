"""Date formatting helpers."""

from datetime import date, datetime

MESES_PT_BR = {
    1: "janeiro",
    2: "fevereiro",
    3: "mar\u00e7o",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


def format_date_pt_br(value: date | datetime) -> str:
    """Return a Portuguese date string like '10 de dezembro de 2024'."""
    return f"{value.day} de {MESES_PT_BR[value.month]} de {value.year}"
