"""Testa a lógica do VoiceLoop com STT/TTS/engine falsos (sem áudio nem threads)."""

from aris.core.context import Context
from aris.voice.loop import VoiceLoop


class _FakeEngine:
    def process(self, text: str, ctx: Context) -> str:
        return f"resposta para {text}"


class _FakeSTT:
    def __init__(self, falas):
        self._falas = list(falas)

    def calibrate(self) -> None:
        pass

    def listen(self, timeout: float = 5, phrase_time_limit: float = 6) -> str:
        return self._falas.pop(0) if self._falas else ""


class _FakeTTS:
    def __init__(self):
        self.ditas = []

    def speak(self, text: str) -> bool:
        self.ditas.append(text)
        return True


def _montar(falas):
    eventos: list[dict] = []
    tts = _FakeTTS()
    loop = VoiceLoop(_FakeEngine(), _FakeSTT(falas), tts, eventos.append)
    ctx = Context(speak=loop._falar, listen=loop._ouvir)
    return loop, ctx, eventos, tts


def test_step_processa_ouve_e_fala():
    loop, ctx, eventos, tts = _montar(["que horas são"])
    assert loop._step(ctx) is True
    assert any(e.get("type") == "user_said" for e in eventos)
    assert any(
        e.get("type") == "aris_said" and "resposta para" in e["text"] for e in eventos
    )
    assert any("resposta para" in d for d in tts.ditas)


def test_step_silencio_nao_processa():
    loop, ctx, eventos, tts = _montar([""])
    assert loop._step(ctx) is True
    assert not any(e.get("type") == "aris_said" for e in eventos)
    assert tts.ditas == []


def test_comando_de_saida_encerra_o_loop():
    loop, ctx, eventos, tts = _montar(["tchau senhor"])
    assert loop._step(ctx) is False
    assert any(
        e.get("type") == "aris_said" and "Até mais" in e["text"] for e in eventos
    )


def test_emite_estado_processing_em_comando_valido():
    loop, ctx, eventos, _ = _montar(["abrir navegador"])
    loop._step(ctx)
    assert any(e.get("type") == "state" and e.get("state") == "processing" for e in eventos)
