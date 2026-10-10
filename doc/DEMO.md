# Guide de Démonstration - GOB Agent

Guide complet pour présenter le projet lors de la soutenance.

---

## 🎬 Scénarios de Démonstration

### Scenario 1: Conversation Simple avec Mémoire

**Objectif**: Démontrer la reconnaissance vocale, conversation naturelle, et mémoire persistante.

**Étapes:**

1. **Lancement de l'agent**
   ```
   User clique sur MicButton
   Avatar: idle → listening (animation micro)
   ```

2. **Premier contact**
   ```
   User: "Hello!"
   
   STT transcription affichée: "Hello!"
   Avatar: listening → thinking (animation engrenages)
   
   Agent response: "Hello! I'm GOB, your personal assistant. How can I help you today?"
   Avatar: thinking → speaking (animation bouche)
   Audio response joue automatiquement
   
   Conversation History: Message ajouté
   Memory Panel: Pas de nouvelle info
   ```

3. **Partage d'informations personnelles**
   ```
   User: "My name is Yamin and I really love pizza"
   
   STT: "My name is Yamin and I really love pizza"
   
   Agent: "Nice to meet you, Yamin! I'll remember that you love pizza. Is there anything specific you'd like help with today?"
   
   Memory Panel se met à jour:
   ┌────────────────────────────────┐
   │ 💾 Memory Panel                │
   │                                │
   │ 👤 Name: Yamin                 │
   │ 🍕 Likes: pizza                │
   │ 📊 Facts: 2                    │
   │ 😊 Mood: happy                 │
   └────────────────────────────────┘
   ```

4. **Test de rappel mémoire** (fermer et rouvrir UI)
   ```
   User refresh la page → Login à nouveau
   User: "What's my name?"
   
   Agent: "Your name is Yamin! I remember you also love pizza."
   
   ✅ Démontre: Persistance mémoire dans SQLite
   ```

**Points à souligner:**

- ✨ **STT en temps réel**: Whisper transcription instantanée
- 🎯 **LLM contextuel**: Ollama comprend et répond naturellement
- 💾 **Memory extraction**: Entités automatiquement extraites et stockées
- 🔊 **TTS naturel**: Piper génère audio fluide
- 📱 **UI responsive**: Animations Lottie fluides
- 🧠 **Persistance**: Mémoire conservée entre sessions

---

### Scenario 2: Contrôle IoT avec Confirmation

**Objectif**: Démontrer la classification, génération d'actions, workflow de confirmation, et ActionPanel.

**Étapes:**

1. **Commande IoT**
   ```
   User: "Turn on the lamp in the living room"
   
   STT: "Turn on the lamp in the living room"
   Avatar: thinking (plus longue pause)
   
   Classification: ACTION détectée (mots clés: "turn on", "lamp")
   LLM analyse et extrait entités:
   {
     "device_type": "lamp",
     "action": "turn_on",
     "location": "living_room"
   }
   
   ActionJSON créé avec action_id: act_abc123
   État: DRAFT → PENDING_CONFIRMATION
   
   Agent: "I understand you want to turn on the lamp in the living room. Should I proceed?"
   
   Conversation History affiche la demande de confirmation
   ```

2. **ActionPanel apparaît**
   ```
   Panneau à droite montre:
   
   ┌───────────────────────────────────┐
   │ ⚡ Actions (1)            [🔄]    │
   │                                   │
   │ 🟠 act_abc123 (PENDING)           │
   │    💡 Lamp - living_room          │
   │    ⏱️ 2 seconds ago                │
   │    Action: turn_on                │
   │                                   │
   │    Waiting for confirmation...    │
   │    ▓░░░░░░░░░░ 10%               │
   └───────────────────────────────────┘
   ```

