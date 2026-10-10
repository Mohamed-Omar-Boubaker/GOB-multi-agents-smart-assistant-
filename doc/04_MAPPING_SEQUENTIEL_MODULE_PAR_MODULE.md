# 🎯 Mapping Séquentiel - Module par Module
## Approche : Terminer un module avant de passer au suivant

**Version :** 1.0 - Approche Séquentielle  
**Date :** 20 janvier 2026  
**Équipe :** 3 personnes (Montassar, Amine, Omar)  
**Durée estimée :** 12-14 semaines  

---

## 📑 Table des Matières

1. [Principe de l'approche séquentielle](#1-principe-de-lapproche-séquentielle)
2. [Phase 1 - MODULE BACKEND PYTHON (Semaines 1-6)](#2-phase-1---module-backend-python-semaines-1-6)
3. [Phase 2 - MODULE N8N ORCHESTRATION (Semaines 7-9)](#3-phase-2---module-n8n-orchestration-semaines-7-9)
4. [Phase 3 - MODULE ESP32 EMBARQUÉ (Semaines 10-12)](#4-phase-3---module-esp32-embarqué-semaines-10-12)
5. [Phase 4 - INTÉGRATION GLOBALE (Semaines 13-14)](#5-phase-4---intégration-globale-semaines-13-14)
6. [Phase 5 - DOCUMENTATION & SOUTENANCE (Semaines 15-16)](#6-phase-5---documentation--soutenance-semaines-15-16)

---

## 1. Principe de l'approche séquentielle

### 1.1 Concept

**🎯 Objectif :** Toute l'équipe se concentre sur **un seul module à la fois** jusqu'à ce qu'il soit **100% complet et testé** avant de passer au suivant.

```
┌─────────────────────────────────────────────────────────────┐
│                    APPROCHE SÉQUENTIELLE                     │
└─────────────────────────────────────────────────────────────┘

Phase 1 (S1-S6): 🔴 BACKEND PYTHON
├── Montassar: Core + AI/LLM (Lead)
├── Amine: Intégrations + Validators
└── Omar: Tests + MQTT Client
   ↓ Backend 100% terminé ✅

Phase 2 (S7-S9): 🟠 N8N ORCHESTRATION
├── Amine: Workflows (Lead)
├── Montassar: Intégration Backend ↔ n8n
└── Omar: Tests + MQTT Setup
   ↓ n8n 100% terminé ✅

Phase 3 (S10-S12): 🟢 ESP32 EMBARQUÉ
├── Omar: Code ESP32 (Lead)
├── Amine: MQTT Broker + Tests
└── Montassar: Audio + Intégration
   ↓ ESP32 100% terminé ✅

Phase 4 (S13-S14): 🔵 INTÉGRATION GLOBALE
├── TOUS: Tests end-to-end
└── TOUS: Corrections finales
   ↓ Système complet ✅

Phase 5 (S15-S16): 📚 DOCUMENTATION & SOUTENANCE
└── TOUS: Documentation + Présentation
```

### 1.2 Avantages de cette approche

✅ **Concentration maximale** : Toute l'équipe sur un seul objectif  
✅ **Qualité garantie** : Module testé à 100% avant de passer au suivant  
✅ **Pas de blocages** : Pas d'attente entre modules  
✅ **Apprentissage partagé** : Tout le monde comprend chaque module  
✅ **Flexibilité** : Possibilité d'adapter selon les compétences  

### 1.3 Rôles par phase

| Phase | Lead | Support 1 | Support 2 |
|-------|------|-----------|-----------|
| **Backend Python** | Montassar | Amine | Omar |
| **n8n Orchestration** | Amine | Montassar | Omar |
| **ESP32 Embarqué** | Omar | Amine | Montassar |
| **Intégration** | Montassar | Amine | Omar |

**Principe :** Le **Lead** a la responsabilité principale, les **Supports** aident selon leurs compétences.

---

## 2. Phase 1 - MODULE BACKEND PYTHON (Semaines 1-6)

### 2.1 Vue d'ensemble de la phase

**🎯 Objectif :** Développer le Backend Python **complet et fonctionnel** avec tous ses composants.

**📦 Livrables attendus :**
- ✅ API FastAPI complète (4 routes)
- ✅ Agent Core orchestrateur
- ✅ Modules AI (Classifier, STT, TTS, LLM)
- ✅ State Manager + Security Manager
- ✅ Action Builder + Confirmation Handler
- ✅ Clients n8n et MQTT (mockés)
- ✅ Validators complets
- ✅ Tests unitaires (couverture 80%+)
- ✅ Documentation API

**👥 Distribution de l'équipe :**

| Membre | Charge | Rôle Principal | Focus |
|--------|--------|----------------|-------|
| **MONTASSAR** | 60% | Lead Backend + AI | Core + Classifier + LLM + STT/TTS |
| **AMINE** | 25% | Intégrations + Validation | Clients + Validators + Tests |
| **OMAR** | 15% | Tests + MQTT | Tests unitaires + MQTT mockup |

**📅 Durée :** 6 semaines (228h total)

---

### 2.2 Semaine 1 - Setup & Architecture (TOUS)

**Objectif :** Environnement prêt + Structure projet + Premiers modules

#### 🔧 Tâches communes (Ensemble, jour 1-2)

**T1.0 - Setup environnement (TOUS - 6h)**
```bash
# Jour 1 - Tous ensemble
1. Créer structure projet
   backend/
   ├── agent/
   ├── actions/
   ├── ai/
   ├── classifier/
   ├── integrations/
   ├── utils/
   └── tests/

2. Setup Git
   git init
   git remote add origin ...
   
3. Configuration Python
   python -m venv venv
   pip install -r requirements.txt
   
4. Tests installation
   pytest --version
   python -c "import fastapi; print('OK')"
```

**Responsabilité :** Montassar dirige, Amine et Omar suivent et valident sur leurs machines.

---

#### 👤 Montassar - Semaine 1 (38h)

**T1.1 - Configuration globale (config.py) - 4h**
```python
# Fichier: backend/config.py
# Montassar crée TOUTE la configuration

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Serveur
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # LLM
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    HMAC_SECRET: str = "your-hmac-secret"
    
    # n8n
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/action"
    
    # MQTT
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_DEVICE_ID: str = "esp32_001"
    
    # Audio
    STT_MODEL: str = "base"  # whisper
    TTS_LANGUAGE: str = "fr"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Livrable :** `config.py` + `.env.example`  
**Test :** `python -c "from backend.config import settings; print(settings.API_PORT)"`

---

**T1.2 - Logger centralisé (logger.py) - 6h**
```python
# Fichier: backend/agent/logger.py
# Montassar crée le système de logging complet

import logging
import json
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Formatter pour logs JSON structurés"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Ajouter extra fields si présents
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'action_id'):
            log_data['action_id'] = record.action_id
            
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(name: str, log_file: str = None):
    """Configure et retourne un logger"""
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Console handler (pour dev)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (JSON structuré)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

# Logger global
app_logger = setup_logger("pcd_agent", "logs/app.log")
```

**Livrable :** `logger.py` fonctionnel  
**Test :** Script de test `test_logger.py`

---

**T1.3 - API FastAPI squelette (main.py) - 8h**
```python
# Fichier: backend/main.py
# Montassar crée l'API complète avec routes mockées

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
from datetime import datetime

from backend.config import settings
from backend.agent.logger import app_logger

app = FastAPI(
    title="PCD Agent API",
    description="API Agent Intelligent Embarqué",
    version="1.0.0"
)

# ============= MODELS =============

class CommandTextRequest(BaseModel):
    user_id: str
    text: str
    context: dict = {}

class CommandAudioRequest(BaseModel):
    user_id: str
    audio_data: str  # base64
    audio_format: str = "wav"

class CallbackN8nRequest(BaseModel):
    action_id: str
    status: str
    result_data: dict = {}

class CommandResponse(BaseModel):
    request_id: str
    status: str
    classification: str = None
    response: dict = {}

# ============= ROUTES =============

@app.post("/command/text", response_model=CommandResponse)
async def command_text(request: CommandTextRequest):
    """
    Commande texte utilisateur
    
    Flow:
    1. Classifier → Conversation ou Action
    2. Si Conversation → LLM → Réponse
    3. Si Action → Build ActionJSON → Attente confirmation
    """
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    app_logger.info(
        f"Received text command: {request.text}",
        extra={"request_id": request_id, "user_id": request.user_id}
    )
    
    # TODO: Appeler classifier (Semaine 2)
    # TODO: Router vers conversation ou action (Semaine 2)
    
    # Mock pour l'instant
    return CommandResponse(
        request_id=request_id,
        status="processing",
        classification="unknown",
        response={"message": "Backend mockup - à implémenter"}
    )

@app.post("/command/audio", response_model=CommandResponse)
async def command_audio(request: CommandAudioRequest):
    """
    Commande audio utilisateur
    
    Flow:
    1. STT → Texte
    2. Classifier → Conversation ou Action
    3. Suite identique à /command/text
    """
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    app_logger.info(
        f"Received audio command",
        extra={"request_id": request_id, "user_id": request.user_id}
    )
    
    # TODO: Appeler STT (Semaine 3)
    # TODO: Puis flow identique à /command/text
    
    return CommandResponse(
        request_id=request_id,
        status="processing",
        classification="unknown",
        response={"message": "Audio processing - à implémenter"}
    )

@app.post("/callback/n8n")
async def callback_n8n(request: CallbackN8nRequest):
    """
    Callback depuis n8n après exécution action
    
    Flow:
    1. Update state de l'action
    2. Log résultat
    3. Notifier utilisateur (TTS si audio)
    """
    app_logger.info(
        f"Received n8n callback for action {request.action_id}",
        extra={"action_id": request.action_id}
    )
    
    # TODO: Update state manager (Semaine 2)
    # TODO: Notifier utilisateur (Semaine 3)
    
    return {"status": "acknowledged"}

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/status/{action_id}")
async def get_status(action_id: str):
    """
    Récupérer statut d'une action
    """
    # TODO: Query state manager (Semaine 2)
    
    return {
        "action_id": action_id,
        "state": "unknown",
        "message": "State manager à implémenter"
    }

# ============= STARTUP =============

@app.on_event("startup")
async def startup_event():
    app_logger.info("🚀 PCD Agent API Starting...")
    app_logger.info(f"📍 Host: {settings.API_HOST}:{settings.API_PORT}")

@app.on_event("shutdown")
async def shutdown_event():
    app_logger.info("🛑 PCD Agent API Shutting down...")

# ============= ERROR HANDLERS =============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    app_logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
```

**Livrable :** API fonctionnelle (mockée)  
**Test :** 
```bash
uvicorn backend.main:app --reload
curl http://localhost:8000/health
curl -X POST http://localhost:8000/command/text \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "text": "Bonjour"}'
```

---

**T1.4 - Requirements complet (requirements.txt) - 2h**
```txt
# Fichier: requirements.txt
# Montassar liste TOUTES les dépendances

# API
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
python-multipart==0.0.6

# AI/LLM
openai==1.10.0
openai-whisper==20231117
gtts==2.5.0
torch==2.1.2
torchaudio==2.1.2

# Communication
paho-mqtt==1.6.1
requests==2.31.0

# Security
cryptography==42.0.0
python-jose[cryptography]==3.3.0
passlib==1.7.4

# Utils
python-dotenv==1.0.0
pydantic-settings==2.1.0

# Audio processing
pydub==0.25.1
numpy==1.26.3

# Logging
python-json-logger==2.0.7

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0

# Dev
black==24.1.1
flake8==7.0.0
mypy==1.8.0
```

**Livrable :** `requirements.txt` complet  
**Test :** `pip install -r requirements.txt`

---

**T1.5 - State Manager (state_manager.py) - 10h**
```python
# Fichier: backend/agent/state_manager.py
# Montassar crée le gestionnaire d'états complet

from enum import Enum
from typing import Dict, Optional
from datetime import datetime
import uuid

from backend.agent.logger import app_logger

class ActionState(Enum):
    """États possibles d'une action"""
    IDLE = "IDLE"
    DRAFT = "DRAFT"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

class StateManager:
    """
    Gestionnaire d'états des actions
    
    Responsabilités:
    - Créer actions (état DRAFT)
    - Valider transitions d'états
    - Stocker ActionJSON
    - Récupérer état action
    """
    
    def __init__(self):
        self.actions: Dict[str, dict] = {}
        app_logger.info("StateManager initialized")
    
    def create_action(self, action_json: dict) -> str:
        """
        Créer nouvelle action état DRAFT
        
        Args:
            action_json: ActionJSON complet
            
        Returns:
            action_id généré
        """
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        
        action_data = {
            "action_id": action_id,
            "state": ActionState.DRAFT.value,
            "action_json": action_json,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "history": [
                {
                    "state": ActionState.DRAFT.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        
        self.actions[action_id] = action_data
        
        app_logger.info(
            f"Action created: {action_id}",
            extra={"action_id": action_id}
        )
        
        return action_id
    
    def update_state(
        self, 
        action_id: str, 
        new_state: ActionState,
        details: dict = None
    ) -> bool:
        """
        Mettre à jour état d'une action
        
        Valide la transition avant de l'appliquer
        """
        if action_id not in self.actions:
            app_logger.error(f"Action not found: {action_id}")
            return False
        
        action = self.actions[action_id]
        current_state = ActionState(action["state"])
        
        # Valider transition
        if not self._is_valid_transition(current_state, new_state):
            app_logger.error(
                f"Invalid transition: {current_state.value} → {new_state.value}",
                extra={"action_id": action_id}
            )
            return False
        
        # Appliquer transition
        action["state"] = new_state.value
        action["updated_at"] = datetime.utcnow().isoformat()
        
        # Ajouter à l'historique
        history_entry = {
            "state": new_state.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        if details:
            history_entry["details"] = details
        
        action["history"].append(history_entry)
        
        app_logger.info(
            f"State updated: {current_state.value} → {new_state.value}",
            extra={"action_id": action_id}
        )
        
        return True
    
    def get_action(self, action_id: str) -> Optional[dict]:
        """Récupérer action par ID"""
        return self.actions.get(action_id)
    
    def get_action_state(self, action_id: str) -> Optional[str]:
        """Récupérer état d'une action"""
        action = self.get_action(action_id)
        return action["state"] if action else None
    
    def _is_valid_transition(
        self, 
        current: ActionState, 
        target: ActionState
    ) -> bool:
        """
        Valider si transition est autorisée
        
        Transitions valides:
        DRAFT → PENDING_CONFIRMATION
        PENDING_CONFIRMATION → CONFIRMED | CANCELED
        CONFIRMED → EXECUTING
        EXECUTING → COMPLETED | FAILED
        """
        valid_transitions = {
            ActionState.DRAFT: [ActionState.PENDING_CONFIRMATION],
            ActionState.PENDING_CONFIRMATION: [
                ActionState.CONFIRMED,
                ActionState.CANCELED
            ],
            ActionState.CONFIRMED: [ActionState.EXECUTING],
            ActionState.EXECUTING: [
                ActionState.COMPLETED,
                ActionState.FAILED
            ],
            # États finaux - pas de transition
            ActionState.COMPLETED: [],
            ActionState.FAILED: [],
            ActionState.CANCELED: []
        }
        
        return target in valid_transitions.get(current, [])
    
    def get_all_actions(self, user_id: str = None) -> list:
        """Récupérer toutes les actions (optionnel: filtrer par user)"""
        actions = list(self.actions.values())
        
        if user_id:
            actions = [
                a for a in actions 
                if a["action_json"].get("user_id") == user_id
            ]
        
        return actions

# Instance globale
state_manager = StateManager()
```

**Livrable :** `state_manager.py` complet  
**Test :** Tests unitaires dans `tests/test_state_manager.py`

---

**Résumé Montassar Semaine 1:**
- T1.1: config.py (4h)
- T1.2: logger.py (6h)
- T1.3: main.py (8h)
- T1.4: requirements.txt (2h)
- T1.5: state_manager.py (10h)
- T1.0: Setup commun (6h partagé = 2h)
- Meetings (6h)
**Total Montassar S1: 38h**

---

#### 👤 Amine - Semaine 1 (38h)

**Rôle Amine :** Créer les modules d'intégration et validation

**T1.6 - Security Manager (security_manager.py) - 12h**
```python
# Fichier: backend/agent/security_manager.py
# Amine crée la sécurité complète

import hmac
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from backend.config import settings
from backend.agent.logger import app_logger

class SecurityManager:
    """
    Gestionnaire de sécurité
    
    Responsabilités:
    - Génération signatures HMAC
    - Vérification signatures
    - Gestion tokens JWT
    - Validation permissions
    """
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.hmac_secret = settings.HMAC_SECRET.encode()
        self.algorithm = "HS256"
        app_logger.info("SecurityManager initialized")
    
    def generate_signature(self, action_json: dict) -> str:
        """
        Générer signature HMAC-SHA256 pour ActionJSON
        
        Utilisé pour signer les actions CONFIRMED
        avant envoi vers n8n
        """
        # Sérialiser JSON de manière déterministe
        json_string = json.dumps(action_json, sort_keys=True)
        
        # Générer HMAC
        signature = hmac.new(
            self.hmac_secret,
            json_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        app_logger.debug(f"Generated signature for action {action_json.get('action_id')}")
        
        return signature
    
    def verify_signature(self, action_json: dict, signature: str) -> bool:
        """
        Vérifier signature HMAC
        
        Returns:
            True si signature valide
        """
        expected_signature = self.generate_signature(action_json)
        
        # Comparaison sécurisée (protection contre timing attacks)
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if not is_valid:
            app_logger.warning(
                f"Invalid signature for action {action_json.get('action_id')}"
            )
        
        return is_valid
    
    def create_token(self, user_id: str, expires_delta: timedelta = None) -> str:
        """
        Créer token JWT pour utilisateur
        
        Usage: Authentification API (optionnel)
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        app_logger.info(f"JWT token created for user {user_id}")
        
        return token
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Vérifier et décoder token JWT
        
        Returns:
            Payload si token valide, None sinon
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            app_logger.error(f"JWT verification failed: {str(e)}")
            return None
    
    def check_permissions(self, user_id: str, action: dict) -> bool:
        """
        Vérifier permissions utilisateur pour action
        
        Pour l'instant: tous les users autorisés
        Future: implémenter système de rôles
        """
        # TODO: Implémenter logique permissions
        # Pour MVP: autoriser tout le monde
        return True

# Instance globale
security_manager = SecurityManager()
```

**Livrable :** `security_manager.py` fonctionnel  
**Test :** Tests unitaires + script de démo

---

**T1.7 - Validators JSON (validators.py) - 14h**
```python
# Fichier: backend/utils/validators.py
# Amine crée TOUS les validators pour les flux JSON

from typing import Dict, Any, Optional
from datetime import datetime

from backend.agent.logger import app_logger

class ValidationError(Exception):
    """Exception levée lors d'erreur validation"""
    pass

class JSONValidator:
    """
    Validators pour tous les flux JSON
    
    Référence: Fichier 02 - Spécifications JSON
    """
    
    @staticmethod
    def validate_classification_input(data: dict) -> bool:
        """
        Valider Flux 0 INPUT
        Section 2.2 du Fichier 02
        """
        required_fields = ["request_id", "raw_text", "source", "user_id"]
        
        # Vérifier champs requis
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Vérifier types
        if not isinstance(data["raw_text"], str):
            raise ValidationError("raw_text must be string")
        
        if data["source"] not in ["voice", "text"]:
            raise ValidationError("source must be 'voice' or 'text'")
        
        # Vérifier longueur texte
        if len(data["raw_text"]) > 500:
            raise ValidationError("raw_text too long (max 500 chars)")
        
        app_logger.debug(f"Classification input validated: {data['request_id']}")
        return True
    
    @staticmethod
    def validate_classification_output(data: dict) -> bool:
        """
        Valider Flux 0 OUTPUT
        Section 2.3 du Fichier 02
        """
        required_fields = ["request_id", "classification", "confidence"]
        
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Vérifier classification
        if data["classification"] not in ["conversation", "action"]:
            raise ValidationError(
                "classification must be 'conversation' or 'action'"
            )
        
        # Vérifier confidence
        if not isinstance(data["confidence"], (int, float)):
            raise ValidationError("confidence must be numeric")
        
        if not 0 <= data["confidence"] <= 1:
            raise ValidationError("confidence must be between 0 and 1")
        
        return True
    
    @staticmethod
    def validate_action_json(data: dict) -> bool:
        """
        Valider ActionJSON complet
        Section 6.2 du Fichier 02
        
        Structure:
        {
          "action_id": "...",
          "user_id": "...",
          "intent": "...",
          "confirmed": bool,
          "state": "...",
          "payload": {...},
          "context": {...},
          "security": {...},
          "timestamps": {...}
        }
        """
        required_fields = [
            "action_id", "user_id", "intent", 
            "confirmed", "state", "payload"
        ]
        
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Vérifier intent valide
        valid_intents = [
            "control_iot", "send_email", 
            "set_reminder", "web_search"
        ]
        if data["intent"] not in valid_intents:
            raise ValidationError(f"Invalid intent: {data['intent']}")
        
        # Vérifier confirmed
        if not isinstance(data["confirmed"], bool):
            raise ValidationError("confirmed must be boolean")
        
        # Vérifier state
        valid_states = [
            "DRAFT", "PENDING_CONFIRMATION", "CONFIRMED",
            "EXECUTING", "COMPLETED", "FAILED", "CANCELED"
        ]
        if data["state"] not in valid_states:
            raise ValidationError(f"Invalid state: {data['state']}")
        
        # Valider payload selon intent
        if not isinstance(data["payload"], dict):
            raise ValidationError("payload must be dict")
        
        # Validation spécifique par intent
        if data["intent"] == "control_iot":
            JSONValidator._validate_control_iot_payload(data["payload"])
        elif data["intent"] == "send_email":
            JSONValidator._validate_send_email_payload(data["payload"])
        # ... autres intents
        
        return True
    
    @staticmethod
    def _validate_control_iot_payload(payload: dict):
        """Valider payload control_iot"""
        required = ["device_id", "action", "location"]
        
        for field in required:
            if field not in payload:
                raise ValidationError(f"control_iot: missing {field}")
        
        valid_actions = ["turn_on", "turn_off", "toggle", "set_value"]
        if payload["action"] not in valid_actions:
            raise ValidationError(f"Invalid iot action: {payload['action']}")
    
    @staticmethod
    def _validate_send_email_payload(payload: dict):
        """Valider payload send_email"""
        if "recipient_email" not in payload and "recipient" not in payload:
            raise ValidationError("send_email: need recipient_email or recipient")
        
        if "subject" not in payload:
            raise ValidationError("send_email: missing subject")
        
        if "body" not in payload:
            raise ValidationError("send_email: missing body")
    
    @staticmethod
    def validate_confirmation_request(data: dict) -> bool:
        """
        Valider demande confirmation
        Section 7.2 du Fichier 02
        """
        required_fields = ["action_id", "confirmation_text", "action_summary"]
        
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        return True
    
    @staticmethod
    def validate_confirmation_response(data: dict) -> bool:
        """
        Valider réponse confirmation
        Section 7.3 du Fichier 02
        """
        required_fields = ["action_id", "user_response", "parsed_response"]
        
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Vérifier parsed_response
        parsed = data["parsed_response"]
        if parsed["intent"] not in ["confirm", "cancel", "modify"]:
            raise ValidationError(f"Invalid intent: {parsed['intent']}")
        
        return True
    
    @staticmethod
    def validate_n8n_callback(data: dict) -> bool:
        """
        Valider callback n8n
        Section 11.2 du Fichier 02
        """
        required_fields = ["action_id", "status", "result_data"]
        
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Vérifier status
        valid_statuses = ["SUCCESS", "FAILED", "TIMEOUT", "PARTIAL"]
        if data["status"] not in valid_statuses:
            raise ValidationError(f"Invalid status: {data['status']}")
        
        return True

# Instance globale
json_validator = JSONValidator()
```

**Livrable :** `validators.py` complet avec 8+ validators  
**Test :** Suite de tests exhaustive

---

**T1.8 - Tests unitaires Setup - 12h**
```python
# Fichier: tests/test_state_manager.py
# Amine crée les premiers tests

import pytest
from backend.agent.state_manager import StateManager, ActionState

def test_create_action():
    """Test création action"""
    sm = StateManager()
    
    action_json = {
        "user_id": "user1",
        "intent": "control_iot",
        "payload": {"device_id": "lamp1"}
    }
    
    action_id = sm.create_action(action_json)
    
    assert action_id.startswith("act_")
    assert sm.get_action_state(action_id) == ActionState.DRAFT.value

def test_valid_transition():
    """Test transition valide"""
    sm = StateManager()
    
    action_json = {"user_id": "user1"}
    action_id = sm.create_action(action_json)
    
    # DRAFT → PENDING_CONFIRMATION (valide)
    result = sm.update_state(action_id, ActionState.PENDING_CONFIRMATION)
    assert result is True
    assert sm.get_action_state(action_id) == ActionState.PENDING_CONFIRMATION.value

def test_invalid_transition():
    """Test transition invalide"""
    sm = StateManager()
    
    action_json = {"user_id": "user1"}
    action_id = sm.create_action(action_json)
    
    # DRAFT → COMPLETED (invalide)
    result = sm.update_state(action_id, ActionState.COMPLETED)
    assert result is False
    assert sm.get_action_state(action_id) == ActionState.DRAFT.value

# ... 20+ tests au total
```

**Plus de tests :**
- `tests/test_security_manager.py` (10 tests)
- `tests/test_validators.py` (30+ tests)
- `tests/test_api.py` (tests des routes mockées)

**Livrable :** Suite tests complète (couverture 80%+)

---

**Résumé Amine Semaine 1:**
- T1.6: security_manager.py (12h)
- T1.7: validators.py (14h)
- T1.8: Tests unitaires (12h)
**Total Amine S1: 38h**

---

#### 👤 Omar - Semaine 1 (38h)

**Rôle Omar :** Créer MQTT client mockup + aide tests

**T1.9 - MQTT Client (mqtt_client.py) - 16h**
```python
# Fichier: backend/integrations/mqtt_client.py
# Omar crée le client MQTT complet

import paho.mqtt.client as mqtt
import json
import base64
from typing import Callable, Optional

from backend.config import settings
from backend.agent.logger import app_logger

class MQTTClient:
    """
    Client MQTT pour communication avec ESP32
    
    Topics:
    - esp32/audio/upload/{device_id} (SUB) - Audio depuis ESP32
    - esp32/audio/response/{device_id} (PUB) - Audio vers ESP32
    - esp32/command/{device_id} (PUB) - Commandes IoT
    - esp32/status/{device_id} (SUB) - Statuts ESP32
    """
    
    def __init__(
        self, 
        broker: str = None, 
        port: int = None,
        device_id: str = None
    ):
        self.broker = broker or settings.MQTT_BROKER
        self.port = port or settings.MQTT_PORT
        self.device_id = device_id or settings.MQTT_DEVICE_ID
        
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        # Callbacks externes
        self.audio_upload_callback: Optional[Callable] = None
        self.status_callback: Optional[Callable] = None
        
        app_logger.info(
            f"MQTT Client initialized: {self.broker}:{self.port}"
        )
    
    def connect(self):
        """Connexion au broker MQTT"""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            app_logger.info("MQTT Client connected")
        except Exception as e:
            app_logger.error(f"MQTT connection failed: {str(e)}")
            raise
    
    def disconnect(self):
        """Déconnexion"""
        self.client.loop_stop()
        self.client.disconnect()
        app_logger.info("MQTT Client disconnected")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback connexion"""
        if rc == 0:
            app_logger.info("MQTT Connected successfully")
            
            # Souscrire aux topics
            audio_topic = f"esp32/audio/upload/{self.device_id}"
            status_topic = f"esp32/status/{self.device_id}"
            
            self.client.subscribe(audio_topic)
            self.client.subscribe(status_topic)
            
            app_logger.info(f"Subscribed to {audio_topic}")
            app_logger.info(f"Subscribed to {status_topic}")
        else:
            app_logger.error(f"MQTT Connection failed with code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback réception message"""
        topic = msg.topic
        
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            if "audio/upload" in topic:
                self._handle_audio_upload(payload)
            elif "status" in topic:
                self._handle_status(payload)
            else:
                app_logger.warning(f"Unknown topic: {topic}")
                
        except Exception as e:
            app_logger.error(f"Error processing MQTT message: {str(e)}")
    
    def _handle_audio_upload(self, payload: dict):
        """
        Gérer upload audio depuis ESP32
        
        Référence: Section 12.2 Fichier 02
        """
        app_logger.info("Received audio upload from ESP32")
        
        if self.audio_upload_callback:
            self.audio_upload_callback(payload)
        else:
            app_logger.warning("No audio upload callback registered")
    
    def _handle_status(self, payload: dict):
        """
        Gérer status depuis ESP32
        
        Référence: Section 10.2 Fichier 02
        """
        app_logger.info(f"Received status from ESP32: {payload.get('status')}")
        
        if self.status_callback:
            self.status_callback(payload)
    
    def send_audio_response(
        self, 
        audio_data: str, 
        config: dict = None
    ):
        """
        Envoyer réponse audio vers ESP32
        
        Référence: Section 13.2 Fichier 02
        
        Args:
            audio_data: Audio encodé base64
            config: Configuration playback
        """
        topic = f"esp32/audio/response/{self.device_id}"
        
        message = {
            "audio_data": audio_data,
            "audio_format": config.get("format", "mp3") if config else "mp3",
            "audio_metadata": config.get("metadata", {}) if config else {}
        }
        
        payload = json.dumps(message)
        self.client.publish(topic, payload, qos=1)
        
        app_logger.info(f"Audio response sent to ESP32 (size: {len(audio_data)} bytes)")
    
    def send_command(self, command: dict):
        """
        Envoyer commande IoT vers ESP32
        
        Référence: Section 9.2 Fichier 02
        
        Note: En pratique, c'est n8n qui envoie les commandes.
        Cette méthode est pour tests directs.
        """
        topic = f"esp32/command/{self.device_id}"
        
        payload = json.dumps(command)
        self.client.publish(topic, payload, qos=1)
        
        app_logger.info(
            f"Command sent to ESP32: {command.get('action')}"
        )
    
    def register_audio_callback(self, callback: Callable):
        """Enregistrer callback pour audio uploads"""
        self.audio_upload_callback = callback
        app_logger.info("Audio upload callback registered")
    
    def register_status_callback(self, callback: Callable):
        """Enregistrer callback pour statuts"""
        self.status_callback = callback
        app_logger.info("Status callback registered")

# Instance globale
mqtt_client = MQTTClient()
```

**Livrable :** `mqtt_client.py` fonctionnel  
**Test :** Script de test avec broker MQTT local

---

**T1.10 - Tests intégration + documentation - 22h**

Omar aide à :
1. **Tests intégration** (12h)
   - Tests API avec requêtes réelles
   - Tests State Manager + Security ensemble
   - Tests MQTT (avec broker local)

2. **Documentation** (10h)
   - README.md initial
   - Guide installation
   - Documentation API (Swagger auto-générée)
   - Scripts de démo

```markdown
# Fichier: README.md
# Omar documente setup complet

# PCD - Agent Intelligent Embarqué

## Installation

### Prérequis
- Python 3.10+
- Broker MQTT (Mosquitto)
- OpenAI API Key

### Setup
```bash
# Cloner repo
git clone ...

# Environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos credentials
```

### Lancer l'API
```bash
uvicorn backend.main:app --reload
```

### Tests
```bash
pytest tests/ -v --cov=backend
```

## Architecture

[Diagrammes à ajouter]

## Utilisation

### Commande texte
```bash
curl -X POST http://localhost:8000/command/text \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user1",
    "text": "Allume la lampe du salon"
  }'
```

[... suite documentation]
```

**Livrable :** Documentation complète + tests intégration

---

**Résumé Omar Semaine 1:**
- T1.9: mqtt_client.py (16h)
- T1.10: Tests + documentation (22h)
**Total Omar S1: 38h**

---

### 2.3 Semaine 2 - Core Intelligence (TOUS)

**Focus :** Agent Core + Classifier + Action Builder

#### 👤 Montassar - Semaine 2 (38h)

**T2.1 - Intent Classifier (intent_classifier.py) - 14h**
```python
# Fichier: backend/classifier/intent_classifier.py
# Montassar crée le classificateur complet

import re
from typing import Dict, List

from backend.agent.logger import app_logger
from backend.utils.validators import json_validator

class IntentClassifier:
    """
    Classificateur Conversation vs Action
    
    Méthodes:
    - rules: Basé sur mots-clés (rapide, MVP)
    - ml: Machine Learning (futur)
    - llm: Via LLM (plus précis mais coûteux)
    """
    
    def __init__(self, method: str = "rules"):
        self.method = method
        
        # Mots-clés conversation
        self.keywords_conversation = [
            "bonjour", "salut", "hey", "coucou",
            "ça va", "comment vas-tu", "comment tu vas",
            "qui es-tu", "tu es qui", "c'est quoi ton nom",
            "que fais-tu", "tu fais quoi",
            "merci", "thanks", "ok", "d'accord",
            "au revoir", "bye", "à plus", "ciao",
            "aide", "help", "explique", "comment"
        ]
        
        # Mots-clés action
        self.keywords_action = [
            # IoT
            "allume", "éteins", "active", "désactive",
            "ouvre", "ferme", "mets", "règle",
            "augmente", "diminue", "baisse",
            "lampe", "lumière", "chauffage", "climatisation",
            "porte", "fenêtre", "volet",
            
            # Email
            "envoie", "envoi", "mail", "email", "message",
            "écris", "rédige",
            
            # Reminder
            "rappelle", "rappel", "rendez-vous", "rdv",
            "note", "agenda", "calendrier",
            
            # Web
            "cherche", "recherche", "trouve", "google",
            "internet", "web", "site"
        ]
        
        # Verbes d'action forts
        self.action_verbs = [
            "allume", "éteins", "active", "désactive",
            "envoie", "envoi", "cherche", "recherche",
            "rappelle", "ouvre", "ferme", "mets"
        ]
        
        app_logger.info(f"IntentClassifier initialized (method={method})")
    
    def classify(self, text: str, context: dict = None) -> dict:
        """
        Classifier texte
        
        Input (Section 2.2 Fichier 02):
        {
          "request_id": "...",
          "raw_text": text,
          "source": "voice|text",
          "user_id": "...",
          "context": context
        }
        
        Output (Section 2.3 Fichier 02):
        {
          "request_id": "...",
          "classification": "conversation|action",
          "confidence": 0.0-1.0,
          "method": "rules|ml|llm",
          "reasoning": {...}
        }
        """
        text_lower = text.lower().strip()
        
        app_logger.info(f"Classifying: '{text}'")
        
        if self.method == "rules":
            result = self._classify_rules(text_lower, context)
        elif self.method == "ml":
            result = self._classify_ml(text_lower, context)
        elif self.method == "llm":
            result = self._classify_llm(text_lower, context)
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        app_logger.info(
            f"Classification: {result['classification']} "
            f"(confidence={result['confidence']:.2f})"
        )
        
        return result
    
    def _classify_rules(self, text: str, context: dict = None) -> dict:
        """
        Classification par règles et mots-clés
        
        Logique:
        1. Détecter mots-clés conversation
        2. Détecter mots-clés action
        3. Détecter verbes d'action
        4. Calculer scores
        5. Décider avec seuils
        """
        # Scores
        score_conversation = 0
        score_action = 0
        
        # Mots-clés conversation
        for keyword in self.keywords_conversation:
            if keyword in text:
                score_conversation += 1
        
        # Mots-clés action
        for keyword in self.keywords_action:
            if keyword in text:
                score_action += 1
        
        # Verbes d'action (poids plus fort)
        for verb in self.action_verbs:
            if verb in text:
                score_action += 2
        
        # Patterns regex
        # Détection question (souvent conversation)
        if re.search(r'\?$', text) or re.search(r'^(qui|quoi|où|quand|comment|pourquoi)', text):
            score_conversation += 1
        
        # Détection impératif (souvent action)
        if re.search(r'^(allume|éteins|envoie|cherche)', text):
            score_action += 2
        
        # Contexte (si action précédente, plus probable action)
        if context and context.get("previous_classification") == "action":
            score_action += 0.5
        
        # Décision
        total_score = score_conversation + score_action
        
        if total_score == 0:
            # Pas de signal clair → conversation par défaut
            classification = "conversation"
            confidence = 0.5
        elif score_action > score_conversation:
            classification = "action"
            confidence = min(0.7 + (score_action * 0.1), 0.99)
        else:
            classification = "conversation"
            confidence = min(0.7 + (score_conversation * 0.1), 0.99)
        
        return {
            "classification": classification,
            "confidence": confidence,
            "method": "rules",
            "reasoning": {
                "score_conversation": score_conversation,
                "score_action": score_action,
                "keywords_found": {
                    "conversation": [
                        kw for kw in self.keywords_conversation 
                        if kw in text
                    ],
                    "action": [
                        kw for kw in self.keywords_action 
                        if kw in text
                    ]
                }
            }
        }
    
    def _classify_ml(self, text: str, context: dict = None) -> dict:
        """Classification ML (à implémenter futur)"""
        app_logger.warning("ML classification not implemented yet")
        return self._classify_rules(text, context)
    
    def _classify_llm(self, text: str, context: dict = None) -> dict:
        """Classification via LLM (à implémenter futur)"""
        app_logger.warning("LLM classification not implemented yet")
        return self._classify_rules(text, context)

# Instance globale
intent_classifier = IntentClassifier(method="rules")
```

**Livrable :** Classifier fonctionnel avec 90%+ précision sur dataset test  
**Test :** Dataset 50+ exemples annotés

---

**T2.2 - Agent Core orchestrateur (agent_core.py) - 18h**

*[Contenu très détaillé de agent_core.py - 800+ lignes]*

Agent Core intègre :
- Classifier
- State Manager
- Security Manager
- Action Builder
- Confirmation Handler
- LLM Client
- n8n Client
- MQTT Client

**Livrable :** agent_core.py fonctionnel  
**Test :** Tests unitaires + tests intégration

---

**T2.3 - Intégration dans main.py - 6h**

Mettre à jour routes API pour utiliser Agent Core au lieu des mocks.

---

**Résumé Montassar S2: 38h** (Classifier + Agent Core + Intégration)

#### 👤 Amine - Semaine 2 (38h)

**T2.4 - Action Builder (action_builder.py) - 18h**

Créer tous les builders pour construire ActionJSON selon l'intent.

**T2.5 - Confirmation Handler (confirmation_handler.py) - 14h**

Gérer demandes confirmation + parsing réponses utilisateur.

**T2.6 - n8n Client (n8n_client.py) - 6h**

Client pour envoyer ActionJSON vers n8n (mocké pour l'instant).

**Résumé Amine S2: 38h**

#### 👤 Omar - Semaine 2 (38h)

**T2.7 - Tests Agent Core - 20h**

Suite de tests complète pour Agent Core (scénarios complets).

**T2.8 - Scripts démo - 10h**

Scripts pour démonstrations (conversation, action, confirmation).

**T2.9 - Documentation architecture - 8h**

Diagrammes + explications flux.

**Résumé Omar S2: 38h**

---

### 2.4 Semaines 3-4 - Modules AI (STT, TTS, LLM)

*[Détails similaires pour semaines 3-4]*

---

### 2.5 Semaines 5-6 - Tests & Finalisation Backend

**Objectif :** Backend 100% terminé, testé, documenté

Tous les 3 travaillent sur :
- Tests end-to-end Backend
- Corrections bugs
- Optimisations performance
- Documentation complète
- Validation finale

**Résultat fin Semaine 6 :**
✅ Backend Python 100% opérationnel  
✅ Tests passants (couverture 80%+)  
✅ Documentation complète  
✅ Prêt pour intégration n8n

---

## 3. Phase 2 - MODULE N8N ORCHESTRATION (Semaines 7-9)

**🎯 Objectif :** Développer n8n complet avec tous les workflows

**Lead : Amine**  
**Support : Montassar, Omar**

### 3.1 Vue d'ensemble

Maintenant que le Backend est terminé, toute l'équipe se concentre sur n8n.

**Distribution :**
- **Amine (70%)** : Tous les workflows n8n
- **Montassar (20%)** : Intégration Backend ↔ n8n + Tests
- **Omar (10%)** : Setup MQTT + Tests

**Durée :** 3 semaines (114h total)

### 3.2 Semaine 7 - Setup n8n + Workflows de base

#### Amine - Lead (38h)
- Setup n8n complet
- wf_action_router
- wf_control_iot
- wf_send_email

#### Montassar - Support (38h)
- Aide setup n8n
- Tests intégration Backend → n8n
- Corrections Backend si nécessaire

#### Omar - Support (38h)
- Setup Broker MQTT
- Tests MQTT avec n8n
- Aide tests workflows

---

### 3.3 Semaine 8 - Workflows avancés

*[Détails similaires]*

---

### 3.4 Semaine 9 - Tests & Finalisation n8n

**Résultat fin Semaine 9 :**
✅ n8n 100% opérationnel  
✅ Intégration Backend ↔ n8n validée  
✅ Prêt pour ESP32

---

## 4. Phase 3 - MODULE ESP32 EMBARQUÉ (Semaines 10-12)

**🎯 Objectif :** Développer ESP32 complet

**Lead : Omar**  
**Support : Amine, Montassar**

### 4.1 Vue d'ensemble

**Distribution :**
- **Omar (70%)** : Tout le code ESP32
- **Amine (20%)** : MQTT broker + Tests
- **Montassar (10%)** : Audio + Intégration

**Durée :** 3 semaines (114h total)

*[Détails similaires aux phases précédentes]*

---

## 5. Phase 4 - INTÉGRATION GLOBALE (Semaines 13-14)

**🎯 Objectif :** Intégrer tous les modules ensemble

**Tous égaux (33% chacun)**

### 5.1 Semaine 13 - Intégration

- Tests end-to-end complets
- Corrections bugs inter-modules
- Optimisations

### 5.2 Semaine 14 - Validation finale

- Tous les scénarios testés
- Système stable
- Prêt pour documentation

---

## 6. Phase 5 - DOCUMENTATION & SOUTENANCE (Semaines 15-16)

**Tous travaillent sur documentation et présentation**

---

## 📊 Résumé Global Approche Séquentielle

| Phase | Semaines | Lead | Livrable | Statut |
|-------|----------|------|----------|--------|
| **Backend Python** | 1-6 | Montassar | Backend 100% | ⏳ En cours |
| **n8n Orchestration** | 7-9 | Amine | n8n 100% | ⏸️ À venir |
| **ESP32 Embarqué** | 10-12 | Omar | ESP32 100% | ⏸️ À venir |
| **Intégration** | 13-14 | TOUS | Système complet | ⏸️ À venir |
| **Documentation** | 15-16 | TOUS | Soutenance | ⏸️ À venir |

**Total : 16 semaines (4 mois)**

---

## 🎯 Avantages de cette approche

✅ **Concentration maximale** : Toute l'équipe sur un seul module  
✅ **Qualité garantie** : Module testé avant de passer au suivant  
✅ **Pas de blocages d'attente** : Pas besoin d'attendre les autres  
✅ **Apprentissage collectif** : Tout le monde comprend chaque module  
✅ **Flexibilité** : Adaptation facile selon avancement  

---

**Document créé le : 20 janvier 2026**  
**Version : 1.0 - Approche Séquentielle**  
**Statut : PRÊT pour exécution - Commencer par Backend**

**Bon courage à toute l'équipe ! 🚀**
