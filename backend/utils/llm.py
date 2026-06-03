import os
import logging
from backend.config import (
    GEMINI_API_KEY,
    USE_VERTEX_AI,
    VERTEX_PROJECT_ID,
    VERTEX_LOCATION,
)

logger = logging.getLogger(__name__)

# Initialisation globale Vertex AI
vertex_available = False
if USE_VERTEX_AI:
    try:
        import vertexai
        vertexai.init(project=VERTEX_PROJECT_ID, location=VERTEX_LOCATION)
        vertex_available = True
        logger.info(f"Vertex AI initialisé avec succès sur le projet {VERTEX_PROJECT_ID}.")
    except Exception as e:
        logger.error(f"Erreur d'initialisation de Vertex AI : {e}. Utilisation du fallback API Gemini.")

# 1. Utilitaire pour récupérer le client brut (pour l'extraction ou le chatbot)
def get_generative_model(model_name: str, system_instruction: str = None):
    """
    Retourne un GenerativeModel brut (google.generativeai ou Vertex AI).
    Le model_name doit être spécifié explicitement par l'appelant.
    """
    if USE_VERTEX_AI and vertex_available:
        try:
            from vertexai.generative_models import GenerativeModel
            return GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
        except Exception as e:
            logger.error(f"Impossible de charger le modèle Vertex AI : {e}. Fallback vers Gemini API.")

    # Fallback standard Gemini API (Google AI Studio)
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            return genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
        except Exception as e:
            logger.error(f"Erreur d'initialisation du modèle Gemini API : {e}")

    return None

# 2. Utilitaire pour récupérer le modèle LangChain (utilisé par le générateur LangGraph)
def get_langchain_llm(model_name: str, thinking_budget: int = 0, temperature: float = 0.7):
    """
    Retourne un LLM LangChain avec le modèle et le thinking budget spécifiés.
    
    Args:
        model_name: Nom du modèle Gemini (ex: gemini-2.5-flash, gemini-2.5-pro)
        thinking_budget: -1 = dynamique, 0 = désactivé, N = budget fixe en tokens
        temperature: Température de génération (0.0 à 1.0)
    """
    if USE_VERTEX_AI and vertex_available:
        try:
            from langchain_google_vertexai import ChatVertexAI
            return ChatVertexAI(
                model_name=model_name,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Erreur d'initialisation de ChatVertexAI : {e}. Fallback vers Gemini API.")

    if GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            kwargs = {
                "model": model_name,
                "google_api_key": GEMINI_API_KEY,
                "temperature": temperature,
            }
            # Activer le thinking uniquement pour les modèles 2.5+ qui le supportent
            if thinking_budget != 0 and ("2.5" in model_name or "3" in model_name):
                kwargs["thinking_budget"] = thinking_budget
            return ChatGoogleGenerativeAI(**kwargs)
        except Exception as e:
            logger.error(f"Erreur d'initialisation de ChatGoogleGenerativeAI : {e}")

    return None
