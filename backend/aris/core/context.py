"""Context — estado de uma interação, repassado a cada skill.

Carrega os callbacks de voz (speak/listen) para que skills que precisam de
diálogo ("de qual cidade?") funcionem sem conhecer a UI, além de entidades
extraídas e o flag de modo privado.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Context:
    """Contexto de uma única interação com o ARIS."""

    speak: Callable[[str], None]
    listen: Callable[..., str]
    entities: dict[str, Any] = field(default_factory=dict)
    private_mode: bool = False
