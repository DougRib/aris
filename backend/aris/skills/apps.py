"""Skill de abertura de apps e sites (Windows).

Porta os comandos "abrir ..." do antigo CommandProcessor: navegador,
calculadora, Word, Excel, VS Code, WhatsApp, Telegram, LinkedIn, Instagram,
Facebook. Cada alvo tem suas estratégias (executável, protocolo, AppsFolder
ou web) tentadas em ordem. Roda no backend local, dono do sistema.
"""

import os
import shutil
import subprocess
import sys
import unicodedata
import webbrowser
from pathlib import Path

from loguru import logger

from aris.core.context import Context


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return " ".join("".join(ch for ch in texto if not unicodedata.combining(ch)).split())


class AppsSkill:
    """Abre programas e sites a partir de comandos de voz/texto."""

    name = "apps"

    def __init__(self, word_path: str = "", instagram_handle: str = "", facebook_profile: str = "") -> None:
        self._word_path = word_path
        self._instagram_handle = instagram_handle
        self._facebook_profile = facebook_profile
        # Ordem importa: alvos mais específicos primeiro (ex.: "microsoft word").
        self._alvos: list[tuple[tuple[str, ...], object]] = [
            (("navegador",), self._abrir_navegador),
            (("calculadora",), lambda: self._abrir_programa("calc", "a calculadora")),
            (("word", "microsoft word"), self._abrir_word),
            (("excel", "microsoft excel"), lambda: self._abrir_programa("excel", "o Microsoft Excel")),
            (("vs code", "vscode", "visual studio code"), self._abrir_vscode),
            (("whatsapp", "whats app", "zap"), self._abrir_whatsapp),
            (("telegram", "telegran"), self._abrir_telegram),
            (("linkedin", "linked in"), self._abrir_linkedin),
            (("instagram", "instagran", "insta"), self._abrir_instagram),
            (("facebook", "face", "fb"), self._abrir_facebook),
        ]

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece 'abrir <alvo>' para um alvo conhecido."""
        t = _normalizar(text)
        if "abrir" not in t:
            return False
        return any(any(p in t for p in palavras) for palavras, _ in self._alvos)

    def handle(self, text: str, ctx: Context) -> str:
        """Abre o primeiro alvo conhecido mencionado no comando."""
        t = _normalizar(text)
        for palavras, abrir in self._alvos:
            if any(p in t for p in palavras):
                return abrir()  # type: ignore[operator]
        return "Não sei abrir isso, senhor."

    # --- estratégias genéricas ---

    def _abrir_navegador(self) -> str:
        return self._abrir_url("o navegador", "https://www.google.com")

    def _abrir_url(self, descricao: str, url: str) -> str:
        try:
            webbrowser.open(url)
            return f"Abrindo {descricao}, senhor."
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao abrir {descricao}: {exc}")
            return f"Não consegui abrir {descricao}, senhor."

    def _abrir_programa(self, comando: str, descricao: str) -> str:
        try:
            caminho = shutil.which(comando)
            if caminho:
                subprocess.Popen([caminho])
            elif sys.platform.startswith("win"):
                subprocess.Popen(["cmd", "/c", "start", "", comando], shell=False)
            else:
                subprocess.Popen([comando], start_new_session=True)
            return f"Abrindo {descricao}, senhor."
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao abrir {descricao}: {exc}")
            return f"Não consegui abrir {descricao}. Verifique se está instalado, senhor."

    def _abrir_protocolo(self, protocolo: str) -> bool:
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["cmd", "/c", "start", "", protocolo], shell=False)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", protocolo], start_new_session=True)
            else:
                subprocess.Popen(["xdg-open", protocolo], start_new_session=True)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao abrir protocolo {protocolo}: {exc}")
            return False

    def _abrir_appsfolder(self, app_id: str) -> bool:
        if not sys.platform.startswith("win"):
            return False
        try:
            subprocess.Popen(["cmd", "/c", "start", "", f"shell:AppsFolder\\{app_id}"], shell=False)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao abrir AppsFolder {app_id}: {exc}")
            return False

    # --- alvos específicos ---

    def _abrir_word(self) -> str:
        if not sys.platform.startswith("win"):
            return self._abrir_programa("winword", "o Microsoft Word")
        if self._word_path and Path(self._word_path).is_file():
            try:
                subprocess.Popen([self._word_path])
                return "Abrindo o Microsoft Word, senhor."
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Erro ao abrir Word: {exc}")
        bases = [Path(os.environ.get("ProgramFiles", "")), Path(os.environ.get("ProgramFiles(x86)", ""))]
        for base in bases:
            for versao in ("16", "15", "14"):
                for sub in (f"Microsoft Office/root/Office{versao}", f"Microsoft Office/Office{versao}"):
                    caminho = base / sub / "WINWORD.EXE"
                    if caminho.is_file():
                        try:
                            subprocess.Popen([str(caminho)])
                            return "Abrindo o Microsoft Word, senhor."
                        except Exception as exc:  # noqa: BLE001
                            logger.error(f"Erro ao abrir Word: {exc}")
        return "Não consegui abrir o Microsoft Word. Verifique se está instalado, senhor."

    def _abrir_vscode(self) -> str:
        if sys.platform.startswith("win"):
            candidatos = [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Microsoft VS Code/Code.exe",
                Path(os.environ.get("ProgramFiles", "")) / "Microsoft VS Code/Code.exe",
            ]
            for caminho in candidatos:
                if caminho.is_file():
                    try:
                        subprocess.Popen([str(caminho)])
                        return "Abrindo o Visual Studio Code, senhor."
                    except Exception as exc:  # noqa: BLE001
                        logger.error(f"Erro ao abrir VS Code: {exc}")
        return self._abrir_programa("code", "o Visual Studio Code")

    def _abrir_whatsapp(self) -> str:
        if self._abrir_protocolo("whatsapp://"):
            return "Abrindo o WhatsApp, senhor."
        return self._abrir_url("o WhatsApp Web", "https://web.whatsapp.com/")

    def _abrir_telegram(self) -> str:
        if self._abrir_protocolo("tg://"):
            return "Abrindo o Telegram, senhor."
        return self._abrir_url("o Telegram Web", "https://web.telegram.org/")

    def _abrir_linkedin(self) -> str:
        return self._abrir_url("o LinkedIn", "https://www.linkedin.com/")

    def _abrir_instagram(self) -> str:
        handle = (self._instagram_handle or "").lstrip("@").strip()
        if handle and self._abrir_protocolo(f"instagram://user?username={handle}"):
            return "Abrindo o Instagram, senhor."
        url = f"https://www.instagram.com/{handle}/" if handle else "https://www.instagram.com/"
        return self._abrir_url("o Instagram", url)

    def _abrir_facebook(self) -> str:
        perfil = (self._facebook_profile or "").strip()
        if perfil:
            url = perfil if perfil.startswith("http") else f"https://www.facebook.com/{perfil}"
        else:
            url = "https://www.facebook.com/"
        return self._abrir_url("o Facebook", url)
