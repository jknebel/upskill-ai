# 🚀 Upskill AI — Agentic E-Learning Platform POC

> **Analyse passive des prompts, détection intelligente des lacunes et génération autonome de formations personnalisées (Quiz & Podcasts multi-voix type NotebookLM).**

---

## 💡 Le Concept

**Upskill AI** est une démonstration de faisabilité (POC) d'une plateforme d'apprentissage continue et proactive. Au lieu de demander aux employés de déclarer leurs besoins de formation, l'outil **analyse passivement leurs interactions quotidiennes avec un chatbot IA (style Gemini)** pour détecter leurs lacunes de manière anonyme et non intrusive.

```
[Utilisateur Prompte] ──► [Extraction Temps Réel des Lacunes] ──► [Base Vectorielle]
                                                                        │
[Dashboard Apprenant] ◄── [Cours + Quiz + Podcast Hôtes] ◄── [Job Cron (Clustering & Temps)]
```

### 🧠 Fonctionnalités Clés
1. **Chatbot Intelligent Local** : Un chatbot standard basé sur Gemini avec historique conversationnel.
2. **Extraction des Lacunes en Temps Réel** : Un agent analyse chaque prompt en arrière-plan pour détecter des manques de compétences précis et générer un embedding vectoriel du concept associé.
3. **Clustering & Dépréciation Temporelle (Job Cron)** :
   * Regroupement des lacunes par similarité sémantique (via **DBSCAN** sur embeddings).
   * **Calculateur de décroissance temporelle** : Les prompts récents pèsent plus lourd que les anciens (formule de demi-vie/décroissance exponentielle $e^{-\lambda t}$).
   * Déclenchement automatique d'un cours dès qu'une thématique accumule un poids critique (ex: *50 prompts sur Pandas en 1h* vs. *50 en 5 ans*).
4. **Génération de Contenu Multi-Agent (LangGraph & LangChain)** :
   * **Cours de lecture** : Synthèse pédagogique complète pour combler la lacune.
   * **Quiz Interactif** : Test de validation des connaissances à choix multiples.
   * **Podcast Audio Interactif** : Script de dialogue à **2 hôtes** (format conversationnel naturel type *NotebookLM*) lu par synthèse vocale (Web Speech API).
5. **Dashboard Manager** : Visualisation globale et anonyme des compétences manquantes pour identifier les besoins de formation collectifs.

---

## 🛠️ Stack Technique

*   **Frontend** : React.js (Vite), CSS Moderne (Premium Dark Mode, Glassmorphism).
*   **Backend** : Python 3.10+, FastAPI, LangChain, LangGraph.
*   **IA & Modèles** : Gemini (famille `gemini-1.5-flash` & `gemini-1.5-pro`), embeddings `text-embedding-004`.
*   **Base de Données / Stockage** :
    *   *Local (POC)* : Système de fichiers JSON pour une exécution locale immédiate hors-ligne.
    *   *Production* : Firebase (Firestore Vector Search + Auth).
*   **CI/CD** : GitHub Actions (Cloud Run & Firebase Hosting).

---

## 📂 Architecture des Dossiers

```bash
upskill-ai/
├── backend/
│   ├── agents/           # Logique d'agents LangChain / LangGraph
│   │   ├── extractor.py  # Agent d'extraction des lacunes
│   │   └── generator.py  # Graph de génération (Cours, Quiz, Podcast)
│   ├── utils/
│   │   ├── clustering.py # Clustering DBSCAN & Décroissance temporelle
│   │   └── storage.py    # Gestionnaire de base de données locale JSON
│   ├── config.py         # Fichier de configurations
│   ├── main.py           # API FastAPI
│   └── requirements.txt  # Dépendances Python
├── frontend/             # Application React (Vite)
├── .github/
│   └── workflows/        # Workflows GitHub Actions pour le CI/CD
└── README.md
```

---

## 🚀 Lancement en Local

### 1. Cloner le Projet
```bash
git clone https://github.com/votre-user/upskill-ai.git
cd upskill-ai
```

### 2. Configuration du Backend
1. Naviguez dans le dossier `backend` :
   ```bash
   cd backend
   ```
2. Créez un environnement virtuel et activez-le :
   ```bash
   python -m venv venv
   # Sur Windows :
   .\venv\Scripts\activate
   # Sur macOS/Linux :
   source venv/bin/activate
   ```
3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
4. Créez un fichier `.env` dans le dossier `backend/` :
   ```env
   GEMINI_API_KEY=votre_cle_api_gemini
   GEMINI_MODEL_NAME=gemini-1.5-flash
   CLUSTERING_THRESHOLD=3.0
   DECAY_RATE_LAMBDA=0.05
   ```
5. Lancez l'API FastAPI :
   ```bash
   uvicorn main:app --reload
   ```
   L'API sera disponible sur `http://localhost:8000`.

### 3. Configuration du Frontend
1. Naviguez dans le dossier `frontend` :
   ```bash
   cd ../frontend
   ```
2. Installez les dépendances npm :
   ```bash
   npm install
   ```
3. Lancez le serveur de développement local :
   ```bash
   npm run dev
   ```
   L'application sera accessible sur `http://localhost:5173`.

---

## 🎯 Démo Récursive Intégrée

L'application inclut un **Mode Démo** accessible sur le Dashboard.
1. Cliquez sur **"Charger le compte démo"** pour simuler un historique de prompts.
2. Les prompts préchargés portent sur le projet **Upskill AI** lui-même (explication de l'architecture, etc.).
3. Cliquez sur **"Lancer l'analyse batch"**.
4. Le système va détecter un besoin de formation sur le sujet "Upskill AI" et générer instantanément :
   * Un cours sur le projet.
   * Un quiz pour valider que vous avez compris comment fonctionne l'outil.
   * Un podcast à 2 voix où deux présentateurs IA débattent du projet !

---

## 🛡️ Anonymat et Sécurité

Pour concilier **recommandations personnalisées** et **protection de la vie privée** :
* Les prompts et les lacunes extraites sont rattachés à un identifiant anonyme généré par Firebase Auth.
* Aucune donnée nominative (email, nom) n'est transmise au module d'analyse ou au stockage des lacunes.
* Le Dashboard Manager n'affiche que des agrégats thématiques de groupe (ex: thèmes récurrents du service "R&D"), garantissant qu'un manager ne peut pas cibler l'activité d'un individu en particulier.
