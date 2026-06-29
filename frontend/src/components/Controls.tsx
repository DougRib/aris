// Controles: campo de texto para enviar comandos e botão para ligar/desligar
// o modo de voz. O botão alterna conforme o estado atual do assistente.
import { useState } from "react";
import { useStore } from "../state/store";

interface Props {
  onSend: (text: string) => void;
  onStartVoice: () => void;
  onStopVoice: () => void;
}

const VOICE_ATIVO = new Set(["listening", "processing", "speaking", "starting"]);

export function Controls({ onSend, onStartVoice, onStopVoice }: Props) {
  const [text, setText] = useState("");
  const voiceState = useStore((s) => s.voiceState);
  const connected = useStore((s) => s.connected);
  const voiceAtivo = VOICE_ATIVO.has(voiceState);

  return (
    <div className="flex w-full max-w-md flex-col gap-3">
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          onSend(text);
          setText("");
        }}
      >
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Digite um comando, senhor…"
          disabled={!connected}
          className="flex-1 rounded-lg border border-edge bg-panel-inner px-3 py-2 text-sm text-content outline-none placeholder:text-muted focus:border-primary disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!connected}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-bg transition hover:brightness-110 disabled:opacity-50"
        >
          Enviar
        </button>
      </form>

      <button
        type="button"
        disabled={!connected}
        onClick={voiceAtivo ? onStopVoice : onStartVoice}
        className={`rounded-lg border px-4 py-2 text-sm font-semibold transition disabled:opacity-50 ${
          voiceAtivo
            ? "border-danger text-danger hover:bg-danger/10"
            : "border-primary text-primary hover:bg-primary/10"
        }`}
      >
        {voiceAtivo ? "⏹ Parar voz" : "🎙 Iniciar voz"}
      </button>
    </div>
  );
}
