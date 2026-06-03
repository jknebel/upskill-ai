import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration Gemini API (Google AI Studio)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Configuration Vertex AI (GCP)
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"

# --- Modèles dédiés par agent ---
MODEL_CHATBOT = os.getenv("MODEL_CHATBOT", "gemini-2.0-flash-lite")       # Chatbot conversationnel (rapide, pas de thinking)
MODEL_EXTRACTOR = os.getenv("MODEL_EXTRACTOR", "gemini-2.5-flash")        # Extracteur de lacunes (thinking activé)
MODEL_TEACHER = os.getenv("MODEL_TEACHER", "gemini-2.5-flash")            # Prof A & Prof B (thinking activé)
MODEL_DIRECTOR = os.getenv("MODEL_DIRECTOR", "gemini-2.5-pro")            # Directeur vérificateur (thinking activé)
MODEL_PODCAST = os.getenv("MODEL_PODCAST", "gemini-2.5-pro")              # Générateur de podcast (pas de thinking)
MODEL_EMBEDDING = os.getenv("MODEL_EMBEDDING", "gemini-embedding-2")      # Embeddings vectoriels

# --- Thinking budgets par agent (-1 = dynamique, 0 = désactivé) ---
THINKING_CHATBOT = int(os.getenv("THINKING_CHATBOT", "0"))
THINKING_EXTRACTOR = int(os.getenv("THINKING_EXTRACTOR", "-1"))
THINKING_TEACHER = int(os.getenv("THINKING_TEACHER", "-1"))
THINKING_DIRECTOR = int(os.getenv("THINKING_DIRECTOR", "-1"))
THINKING_PODCAST = int(os.getenv("THINKING_PODCAST", "0"))



# Configuration de l'analyse
CLUSTERING_THRESHOLD = float(os.getenv("CLUSTERING_THRESHOLD", "3.0"))  # Poids cumulé requis pour générer un cours
DECAY_RATE_LAMBDA = float(os.getenv("DECAY_RATE_LAMBDA", "0.05"))      # Taux de dépréciation journalier (lambda)

# Paramètres de simulation / stockage (pour le POC)
# Pour que le POC soit simple et autonome sans base de données externe obligatoire,
# nous créons une structure de stockage locale en mémoire/JSON, tout en étant
# compatible avec l'intégration Firebase Firestore ultérieure.
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
