"""Tkinter UI for ARIS."""

import importlib
import math
import random
import sys
import time
import types
import unicodedata
from datetime import datetime
from queue import Queue
from threading import Event, Thread


def _ensure_distutils() -> None:
    """Provide distutils.version for SpeechRecognition on Python 3.12+."""
    if "distutils.version" in sys.modules:
        return

    try:
        distutils_version = importlib.import_module("setuptools._distutils.version")
        LooseVersion = distutils_version.LooseVersion
    except Exception:
        return

    distutils_module = types.ModuleType("distutils")
    version_module = types.ModuleType("distutils.version")
    version_module.LooseVersion = LooseVersion
    distutils_module.version = version_module
    sys.modules.setdefault("distutils", distutils_module)
    sys.modules.setdefault("distutils.version", version_module)


_ensure_distutils()

import pyttsx3
import speech_recognition as sr
import tkinter as tk
from loguru import logger
from tkinter import scrolledtext

from app.config import Config
from app.core.command_processor import CommandProcessor
from app.managers.memory import MemoryManager
from app.managers.notes import NotesManager
from app.services.gemini import GeminiService
from app.services.music import MusicService
from app.services.tts import EdgeTTS
from app.services.weather import WeatherService
from app.utils.dates import format_date_pt_br


def _is_hex_color(value: str) -> bool:
    return isinstance(value, str) and value.startswith("#") and len(value) == 7


def _hex_to_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _adjust_color(value: str, factor: float) -> str:
    if not _is_hex_color(value):
        return value
    r, g, b = _hex_to_rgb(value)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return _rgb_to_hex((r, g, b))


