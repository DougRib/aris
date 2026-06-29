"""System volume control."""

from __future__ import annotations

import sys
import ctypes
from ctypes import wintypes
from typing import Iterable

from loguru import logger

from app.config import Config


def _clamp(value: int, minimum: int = 0, maximum: int = 0xFFFF) -> int:
    return max(minimum, min(maximum, value))

def _clamp_float(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _get_core_audio_endpoint():
    try:
        from ctypes import POINTER, cast
        from comtypes import CLSCTX_ALL  # type: ignore
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"Core Audio indisponivel: {exc}") from exc

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def _ajustar_core_audio(fator: float) -> bool:
    try:
        endpoint = _get_core_audio_endpoint()
        current = float(endpoint.GetMasterVolumeLevelScalar())
        new_value = _clamp_float(current * fator)
        endpoint.SetMasterVolumeLevelScalar(new_value, None)
        return True
    except Exception as exc:
        logger.debug(f"Core Audio nao disponivel: {exc}")
        return False


def _parse_process_names(names: str) -> set[str]:
    return {nome.strip().lower() for nome in (names or "").split(",") if nome.strip()}


def _target_youtube_processes() -> set[str]:
    raw = (Config.YOUTUBE_VOLUME_APPS or "").strip()
    if not raw:
        return {"msedge.exe"}
    return _parse_process_names(raw)


def _ajustar_sessoes_por_processo(fator: float, process_names: Iterable[str]) -> int:
    try:
        from pycaw.pycaw import AudioUtilities  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"pycaw indisponivel: {exc}") from exc

    nomes = {nome.lower() for nome in process_names}
    prefixos = {nome[:-4] for nome in nomes if nome.endswith(".exe")}
    ajustados = 0
    for session in AudioUtilities.GetAllSessions():
        if not session or not session.Process:
            continue
        try:
            nome = session.Process.name().lower()
        except Exception:
            continue
        if nome not in nomes and nome not in {f"{p}.exe" for p in prefixos}:
            continue
        try:
            volume = session.SimpleAudioVolume
            atual = float(volume.GetMasterVolume())
            novo = _clamp_float(atual * fator)
            volume.SetMasterVolume(novo, None)
            ajustados += 1
        except Exception:
            continue
    return ajustados


def _listar_sessoes_audio() -> set[str]:
    try:
        from pycaw.pycaw import AudioUtilities  # type: ignore
    except Exception:
        return set()

    nomes = set()
    for session in AudioUtilities.GetAllSessions():
        if not session or not session.Process:
            continue
        try:
            nomes.add(session.Process.name().lower())
        except Exception:
            continue
    return nomes


def _get_volume() -> tuple[int, int]:
    volume = wintypes.DWORD()
    result = ctypes.windll.winmm.waveOutGetVolume(0, ctypes.byref(volume))
    if result != 0:
        raise RuntimeError(f"waveOutGetVolume failed: {result}")
    left = volume.value & 0xFFFF
    right = (volume.value >> 16) & 0xFFFF
    return left, right


def _set_volume(left: int, right: int) -> None:
    packed = wintypes.DWORD((right << 16) | left)
    result = ctypes.windll.winmm.waveOutSetVolume(0, packed)
    if result != 0:
        raise RuntimeError(f"waveOutSetVolume failed: {result}")


class VolumeService:
    """Controla o volume do sistema."""

    STEP = 0.25

    @staticmethod
    def aumentar() -> str:
        return VolumeService._ajustar(1 + VolumeService.STEP, "aumentado")

    @staticmethod
    def diminuir() -> str:
        return VolumeService._ajustar(1 - VolumeService.STEP, "reduzido")

    @staticmethod
    def aumentar_youtube() -> str:
        return VolumeService._ajustar_app(1 + VolumeService.STEP, "aumentado", "YouTube")

    @staticmethod
    def diminuir_youtube() -> str:
        return VolumeService._ajustar_app(1 - VolumeService.STEP, "reduzido", "YouTube")

    @staticmethod
    def _ajustar(fator: float, acao: str) -> str:
        if not sys.platform.startswith("win"):
            return "Controle de volume disponível apenas no Windows, senhor."

        try:
            if _ajustar_core_audio(fator):
                return f"Volume {acao} em 25%, senhor."
            left, right = _get_volume()
            new_left = _clamp(int(left * fator))
            new_right = _clamp(int(right * fator))
            _set_volume(new_left, new_right)
            return f"Volume {acao} em 25%, senhor."
        except Exception as exc:
            logger.error(f"Erro ao ajustar volume: {exc}")
            return "Não consegui ajustar o volume, senhor."

    @staticmethod
    def _ajustar_app(fator: float, acao: str, descricao: str) -> str:
        if not sys.platform.startswith("win"):
            return "Controle de volume disponível apenas no Windows, senhor."

        try:
            processos = _target_youtube_processes()
            ajustados = _ajustar_sessoes_por_processo(fator, processos)
            if ajustados:
                return f"Volume do {descricao} {acao} em 25%, senhor."
            ativos = _listar_sessoes_audio()
            if ativos:
                logger.info(f"Sessoes de audio ativas: {', '.join(sorted(ativos))}")
            return f"Não encontrei áudio do {descricao} ativo, senhor."
        except Exception as exc:
            logger.error(f"Erro ao ajustar volume do {descricao}: {exc}")
            return f"Não consegui ajustar o volume do {descricao}, senhor."
