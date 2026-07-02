// Botão de microfone (vidro + relevo). Liga/desliga a escuta; reflete o estado.
import { Mic } from "lucide-react";
import { useStore } from "@/state/store";

export default function VoiceButton({ onToggle }: { onToggle: () => void }) {
  const micActive = useStore((s) => s.micActive);
  const connected = useStore((s) => s.connected);
  const supported = useStore((s) => s.supported);

  return (
    <div className="flex flex-col items-center mt-5">
      <button
        type="button"
        onClick={onToggle}
        disabled={!connected || !supported}
        className={`
          mic-button
          ${micActive ? "mic-active" : ""}
        `}
      >
        {micActive && (
          <div className="absolute inset-0 rounded-full animate-ping bg-green-400/15" />
        )}
        <Mic
          size={30}
          className="mic-icon"
        />
      </button>

      <p className="text-slate-400 mt-3 text-sm">
        {!supported
          ? "Navegador sem reconhecimento de voz"
          : micActive
            ? "Ouvindo — toque para parar"
            : "Toque para falar"}
      </p>
    </div>
  );
}
