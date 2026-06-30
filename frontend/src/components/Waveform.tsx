// Waveform horizontal reativa: barras espelhadas que saem dos lados do orb e
// reagem ao nível de áudio (voz do usuário ao ouvir, animação ao falar).
// Gradiente magenta (esquerda) → cyan (direita), como numa onda sonora.
import { useStore } from "../state/store";

const W = 360;
const H = 150;
const MID = H / 2;
const GAP = 112; // começa FORA do anel de spokes, na faixa lateral visível
const STEP = 5;

export function Waveform() {
  const level = useStore((s) => s.level);
  const mode = useStore((s) => s.mode);
  const active = mode === "listening" || mode === "speaking";
  const t = performance.now() / 130;

  const bars: { x: number; h: number }[] = [];
  for (let x = 6; x <= W - 6; x += STEP) {
    const d = Math.abs(x - W / 2);
    if (d < GAP) continue; // deixa o centro livre pro núcleo do orb
    // taper: alto perto do orb, suave até as bordas (não some)
    const taper = Math.max(0.3, 1 - (d - GAP) / (W / 2 - GAP));
    const wave = 0.4 + 0.6 * Math.abs(Math.sin(x * 0.16 + t));
    const amp = active ? 0.55 + level * 0.8 : 0.5;
    const h = 5 + taper * 110 * wave * amp;
    bars.push({ x, h });
  }

  return (
    <svg
      className="absolute inset-0 h-full w-full"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <linearGradient id="waveGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="var(--color-magenta)" />
          <stop offset="50%" stopColor="var(--color-violet)" />
          <stop offset="100%" stopColor="var(--color-primary)" />
        </linearGradient>
      </defs>
      <g stroke="url(#waveGrad)" strokeWidth="2.5" strokeLinecap="round">
        {bars.map((b, i) => (
          <line key={i} x1={b.x} y1={MID - b.h / 2} x2={b.x} y2={MID + b.h / 2} opacity={0.85} />
        ))}
      </g>
    </svg>
  );
}
