# Architecture Technique - GOB Agent

Documentation détaillée de l'architecture système.

---

## 🏛️ Vue d'Ensemble Architecture

### Architecture en Couches

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRÉSENTATION LAYER                           │
│  React UI (TypeScript) - Vite - Zustand - Lottie              │
└─────────────────────────────────────────────────────────────────┘
                            ↕ HTTP/JSON
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER                                  │
│  FastAPI - Pydantic - CORS - Middleware                       │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                         │
│  AgentCore - StateManager - ActionBuilder                     │
│  MemoryService - ConfirmationHandler                          │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                               │
│  STT (Whisper) - LLM (Ollama) - TTS (Piper)                  │
│  Classifier - Memory Extractor                                │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
│  SQLite Database - File System - MQTT (optional)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Backend Architecture

### 📂 Structure des Fichiers

```
backend/
├── main.py                    # Point d'entrée FastAPI
├── config.py                  # Configuration centralisée
├── requirements.txt           # Dépendances Python
├── .env                       # Variables d'environnement
│
├── agent/                     # Core Agent Logic
│   ├── __init__.py
│   ├── agent_core.py         # Orchestrateur principal
│   ├── classifier.py         # Classification Conversation/Action
│   ├── state_manager.py      # Gestion états actions
│   ├── memory_service.py     # Service mémoire utilisateur
│   ├── logger_service.py     # Logging structuré
│   └── tests/                # Tests unitaires
│       ├── test_agent_core.py
│       ├── test_classifier.py
│       └── test_memory.py
│
├── llm/                       # LLM Integration
│   ├── __init__.py
│   ├── base_client.py        # Interface abstraite
│   ├── ollama_client.py      # Client Ollama
│   └── prompts.py            # System prompts
│
├── stt/                       # Speech-to-Text
│   ├── __init__.py
│   ├── base_stt.py
│   └── whisper_stt.py        # Faster-Whisper
│
├── tts/                       # Text-to-Speech
│   ├── __init__.py
│   ├── base_tts.py
│   └── piper_tts.py          # Piper via Wyoming
│
├── actions/                   # Action Management
│   ├── __init__.py
│   ├── action_builder.py     # Création ActionJSON
│   ├── confirmation_handler.py
│   ├── security_manager.py   # HMAC signatures
│   └── n8n_client.py         # Client n8n (optionnel)
│
├── memory/                    # Memory System
│   ├── __init__.py
│   ├── memory_extractor.py   # Extraction entités
│   └── database.py           # SQLite operations
│
└── mqtt/                      # MQTT Integration
    ├── __init__.py
    └── mqtt_client.py        # Client MQTT IoT
```

### 🔄 Agent Core - Flux Principal

**Fichier**: `backend/agent/agent_core.py`

```python
class AgentCore:
    """Orchestrateur central du système"""
    
    def __init__(self):
        self.stt_engine: WhisperSTT
        self.llm_client: OllamaClient
        self.tts_engine: PiperTTS
        self.classifier: Classifier
        self.memory_service: MemoryService
        self.state_manager: StateManager
        self.action_builder: ActionBuilder
        self.confirmation_handler: ConfirmationHandler
        self.security_manager: SecurityManager
        self.mqtt_client: MQTTClient  # Optionnel
        self.logger: LoggerService
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Point d'entrée principal
        
        Pipeline:
        1. Extract text (from text or audio via STT)
        2. Check for pending action (bypass classification)
        3. Classify: Conversation vs Action
        4. Route to appropriate handler
        5. Return response with metadata
        """
        
        # 1. Text extraction
        if input_data["command_type"] == "audio":
            text = await self._call_stt(audio_data, audio_format)
        else:
            text = input_data["text"]
        
        # 2. Pending action priority
        pending_action = self.state_manager.get_pending_action(user_id)
        if pending_action:
            return await self._handle_pending_confirmation(...)
        
        # 3. Classification
        classification = await self._classify_intent(text, language)
        
        # 4. Routing
        if classification["type"] == "conversation":
            result = await self._handle_conversation(...)
        else:
            result = await self._handle_action(...)
        
        return result
```

**Méthodes clés:**

