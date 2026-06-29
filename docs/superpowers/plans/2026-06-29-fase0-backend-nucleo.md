# Fase 0 — Backend Headless (Núcleo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir o núcleo headless do ARIS — um motor que recebe um comando em texto, roteia para uma skill ou para o LLM, e responde — exposto por WebSocket, sem nenhuma dependência de UI.

**Architecture:** Pacote Python `backend/aris/` com camadas isoladas: `core` (Context/Skill/Registry/Orchestrator), `llm` (provider trocável Gemini/Ollama), `memory` (curto prazo), `skills` (uma skill = um arquivo) e `api` (gateway WebSocket FastAPI). O frontend e a voz serão clientes do mesmo gateway em planos posteriores. A skill `datetime` é migrada aqui como fatia vertical de prova.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, pydantic-settings, google-generativeai, requests, loguru, pytest, ruff, black, mypy.

## Global Constraints

- Todo arquivo Python começa com docstring de módulo explicando sua responsabilidade (preferência do usuário: código comentado para manutenção futura).
- Respostas do ARIS em PT-BR, persona "ÁRIS", trata o usuário por "senhor", máx. 40 palavras no LLM.
- `LLMProvider` trocável por env `ARIS_LLM_PROVIDER` (`gemini` | `ollama`); padrão `gemini`.
- Nenhum segredo no código. Existe **UM único `.env`, na raiz do repositório** (já no `.gitignore`); o backend o lê via `ROOT_DIR / ".env"`. Não criar `.env` dentro de `backend/`.
- Nenhuma rede/áudio real em teste — Gemini, Ollama e voz são sempre mockados.
- Backend mora em `backend/`; não editar o `app/` legado (será aposentado depois).
- Todos os comandos rodam a partir de `backend/` salvo indicação contrária.

---

### Task 1: Scaffolding do backend + configuração tipada

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/aris/__init__.py`
- Create: `backend/aris/config.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_config.py`

**Interfaces:**
- Produces: `aris.config.Settings` (classe pydantic-settings) e instância `settings`. Campos usados adiante: `gemini_key: str`, `openweather_key: str`, `aris_llm_provider: str`, `ollama_base_url: str`, `ollama_model: str`, `cidade_padrao: str`, `max_memoria: int`, `arquivo_memoria: Path`.

- [ ] **Step 1: Criar `backend/pyproject.toml`**

```toml
[project]
name = "aris-backend"
version = "0.1.0"
description = "ARIS — núcleo headless do assistente de voz"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "pydantic-settings>=2.2",
    "google-generativeai>=0.8",
    "requests>=2.31",
    "loguru>=0.7",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.4", "black>=24.0", "mypy>=1.9", "httpx>=0.27"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.black]
line-length = 100

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 2: Escrever o teste que falha**

`backend/tests/test_config.py`:

```python
"""Testa o carregamento de configuração tipada."""

from aris.config import Settings


def test_settings_defaults():
    s = Settings(_env_file=None)
    assert s.aris_llm_provider == "gemini"
    assert s.ollama_base_url == "http://localhost:11434"
    assert s.cidade_padrao == "São Paulo"
    assert s.max_memoria == 20


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("ARIS_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("GEMINI_KEY", "abc123")
    s = Settings(_env_file=None)
    assert s.aris_llm_provider == "ollama"
    assert s.gemini_key == "abc123"
```

- [ ] **Step 3: Rodar o teste e ver falhar**

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'aris.config'`

- [ ] **Step 4: Criar os arquivos de pacote**

`backend/aris/__init__.py`:

```python
"""ARIS — núcleo headless do assistente."""
```

`backend/tests/__init__.py`:

```python
```

`backend/aris/config.py`:

```python
"""Configuração central do ARIS, carregada de variáveis de ambiente (.env).

Substitui a antiga classe Config baseada em os.getenv por pydantic-settings,
que valida tipos e centraliza os valores padrão num único lugar.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py vive em backend/aris/ → BACKEND_DIR = backend/, ROOT_DIR = raiz do repo.
# Há UM único .env, na raiz do repositório (com as secrets), compartilhado pelo backend.
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Todas as configurações do ARIS. Nomes de campo casam com env vars (case-insensitive)."""

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    # APIs externas
    gemini_key: str = ""
    openweather_key: str = ""

    # Motor de raciocínio (LLM)
    aris_llm_provider: str = "gemini"  # "gemini" | "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Localização
    cidade_padrao: str = "São Paulo"

    # Memória
    max_memoria: int = 20
    arquivo_memoria: Path = BACKEND_DIR / "data" / "memoria.json"


