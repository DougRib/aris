"""Perfil do usuário — fatos e preferências persistidos em JSON.

Coisas estáveis sobre o usuário ("prefere café às 8h", "trabalha com Python")
que o Orchestrator injeta no prompt para personalizar as respostas. Diferente
da memória episódica (longo prazo), aqui são poucos fatos curados.
"""

import json
from pathlib import Path

from loguru import logger


class UserProfile:
    """Conjunto de fatos sobre o usuário, gravado em disco."""

    def __init__(self, arquivo: Path) -> None:
        self._arquivo = Path(arquivo)
        self._fatos: dict[str, str] = {}
        self._carregar()

    def set_fact(self, chave: str, valor: str) -> None:
        """Registra/atualiza um fato (chave normalizada evita duplicatas)."""
        chave = " ".join(chave.lower().split())
        self._fatos[chave] = valor.strip()
        self._salvar()

    def all(self) -> dict[str, str]:
        return dict(self._fatos)

    def as_prompt_context(self) -> str:
        """Fatos formatados para injeção no prompt (ou '')."""
        if not self._fatos:
            return ""
        return "\n".join(f"- {v}" for v in self._fatos.values())

    def _carregar(self) -> None:
        try:
            if self._arquivo.exists():
                self._fatos = json.loads(self._arquivo.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao carregar perfil: {exc}")

    def _salvar(self) -> None:
        try:
            self._arquivo.parent.mkdir(parents=True, exist_ok=True)
            self._arquivo.write_text(
                json.dumps(self._fatos, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Erro ao salvar perfil: {exc}")
