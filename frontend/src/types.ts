// Tipos compartilhados do frontend do ARIS.

// Estados do assistente — espelham os eventos `state` do gateway WebSocket.
export type VoiceState =
  | "disconnected"
  | "idle"
  | "listening"
  | "processing"
  | "speaking"
  | "starting"
  | "stopped"
  | "voice_unavailable";

// Eventos recebidos do backend pelo WebSocket.
export interface ArisEvent {
  type: "state" | "user_said" | "aris_said";
  state?: VoiceState;
  text?: string;
}

// Uma linha do histórico de interações exibido no HUD.
export interface LogEntry {
  id: number;
  who: "user" | "aris";
  text: string;
  time: string;
}
