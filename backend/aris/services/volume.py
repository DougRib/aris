"""Serviço de volume do sistema (Windows).

Porta o antigo VolumeService: ajusta o volume mestre via Core Audio (pycaw) e,
se indisponível, cai no winmm (ctypes, sem dependências). O volume por-app do
YouTube usa pycaw — se não estiver instalado, degrada com mensagem amigável.

pycaw/comtypes são opcionais: importados sob demanda. Sem eles, o volume do
sistema ainda funciona pelo winmm; só o volume por-app fica indisponível.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from typing import Iterable

from loguru import logger

STEP = 0.25  # ±25% por comando


def _clamp_float(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _clamp_int(v: int, lo: int = 0, hi: int = 0xFFFF) -> int:
    return max(lo, min(hi, v))


def _ajustar_core_audio(fator: float) -> bool:
    """Tenta ajustar o volume mestre via Core Audio (pycaw). False se indisponível."""
    try:
        from ctypes import POINTER, cast

        from comtypes import CLSCTX_ALL  # type: ignore
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        endpoint = cast(interface, POINTER(IAudioEndpointVolume))
        atual = float(endpoint.GetMasterVolumeLevelScalar())
        endpoint.SetMasterVolumeLevelScalar(_clamp_float(atual * fator), None)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Core Audio indisponível: {exc}")
        return False


def _winmm_get() -> tuple[int, int]:
    vol = wintypes.DWORD()
    if ctypes.windll.winmm.waveOutGetVolume(0, ctypes.byref(vol)) != 0:
        raise RuntimeError("waveOutGetVolume falhou")
    return vol.value & 0xFFFF, (vol.value >> 16) & 0xFFFF


def _winmm_set(left: int, right: int) -> None:
    packed = wintypes.DWORD((right << 16) | left)
    if ctypes.windll.winmm.waveOutSetVolume(0, packed) != 0:
        raise RuntimeError("waveOutSetVolume falhou")


def _ajustar_por_processo(fator: float, nomes: Iterable[str]) -> int:
    """Ajusta o volume das sessões de áudio dos processos dados (pycaw). Conta quantas."""
    from pycaw.pycaw import AudioUtilities  # type: ignore

    alvos = {n.lower() for n in nomes}
    ajustados = 0
    for sessao in AudioUtilities.GetAllSessions():
        if not sessao or not sessao.Process:
            continue
        try:
            if sessao.Process.name().lower() not in alvos:
                continue
            vol = sessao.SimpleAudioVolume
            vol.SetMasterVolume(_clamp_float(float(vol.GetMasterVolume()) * fator), None)
            ajustados += 1
        except Exception:  # noqa: BLE001
            continue
    return ajustados


class VolumeService:
    """Controla o volume mestre e o volume por-app do navegador."""

    def __init__(self, youtube_apps: str) -> None:
        self._youtube_apps = [n.strip().lower() for n in (youtube_apps or "").split(",") if n.strip()]

    def aumentar(self) -> str:
        return self._ajustar_sistema(1 + STEP, "aumentado")

    def diminuir(self) -> str:
        return self._ajustar_sistema(1 - STEP, "reduzido")

    def aumentar_youtube(self) -> str:
        return self._ajustar_youtube(1 + STEP, "aumentado")

    def diminuir_youtube(self) -> str:
        return self._ajustar_youtube(1 - STEP, "reduzido")

    def _ajustar_sistema(self, fator: float, acao: str) -> str:
        if not sys.platform.startswith("win"):
            return "Controle de volume disponível apenas no Windows, senhor."
        try:
            if _ajustar_core_audio(fator):
                return f"Volume {acao} em 25%, senhor."
            left, right = _winmm_get()
            _winmm_set(_clamp_int(int(left * fator)), _clamp_int(int(right * fator)))
            return f"Volume {acao} em 25%, senhor."
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao ajustar volume: {exc}")
            return "Não consegui ajustar o volume, senhor."

    def _ajustar_youtube(self, fator: float, acao: str) -> str:
        if not sys.platform.startswith("win"):
            return "Controle de volume disponível apenas no Windows, senhor."
        try:
            ajustados = _ajustar_por_processo(fator, self._youtube_apps)
            if ajustados:
                return f"Volume do YouTube {acao} em 25%, senhor."
            return "Não encontrei áudio do YouTube ativo, senhor."
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao ajustar volume do YouTube: {exc}")
            return "Não consegui ajustar o volume do YouTube (pycaw indisponível?), senhor."
