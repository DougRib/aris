"""Testa a skill de playlists (webbrowser mockado)."""

from aris.core.context import Context
from aris.skills.playlists import PlaylistsSkill

_PLAYLISTS = {"musica": "http://m", "estudo": "http://e", "treino": "http://t"}


def _ctx(resposta_voz: str = "") -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: resposta_voz)


def test_matches():
    skill = PlaylistsSkill(_PLAYLISTS)
    assert skill.matches("tocar playlist treino", _ctx())
    assert skill.matches("tocar música", _ctx())
    assert not skill.matches("que horas são", _ctx())


def test_abre_url_da_playlist_citada(monkeypatch):
    abertos = []
    monkeypatch.setattr(
        "aris.skills.playlists.webbrowser.open", lambda url: abertos.append(url)
    )
    skill = PlaylistsSkill(_PLAYLISTS)
    out = skill.handle("tocar playlist treino", _ctx())
    assert abertos == ["http://t"]
    assert "treino" in out


def test_pergunta_quando_sem_nome(monkeypatch):
    abertos = []
    monkeypatch.setattr(
        "aris.skills.playlists.webbrowser.open", lambda url: abertos.append(url)
    )
    skill = PlaylistsSkill(_PLAYLISTS)
    out = skill.handle("tocar playlist", _ctx(resposta_voz="estudo"))
    assert abertos == ["http://e"]
    assert "estudo" in out
