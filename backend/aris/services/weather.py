"""Serviço de clima — wrapper da API OpenWeather (v2.5).

Porta a lógica do antigo WeatherService: consulta temperatura atual e previsão
de amanhã, convertendo de Kelvin para Celsius e respondendo em português.
A API key é injetada (vem de settings.openweather_key), não lida globalmente.
"""

from datetime import datetime, timedelta

import requests
from loguru import logger

_BASE = "http://api.openweathermap.org/data/2.5"


class WeatherService:
    """Consulta o OpenWeather e formata respostas em PT-BR."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def obter_temperatura(self, cidade: str) -> str:
        """Temperatura atual da cidade, em graus Celsius."""
        if not self._api_key:
            return "Serviço de clima não configurado, senhor."
        try:
            resp = requests.get(
                f"{_BASE}/weather",
                params={"appid": self._api_key, "q": cidade, "lang": "pt_br"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            temp = round(data["main"]["temp"] - 273.15, 1)
            desc = data["weather"][0]["description"]
            return f"A temperatura em {cidade} é de {temp} graus com tempo {desc}, senhor."
        except requests.exceptions.Timeout:
            logger.error("Timeout ao buscar clima")
            return "Tempo esgotado ao consultar o clima, senhor."
        except requests.exceptions.RequestException as exc:
            logger.error(f"Erro ao buscar clima: {exc}")
            return "Não consegui encontrar informações sobre essa cidade, senhor."
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro inesperado no clima: {exc}")
            return "Ocorreu um erro ao consultar o clima, senhor."

    def obter_previsao(self, cidade: str) -> str:
        """Previsão para amanhã (primeiro horário disponível)."""
        if not self._api_key:
            return "Serviço de previsão não configurado, senhor."
        try:
            resp = requests.get(
                f"{_BASE}/forecast",
                params={"appid": self._api_key, "q": cidade, "lang": "pt_br"},
                timeout=10,
            )
            resp.raise_for_status()
            dados = resp.json()
            amanha = (datetime.now() + timedelta(days=1)).date()
            previsao = [
                item
                for item in dados["list"]
                if datetime.fromtimestamp(item["dt"]).date() == amanha
            ]
            if not previsao:
                return "Não encontrei dados de previsão para amanhã, senhor."
            temp = round(previsao[0]["main"]["temp"] - 273.15, 1)
            desc = previsao[0]["weather"][0]["description"]
            return (
                f"A previsão para amanhã em {cidade} é de tempo {desc}, "
                f"com temperatura de {temp} graus, senhor."
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao obter previsão: {exc}")
            return "Não consegui obter a previsão, senhor."
