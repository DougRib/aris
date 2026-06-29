// Store global (Zustand) com o estado do HUD: conexão, estado de voz e log.
import { create } from "zustand";
import type { LogEntry, VoiceState } from "../types";

interface ArisStore {
  connected: boolean;
  voiceState: VoiceState;
  log: LogEntry[];
  setConnected: (c: boolean) => void;
  setVoiceState: (s: VoiceState) => void;
  addLog: (who: "user" | "aris", text: string) => void;
}

let _nextId = 0;

export const useStore = create<ArisStore>((set) => ({
  connected: false,
  voiceState: "disconnected",
  log: [],
  setConnected: (connected) => set({ connected }),
  setVoiceState: (voiceState) => set({ voiceState }),
  addLog: (who, text) =>
    set((s) => ({
      // mantém só as últimas 100 linhas
      log: [
        ...s.log,
        { id: ++_nextId, who, text, time: new Date().toLocaleTimeString("pt-BR") },
      ].slice(-100),
    })),
}));
