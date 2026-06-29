"""Skill de clima — temperatura atual e previsão para amanhã.

Extrai a cidade do próprio comando ("temperatura em Lisboa"). Se não houver,
pergunta por voz (ctx.listen); sem resposta, cai na cidade padrão. Assim a
skill já funciona por texto hoje e fica interativa quando a voz entrar.
"""

import unicodedata

from aris.core.context import Context
from aris.services.weather import WeatherService


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


class WeatherSkill:
    """Responde sobre temperatura e previsão usando o OpenWeather."""

    name = "weather"

    def __init__(self, service: WeatherService, cidade_padrao: str) -> None:
        self._service = service
        self._cidade_padrao = cidade_padrao

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece pedidos de temperatura, previsão ou clima."""
        t = _normalizar(text)
        return any(g in t for g in ("temperatura", "previsao", "clima"))

    def handle(self, text: str, ctx: Context) -> str:
        """Consulta o clima da cidade citada (ou perguntada, ou a padrão)."""
        quer_previsao = "previsao" in _normalizar(text)
        cidade = self._cidade_do_texto(text)
        if not cidade:
            ctx.speak("De qual cidade, senhor?")
            cidade = (ctx.listen() or "").strip()
        if not cidade:
            cidade = self._cidade_padrao
        if quer_previsao:
            return self._service.obter_previsao(cidade)
        return self._service.obter_temperatura(cidade)

    def _cidade_do_texto(self, text: str) -> str:
        """Extrai a cidade após ' em ' (ex.: 'temperatura em São Paulo')."""
        marcador = " em "
        baixo = text.lower()
        if marcador in baixo:
            idx = baixo.rindex(marcador) + len(marcador)
            return text[idx:].strip(" ?.!,")
        return ""
