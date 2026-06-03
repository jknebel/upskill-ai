import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  BookOpen, 
  BarChart2, 
  Play, 
  Pause, 
  RotateCcw, 
  Send, 
  HelpCircle, 
  Sparkles, 
  TrendingUp, 
  Users, 
  Award, 
  Trash2, 
  Volume2, 
  AlertCircle,
  Brain,
  CheckCircle2
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USER_ID = 'demo_user_123'; // ID pseudonymisé pour le POC

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // chat, learner, manager
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState(false);
  
  // Learner Dashboard Data
  const [courses, setCourses] = useState([]);
  const [pendingTopics, setPendingTopics] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizScore, setQuizScore] = useState(null);
  
  // Manager Dashboard Data
  const [globalStats, setGlobalStats] = useState([]);
  const [totalAnalyzed, setTotalAnalyzed] = useState(0);
  
  // Podcast State
  const [isPlayingPodcast, setIsPlayingPodcast] = useState(false);
  const [currentLineIndex, setCurrentLineIndex] = useState(-1);
  const synthRef = useRef(window.speechSynthesis);
  const speechTimeoutRef = useRef(null);

  // Auto-scroll chat
  const chatEndRef = useRef(null);

  // Suggestions de démo du guide
  const demoScenarios = [
    {
      title: "🐼 Pandas (Code)",
      name: "pandas",
      prompts: [
        "Comment faire pour fusionner deux tables avec Pandas ? J'ai deux DataFrames.",
        "Quelle est la différence exacte entre merge et join dans la librairie Pandas en Python ?",
        "Dans pd.merge, mes colonnes clés n'ont pas les mêmes noms entre ma table de gauche et ma table de droite, comment je gère ça ?",
        "À chaque fois que je lance un merge sur mes dataframes, certaines lignes disparaissent de mon résultat. Pourquoi ?"
      ]
    },
    {
      title: "🐳 Docker (Volumes)",
      name: "docker",
      prompts: [
        "J'ai arrêté mon conteneur PostgreSQL et quand je l'ai relancé, toutes mes tables avaient disparu...",
        "Qu'est-ce qu'un volume Docker et comment on s'en sert pour garder des données ?",
        "C'est quoi la différence entre un Volume géré par Docker et un Bind Mount ?",
        "Comment monter le dossier /var/lib/postgresql/data sur un dossier de mon ordinateur ?"
      ]
    },
    {
      title: "🚀 Upskill AI (Projet)",
      name: "upskill",
      prompts: [
        "Comment fonctionne le projet Upskill AI et son flux d'analyse de prompts ?",
        "Comment l'algorithme DBSCAN et la décroissance temporelle exponentielle permettent-ils d'écarter le bruit ?",
        "Quelles sont les ressources pédagogiques générées par Upskill AI quand un besoin est détecté ?",
        "Comment le podcast à double voix est-il conçu à partir d'un cours généré ?"
      ]
    }
  ];

  const noisePrompt = "Salut ! Je cherche une recette simple de lasagnes végétariennes pour ce soir, tu as ça ?";

  useEffect(() => {
    checkHealth();
    fetchChatHistory();
    fetchLearnerData();
    fetchManagerData();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/api/health`);
      const data = await res.json();
      setBackendHealthy(res.ok);
    } catch {
      setBackendHealthy(false);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/api/chat/history?user_id=${USER_ID}`);
      const data = await res.json();
      setChatHistory(data.history || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchLearnerData = async () => {
    try {
      const res = await fetch(`${API_URL}/api/dashboard/learner?user_id=${USER_ID}`);
      const data = await res.json();
      setCourses(data.courses || []);
      setPendingTopics(data.pending_topics || []);
      if (data.courses && data.courses.length > 0 && !selectedCourse) {
        setSelectedCourse(data.courses[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchManagerData = async () => {
    try {
      const res = await fetch(`${API_URL}/api/dashboard/manager`);
      const data = await res.json();
      setGlobalStats(data.global_stats || []);
      setTotalAnalyzed(data.total_analyzed_prompts || 0);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendMessage = async (textToSend) => {
    const msg = textToSend || chatMessage;
    if (!msg.trim()) return;

    setIsSending(true);
    if (!textToSend) setChatMessage('');

    // Ajouter temporairement le message utilisateur localement pour la réactivité
    const localUserMsg = { id: Date.now().toString(), role: 'user', content: msg, timestamp: new Date().toISOString() };
    setChatHistory(prev => [...prev, localUserMsg]);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, message: msg })
      });
      const data = await res.json();
      
      // Mettre à jour l'historique réel
      fetchChatHistory();
      fetchLearnerData(); // Pour voir si de nouvelles lacunes en attente apparaissent
      fetchManagerData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSending(false);
    }
  };

  // Charger le scénario de démo en 1 clic
  const loadScenario = async (scenarioName) => {
    setIsSending(true);
    try {
      const res = await fetch(`${API_URL}/api/demo/load`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, scenario: scenarioName })
      });
      if (res.ok) {
        fetchChatHistory();
        fetchLearnerData();
        fetchManagerData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSending(false);
    }
  };

  // Lancer l'analyse Cron (Clustering + Génération)
  const triggerAnalysis = async () => {
    setIsSending(true);
    try {
      const res = await fetch(`${API_URL}/api/demo/trigger-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID })
      });
      const data = await res.json();
      
      await fetchLearnerData();
      await fetchManagerData();
      
      if (data.generated_courses && data.generated_courses.length > 0) {
        setSelectedCourse(data.generated_courses[0]);
        setActiveTab('learner');
        setQuizScore(null);
        setQuizAnswers({});
      } else {
        alert("Analyse terminée : Aucun groupe de lacunes n'a dépassé le seuil d'activation de cours (seuil = 3.0). Continuez à promptter !");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSending(false);
    }
  };

  // Réinitialiser les bases de données
  const resetDb = async () => {
    if (!confirm("Voulez-vous réinitialiser toutes les données de simulation ?")) return;
    try {
      await fetch(`${API_URL}/api/demo/reset`, { method: 'POST' });
      setChatHistory([]);
      setCourses([]);
      setPendingTopics([]);
      setSelectedCourse(null);
      setGlobalStats([]);
      setTotalAnalyzed(0);
      setQuizAnswers({});
      setQuizScore(null);
      stopPodcast();
      alert("Base de données locale réinitialisée !");
    } catch (err) {
      console.error(err);
    }
  };

  // --- PODCAST AUDIO SEQUENCER (SpeechSynthesis) ---
  
  const playPodcast = () => {
    if (!selectedCourse || !selectedCourse.podcast_script || selectedCourse.podcast_script.length === 0) return;
    setIsPlayingPodcast(true);
    speakLine(0);
  };

  const stopPodcast = () => {
    setIsPlayingPodcast(false);
    setCurrentLineIndex(-1);
    if (synthRef.current) {
      synthRef.current.cancel();
    }
    if (speechTimeoutRef.current) {
      clearTimeout(speechTimeoutRef.current);
    }
  };

  const speakLine = (index) => {
    if (!isPlayingPodcast || !selectedCourse || index >= selectedCourse.podcast_script.length) {
      stopPodcast();
      return;
    }

    setCurrentLineIndex(index);
    const line = selectedCourse.podcast_script[index];
    
    // Annuler tout discours en cours
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(line.text);
    
    // Déterminer la langue (Français par défaut)
    utterance.lang = 'fr-FR';

    // Essayer de différencier les voix des hôtes (homme/femme si disponible)
    const voices = synthRef.current.getVoices();
    const frenchVoices = voices.filter(v => v.lang.startsWith('fr'));
    
    if (frenchVoices.length > 0) {
      if (line.speaker === "Hôte A") {
        // Hôte A : Première voix de la liste (ex: Voix 1)
        utterance.voice = frenchVoices[0];
        utterance.pitch = 1.0;
        utterance.rate = 1.05;
      } else {
        // Hôte B : Deuxième voix ou voix modifiée
        utterance.voice = frenchVoices[1] || frenchVoices[0];
        utterance.pitch = 1.2; // Pitch plus aigu pour différencier
        utterance.rate = 1.0;
      }
    }

    utterance.onend = () => {
      // Petite pause entre les répliques
      speechTimeoutRef.current = setTimeout(() => {
        speakLine(index + 1);
      }, 800);
    };

    utterance.onerror = (e) => {
      console.error("Erreur de synthèse vocale : ", e);
      // Passer au suivant en cas d'erreur de voix
      speechTimeoutRef.current = setTimeout(() => {
        speakLine(index + 1);
      }, 1000);
    };

    synthRef.current.speak(utterance);
  };

  // Gérer le changement de cours sélectionné
  const handleSelectCourse = (course) => {
    stopPodcast();
    setSelectedCourse(course);
    setQuizScore(null);
    setQuizAnswers({});
  };

  // Gérer la soumission du Quiz
  const handleQuizAnswer = (qIdx, option) => {
    setQuizAnswers(prev => ({ ...prev, [qIdx]: option }));
  };

  const submitQuiz = () => {
    if (!selectedCourse || !selectedCourse.quiz) return;
    let score = 0;
    selectedCourse.quiz.forEach((q, idx) => {
      if (quizAnswers[idx] === q.answer) {
        score++;
      }
    });
    setQuizScore(score);
  };

  // Convertir le Markdown du cours simple en blocs HTML
  const renderMarkdown = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      if (line.startsWith('# ')) {
        return <h1 key={idx} style={{ color: 'var(--text-primary)', fontSize: '24px', margin: '20px 0 10px 0', borderBottom: '1px solid var(--panel-border)', paddingBottom: '8px' }}>{line.slice(2)}</h1>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={idx} style={{ color: 'var(--primary)', fontSize: '18px', margin: '15px 0 8px 0' }}>{line.slice(3)}</h2>;
      }
      if (line.startsWith('* ') || line.startsWith('- ')) {
        return <li key={idx} style={{ marginLeft: '20px', color: 'var(--text-secondary)', marginBottom: '5px' }}>{line.slice(2)}</li>;
      }
      if (line.startsWith('```')) {
        if (line === '```' || line.startsWith('```python') || line.startsWith('```bash')) {
          return null; // On gère l'ouverture/fermeture du bloc différemment ou on ignore les marqueurs
        }
      }
      if (line.trim() === '') return <div key={idx} style={{ height: '10px' }}></div>;
      
      // Simple mise en valeur du code en ligne ou bloc de code simple
      if (line.includes('`')) {
        const parts = line.split('`');
        return (
          <p key={idx} style={{ color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '8px' }}>
            {parts.map((part, pIdx) => pIdx % 2 === 1 ? <code key={pIdx} style={{ backgroundColor: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px', color: 'var(--accent-cyan)', fontFamily: 'monospace' }}>{part}</code> : part)}
          </p>
        );
      }
      
      return <p key={idx} style={{ color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '8px' }}>{line}</p>;
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-color)', position: 'relative' }}>
      
      {/* HEADER BANNER */}
      <header className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 32px', margin: '16px', borderRadius: 'var(--radius-md)', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)', padding: '10px', borderRadius: 'var(--radius-sm)', boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)' }}>
            <Brain size={24} color="white" />
          </div>
          <div>
            <h1 className="glow-text-primary" style={{ fontSize: '22px', fontWeight: '800' }}>UPSKILL AI</h1>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Agentic Passive Learning POC</span>
          </div>
        </div>

        {/* NAVIGATION */}
        <nav style={{ display: 'flex', gap: '8px' }}>
          <button 
            className={`btn ${activeTab === 'chat' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={18} /> Chatbot local
          </button>
          <button 
            className={`btn ${activeTab === 'learner' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setActiveTab('learner'); fetchLearnerData(); }}
            style={{ position: 'relative' }}
          >
            <BookOpen size={18} /> E-space Apprenant
            {pendingTopics.length > 0 && (
              <span style={{ position: 'absolute', top: '-4px', right: '-4px', backgroundColor: 'var(--accent-rose)', color: 'white', fontSize: '10px', width: '18px', height: '18px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                {pendingTopics.length}
              </span>
            )}
          </button>
          <button 
            className={`btn ${activeTab === 'manager' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setActiveTab('manager'); fetchManagerData(); }}
          >
            <BarChart2 size={18} /> Vue Manager
          </button>
        </nav>

        {/* SYSTEM STATUS */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: backendHealthy ? 'var(--accent-cyan)' : 'var(--accent-rose)' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: backendHealthy ? 'var(--accent-cyan)' : 'var(--accent-rose)', display: 'inline-block', boxShadow: backendHealthy ? '0 0 8px var(--accent-cyan)' : 'none' }}></span>
            {backendHealthy ? 'API Connectée' : 'Déconnecté'}
          </div>
          <button onClick={resetDb} className="btn btn-secondary" style={{ padding: '8px 12px', color: 'var(--accent-rose)', borderColor: 'rgba(244, 63, 94, 0.2)' }} title="Réinitialiser le POC">
            <Trash2 size={16} /> Reset
          </button>
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <main style={{ flex: 1, display: 'flex', padding: '0 16px 16px 16px', gap: '16px', height: 'calc(100vh - 120px)', overflow: 'hidden' }}>
        
        {/* ================= CHATBOT TAB ================= */}
        {activeTab === 'chat' && (
          <>
            {/* LEFT SIDEBAR: DEMO CONTROLS */}
            <div className="glass-panel" style={{ width: '350px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
              <div>
                <h3 className="glow-text-primary" style={{ fontSize: '18px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={18} color="var(--primary)" /> Simulateur de Démo
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  Utilisez ces scénarios préconfigurés pour injecter instantanément l'historique de questions dans la base et tester le clustering.
                </p>
              </div>

              {demoScenarios.map((scenario) => (
                <div key={scenario.name} className="glass-panel" style={{ padding: '16px', background: 'rgba(255,255,255,0.02)' }}>
                  <h4 style={{ fontSize: '14px', color: 'white', marginBottom: '10px' }}>{scenario.title}</h4>
                  
                  {/* Clickable Prompts List */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '12px' }}>
                    {scenario.prompts.map((p, pIdx) => (
                      <button 
                        key={pIdx} 
                        onClick={() => handleSendMessage(p)}
                        style={{ textAlign: 'left', background: 'transparent', border: 'none', color: 'var(--text-secondary)', fontSize: '11px', cursor: 'pointer', padding: '4px', borderLeft: '2px solid var(--panel-border)', transition: 'all 0.2s' }}
                        onMouseEnter={(e) => { e.target.style.color = 'white'; e.target.style.borderLeftColor = 'var(--primary)'; }}
                        onMouseLeave={(e) => { e.target.style.color = 'var(--text-secondary)'; e.target.style.borderLeftColor = 'var(--panel-border)'; }}
                      >
                        "{p.slice(0, 50)}..."
                      </button>
                    ))}
                  </div>

                  <button 
                    onClick={() => loadScenario(scenario.name)}
                    className="btn btn-accent" 
                    style={{ width: '100%', padding: '8px', fontSize: '12px' }}
                    disabled={isSending}
                  >
                    Injecter le scénario complet
                  </button>
                </div>
              ))}

              <div className="glass-panel" style={{ padding: '16px', background: 'rgba(244, 63, 94, 0.05)', borderColor: 'rgba(244, 63, 94, 0.15)' }}>
                <h4 style={{ fontSize: '13px', color: 'var(--accent-rose)', marginBottom: '6px' }}>Bruit Informel (Ignoré)</h4>
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '8px' }}>Testez ce prompt pour prouver que les sujets hors-sujet ne génèrent pas de cours.</p>
                <button 
                  onClick={() => handleSendMessage(noisePrompt)}
                  className="btn btn-secondary" 
                  style={{ width: '100%', padding: '6px', fontSize: '11px', borderColor: 'rgba(244, 63, 94, 0.2)' }}
                >
                  Envoyer question lasagnes 🍕
                </button>
              </div>
            </div>

            {/* MAIN CHAT WINDOW */}
            <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              
              {/* CHAT HEADER */}
              <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--panel-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.1)' }}>
                <div>
                  <h3 style={{ fontSize: '16px', color: 'white' }}>Assistant IA Upskill</h3>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Discutez technique. Vos lacunes généreront vos formations.</span>
                </div>
                <button 
                  onClick={triggerAnalysis} 
                  className="btn btn-primary"
                  style={{ boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)' }}
                  disabled={isSending}
                >
                  Déclencher l'analyse Cron ⚡
                </button>
              </div>

              {/* MESSAGES FEED */}
              <div style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {chatHistory.length === 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', gap: '12px' }}>
                    <MessageSquare size={48} style={{ opacity: 0.3 }} />
                    <p style={{ fontSize: '14px' }}>Envoyez des messages ou injectez un scénario de démo à gauche pour commencer.</p>
                  </div>
                ) : (
                  chatHistory.map((msg, idx) => (
                    <div 
                      key={msg.id || idx} 
                      style={{ 
                        alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        maxWidth: '70%',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px'
                      }}
                    >
                      <div 
                        style={{ 
                          backgroundColor: msg.role === 'user' ? 'var(--primary)' : 'rgba(244, 63, 94, 0.08)',
                          border: msg.role === 'user' ? 'none' : '1px solid rgba(244, 63, 94, 0.3)',
                          borderRadius: msg.role === 'user' ? '18px 18px 2px 18px' : '18px 18px 18px 2px',
                          padding: '12px 18px',
                          color: msg.role === 'user' ? 'white' : '#f87171',
                          fontSize: '14px',
                          lineHeight: '1.5',
                          whiteSpace: 'pre-wrap'
                        }}
                      >
                        {msg.content}
                      </div>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  ))
                )}
                {isSending && (
                  <div 
                    style={{ 
                      alignSelf: 'flex-start',
                      maxWidth: '70%',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      backgroundColor: 'rgba(244, 63, 94, 0.08)',
                      border: '1px solid rgba(244, 63, 94, 0.3)',
                      borderRadius: '18px 18px 18px 2px',
                      padding: '12px 18px',
                      color: '#f87171',
                      fontSize: '13px'
                    }}
                  >
                    <div 
                      style={{ 
                        width: '14px', 
                        height: '14px', 
                        border: '2px solid rgba(244, 63, 94, 0.3)', 
                        borderTopColor: '#f87171', 
                        borderRadius: '50%', 
                        animation: 'spin 0.8s linear infinite' 
                      }}
                    ></div>
                    <span>L'IA analyse et réfléchit...</span>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* INPUT BAR */}
              <div style={{ padding: '16px', borderTop: '1px solid var(--panel-border)', display: 'flex', gap: '12px', background: 'rgba(0,0,0,0.1)' }}>
                <input 
                  type="text" 
                  className="input-field" 
                  style={{ flex: 1 }}
                  placeholder="Posez une question technique..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  disabled={isSending}
                />
                <button 
                  className="btn btn-primary" 
                  onClick={() => handleSendMessage()}
                  disabled={isSending || !chatMessage.trim()}
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </>
        )}

        {/* ================= LEARNER TAB ================= */}
        {activeTab === 'learner' && (
          <>
            {/* LEFT SIDEBAR: LIST OF COURSES & PENDING TOPICS */}
            <div className="glass-panel" style={{ width: '300px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
              
              {/* PENDING TOPICS */}
              <div>
                <h4 style={{ fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                  Lacunes détectées (En attente)
                </h4>
                {pendingTopics.length === 0 ? (
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Aucune lacune en attente d'analyse.</p>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {pendingTopics.map((pt, idx) => (
                      <span key={idx} style={{ fontSize: '11px', backgroundColor: 'rgba(244, 63, 94, 0.1)', color: 'var(--accent-rose)', border: '1px solid rgba(244, 63, 94, 0.2)', padding: '4px 8px', borderRadius: '12px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <AlertCircle size={10} /> {pt.topic}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <hr style={{ border: 'none', borderTop: '1px solid var(--panel-border)' }} />

              {/* GENERATED COURSES */}
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <h4 style={{ fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
                  Formations générées
                </h4>
                {courses.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: '12px' }}>
                    Aucun cours n'a été généré pour le moment.
                  </div>
                ) : (
                  courses.map((course) => (
                    <button
                      key={course.id}
                      onClick={() => handleSelectCourse(course)}
                      style={{ 
                        textAlign: 'left',
                        padding: '12px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: selectedCourse?.id === course.id ? 'var(--primary-glow)' : 'transparent',
                        border: '1px solid',
                        borderColor: selectedCourse?.id === course.id ? 'var(--primary)' : 'transparent',
                        color: 'white',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px'
                      }}
                      onMouseEnter={(e) => { if (selectedCourse?.id !== course.id) e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.02)'; }}
                      onMouseLeave={(e) => { if (selectedCourse?.id !== course.id) e.currentTarget.style.backgroundColor = 'transparent'; }}
                    >
                      <span style={{ fontWeight: '600', fontSize: '13px' }}>{course.topic}</span>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{new Date(course.timestamp).toLocaleDateString()}</span>
                    </button>
                  ))
                )}
              </div>
            </div>

            {/* MAIN LEARNING VIEW */}
            {selectedCourse ? (
              <div style={{ flex: 1, display: 'flex', gap: '16px', overflow: 'hidden' }}>
                
                {/* COURSE CONTENT */}
                <div className="glass-panel" style={{ flex: 1, padding: '32px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  {renderMarkdown(selectedCourse.course_content)}
                </div>

                {/* PODCAST & QUIZ SIDE PANEL */}
                <div style={{ width: '400px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
                  
                  {/* PODCAST CARD */}
                  {selectedCourse.podcast_script && selectedCourse.podcast_script.length > 0 && (
                    <div className="glass-panel" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.1) 100%)', borderColor: 'rgba(99, 102, 241, 0.2)' }}>
                      <h4 style={{ fontSize: '15px', color: 'white', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                        <Volume2 color="var(--primary)" /> Podcast double voix (NotebookLM Style)
                      </h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: '1.4' }}>
                        Écoutez deux experts IA résumer de façon vivante et interactive le contenu de votre formation.
                      </p>

                      {/* AUDIO PLAYER CONTROLS */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                        {!isPlayingPodcast ? (
                          <button onClick={playPodcast} className="btn btn-primary" style={{ borderRadius: '50%', width: '48px', height: '48px', padding: 0 }}>
                            <Play size={20} fill="white" />
                          </button>
                        ) : (
                          <button onClick={stopPodcast} className="btn btn-accent" style={{ borderRadius: '50%', width: '48px', height: '48px', padding: 0 }}>
                            <Pause size={20} fill="white" />
                          </button>
                        )}
                        <div>
                          <span style={{ fontSize: '13px', color: 'white', fontWeight: 'bold', display: 'block' }}>
                            {isPlayingPodcast ? 'Lecture en cours...' : 'Podcast prêt'}
                          </span>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            {selectedCourse.podcast_script.length} répliques alternées
                          </span>
                        </div>
                      </div>

                      {/* DIALOGUE VISUALIZATION FEED */}
                      <div style={{ maxHeight: '200px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', padding: '10px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-sm)' }}>
                        {selectedCourse.podcast_script.map((line, idx) => (
                          <div 
                            key={idx} 
                            style={{ 
                              padding: '6px 10px', 
                              borderRadius: '6px',
                              fontSize: '11px',
                              lineHeight: '1.4',
                              backgroundColor: idx === currentLineIndex ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                              borderLeft: '3px solid',
                              borderLeftColor: idx === currentLineIndex ? 'var(--primary)' : (line.speaker === 'Hôte A' ? 'var(--accent-cyan)' : 'var(--secondary)'),
                              color: idx === currentLineIndex ? 'white' : 'var(--text-secondary)',
                              transition: 'all 0.2s'
                            }}
                          >
                            <strong style={{ color: line.speaker === 'Hôte A' ? 'var(--accent-cyan)' : 'var(--secondary)' }}>{line.speaker}</strong> : {line.text}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* QUIZ CARD */}
                  {selectedCourse.quiz && selectedCourse.quiz.length > 0 && (
                    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      <h4 style={{ fontSize: '15px', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Award color="var(--accent-cyan)" /> Test de validation
                      </h4>
                      
                      {selectedCourse.quiz.map((q, qIdx) => (
                        <div key={qIdx} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          <span style={{ fontSize: '13px', color: 'white', fontWeight: '500' }}>{qIdx + 1}. {q.question}</span>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {q.options.map((opt, optIdx) => (
                              <button 
                                key={optIdx}
                                onClick={() => handleQuizAnswer(qIdx, opt)}
                                style={{ 
                                  textAlign: 'left',
                                  padding: '8px 12px',
                                  fontSize: '12px',
                                  borderRadius: '6px',
                                  cursor: 'pointer',
                                  border: '1px solid',
                                  backgroundColor: quizAnswers[qIdx] === opt ? 'var(--primary-glow)' : 'rgba(255,255,255,0.01)',
                                  borderColor: quizAnswers[qIdx] === opt ? 'var(--primary)' : 'var(--panel-border)',
                                  color: quizAnswers[qIdx] === opt ? 'white' : 'var(--text-secondary)',
                                  transition: 'all 0.15s'
                                }}
                              >
                                {opt}
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}

                      {quizScore === null ? (
                        <button 
                          className="btn btn-accent" 
                          onClick={submitQuiz}
                          disabled={Object.keys(quizAnswers).length < selectedCourse.quiz.length}
                          style={{ width: '100%', marginTop: '10px' }}
                        >
                          Valider mes réponses
                        </button>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', borderRadius: 'var(--radius-sm)', backgroundColor: 'rgba(6, 182, 212, 0.05)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                          <CheckCircle2 color="var(--accent-cyan)" size={32} />
                          <span style={{ color: 'white', fontWeight: 'bold' }}>Quiz Validé !</span>
                          <span style={{ fontSize: '18px', color: 'var(--accent-cyan)', fontWeight: '800' }}>
                            {quizScore} / {selectedCourse.quiz.length} Correct
                          </span>
                          <button onClick={() => setQuizScore(null)} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '11px', marginTop: '6px' }}>
                            Recommencer
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                </div>
              </div>
            ) : (
              <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                <BookOpen size={64} style={{ opacity: 0.3, marginBottom: '16px' }} />
                <p>Aucun cours disponible.</p>
                <p style={{ fontSize: '12px' }}>Retournez sur le Chatbot pour envoyer des prompts ou charger un scénario de démo.</p>
              </div>
            )}
          </>
        )}

        {/* ================= MANAGER TAB ================= */}
        {activeTab === 'manager' && (
          <div style={{ flex: 1, display: 'flex', gap: '16px', overflowY: 'auto' }}>
            
            {/* LEFT STATS AND GRAPHS */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
              
              {/* TOP CARDS ROW */}
              <div style={{ display: 'flex', gap: '16px' }}>
                <div className="glass-panel" style={{ flex: 1, padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ backgroundColor: 'var(--primary-glow)', padding: '16px', borderRadius: 'var(--radius-sm)', color: 'var(--primary)' }}>
                    <MessageSquare size={24} />
                  </div>
                  <div>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block' }}>Prompts Totaux Analysés</span>
                    <strong style={{ fontSize: '24px', color: 'white' }}>{totalAnalyzed}</strong>
                  </div>
                </div>

                <div className="glass-panel" style={{ flex: 1, padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ backgroundColor: 'var(--accent-cyan-glow)', padding: '16px', borderRadius: 'var(--radius-sm)', color: 'var(--accent-cyan)' }}>
                    <TrendingUp size={24} />
                  </div>
                  <div>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block' }}>Sujets de lacunes distincts</span>
                    <strong style={{ fontSize: '24px', color: 'white' }}>{globalStats.length}</strong>
                  </div>
                </div>
              </div>

              {/* DETAILED STATS LIST */}
              <div className="glass-panel" style={{ flex: 1, padding: '32px' }}>
                <h3 className="glow-text-primary" style={{ fontSize: '18px', marginBottom: '20px' }}>Tendances de besoins en compétences (Groupe)</h3>
                
                {globalStats.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Aucune donnée statistique disponible pour le moment.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {globalStats.map((stat, idx) => (
                      <div key={idx} style={{ padding: '16px', borderRadius: 'var(--radius-sm)', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid var(--panel-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <span style={{ color: 'white', fontWeight: 'bold', fontSize: '14px', display: 'block', marginBottom: '4px' }}>
                            {stat.topic}
                          </span>
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block' }}>
                            Extraits : {stat.summary.slice(0, 100)}...
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            Dernier prompt : {new Date(stat.latest).toLocaleDateString()}
                          </span>
                          <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--primary)', color: 'white', fontWeight: 'bold', fontSize: '12px', width: '28px', height: '28px', borderRadius: '50%' }}>
                            {stat.count}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* RIGHT SIDEBAR: AI-GENERATED REPORT */}
            <div className="glass-panel" style={{ width: '450px', padding: '32px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <h3 className="glow-text-primary" style={{ fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Users color="var(--primary)" /> Synthèse AI Manager
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                Cette synthèse automatique et anonyme permet aux responsables formation d'identifier les tendances de lacunes au niveau de l'équipe ou de l'entreprise.
              </p>

              <hr style={{ border: 'none', borderTop: '1px solid var(--panel-border)' }} />

              <div style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.2)', padding: '20px', borderRadius: 'var(--radius-sm)', fontSize: '13px', lineHeight: '1.6', color: 'var(--text-secondary)', overflowY: 'auto' }}>
                {globalStats.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)' }}>En attente de données pour générer le rapport...</p>
                ) : (
                  <div>
                    <h4 style={{ color: 'white', marginBottom: '10px' }}>📌 Diagnostic de formation du mois</h4>
                    <p style={{ marginBottom: '12px' }}>
                      L'analyse passive montre une concentration de lacunes sur le sujet <strong>{globalStats[0]?.topic}</strong> ({globalStats[0]?.count} signaux détectés).
                    </p>
                    <p style={{ marginBottom: '12px' }}>
                      <strong>Recommandation :</strong> Il est fortement suggéré de planifier un atelier pratique de 2 heures en groupe sur ce thème. Les ressources autonomes (cours et podcasts) ont déjà été distribuées de façon individualisée aux apprenants concernés.
                    </p>
                    <p>
                      <strong>Indice de maturité :</strong> Stable. Les thématiques de développement restent dominantes cette semaine.
                    </p>
                  </div>
                )}
              </div>
            </div>

          </div>
        )}

      </main>
    </div>
  );
}
