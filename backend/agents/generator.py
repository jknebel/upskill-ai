import json
import logging
import os
from typing import TypedDict, List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from backend.config import (
    GEMINI_API_KEY,
    MODEL_TEACHER,
    MODEL_DIRECTOR,
    MODEL_PODCAST,
    THINKING_TEACHER,
    THINKING_DIRECTOR,
    THINKING_PODCAST,
)

from backend.utils.llm import get_langchain_llm

logger = logging.getLogger(__name__)

# Définition de l'état du Graph LangGraph (étendu pour le pattern 2 Profs + 1 Directeur)
class AgentState(TypedDict):
    topic: str
    description: str
    # Sorties du Prof A (pédagogie structurée)
    course_teacher_a: str
    quiz_teacher_a: List[Dict[str, Any]]
    # Sorties du Prof B (exemples pratiques)
    course_teacher_b: str
    quiz_teacher_b: List[Dict[str, Any]]
    # Sorties finales du Directeur
    course_content: str
    quiz: List[Dict[str, Any]]
    podcast_script: List[Dict[str, str]]


# ============================================================================
# NOEUD 1A : Prof A — Pédagogie structurée et théorique
# ============================================================================
def generate_course_teacher_a(state: AgentState) -> Dict[str, Any]:
    topic = state["topic"]
    description = state["description"]

    llm = get_langchain_llm(
        model_name=MODEL_TEACHER,
        thinking_budget=THINKING_TEACHER,
        temperature=0.7
    )
    if not llm:
        logger.info("Simulation Prof A (pas de LLM).")
        return {
            "course_teacher_a": get_mock_course(topic),
            "quiz_teacher_a": get_mock_quiz(topic)
        }

    # Prompt orienté pédagogie structurée
    course_prompt = ChatPromptTemplate.from_template(
        "Tu es un professeur universitaire expert en pédagogie structurée. "
        "Crée un cours condensé, très structuré et académique en Markdown "
        "sur le sujet suivant : '{topic}'.\n"
        "Le cours doit s'adresser à quelqu'un qui a la lacune suivante : '{description}'.\n"
        "Organise le cours de façon très hiérarchique avec :\n"
        "- Des définitions précises et formelles\n"
        "- Des concepts théoriques bien expliqués\n"
        "- Des règles et bonnes pratiques\n"
        "- Un exemple de code commenté si pertinent\n"
        "Divise le cours en 3 sections principales. "
        "Le cours doit pouvoir se lire en 5 minutes environ."
    )

    chain = course_prompt | llm
    course_response = chain.invoke({"topic": topic, "description": description})
    course_content = course_response.content

    # Générer le quiz du Prof A
    quiz = _generate_quiz_from_course(llm, course_content, topic)

    return {
        "course_teacher_a": course_content,
        "quiz_teacher_a": quiz
    }


# ============================================================================
# NOEUD 1B : Prof B — Exemples pratiques et cas concrets
# ============================================================================
def generate_course_teacher_b(state: AgentState) -> Dict[str, Any]:
    topic = state["topic"]
    description = state["description"]

    llm = get_langchain_llm(
        model_name=MODEL_TEACHER,
        thinking_budget=THINKING_TEACHER,
        temperature=0.8  # Légèrement plus créatif
    )
    if not llm:
        logger.info("Simulation Prof B (pas de LLM).")
        return {
            "course_teacher_b": get_mock_course(topic),
            "quiz_teacher_b": get_mock_quiz(topic)
        }

    # Prompt orienté exemples pratiques
    course_prompt = ChatPromptTemplate.from_template(
        "Tu es un formateur technique pragmatique spécialisé dans l'apprentissage par l'exemple. "
        "Crée un cours condensé, très pratique et orienté cas concrets en Markdown "
        "sur le sujet suivant : '{topic}'.\n"
        "Le cours doit s'adresser à quelqu'un qui a la lacune suivante : '{description}'.\n"
        "Privilégie :\n"
        "- Des exemples de code réels et fonctionnels\n"
        "- Des cas d'usage courants et des erreurs fréquentes\n"
        "- Des analogies simples pour expliquer les concepts\n"
        "- Des astuces et raccourcis pratiques\n"
        "Divise le cours en 3 sections principales. "
        "Le cours doit pouvoir se lire en 5 minutes environ."
    )

    chain = course_prompt | llm
    course_response = chain.invoke({"topic": topic, "description": description})
    course_content = course_response.content

    # Générer le quiz du Prof B
    quiz = _generate_quiz_from_course(llm, course_content, topic)

    return {
        "course_teacher_b": course_content,
        "quiz_teacher_b": quiz
    }


