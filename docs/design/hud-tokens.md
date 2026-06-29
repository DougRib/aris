# HUD — Design Tokens (referência para o frontend React)

Extraído do HUD Tkinter legado (`app/ui/app.py`, agora removido). Serve de base
para o HUD futurista do Plano 3 (React + Tailwind). Estética: "JARVIS", neon ciano
sobre fundo azul-petróleo escuro, com grid sci-fi e anel central pulsante.

## Paleta

| Token | Hex | Uso |
|---|---|---|
| `bg` | `#07121B` | fundo principal |
| `panel` | `#0B1D2A` | painéis (ex.: log) |
| `panel-inner` | `#0A1724` | interior de painel |
| `border` | `#123243` | bordas |
| `grid` | `#0C2333` | linhas do grid de fundo |
| `trace` | `#143A55` | traços/arcos de fundo (destaque) |
| `trace-dim` | `#0D2A3D` | traços de fundo (apagado) |
| `neon-core` | `#06121D` | núcleo do anel central |
| `primary` (fg) | `#2FD2FF` | ciano neon principal (anel, títulos) |
| `primary-glow` | `#7BE7FF` | brilho/realce ciano |
| `text` | `#E6F2EF` | texto principal |
| `text-muted` | `#91A6B8` | texto secundário |
| `danger` | `#FF5C5C` | erro / parar |
| `warning` | `#FFC857` | aguardando / confirmar |
| `success` | `#3DFF9E` | online / sucesso |
| `user-line` | `#9FE870` | transcrição do usuário no log |

## Tipografia

- Títulos: **Segoe UI** 18 bold · subtítulo 10 · status 10 bold · corpo 10 · botão 11 bold
- Monoespaçada (log): **Cascadia Code** 9
- No web: usar Segoe UI / system-ui; mono: Cascadia Code / ui-monospace.

## Elementos visuais

- **Anel central** (~210px): anel de brilho externo, círculo principal (contorno ciano,
  ~3px), núcleo interno preenchido (`neon-core`), e um *pulse ring* animado.
- **Arcos rotativos** (externo com brilho, interno mais forte) + 12 *ticks* ao redor.
- **Animação ao falar**: o pulse ring expande/contrai (senoidal), os arcos giram e as
  larguras "respiram". Cor muda conforme estado.
- **Fundo sci-fi**: grid de linhas, círculos concêntricos, arcos radiais, ticks e pontos.
- **Estados** (mapear para eventos do WebSocket `state`):
  - `idle`/online → ciano `primary` (⚪/🟢)
  - `listening` → `warning` amarelo (🟡)
  - `processing` → `primary-glow`
  - `speaking` → pulso animado em `primary`
  - `stopped`/erro → `danger` (🔴)
- **Janela legada**: 540×700. No web, layout responsivo centrado.
- **Log de interações**: linhas com timestamp; usuário em `user-line`, ARIS em `primary`,
  erro em `danger`, aviso em `warning`.

## Mapeamento de eventos (WebSocket → HUD)

O gateway emite `{"type":"state","state":...}`, `{"type":"user_said","text":...}`,
`{"type":"aris_said","text":...}`. O HUD reflete `state` no anel/animação e anexa
`user_said`/`aris_said` ao log. Comandos do HUD → backend: `command_text`,
`start_voice`, `stop_voice`.