settings = Settings()
```

- [ ] **Step 5: Rodar o teste e ver passar**

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/aris/__init__.py backend/aris/config.py backend/tests/
git commit -m "feat(backend): scaffold + configuração tipada com pydantic-settings"
```

---

### Task 2: Núcleo — Context, Skill (Protocol) e Registry

**Files:**
- Create: `backend/aris/core/__init__.py`
- Create: `backend/aris/core/context.py`
- Create: `backend/aris/core/skill.py`
- Create: `backend/aris/core/registry.py`
- Create: `backend/tests/test_registry.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `Context` (dataclass): `speak: Callable[[str], None]`, `listen: Callable[..., str]`, `entities: dict`, `private_mode: bool`.
  - `Skill` (Protocol): atributo `name: str`; métodos `matches(text: str, ctx: Context) -> bool` e `handle(text: str, ctx: Context) -> str`.
  - `Registry`: `register(skill: Skill) -> None`, `resolve(text: str, ctx: Context) -> Skill | None` (primeira skill cuja `matches` retorna True, na ordem de registro).

- [ ] **Step 1: Escrever o teste que falha**

`backend/tests/test_registry.py`:

```python
"""Testa o registro e a resolução de skills por prioridade de ordem."""

from dataclasses import dataclass

from aris.core.context import Context
from aris.core.registry import Registry


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


@dataclass
class _FakeSkill:
    name: str
    keyword: str

    def matches(self, text: str, ctx: Context) -> bool:
        return self.keyword in text

    def handle(self, text: str, ctx: Context) -> str:
        return f"{self.name} executou"


def test_resolve_returns_matching_skill():
    reg = Registry()
    reg.register(_FakeSkill("clima", "tempo"))
    assert reg.resolve("como esta o tempo", _ctx()).name == "clima"


def test_resolve_respects_registration_order():
    reg = Registry()
    reg.register(_FakeSkill("primeira", "abrir"))
    reg.register(_FakeSkill("segunda", "abrir"))
    assert reg.resolve("abrir algo", _ctx()).name == "primeira"


def test_resolve_returns_none_when_no_match():
    reg = Registry()
    reg.register(_FakeSkill("clima", "tempo"))
    assert reg.resolve("qualquer coisa", _ctx()) is None
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && python -m pytest tests/test_registry.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'aris.core'`

- [ ] **Step 3: Implementar o núcleo**

`backend/aris/core/__init__.py`:

```python
"""Núcleo do ARIS: contexto de conversa, contrato de skill, registro e orquestração."""
```

`backend/aris/core/context.py`:

```python
"""Context — estado de uma interação, repassado a cada skill.

Carrega os callbacks de voz (speak/listen) para que skills que precisam de
diálogo ("de qual cidade?") funcionem sem conhecer a UI, além de entidades
extraídas e o flag de modo privado.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Context:
    """Contexto de uma única interação com o ARIS."""

    speak: Callable[[str], None]
    listen: Callable[..., str]
    entities: dict[str, Any] = field(default_factory=dict)
    private_mode: bool = False
```

`backend/aris/core/skill.py`:

```python
"""Skill — o contrato que toda habilidade do ARIS implementa.

Substitui a cadeia if/elif do antigo CommandProcessor: cada habilidade vira
uma classe isolada que diz se reconhece o texto (matches) e o executa (handle).
"""

from typing import Protocol, runtime_checkable

from aris.core.context import Context


@runtime_checkable
class Skill(Protocol):
    """Toda skill tem um nome e sabe reconhecer e tratar um comando."""

    name: str

    def matches(self, text: str, ctx: Context) -> bool:
        """Retorna True se esta skill deve tratar o texto."""
        ...

    def handle(self, text: str, ctx: Context) -> str:
        """Executa a ação e retorna a resposta falada ao usuário."""
        ...
```

`backend/aris/core/registry.py`:

```python
"""Registry — guarda as skills e resolve qual trata cada comando.

