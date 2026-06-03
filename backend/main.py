from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import logging

from backend.config import GEMINI_API_KEY, MODEL_NAME
from backend.agents.extractor import PromptExtractor
from backend.agents.generator import generate_learning_assets
from backend.utils.clustering import find_learning_needs
from backend.utils.storage import JSONStorage

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialiser FastAPI et le stockage local
app = FastAPI(title="Upskill AI API", version="1.0.0")
storage = JSONStorage()
extractor = PromptExtractor()

# Configurer le CORS pour permettre au frontend React de communiquer avec l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En développement local, autoriser tout
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles de données Pydantic pour les requêtes
class ChatRequest(BaseModel):
    user_id: str
    message: str

class TriggerRequest(BaseModel):
    user_id: str

class LoadDemoRequest(BaseModel):
    user_id: str
    scenario: str # 'pandas', 'docker', 'upskill'

# --- ENDPOINTS ---

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "gemini_key_configured": bool(GEMINI_API_KEY)}

@app.post("/api/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    user_id = request.user_id
    user_message = request.message
    
    # 1. Enregistrer le message utilisateur dans l'historique
    storage.save_chat_message(user_id, "user", user_message)
    
    # 2. Générer la réponse de l'assistant (avec Gemini ou mock local)
    assistant_response = ""
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel(MODEL_NAME)
            # Récupérer l'historique récent pour donner du contexte au modèle
            history = storage.get_chat_history(user_id)[-10:]
            chat_history_gemini = []
            for msg in history:
                if msg["id"] == user_message: # Éviter de dupliquer le dernier message
                    continue
                chat_history_gemini.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [msg["content"]]
                })
            
            chat_session = model.start_chat(history=chat_history_gemini[:-1] if len(chat_history_gemini) > 0 else None)
            response = chat_session.send_message(user_message)
            assistant_response = response.text
        except Exception as e:
            logger.error(f"Erreur lors de l'appel Gemini : {e}")
            assistant_response = f"Désolé, j'ai rencontré une erreur. Voici une réponse locale simulée. Tu as dit : '{user_message}'"
    else:
        # Mock de réponse de chat local si pas de clé API
        msg_lower = user_message.lower()
        if "pandas" in msg_lower:
            assistant_response = "Pour fusionner deux DataFrames en Pandas, tu peux utiliser `pd.merge(df1, df2, on='colonne_commune')`. Si tes colonnes ont des noms différents, utilise `left_on` et `right_on`."
        elif "docker" in msg_lower:
            assistant_response = "Pour conserver les données de tes conteneurs, utilise les volumes Docker : `docker run -v mon_volume:/chemin/dans/conteneur mon_image`."
        elif "upskill" in msg_lower:
            assistant_response = "Le projet Upskill AI est conçu pour analyser tes prompts, extraire tes besoins de formation, et générer automatiquement des cours, des quiz et des podcasts pour t'aider."
        else:
            assistant_response = f"Je suis en mode démo locale hors-ligne. Tu as écrit : '{user_message}'. Pour tester les fonctionnalités IA, ajoute une clé GEMINI_API_KEY dans le fichier .env !"

    # 3. Enregistrer la réponse de l'assistant dans l'historique
    storage.save_chat_message(user_id, "assistant", assistant_response)
    
    # 4. Lancer l'extraction des lacunes en arrière-plan (asynchrone)
    background_tasks.add_task(run_background_extraction, user_id, user_message)
    
    return {"response": assistant_response}

@app.get("/api/chat/history")
def get_chat_history(user_id: str):
    return {"history": storage.get_chat_history(user_id)}

@app.get("/api/dashboard/learner")
def get_learner_dashboard(user_id: str):
    courses = storage.get_user_courses(user_id)
    gaps = storage.get_unprocessed_gaps(user_id)
    # Extraire uniquement les infos légères pour la liste des lacunes en attente
    pending_topics = [{"topic": g["topic"], "timestamp": g["timestamp"]} for g in gaps]
    
    return {
        "courses": courses,
        "pending_topics": pending_topics
    }

@app.get("/api/dashboard/manager")
def get_manager_dashboard():
    all_gaps = storage.get_all_gaps_global()
    
    # Agrégation des statistiques par sujet
    stats = {}
    for gap in all_gaps:
        topic = gap["topic"]
        if topic not in stats:
            stats[topic] = {"count": 0, "latest": gap["timestamp"], "descriptions": []}
        stats[topic]["count"] += 1
        stats[topic]["descriptions"].append(gap["gap_description"])
        if gap["timestamp"] > stats[topic]["latest"]:
            stats[topic]["latest"] = gap["timestamp"]
            
    formatted_stats = []
    for topic, info in stats.items():
        # Obtenir un résumé unique des descriptions
        unique_desc = list(set(info["descriptions"]))[:3]
        formatted_stats.append({
            "topic": topic,
            "count": info["count"],
            "latest": info["latest"],
            "summary": "; ".join(unique_desc)
        })
        
    return {
        "global_stats": formatted_stats,
        "total_analyzed_prompts": len(all_gaps)
    }