3. **Confirmation "yes"**
   ```
   User: "Yes"
   
   Agent: "Great! I'm executing the action to turn on the lamp."
   
   ActionPanel mise à jour en temps réel:
   
   État: PENDING → CONFIRMED → EXECUTING
   Couleur: 🟠 → 🟣
   
   ┌───────────────────────────────────┐
   │ ⚡ Actions (1)            [🔄]    │
   │                                   │
   │ 🟣 act_abc123 (EXECUTING)         │
   │    💡 Lamp - living_room          │
   │    ⏱️ 5 seconds ago                │
   │    Action: turn_on                │
   │                                   │
   │    Sending to smart home...       │
   │    ▓▓▓▓▓▓▓▓░░ 70%               │
   └───────────────────────────────────┘
   
   Backend send ActionJSON signé à n8n webhook
   n8n exécute le workflow IoT
   Callback manuel → /action/status/act_abc123
   
   ┌───────────────────────────────────┐
   │ ⚡ Actions (1)            [🔄]    │
   │                                   │
   │ 🟢 act_abc123 (COMPLETED)         │
   │    💡 Lamp - living_room          │
   │    ⏱️ 12 seconds ago               │
   │    Action: turn_on                │
   │                                   │
   │    ✅ Done!                        │
   │    ▓▓▓▓▓▓▓▓▓▓ 100%              │
   └───────────────────────────────────┘
   ```

4. **Annulation (alternative)**
   ```
   User: "Turn off the door in the bedroom"
   
   Agent: "Do you want me to close the door in the bedroom?"
   
   ActionPanel: 🟠 PENDING_CONFIRMATION
   
   User: "No, cancel that"
   
   Agent: "Okay, I've canceled the action."
   
   ActionPanel:
   🔴 act_xyz789 (CANCELED)
      🚪 Door - bedroom
      Action: close
      ❌ Canceled by user
   ```

**Points à souligner:**

- 🎯 **Classification intelligente**: Détection automatique Action vs Conversation
- 🏗️ **Action Builder**: Construction automatique ActionJSON structuré
- 🔄 **State Machine**: Transitions d'états validées (DRAFT → PENDING → CONFIRMED → EXECUTING → COMPLETED)
- ✅ **Confirmation obligatoire**: Sécurité avant exécution IoT
- 📡 **ActionPanel temps réel**: Polling toutes les 10s pour mises à jour en direct
- 🔐 **Signature HMAC**: ActionJSON signé pour sécurité n8n
- 📊 **Visualisation états**: Couleurs et icônes selon état action

---

### Scenario 3: Settings Panel - Multi-langue

**Objectif**: Démontrer la personnalisation et support multi-langue (EN/FR/AR).

**Étapes:**

1. **Ouvrir Settings**
   ```
   User clique sur le bouton ⚙️ en haut à droite
   
   Modal s'ouvre avec:
   ┌─────────────────────────────────────────┐
   │          ⚙️ Settings                    │
   │                                         │
   │  🌐 Language                            │
   │  ┌──────┐  ┌──────┐  ┌──────┐         │
   │  │🇬🇧 EN │  │🇫🇷 FR │  │🇸🇦 AR │         │
   │  └──────┘  └──────┘  └──────┘         │
   │     ✓                                  │
   │                                         │
   │  🔊 Audio Output        [ON  ]         │
   │  🌙 Dark Mode           [OFF ]         │
   │  ⌨️ Keyboard Shortcut   SPACE          │
   │                                         │
   │  [Reset to Defaults]                   │
   │                                         │
   │  Version: 1.0.0                        │
   └─────────────────────────────────────────┘
   ```

2. **Changer en Français**
   ```
   User clique sur 🇫🇷 FR
   
   Modal se ferme
   localStorage.setItem('gob-settings', { language: 'fr', ... })
   ```

3. **Conversation en français**
   ```
   User: "Bonjour!"
   
   API call: POST /command/audio
   Body: { audio: "...", language: "fr", user_id: "..." }
   
   Console log: 🌐 Using language: fr
   
   STT: "Bonjour!"
   LLM reçoit: language = "fr" dans le prompt
   
   Agent: "Bonjour! Je suis GOB, votre assistant personnel. Comment puis-je vous aider aujourd'hui?"
   
   TTS: Audio en français (voix Piper FR)
   ```

4. **Test multi-langue mixte**
   ```
   User reste en français
   User: "Allumer la lampe dans le salon"
   
   Agent (FR): "Je comprends que vous voulez allumer la lampe dans le salon. Dois-je procéder?"
   
   ActionPanel affiche:
   💡 Lampe - salon
   Action: allumer
   ```

5. **Dark Mode demo**
   ```
   User ouvre Settings
   User toggle 🌙 Dark Mode ON
   
   UI transitions:
   - Background: white → #1a1a2e
   - Cards: white → #16213e
   - Text: black → #eaeaea
   - Avatar border: cyan → violet
   
   body.dark-mode class appliquée
   ```

**Points à souligner:**

