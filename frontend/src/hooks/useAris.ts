// Orquestrador do frontend: conecta ao backend (WebSocket) e cuida da voz NO
// NAVEGADOR — reconhecimento (Web Speech API), síntese (speechSynthesis) e o
// nível de áudio do microfone para o visualizador reativo.
//
// Fluxo: o navegador reconhece a fala → envia { command_text } ao backend → o
// backend responde { aris_said } → o navegador fala a resposta. Enquanto o ARIS
// fala, o reconhecimento é pausado para ele não ouvir a si mesmo.
import { useCallback, useEffect, useRef } from "react";
import { useStore } from "../state/store";

const WS_URL = "ws://127.0.0.1:8000/ws";

export function useAris() {
  const setConnected = useStore((s) => s.setConnected);
  const setMode = useStore((s) => s.setMode);
  const setLevel = useStore((s) => s.setLevel);
  const setMicActive = useStore((s) => s.setMicActive);
  const setSupported = useStore((s) => s.setSupported);
  const addLog = useStore((s) => s.addLog);

  const wsRef = useRef<WebSocket | null>(null);
  const recogRef = useRef<any>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef<number>(0);
  const levelRef = useRef(0.05);
  const speakingRef = useRef(false);
  const micActiveRef = useRef(false);

  // ---- WebSocket (com reconexão) ----
  useEffect(() => {
    let alive = true;
    let retry: ReturnType<typeof setTimeout>;
    function connect() {
      const sock = new WebSocket(WS_URL);
      wsRef.current = sock;
      sock.onopen = () => {
        setConnected(true);
        setMode(micActiveRef.current ? "listening" : "idle");
      };
      sock.onclose = () => {
        setConnected(false);
        setMode("disconnected");
        if (alive) retry = setTimeout(connect, 1500);
      };
      sock.onerror = () => sock.close();
      sock.onmessage = (e) => {
        const ev = JSON.parse(e.data);
        if (ev.type === "aris_said" && ev.text) {
          addLog("aris", ev.text);
          speak(ev.text);
        }
      };
    }
    connect();
    return () => {
      alive = false;
      clearTimeout(retry);
      wsRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- Loop de animação: nível de áudio para o visualizador ----
  useEffect(() => {
    function tick() {
      const mode = useStore.getState().mode;
      let target = 0.05;
      if (mode === "listening" && analyserRef.current) {
        const a = analyserRef.current;
        const buf = new Uint8Array(a.fftSize);
        a.getByteTimeDomainData(buf);
        let sum = 0;
        for (let i = 0; i < buf.length; i++) {
          const x = (buf[i] - 128) / 128;
          sum += x * x;
        }
        target = Math.min(1, Math.sqrt(sum / buf.length) * 4);
      } else if (mode === "speaking") {
        const t = performance.now() / 110;
        target = 0.35 + 0.35 * Math.abs(Math.sin(t)) + Math.random() * 0.12;
      } else if (mode === "processing") {
        target = 0.2 + 0.1 * Math.sin(performance.now() / 300);
      }
      levelRef.current = levelRef.current * 0.75 + target * 0.25;
      setLevel(Math.round(levelRef.current * 1000) / 1000);
      rafRef.current = requestAnimationFrame(tick);
    }
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [setLevel]);

  // ---- Reconhecimento de voz (STT) ----
  function ensureRecognition(): any {
    if (recogRef.current) return recogRef.current;
    const SR =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setSupported(false);
      return null;
    }
    const r = new SR();
    r.lang = "pt-BR";
    r.continuous = true;
    r.interimResults = false;
    r.onresult = (e: any) => {
      const res = e.results[e.results.length - 1];
      if (!res.isFinal) return;
      const text = (res[0].transcript || "").trim();
      if (text) onUserSpeech(text);
    };
    r.onerror = () => {};
    r.onend = () => {
      // o reconhecimento para sozinho às vezes: reinicia se ainda estamos ouvindo
      if (micActiveRef.current && !speakingRef.current) {
        try {
          r.start();
        } catch {
          /* já iniciado */
        }
      }
    };
    recogRef.current = r;
    return r;
  }

  function onUserSpeech(text: string) {
    addLog("user", text);
    setMode("processing");
    const sock = wsRef.current;
    if (sock && sock.readyState === WebSocket.OPEN) {
      sock.send(JSON.stringify({ type: "command_text", text }));
    }
  }

  // ---- Síntese de voz (TTS) ----
  function pickVoice(): SpeechSynthesisVoice | null {
    const voices = window.speechSynthesis.getVoices();
    return (
      voices.find((v) => /pt[-_]?BR/i.test(v.lang)) ||
      voices.find((v) => /pt/i.test(v.lang)) ||
      null
    );
  }

  function speak(text: string) {
    if (!("speechSynthesis" in window)) {
      backToListening();
      return;
    }
    try {
      recogRef.current?.stop();
    } catch {
      /* noop */
    }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "pt-BR";
    const v = pickVoice();
    if (v) u.voice = v;
    u.onstart = () => {
      speakingRef.current = true;
      setMode("speaking");
    };
    u.onend = () => {
      speakingRef.current = false;
      backToListening();
    };
    u.onerror = () => {
      speakingRef.current = false;
      backToListening();
    };
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }

  function backToListening() {
    if (micActiveRef.current) {
      setMode("listening");
      try {
        recogRef.current?.start();
      } catch {
        /* já iniciado */
      }
    } else {
      setMode("idle");
    }
  }

  // ---- Microfone (liga/desliga toda a pipeline de voz) ----
  async function startMic() {
    const r = ensureRecognition();
    if (!r) return;
    micActiveRef.current = true;
    setMicActive(true);
    // analyser para o nível REAL do microfone (visualizador reativo)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const ctx = new AudioContext();
      audioCtxRef.current = ctx;
      const an = ctx.createAnalyser();
      an.fftSize = 512;
      ctx.createMediaStreamSource(stream).connect(an);
      analyserRef.current = an;
    } catch {
      /* sem analyser: o visualizador ainda anima por estado */
    }
    setMode("listening");
    try {
      r.start();
    } catch {
      /* já iniciado */
    }
  }

  function stopMic() {
    micActiveRef.current = false;
    setMicActive(false);
    try {
      recogRef.current?.stop();
    } catch {
      /* noop */
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
    analyserRef.current = null;
    setMode(useStore.getState().connected ? "idle" : "disconnected");
  }

  const toggleMic = useCallback(() => {
    if (micActiveRef.current) stopMic();
    else void startMic();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { toggleMic };
}
