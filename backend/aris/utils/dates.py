"""Formatação de datas em português."""

from datetime import date, datetime

MESES_PT_BR = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
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
    """Retorna algo como '29 de junho de 2026'."""
    return f"{value.day} de {MESES_PT_BR[value.month]} de {value.year}"
