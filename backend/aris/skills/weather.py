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


# Palavras-chave de clima: a cidade vem DEPOIS da última delas.
_PALAVRAS_CLIMA = ("temperatura", "previsão", "previsao", "clima", "tempo")

# Preposições/enchimento a descartar no início do nome da cidade (já sem acento).
# Não removemos do meio, para preservar nomes como "Rio de Janeiro".
_ENCHIMENTO = {
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "pra", "a", "o", "ao", "hoje", "agora", "amanha", "manha",
    "por", "favor", "ai", "la", "esta", "e",
}


class WeatherSkill:
    """Responde sobre temperatura e previsão usando o OpenWeather."""

    name = "weather"

    def __init__(self, service: WeatherService, cidade_padrao: str) -> None:
        self._service = service
        self._cidade_padrao = cidade_padrao

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece pedidos de temperatura, previsão, clima ou 'tempo'."""
        t = _normalizar(text)
        return any(g in t for g in ("temperatura", "previsao", "clima", "tempo"))

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
        """Extrai a cidade que vem após a palavra de clima.

        Pega tudo após a ÚLTIMA palavra-chave de clima e remove preposições/
        enchimento só do INÍCIO ("no", "de hoje em"…), preservando o restante —
        assim "previsão do tempo no Rio de Janeiro" → "Rio de Janeiro".
        """
        baixo = text.lower()  # mesmo tamanho do original (preserva o corte)
        fim = -1
        for palavra in _PALAVRAS_CLIMA:
            idx = baixo.rfind(palavra)
            if idx != -1:
                fim = max(fim, idx + len(palavra))
        if fim == -1:
            return ""
        tokens = text[fim:].strip(" ?.!,").split()
        while tokens and _normalizar(tokens[0]) in _ENCHIMENTO:
            tokens.pop(0)
        return " ".join(tokens).strip(" ?.!,")
