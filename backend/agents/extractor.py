import json
import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.config import GEMINI_API_KEY, MODEL_EXTRACTOR, MODEL_EMBEDDING, USE_VERTEX_AI
from backend.utils.llm import get_generative_model

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Schéma Pydantic pour la réponse structurée
class KnowledgeGap(BaseModel):
    topic: str = Field(description="Le sujet général de la lacune identifiée, par exemple 'Pandas DataFrames', 'Docker Volumes', 'SQL Joins'.")
    gap_description: str = Field(description="Description précise de ce que l'utilisateur ne sait pas ou tente de comprendre.")
    confidence: float = Field(description="Score de confiance entre 0.0 et 1.0 sur le fait qu'il s'agit d'une réelle lacune.")
    is_learning_gap: bool = Field(description="True si le prompt montre un besoin de formation/compréhension technique, False s'il s'agit d'une question générale, d'une tâche de routine ou d'un sujet informel (bruit).")

class ExtractorResponse(BaseModel):
    detected_gaps: List[KnowledgeGap] = Field(description="Liste des lacunes détectées dans le prompt.")

def inline_refs(schema: dict) -> dict:
    """
    Résout et remplace récursivement les références '$ref' par les définitions réelles dans '$defs'.
    Indispensable car les API Gemini et Vertex AI n'acceptent pas les schémas avec des définitions séparées ($defs).
    """
    if not isinstance(schema, dict):
        return schema
        
    defs = schema.get("$defs", schema.get("definitions", {}))
    
    def resolve(node):
        if isinstance(node, dict):
            if "$ref" in node:
                ref_path = node["$ref"]
                def_name = ref_path.split("/")[-1]
                if def_name in defs:
                    return resolve(defs[def_name])
            return {k: resolve(v) for k, v in node.items() if k not in ("$defs", "definitions")}
        elif isinstance(node, list):
            return [resolve(item) for item in node]
        return node
        
    return resolve(schema)

def clean_schema(schema: dict) -> dict:
    """
    Supprime récursivement les attributs incompatibles comme 'default' ou 'title'
    qui bloquent la validation du schéma sur Gemini.
    """
    if not isinstance(schema, dict):
        return schema
    cleaned = {}
    for k, v in schema.items():
        if k in ("default", "title"):
            continue
        if isinstance(v, dict):
            cleaned[k] = clean_schema(v)
        elif isinstance(v, list):
            cleaned[k] = [clean_schema(item) if isinstance(item, dict) else item for item in v]
        else:
            cleaned[k] = v
    return cleaned

