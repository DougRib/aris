"""Testa a ToolBox de ferramentas dos sub-agentes (sem rede)."""

from aris.agents.tools import ToolBox


class _FakeWeather:
    def obter_temperatura(self, cidade: str) -> str:
        return f"temp de {cidade}"

    def obter_previsao(self, cidade: str) -> str:
        return f"previsao de {cidade}"


def test_consultar_clima_atual():
    tb = ToolBox(_FakeWeather())
    assert tb.consultar_clima("Lisboa") == "temp de Lisboa"


def test_consultar_clima_previsao():
    tb = ToolBox(_FakeWeather())
    assert tb.consultar_clima("Rio de Janeiro", previsao=True) == "previsao de Rio de Janeiro"


def test_tools_expostas():
    nomes = [t.__name__ for t in ToolBox(_FakeWeather()).tools()]
    assert "consultar_clima" in nomes
    assert "data_e_hora" in nomes
