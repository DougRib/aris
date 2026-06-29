"""Command processing logic."""

import os
import shutil
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
import unicodedata

from loguru import logger

from app.config import Config
from app.managers.memory import MemoryManager
from app.managers.notes import NotesManager
from app.services.gemini import GeminiService
from app.services.music import MusicService
from app.services.volume import VolumeService
from app.services.weather import WeatherService
from app.utils.dates import format_date_pt_br


class CommandProcessor:
    """Processa comandos do usuário"""

    def __init__(
        self,
        memory: MemoryManager,
        notes: NotesManager,
        weather: WeatherService,
        gemini: GeminiService,
        music: MusicService,
    ):
        self.memory = memory
        self.notes = notes
        self.weather = weather
        self.gemini = gemini
        self.music = music

    def processar(self, comando: str, falar_callback, ouvir_callback) -> str:
        """Processa comando e retorna resposta"""
        comando_lower = comando.lower()
        logger.info(f"Processando comando: {comando}")

        try:
            # COMANDOS DE SISTEMA
            if "abrir navegador" in comando_lower:
                return self._abrir_navegador()

            if "abrir calculadora" in comando_lower:
                return self._abrir_programa("calc", "a calculadora")

            if any(x in comando_lower for x in ["abrir word", "abrir microsoft word"]):
                return self._abrir_word()

            if any(x in comando_lower for x in ["abrir excel", "abrir microsoft excel"]):
                return self._abrir_programa("excel", "o Microsoft Excel")

            if any(
                x in comando_lower
                for x in [
                    "abrir vs code",
                    "abrir vscode",
                    "abrir visual studio code",
                ]
            ):
                return self._abrir_vscode()

            if any(x in comando_lower for x in ["abrir whatsapp", "abrir whats app", "abrir zap"]):
                return self._abrir_whatsapp()

            if any(x in comando_lower for x in ["abrir telegram", "abrir telegran"]):
                return self._abrir_telegram()

            if any(x in comando_lower for x in ["abrir linkedin", "abrir linked in"]):
                return self._abrir_linkedin()

            if any(x in comando_lower for x in ["abrir instagram", "abrir instagran", "abrir insta"]):
                return self._abrir_instagram()

            if any(x in comando_lower for x in ["abrir facebook", "abrir face", "abrir fb"]):
                return self._abrir_facebook()

            # VOLUME YOUTUBE (NAVEGADOR)
            if any(y in comando_lower for y in ["youtube", "you tube"]) and any(
                x in comando_lower for x in ["aumentar", "subir", "mais"]
            ):
                return VolumeService.aumentar_youtube()

            if any(y in comando_lower for y in ["youtube", "you tube"]) and any(
                x in comando_lower for x in ["baixar", "diminuir", "reduzir", "menos"]
            ):
                return VolumeService.diminuir_youtube()

            # VOLUME
            if any(
                x in comando_lower
                for x in [
                    "aumentar volume",
                    "aumentar o volume",
                    "subir volume",
                    "subir o volume",
                    "mais volume",
                ]
            ):
                return VolumeService.aumentar()

            if any(
                x in comando_lower
                for x in [
                    "baixar volume",
                    "baixar o volume",
                    "diminuir volume",
                    "diminuir o volume",
                    "reduzir volume",
                    "reduzir o volume",
                    "menos volume",
                ]
            ):
                return VolumeService.diminuir()

            # HORA / DATA
            if "que horas são" in comando_lower or "horas" in comando_lower:
                hora = datetime.now().strftime("%H:%M")
                return f"Agora são {hora}, senhor."

            if "que dia é hoje" in comando_lower or "data de hoje" in comando_lower:
                data = format_date_pt_br(datetime.now())
                return f"Hoje é {data} senhor."

            # CLIMA
            if "temperatura" in comando_lower:
                falar_callback("De qual cidade deseja saber?")
                cidade = ouvir_callback()
                if cidade:
                    return self.weather.obter_temperatura(cidade)
                return "Não consegui ouvir o nome da cidade, senhor."

            if "previsão" in comando_lower or "previsao" in comando_lower:
                falar_callback("Para qual cidade devo consultar a previsão?")
                cidade = ouvir_callback()
                if cidade:
                    return self.weather.obter_previsao(cidade)
                return "Não consegui ouvir o nome da cidade, senhor."

            # PESQUISA COM IA
            if any(
                x in comando_lower
                for x in ["pesquisar", "perguntar", "me explique", "o que é"]
            ):
                assunto = comando_lower
                for palavra in ["pesquisar", "perguntar", "me explique", "o que é"]:
                    assunto = assunto.replace(palavra, "").strip()

                if not assunto:
                    falar_callback("Sobre o que deseja saber, senhor?")
                    assunto = ouvir_callback()

                if assunto:
                    falar_callback("Um momento, consultando minha base de conhecimento.")
                    return self.gemini.pesquisar(assunto)
                return "Não consegui entender o assunto da pesquisa."

            # PLAYLISTS
            if (
                "playlist" in comando_lower
                or "tocar música" in comando_lower
                or "tocar musica" in comando_lower
            ):
                comando_normalizado = self._normalizar_texto(comando_lower)
                for chave in Config.PLAYLISTS.keys():
                    if self._normalizar_texto(chave) in comando_normalizado:
                        return self.music.tocar_playlist(chave)

                falar_callback("Qual playlist o senhor deseja? Música, estudo ou treino?")
                nome_playlist = ouvir_callback(timeout=7, phrase_time_limit=5)
                if not nome_playlist:
                    falar_callback("Não consegui ouvir. Diga, por exemplo: playlist música.")
                    nome_playlist = ouvir_callback(timeout=7, phrase_time_limit=5)

                if nome_playlist:
                    return self.music.tocar_playlist(nome_playlist)
                return "Não entendi o nome da playlist."

            # NOTAS
            if "anotar" in comando_lower or "registrar nota" in comando_lower:
                falar_callback("O que deseja anotar, senhor?")
                nota = ouvir_callback()
                if nota:
                    return self.notes.registrar_nota(nota)
                return "Não consegui ouvir o conteúdo da anotação."

            # MEMÓRIA
            if any(x in comando_lower for x in ["o que falamos", "histórico", "historico", "resumo"]):
                return self.memory.obter_resumo()

            # MODO PRIVADO
            if "ativar modo privado" in comando_lower:
                return self.memory.ativar_modo_privado()

            if "desativar modo privado" in comando_lower:
                return self.memory.desativar_modo_privado()

            # AJUDA
            if (
                "ajuda" in comando_lower
                or "comandos" in comando_lower
                or "o que você pode fazer" in comando_lower
            ):
                return self._obter_ajuda()

            # Fallback IA
            return self.gemini.pesquisar(comando)

        except Exception as e:
            logger.error(f"Erro ao processar comando: {e}")
            return "Desculpe, ocorreu um erro ao processar seu comando, senhor."

    def _obter_ajuda(self) -> str:
        """Retorna lista de comandos disponíveis"""
        return """Posso ajudá-lo com:

        SISTEMA: abrir navegador, calculadora, Word, Excel, VS Code.
        APPS: abrir WhatsApp, Telegram, LinkedIn, Instagram, Facebook.
        TEMPO: que horas são, que dia é hoje.
        CLIMA: temperatura, previsão do tempo.
        VOLUME: aumentar volume, baixar volume, aumentar/baixar volume do YouTube.
        MÚSICA: tocar playlist (música, estudo, treino).
        NOTAS: anotar, registrar nota.
        MEMÓRIA: histórico, o que falamos hoje.
        PRIVACIDADE: ativar/desativar modo privado.
        IA: pesquisar qualquer coisa, fazer perguntas.

        Como posso ajudá-lo, senhor?"""

    def _abrir_navegador(self) -> str:
        try:
            webbrowser.open("https://www.google.com")
            return "Abrindo o navegador padrão, senhor."
        except Exception as e:
            logger.error(f"Erro ao abrir navegador: {e}")
            return "Não consegui abrir o navegador, senhor."

    def _abrir_programa(self, comando: str, descricao: str) -> str:
        try:
            caminho = shutil.which(comando)
            if caminho:
                subprocess.Popen([caminho])
            elif sys.platform.startswith("win"):
                subprocess.Popen(["cmd", "/c", "start", "", comando], shell=False)
            else:
                subprocess.Popen([comando], start_new_session=True)
            return f"Abrindo {descricao}."
        except Exception as e:
            logger.error(f"Erro ao abrir {descricao}: {e}")
            return f"Não consegui abrir {descricao}. Verifique se está instalado."

    def _abrir_url(self, descricao: str, url: str) -> str:
        try:
            webbrowser.open(url)
            return f"Abrindo {descricao}, senhor."
        except Exception as e:
            logger.error(f"Erro ao abrir {descricao}: {e}")
            return f"Não consegui abrir {descricao}, senhor."

    def _abrir_protocolo(self, protocolo: str) -> bool:
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["cmd", "/c", "start", "", protocolo], shell=False)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", protocolo], start_new_session=True)
            else:
                subprocess.Popen(["xdg-open", protocolo], start_new_session=True)
            return True
        except Exception as e:
            logger.error(f"Erro ao abrir protocolo {protocolo}: {e}")
            return False

    def _abrir_appsfolder(self, app_id: str) -> bool:
        if not sys.platform.startswith("win"):
            return False
        try:
            alvo = f"shell:AppsFolder\\{app_id}"
            subprocess.Popen(["cmd", "/c", "start", "", alvo], shell=False)
            return True
        except Exception as e:
            logger.error(f"Erro ao abrir AppsFolder {app_id}: {e}")
            return False

    def _abrir_word(self) -> str:
        if sys.platform.startswith("win"):
            if Config.WORD_PATH:
                caminho = Path(Config.WORD_PATH)
                if caminho.is_file():
                    try:
                        subprocess.Popen([str(caminho)])
                        return "Abrindo o Microsoft Word."
                    except Exception as e:
                        logger.error(f"Erro ao abrir Word: {e}")

            bases = [
                Path(os.environ.get("ProgramFiles", "")),
                Path(os.environ.get("ProgramFiles(x86)", "")),
            ]
            versoes = ("16", "15", "14", "12")
            candidatos = []
            for base in bases:
                if not str(base):
                    continue
                for versao in versoes:
                    candidatos.extend(
                        [
                            base
                            / f"Microsoft Office/root/Office{versao}/WINWORD.EXE",
                            base / f"Microsoft Office/Office{versao}/WINWORD.EXE",
                        ]
                    )
            for caminho in candidatos:
                if caminho.is_file():
                    try:
                        subprocess.Popen([str(caminho)])
                        return "Abrindo o Microsoft Word."
                    except Exception as e:
                        logger.error(f"Erro ao abrir Word: {e}")
                        break
            app_ids = [
                "Microsoft.Office.Word_8wekyb3d8bbwe!microsoft.office.word",
                "Microsoft.Office.Word_8wekyb3d8bbwe!App",
                "Microsoft.Office.Desktop_8wekyb3d8bbwe!Word",
                "Microsoft.Office.Desktop_8wekyb3d8bbwe!Microsoft.Office.Word",
            ]
            for app_id in app_ids:
                if self._abrir_appsfolder(app_id):
                    return "Abrindo o Microsoft Word."

            return "Não consegui abrir o Microsoft Word. Verifique se está instalado."

        return self._abrir_programa("winword", "o Microsoft Word")

    def _normalizar_texto(self, texto: str) -> str:
        texto = (texto or "").lower().strip()
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
        return " ".join(texto.split())

    def _abrir_whatsapp(self) -> str:
        if self._abrir_protocolo("whatsapp://"):
            return "Abrindo o WhatsApp."
        return self._abrir_url("o WhatsApp Web", "https://web.whatsapp.com/")

    def _abrir_telegram(self) -> str:
        if sys.platform.startswith("win"):
            candidatos = [
                Path(os.environ.get("APPDATA", "")) / "Telegram Desktop/Telegram.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Telegram Desktop/Telegram.exe",
            ]
            for caminho in candidatos:
                if caminho.is_file():
                    try:
                        subprocess.Popen([str(caminho)])
                        return "Abrindo o Telegram."
                    except Exception as e:
                        logger.error(f"Erro ao abrir Telegram: {e}")
                        break
        if self._abrir_protocolo("tg://"):
            return "Abrindo o Telegram."
        return self._abrir_url("o Telegram Web", "https://web.telegram.org/")

    def _abrir_linkedin(self) -> str:
        return self._abrir_url("o LinkedIn", "https://www.linkedin.com/")

    def _abrir_instagram(self) -> str:
        handle = (Config.INSTAGRAM_HANDLE or "").lstrip("@").strip()
        perfil = f"https://www.instagram.com/{handle}/" if handle else "https://www.instagram.com/"

        app_ids = [
            Config.INSTAGRAM_APP_ID,
            "Facebook.Instagram_8xx8rvfyw5nnt!App",
            "Facebook.Instagram_8xx8rvfyw5nnt!Instagram",
            "Facebook.InstagramBeta_8xx8rvfyw5nnt!App",
            "Facebook.InstagramBeta_8xx8rvfyw5nnt!Instagram",
        ]
        for app_id in app_ids:
            if app_id and self._abrir_appsfolder(app_id):
                return "Abrindo o Instagram."

        if handle and self._abrir_protocolo(f"instagram://user?username={handle}"):
            return "Abrindo o Instagram."

        return self._abrir_url("o Instagram", perfil)

    def _abrir_facebook(self) -> str:
        app_ids = [
            Config.FACEBOOK_APP_ID,
            "Facebook.Facebook_8xx8rvfyw5nnt!App",
            "Facebook.Facebook_8xx8rvfyw5nnt!Facebook",
        ]
        for app_id in app_ids:
            if app_id and self._abrir_appsfolder(app_id):
                return "Abrindo o Facebook."

        perfil = (Config.FACEBOOK_PROFILE or "").strip()
        if perfil:
            if perfil.startswith("http"):
                url = perfil
            else:
                url = f"https://www.facebook.com/{perfil}"
        else:
            url = "https://www.facebook.com/"
        return self._abrir_url("o Facebook", url)

    def _abrir_vscode(self) -> str:
        if sys.platform.startswith("win"):
            candidatos = [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Microsoft VS Code/Code.exe",
                Path(os.environ.get("ProgramFiles", "")) / "Microsoft VS Code/Code.exe",
                Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft VS Code/Code.exe",
            ]
            for caminho in candidatos:
                if caminho.is_file():
                    try:
                        subprocess.Popen([str(caminho)])
                        return "Abrindo o Visual Studio Code."
                    except Exception as e:
                        logger.error(f"Erro ao abrir VS Code: {e}")
                        break
        return self._abrir_programa("code", "o Visual Studio Code")