class PromptExtractor:
    def __init__(self):
        pass
        
    def extract_gaps(self, prompt: str) -> List[dict]:
        """
        Analyse un prompt utilisateur pour identifier les lacunes en connaissances/compétences.
        """
        system_instruction = (
            "Tu es un agent d'analyse pédagogique. Ton rôle est d'analyser le prompt d'un utilisateur "
            "pour extraire ce qu'il NE SAIT PAS ou ce qu'il a du mal à maîtriser (ses lacunes cognitives/techniques). "
            "Sois précis. Si le prompt est une question banale sur la météo ou des vacances, indique que ce n'est pas "
            "une lacune d'apprentissage ('is_learning_gap': false). "
            "S'il demande comment faire une jointure complexe en Pandas parce qu'il s'emmêle les pinceaux, c'est une "
            "lacune ('is_learning_gap': true)."
        )
        
        model = get_generative_model(model_name=MODEL_EXTRACTOR, system_instruction=system_instruction)
        if not model:
            return self._simulate_extraction(prompt)
            
        try:
            # 1. Générer le schéma JSON brut de Pydantic
            raw_schema = ExtractorResponse.model_json_schema()
            
            # 2. Aplatir le schéma en résolvant les définitions imbriquées ($defs)
            flat_schema = inline_refs(raw_schema)
            
            # 3. Nettoyer les attributs interdits (title, default)
            cleaned_schema = clean_schema(flat_schema)

            config = {
                "response_mime_type": "application/json",
                "response_schema": cleaned_schema,
                "temperature": 0.1
            }
            
            if USE_VERTEX_AI:
                from vertexai.generative_models import GenerationConfig
                generation_config = GenerationConfig(**config)
                response = model.generate_content(
                    f"Analyse le prompt utilisateur suivant :\n\n\"\"\"\n{prompt}\n\"\"\"",
                    generation_config=generation_config
                )
            else:
                import google.generativeai as genai
                generation_config = genai.GenerationConfig(**config)
                response = model.generate_content(
                    f"Analyse le prompt utilisateur suivant :\n\n\"\"\"\n{prompt}\n\"\"\"",
                    generation_config=generation_config
                )
            
            data = json.loads(response.text)
            gaps = [
                gap for gap in data.get("detected_gaps", [])
                if gap.get("is_learning_gap") and gap.get("confidence", 0) > 0.5
            ]
            
            for gap in gaps:
                gap["embedding"] = self.generate_embedding(gap["topic"])
                
            return gaps
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction par le LLM : {e}")
            return self._simulate_extraction(prompt)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Génère un embedding vectoriel pour le texte spécifié.
        """
        if USE_VERTEX_AI:
            try:
                from vertexai.language_models import TextEmbeddingModel
                model = TextEmbeddingModel.from_pretrained("text-embedding-004")
                embeddings = model.get_embeddings([text])
                return [float(x) for x in embeddings[0].values]
            except Exception as e:
                logger.error(f"Erreur d'embedding Vertex AI : {e}")
                
        if GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                
                result = genai.embed_content(
                    model=f"models/{MODEL_EMBEDDING}",
                    content=text,
                    task_type="clustering"
                )
                return result['embedding']
            except Exception as e:
                logger.error(f"Erreur d'embedding Google AI Studio (gemini-embedding-2) : {e}")
                # Fallback de secours sur le modèle gemini-embedding-001 si gemini-embedding-2 échoue
                try:
                    result = genai.embed_content(
                        model="models/gemini-embedding-001",
                        content=text,
                        task_type="clustering"
                    )
                    return result['embedding']
                except Exception as e2:
                    logger.error(f"Erreur d'embedding Google AI Studio (gemini-embedding-001) : {e2}")
                
        import random
        random.seed(text)
        return [random.uniform(-1, 1) for _ in range(16)]

    def _simulate_extraction(self, prompt: str) -> List[dict]:
        """
        Simulation d'extraction pour tests sans clé API.
        """
        prompt_lower = prompt.lower()
        gaps = []
        
        if "pandas" in prompt_lower or "dataframe" in prompt_lower or "merge" in prompt_lower or "join" in prompt_lower:
            gaps.append({
                "topic": "Pandas DataFrames",
                "gap_description": "Difficulté à manipuler, fusionner (merge/join) et nettoyer des DataFrames avec Pandas.",
                "confidence": 0.95,
                "is_learning_gap": True
            })
        elif "docker" in prompt_lower or "volume" in prompt_lower or "container" in prompt_lower:
            gaps.append({
                "topic": "Docker Containers",
                "gap_description": "Manque de maîtrise de la gestion des volumes et du réseau entre conteneurs Docker.",
                "confidence": 0.90,
                "is_learning_gap": True
            })
        elif "upskill" in prompt_lower or "poc" in prompt_lower or "agent" in prompt_lower:
            gaps.append({
                "topic": "Upskill AI & Agentic",
                "gap_description": "Compréhension de l'architecture d'analyse passive des prompts et de génération de podcasts pédagogiques.",
                "confidence": 0.98,
                "is_learning_gap": True
            })
            
        for gap in gaps:
            gap["embedding"] = self.generate_embedding(gap["topic"])
            
        return gaps