# ============================================================================
# Utilitaire partagé : Génération de quiz à partir d'un cours
# ============================================================================
def _generate_quiz_from_course(llm, course_content: str, topic: str) -> List[Dict[str, Any]]:
    prompt = ChatPromptTemplate.from_template(
        "En te basant sur le cours suivant :\n\n{course_content}\n\n"
        "Génère un quiz de 3 questions à choix multiples (QCM) au format JSON.\n"
        "Le JSON retourné doit être valide et respecter strictement la structure suivante :\n"
        "[\n"
        "  {{\n"
        "    \"question\": \"Texte de la question\",\n"
        "    \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"],\n"
        "    \"answer\": \"L'option correcte exacte\"\n"
        "  }}\n"
        "]\n"
        "Ne retourne RIEN d'autre que le JSON brut (pas de balises ```json ou markdown)."
    )

    chain = prompt | llm
    response = chain.invoke({"course_content": course_content})
    try:
        text = response.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        logger.error(f"Erreur de parsing du quiz JSON : {e}. Utilisation du fallback.")
        return get_mock_quiz(topic)


# ============================================================================
# NOEUD 2 : Directeur — Fusion et vérification anti-hallucination
# ============================================================================
def director_merge_node(state: AgentState) -> Dict[str, Any]:
    course_a = state["course_teacher_a"]
    quiz_a = state["quiz_teacher_a"]
    course_b = state["course_teacher_b"]
    quiz_b = state["quiz_teacher_b"]
    topic = state["topic"]

    llm = get_langchain_llm(
        model_name=MODEL_DIRECTOR,
        thinking_budget=THINKING_DIRECTOR,
        temperature=0.3  # Faible température pour la vérification factuelle
    )
    if not llm:
        logger.info("Simulation Directeur — utilisation du cours Prof A par défaut.")
        return {
            "course_content": course_a,
            "quiz": quiz_a
        }

    # Prompt du Directeur-Vérificateur
    prompt = ChatPromptTemplate.from_template(
        "Tu es un directeur pédagogique expert et rigoureux. Tu reçois deux versions d'un cours "
        "et deux quiz créés par deux professeurs différents sur le sujet : '{topic}'.\n\n"
        "--- COURS DU PROFESSEUR A (structuré et théorique) ---\n{course_a}\n\n"
        "--- COURS DU PROFESSEUR B (pratique et exemples concrets) ---\n{course_b}\n\n"
        "--- QUIZ DU PROFESSEUR A ---\n{quiz_a_json}\n\n"
        "--- QUIZ DU PROFESSEUR B ---\n{quiz_b_json}\n\n"
        "Ta mission est de produire UN SEUL cours final optimal en Markdown :\n"
        "1. Compare les deux cours et identifie les contradictions ou erreurs factuelles\n"
        "2. Fusionne les meilleures parties : la structure théorique du Prof A avec les exemples pratiques du Prof B\n"
        "3. Si un fait ou une information n'apparaît que dans un seul cours, vérifie-le soigneusement et retire-le si douteux\n"
        "4. Le cours final doit être structuré en 3 sections principales, clair et vérifiable\n"
        "5. Le cours doit pouvoir se lire en 5 minutes environ\n\n"
        "Retourne UNIQUEMENT le cours final en Markdown, sans commentaire sur ta démarche."
    )

    chain = prompt | llm
    try:
        response = chain.invoke({
            "topic": topic,
            "course_a": course_a,
            "course_b": course_b,
            "quiz_a_json": json.dumps(quiz_a, ensure_ascii=False, indent=2),
            "quiz_b_json": json.dumps(quiz_b, ensure_ascii=False, indent=2),
        })
        merged_course = response.content
    except Exception as e:
        logger.error(f"Erreur Directeur (cours) : {e}. Fallback sur le cours Prof A.")
        merged_course = course_a

    # Générer le quiz final à partir du cours fusionné
    quiz_llm = get_langchain_llm(
        model_name=MODEL_DIRECTOR,
        thinking_budget=THINKING_DIRECTOR,
        temperature=0.2
    )
    if quiz_llm:
        quiz_prompt = ChatPromptTemplate.from_template(
            "Tu es un directeur pédagogique. Voici le cours final vérifié :\n\n{course_content}\n\n"
            "Voici les quiz proposés par deux professeurs :\n"
            "--- Quiz Prof A ---\n{quiz_a_json}\n"
            "--- Quiz Prof B ---\n{quiz_b_json}\n\n"
            "Crée un quiz final de 3 questions QCM en sélectionnant et améliorant les meilleures questions. "
            "Assure-toi que chaque réponse est factuelle et cohérente avec le cours final.\n"
            "Retourne UNIQUEMENT le JSON brut au format :\n"
            "[{{\"question\": \"...\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"answer\": \"...\"}}]\n"
            "Pas de balises ```json ou markdown."
        )
        quiz_chain = quiz_prompt | quiz_llm
        try:
            quiz_response = quiz_chain.invoke({
                "course_content": merged_course,
                "quiz_a_json": json.dumps(quiz_a, ensure_ascii=False, indent=2),
                "quiz_b_json": json.dumps(quiz_b, ensure_ascii=False, indent=2),
            })
            text = quiz_response.content.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            merged_quiz = json.loads(text.strip())
        except Exception as e:
            logger.error(f"Erreur Directeur (quiz) : {e}. Utilisation du quiz Prof A.")
            merged_quiz = quiz_a
    else:
        merged_quiz = quiz_a

    return {
        "course_content": merged_course,
        "quiz": merged_quiz
    }


