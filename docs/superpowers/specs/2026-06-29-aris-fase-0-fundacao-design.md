# ARIS — Fase 0: Fundação (Design)

**Data:** 2026-06-29
**Status:** Aprovado para implementação
**Autor:** Douglas + ARIS (arquitetura)

## Contexto

O ARIS hoje é um assistente de voz em PT-BR (Python + Tkinter) com identidade JARVIS-BR
consistente, mas com o cérebro acoplado à interface gráfica. `app/ui/app.py` (~1000 linhas)
contém o loop de voz, TTS/STT, animação e a orquestração dos serviços. Adicionar habilidades
exige editar uma cadeia `if/elif` de ~170 linhas em `app/core/command_processor.py`. Não existe
um "ARIS" separável da janela, o que bloqueia qualquer evolução multimodal/multi-dispositivo.

A visão de longo prazo é uma **plataforma multimodal** entregue em 5 fases (0-4). Este spec
cobre **somente a Fase 0 — Fundação**.

## Meta da Fase 0

Atingir **paridade total de capacidades** com o ARIS atual, porém sobre uma arquitetura
desacoplada (núcleo headless + API WebSocket) e com frontend React no lugar do Tkinter.

**Nenhuma capacidade nova nesta fase.** A Fase 0 é a fundação que destrava as Fases 1-4.

### Critérios de sucesso (paridade)

Tudo que o ARIS faz hoje continua funcionando pela nova arquitetura:
- Voz PT-BR: STT (Google Speech) + TTS (edge-tts com reverb, fallback pyttsx3)
- Wake word "Áris" + modo always-active
- Abrir apps/sites (navegador, Office, VS Code, WhatsApp, Telegram, redes sociais)
- Volume do sistema e por-app (YouTube)
- Clima/previsão (OpenWeather), hora/data
- Playlists YouTube, notas, memória curta, modo privado
- Conversa/pesquisa via LLM (fallback)

### Adições de fundação (não são "capacidades novas", são correções estruturais)

- **Input por texto** no frontend (hoje só existe voz)
- **Memória de curto prazo realimenta o prompt** do LLM (hoje a memória é ignorada no raciocínio)
- **Provider de LLM trocável**: Gemini (nuvem) ou Ollama (local) por config
- **Testes automatizados** do núcleo (hoje: zero)

## Não-objetivos (ficam para fases posteriores)

- ChromaDB / memória vetorial de longo prazo → Fase 1
- Whisper, ElevenLabs, Porcupine → fases posteriores (decisão: manter Google STT + edge-tts agora)
- Sub-agentes paralelos, planejamento, proatividade → Fase 2
- Automação de PC, integrações (Notion/Gmail/Calendar/GitHub), métricas → Fase 3
- Visão computacional, reconhecimento facial, OCR → Fase 4

## Decisões técnicas (confirmadas pelo usuário)

| Decisão | Escolha | Observação |
|---|---|---|
| Motor LLM | **Gemini + Ollama** (trocável) | `GEMINI_KEY` (Google AI Studio) já funciona; Ollama em `localhost:11434` |
| STT | **Google Speech** (mantido) | Online, grátis, já em uso |
| TTS | **edge-tts** (mantido) | Voz Antonio + reverb; fallback pyttsx3 |
| Backend | **FastAPI + WebSocket** | Backend roda local (dono de mic/áudio/OS) |
| Frontend | **React + TS + Tailwind + Vite** | HUD que porta a estética sci-fi atual |

## Arquitetura