class RoundedButton(tk.Canvas):
    """Custom rounded button with hover/press effects."""

    def __init__(
        self,
        master,
        text,
        command=None,
        width=170,
        height=44,
        radius=16,
        bg="#00D9FF",
        fg="#0A1422",
        font=("Segoe UI", 11, "bold"),
        hover_bg=None,
        press_bg=None,
        disabled_bg=None,
        disabled_fg=None,
        border_color=None,
    ):
        super().__init__(
            master,
            width=width,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=master.cget("bg"),
        )
        self.command = command
        self.state = "normal"
        self.radius = radius
        self.fill_normal = bg
        self.fill_hover = hover_bg or _adjust_color(bg, 1.08)
        self.fill_press = press_bg or _adjust_color(bg, 0.92)
        self.fill_disabled = disabled_bg or _adjust_color(bg, 0.55)
        self.text_normal = fg
        self.text_disabled = disabled_fg or _adjust_color(fg, 0.7)
        self.border_color = border_color or _adjust_color(bg, 0.8)

        self.rect_id = self._create_round_rect(
            2,
            2,
            width - 2,
            height - 2,
            radius,
            fill=self.fill_normal,
            outline=self.border_color,
            width=1,
        )
        self.text_id = self.create_text(
            width / 2,
            height / 2,
            text=text,
            fill=self.text_normal,
            font=font,
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.configure(cursor="hand2")

    def _create_round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _apply(self, fill, text_color):
        self.itemconfig(self.rect_id, fill=fill)
        self.itemconfig(self.text_id, fill=text_color)

    def _on_enter(self, _event):
        if self.state != "normal":
            return
        self._apply(self.fill_hover, self.text_normal)

    def _on_leave(self, _event):
        if self.state != "normal":
            return
        self._apply(self.fill_normal, self.text_normal)

    def _on_press(self, _event):
        if self.state != "normal":
            return
        self._apply(self.fill_press, self.text_normal)

    def _on_release(self, event):
        if self.state != "normal":
            return
        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        self._apply(self.fill_hover if inside else self.fill_normal, self.text_normal)
        if inside and self.command:
            self.command()

    def set_state(self, state: str):
        self.state = state
        if state == "disabled":
            self._apply(self.fill_disabled, self.text_disabled)
            self.configure(cursor="")
        else:
            self._apply(self.fill_normal, self.text_normal)
            self.configure(cursor="hand2")

class ArisApp:
    """Interface gráfica principal"""

    def __init__(self, root):
        self.root = root
        self.root.title("ARIS - AI Assistant")
        self.root.geometry("540x700")
        self.root.resizable(False, False)

        # Cores e estilos
        self.bg_color = "#07121B"
        self.panel_color = "#0B1D2A"
        self.panel_inner = "#0A1724"
        self.border_color = "#123243"
        self.bg_grid = "#0C2333"
        self.bg_trace = "#143A55"
        self.bg_trace_dim = "#0D2A3D"
        self.neon_core = "#06121D"
        self.fg_color = "#2FD2FF"
        self.fg_glow = "#7BE7FF"
        self.text_color = "#E6F2EF"
        self.text_muted = "#91A6B8"
        self.danger_color = "#FF5C5C"
        self.warning_color = "#FFC857"
        self.success_color = "#3DFF9E"
        self.root.configure(bg=self.bg_color)

        self.font_title = ("Segoe UI", 18, "bold")
        self.font_subtitle = ("Segoe UI", 10)
        self.font_status = ("Segoe UI", 10, "bold")
        self.font_body = ("Segoe UI", 10)
        self.font_button = ("Segoe UI", 11, "bold")
        self.font_mono = ("Cascadia Code", 9)

        # Componentes
        self.memory = MemoryManager()
        self.notes = NotesManager(self.memory)
        self.weather = WeatherService()
        self.gemini = GeminiService()
        self.music = MusicService()
        self.processor = CommandProcessor(
            self.memory, self.notes, self.weather, self.gemini, self.music
        )

        # Threading
        self.running = False
        self.shutdown_event = Event()
        self.command_queue = Queue()

        # TTS/STT
        self.engine = None
        self.recognizer = None
        self.edge_tts = None
        self.listen_timeout = 5
        self.listen_phrase_time_limit = 6
        self.ambient_duration = 0.2
        self.confirm_timeout = 3
        self.confirm_phrase_time_limit = 4
        self.confirm_ambient_duration = 0.2
        self.speaking = False
        self.pulse_phase = 0.0
        self.pulse_job = None
        self.arc_angle = 0.0
        self._bg_last_size = (0, 0)
        self.bg_canvas = None
        self.last_no_wake_notice = 0.0
        self.always_active = True
        self.require_confirmation = False

        self._criar_interface()
        self.root.protocol("WM_DELETE_WINDOW", self.fechar)

    def _criar_interface(self):
        """Cria elementos da interface"""
        self.bg_canvas = tk.Canvas(
            self.root, bg=self.bg_color, highlightthickness=0, bd=0
        )
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.root.after(60, self._draw_background)
        self.root.bind("<Configure>", self._on_resize)

        # Header
        header_frame = tk.Frame(self.root, bg=self.bg_color)
        header_frame.pack(pady=(22, 10))

        tk.Label(
            header_frame,
            text="ARIS - AI ASSISTANT",
            bg=self.bg_color,
            fg=self.fg_color,
            font=self.font_title,
        ).pack()

        tk.Label(
            header_frame,
            text="Assistente Pessoal • Comando por Voz",
            bg=self.bg_color,
            fg=self.text_muted,
            font=self.font_subtitle,
        ).pack()

        # Status
        self.status_label = tk.Label(
            self.root,
            text="⚪ Desconectado",
            bg=self.bg_color,
            fg=self.text_muted,
            font=self.font_status,
        )
        self.status_label.pack(pady=(0, 12))

        # Canvas para indicador visual
        visual_frame = tk.Frame(self.root, bg=self.bg_color)
        visual_frame.pack(pady=(0, 16), padx=24)
        self.canvas = tk.Canvas(
            visual_frame, width=210, height=210, bg=self.bg_color, highlightthickness=0
        )
        self.canvas.pack(padx=12, pady=12)

        self.glow_ring = self.canvas.create_oval(
            20, 20, 190, 190, outline=self.fg_glow, width=1
        )
        self.circle = self.canvas.create_oval(
            32, 32, 178, 178, outline=self.fg_color, width=3
        )
        self.inner_circle = self.canvas.create_oval(
            64, 64, 146, 146, fill=self.neon_core, outline=""
        )
        self.pulse_ring = self.canvas.create_oval(
            26, 26, 184, 184, outline=self.fg_glow, width=1, state="hidden"
        )
        self.arc_outer = self.canvas.create_arc(
            16,
            16,
            194,
            194,
            outline=self.fg_glow,
            width=1,
            style=tk.ARC,
            start=20,
            extent=60,
        )
        self.arc_inner = self.canvas.create_arc(
            44,
            44,
            166,
            166,
            outline=self.fg_color,
            width=2,
            style=tk.ARC,
            start=200,
            extent=70,
        )
        self.tick_ids = []
        center = 105
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            r1 = 88
            r2 = 96
            x1 = center + math.cos(rad) * r1
            y1 = center + math.sin(rad) * r1
            x2 = center + math.cos(rad) * r2
            y2 = center + math.sin(rad) * r2
            self.tick_ids.append(
                self.canvas.create_line(
                    x1, y1, x2, y2, fill=self.fg_glow, width=1
                )
            )

        # Log de interações
        log_frame = tk.Frame(
            self.root,
            bg=self.panel_color,
            highlightthickness=1,
            highlightbackground=self.border_color,
        )
        log_frame.pack(pady=(0, 16), padx=24, fill=tk.BOTH, expand=True)

        tk.Label(
            log_frame,
            text="Histórico de Interações:",
            bg=self.panel_color,
            fg=self.text_color,
            font=self.font_body,
        ).pack(anchor=tk.W, padx=12, pady=(10, 6))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            bg=self.panel_inner,
            fg=self.text_color,
            font=self.font_mono,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bd=0,
            relief=tk.FLAT,
            insertbackground=self.text_color,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        # Botões
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(pady=(0, 20))

        self.btn_iniciar = RoundedButton(
            btn_frame,
            text="🚀 Iniciar ARIS",
            command=self.iniciar_assistente,
            width=180,
            height=46,
            radius=18,
            bg=self.fg_color,
            fg=self.bg_color,
            font=self.font_button,
        )
        self.btn_iniciar.pack(side=tk.LEFT, padx=8)

        self.btn_parar = RoundedButton(
            btn_frame,
            text="⏹️ Parar",
            command=self.parar_assistente,
            width=150,
            height=46,
            radius=18,
            bg=self.danger_color,
            fg="#FFFFFF",
            font=self.font_button,
        )
        self.btn_parar.set_state("disabled")
        self.btn_parar.pack(side=tk.LEFT, padx=8)

    def _on_resize(self, _event):
        self._draw_background()

    def _draw_background(self):
        if not self.bg_canvas:
            return

        width = self.root.winfo_width() or 540
        height = self.root.winfo_height() or 700
        if (width, height) == self._bg_last_size:
            return
        self._bg_last_size = (width, height)

        self.bg_canvas.delete("bg")

        for y in range(40, height, 90):
            self.bg_canvas.create_line(
                0, y, width, y, fill=self.bg_grid, width=1, tags="bg"
            )
        for x in range(30, width, 120):
            self.bg_canvas.create_line(
                x, 0, x, height, fill=self.bg_grid, width=1, tags="bg"
            )

        for offset in range(-width, width, 160):
            self.bg_canvas.create_line(
                offset,
                int(height * 0.15),
                offset + width,
                int(height * 0.85),
                fill=self.bg_trace_dim,
                width=1,
                tags="bg",
            )

        cx = width / 2
        cy = int(height * 0.32)
        for radius in (90, 120, 150, 180):
            self.bg_canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                outline=self.bg_trace_dim,
                width=1,
                tags="bg",
            )

        for angle in range(0, 360, 45):
            self.bg_canvas.create_arc(
                cx - 175,
                cy - 175,
                cx + 175,
                cy + 175,
                start=angle,
                extent=20,
                style=tk.ARC,
                outline=self.bg_trace,
                width=1,
                tags="bg",
            )

        for angle in range(0, 360, 20):
            rad = math.radians(angle)
            r1 = 190
            r2 = 200
            x1 = cx + math.cos(rad) * r1
            y1 = cy + math.sin(rad) * r1
            x2 = cx + math.cos(rad) * r2
            y2 = cy + math.sin(rad) * r2
            self.bg_canvas.create_line(
                x1, y1, x2, y2, fill=self.bg_trace, width=1, tags="bg"
            )

        for y in range(int(height * 0.55), height, 80):
            self.bg_canvas.create_line(
                20, y, width - 20, y, fill=self.bg_trace_dim, width=1, tags="bg"
            )

        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            r = 145
            x = cx + math.cos(rad) * r
            y = cy + math.sin(rad) * r
            self.bg_canvas.create_oval(
                x - 2, y - 2, x + 2, y + 2, fill=self.bg_trace, outline="", tags="bg"
            )

    def log(self, mensagem: str, tipo: str = "info"):
        """Adiciona mensagem ao log visual"""
        self.log_text.config(state=tk.NORMAL)

        timestamp = datetime.now().strftime("%H:%M:%S")
        cor_tag = {
            "info": self.text_muted,
            "user": "#9FE870",
            "aris": self.fg_color,
            "error": self.danger_color,
            "warn": self.warning_color,
        }.get(tipo, self.text_color)

        tag_name = f"tag_{tipo}"
        self.log_text.tag_config(tag_name, foreground=cor_tag)
        self.log_text.tag_config("time", foreground=self.text_muted)
        self.log_text.insert(tk.END, f"[{timestamp}] ", "time")
        self.log_text.insert(tk.END, f"{mensagem}\n", tag_name)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def mudar_status(self, texto: str, cor: str = None):
        """Atualiza status"""
        self.status_label.config(text=texto)
        if cor:
            self.status_label.config(fg=cor)

    def mudar_cor_circulo(self, cor: str):
        """Muda cor do indicador"""
        self.canvas.itemconfig(self.circle, outline=cor)
        self.canvas.itemconfig(self.glow_ring, outline=_adjust_color(cor, 1.15))
        self.canvas.itemconfig(self.arc_outer, outline=_adjust_color(cor, 1.35))
        self.canvas.itemconfig(self.arc_inner, outline=cor)
        self.canvas.itemconfig(self.pulse_ring, outline=_adjust_color(cor, 1.4))

    def _start_speaking_animation(self):
        if self.speaking:
            return
        self.speaking = True
        self.pulse_phase = 0.0
        self.canvas.itemconfig(self.pulse_ring, state="normal")
        self._animate_speaking()

    def _stop_speaking_animation(self):
        if not self.speaking:
            return
        self.speaking = False
        if self.pulse_job:
            try:
                self.root.after_cancel(self.pulse_job)
            except Exception:
                pass
            self.pulse_job = None
        self.canvas.itemconfig(self.pulse_ring, state="hidden")
        self.canvas.itemconfig(self.circle, width=6)
        self.canvas.itemconfig(self.glow_ring, width=2)
        self.mudar_cor_circulo(self.fg_color)

    def _animate_speaking(self):
        if not self.speaking:
            return

        size = max(self.canvas.winfo_width(), self.canvas.winfo_height(), 210)
        center = size / 2
        base = size * 0.36
        amplitude = size * 0.05

        self.pulse_phase += 0.35
        pulse = (math.sin(self.pulse_phase) + 1) / 2
        radius = base + amplitude * pulse

        self.arc_angle = (self.arc_angle + 7) % 360
        self.canvas.itemconfig(self.arc_outer, start=self.arc_angle)
        self.canvas.itemconfig(self.arc_inner, start=(self.arc_angle * 1.7) % 360)

        self.canvas.coords(
            self.pulse_ring,
            center - radius,
            center - radius,
            center + radius,
            center + radius,
        )
        glow = _adjust_color(self.fg_glow, 0.9 + 0.3 * pulse)
        self.canvas.itemconfig(
            self.pulse_ring, width=1 + int(3 * pulse), outline=glow
        )
        self.canvas.itemconfig(self.circle, width=3 + int(2 * pulse))
        self.canvas.itemconfig(self.glow_ring, width=1 + int(1 * pulse), outline=glow)
        self.canvas.itemconfig(self.arc_outer, width=1 + int(1 * pulse), outline=glow)
        self.canvas.itemconfig(self.arc_inner, width=2 + int(1 * pulse))
        self.pulse_job = self.root.after(50, self._animate_speaking)

    def _extrair_comando_frase(self, frase: str) -> str:
        texto = self._normalizar_texto(frase)
        for wake in ("aris", "aries"):
            texto = texto.replace(wake, " ")
        texto = texto.strip(" ,.!?:;")
        texto = " ".join(texto.split())

        ignorar = {
            "oi",
            "ola",
            "olá",
            "e ai",
            "e aí",
            "tudo bem",
            "bom dia",
            "boa tarde",
            "boa noite",
        }
        if texto in ignorar:
            return ""
        return texto

    def _tem_wake_word(self, frase: str) -> bool:
        texto = self._normalizar_texto(frase)
        tokens = texto.replace(",", " ").replace(".", " ").split()
        return any(token in ("aris", "aries") for token in tokens)

    def _parece_comando(self, frase: str) -> bool:
        texto = self._normalizar_texto(frase)
        gatilhos = [
            "abrir",
            "temperatura",
            "previsao",
            "previsao do tempo",
            "tocar",
            "playlist",
            "anotar",
            "registrar",
            "historico",
            "resumo",
            "ajuda",
            "que horas",
            "que dia",
            "modo privado",
            "pesquisar",
            "perguntar",
        ]
        return any(gatilho in texto for gatilho in gatilhos)

    def _eh_confirmacao(self, resposta: str) -> bool:
        texto = resposta.lower()
        gatilhos = [
            "sim",
            "confirmar",
            "confirmo",
            "pode",
            "ok",
            "certo",
            "isso",
            "afirmativo",
            "vai",
        ]
        return any(gatilho in texto for gatilho in gatilhos)

    def _eh_negacao(self, resposta: str) -> bool:
        texto = resposta.lower()
        gatilhos = ["não", "nao", "negativo", "cancela", "cancelar"]
        return any(gatilho in texto for gatilho in gatilhos)

    def _confirmar_comando(self, comando: str, falar, ouvir) -> bool:
        falar(f"Confirmar comando: {comando}?")
        resposta = ouvir(
            timeout=self.confirm_timeout,
            phrase_time_limit=self.confirm_phrase_time_limit,
            ambient_duration=self.confirm_ambient_duration,
        )
        if not resposta:
            falar("Não ouvi a confirmação. Comando cancelado.")
            return False
        if self._eh_confirmacao(resposta):
            falar("Confirmado. Executando.")
            return True
        if self._eh_negacao(resposta):
            falar("Comando cancelado.")
            return False
        falar("Não entendi. Comando cancelado.")
        return False

    def _normalizar_idiomas(self, voice) -> str:
        idiomas = []
        for lang in getattr(voice, "languages", []) or []:
            if isinstance(lang, bytes):
                try:
                    lang = lang.decode(errors="ignore")
                except Exception:
                    lang = str(lang)
            idiomas.append(str(lang).lower())
        return " ".join(idiomas)

    def _normalizar_texto(self, valor: str) -> str:
        texto = (valor or "").lower()
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
        return " ".join(texto.split())

    def _sanitizar_fala(self, texto: str) -> str:
        if not texto:
            return ""
        filtrado = []
        for ch in texto:
            categoria = unicodedata.category(ch)
            if categoria.startswith("So") or categoria.startswith("Sk"):
                continue
            filtrado.append(ch)
        return " ".join("".join(filtrado).split())

    def _selecionar_voz_por_nome(self, voices, nome: str):
        alvo = self._normalizar_texto(nome)
        for voice in voices:
            voice_name = self._normalizar_texto(voice.name or "")
            voice_id = self._normalizar_texto(voice.id or "")
            if alvo in voice_name or alvo in voice_id:
                return voice
        return None

    def _selecionar_voz(self, voices):
        melhor = None
        melhor_score = -999
        nomes_masculinos = {
            "daniel",
            "antonio",
            "thiago",
            "felipe",
            "ricardo",
            "paulo",
            "joao",
            "miguel",
            "bruno",
            "lucas",
            "david",
            "mark",
        }
        nomes_femininos = {"zira", "helia", "female", "mulher"}

        for voice in voices:
            name = self._normalizar_texto(voice.name or "")
            voice_id = self._normalizar_texto(voice.id or "")
            idiomas = self._normalizar_idiomas(voice)
            score = 0

            if "pt" in idiomas or "portuguese" in name or "portuguese" in voice_id:
                score += 3
            if "brazil" in name or "brazil" in voice_id or "pt-br" in idiomas:
                score += 2
            if any(nome in name for nome in nomes_masculinos):
                score += 2
            if "male" in name:
                score += 1
            if any(nome in name for nome in nomes_femininos):
                score -= 2

            if score > melhor_score:
                melhor_score = score
                melhor = voice

        return melhor

    def _configurar_voz(self):
        try:
            voices = self.engine.getProperty("voices") or []
        except Exception as e:
            logger.warning(f"Não foi possível carregar vozes: {e}")
            return
        voz = self._selecionar_voz_por_nome(voices, "antonio")
        if not voz:
            nomes_disponiveis = ", ".join(
                sorted({voice.name for voice in voices if voice.name})
            )
            logger.warning(
                f"Voz 'Antonio' não encontrada. Disponíveis: {nomes_disponiveis or 'nenhuma'}"
            )
            voz = self._selecionar_voz(voices)

        if not voz:
            logger.info("Mantendo voz padrão do sistema.")
            return
        try:
            self.engine.setProperty("voice", voz.id)
            logger.info(f"Voz selecionada: {voz.name}")
        except Exception as e:
            logger.warning(f"Erro ao definir voz: {e}")

    def iniciar_assistente(self):
        """Inicia o assistente"""
        if not self.running:
            self.running = True
            self.shutdown_event.clear()
            self.btn_iniciar.set_state("disabled")
            self.btn_parar.set_state("normal")

            thread = Thread(target=self.executar_assistente, daemon=True)
            thread.start()

            self.mudar_status("🟢 Online", self.success_color)
            self.log("ARIS iniciado com sucesso!", "info")
            logger.info("Assistente iniciado")

    def parar_assistente(self):
        """Para o assistente"""
        self.running = False
        self.shutdown_event.set()
        self.btn_iniciar.set_state("normal")
        self.btn_parar.set_state("disabled")
        self.mudar_status("🔴 Offline", self.danger_color)
        self._stop_speaking_animation()
        self.log("ARIS desligado", "warn")
        self.memory.salvar_memoria()
        logger.info("Assistente parado")

    def fechar(self):
        """Fecha aplicação"""
        if self.running:
            self.parar_assistente()
        else:
            self._stop_speaking_animation()
        self.root.destroy()

    def executar_assistente(self):
        """Loop principal do assistente"""
        try:
            # Inicializa TTS e STT
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 180)
            if Config.TTS_ENGINE.lower() == "edge":
                self.edge_tts = EdgeTTS(
                    voice=Config.EDGE_TTS_VOICE,
                    rate=Config.EDGE_TTS_RATE,
                    pitch=Config.EDGE_TTS_PITCH,
                    volume=Config.EDGE_TTS_VOLUME,
                    echo_delay_ms=Config.EDGE_TTS_ECHO_DELAY_MS,
                    echo_volume=Config.EDGE_TTS_ECHO_VOLUME,
                    echo2_delay_ms=Config.EDGE_TTS_ECHO2_DELAY_MS,
                    echo2_volume=Config.EDGE_TTS_ECHO2_VOLUME,
                )
                if not self.edge_tts.is_ready():
                    logger.warning("Edge TTS indisponivel. Usando voz do sistema.")
                    self.edge_tts = None
                    self._configurar_voz()
                else:
                    logger.info(f"Edge TTS ativo: {Config.EDGE_TTS_VOICE}")
            else:
                self._configurar_voz()
            self.recognizer = sr.Recognizer()
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.5
            self.recognizer.phrase_threshold = 0.3
            self.recognizer.non_speaking_duration = 0.3
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
            self.ambient_duration = 0.0

            def falar(texto):
                """Fala texto"""
                try:
                    texto_fala = self._sanitizar_fala(texto)
                    if not texto_fala:
                        return
                    self.mudar_cor_circulo(self.fg_color)
                    self._start_speaking_animation()
                    self.log(f"ARIS: {texto}", "aris")
                    if self.edge_tts and self.edge_tts.speak(texto_fala):
                        return
                    self.engine.say(texto_fala)
                    self.engine.runAndWait()
                except Exception as e:
                    logger.error(f"Erro TTS: {e}")
                finally:
                    self._stop_speaking_animation()
                    self.mudar_cor_circulo(self.fg_color)

            def ouvir(timeout=None, phrase_time_limit=None, ambient_duration=None):
                """Ouve comando"""
                try:
                    timeout = self.listen_timeout if timeout is None else timeout
                    phrase_time_limit = (
                        self.listen_phrase_time_limit
                        if phrase_time_limit is None
                        else phrase_time_limit
                    )
                    ambient_duration = (
                        self.ambient_duration
                        if ambient_duration is None
                        else ambient_duration
                    )
                    self.mudar_cor_circulo(self.warning_color)
                    with sr.Microphone() as source:
                        if ambient_duration and ambient_duration > 0:
                            self.recognizer.adjust_for_ambient_noise(
                                source, duration=ambient_duration
                            )
                        audio = self.recognizer.listen(
                            source,
                            timeout=timeout,
                            phrase_time_limit=phrase_time_limit,
                        )

                    self.mudar_cor_circulo(self.fg_glow)
                    comando = self.recognizer.recognize_google(
                        audio, language="pt-BR"
                    ).lower()
                    self.log(f"Você: {comando}", "user")
                    logger.info(f"Comando ouvido: {comando}")
                    self.mudar_cor_circulo(self.fg_color)
                    return comando

                except sr.WaitTimeoutError:
                    logger.debug("Timeout ao ouvir")
                    self.mudar_cor_circulo(self.fg_color)
                    return ""
                except sr.UnknownValueError:
                    logger.debug("Não entendeu o áudio")
                    self.mudar_cor_circulo(self.fg_color)
                    return ""
                except sr.RequestError as e:
                    logger.error(f"Erro API Speech Recognition: {e}")
                    self.mudar_cor_circulo(self.danger_color)
                    return ""
                except Exception as e:
                    logger.error(f"Erro ao ouvir: {e}")
                    self.mudar_cor_circulo(self.danger_color)
                    return ""

            # Saudação inicial
            hora = datetime.now().hour
            saudacao = (
                "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
            )

            clima_msg = ""
            if Config.OPENWEATHER_KEY:
                clima_msg = self.weather.obter_temperatura(Config.CIDADE_PADRAO)

            data_atual = format_date_pt_br(datetime.now())
            hora_atual = datetime.now().strftime("%H:%M")

            msg_inicial = (
                f"{saudacao} Douglas, tudo bem! Hoje é {data_atual}, são {hora_atual} minutos. {clima_msg} "
                "Meu nome é ÀRIS, seu assistente de IA. Estou pronto para ajudar, senhor."
            )
            falar(msg_inicial)

            # Loop principal
            while self.running and not self.shutdown_event.is_set():
                frase = ouvir()

                if not frase:
                    continue

                texto_norm = self._normalizar_texto(frase)
                if self.always_active:
                    if texto_norm in ("aris", "aries"):
                        respostas = [
                            "Sim, senhor?",
                            "Às ordens.",
                            "Estou aqui.",
                            "Pronto para ajudar.",
                            "Como posso ajudar?",
                        ]
                        falar(random.choice(respostas))
                        comando = ouvir()
                        if not comando:
                            falar("Não consegui entender o comando senhor.")
                            continue
                    else:
                        comando = frase

                    if any(
                        x in comando
                        for x in ["desligar", "encerrar", "sair", "tchau"]
                    ):
                        falar("Encerrando o sistema. Até mais senhor.")
                        self.parar_assistente()
                        break

                    if self.require_confirmation and self._parece_comando(comando):
                        self.mudar_status("🟡 Confirmar comando...", self.warning_color)
                        if not self._confirmar_comando(comando, falar, ouvir):
                            self.mudar_status("🟢 Online", self.success_color)
                            continue

                    resposta_texto = self.processor.processar(comando, falar, ouvir)
                    if resposta_texto:
                        falar(resposta_texto)
                        self.memory.registrar(comando, resposta_texto)

                    self.mudar_status("🟢 Online", self.success_color)
                    continue

                # Wake word (modo antigo)
                if self._tem_wake_word(frase):
                    comando_inline = self._extrair_comando_frase(frase)
                    if comando_inline:
                        self.mudar_status("🟡 Confirmar comando...", self.warning_color)
                        if self._confirmar_comando(comando_inline, falar, ouvir):
                            resposta_texto = self.processor.processar(
                                comando_inline, falar, ouvir
                            )
                            if resposta_texto:
                                falar(resposta_texto)
                                self.memory.registrar(comando_inline, resposta_texto)
                        self.mudar_status("🟢 Online", self.success_color)
                        continue

                    respostas = [
                        "Sim, senhor?",
                        "Às ordens.",
                        "Estou aqui.",
                        "Pronto para ajudar.",
                        "Como posso ajudar?",
                    ]
                    resp = random.choice(respostas)
                    falar(resp)

                    self.mudar_status("🟡 Aguardando comando...", self.warning_color)
                    comando = ouvir()

                    if not comando:
                        falar("Não consegui entender o comando senhor.")
                        self.mudar_status("🟢 Online", self.success_color)
                        continue

                    # Comando de desligamento
                    if any(
                        x in comando for x in ["desligar", "encerrar", "sair", "tchau"]
                    ):
                        falar("Encerrando o sistema. Até mais senhor.")
                        self.parar_assistente()
                        break

                    # Processa comando
                    resposta_texto = self.processor.processar(comando, falar, ouvir)

                    if resposta_texto:
                        falar(resposta_texto)
                        self.memory.registrar(comando, resposta_texto)

                    self.mudar_status("🟢 Online", self.success_color)
                elif self._parece_comando(frase):
                    agora = time.time()
                    if agora - self.last_no_wake_notice > 10:
                        falar("Diga 'Aris' antes do comando senhor.")
                        self.last_no_wake_notice = agora

        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            self.log(f"Erro crítico: {e}", "error")
            self.parar_assistente()

        finally:
            self.memory.salvar_memoria()
