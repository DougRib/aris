// Visualizador central reativo: um anel de barras que responde ao nível de
// áudio (voz do usuário ao ouvir, ou animação ao falar) e um núcleo em
// gradiente que pulsa. A cor e o rótulo refletem o modo atual do ARIS.
import { useStore } from "../state/store";
import type { Mode } from "../types";

const SIZE = 300;
const C = SIZE / 2;
const R_INNER = 78;
const BARS = 64;

const MODE_INFO: Record<Mode, { label: string; color: string }> = {
  disconnected: { label: "Desconectado", color: "var(--color-muted)" },
  idle: { label: "Pronto", color: "var(--color-primary)" },
  listening: { label: "Ouvindo", color: "var(--color-success)" },
  processing: { label: "Processando", color: "var(--color-violet)" },
  speaking: { label: "Falando", color: "var(--color-primary-glow)" },
};

export function Hud() {
  const level = useStore((s) => s.level);
  const mode = useStore((s) => s.mode);
  const info = MODE_INFO[mode];

  const t = performance.now() / 220;
  const bars = Array.from({ length: BARS }, (_, i) => {
    const ang = (i / BARS) * Math.PI * 2 - Math.PI / 2;
    const phase = Math.sin(i * 0.8 + t) * 0.5 + 0.5; // ondulação por barra
    const amp = (5 + level * 52) * (0.3 + 0.7 * phase);
    const r2 = R_INNER + amp;
    return {
      x1: C + Math.cos(ang) * R_INNER,
      y1: C + Math.sin(ang) * R_INNER,
      x2: C + Math.cos(ang) * r2,
      y2: C + Math.sin(ang) * r2,
    };
  });

  const coreScale = 1 + level * 0.18;

  return (
    <div className="relative flex flex-col items-center">
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
        <defs>
          <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--color-primary)" />
            <stop offset="100%" stopColor="var(--color-violet)" />
          </linearGradient>
          <radialGradient id="coreGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--color-primary-glow)" stopOpacity="0.95" />
            <stop offset="55%" stopColor="var(--color-primary)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-violet)" stopOpacity="0.05" />
          </radialGradient>
        </defs>

        {/* halo externo */}
        <circle cx={C} cy={C} r={R_INNER + 64} fill="none" stroke={info.color} strokeOpacity="0.12" strokeWidth="1" />
        <circle cx={C} cy={C} r={R_INNER - 6} fill="none" stroke={info.color} strokeOpacity="0.25" strokeWidth="1" />

        {/* núcleo em gradiente, pulsando com o nível */}
        <circle
          cx={C}
          cy={C}
          r={R_INNER - 10}
          fill="url(#coreGrad)"
          style={{ transformOrigin: "center", transform: `scale(${coreScale})`, transition: "transform 60ms linear" }}
        />

        {/* barras reativas */}
        <g stroke="url(#barGrad)" strokeWidth="3" strokeLinecap="round">
          {bars.map((b, i) => (
            <line key={i} x1={b.x1} y1={b.y1} x2={b.x2} y2={b.y2} />
          ))}
        </g>

        {/* marca central */}
        <text x={C} y={C + 7} textAnchor="middle" fill="var(--color-content)" fontSize="20" fontWeight="700" letterSpacing="3">
          ÁRIS
        </text>
      </svg>

      <div className="mt-1 text-sm font-semibold tracking-[0.2em] uppercase" style={{ color: info.color }}>
        {info.label}
      </div>
    </div>
  );
}
