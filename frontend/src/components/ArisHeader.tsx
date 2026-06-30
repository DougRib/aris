// Cabeçalho: título ARIS holográfico + indicador de conexão (dinâmico).
import { useStore } from "@/state/store";

export default function ArisHeader() {
  const connected = useStore((s) => s.connected);

  return (
    <div className="flex justify-between items-start px-6 pt-6">
      <div>
        <h1
          className="text-2xl font-semibold tracking-[0.18em] holo-text"
        >
          ARIS
        </h1>
        <p className="text-slate-400 text-md leading-tight">
          Assistente por voz
        </p>
      </div>

      <div className="flex items-center gap-2">
        <div
          className={`w-2.5 h-2.5 rounded-full ${connected ? "bg-green-400 animate-pulse" : "bg-red-400"}`}
        />
        <span
          className={`tracking-widest text-xs ${connected ? "text-green-400" : "text-slate-500"}`}
        >
          {connected ? "ONLINE" : "OFF"}
        </span>
      </div>
    </div>
  );
}