```
aris/
├── backend/                          # Python — cérebro headless, roda local
│   ├── aris/
│   │   ├── core/
│   │   │   ├── orchestrator.py        # roteia comando → skill ou LLM
│   │   │   ├── skill.py               # Protocol: matches() + handle()
│   │   │   ├── registry.py            # registro/descoberta de skills
│   │   │   └── context.py             # estado da conversa, entidades, callbacks
│   │   ├── llm/
│   │   │   ├── base.py                # LLMProvider (Protocol)
│   │   │   ├── gemini_provider.py
│   │   │   └── ollama_provider.py
│   │   ├── voice/
│   │   │   ├── stt.py                 # SpeechToText (Protocol) + GoogleSTT
│   │   │   └── tts.py                 # TextToSpeech (Protocol) + EdgeTTS/Pyttsx3
│   │   ├── memory/
│   │   │   ├── short_term.py          # histórico da sessão (porta MemoryManager)
│   │   │   └── profile.py             # stub p/ Fase 1 (perfil do usuário)
│   │   ├── skills/                    # uma habilidade = um arquivo
│   │   │   ├── apps.py                # abrir programas/sites
│   │   │   ├── volume.py
│   │   │   ├── weather.py
│   │   │   ├── datetime_skill.py      # hora/data
│   │   │   ├── playlists.py
│   │   │   ├── notes.py
│   │   │   └── memory_skill.py        # resumo/histórico, modo privado
│   │   ├── api/
│   │   │   ├── gateway.py             # WebSocket: eventos bidirecionais
│   │   │   └── events.py              # schemas dos eventos (pydantic)
│   │   ├── assistant.py               # AssistantEngine: liga voz + orchestrator + memória
│   │   └── config.py                  # pydantic-settings
│   ├── tests/
│   │   ├── test_registry.py
│   │   ├── test_orchestrator.py
│   │   └── test_skills/
│   ├── pyproject.toml                 # ruff, black, mypy, pytest
│   └── main.py                        # uvicorn entrypoint
│
└── frontend/                         # React + TS + Tailwind + Vite
    ├── src/
    │   ├── components/hud/            # anel pulsante, arcos, grid (porta o Tkinter)
    │   ├── components/Log.tsx         # histórico de interações em tempo real
    │   ├── components/TextInput.tsx   # input por texto (novo)
    │   ├── hooks/useAris.ts           # cliente WebSocket
    │   ├── state/store.ts             # Zustand
    │   └── App.tsx
    ├── package.json
    └── tailwind.config.ts
```

### Princípio central

`api/gateway.py` expõe WebSocket. O React, a camada de voz e (no futuro) câmera/celular são
**todos clientes iguais** do mesmo núcleo. O cérebro nunca mais mora dentro da tela.

O backend roda na máquina local do usuário (Windows) porque precisa de acesso ao microfone,
alto-falante, abertura de apps e controle de volume — tudo OS-level. O frontend é a "face" e
conversa com o backend por WebSocket em localhost.

## Componentes

### `core/skill.py` — Skill (Protocol)
- **O que faz:** define o contrato de toda habilidade.
- **Interface:**
  ```python
  class Skill(Protocol):
      name: str
      def matches(self, text: str, ctx: Context) -> bool: ...
      def handle(self, text: str, ctx: Context) -> str: ...
  ```
- **Depende de:** `Context`.

### `core/registry.py` — Registry
- **O que faz:** mantém a lista ordenada de skills; descobre a primeira que dá `matches()`.
- **Interface:** `register(skill)`, `resolve(text, ctx) -> Skill | None`.
- **Depende de:** `Skill`.
- **Substitui:** o `if/elif` de `command_processor.py`. Ordem de registro = prioridade.

### `core/orchestrator.py` — Orchestrator
- **O que faz:** recebe o texto do comando, consulta o `Registry`; se nenhuma skill casa,
  delega ao `LLMProvider` (com a memória de curto prazo injetada no prompt).
- **Interface:** `process(text, ctx) -> str`.
- **Depende de:** `Registry`, `LLMProvider`, `ShortTermMemory`.

### `core/context.py` — Context
- **O que faz:** carrega estado da conversa, entidades e os callbacks `falar`/`ouvir` (para
  skills que precisam de diálogo, ex.: "de qual cidade?"). Desacopla a skill da UI.
- **Depende de:** nada.

### `llm/base.py` — LLMProvider (Protocol)
- **Interface:** `generate(prompt: str, ctx: Context) -> str`.
- **Implementações:** `GeminiProvider` (usa `GEMINI_KEY`), `OllamaProvider` (HTTP local).
- **Seleção:** `ARIS_LLM_PROVIDER=gemini|ollama` no config.
- A persona ("ÁRIS… máx 40 palavras… trata por senhor") vira **um template central** aqui,
  não mais strings espalhadas.

### `voice/stt.py` e `voice/tts.py`
- **O que fazem:** abstraem reconhecimento e síntese atrás de Protocols (`SpeechToText`,
  `TextToSpeech`). Implementações iniciais portam o código atual (Google + edge-tts/pyttsx3).
- **Por quê:** trocar por Whisper/ElevenLabs depois = nova implementação, zero mudança no núcleo.

### `memory/short_term.py`
- **O que faz:** porta o `MemoryManager` (deque persistido, thread-safe, modo privado) e expõe
  `as_prompt_context()` para o `Orchestrator` injetar no LLM.