A ordem de registro define a prioridade: a primeira skill cujo matches()
retorna True vence. Skills mais específicas devem ser registradas antes.
"""

from aris.core.context import Context
from aris.core.skill import Skill


class Registry:
    """Coleção ordenada de skills com resolução por prioridade."""

    def __init__(self) -> None:
        self._skills: list[Skill] = []

    def register(self, skill: Skill) -> None:
        """Adiciona uma skill ao fim da lista (menor prioridade que as anteriores)."""
        self._skills.append(skill)

    def resolve(self, text: str, ctx: Context) -> Skill | None:
        """Retorna a primeira skill que reconhece o texto, ou None."""
        for skill in self._skills:
            if skill.matches(text, ctx):
                return skill
        return None
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd backend && python -m pytest tests/test_registry.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/aris/core/ backend/tests/test_registry.py
git commit -m "feat(core): Context, Skill Protocol e Registry"
```

---

### Task 3: Camada LLM — prompt da persona, provider Gemini e Ollama

**Files:**
- Create: `backend/aris/llm/__init__.py`
- Create: `backend/aris/llm/base.py`
- Create: `backend/aris/llm/gemini_provider.py`
- Create: `backend/aris/llm/ollama_provider.py`
- Create: `backend/aris/llm/factory.py`
- Create: `backend/tests/test_llm.py`

**Interfaces:**
- Consumes: `aris.core.context.Context`, `aris.config.Settings`.
- Produces:
  - `PERSONA: str` (texto da persona ÁRIS).
  - `build_prompt(persona: str, memory_context: str, question: str) -> str`.
  - `LLMProvider` (Protocol): `generate(prompt: str, ctx: Context) -> str`.
  - `GeminiProvider(api_key: str, model: str = "gemini-2.0-flash-exp")`.
  - `OllamaProvider(base_url: str, model: str)`.
  - `build_provider(settings: Settings) -> LLMProvider`.

- [ ] **Step 1: Escrever o teste que falha**

`backend/tests/test_llm.py`:

```python
"""Testa a montagem do prompt e o provider Ollama (HTTP mockado)."""

from aris.core.context import Context
from aris.llm.base import build_prompt
from aris.llm.ollama_provider import OllamaProvider


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


def test_build_prompt_inclui_memoria_quando_existe():
    prompt = build_prompt("PERSONA", "memoria recente", "que horas sao")
    assert "PERSONA" in prompt
    assert "memoria recente" in prompt
    assert "que horas sao" in prompt


def test_build_prompt_omite_memoria_quando_vazia():
    prompt = build_prompt("PERSONA", "", "ola")
    assert "Histórico" not in prompt


def test_ollama_generate(monkeypatch):
    class _FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"response": "  resposta do modelo  "}

    captured = {}

    def _fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _FakeResp()

    monkeypatch.setattr("aris.llm.ollama_provider.requests.post", _fake_post)
    provider = OllamaProvider("http://localhost:11434", "llama3.1")
    out = provider.generate("meu prompt", _ctx())
    assert out == "resposta do modelo"
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["json"]["model"] == "llama3.1"
    assert captured["json"]["stream"] is False
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && python -m pytest tests/test_llm.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'aris.llm'`

- [ ] **Step 3: Implementar a camada LLM**

`backend/aris/llm/__init__.py`:

```python
"""Camada de LLM: provider trocável (Gemini nuvem / Ollama local) e prompt da persona."""
```

`backend/aris/llm/base.py`:

```python
"""Contrato comum dos providers de LLM e a montagem do prompt da persona.

A persona do ÁRIS fica centralizada aqui (antes estava espalhada em strings),
e build_prompt injeta a memória de curto prazo no contexto do modelo.
"""

from typing import Protocol

from aris.core.context import Context

PERSONA = (
    "Você é o ÁRIS, assistente de IA pessoal avançado.\n"
    "- Seja direto, educado e profissional.\n"
    "- Use no máximo 40 palavras.\n"
    '- Trate o usuário por "senhor".\n'
    "- Se não souber, admita."
)


class LLMProvider(Protocol):
    """Qualquer motor de raciocínio que gere texto a partir de um prompt."""

    def generate(self, prompt: str, ctx: Context) -> str:
        """Gera a resposta do ARIS para o prompt fornecido."""
        ...


def build_prompt(persona: str, memory_context: str, question: str) -> str:
    """Monta o prompt final: persona + (histórico, se houver) + pergunta."""
    parts = [persona]
    if memory_context:
        parts.append(f"Histórico recente:\n{memory_context}")
    parts.append(f"Pergunta: {question}")
    return "\n\n".join(parts)
```

`backend/aris/llm/gemini_provider.py`:

```python
"""Provider de LLM usando Google Gemini (nuvem)."""

import google.generativeai as genai
from loguru import logger

from aris.core.context import Context


class GeminiProvider:
    """Raciocínio via Gemini, mantendo uma sessão de chat por execução."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp") -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self._chat = self._model.start_chat(history=[])

    def generate(self, prompt: str, ctx: Context) -> str:
        """Envia o prompt ao Gemini e retorna o texto da resposta."""
        try:
            resposta = self._chat.send_message(prompt)
            return resposta.text
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro Gemini: {exc}")
            return "Desculpe, não consegui processar sua pergunta no momento."