```python
async def _handle_conversation(text, user_id, language) -> Dict:
    """
    Pipeline Conversation:
    1. Load memory context
    2. Generate LLM response
    3. Store conversation
    4. Extract new facts/entities
    5. Generate TTS audio
    6. Publish audio to MQTT (optionnel)
    """

async def _handle_action(text, user_id, language, classification) -> Dict:
    """
    Pipeline Action:
    1. LLM analyze intent + extract entities
    2. Validate required entities
    3. Build ActionJSON
    4. Create action in DRAFT state
    5. Transition to PENDING_CONFIRMATION
    6. Generate confirmation message
    7. TTS confirmation audio
    8. Return action details
    """

async def confirm_action(action_id, user_response) -> Dict:
    """
    Traitement confirmation:
    - "yes" → CONFIRMED → send to n8n → EXECUTING
    - "no" → CANCELED
    - "change" → back to DRAFT
    """
```

---

### 🧠 State Manager - Machine à États

**Fichier**: `backend/agent/state_manager.py`

**Diagramme des états:**

```
                    ┌──────┐
                    │DRAFT │
                    └──┬───┘
                       │ create_action()
                       ↓
            ┌──────────────────────┐
            │PENDING_CONFIRMATION  │
            └──────────┬───────────┘
                       │
          ┌────────────┼────────────┐
          │ yes        │ no         │ change
          ↓            ↓            ↓
    ┌─────────┐  ┌─────────┐  ┌──────┐
    │CONFIRMED│  │CANCELED │  │DRAFT │
    └────┬────┘  └─────────┘  └──────┘
         │ execute_action()
         ↓
    ┌─────────┐
    │EXECUTING│
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    ↓         ↓
┌─────────┐ ┌──────┐
│COMPLETED│ │FAILED│
└─────────┘ └──────┘
```

**Transitions validées:**

```python
VALID_TRANSITIONS = {
    "DRAFT": ["PENDING_CONFIRMATION", "CANCELED"],
    "PENDING_CONFIRMATION": ["CONFIRMED", "CANCELED", "DRAFT"],
    "CONFIRMED": ["EXECUTING", "FAILED"],
    "EXECUTING": ["COMPLETED", "FAILED"],
    "COMPLETED": [],  # Terminal
    "CANCELED": [],   # Terminal
    "FAILED": []      # Terminal
}
```

**Storage:**

```python
# In-memory storage (restart = loss)
self.actions: Dict[str, Dict] = {}  # action_id → action_data

# Chaque action:
{
    "action_id": "act_123",
    "current_state": "PENDING_CONFIRMATION",
    "action_json": {...},  # ActionJSON complet
    "history": [...]       # Historique transitions
}
```

---

### 💾 Memory Service - Système de Mémoire

**Fichier**: `backend/agent/memory_service.py`

**Base de données SQLite:**

```sql
-- Table: user_facts
CREATE TABLE user_facts (
    fact_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    fact_type TEXT,      -- person, preference, device, location, etc.
    fact_text TEXT,
    confidence REAL,
    extracted_at TEXT,
    source_conversation_id TEXT,
    metadata TEXT        -- JSON for additional data
);

-- Table: conversations
CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_message TEXT,
    agent_response TEXT,
    timestamp TEXT,
    classification TEXT, -- conversation or action
    metadata TEXT        -- JSON: entities, emotion, intent
);

-- Index pour performances
CREATE INDEX idx_user_facts_user_id ON user_facts(user_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
```

**Memory Extractor:**

```python
class MemoryExtractor:
    """Extraction entités et émotions depuis conversations"""
    
    async def extract_from_conversation(
        self, 
        user_message: str, 
        agent_response: str, 
        user_id: str
    ) -> Dict:
        """
        Utilise le LLM pour extraire:
        1. Entités (person, food, drink, device, location)
        2. Émotion (happy, frustrated, angry, neutral)
        3. Intent (order_food, control_device, general_chat)
        4. Summary (résumé conversation)
        """
        
        prompt = f"""
        Analyze this conversation and extract:
        - Entities (person, food, drink, device, location, object)
        - User emotion
        - Intent
        - Brief summary
        
        User: {user_message}
        Agent: {agent_response}
        """
        
        llm_response = await self.llm_client.generate(prompt)
        structured_data = self._parse_llm_output(llm_response)
        
        # Store in database
        for entity in structured_data["entities"]:
            self.memory_service.store_fact(
                user_id=user_id,
                fact_type=entity["type"],
                fact_text=entity["text"],
                confidence=entity["confidence"]
            )
        
        return structured_data
```

**Context Loading:**

