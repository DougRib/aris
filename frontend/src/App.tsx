// Tela do ARIS: um painel compacto, glassmorfismo sobre fundo em gradiente.
// Interface só-voz: HUD reativo + botão de microfone + transcrição.
import { useAris } from "./hooks/useAris";
import { useStore } from "./state/store";
import { Hud } from "./components/Hud";
import { MicButton } from "./components/MicButton";
import { Transcript } from "./components/Transcript";

export default function App() {
  const { toggleMic } = useAris();
  const connected = useStore((s) => s.connected);

  return (
    <div className="flex h-full w-full items-center justify-center p-4">
      <div
        className="flex w-[380px] max-w-full flex-col items-center gap-5 rounded-[28px] border border-edge/60 bg-panel/35 px-6 py-7 backdrop-blur-xl"
        style={{ boxShadow: "0 0 80px -28px var(--color-primary), inset 0 0 40px -30px var(--color-violet)" }}
      >
        <header className="flex w-full items-center justify-between">
          <div>
            <h1 className="text-lg font-bold tracking-[0.4em] text-primary">ARIS</h1>
            <p className="text-[11px] tracking-wide text-muted">assistente por voz</p>
          </div>
          <span
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{
              background: connected ? "var(--color-success)" : "var(--color-danger)",
              boxShadow: connected ? "0 0 10px var(--color-success)" : "none",
            }}
          />
        </header>

        <Hud />
        <MicButton onToggle={toggleMic} />
        <Transcript />
      </div>
    </div>
  );
}
