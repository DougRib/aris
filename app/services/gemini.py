"""Gemini AI service."""

from loguru import logger
import google.generativeai as genai

from app.config import Config


def configure_gemini() -> None:
    """Configura o SDK do Gemini se disponível."""
    if Config.GEMINI_KEY:
        try:
            genai.configure(api_key=Config.GEMINI_KEY)
            logger.info("Google Gemini configurado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar Gemini: {e}")


class GeminiService:
    """Serviço de IA (Google Gemini)"""

    def __init__(self):
        self.model = None
        self.chat = None
        if Config.GEMINI_KEY:
            try:
                self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
                self.chat = self.model.start_chat(history=[])
                logger.info("Gemini chat iniciado")
            except Exception as e:
                logger.error(f"Erro ao iniciar Gemini: {e}")

    def pesquisar(self, pergunta: str) -> str:
        """Pesquisa usando Gemini"""
        if not self.model:
            return "Serviço de IA não configurado. Configure GEMINI_KEY no arquivo .env"

        try:
            regras = """
            Responda como ÁRIS, assistente de IA avançado:
            - Seja direto, educado e profissional
            - Use no máximo 40 palavras
            - Mantenha tom amigável mas respeitoso
            - Se não souber, admita
            """

            prompt = f"{regras}\n\nPergunta: {pergunta}"
            resposta = self.chat.send_message(prompt)

            logger.info(f"Resposta Gemini obtida para: {pergunta[:50]}...")
            return resposta.text

        except Exception as e:
            logger.error(f"Erro ao consultar Gemini: {e}")
            return "Desculpe, não consegui processar sua pergunta no momento."
