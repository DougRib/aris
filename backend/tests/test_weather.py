"""Testa o serviço de clima (HTTP mockado) e a skill de clima."""

import pytest

from aris.core.context import Context
from aris.services.weather import WeatherService
from aris.skills.weather import WeatherSkill


def _ctx(resposta_voz: str = "") -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: resposta_voz)


# --- serviço ---


def test_service_temperatura(monkeypatch):
    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"main": {"temp": 300.15}, "weather": [{"description": "céu limpo"}]}

    monkeypatch.setattr(
        "aris.services.weather.requests.get", lambda *a, **k: _Resp()
    )
    service = WeatherService("fake-key")
    out = service.obter_temperatura("Lisboa")
    assert "27.0 graus" in out
    assert "céu limpo" in out


def test_service_sem_chave():
    assert "não configurado" in WeatherService("").obter_temperatura("Lisboa")


# --- skill ---


class _FakeService:
    def __init__(self):
        self.cidade = None

    def obter_temperatura(self, cidade):
        self.cidade = cidade
        return f"temp de {cidade}"

    def obter_previsao(self, cidade):
        self.cidade = cidade
        return f"previsao de {cidade}"


def test_skill_matches():
    skill = WeatherSkill(_FakeService(), "São Paulo")
    assert skill.matches("qual a temperatura em Lisboa", _ctx())
    assert skill.matches("previsão do tempo", _ctx())
    assert not skill.matches("que horas são", _ctx())


@pytest.mark.parametrize(
    "comando,esperado",
    [
        ("temperatura em Lisboa", "Lisboa"),
        ("me diga o tempo em Porto Alegre", "Porto Alegre"),
        ("previsão do tempo no Rio de Janeiro", "Rio de Janeiro"),
        ("qual o clima na Bahia", "Bahia"),
        ("previsão de Lisboa", "Lisboa"),
        ("como está o tempo de hoje em São Paulo", "São Paulo"),
    ],
)
def test_skill_extrai_cidade_do_texto(comando, esperado):
    fake = _FakeService()
    WeatherSkill(fake, "São Paulo").handle(comando, _ctx())
    assert fake.cidade == esperado


def test_skill_sem_cidade_no_texto_usa_padrao():
    fake = _FakeService()
    WeatherSkill(fake, "São Paulo").handle("qual o tempo de hoje", _ctx())
    assert fake.cidade == "São Paulo"


def test_skill_cai_na_cidade_padrao_sem_voz():
    fake = _FakeService()
    skill = WeatherSkill(fake, "São Paulo")
    skill.handle("qual a temperatura", _ctx(resposta_voz=""))
    assert fake.cidade == "São Paulo"


def test_skill_previsao():
    fake = _FakeService()
    skill = WeatherSkill(fake, "São Paulo")
    out = skill.handle("previsão em Curitiba", _ctx())
    assert out == "previsao de Curitiba"
