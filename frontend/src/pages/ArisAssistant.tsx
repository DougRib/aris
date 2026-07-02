// Página principal do ARIS (estilo app). Moldura com gradiente animado, malha
// tecnológica de fundo, globo 3D reativo, e estado dinâmico (PRONTO/OUVINDO…).
import ArisHeader from "@/components/ArisHeader";
import ArisOrb from "@/components/ArisOrb";
import VoiceButton from "@/components/VoiceButton";
import SuggestionCard from "@/components/SuggestionCard";
import BottomNavigation from "@/components/BottomNavigation";
import { Waveform } from "@/components/Waveform";
import { TechMesh } from "@/components/TechMesh";
import { useAris } from "@/hooks/useAris";
import { useStore } from "@/state/store";
import type { Mode } from "@/types";

const LABEL: Record<Mode, string> = {
  disconnected: "OFFLINE",
  idle: "PRONTO",
  listening: "OUVINDO",
  processing: "PROCESSANDO",
  speaking: "FALANDO",
};

export default function ArisAssistant() {
  const { toggleMic } = useAris();
  const mode = useStore((s) => s.mode);

  return (
    <div className="min-h-screen flex justify-center items-center p-5">
      {/* moldura com gradiente animado em tempo real */}
      <div
        className="grad-anim rounded-[42px] p-[1.5px]"
        style={{ boxShadow: "0 0 90px -28px var(--color-violet), 0 0 44px -22px var(--color-primary)" }}
      >
        <div className="relative w-[400px] h-[800px] max-h-[96vh] rounded-[40px] overflow-hidden bg-[#050a16]">
          {/* malha tecnológica + leve gradiente */}
          <TechMesh />
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-purple-500/10" />

          <div className="relative z-10 h-full flex flex-col">
            <ArisHeader />

            <div className="flex-1 flex flex-col items-center pt-2">
              {/* globo + waveform reativa atrás */}
              <div className="relative flex h-[258px] w-full items-center justify-center">
                <Waveform />
                <div className="relative z-10">
                  <ArisOrb />
                </div>
              </div>

              <h3 className="mt-3 tracking-[7px] text-sm text-cyan-300">{LABEL[mode]}</h3>

              <VoiceButton onToggle={toggleMic} />

              <SuggestionCard />
            </div>

            <BottomNavigation />
          </div>
        </div>
      </div>
    </div>
  );
}
