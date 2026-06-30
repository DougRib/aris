// Transcrição compacta: as últimas falas (usuário e ARIS), centralizadas.
import { useStore } from "../state/store";

export function Transcript() {
  const log = useStore((s) => s.log);
  const ultimas = log.slice(-4);

  return (
    <div className="flex min-h-16 w-full flex-col justify-end gap-1 text-center text-sm">
      {ultimas.length === 0 ? (
        <p className="text-muted">Toque no microfone e fale, senhor.</p>
      ) : (
        ultimas.map((e) => (
          <p key={e.id} className={e.who === "user" ? "text-user-line/90" : "text-primary"}>
            <span className="text-muted">{e.who === "user" ? "você: " : "áris: "}</span>
            {e.text}
          </p>
        ))
      )}
    </div>
  );
}
