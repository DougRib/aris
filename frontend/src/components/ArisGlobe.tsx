// Globo 3D (Three.js via React Three Fiber): esferas wireframe girando, com um
// núcleo translúcido. Reage ao nível de áudio (escala/giro), lido do store sem
// causar re-render (useFrame + getState).
import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Group, Mesh } from "three";
import { useStore } from "@/state/store";

function Globe() {
  const grupo = useRef<Group>(null!);
  const interno = useRef<Mesh>(null!);

  useFrame((_state, delta) => {
    const level = useStore.getState().level;
    if (grupo.current) {
      grupo.current.rotation.y += delta * 0.25;
      grupo.current.rotation.x += delta * 0.07;
      grupo.current.scale.setScalar(1 + level * 0.18);
    }
    if (interno.current) {
      interno.current.rotation.y -= delta * 0.18;
      interno.current.rotation.z += delta * 0.05;
    }
  });

  return (
    <group ref={grupo}>
      {/* casca externa wireframe (cyan) */}
      <mesh>
        <icosahedronGeometry args={[1.3, 1]} />
        <meshBasicMaterial color="#2fd2ff" wireframe transparent opacity={0.55} />
      </mesh>
      {/* casca interna wireframe (violeta), gira ao contrário */}
      <mesh ref={interno}>
        <icosahedronGeometry args={[1.05, 2]} />
        <meshBasicMaterial color="#8a5cff" wireframe transparent opacity={0.35} />
      </mesh>
      {/* núcleo translúcido para dar profundidade */}
      <mesh>
        <sphereGeometry args={[0.82, 32, 32]} />
        <meshBasicMaterial color="#0b2c52" transparent opacity={0.6} />
      </mesh>
    </group>
  );
}

export function ArisGlobe() {
  return (
    <Canvas
      camera={{ position: [0, 0, 3.4], fov: 50 }}
      gl={{ antialias: true, alpha: true }}
      dpr={[1, 2]}
      style={{ background: "transparent" }}
    >
      <Globe />
    </Canvas>
  );
}