# ============================================================================
# NOEUD 3 : Génération du Podcast (à partir du cours vérifié par le Directeur)
# ============================================================================
def generate_podcast_node(state: AgentState) -> Dict[str, Any]:
    topic = state["topic"]
    course_content = state["course_content"]

    llm = get_langchain_llm(
        model_name=MODEL_PODCAST,
        thinking_budget=THINKING_PODCAST,
        temperature=0.7
    )
    if not llm:
        logger.info("Simulation de génération de podcast.")
        return {"podcast_script": get_mock_podcast(topic)}

    prompt = ChatPromptTemplate.from_template(
        "Tu es un scénariste de podcast de vulgarisation scientifique et technique.\n"
        "En te basant sur le cours suivant : \n\n{course_content}\n\n"
        "Rédige un script de podcast à deux voix (Hôte A: l'expert pédagogue, Hôte B: le co-animateur curieux et candide).\n"
        "Le dialogue doit être très dynamique, plein d'enthousiasme, avec des questions/réponses rapides.\n"
        "Retourne le script sous forme d'un tableau JSON d'objets structurés de la façon suivante :\n"
        "[\n"
        "  {{\n"
        "    \"speaker\": \"Hôte A\",\n"
        "    \"text\": \"Bonjour et bienvenue dans notre micro-capsule d'apprentissage ! Aujourd'hui on parle de...\"\n"
        "  }},\n"
        "  {{\n"
        "    \"speaker\": \"Hôte B\",\n"
        "    \"text\": \"Salut ! Oui, et c'est un sujet super intéressant parce que beaucoup de gens font l'erreur...\"\n"
        "  }}\n"
        "]\n"
        "Génère environ 6 à 10 répliques au total pour ce court podcast de démonstration.\n"
        "Ne retourne RIEN d'autre que le JSON brut (pas de balises ```json ou markdown)."
    )

    chain = prompt | llm
    response = chain.invoke({"course_content": course_content})
    try:
        text = response.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        script_data = json.loads(text.strip())
        return {"podcast_script": script_data}
    except Exception as e:
        logger.error(f"Erreur de parsing du script de podcast : {e}. Utilisation du fallback.")
        return {"podcast_script": get_mock_podcast(topic)}


