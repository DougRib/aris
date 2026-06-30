// Tipos compartilhados do frontend do ARIS.

// Modo atual do assistente (dirige o visualizador do HUD).
export type Mode = "disconnected" | "idle" | "listening" | "processing" | "speaking";

// Uma linha do histórico/transcrição.
export interface LogEntry {
  id: number;
  who: "user" | "aris";
  text: string;
  time: string;
}
