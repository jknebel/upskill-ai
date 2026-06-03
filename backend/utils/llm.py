import os
import logging
from backend.config import (
    GEMINI_API_KEY, 
    MODEL_NAME, 
    USE_VERTEX_AI, 
    VERTEX_PROJECT_ID, 
    VERTEX_LOCATION, 
    ENABLE_THINKING, 
    THINKING_MODEL
)

logger = logging.getLogger(__name__)

# Initialisation globale
vertex_available = False
if USE_VERTEX_AI:
    try:
        import vertexai
        vertexai.init(project=VERTEX_PROJECT_ID, location=VERTEX_LOCATION)
        vertex_available = True
        logger.info(f"Vertex AI initialisé avec succès sur le projet {VERTEX_PROJECT_ID}.")
    except Exception as e:
        logger.error(f"Erreur d'initialisation de Vertex AI : {e}. Utilisation du fallback API Gemini.")

# 1. Utilitaire pour récupérer le client brut (pour l'extraction rapide ou le chatbot)
def get_generative_model(model_name: str = None, system_instruction: str = None):
    # Choisir le modèle (thinking vs standard)
    if not model_name:
        model_name = THINKING_MODEL if ENABLE_THINKING else MODEL_NAME

    if USE_VERTEX_AI and vertex_available:
        try:
            from vertexai.generative_models import GenerativeModel
            # Le modèle thinking n'est pas forcément disponible sur le même nom dans Vertex, ajuster au besoin
            v_model_name = model_name
            if "thinking" in model_name and not model_name.startswith("projects/"):
                v_model_name = "gemini-2.0-flash-thinking-exp" # Nom standard Vertex
            
            return GenerativeModel(
                model_name=v_model_name,
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
def get_langchain_llm(model_name: str = None, temperature: float = 0.7):
    if not model_name:
        model_name = THINKING_MODEL if ENABLE_THINKING else MODEL_NAME
        
    if USE_VERTEX_AI and vertex_available:
        try:
            from langchain_google_vertexai import ChatVertexAI
            v_model_name = model_name
            if "thinking" in model_name:
                v_model_name = "gemini-2.0-flash-thinking-exp"
            return ChatVertexAI(
                model_name=v_model_name,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Erreur d'initialisation de ChatVertexAI : {e}. Fallback vers Gemini API.")

    if GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=GEMINI_API_KEY,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Erreur d'initialisation de ChatGoogleGenerativeAI : {e}")
            
    return None
