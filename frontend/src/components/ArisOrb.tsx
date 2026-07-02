// Orb central: anel de spokes girando + glow reativo + GLOBO 3D (Three.js) no
// núcleo, com "ÁRIS" sobreposto. Menor que a versão anterior.
import { useStore } from "@/state/store";
import { ArisGlobe } from "./ArisGlobe";

export default function ArisOrb() {
  const level = useStore((s) => s.level);

  return (
    <div className="relative w-[240px] h-[240px] flex items-center justify-center">
      {/* anel de spokes (index.css) */}
      <div className="absolute orbit-ring" />
      {/* glow reativo ao áudio */}
      <div
        className="absolute w-[170px] h-[170px] rounded-full blur-3xl bg-cyan-400/30"
        style={{ opacity: 0.22 + level * 0.6, transform: `scale(${1 + level * 0.2})` }}
      />
      {/* globo 3D + texto */}
      <div className="relative w-[188px] h-[188px]">
        <ArisGlobe />
        <span
          className="absolute inset-0 flex items-center justify-center text-3xl  tracking-[6px] text-white pointer-events-none"
          style={{ textShadow: "0 0 18px rgba(47,210,255,0.6)" }}
        >
          ÁRIS
        </span>
      </div>
    </div>
  );
}