# ============================================================================
# CONSTRUCTION DU GRAPHE LANGGRAPH — Pattern 2 Profs + 1 Directeur
# ============================================================================
def build_generation_graph():
    """
    Graphe LangGraph :
    
        START ──┬──> Prof A (gemini-2.5-flash + thinking) ──┐
                │                                            ├──> Directeur (gemini-2.5-pro + thinking) ──> Podcast (gemini-2.5-pro) ──> END
                └──> Prof B (gemini-2.5-flash + thinking) ──┘
    
    Prof A et Prof B s'exécutent en parallèle.
    Le Directeur fusionne et vérifie les deux cours avant de passer au podcast.
    """
    workflow = StateGraph(AgentState)

    # Ajouter les nœuds
    workflow.add_node("teacher_a", generate_course_teacher_a)
    workflow.add_node("teacher_b", generate_course_teacher_b)
    workflow.add_node("director", director_merge_node)
    workflow.add_node("podcast", generate_podcast_node)

    # Relier les nœuds : START → [Prof A || Prof B] → Directeur → Podcast → END
    workflow.add_edge(START, "teacher_a")
    workflow.add_edge(START, "teacher_b")
    workflow.add_edge("teacher_a", "director")
    workflow.add_edge("teacher_b", "director")
    workflow.add_edge("director", "podcast")
    workflow.add_edge("podcast", END)

    return workflow.compile()

# --- INSTANCE DU GRAPH COMPILÉ ---
generator_agent = build_generation_graph()

def generate_learning_assets(topic: str, description: str) -> Dict[str, Any]:
    """
    Fonction principale à appeler pour lancer la génération de cours, quiz et podcast.
    Utilise le pattern 2 Professeurs + 1 Directeur pour réduire les hallucinations.
    """
    initial_state = {
        "topic": topic,
        "description": description,
        "course_teacher_a": "",
        "quiz_teacher_a": [],
        "course_teacher_b": "",
        "quiz_teacher_b": [],
        "course_content": "",
        "quiz": [],
        "podcast_script": []
    }

    result = generator_agent.invoke(initial_state)
    return {
        "course_content": result["course_content"],
        "quiz": result["quiz"],
        "podcast_script": result["podcast_script"]
    }

# ============================================================================
# CONTENU SIMULÉ DE FALLBACK (POUR DÉMO INSTANTANÉE EN LOCAL)
# ============================================================================

