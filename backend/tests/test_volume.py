"""Testa o roteamento da skill de volume (serviço falso)."""

from aris.core.context import Context
from aris.skills.volume import VolumeSkill


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


class _FakeService:
    def __init__(self):
        self.chamada = None

    def aumentar(self):
        self.chamada = "aumentar"
        return "ok"

    def diminuir(self):
        self.chamada = "diminuir"
        return "ok"

    def aumentar_youtube(self):
        self.chamada = "aumentar_youtube"
        return "ok"

    def diminuir_youtube(self):
        self.chamada = "diminuir_youtube"
        return "ok"


def test_matches():
    skill = VolumeSkill(_FakeService())
    assert skill.matches("aumentar volume", _ctx())
    assert skill.matches("abaixar o volume do youtube", _ctx())
    assert not skill.matches("que horas são", _ctx())


def test_aumentar_sistema():
    fake = _FakeService()
    VolumeSkill(fake).handle("aumentar o volume", _ctx())
    assert fake.chamada == "aumentar"


def test_diminuir_youtube():
    fake = _FakeService()
    VolumeSkill(fake).handle("diminuir o volume do youtube", _ctx())
    assert fake.chamada == "diminuir_youtube"


def test_sem_direcao_pergunta():
    fake = _FakeService()
    out = VolumeSkill(fake).handle("volume", _ctx())
    assert fake.chamada is None
    assert "aumentar ou diminuir" in out.lower()
