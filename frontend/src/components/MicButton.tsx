// Botão de microfone: liga/desliga a escuta. Brilha quando ativo. É o único
// controle da interface (ARIS é só-voz).
import { useStore } from "../state/store";

function MicIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <line x1="12" y1="18" x2="12" y2="21" />
    </svg>
  );
}

export function MicButton({ onToggle }: { onToggle: () => void }) {
  const micActive = useStore((s) => s.micActive);
  const connected = useStore((s) => s.connected);
  const supported = useStore((s) => s.supported);

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={onToggle}
        disabled={!connected || !supported}
        className={`relative flex h-16 w-16 items-center justify-center rounded-full border-2 transition disabled:opacity-40 ${
          micActive ? "border-success text-success" : "border-primary text-primary hover:bg-primary/10"
        }`}
        style={{
          boxShadow: micActive
            ? "0 0 28px -2px var(--color-success)"
            : "0 0 18px -4px var(--color-primary)",
        }}
      >
        <MicIcon />
        {micActive && (
          <span className="absolute inset-0 animate-ping rounded-full border-2 border-success/40" />
        )}
      </button>
      <span className="text-xs text-muted">
        {!supported
          ? "Navegador sem reconhecimento de voz"
          : micActive
            ? "Ouvindo — toque para parar"
            : "Toque para falar"}
      </span>
    </div>
  );
}
