// Histórico de interações: transcrições do usuário e respostas do ARIS,
// com timestamp, em fonte monoespaçada. Rola sozinho para a última linha.
import { useEffect, useRef } from "react";
import { useStore } from "../state/store";

export function Log() {
  const log = useStore((s) => s.log);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight });
  }, [log]);

  return (
    <div className="flex w-full max-w-md flex-col rounded-xl border border-edge bg-panel">
      <div className="px-4 py-2 text-sm text-content/80">Histórico de Interações</div>
      <div ref={ref} className="h-48 overflow-y-auto rounded-b-xl bg-panel-inner px-4 py-3 font-mono text-xs leading-relaxed">
        {log.length === 0 ? (
          <div className="text-muted">Sem interações ainda. Fale ou digite um comando, senhor.</div>
        ) : (
          log.map((e) => (
            <div key={e.id} className="mb-1">
              <span className="text-muted">[{e.time}] </span>
              <span className={e.who === "user" ? "text-user-line" : "text-primary"}>
                {e.who === "user" ? "Você: " : "ÁRIS: "}
                {e.text}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