def get_mock_course(topic: str) -> str:
    if "pandas" in topic.lower():
        return """# Fusionner des DataFrames avec Pandas 🐼

La fusion de données est l'une des tâches les plus fréquentes en Data Science. En Pandas, cela se fait principalement via la fonction `pd.merge()`.

## 1. Différence entre `merge()` et `join()`
* `pd.merge()` : Fusionne sur la base de colonnes communes (très flexible, similaire à un JOIN SQL).
* `DataFrame.join()` : Fusionne principalement sur la base des index des DataFrames.

## 2. Les différents types de jointures (How)
Comme en SQL, vous disposez de 4 modes principaux :
* **Inner Join** (Par défaut) : Ne garde que les clés présentes dans les deux DataFrames.
* **Left Join** : Garde toutes les lignes du DataFrame de gauche, et ajoute les correspondances de droite.
* **Right Join** : Garde toutes les lignes du DataFrame de droite.
* **Outer Join** : Garde toutes les lignes des deux DataFrames en insérant des `NaN` s'il n'y a pas de correspondance.

## 3. Exemple de code
```python
import pandas as pd

df1 = pd.DataFrame({'id': [1, 2], 'nom': ['Alice', 'Bob']})
df2 = pd.DataFrame({'id': [1, 3], 'score': [95, 80]})

# Jointure à gauche (Left Join)
resultat = pd.merge(df1, df2, on='id', how='left')
print(resultat)
```
"""
    elif "docker" in topic.lower():
        return """# Maîtriser les volumes Docker 🐳

Par défaut, les données créées à l'intérieur d'un conteneur Docker sont éphémères. Si le conteneur est supprimé, les données le sont aussi. Pour persister les données, Docker utilise les **Volumes**.

## 1. Qu'est-ce qu'un volume Docker ?
Un volume est un dossier géré par Docker sur la machine hôte. Il est totalement indépendant du cycle de vie des conteneurs.

## 2. Différence entre Volume et Bind Mount
* **Volume** : Géré par Docker. Stocké dans une zone dédiée (`/var/lib/docker/volumes/` sur Linux). Recommandé pour persister les données.
* **Bind Mount** : Relie un dossier spécifique de votre machine hôte (ex: `C:/projets/app`) à un dossier du conteneur. Parfait pour le développement à chaud.

## 3. Commandes essentielles
```bash
# Créer un volume
docker volume create mon_volume

# Monter le volume dans un conteneur
docker run -d -v mon_volume:/data alpine
```
"""
    # Default is Upskill AI (recursive demo)
    return """# Découverte du projet Upskill AI 🚀

Bienvenue dans le cours d'introduction à **Upskill AI**. Cet outil réinvente la formation professionnelle continue en y intégrant de l'IA agentique passive.

## 1. Le flux d'analyse
Upskill AI analyse silencieusement vos prompts de chat quotidiens. À chaque prompt, l'**Agent Extracteur** isole les concepts non maîtrisés (lacunes) et en génère un embedding vectoriel.

## 2. Détection temporelle (Clustering)
Un job d'analyse regroupe les lacunes similaires. Grâce à un algorithme de décroissance temporelle (dépréciation exponentielle), le système fait la différence entre un besoin ponctuel et une lacune persistante. Si vous posez 20 questions sur Docker en une matinée, le système détecte l'urgence et génère votre formation.

## 3. Les ressources générées
Une fois le besoin détecté, le système génère un cours écrit synthétique, un quiz interactif de 3 questions, et un podcast dialogue dynamique avec 2 voix IA (Hôte A et Hôte B) pour vous expliquer le concept !
"""

def get_mock_quiz(topic: str) -> List[Dict[str, Any]]:
    if "pandas" in topic.lower():
        return [
            {
                "question": "Quelle fonction Pandas est la plus flexible pour effectuer des jointures sur des colonnes ?",
                "options": ["df.join()", "pd.merge()", "pd.concat()", "df.combine()"],
                "answer": "pd.merge()"
            },
            {
                "question": "Quel type de jointure conserve toutes les lignes du DataFrame de gauche ?",
                "options": ["inner", "outer", "left", "right"],
                "answer": "left"
            }
        ]
    elif "docker" in topic.lower():
        return [
            {
                "question": "Où sont stockés les volumes gérés par Docker sous Linux ?",
                "options": ["/etc/docker/", "/var/lib/docker/volumes/", "/tmp/docker/", "/home/user/volumes/"],
                "answer": "/var/lib/docker/volumes/"
            },
            {
                "question": "Quelle option permet de monter un volume lors d'un docker run ?",
                "options": ["-p", "-d", "-v", "--link"],
                "answer": "-v"
            }
        ]
    return [
        {
            "question": "Comment s'appelle l'algorithme qui regroupe les lacunes sémantiquement proches dans Upskill AI ?",
            "options": ["K-Means", "DBSCAN", "Régression linéaire", "Random Forest"],
            "answer": "DBSCAN"
        },
        {
            "question": "Pourquoi applique-t-on une pondération temporelle aux lacunes ?",
            "options": ["Pour économiser de la mémoire", "Pour accorder plus de poids aux difficultés récentes", "Pour trier par ordre alphabétique", "Pour masquer l'identité des utilisateurs"],
            "answer": "Pour accorder plus de poids aux difficultés récentes"
        }
    ]

