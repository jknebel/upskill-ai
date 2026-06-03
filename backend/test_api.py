import pytest
from fastapi.testclient import TestClient
from backend.main import app, storage

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # S'assurer que le stockage est propre avant chaque test
    storage.reset_all_data()
    yield
    storage.reset_all_data()

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

def test_chat_and_history():
    user_id = "test_user_999"
    message = "Comment utiliser pandas merge ?"
    
    # Envoyer un message de chat
    response = client.post("/api/chat", json={"user_id": user_id, "message": message})
    assert response.status_code == 200
    assert "response" in response.json()
    
    # Vérifier que l'historique a été mis à jour
    history_response = client.get(f"/api/chat/history?user_id={user_id}")
    assert history_response.status_code == 200
    history = history_response.json()["history"]
    assert len(history) == 2  # Le message utilisateur + la réponse de l'assistant

def test_demo_scenario_and_analysis():
    user_id = "test_user_888"
    
    # 1. Charger le scénario Pandas
    load_response = client.post("/api/demo/load", json={"user_id": user_id, "scenario": "pandas"})
    assert load_response.status_code == 200
    assert load_response.json()["status"] == "scenario_loaded"
    
    # Vérifier qu'il y a des lacunes en attente dans le dashboard
    dashboard_before = client.get(f"/api/dashboard/learner?user_id={user_id}")
    assert dashboard_before.status_code == 200
    assert len(dashboard_before.json()["pending_topics"]) > 0
    
    # 2. Déclencher l'analyse (Clustering DBSCAN)
    analysis_response = client.post("/api/demo/trigger-analysis", json={"user_id": user_id})
    assert analysis_response.status_code == 200
    assert analysis_response.json()["status"] == "completed"
    
    # Vérifier que le cours a bien été généré
    dashboard_after = client.get(f"/api/dashboard/learner?user_id={user_id}")
    assert dashboard_after.status_code == 200
    assert len(dashboard_after.json()["courses"]) > 0
    
    # Vérifier que le cours contient les sections attendues
    course = dashboard_after.json()["courses"][0]
    assert course["topic"] == "Pandas DataFrames"
    assert "quiz" in course
    assert len(course["quiz"]) > 0
    assert "podcast_script" in course
    assert len(course["podcast_script"]) > 0