- 🌐 **Multi-langue native**: EN/FR/AR supportés
- 💾 **Persistence localStorage**: Settings conservés entre sessions
- 🎨 **Dark mode complet**: Tous les composants adaptés
- 🔊 **Toggle audio**: Contrôle playback TTS
- ⌨️ **Keyboard shortcuts**: SPACE ou Ctrl+K pour enregistrer
- 🚀 **Sans reload**: Changements appliqués immédiatement

---

### Scenario 4: Memory Panel - Gestion Contexte

**Objectif**: Démontrer la mémoire contextuelle longue durée.

**Étapes:**

1. **Construire le profil utilisateur**
   ```
   Conversation 1:
   User: "My name is Ahmed"
   Agent: "Nice to meet you, Ahmed!"
   Memory: 👤 Ahmed
   
   Conversation 2:
   User: "I live in Tunis"
   Agent: "That's great! Tunisia is beautiful."
   Memory: 📍 Location: Tunis
   
   Conversation 3:
   User: "I have a smart TV and a coffee maker"
   Agent: "I've noted your devices. I can help control them!"
   Memory: 
     📺 Device: smart TV
     ☕ Device: coffee maker
   
   Conversation 4:
   User: "I prefer coffee in the morning"
   Agent: "I'll remember that you like coffee in the morning."
   Memory: ☕ Preference: coffee (morning)
   ```

2. **Memory Panel affiche tout**
   ```
   ┌─────────────────────────────────────┐
   │ 💾 Memory Panel           [Expand]  │
   ├─────────────────────────────────────┤
   │                                     │
   │ 👤 Name: Ahmed                      │
   │ 📍 Location: Tunis                  │
   │                                     │
   │ Devices (2):                        │
   │   📺 Smart TV                       │
   │   ☕ Coffee Maker                   │
   │                                     │
   │ Preferences:                        │
   │   ☕ Coffee in morning              │
   │                                     │
   │ Recent emotions:                    │
   │   😊 happy, 😌 satisfied            │
   │                                     │
   │ 📊 Total facts: 5                   │
   │ 💬 Conversations: 4                 │
   └─────────────────────────────────────┘
   ```

3. **Utilisation du contexte**
   ```
   Nouvelle session (après reload)
   
   User: "Can you make me coffee?"
   
   Backend charge memory context:
   - Name: Ahmed
   - Location: Tunis
   - Has coffee maker
   - Prefers coffee in morning
   
   LLM reçoit contexte injecté dans prompt
   
   Agent: "Good morning, Ahmed! I can turn on your coffee maker. Should I proceed?"
   
   ✅ Agent utilise le nom, connaît l'appareil, et comprend la préférence
   ```

4. **Expansion du panneau**
   ```
   User clique sur [Expand]
   
   Panel s'agrandit et montre:
   
   ┌─────────────────────────────────────────────────┐
   │ 💾 Memory Panel                    [Collapse]   │
   ├─────────────────────────────────────────────────┤
   │                                                 │
   │ 📋 All Facts (5):                               │
   │                                                 │
   │ 1. 👤 person: Ahmed                             │
   │    Source: Conv #123                            │
   │    Confidence: 95%                              │
   │    Extracted: 10 min ago                        │
   │                                                 │
   │ 2. 📍 location: Tunis                           │
   │    Source: Conv #124                            │
   │    Confidence: 90%                              │
   │    Extracted: 8 min ago                         │
   │                                                 │
   │ 3. 📺 device: Smart TV                          │
   │    Source: Conv #125                            │
   │    Confidence: 85%                              │
   │    Extracted: 5 min ago                         │
   │                                                 │
   │ ... (voir tous les facts)                       │
   │                                                 │
   │ 💬 Conversation History:                        │
   │                                                 │
   │ Conv #125 - 5 min ago:                          │
   │ User: "I have a smart TV"                       │
   │ Agent: "I've noted your devices"                │
   │ Classification: conversation                    │
   │ Emotion: neutral                                │
   │                                                 │
   │ ... (scroll pour voir historique complet)       │
   └─────────────────────────────────────────────────┘
   ```

**Points à souligner:**

- 💾 **Extraction automatique**: LLM extrait entités sans prompts spécifiques
- 🗄️ **SQLite storage**: Persistance long terme
- 📊 **Confidence scores**: Mesure fiabilité extraction
- 🔗 **Source tracking**: Chaque fact lié à conversation d'origine
- 🧠 **Context injection**: Mémoire injectée dans chaque prompt LLM
- 🌐 **Multi-user**: Isolation mémoire par user_id

