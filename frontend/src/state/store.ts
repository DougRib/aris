// Store global (Zustand): conexão, modo, nível de áudio (visualizador) e log.
import { create } from "zustand";
import type { LogEntry, Mode } from "../types";

interface ArisStore {
  connected: boolean;
  mode: Mode;
  level: number; // 0..1 — amplitude para o visualizador reativo
  micActive: boolean;
  supported: boolean; // navegador suporta reconhecimento de voz?
  log: LogEntry[];
  setConnected: (c: boolean) => void;
  setMode: (m: Mode) => void;
  setLevel: (l: number) => void;
  setMicActive: (a: boolean) => void;
  setSupported: (s: boolean) => void;
  addLog: (who: "user" | "aris", text: string) => void;
}

let _nextId = 0;

export const useStore = create<ArisStore>((set) => ({
  connected: false,
  mode: "disconnected",
  level: 0.05,
  micActive: false,
  supported: true,
  log: [],
  setConnected: (connected) => set({ connected }),
  setMode: (mode) => set({ mode }),
  setLevel: (level) => set({ level }),
  setMicActive: (micActive) => set({ micActive }),
  setSupported: (supported) => set({ supported }),
  addLog: (who, text) =>
    set((s) => ({
      log: [
        ...s.log,
        { id: ++_nextId, who, text, time: new Date().toLocaleTimeString("pt-BR") },
      ].slice(-50),
    })),
}));
