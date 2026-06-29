// Tela principal do ARIS: HUD central, histórico e controles, sobre um fundo
// com grid sci-fi. Estabelece a conexão WebSocket via useAris().
import { useAris } from "./hooks/useAris";
import { useStore } from "./state/store";
import { Hud } from "./components/Hud";
import { Log } from "./components/Log";
import { Controls } from "./components/Controls";

const GRID_BG = {
  backgroundImage:
    "linear-gradient(var(--color-grid) 1px, transparent 1px), linear-gradient(90deg, var(--color-grid) 1px, transparent 1px)",
  backgroundSize: "44px 44px",
};

export default function App() {
  const { sendText, startVoice, stopVoice } = useAris();
  const connected = useStore((s) => s.connected);

  return (
    <div className="min-h-full w-full" style={GRID_BG}>
      <div className="mx-auto flex min-h-full max-w-2xl flex-col items-center gap-6 px-4 py-8">
        <header className="flex flex-col items-center gap-1">
          <h1 className="text-2xl font-bold tracking-[0.25em] text-primary">ARIS</h1>
          <p className="text-sm text-muted">Assistente Pessoal • Comando por Voz</p>
          <div className="mt-1 flex items-center gap-2 text-xs">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: connected ? "var(--color-success)" : "var(--color-danger)" }}
            />
            <span className="text-muted">{connected ? "Conectado ao núcleo" : "Conectando…"}</span>
          </div>
        </header>

        <Hud />
        <Log />
        <Controls onSend={sendText} onStartVoice={startVoice} onStopVoice={stopVoice} />
      </div>
    </div>
  );
}
