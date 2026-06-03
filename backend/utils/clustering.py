import numpy as np
from datetime import datetime, timezone
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
from typing import List, Dict, Any, Tuple
import logging
from backend.config import DECAY_RATE_LAMBDA, CLUSTERING_THRESHOLD

logger = logging.getLogger(__name__)

def calculate_time_weight(gap_timestamp: str) -> float:
    """
    Calcule le poids d'un gap en appliquant une fonction de décroissance temporelle exponentielle :
    poids = e^(-lambda * age_en_jours)
    """
    try:
        # Convertir le timestamp ISO en datetime
        dt = datetime.fromisoformat(gap_timestamp.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age_seconds = (now - dt).total_seconds()
        age_days = max(0.0, age_seconds / (24 * 3600))
        
        # Décroissance exponentielle
        weight = np.exp(-DECAY_RATE_LAMBDA * age_days)
        return float(weight)
    except Exception as e:
        logger.error(f"Erreur lors du calcul du poids temporel : {e}")
        return 1.0

def find_learning_needs(gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyse l'historique des lacunes d'un utilisateur, applique DBSCAN pour regrouper par similarité
    vectorielle, pondère par récence, et identifie les sujets qui nécessitent une formation.
    
    Retourne la liste des besoins de formation identifiés.
    """
    if not gaps:
        return []
        
    # Filtrer les lacunes valides ayant un embedding
    valid_gaps = [g for g in gaps if "embedding" in g and g["embedding"]]
    if len(valid_gaps) < 2:
        # Si trop peu de lacunes, pas besoin de clusteriser.
        # On vérifie juste si une seule lacune répétée ou très récente dépasse le seuil individuellement.
        for g in valid_gaps:
            weight = calculate_time_weight(g.get("timestamp", datetime.now(timezone.utc).isoformat()))
            if weight >= CLUSTERING_THRESHOLD:
                return [{
                    "topic": g["topic"],
                    "description": g["gap_description"],
                    "weight": weight,
                    "gap_ids": [g.get("id")]
                }]
        return []
        
    # Extraire les embeddings et calculer les poids
    embeddings = np.array([g["embedding"] for g in valid_gaps])
    weights = np.array([calculate_time_weight(g.get("timestamp", datetime.now(timezone.utc).isoformat())) for g in valid_gaps])
    
    # Calculer la matrice des distances cosinus
    # DBSCAN utilise cette matrice pour le clustering
    dist_matrix = cosine_distances(embeddings)
    
    # DBSCAN avec distance cosinus.
    # eps est le seuil de distance cosinus (0.3 correspond à 70% de similarité cosinus)
    # min_samples = 2 pour pouvoir créer un groupe d'apprentissage à partir de 2 questions proches
    db = DBSCAN(eps=0.3, min_samples=2, metric="precomputed")
    labels = db.fit_predict(dist_matrix)
    
    clusters = {}
    
    for idx, label in enumerate(labels):
        if label == -1:
            # Bruit identifié par DBSCAN (lacune isolée)
            # On vérifie quand même si à elle seule elle dépasse le seuil
            if weights[idx] >= CLUSTERING_THRESHOLD:
                cluster_id = f"single_{idx}"
                clusters[cluster_id] = {
                    "topic": valid_gaps[idx]["topic"],
                    "descriptions": [valid_gaps[idx]["gap_description"]],
                    "weight": weights[idx],
                    "gaps": [valid_gaps[idx]]
                }
            continue
            
        if label not in clusters:
            clusters[label] = {
                "topic": valid_gaps[idx]["topic"], # Prendra le premier comme référence
                "descriptions": [],
                "weight": 0.0,
                "gaps": []
            }
            
        clusters[label]["descriptions"].append(valid_gaps[idx]["gap_description"])
        clusters[label]["weight"] += weights[idx]
        clusters[label]["gaps"].append(valid_gaps[idx])
        
    # Filtrer les clusters qui dépassent le seuil requis pour déclencher une formation
    learning_needs = []
    for c_id, c_data in clusters.items():
        if c_data["weight"] >= CLUSTERING_THRESHOLD:
            # Synthétiser les descriptions du cluster
            unique_desc = list(set(c_data["descriptions"]))
            learning_needs.append({
                "topic": c_data["topic"],
                "description": "; ".join(unique_desc),
                "weight": float(c_data["weight"]),
                "gap_ids": [g.get("id") for g in c_data["gaps"]]
            })
            
    return learning_needs