```python
async def load_memory_context(self, user_id: str) -> str:
    """
    Charge le contexte mémoire pour injection dans le prompt LLM
    
    Returns formatted string:
    '''
    ## User Memory Context:
    
    ### About the user:
    - Name: Yamin
    - Likes pizza and coffee
    - Has a smart lamp in living room
    
    ### Recent emotions:
    - happy, satisfied, curious
    
    ### Previous conversations (last 3):
    1. User: "Hello" → Agent: "Hi! How can I help?"
    2. User: "My name is Yamin" → Agent: "Nice to meet you!"
    3. ...
    '''
    """
    
    facts = self.get_facts(user_id)
    recent_convos = self.get_conversation_history(user_id, limit=3)
    
    context = self._format_memory_context(facts, recent_convos)
    return context
```

---

### 🔨 Action Builder

**Fichier**: `backend/actions/action_builder.py`

**ActionJSON Format:**

```json
{
  "action_id": "act_7716359599d7",
  "user_id": "web_user_001",
  "intent": "control_iot",
  "entities": {
    "device_type": "door",
    "action": "close",
    "location": "living_room"
  },
  "original_text": "Close the door in the living room",
  "language": "en",
  "timestamp": "2026-02-14T15:47:15Z",
  "request_id": "req_c7d23feac209",
  "confirmed": false,
  "state": "DRAFT"
}
```

**Builder Pipeline:**

```python
async def build_action(
    self, 
    llm_analysis: Dict, 
    user_id: str, 
    original_text: str,
    language: str
) -> Dict:
    """
    1. Generate unique action_id
    2. Map LLM entities to ActionJSON format
    3. Add metadata (timestamp, request_id)
    4. Validate required fields
    5. Return ActionJSON
    """
    
    action_id = f"act_{uuid.uuid4().hex[:12]}"
    
    action_json = {
        "action_id": action_id,
        "user_id": user_id,
        "intent": llm_analysis["primary_intent"],
        "entities": self._map_entities(llm_analysis["entities"]),
        "original_text": original_text,
        "language": language,
        "timestamp": datetime.now(UTC).isoformat(),
        "confirmed": False,
        "state": "DRAFT"
    }
    
    self._validate_action_json(action_json)
    
    return action_json
```

---

### 🔐 Security Manager

**Fichier**: `backend/actions/security_manager.py`

**HMAC Signature:**

```python
def sign_action(self, action_json: Dict) -> Dict:
    """
    Signe l'ActionJSON avec HMAC-SHA256
    
    Returns:
    {
        ...action_json,
        "signature": "abc123...",
        "signed_at": "2026-02-14T15:47:15Z"
    }
    """
    
    payload = json.dumps(action_json, sort_keys=True)
    signature = hmac.new(
        self.secret_key.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    signed_action = {
        **action_json,
        "signature": signature,
        "signed_at": datetime.now(UTC).isoformat()
    }
    
    return signed_action

def verify_signature(self, signed_action: Dict) -> bool:
    """Vérifie la signature HMAC"""
    
    received_sig = signed_action.pop("signature")
    payload = json.dumps(signed_action, sort_keys=True)
    
    expected_sig = hmac.new(
        self.secret_key.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(received_sig, expected_sig)
```

---

## 🎨 Frontend Architecture

### 📂 Structure des Fichiers

```
agent-ui/
├── public/
│   └── vite.svg
│
├── src/
│   ├── main.tsx              # Entry point
│   ├── App.tsx               # Root component
│   ├── App.css               # Global styles
│   │
│   ├── components/           # Composants réutilisables
│   │   ├── MicButton/
│   │   │   ├── MicButton.tsx
│   │   │   └── MicButton.css
│   │   ├── Avatar/
│   │   ├── Waveform/
│   │   ├── Toast/
│   │   ├── EntityBadge/
│   │   ├── ConversationHistory/
│   │   ├── MemoryPanel/
│   │   ├── ActionPanel/
│   │   └── SettingsPanel/
│   │
│   ├── screens/              # Pages principales
│   │   ├── Welcome/
│   │   ├── Login/
│   │   └── AgentScreen/
│   │
│   ├── services/             # Services API
│   │   ├── api.ts            # Backend API calls
│   │   └── audio.ts          # Audio recording/playback
│   │
│   ├── store/                # State management
│   │   └── agentStore.ts     # Zustand store
│   │
│   ├── types/                # TypeScript types
│   │   └── index.ts
│   │
│   └── assets/               # Assets statiques
│       └── animations/       # Lottie JSON files
│           ├── idle.json
│           ├── listening.json
│           ├── thinking.json
│           └── speaking.json
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

### 🔄 State Management - Zustand

**Fichier**: `agent-ui/src/store/agentStore.ts`

```typescript
interface AgentStore {
  // State
  state: AgentState;
  transcription: string;
  response: string;
  metadata: ConversationMetadata | null;
  messages: Message[];
  toasts: ToastMessage[];
  