---

## 🎯 Points Clés à Démontrer

### 1. Intelligence Conversationnelle

| Capacité | Démo | Preuve |
|----------|------|--------|
| Compréhension langage naturel | "Turn on the lamp" → action extracted | LLM parse intent + entities |
| Mémoire contextuelle | "Who am I?" → "You're Ahmed" | SQLite memory lookup |
| Multi-tour conversation | Suivi du contexte entre messages | Conversation history injected |
| Détection émotions | "I'm frustrated" → 😤 mood updated | Memory Panel affect display |

### 2. Architecture Modulaire

| Module | Point technique | Visibilité |
|--------|-----------------|------------|
| STT | Faster-Whisper offline | Transcription instantanée |
| LLM | Ollama local (Mistral 7B) | Réponses naturelles |
| TTS | Piper Wyoming protocol | Audio généré |
| Memory | SQLite + LLM extraction | Memory Panel |
| Actions | State machine + confirmation | ActionPanel |

### 3. Sécurité & Fiabilité

| Aspect | Implémentation | Demo |
|--------|----------------|------|
| Confirmation obligatoire | Actions nécessitent "yes" | User dit "no" → canceled |
| Signature HMAC | ActionJSON signé avant envoi | Code dans security_manager.py |
| State machine | Transitions validées | Pas d'état invalide possible |
| Error handling | Try/catch + fallbacks | Backend crash → front affiche erreur Toast |

### 4. UI/UX

| Feature | Qualité | Impact |
|---------|---------|--------|
| Animations Lottie | 4 états (idle/listening/thinking/speaking) | Immersion utilisateur |
| Temps réel | Polling 10s ActionPanel | Feedback immédiat |
| Dark mode | Support complet | Accessibilité |
| Multi-langue | EN/FR/AR | Inclusion |
| Responsive | Mobile/Desktop | Utilisable partout |

---

## 🚀 Script de Présentation (5 minutes)

### Minute 1: Introduction

> "Bonjour, je vais vous présenter **GOB Agent**, un assistant conversationnel multimodal pour le contrôle IoT domestique.  
> 
> Le projet combine **reconnaissance vocale**, **IA générative locale**, et **workflow d'actions IoT sécurisé**.  
> 
> Stack technique: React TypeScript, FastAPI Python, Ollama LLM, Whisper STT, Piper TTS, SQLite."

### Minute 2: Demo Conversation

> "Je commence par une conversation simple."
> 
> [DEMO: "Hello" → "My name is Yamin" → Memory Panel update]
> 
> "Vous voyez ici:
> - La transcription STT en temps réel
> - La réponse LLM contextuelle
> - L'extraction automatique d'entités dans le Memory Panel
> - La génération audio TTS
> 
> Tout cela fonctionne **entièrement offline**, sans APIs cloud."

### Minute 3: Demo IoT Action

> "Maintenant, une commande IoT."
> 
> [DEMO: "Turn on the lamp" → Confirmation → "Yes" → ActionPanel EXECUTING → COMPLETED]
> 
> "Le système:
> 1. **Classifie** l'intent comme ACTION (vs conversation)
> 2. **Extrait** les entités (device, action, location)
> 3. **Construit** un ActionJSON structuré
> 4. **Demande confirmation** obligatoire
> 5. **Signe** l'action avec HMAC
> 6. **Envoie** à n8n pour exécution
> 7. **Visualise** l'état en temps réel dans ActionPanel
> 
> La state machine garantit qu'aucune action n'est exécutée sans confirmation explicite."

### Minute 4: Demo Settings & Memory

> "Le système est personnalisable."
> 
> [DEMO: Settings → Change to FR → "Bonjour" → French response]
> 
> "Support natif de 3 langues avec TTS adapté.  
> Dark mode pour l'accessibilité.  
> Tout persisté dans localStorage."
> 
> [DEMO: Memory Panel expansion]
> 
> "La mémoire SQLite stocke:
> - Profil utilisateur
> - Préférences
> - Appareils connectés
> - Historique conversations
> 
> Injecté automatiquement dans chaque prompt LLM pour un contexte continu."

### Minute 5: Architecture & Conclusion