@app.post("/api/demo/trigger-analysis")
def trigger_analysis(request: TriggerRequest):
    user_id = request.user_id
    
    # 1. Récupérer toutes les lacunes non traitées de l'utilisateur
    unprocessed_gaps = storage.get_unprocessed_gaps(user_id)
    if not unprocessed_gaps:
        return {"status": "no_new_gaps", "generated_courses": []}
        
    # 2. Lancer l'algorithme de clustering et de pondération temporelle
    learning_needs = find_learning_needs(unprocessed_gaps)
    generated_courses = []
    
    # 3. Pour chaque besoin identifié, générer les ressources pédagogiques
    for need in learning_needs:
        topic = need["topic"]
        desc = need["description"]
        gap_ids = need["gap_ids"]
        
        # Génération du cours, quiz et podcast (LangGraph / Mock)
        logger.info(f"Génération de ressources pour le sujet : {topic}")
        assets = generate_learning_assets(topic, desc)
        
        # Sauvegarder le cours
        course_doc = storage.save_course(
            user_id=user_id,
            topic=topic,
            course_content=assets["course_content"],
            quiz=assets["quiz"],
            podcast_script=assets["podcast_script"]
        )
        generated_courses.append(course_doc)
        
        # Marquer les lacunes d'origine comme traitées/archivées
        storage.mark_gaps_as_processed(gap_ids)
        
    return {
        "status": "completed",
        "generated_courses": generated_courses
    }

@app.post("/api/demo/load")
def load_demo_scenario(request: LoadDemoRequest):
    user_id = request.user_id
    scenario = request.scenario
    
    # Simuler des prompts utilisateur correspondant au scénario
    demo_prompts = []
    if scenario == "pandas":
        demo_prompts = [
            "Comment faire une jointure entre deux tables en pandas ?",
            "pandas merge vs join c'est quoi la différence ?",
            "j'ai un dataframe et je veux ajouter une colonne d'une autre table, merge est le mieux ?",
            "comment spécifier les colonnes de jointure dans pd.merge quand elles n'ont pas le même nom ?",
            "quand je fais un merge pandas, ça supprime mes lignes qui n'ont pas de correspondance, pourquoi ?"
        ]
    elif scenario == "docker":
        demo_prompts = [
            "comment sauvegarder des données de ma DB docker ?",
            "c'est quoi un volume docker et comment le déclarer ?",
            "différence entre volume docker et bind mount ?",
            "comment monter un répertoire de mon PC dans mon conteneur docker ?",
            "quand je recrée mon conteneur postgres, je perds toutes mes tables, à l'aide !"
        ]
    elif scenario == "upskill":
        demo_prompts = [
            "Quel est le concept de l'application Upskill AI ?",
            "Comment l'agent IA fait-il pour extraire les lacunes de formation dans mes prompts ?",
            "Comment marche la pondération temporelle et le clustering DBSCAN ?",
            "Quelles ressources de formation Upskill AI génère-t-il ?",
            "Comment le podcast à deux voix NotebookLM est-il créé à partir de mon profil ?"
        ]
    else:
        raise HTTPException(status_code=400, detail="Scénario inconnu")
        
    # Injecter les prompts dans l'historique et forcer l'extraction immédiate des lacunes
    inserted_gaps = []
    for prompt in demo_prompts:
        # Enregistrer le message de chat
        storage.save_chat_message(user_id, "user", prompt)
        # Extraire la lacune
        gaps = extractor.extract_gaps(prompt)
        for gap in gaps:
            gap_doc = storage.save_gap(user_id, gap)
            inserted_gaps.append(gap_doc)
            
    return {
        "status": "scenario_loaded",
        "prompts_loaded_count": len(demo_prompts),
        "gaps_extracted_count": len(inserted_gaps)
    }

@app.post("/api/demo/reset")
def reset_demo():
    storage.reset_all_data()
    return {"status": "database_reset"}

# --- FONCTION D'EXTRACTION EN ARRIÈRE-PLAN ---
def run_background_extraction(user_id: str, prompt: str):
    logger.info(f"Extraction des lacunes en arrière-plan pour {user_id}...")
    try:
        gaps = extractor.extract_gaps(prompt)
        for gap in gaps:
            storage.save_gap(user_id, gap)
            logger.info(f"Lacune enregistrée pour {user_id} : {gap['topic']}")
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction en arrière-plan : {e}")