  // Actions
  setState: (state: AgentState) => void;
  setTranscription: (text: string) => void;
  setResponse: (text: string, metadata?: ConversationMetadata) => void;
  addMessage: (sender: 'user' | 'agent', text: string, metadata?: any) => void;
  clearMessages: () => void;
  showToast: (message: string, type: ToastType) => void;
  hideToast: (id: string) => void;
}

export const useAgentStore = create<AgentStore>((set) => ({
  // Initial state
  state: 'idle',
  transcription: '',
  response: '',
  metadata: null,
  messages: [],
  toasts: [],
  
  // Actions
  setState: (state) => set({ state }),
  setTranscription: (text) => set({ transcription: text }),
  setResponse: (text, metadata) => set({ 
    response: text, 
    metadata: metadata || null 
  }),
  addMessage: (sender, text, metadata) => set((state) => ({
    messages: [
      ...state.messages,
      {
        id: `msg_${Date.now()}`,
        sender,
        text,
        timestamp: new Date(),
        ...metadata
      }
    ]
  })),
  // ... autres actions
}));
```

**Usage dans composants:**

```typescript
function MicButton() {
  const { state, setState, addMessage } = useAgentStore();
  
  const handleRecording = async () => {
    setState('listening');
    // ... recording logic
    setState('thinking');
    // ... API call
    addMessage('user', transcription);
    addMessage('agent', response);
    setState('idle');
  };
}
```

---

### 🎯 Flux de Communication Frontend→Backend

```
User clicks MicButton
    ↓
MicButton.tsx: Start recording (MediaRecorder)
    ↓
User releases button
    ↓
Stop recording → Blob (audio/webm)
    ↓
audioService.ts: Convert Blob to base64
    ↓
apiService.ts: POST /command/audio
    ↓
Backend processes (STT → LLM → TTS)
    ↓
Response: { transcription, response, audio, metadata }
    ↓
MicButton.tsx: Update store
    ↓
AgentScreen.tsx: Re-render with new data
    ↓
audioService.ts: Play response audio
    ↓
Back to idle state
```

---

## 📊 Performance & Scalabilité

### Backend Performance

**Temps de traitement moyen:**

| Étape | Temps moyen | Optimisations |
|-------|-------------|---------------|
| STT (Whisper base) | 500-800ms | Utiliser `tiny` pour CPU faibles |
| Classification | 50-100ms | Simple keyword matching |
| LLM (Ollama) | 800-1500ms | Utiliser GPU si disponible |
| Memory extraction | 200-400ms | Cache fréquentes queries |
| TTS (Piper) | 300-600ms | Pre-generate common phrases |
| **Total** | **1.8-3.4s** | Acceptable pour conversation |

**Optimisations CPU:**

```python
# config.py

# CPU faible
WHISPER_MODEL_SIZE = "tiny"
WHISPER_COMPUTE_TYPE = "int8"
LLM_MAX_TOKENS = 200

# CPU moyen
WHISPER_MODEL_SIZE = "base"
WHISPER_COMPUTE_TYPE = "int8"
LLM_MAX_TOKENS = 500

# GPU disponible
WHISPER_MODEL_SIZE = "medium"
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE_TYPE = "float16"
LLM_MAX_TOKENS = 1000
```

### Frontend Performance

**Bundle size:**

```
dist/
├── index.html              1 KB
├── assets/
│   ├── index-abc123.js    450 KB (React + deps)
│   ├── index-def456.css   25 KB
│   └── animations/        ~2 MB (Lottie files)
```

**Optimisations:**

```typescript
// Lazy loading animations
const LottieAnimation = lazy(() => import('lottie-react'));

// Memoize expensive components
const MemoizedConversationHistory = memo(ConversationHistory);

// Debounce API calls
const debouncedFetchActions = debounce(fetchActions, 1000);
```

---

## 🔄 Patterns de Conception

### Backend

- **Dependency Injection**: Services injectés dans AgentCore
- **Strategy Pattern**: Interface abstraite pour STT/LLM/TTS
- **State Machine**: StateManager avec transitions validées
- **Observer Pattern**: MQTT pour notifications IoT
- **Repository Pattern**: MemoryService pour accès données

### Frontend

- **Flux/Unidirectional Data Flow**: Zustand store
- **Presentational/Container**: Composants séparés
- **Composition**: Composants atomiques réutilisables
- **Custom Hooks**: useAudio, useKeyPress, etc.

---

**Version**: 1.0.0  
**Dernière mise à jour**: 14 février 2026
