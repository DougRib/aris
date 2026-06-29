"""Testa a memória de curto prazo: registro, contexto p/ prompt e modo privado."""

from aris.memory.short_term import ShortTermMemory


def _mem(tmp_path):
    return ShortTermMemory(max_items=3, arquivo=tmp_path / "mem.json")


def test_registrar_e_contexto(tmp_path):
    mem = _mem(tmp_path)
    mem.registrar("que horas sao", "sao 10h")
    ctx = mem.as_prompt_context()
    assert "que horas sao" in ctx
    assert "sao 10h" in ctx


def test_limite_de_itens(tmp_path):
    mem = _mem(tmp_path)
    for i in range(5):
        mem.registrar(f"p{i}", f"r{i}")
    ctx = mem.as_prompt_context()
    assert "p0" not in ctx  # estourou o limite de 3
    assert "p4" in ctx


def test_modo_privado_nao_registra(tmp_path):
    mem = _mem(tmp_path)
    mem.private_mode = True
    mem.registrar("segredo", "resposta")
    assert mem.as_prompt_context() == ""


def test_persiste_e_carrega(tmp_path):
    arquivo = tmp_path / "mem.json"
    mem = ShortTermMemory(max_items=3, arquivo=arquivo)
    mem.registrar("oi", "ola")
    mem.salvar()
    outra = ShortTermMemory(max_items=3, arquivo=arquivo)
    assert "oi" in outra.as_prompt_context()
