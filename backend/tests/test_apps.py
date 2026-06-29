"""Testa o reconhecimento e o roteamento da skill de apps (aberturas mockadas)."""

from aris.core.context import Context
from aris.skills.apps import AppsSkill


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


def test_matches_alvos_conhecidos():
    skill = AppsSkill()
    assert skill.matches("abrir navegador", _ctx())
    assert skill.matches("pode abrir o VS Code", _ctx())
    assert skill.matches("abrir instagram", _ctx())


def test_nao_casa_sem_abrir_ou_alvo():
    skill = AppsSkill()
    assert not skill.matches("que horas são", _ctx())
    assert not skill.matches("abrir a janela da sala", _ctx())  # 'abrir' sem alvo conhecido


def test_navegador_abre_url(monkeypatch):
    abertos = []
    monkeypatch.setattr("aris.skills.apps.webbrowser.open", lambda url: abertos.append(url))
    skill = AppsSkill()
    out = skill.handle("abrir navegador", _ctx())
    assert abertos == ["https://www.google.com"]
    assert "navegador" in out.lower()


def test_linkedin_usa_url(monkeypatch):
    abertos = []
    monkeypatch.setattr("aris.skills.apps.webbrowser.open", lambda url: abertos.append(url))
    skill = AppsSkill()
    skill.handle("abrir linkedin", _ctx())
    assert abertos == ["https://www.linkedin.com/"]


def test_instagram_usa_handle_configurado(monkeypatch):
    abertos = []
    monkeypatch.setattr("aris.skills.apps.webbrowser.open", lambda url: abertos.append(url))
    # Sem protocolo disponível (força fallback web): finge falha no protocolo.
    monkeypatch.setattr(AppsSkill, "_abrir_protocolo", lambda self, p: False)
    skill = AppsSkill(instagram_handle="odev.douglas")
    skill.handle("abrir instagram", _ctx())
    assert abertos == ["https://www.instagram.com/odev.douglas/"]
