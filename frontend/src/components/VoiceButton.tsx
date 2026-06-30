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
        className={`relative w-20 h-20 rounded-full glass neumorph flex items-center justify-center transition hover:scale-105 disabled:opacity-40 disabled:hover:scale-100 cursor-pointer ${
          micActive ? "border-2 border-green-400" : "border-2 border-cyan-400/70"
        }`}
      >
        {micActive && <div className="absolute inset-0 rounded-full animate-ping bg-green-400/15" />}
        <Mic size={30} className={`relative z-10 ${micActive ? "text-green-300" : "text-cyan-300"}`} />
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