### `api/gateway.py` — WebSocket Gateway
- **O que faz:** publica eventos do núcleo (estado: ouvindo/processando/falando; transcrições;
  respostas) e recebe comandos do frontend (texto digitado, iniciar/parar).
- **Eventos (pydantic em `events.py`):** `state_changed`, `user_said`, `aris_said`,
  `command_text` (entrada do frontend).

### `assistant.py` — AssistantEngine
- **O que faz:** o loop principal headless. Liga STT → Orchestrator → TTS, registra na memória,
  emite eventos pelo gateway. É o `executar_assistente` atual, **sem Tkinter**.

### Frontend
- **`useAris.ts`:** conecta ao WebSocket, despacha eventos pro store.
- **`store.ts` (Zustand):** estado do HUD (status, log).
- **`components/hud/`:** porta a estética (anel, arcos, grid) para Canvas/SVG + Tailwind.
- **`TextInput.tsx`:** envia `command_text` pelo WebSocket.

## Fluxo de dados

```
[mic] → GoogleSTT → AssistantEngine → Orchestrator → Registry.resolve()
                                                         │
                                          ┌──────────────┴───────────────┐
                                     skill casa                    nenhuma casa
                                          │                              │
                                    skill.handle()              LLMProvider.generate()
                                          │                     (memória injetada)
                                          └──────────────┬───────────────┘
                                                    resposta (texto)
                                                         │
                                   ┌─────────────────────┼────────────────────┐
                                EdgeTTS → [alto-falante]   WebSocket → React HUD (log + estado)
                                                         │
                                              ShortTermMemory.registrar()

[frontend TextInput] → WebSocket command_text → AssistantEngine (mesmo pipeline, sem STT)
```

## Tratamento de erros

- **STT:** timeout / não-entendido / erro de API tratados como hoje (retorna vazio, atualiza
  estado visual). Erro de rede → evento de estado "erro" no HUD.
- **LLM:** provider indisponível (Gemini sem key / Ollama offline) → mensagem de fallback
  educada; log do erro. Se `ARIS_LLM_PROVIDER` inválido → falha na inicialização com mensagem clara.
- **WebSocket:** frontend reconecta automaticamente; backend tolera ausência de cliente
  (a voz funciona sem o HUD aberto).
- **Skills:** exceção em `handle()` é capturada pelo Orchestrator → resposta de erro padrão,
  log com stack; nunca derruba o loop.

## Testes

- **pytest** no backend. TDD para o núcleo:
  - `test_registry.py`: registro, ordem de prioridade, `resolve` com/sem match.
  - `test_orchestrator.py`: roteia para skill quando casa; cai no LLM (mockado) quando não casa;
    injeta memória no prompt; captura exceção de skill.
  - `test_skills/`: cada skill migrada com teste de `matches()` (palavras-chave) e `handle()`.
- LLM, STT e TTS são **mockados** nos testes do núcleo (nada de rede/áudio em teste).
- Frontend: testes ficam mínimos na Fase 0 (smoke do hook WebSocket); foco do TDD é o backend.

## Tooling

- Backend: `ruff` (lint) + `black` (format) + `mypy` (tipos) + `pytest`. Config em `pyproject.toml`.
- Frontend: `eslint` + `prettier`.

## Estratégia de migração

1. Construir `backend/` ao lado do `app/` atual (não editar o monolito in-place).
2. Portar serviços que já são quase puros (weather, music, volume, dates) primeiro.
3. Portar memória e notas.
4. Construir núcleo (skill/registry/orchestrator) com TDD.
5. Portar voz (STT/TTS) atrás das interfaces.
6. Ligar `AssistantEngine` + `gateway`.
7. Construir frontend React e conectar.
8. Validar paridade ponta-a-ponta.
9. Aposentar `app/` (Tkinter) — preservado no histórico do git.

## Critérios de aceite da Fase 0

- [ ] Backend sobe com `uvicorn` e expõe WebSocket.
- [ ] Frontend React conecta e mostra estado + log em tempo real.
- [ ] Comando por voz e por texto percorrem o mesmo pipeline.
- [ ] Todas as skills atuais migradas e funcionando (paridade).
- [ ] LLM trocável Gemini ↔ Ollama por `.env`.
- [ ] Memória de curto prazo injetada no prompt do LLM.
- [ ] `pytest` verde para núcleo e skills migradas.
- [ ] ruff/black/mypy sem erros no backend.
