"""Testa o perfil do usuário (fatos persistidos em JSON)."""

from aris.memory.profile import UserProfile


def test_set_fact_e_contexto(tmp_path):
    p = UserProfile(tmp_path / "p.json")
    p.set_fact("café", "prefere café às 8h")
    assert "prefere café às 8h" in p.as_prompt_context()


def test_persiste_entre_instancias(tmp_path):
    arq = tmp_path / "p.json"
    UserProfile(arq).set_fact("linguagem", "trabalha com Python")
    assert "trabalha com Python" in UserProfile(arq).as_prompt_context()


def test_contexto_vazio(tmp_path):
    assert UserProfile(tmp_path / "p.json").as_prompt_context() == ""