def get_mock_podcast(topic: str) -> List[Dict[str, str]]:
    if "pandas" in topic.lower():
        return [
            {"speaker": "Hôte A", "text": "Bonjour à tous ! Aujourd'hui, on s'attaque à un monument de l'analyse de données en Python : les jointures Pandas !"},
            {"speaker": "Hôte B", "text": "Salut ! Ah oui, Pandas ! J'avoue que je m'emmêle toujours les pinceaux entre merge et join. C'est quoi la vraie différence ?"},
            {"speaker": "Hôte A", "text": "C'est une excellente question. En gros, retiens que merge() est le plus puissant : il te permet de fusionner sur n'importe quelles colonnes communes, comme en SQL. Alors que join() est conçu pour fusionner en utilisant les index des tables."},
            {"speaker": "Hôte B", "text": "D'accord, donc merge pour les colonnes, join pour les index. Et pour les types de jointures ? Left, right, inner... ?"},
            {"speaker": "Hôte A", "text": "Exactement ! Par défaut, merge fait un 'inner join', ce qui veut dire qu'il ne garde que les éléments présents dans les deux DataFrames. Si tu veux tout garder d'un côté, tu utilises left ou right. Et si tu veux la totale, c'est outer !"},
            {"speaker": "Hôte B", "text": "Génial, tout s'éclaire ! Merci pour cette capsule rapide, je file tester ça sur mes DataFrames !"}
        ]
    elif "docker" in topic.lower():
        return [
            {"speaker": "Hôte A", "text": "Bienvenue dans notre capsule tech ! Aujourd'hui, on parle de persistance avec Docker, et plus particulièrement des volumes."},
            {"speaker": "Hôte B", "text": "Salut ! Oui, parce que j'ai perdu toutes mes données de base de données en arrêtant mon conteneur la semaine dernière... C'était la panique !"},
            {"speaker": "Hôte A", "text": "Aïe ! Classique. Par défaut, un conteneur est éphémère. Pour éviter cela, on monte un Volume. C'est un dossier géré par Docker sur ta machine qui survit à la destruction du conteneur."},
            {"speaker": "Hôte B", "text": "Et comment on fait ça en ligne de commande ?"},
            {"speaker": "Hôte A", "text": "Très simple : tu ajoutes l'option tiret v, suivi du nom de ton volume, deux points, et le dossier cible dans ton conteneur. Par exemple : `-v mon_volume:/data`."},
            {"speaker": "Hôte B", "text": "Super simple en fait ! Plus d'excuses pour perdre mes données. Merci !"}
        ]
    return [
        {"speaker": "Hôte A", "text": "Bonjour et bienvenue pour ce focus sur notre projet : Upskill AI !"},
        {"speaker": "Hôte B", "text": "Salut ! Je trouve l'idée géniale : un outil qui détecte ce que je ne sais pas faire rien qu'en lisant mes questions au chatbot ! C'est magique ou c'est de l'IA ?"},
        {"speaker": "Hôte A", "text": "C'est de l'IA et de l'analyse intelligente ! En arrière-plan, chaque question passe par un Agent Extracteur qui repère les lacunes techniques. Ensuite, on utilise le clustering DBSCAN sur les embeddings de ces lacunes."},
        {"speaker": "Hôte B", "text": "D'accord, mais si je pose une question bête sur mes vacances, ça va me générer un cours sur le camping ?"},
        {"speaker": "Hôte A", "text": "Non ! D'abord, l'agent élimine le bruit. Ensuite, l'algorithme applique une décroissance temporelle exponentielle. Les questions isolées ou anciennes perdent de leur poids, tandis que les difficultés répétées et récentes forment un groupe solide."},
        {"speaker": "Hôte B", "text": "Et dès que le groupe est assez important, paf, ça génère ce cours, ce quiz et ce super podcast qu'on est en train d'enregistrer !"},
        {"speaker": "Hôte A", "text": "Exactement ! Tu as tout compris. C'est l'essence même de l'apprentissage adaptatif de demain."}
    ]
