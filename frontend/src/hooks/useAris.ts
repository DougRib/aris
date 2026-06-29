// Hook que mantém a conexão WebSocket com o backend do ARIS, despacha os
// eventos recebidos para o store e expõe ações para enviar comandos.
import { useCallback, useEffect, useRef } from "react";
import { useStore } from "../state/store";
import type { ArisEvent } from "../types";

const WS_URL = "ws://127.0.0.1:8000/ws";

export function useAris() {
  const socketRef = useRef<WebSocket | null>(null);
  const setConnected = useStore((s) => s.setConnected);
  const setVoiceState = useStore((s) => s.setVoiceState);
  const addLog = useStore((s) => s.addLog);

  useEffect(() => {
    let alive = true;
    let retry: ReturnType<typeof setTimeout>;

    function connect() {
      const sock = new WebSocket(WS_URL);
      socketRef.current = sock;

      sock.onopen = () => {
        setConnected(true);
        setVoiceState("idle");
      };
      sock.onclose = () => {
        setConnected(false);
        setVoiceState("disconnected");
        if (alive) retry = setTimeout(connect, 1500); // reconecta sozinho
      };
      sock.onerror = () => sock.close();
      sock.onmessage = (e) => {
        const ev: ArisEvent = JSON.parse(e.data);
        if (ev.type === "state" && ev.state) setVoiceState(ev.state);
        else if (ev.type === "user_said" && ev.text) addLog("user", ev.text);
        else if (ev.type === "aris_said" && ev.text) addLog("aris", ev.text);
      };
    }

    connect();
    return () => {
      alive = false;
      clearTimeout(retry);
      socketRef.current?.close();
    };
  }, [setConnected, setVoiceState, addLog]);

  const send = useCallback((msg: object) => {
    const sock = socketRef.current;
    if (sock && sock.readyState === WebSocket.OPEN) sock.send(JSON.stringify(msg));
  }, []);

  const sendText = useCallback(
    (text: string) => {
      const t = text.trim();
      if (!t) return;
      addLog("user", t); // eco otimista (o backend responde com aris_said)
      send({ type: "command_text", text: t });
    },
    [send, addLog],
  );

  const startVoice = useCallback(() => send({ type: "start_voice" }), [send]);
  const stopVoice = useCallback(() => send({ type: "stop_voice" }), [send]);

  return { sendText, startVoice, stopVoice };
}