> "Architecture en 5 couches:
> 1. **Frontend React** - UI responsive animations Lottie
> 2. **API FastAPI** - 12 endpoints RESTful
> 3. **Agent Core** - Pipeline orchestration
> 4. **Services AI** - STT/LLM/TTS modular
> 5. **Data Layer** - SQLite + MQTT
> 
> **Chiffres:**
> - 4500 lignes backend Python
> - 2500 lignes frontend TypeScript
> - 10 composants React
> - 12 endpoints API
> - 5 animations Lottie
> - 3 langues supportées
> 
> **Contributions:**
> - Pipeline IA locale complète (pas de cloud)
> - State machine d'actions IoT sécurisé
> - Système de mémoire contextuelle évolutif
> - UI temps réel avec animations fluides
> 
> Merci pour votre attention!"

---

## 📋 Checklist Soutenance

### Avant la Présentation

- [ ] Backend running: `cd backend && uvicorn main:app --reload`
- [ ] Frontend running: `cd agent-ui && npm run dev`
- [ ] Ollama running: `ollama serve` + `ollama pull mistral`
- [ ] Piper TTS container: `docker ps` → vérifier Wyoming running
- [ ] Database reset: `rm backend/gob_agent.db` (pour démo propre)
- [ ] Browser ready: `http://localhost:5173` + Console DevTools open
- [ ] Microphone test: Enregistrer 5s et vérifier transcription
- [ ] Backend logs visible: Terminal avec output coloré

### Pendant la Démo

- [ ] Montrer transcription STT en direct
- [ ] Montrer Animation Avatar transitions
- [ ] Montrer Memory Panel update en temps réel
- [ ] Montrer ActionPanel progression états
- [ ] Montrer Settings multi-langue
- [ ] Montrer Dark mode toggle
- [ ] Montrer Conversation History scroll
- [ ] Montrer Backend logs (classification, LLM calls)

### Questions Possibles

**Q: Pourquoi offline et pas ChatGPT?**
> "Pour la vie privée, latence réduite, et coût zéro. Ollama + Mistral 7B offre ~80% de la qualité de GPT-3.5 mais en local."

**Q: Comment garantir la sécurité IoT?**
> "Confirmation obligatoire + signature HMAC + state machine validée. Aucune action directe sans validation humaine."

**Q: Et si le mic ne fonctionne pas?**
> "Input text alternatif disponible avec POST /command/text. Même pipeline backend."

**Q: Performances sur CPU faible?**
> "Whisper 'tiny' model: 400ms. LLM peut tourner sur CPU (3-5s). Configurations modulaires dans config.py."

**Q: Scalabilité multi-utilisateurs?**
> "SQLite suffit pour 10-100 users. Pour plus: PostgreSQL + Redis cache + load balancing FastAPI instances."

**Q: Memory Panel révèle-t-elle des données sensibles?**
> "Uniquement les facts explicitement extraits. Pas de stockage des conversations complètes (sauf IDs). Option future: chiffrement SQLite."

---

## 🎥 Enregistrement Vidéo Demo

Si vous préparez une vidéo:

### Structure

1. **Intro (10s)**
   - Logo/Titre: "GOB Agent - Personal AI Assistant"
   - Nom, classe, date

2. **Overview (20s)**
   - Screen capture: Architecture diagram
   - Voix off: "Multimodal AI agent with voice control and IoT integration"

3. **Demo 1: Conversation (40s)**
   - Split screen: UI left, backend logs right
   - Scenario: Hello → Name sharing → Memory update
   - Zoom sur Memory Panel

4. **Demo 2: IoT Action (50s)**
   - Full screen UI
   - Scenario: Turn on lamp → Confirmation → ActionPanel progression
   - Highlight: État transitions PENDING → EXECUTING → COMPLETED

5. **Demo 3: Settings (30s)**
   - Quick: Language change → French conversation
   - Quick: Dark mode toggle

6. **Architecture (30s)**
   - Slides: React → FastAPI → Ollama/Whisper/Piper → SQLite
   - Highlight: Offline-first, modular

7. **Conclusion (10s)**
   - Stats display: 7000 lignes code, 12 endpoints, 3 langues
   - Merci!

**Total: 3 min**

### Outils

- **Screen recording**: OBS Studio (gratuit)
- **Video editing**: DaVinci Resolve (gratuit)
- **Voice over**: Audacity (gratuit)
- **Subtitles**: YouTube auto-captions → export SRT

---

**Version**: 1.0.0  
**Dernière mise à jour**: 14 février 2026
