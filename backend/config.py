import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration Gemini API (Google AI Studio)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash") # gemini-2.5-flash est le plus récent et le plus rapide

# Configuration Vertex AI (GCP)
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1") # e.g. us-central1

# Paramètre pour utiliser Vertex AI à la place de l'API Gemini standard
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"

# Configuration du mode Thinking/Réflexion
ENABLE_THINKING = os.getenv("ENABLE_THINKING", "true").lower() == "true"
THINKING_MODEL = os.getenv("THINKING_MODEL", "gemini-2.0-flash-thinking-exp")


# Configuration de l'analyse
CLUSTERING_THRESHOLD = float(os.getenv("CLUSTERING_THRESHOLD", "3.0"))  # Poids cumulé requis pour générer un cours
DECAY_RATE_LAMBDA = float(os.getenv("DECAY_RATE_LAMBDA", "0.05"))      # Taux de dépréciation journalier (lambda)

# Paramètres de simulation / stockage (pour le POC)
# Pour que le POC soit simple et autonome sans base de données externe obligatoire,
# nous créons une structure de stockage locale en mémoire/JSON, tout en étant
# compatible avec l'intégration Firebase Firestore ultérieure.
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