```

`backend/aris/llm/ollama_provider.py`:

```python
"""Provider de LLM usando um modelo local via Ollama (http://localhost:11434)."""

import requests
from loguru import logger

from aris.core.context import Context


class OllamaProvider:
    """Raciocínio via Ollama local, sem custo nem dependência de nuvem."""

    def __init__(self, base_url: str, model: str) -> None:
        self._url = base_url.rstrip("/") + "/api/generate"
        self._model = model

    def generate(self, prompt: str, ctx: Context) -> str:
        """Chama a API do Ollama e retorna o texto gerado."""
        try:
            resp = requests.post(
                self._url,
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["response"].strip()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro Ollama: {exc}")
            return "Desculpe, o modelo local não respondeu, senhor."
```

`backend/aris/llm/factory.py`:

```python
"""Fábrica que escolhe o provider de LLM conforme a configuração."""

from aris.config import Settings
from aris.llm.base import LLMProvider
from aris.llm.gemini_provider import GeminiProvider
from aris.llm.ollama_provider import OllamaProvider


def build_provider(settings: Settings) -> LLMProvider:
    """Retorna GeminiProvider ou OllamaProvider conforme settings.aris_llm_provider."""
    if settings.aris_llm_provider == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    return GeminiProvider(settings.gemini_key)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd backend && python -m pytest tests/test_llm.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/aris/llm/ backend/tests/test_llm.py
git commit -m "feat(llm): persona, build_prompt e providers Gemini/Ollama trocáveis"
```

---

### Task 4: Memória de curto prazo (porta do MemoryManager)

**Files:**
- Create: `backend/aris/memory/__init__.py`
- Create: `backend/aris/memory/short_term.py`
- Create: `backend/tests/test_memory.py`

**Interfaces:**
- Consumes: `aris.config.Settings`.
- Produces: `ShortTermMemory(max_items: int, arquivo: Path)` com:
  - `registrar(entrada: str, resposta: str) -> None`
  - `as_prompt_context() -> str` (linhas recentes p/ injetar no LLM)
  - `obter_resumo() -> str`
  - `private_mode: bool` (quando True, não registra nem persiste)
  - `salvar() -> None`, `carregar() -> None`

- [ ] **Step 1: Escrever o teste que falha**

`backend/tests/test_memory.py`:

```python
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && python -m pytest tests/test_memory.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'aris.memory'`

- [ ] **Step 3: Implementar a memória**

`backend/aris/memory/__init__.py`:

```python
"""Memória do ARIS. Fase 0: curto prazo. Fase 1 adiciona memória vetorial (ChromaDB)."""
```

`backend/aris/memory/short_term.py`:

```python
"""Memória de curto prazo — histórico recente da sessão, persistido em JSON.

Porta o antigo MemoryManager e adiciona as_prompt_context(), que entrega o
histórico já formatado para o Orchestrator injetar no prompt do LLM (antes a
memória era persistida mas nunca realimentava o raciocínio).
"""

import json
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock

from loguru import logger


class ShortTermMemory:
    """Histórico circular thread-safe das últimas interações."""

    def __init__(self, max_items: int, arquivo: Path) -> None:
        self._max = max_items
        self._arquivo = Path(arquivo)
        self._itens: deque[dict[str, str]] = deque(maxlen=max_items)
        self._lock = Lock()
        self.private_mode = False
        self.carregar()

    def registrar(self, entrada: str, resposta: str) -> None:
        """Registra uma interação, exceto em modo privado."""
        if self.private_mode:
            return
        with self._lock:
            self._itens.append(
                {
                    "hora": datetime.now().strftime("%H:%M"),
                    "entrada": entrada,
                    "resposta": resposta,
                }
            )

    def as_prompt_context(self) -> str:
        """Retorna o histórico recente formatado para injeção no prompt do LLM."""
        with self._lock:
            if not self._itens:
                return ""
            return "\n".join(
                f"[{m['hora']}] Usuário: {m['entrada']} | ÁRIS: {m['resposta']}"
                for m in self._itens
            )

    def obter_resumo(self) -> str:
        """Resumo legível para quando o usuário pede 'o que falamos'."""
        contexto = self.as_prompt_context()
        if not contexto:
            return "Ainda não tenho registros recentes, senhor."
        return "Aqui está um resumo das nossas últimas interações:\n" + contexto

    def salvar(self) -> None:
        """Persiste a memória em disco, exceto em modo privado."""
        if self.private_mode:
            return
        try:
            self._arquivo.parent.mkdir(parents=True, exist_ok=True)
            with self._lock, open(self._arquivo, "w", encoding="utf-8") as f:
                json.dump(
                    {"atualizado": datetime.now().isoformat(), "memoria": list(self._itens)},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao salvar memória: {exc}")

    def carregar(self) -> None:
        """Carrega a memória do disco, se o arquivo existir."""
        try:
            if self._arquivo.exists():
                with open(self._arquivo, encoding="utf-8") as f:
                    dados = json.load(f)
                self._itens = deque(dados.get("memoria", []), maxlen=self._max)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao carregar memória: {exc}")
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd backend && python -m pytest tests/test_memory.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/aris/memory/ backend/tests/test_memory.py
git commit -m "feat(memory): memória de curto prazo com as_prompt_context"
```

---

### Task 5: Orchestrator — roteia para skill ou cai no LLM

**Files:**
- Create: `backend/aris/core/orchestrator.py`
- Create: `backend/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: `Registry`, `LLMProvider`, `ShortTermMemory`, `Context`, `build_prompt`, `PERSONA`.
- Produces: `Orchestrator(registry, llm, memory)` com `process(text: str, ctx: Context) -> str`.
  - Se uma skill casa: chama `skill.handle`; se a skill lançar exceção, retorna mensagem de erro padrão e não propaga.
  - Se nenhuma skill casa: chama `llm.generate(build_prompt(PERSONA, memory.as_prompt_context(), text), ctx)`.

- [ ] **Step 1: Escrever o teste que falha**

`backend/tests/test_orchestrator.py`:

```python
"""Testa o roteamento do Orchestrator entre skills e LLM."""

from dataclasses import dataclass

from aris.core.context import Context
from aris.core.orchestrator import Orchestrator
from aris.core.registry import Registry


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


class _FakeLLM:
    def __init__(self) -> None:
        self.last_prompt = ""

    def generate(self, prompt: str, ctx: Context) -> str:
        self.last_prompt = prompt
        return "resposta-llm"


class _FakeMemory:
    def as_prompt_context(self) -> str:
        return "memoria-x"


@dataclass
class _OkSkill:
    name: str = "ok"

    def matches(self, text: str, ctx: Context) -> bool:
        return "ping" in text

    def handle(self, text: str, ctx: Context) -> str:
        return "pong"


@dataclass
class _BrokenSkill:
    name: str = "broken"

    def matches(self, text: str, ctx: Context) -> bool:
        return "quebra" in text

    def handle(self, text: str, ctx: Context) -> str:
        raise RuntimeError("falhou")


def test_roteia_para_skill():
    reg = Registry()
    reg.register(_OkSkill())
    orch = Orchestrator(reg, _FakeLLM(), _FakeMemory())
    assert orch.process("manda um ping", _ctx()) == "pong"


def test_cai_no_llm_com_memoria_injetada():
    reg = Registry()
    llm = _FakeLLM()
    orch = Orchestrator(reg, llm, _FakeMemory())
    out = orch.process("fale sobre python", _ctx())
    assert out == "resposta-llm"
    assert "memoria-x" in llm.last_prompt
    assert "fale sobre python" in llm.last_prompt


def test_excecao_de_skill_nao_propaga():
    reg = Registry()
    reg.register(_BrokenSkill())
    orch = Orchestrator(reg, _FakeLLM(), _FakeMemory())
    out = orch.process("quebra isso", _ctx())
    assert "erro" in out.lower()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && python -m pytest tests/test_orchestrator.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'aris.core.orchestrator'`

- [ ] **Step 3: Implementar o Orchestrator**

`backend/aris/core/orchestrator.py`:

```python
"""Orchestrator — o decisor central do ARIS.

Recebe o texto do comando, pergunta ao Registry se alguma skill o reconhece;
se sim, executa a skill; se não, delega ao LLM com a memória recente injetada.
É o substituto desacoplado do antigo CommandProcessor.
"""

from loguru import logger

from aris.core.context import Context
from aris.core.registry import Registry
from aris.llm.base import PERSONA, LLMProvider, build_prompt
from aris.memory.short_term import ShortTermMemory


class Orchestrator:
    """Roteia cada comando para uma skill ou para o motor de raciocínio."""

    def __init__(self, registry: Registry, llm: LLMProvider, memory: ShortTermMemory) -> None:
        self._registry = registry
        self._llm = llm
        self._memory = memory

    def process(self, text: str, ctx: Context) -> str:
        """Processa um comando e retorna a resposta do ARIS."""
        skill = self._registry.resolve(text, ctx)
        if skill is not None:
            try:
                return skill.handle(text, ctx)
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Erro na skill '{skill.name}': {exc}")
                return "Desculpe, ocorreu um erro ao processar seu comando, senhor."

        prompt = build_prompt(PERSONA, self._memory.as_prompt_context(), text)
        return self._llm.generate(prompt, ctx)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd backend && python -m pytest tests/test_orchestrator.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/aris/core/orchestrator.py backend/tests/test_orchestrator.py
git commit -m "feat(core): Orchestrator roteia skill vs LLM com memória injetada"
```

---

### Task 6: Skill `datetime` (fatia vertical de prova)

**Files:**
- Create: `backend/aris/skills/__init__.py`
- Create: `backend/aris/skills/datetime_skill.py`
- Create: `backend/aris/utils/__init__.py`
- Create: `backend/aris/utils/dates.py`
- Create: `backend/tests/test_datetime_skill.py`

**Interfaces:**
- Consumes: `Context`.
- Produces:
  - `format_date_pt_br(value) -> str` (porta de `app/utils/dates.py`).
  - `DateTimeSkill` (implementa `Skill`): `name = "datetime"`; reconhece "que horas", "horas", "que dia", "data de hoje".

- [ ] **Step 1: Escrever o teste que falha**

`backend/tests/test_datetime_skill.py`:

```python
"""Testa a skill de hora/data."""

from aris.core.context import Context
from aris.skills.datetime_skill import DateTimeSkill


def _ctx() -> Context:
    return Context(speak=lambda _t: None, listen=lambda **_k: "")


def test_reconhece_hora():
    skill = DateTimeSkill()
    assert skill.matches("que horas são", _ctx())
    assert skill.matches("que dia é hoje", _ctx())
    assert not skill.matches("abrir navegador", _ctx())


def test_responde_hora():
    skill = DateTimeSkill()
    resposta = skill.handle("que horas são", _ctx())
    assert "senhor" in resposta.lower()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && python -m pytest tests/test_datetime_skill.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'aris.skills'`

- [ ] **Step 3: Implementar a skill e o util de datas**

`backend/aris/utils/__init__.py`:

```python
"""Utilitários puros (sem efeitos colaterais) do ARIS."""
```

`backend/aris/utils/dates.py`:

```python
"""Formatação de datas em português."""

from datetime import date, datetime

MESES_PT_BR = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


def format_date_pt_br(value: date | datetime) -> str:
    """Retorna algo como '29 de junho de 2026'."""
    return f"{value.day} de {MESES_PT_BR[value.month]} de {value.year}"
```

`backend/aris/skills/__init__.py`:

```python
"""Skills do ARIS — cada habilidade em seu próprio arquivo, registrada no Registry."""
```

`backend/aris/skills/datetime_skill.py`:

```python
"""Skill de hora e data — responde 'que horas são' e 'que dia é hoje'."""

from datetime import datetime

from aris.core.context import Context
from aris.utils.dates import format_date_pt_br


class DateTimeSkill:
    """Informa a hora atual ou a data de hoje."""

    name = "datetime"

    def matches(self, text: str, ctx: Context) -> bool:
        """Reconhece perguntas sobre hora ou data."""
        t = text.lower()
        return any(g in t for g in ("que horas", "horas", "que dia", "data de hoje"))

    def handle(self, text: str, ctx: Context) -> str:
        """Responde com a hora ou a data conforme o pedido."""
        t = text.lower()
        if "dia" in t or "data" in t:
            return f"Hoje é {format_date_pt_br(datetime.now())}, senhor."
        return f"Agora são {datetime.now().strftime('%H:%M')}, senhor."
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd backend && python -m pytest tests/test_datetime_skill.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/aris/skills/ backend/aris/utils/ backend/tests/test_datetime_skill.py
git commit -m "feat(skills): skill datetime + util de datas PT-BR"
```

---

### Task 7: AssistantEngine + WebSocket gateway (pipeline end-to-end)

**Files:**
- Create: `backend/aris/assistant.py`
- Create: `backend/aris/api/__init__.py`
- Create: `backend/aris/api/events.py`
- Create: `backend/aris/api/gateway.py`
- Create: `backend/main.py`
- Create: `backend/tests/test_assistant.py`

**Interfaces:**
- Consumes: `Registry`, `Orchestrator`, `ShortTermMemory`, `build_provider`, `settings`, `DateTimeSkill`, `Context`.
- Produces:
  - `build_engine(settings) -> AssistantEngine` (monta registry+memória+llm+orchestrator com as skills registradas).
  - `AssistantEngine.handle_text(text: str) -> str` (processa um comando de texto e registra na memória).
  - `app` (FastAPI) com rota WebSocket `/ws` que recebe `{"type":"command_text","text":...}` e responde `{"type":"aris_said","text":...}`.

- [ ] **Step 1: Escrever o teste que falha**

`backend/tests/test_assistant.py`:

```python
"""Testa o AssistantEngine ponta-a-ponta (skill real + memória)."""

from aris.assistant import build_engine
from aris.config import Settings


def test_engine_responde_datetime(tmp_path):
    settings = Settings(_env_file=None, arquivo_memoria=tmp_path / "mem.json")
    engine = build_engine(settings)
    resposta = engine.handle_text("que horas são")
    assert "senhor" in resposta.lower()


def test_engine_registra_na_memoria(tmp_path):
    settings = Settings(_env_file=None, arquivo_memoria=tmp_path / "mem.json")
    engine = build_engine(settings)
    engine.handle_text("que horas são")
    assert "que horas" in engine.memory.as_prompt_context().lower()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && python -m pytest tests/test_assistant.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'aris.assistant'`

- [ ] **Step 3: Implementar engine, eventos, gateway e entrypoint**

`backend/aris/assistant.py`:

```python
"""AssistantEngine — liga núcleo, memória, LLM e skills num motor headless.

Este é o "cérebro" sem UI. Clientes (WebSocket, voz, futuramente câmera) chamam
handle_text() e recebem a resposta do ARIS. build_engine() faz a montagem
(composition root) registrando todas as skills disponíveis.
"""

from loguru import logger

from aris.config import Settings
from aris.core.context import Context
from aris.core.orchestrator import Orchestrator
from aris.core.registry import Registry
from aris.llm.factory import build_provider
from aris.memory.short_term import ShortTermMemory
from aris.skills.datetime_skill import DateTimeSkill


class AssistantEngine:
    """Motor headless: recebe texto, processa e devolve a resposta do ARIS."""

    def __init__(self, orchestrator: Orchestrator, memory: ShortTermMemory) -> None:
        self._orchestrator = orchestrator
        self.memory = memory

    def handle_text(self, text: str) -> str:
        """Processa um comando em texto e registra a interação na memória."""
        # Em Fase 0 sem voz, speak/listen são no-ops; skills de diálogo entram no Plano 2.
        ctx = Context(speak=lambda _t: None, listen=lambda **_k: "")
        ctx.private_mode = self.memory.private_mode
        resposta = self._orchestrator.process(text, ctx)
        self.memory.registrar(text, resposta)
        return resposta


def build_engine(settings: Settings) -> AssistantEngine:
    """Composition root: monta o motor com skills registradas por prioridade."""
    registry = Registry()
    registry.register(DateTimeSkill())
    # Plano 2 registra aqui: apps, volume, weather, playlists, notes, memory_skill.

    memory = ShortTermMemory(max_items=settings.max_memoria, arquivo=settings.arquivo_memoria)
    llm = build_provider(settings)
    orchestrator = Orchestrator(registry, llm, memory)
    logger.info(f"AssistantEngine pronto (LLM: {settings.aris_llm_provider})")
    return AssistantEngine(orchestrator, memory)
```

`backend/aris/api/__init__.py`:

```python
"""API do ARIS — gateway WebSocket que serve qualquer cliente (web, voz, etc.)."""
```

`backend/aris/api/events.py`:

```python
"""Schemas dos eventos trocados pelo WebSocket entre clientes e o núcleo."""

from pydantic import BaseModel


class CommandText(BaseModel):
    """Comando em texto vindo de um cliente (ex.: input do frontend)."""

    type: str = "command_text"
    text: str


class ArisSaid(BaseModel):
    """Resposta do ARIS enviada de volta ao cliente."""

    type: str = "aris_said"
    text: str
```

`backend/aris/api/gateway.py`:

```python
"""Gateway WebSocket: ponto único onde clientes conversam com o AssistantEngine."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger

from aris.api.events import ArisSaid
from aris.assistant import AssistantEngine, build_engine
from aris.config import settings


def create_app(engine: AssistantEngine | None = None) -> FastAPI:
    """Cria a app FastAPI. Aceita um engine injetado (útil em testes)."""
    app = FastAPI(title="ARIS", version="0.1.0")
    app.state.engine = engine or build_engine(settings)

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        logger.info("Cliente conectado ao /ws")
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "command_text":
                    resposta = app.state.engine.handle_text(data.get("text", ""))
                    await websocket.send_json(ArisSaid(text=resposta).model_dump())
        except WebSocketDisconnect:
            logger.info("Cliente desconectado do /ws")

    return app


app = create_app()
```

`backend/main.py`:

```python
"""Entrypoint do backend: sobe o servidor ASGI do ARIS.

Uso: cd backend && python main.py  (ou: uvicorn aris.api.gateway:app --reload)
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("aris.api.gateway:app", host="127.0.0.1", port=8000, reload=True)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd backend && python -m pytest tests/test_assistant.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Rodar a suíte inteira**

Run: `cd backend && python -m pytest -v`
Expected: PASS (todos os testes das Tasks 1-7)

- [ ] **Step 6: Verificação manual do WebSocket (smoke)**

Run: `cd backend && python main.py` (em um terminal), e em outro:

```bash
python -c "import asyncio, json, websockets; \
asyncio.run((lambda: (lambda ws: None))())" 2>/dev/null || pip install websockets
python - <<'PY'
import asyncio, json, websockets
async def main():
    async with websockets.connect("ws://127.0.0.1:8000/ws") as ws:
        await ws.send(json.dumps({"type": "command_text", "text": "que horas são"}))
        print(await ws.recv())
asyncio.run(main())
PY
```
Expected: imprime um JSON `{"type": "aris_said", "text": "Agora são HH:MM, senhor."}`

- [ ] **Step 7: Commit**

```bash
git add backend/aris/assistant.py backend/aris/api/ backend/main.py backend/tests/test_assistant.py
git commit -m "feat(api): AssistantEngine + gateway WebSocket (pipeline end-to-end)"
```

---

### Task 8: Lint, tipos e atualização do requirements

**Files:**
- Create: `backend/requirements.txt`
- Modify: `CLAUDE.md` (seção do backend)

**Interfaces:**
- Consumes: tudo das Tasks 1-7.
- Produces: ambiente reproduzível e doc atualizada.

- [ ] **Step 1: Gerar `backend/requirements.txt`**

```text
fastapi>=0.110
uvicorn[standard]>=0.29
pydantic-settings>=2.2
google-generativeai>=0.8
requests>=2.31
loguru>=0.7
```

- [ ] **Step 2: Rodar ruff e black**

Run: `cd backend && python -m ruff check . && python -m black --check .`
Expected: sem erros (ou rode `ruff check . --fix && black .` e re-verifique)

- [ ] **Step 3: Rodar mypy**

Run: `cd backend && python -m mypy aris`
Expected: `Success: no issues found`

- [ ] **Step 4: Atualizar CLAUDE.md**

Adicionar ao final de `CLAUDE.md` uma seção:

```markdown
## Backend headless (Fase 0+)

O diretório `backend/` contém o novo núcleo desacoplado (substituindo o monolito Tkinter de `app/`).

- Rodar: `cd backend && python main.py` (WebSocket em `ws://127.0.0.1:8000/ws`)
- Testes: `cd backend && python -m pytest -v`
- Lint/tipos: `ruff check . && black --check . && mypy aris`
- Composition root: `aris/assistant.py:build_engine` (registra as skills)
- Adicionar skill = criar arquivo em `aris/skills/` e registrar em `build_engine`
- LLM trocável por `ARIS_LLM_PROVIDER` no `.env` (`gemini`|`ollama`)
```

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt CLAUDE.md
git commit -m "chore(backend): requirements, lint/tipos limpos e doc no CLAUDE.md"
```

---

## Self-Review

**Spec coverage (Fase 0 / parte backend-núcleo):**
- Monorepo `backend/` ✓ (Task 1) · núcleo Skill/Registry/Orchestrator ✓ (Tasks 2,5) ·
  LLM Gemini+Ollama trocável ✓ (Task 3) · memória injetada no prompt ✓ (Tasks 4,5) ·
  WebSocket gateway ✓ (Task 7) · pydantic-settings ✓ (Task 1) · pytest do núcleo ✓ (todas) ·
  tooling ruff/black/mypy ✓ (Task 8).
- **Fora deste plano (por design):** migração das skills restantes + voz (Plano 2);
  frontend React (Plano 3); `profile.py` stub (Fase 1).

**Placeholder scan:** sem TBD/TODO; todo passo tem código completo. A única "nota" é a
correção explícita do corpo `...` do Protocol em `skill.py` (Task 2, Step 3).

**Type consistency:** `handle_text`, `process`, `as_prompt_context`, `build_prompt`,
`build_provider`, `build_engine`, `create_app` usados de forma consistente entre tasks e testes.
Eventos `command_text`/`aris_said` batem entre `events.py` e `gateway.py`.
