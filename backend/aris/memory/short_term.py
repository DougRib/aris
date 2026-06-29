"""Memória de curto prazo — histórico recente da sessão, persistido em JSON.

Porta o antigo MemoryManager e adiciona as_prompt_context(), que entrega o
histórico já formatado para o Orchestrator injetar no prompt do LLM (antes a
memória era persistida mas nunca realimentava o raciocínio).
"""

import json
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock

from loguru import logger


class ShortTermMemory:
    """Histórico circular thread-safe das últimas interações."""

    def __init__(self, max_items: int, arquivo: Path) -> None:
        self._max = max_items
        self._arquivo = Path(arquivo)
        self._itens: deque[dict[str, str]] = deque(maxlen=max_items)
        self._lock = Lock()
        self.private_mode = False
        self.carregar()

    def registrar(self, entrada: str, resposta: str) -> None:
        """Registra uma interação, exceto em modo privado."""
        if self.private_mode:
            return
        with self._lock:
            self._itens.append(
                {
                    "hora": datetime.now().strftime("%H:%M"),
                    "entrada": entrada,
                    "resposta": resposta,
                }
            )

    def as_prompt_context(self) -> str:
        """Retorna o histórico recente formatado para injeção no prompt do LLM."""
        with self._lock:
            if not self._itens:
                return ""
            return "\n".join(
                f"[{m['hora']}] Usuário: {m['entrada']} | ÁRIS: {m['resposta']}"
                for m in self._itens
            )

    def obter_resumo(self) -> str:
        """Resumo legível para quando o usuário pede 'o que falamos'."""
        contexto = self.as_prompt_context()
        if not contexto:
            return "Ainda não tenho registros recentes, senhor."
        return "Aqui está um resumo das nossas últimas interações:\n" + contexto

    def salvar(self) -> None:
        """Persiste a memória em disco, exceto em modo privado."""
        if self.private_mode:
            return
        try:
            self._arquivo.parent.mkdir(parents=True, exist_ok=True)
            with self._lock, open(self._arquivo, "w", encoding="utf-8") as f:
                json.dump(
                    {"atualizado": datetime.now().isoformat(), "memoria": list(self._itens)},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao salvar memória: {exc}")

    def carregar(self) -> None:
        """Carrega a memória do disco, se o arquivo existir."""
        try:
            if self._arquivo.exists():
                with open(self._arquivo, encoding="utf-8") as f:
                    dados = json.load(f)
                self._itens = deque(dados.get("memoria", []), maxlen=self._max)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao carregar memória: {exc}")
