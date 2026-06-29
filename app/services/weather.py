"""Weather service (OpenWeather)."""

from datetime import datetime, timedelta

import requests
from loguru import logger

from app.config import Config


class WeatherService:
    """Serviço de clima (OpenWeather)"""

    @staticmethod
    def obter_temperatura(cidade: str) -> str:
        """Obtém temperatura atual"""
        if not Config.OPENWEATHER_KEY:
            return "Serviço de clima não configurado."

        try:
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "appid": Config.OPENWEATHER_KEY,
                "q": cidade,
                "lang": "pt_br",
            }

            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            temp = round(data["main"]["temp"] - 273.15, 1)
            desc = data["weather"][0]["description"]

            logger.info(f"Temperatura obtida para {cidade}: {temp} graus")
            return f"A temperatura em {cidade} é de {temp} graus com tempo {desc}."

        except requests.exceptions.Timeout:
            logger.error("Timeout ao buscar clima")
            return "Tempo esgotado ao consultar o clima senhor."
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar clima: {e}")
            return "Não consegui encontrar informações sobre essa cidade, senhor."
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar clima: {e}")
            return "Ocorreu um erro ao consultar o clima senhor."

    @staticmethod
    def obter_previsao(cidade: str) -> str:
        """Obtém previsão para amanhã"""
        if not Config.OPENWEATHER_KEY:
            return "Serviço de previsão não configurado."

        try:
            url = "http://api.openweathermap.org/data/2.5/forecast"
            params = {
                "appid": Config.OPENWEATHER_KEY,
                "q": cidade,
                "lang": "pt_br",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            dados = response.json()
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

            logger.info(f"Previsão obtida para {cidade}")
            return (
                f"A previsão para amanhã em {cidade} é de tempo {desc}, "
                f"com temperatura de {temp} graus."
            )

        except Exception as e:
            logger.error(f"Erro ao obter previsão: {e}")
            return "Não consegui obter a previsão senhor."
