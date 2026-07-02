"""Ferramentas (tools) que o LLM pode CHAMAR sozinho — a base dos sub-agentes.

Cada método é uma função que o Gemini pode invocar via function calling. O SDK
lê o NOME, a DOCSTRING (incl. os Args) e os TIPOS para decidir quando e como
chamar. Manter as docstrings claras é o que ensina o modelo a usar a ferramenta.
"""

from datetime import datetime

from loguru import logger

from aris.services.weather import WeatherService
from aris.utils.dates import format_date_pt_br


class ToolBox:
    """Conjunto de ferramentas disponíveis para o agente."""

    def __init__(self, weather: WeatherService) -> None:
        self._weather = weather

    def consultar_clima(self, cidade: str, previsao: bool = False) -> str:
        """Consulta o tempo de uma cidade: temperatura agora ou previsão de amanhã.

        Use esta ferramenta sempre que o usuário perguntar sobre tempo, clima,
        temperatura, chuva ou se precisa de guarda-chuva.

        Args:
            cidade: nome da cidade, por exemplo "Porto Alegre".
            previsao: True para a previsão de amanhã; False para o tempo agora.
        """
        logger.info(f"🔧 tool consultar_clima(cidade={cidade!r}, previsao={previsao})")
        if previsao:
            return self._weather.obter_previsao(cidade)
        return self._weather.obter_temperatura(cidade)

    def data_e_hora(self) -> str:
        """Retorna a data e a hora atuais. Use para perguntas sobre dia/data/hora."""
        logger.info("🔧 tool data_e_hora()")
        agora = datetime.now()
        return f"{format_date_pt_br(agora)}, {agora.strftime('%H:%M')}"

    def tools(self) -> list:
        """Lista das ferramentas expostas ao LLM (funções que ele pode chamar)."""
        return [self.consultar_clima, self.data_e_hora]
