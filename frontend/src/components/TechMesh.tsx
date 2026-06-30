// Malha tecnológica de fundo (estilo Jarvis): nós flutuantes conectados por
// linhas — uma "constelação" sutil desenhada num canvas, atrás do conteúdo.
import { useEffect, useRef } from "react";

const N = 42;

export function TechMesh() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let w = 0;
    let h = 0;
    let raf = 0;

    const nodes = Array.from({ length: N }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.0007,
      vy: (Math.random() - 0.5) * 0.0007,
    }));

    function resize() {
      if (!canvas) return;
      w = canvas.width = canvas.offsetWidth * dpr;
      h = canvas.height = canvas.offsetHeight * dpr;
    }
    resize();
    window.addEventListener("resize", resize);

    const maxDist = 130 * dpr;

    function draw() {
      ctx!.clearRect(0, 0, w, h);
      for (const n of nodes) {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > 1) n.vx *= -1;
        if (n.y < 0 || n.y > 1) n.vy *= -1;
      }
      // linhas entre nós próximos
      for (let i = 0; i < N; i++) {
        for (let j = i + 1; j < N; j++) {
          const a = nodes[i];
          const b = nodes[j];
          const dx = (a.x - b.x) * w;
          const dy = (a.y - b.y) * h;
          const d = Math.hypot(dx, dy);
          if (d < maxDist) {
            ctx!.strokeStyle = `rgba(47,210,255,${0.14 * (1 - d / maxDist)})`;
            ctx!.lineWidth = dpr;
            ctx!.beginPath();
            ctx!.moveTo(a.x * w, a.y * h);
            ctx!.lineTo(b.x * w, b.y * h);
            ctx!.stroke();
          }
        }
      }
      // nós
      ctx!.fillStyle = "rgba(123,231,255,0.5)";
      for (const n of nodes) {
        ctx!.beginPath();
        ctx!.arc(n.x * w, n.y * h, 1.4 * dpr, 0, Math.PI * 2);
        ctx!.fill();
      }
      raf = requestAnimationFrame(draw);
    }
    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={ref} className="absolute inset-0 h-full w-full opacity-70" />;
}
