// Navegação inferior (vidro) — placeholders para telas futuras.
import { Home, Grid2X2, Clock3, Settings } from "lucide-react";

export default function BottomNavigation() {
  return (
    <div className="mx-6 mb-6 h-16 rounded-full glass flex items-center justify-around">
      <Home size={20} className="text-cyan-300" />
      <Grid2X2 size={20} className="text-slate-400" />
      <div className="grad-anim w-12 h-12 rounded-full shadow-[0_0_28px_rgba(0,255,255,.35)]" />
      <Clock3 size={20} className="text-slate-400" />
      <Settings size={20} className="text-slate-400" />
    </div>
  );
}
