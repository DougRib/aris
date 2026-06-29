// HUD central: anel/arcos que refletem o estado do ARIS (ouvindo, processando,
// falando…). Cor, velocidade de rotação dos arcos e pulso variam por estado.
import { useStore } from "../state/store";
import type { VoiceState } from "../types";

interface Visual {
  label: string;
  color: string;
  spin: number; // segundos por volta (0 = parado)
  pulse: boolean;
}

const VISUALS: Record<VoiceState, Visual> = {
  disconnected: { label: "Desconectado", color: "var(--color-muted)", spin: 0, pulse: false },
  idle: { label: "Online", color: "var(--color-primary)", spin: 22, pulse: false },
  listening: { label: "Ouvindo…", color: "var(--color-warning)", spin: 12, pulse: true },
  processing: { label: "Processando…", color: "var(--color-primary-glow)", spin: 5, pulse: false },
  speaking: { label: "Falando…", color: "var(--color-primary)", spin: 8, pulse: true },
  starting: { label: "Iniciando voz…", color: "var(--color-primary-glow)", spin: 8, pulse: false },
  stopped: { label: "Voz parada", color: "var(--color-muted)", spin: 0, pulse: false },
  voice_unavailable: { label: "Voz indisponível", color: "var(--color-danger)", spin: 0, pulse: false },
};

const TICKS = Array.from({ length: 12 }, (_, i) => i * 30);

export function Hud() {
  const voiceState = useStore((s) => s.voiceState);
  const v = VISUALS[voiceState];
  const spinStyle = v.spin ? { animation: `aris-spin ${v.spin}s linear infinite`, transformOrigin: "center" } : undefined;
  const pulseStyle = v.pulse
    ? { animation: "aris-pulse 1.4s ease-in-out infinite", transformBox: "fill-box" as const, transformOrigin: "center" }
    : undefined;

  return (
    <div className="flex flex-col items-center gap-3">
      <svg width="240" height="240" viewBox="0 0 240 240">
        {/* anel de brilho externo */}
        <circle cx="120" cy="120" r="112" fill="none" stroke={v.color} strokeOpacity="0.25" strokeWidth="1" />

        {/* arcos rotativos */}
        <g style={spinStyle}>
          <circle cx="120" cy="120" r="100" fill="none" stroke={v.color} strokeOpacity="0.8" strokeWidth="2" strokeDasharray="70 320" strokeLinecap="round" />
          <circle cx="120" cy="120" r="100" fill="none" stroke={v.color} strokeOpacity="0.5" strokeWidth="2" strokeDasharray="40 200" strokeDashoffset="180" strokeLinecap="round" />
        </g>

        {/* ticks ao redor */}
        {TICKS.map((deg) => {
          const rad = (deg * Math.PI) / 180;
          const x1 = 120 + Math.cos(rad) * 84;
          const y1 = 120 + Math.sin(rad) * 84;
          const x2 = 120 + Math.cos(rad) * 92;
          const y2 = 120 + Math.sin(rad) * 92;
          return <line key={deg} x1={x1} y1={y1} x2={x2} y2={y2} stroke={v.color} strokeOpacity="0.4" strokeWidth="1" />;
        })}

        {/* anel principal + núcleo (pulsa ao falar) */}
        <g style={pulseStyle}>
          <circle cx="120" cy="120" r="78" fill="none" stroke={v.color} strokeWidth="3" />
          <circle cx="120" cy="120" r="52" fill="var(--color-neon-core)" stroke={v.color} strokeOpacity="0.5" strokeWidth="1" />
        </g>

        {/* marca central */}
        <text x="120" y="128" textAnchor="middle" fill={v.color} fontSize="22" fontFamily="var(--font-display)" fontWeight="700" letterSpacing="2">
          ÁRIS
        </text>
      </svg>

      <div className="text-sm font-semibold tracking-wide" style={{ color: v.color }}>
        {v.label}
      </div>
    </div>
  );
}
