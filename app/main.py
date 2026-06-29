"""Application entrypoint."""

import tkinter as tk

from loguru import logger

from app.config import Config
from app.logging_setup import configure_logging
from app.services.gemini import configure_gemini
from app.ui.app import ArisApp


def main() -> None:
    """Função principal"""
    configure_logging()

    logger.info("=" * 60)
    logger.info("ARIS AI Assistant - Iniciando")
    logger.info("=" * 60)

    # Verifica configurações
    erros = Config.validar()
    if erros:
        logger.warning(f"Avisos de configuração: {erros}")

    # Configura Gemini se disponível
    configure_gemini()

    # Inicia interface
    root = tk.Tk()
    app = ArisApp(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
    finally:
        logger.info("ARIS encerrado")


if __name__ == "__main__":
    main()
