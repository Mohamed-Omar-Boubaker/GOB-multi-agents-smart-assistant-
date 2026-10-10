# 📊 Mapping et Distribution des Tâches - Équipe Projet PCD
## Agent Intelligent Embarqué

**Version :** 1.1 - Distribution Équipe (CORRIGÉ)  
**Date :** 20 janvier 2026  
**Équipe :** 3 personnes (Montassar, Amine, Omar)  
**Durée estimée :** 10-15 semaines

---

## 📑 Table des Matières

1. [Vue d'ensemble de l'équipe](#1-vue-densemble-de-léquipe)
2. [Principe de distribution](#2-principe-de-distribution)
3. [Distribution par module technique](#3-distribution-par-module-technique)
4. [Personne 1 - Montassar (VOUS - Chef de Projet)](#4-personne-1---montassar)
5. [Personne 2 - Amine](#5-personne-2---amine)
6. [Personne 3 - Omar](#6-personne-3---omar)
7. [Checklist de validation](#7-checklist-de-validation)
8. [Planning par sprint](#8-planning-par-sprint)
9. [Matrice des dépendances](#9-matrice-des-dépendances)
10. [Points de synchronisation](#10-points-de-synchronisation)

---

## 1. Vue d'ensemble de l'équipe

### 1.1 Composition de l'équipe

| Membre | Rôle Principal | Modules Assignés | Charge (%) |
|--------|----------------|------------------|------------|
| **Montassar (VOUS)** | Chef de Projet / Architecte / Dev Backend | Backend Python COMPLET (Core + AI) + Coordination | 100% |
| **Amine** | Développeur Full-Stack | n8n Workflows + API Integration | 100% |
| **Omar** | Développeur Embarqué | ESP32 + MQTT + Audio | 100% |

### 1.2 Répartition globale par module

```
┌─────────────────────────────────────────────────────────────┐
│                    PROJET PCD - 4 MODULES                    │
└─────────────────────────────────────────────────────────────┘

Module 1: Backend Python (Agent Core)
├── MONTASSAR (VOUS): Tout le Backend Python
│   ├── Agent Core, State Manager, Security, Confirmation
│   ├── STT, TTS, LLM Client, Classifier, Action Builder
│   └── API FastAPI complète
└── Charge: 100% Montassar

Module 2: LLM / AI Engine
├── MONTASSAR (VOUS): LLM Server, Prompts, Response Formatter
└── Charge: 100% Montassar

Module 3: n8n Orchestration
├── AMINE: Tous les workflows n8n, Intégrations externes
└── Charge: 100% Amine

Module 4: ESP32 Embarqué
├── OMAR: Tout le code ESP32, MQTT, Audio
└── Charge: 100% Omar

Coordination & Tests
├── MONTASSAR (VOUS): Intégration globale, Tests end-to-end, Coordination
└── TOUS: Tests de leur module respectif
```

---

## 2. Principe de distribution

### 2.1 Critères de distribution

**Séparation par compétences techniques :**
- Python backend avancé → Vous + Montassar
- AI/LLM spécialisé → Montassar
- Workflows/Orchestration → Amine
- Embarqué/IoT → Omar

**Séparation par flux JSON :**
- Flux 0-4 (Classification, Conversation, Action) → Vous + Montassar
- Flux 5 (Python → n8n) → Interface Vous ↔ Amine
- Flux 6-8 (n8n ↔ ESP32 ↔ n8n) → Interface Amine ↔ Omar
- Flux Audio (ESP32 ↔ Python) → Interface Omar ↔ Montassar

**Dépendances minimisées :**
- Chaque personne peut développer en parallèle
- Interfaces JSON clairement définies
- Points de synchronisation hebdomadaires

### 2.2 Stratégie de développement

```
Phase 1 (Semaines 1-2): Setup + Maquettes JSON
├── TOUS: Setup environnement
├── MONTASSAR (VOUS): Structure projet, Config, Logger, Tests LLM
├── AMINE: Setup n8n, Workflows mockup
└── OMAR: Setup ESP32, MQTT tests

Phase 2 (Semaines 3-5): Développement Core
├── MONTASSAR (VOUS): Backend Python COMPLET (Core + AI)
├── AMINE: Workflows n8n complets
└── OMAR: Code ESP32 complet

Phase 3 (Semaines 6-7): Intégration
├── MONTASSAR (VOUS): Intégration Backend ↔ n8n (AI déjà intégré)
├── AMINE: Intégration n8n ↔ ESP32
└── OMAR: Tests ESP32 avec vrais messages

Phase 4 (Semaines 8-10): Tests & Documentation
├── MONTASSAR (VOUS): Tests end-to-end, Documentation finale, Coordination soutenance
├── TOUS: Tests unitaires, Corrections bugs
└── TOUS: Préparation soutenance
```

---

## 3. Distribution par module technique

### 3.1 Module 1 - Backend Python (Agent Core)

**Responsables :** Vous (60%) + Montassar (40%)

#### Fichiers VOUS :
```
backend/
├── main.py                          ✅ VOUS
├── config.py                        ✅ VOUS
├── requirements.txt                 ✅ VOUS (avec Montassar)
├── agent/
│   ├── agent_core.py               ✅ VOUS (Orchestration)
│   ├── state_manager.py            ✅ VOUS
│   ├── security_manager.py         ✅ VOUS
│   └── logger.py                   ✅ VOUS
├── actions/
│   ├── action_builder.py           ✅ VOUS
│   ├── confirmation_handler.py     ✅ VOUS
│   └── action_models.py            ✅ VOUS
├── integrations/
│   ├── n8n_client.py               ✅ VOUS
│   └── mqtt_client.py              🔄 VOUS + OMAR (interface)
└── utils/
    ├── validators.py               ✅ VOUS
    ├── serializers.py              ✅ VOUS
    └── exceptions.py               ✅ VOUS
```

#### Fichiers MONTASSAR :
```
backend/
├── ai/
│   ├── llm_client.py               ✅ MONTASSAR
│   ├── stt_engine.py               ✅ MONTASSAR
│   └── tts_engine.py               ✅ MONTASSAR
└── classifier/
    └── intent_classifier.py        ✅ MONTASSAR
```

---

### 3.2 Module 2 - LLM / AI Engine

**Responsable :** Montassar (100%)

```
llm/
├── llm_server.py                   ✅ MONTASSAR
├── prompt_templates.py             ✅ MONTASSAR
├── response_formatter.py           ✅ MONTASSAR
└── schemas.py                      ✅ MONTASSAR
```

**Flux JSON à gérer :**
- Flux 1: Python → LLM (Analyse Linguistique)
- Flux 2: LLM → Python (Résultat Analyse)
- Flux Conversation: ConversationJSON

---

### 3.3 Module 3 - n8n Orchestration

**Responsable :** Amine (100%)

```
n8n/
├── wf_action_router                ✅ AMINE
├── wf_send_email                   ✅ AMINE
├── wf_control_iot                  ✅ AMINE
├── wf_web_search                   ✅ AMINE
├── wf_log_event                    ✅ AMINE
└── wf_set_reminder                 ✅ AMINE
```

**Flux JSON à gérer :**
- Flux 5: Python → n8n (ActionJSON CONFIRMED)
- Flux 6: n8n → ESP32 (Commandes MQTT)
- Flux 7: ESP32 → n8n (Retours état)
- Flux 8: n8n → Python (Résultats finaux)

---

### 3.4 Module 4 - ESP32 Embarqué

**Responsable  (tous)

```
esp32/
├── main.cpp                        ✅ tous
├── mqtt_client.cpp                 ✅ monta
├── audio_handler.cpp               ✅ tous
├── device_manager.cpp              ✅ OMAR
├── sensors.cpp                     ✅ tous
├── actuators.cpp                   ✅ tous
└── config.h                        ✅ monta
```

**Flux JSON à gérer :**
- Flux 6: n8n → ESP32 (Commandes)
- Flux 7: ESP32 → n8n (Retours)
- Flux 12: ESP32 → Python (Audio brut)
- Flux 13: Python → ESP32 (Audio réponse)

---

## 4. Personne 1 - Montassar (VOUS - Chef de Projet)

### 4.1 Rôle et Responsabilités

**Rôle principal :** Chef de Projet + Architecte + Développeur Backend Python COMPLET

**Responsabilités :**
- ✅ Architecture globale et cohérence
- ✅ Coordination équipe (réunions, suivi)
- ✅ **TOUT le Backend Python** (Core + AI + LLM)
- ✅ Intégration inter-modules
- ✅ Gestion des flux JSON critiques
- ✅ Sécurité et état du système
- ✅ Tests end-to-end
- ✅ Documentation finale et soutenance

---

### 4.2 Tâches Détaillées

**NOTE IMPORTANTE :** Vous (Montassar) êtes responsable de TOUT le Backend Python (Core + AI). Les tâches ci-dessous combinent ce qui était prévu pour "Vous" et "Montassar" dans la version initiale.

#### Phase 1: Setup Projet (Semaine 1)

**T1.1 - Structure du projet**
```bash
Créer la structure complète des dossiers
├── backend/
├── llm/
├── n8n/
├── esp32/
├── docs/
├── tests/
└── README.md
```
- Temps estimé: 2h
- Priorité: CRITIQUE
- Dépendances: Aucune
- Livrable: Arborescence complète

**T1.2 - Configuration globale (config.py)**
```python
# Fichier: backend/config.py
# Contenu: Toutes les variables d'environnement
- Configuration serveur (host, port)
- Credentials LLM, MQTT, n8n
- Paramètres sécurité (secret keys)
- Timeouts et limites
```
- Temps estimé: 3h
- Priorité: CRITIQUE
- Dépendances: T1.1
- Livrable: config.py fonctionnel

**T1.3 - Logger centralisé (logger.py)**
```python
# Fichier: backend/agent/logger.py
# Fonctionnalités:
- Logs JSON structurés
- Rotation automatique
- Niveaux: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Intégration avec tous les modules
```
- Temps estimé: 4h
- Priorité: HAUTE
- Dépendances: T1.2
- Livrable: logger.py avec tests

**T1.4 - Requirements Python (requirements.txt)**
```
# Tous les requirements pour Backend Python complet
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
python-multipart==0.0.6
openai==1.10.0
whisper==1.1.10
gtts==2.5.0
paho-mqtt==1.6.1
requests==2.31.0
cryptography==42.0.0
pytest==7.4.4
```
- Temps estimé: 2h
- Priorité: HAUTE
- Dépendances: Aucune
- Livrable: requirements.txt complet

---

#### Phase 2: Développement Core (Semaines 2-4)

**T1.5 - API FastAPI (main.py)**
```python
# Fichier: backend/main.py
# Routes à implémenter:

POST /command/text
├── Input: {"user_id": "...", "text": "..."}
├── Process: Classification → Action/Conversation
└── Output: Response JSON

POST /command/audio
├── Input: Audio base64
├── Process: STT → Classification → Action/Conversation
└── Output: Response JSON + Audio TTS

POST /callback/n8n
├── Input: Résultat exécution n8n
├── Process: Update state, Log, Notify user
└── Output: Acknowledgment

GET /health
├── Output: Status système

GET /status/{action_id}
├── Output: État action
```
- Temps estimé: 12h
- Priorité: CRITIQUE
- Dépendances: T1.2, T1.3
- Livrable: API fonctionnelle avec 4 routes

**T1.6 - Agent Core (agent_core.py)**
```python
# Fichier: backend/agent/agent_core.py
# Classe: AgentCore
# Méthodes principales:

def process_command(user_id: str, input_data: dict):
    """
    Orchestration principale
    1. Validation input
    2. Classification (via Montassar)
    3. Routage Conversation vs Action
    4. Gestion confirmations
    5. Envoi n8n si confirmé
    """

def _handle_conversation(request_id: str, text: str):
    """
    Pipeline conversation
    1. Appel LLM pour réponse
    2. TTS si nécessaire
    3. Logging
    4. Return response
    """

def _handle_action(request_id: str, intent: dict):
    """
    Pipeline action
    1. Construction ActionJSON (DRAFT)
    2. Demande confirmation
    3. Attente réponse utilisateur
    4. Si confirmé → Update CONFIRMED + Envoi n8n
    5. Callback handler pour résultats
    """

def handle_confirmation(action_id: str, user_response: dict):
    """
    Gestion réponse confirmation
    1. Parse réponse (confirm/cancel/modify)
    2. Update ActionJSON
    3. Si confirm → Sign + Send n8n
    4. Si cancel → Update state CANCELED
    5. Si modify → Reprocess
    """

def handle_n8n_callback(action_id: str, result: dict):
    """
    Traitement résultat n8n
    1. Validation signature
    2. Update state (SUCCESS/ERROR)
    3. Logging
    4. Notification utilisateur (TTS)
    """
```
- Temps estimé: 20h
- Priorité: CRITIQUE
- Dépendances: T1.5, T1.21 (Classifier), T1.24 (LLM Client)
- Livrable: agent_core.py complet (500+ lignes)

**T1.7 - State Manager (state_manager.py)**
```python
# Fichier: backend/agent/state_manager.py
# Gestion machine à états

class ActionState(Enum):
    IDLE = "IDLE"
    DRAFT = "DRAFT"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

class StateManager:
    def __init__(self):
        self.actions = {}  # action_id → ActionJSON
    
    def create_action(action_json: dict) -> str:
        """Créer action état DRAFT"""
    
    def update_state(action_id: str, new_state: ActionState):
        """Transition état avec validation"""
    
    def get_action(action_id: str) -> dict:
        """Récupérer ActionJSON"""
    
    def is_valid_transition(current: ActionState, target: ActionState) -> bool:
        """Valider transition autorisée"""
```
- Temps estimé: 8h
- Priorité: HAUTE
- Dépendances: T1.3
- Livrable: state_manager.py avec tests

**T1.8 - Security Manager (security_manager.py)**
```python
# Fichier: backend/agent/security_manager.py
# Sécurité et signatures

class SecurityManager:
    def generate_signature(action_json: dict) -> str:
        """Générer signature HMAC-SHA256"""
    
    def verify_signature(action_json: dict, signature: str) -> bool:
        """Vérifier signature"""
    
    def check_permissions(user_id: str, action: dict) -> bool:
        """Vérifier permissions utilisateur"""
    
    def generate_token(user_id: str) -> str:
        """Générer JWT token"""
    
    def verify_token(token: str) -> dict:
        """Vérifier et décoder JWT"""
```
- Temps estimé: 10h
- Priorité: HAUTE
- Dépendances: T1.2
- Livrable: security_manager.py avec tests

**T1.9 - Action Builder (action_builder.py)**
```python
# Fichier: backend/actions/action_builder.py
# Construction ActionJSON

class ActionBuilder:
    def build_action_json(
        intent: str,
        entities: dict,
        context: dict
    ) -> dict:
        """
        Construire ActionJSON complet
        Référence: Section 6.2 et 6.3 du fichier 02
        """
    
    def build_control_iot_payload(entities: dict) -> dict:
        """Payload spécifique control_iot"""
    
    def build_send_email_payload(entities: dict) -> dict:
        """Payload spécifique send_email"""
    
    def build_set_reminder_payload(entities: dict) -> dict:
        """Payload spécifique set_reminder"""
    
    def build_web_search_payload(entities: dict) -> dict:
        """Payload spécifique web_search"""
```
- Temps estimé: 12h
- Priorité: HAUTE
- Dépendances: T1.7
- Livrable: action_builder.py avec 4 payloads

**T1.10 - Confirmation Handler (confirmation_handler.py)**
```python
# Fichier: backend/actions/confirmation_handler.py
# Gestion confirmations utilisateur

class ConfirmationHandler:
    def generate_confirmation_request(action_json: dict) -> dict:
        """
        Créer demande de confirmation
        Référence: Section 7.2 du fichier 02
        """
    
    def parse_user_response(raw_input: str) -> dict:
        """
        Parser réponse utilisateur
        Détection: confirm, cancel, modify
        Référence: Section 7.3 du fichier 02
        """
    
    def apply_confirmation(
        action_json: dict,
        user_response: dict
    ) -> dict:
        """
        Mettre à jour ActionJSON après confirmation
        Référence: Section 7.4 du fichier 02
        """
```
- Temps estimé: 10h
- Priorité: HAUTE
- Dépendances: T1.9, T1.25 (TTS Engine)
- Livrable: confirmation_handler.py complet

**T1.11 - n8n Client (n8n_client.py)**
```python
# Fichier: backend/integrations/n8n_client.py
# Communication avec n8n

class N8nClient:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_action(action_json: dict) -> dict:
        """
        Envoyer ActionJSON CONFIRMED vers n8n
        Référence: Section 8.2 du fichier 02
        Validation:
        - state = "CONFIRMED"
        - confirmed = true
        - signature valide
        """
    
    def validate_callback(callback_data: dict) -> bool:
        """
        Valider callback reçu de n8n
        Référence: Section 11.2 du fichier 02
        """
```
- Temps estimé: 6h
- Priorité: HAUTE
- Dépendances: T1.8, Interface avec Amine (webhook URL)
- Livrable: n8n_client.py avec tests

**T1.12 - MQTT Client (mqtt_client.py)**
```python
# Fichier: backend/integrations/mqtt_client.py
# Communication MQTT (principalement audio)

class MQTTClient:
    def __init__(self, broker: str, port: int):
        self.client = paho.mqtt.client.Client()
    
    def send_audio_response(
        device_id: str,
        audio_data: str,
        config: dict
    ):
        """
        Envoyer réponse audio vers ESP32
        Référence: Section 13.2 du fichier 02
        Topic: esp32/audio/response/{device_id}
        """
    
    def subscribe_audio_upload(callback: callable):
        """
        Écouter upload audio depuis ESP32
        Topic: esp32/audio/upload/{device_id}
        """
```
- Temps estimé: 6h
- Priorité: MOYENNE
- Dépendances: Interface avec Omar (topics MQTT)
- Livrable: mqtt_client.py fonctionnel

**T1.13 - Validators (validators.py)**
```python
# Fichier: backend/utils/validators.py
# Validation JSON selon specs

class JSONValidator:
    def validate_classification_input(data: dict) -> bool:
        """Valider Flux 0 INPUT - Section 2.2"""
    
    def validate_classification_output(data: dict) -> bool:
        """Valider Flux 0 OUTPUT - Section 2.3"""
    
    def validate_action_json(data: dict) -> bool:
        """Valider ActionJSON complet - Section 6.2"""
    
    def validate_confirmation_request(data: dict) -> bool:
        """Valider demande confirmation - Section 7.2"""
    
    def validate_n8n_callback(data: dict) -> bool:
        """Valider callback n8n - Section 11.2"""
```
- Temps estimé: 8h
- Priorité: HAUTE
- Dépendances: Fichier 02 (JSON specs)
- Livrable: validators.py avec tous les flux

---

#### Phase 2 (Suite): Modules AI/LLM (Semaines 3-4)

**NOTE :** Ces tâches AI font partie de votre responsabilité Backend Python complet.

**T1.21 - Intent Classifier (intent_classifier.py)**
```python
# Fichier: backend/classifier/intent_classifier.py
# Classification Conversation vs Action

class IntentClassifier:
    def __init__(self, method: str = "rules"):
        """
        Methods: "rules", "ml", "llm"
        Default: "rules" (plus rapide)
        """
        self.method = method
        self.keywords_conversation = [
            "bonjour", "salut", "ça va", "comment vas-tu",
            "qui es-tu", "que fais-tu", "merci", "au revoir"
        ]
        self.keywords_action = [
            "envoie", "allume", "éteins", "cherche", "rappelle",
            "active", "désactive", "ouvre", "ferme"
        ]
    
    def classify(self, text: str) -> dict:
        """Classifier texte en conversation ou action
        
        Input (Section 2.2 Fichier 02):
        {
          "request_id": "...",
          "raw_text": "...",
          "source": "voice|text",
          "user_id": "...",
          "context": {...}
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
        if self.method == "rules":
            return self._classify_rules(text)
        elif self.method == "ml":
            return self._classify_ml(text)
        else:
            return self._classify_llm(text)
    
    def _classify_rules(self, text: str) -> dict:
        """Classification par mots-clés"""
        text_lower = text.lower()
        
        score_conv = sum(1 for kw in self.keywords_conversation if kw in text_lower)
        score_action = sum(1 for kw in self.keywords_action if kw in text_lower)
        
        if score_action > score_conv:
            return {
                "classification": "action",
                "confidence": min(0.7 + score_action * 0.1, 0.99),
                "method": "rules"
            }
        else:
            return {
                "classification": "conversation",
                "confidence": min(0.7 + score_conv * 0.1, 0.99),
                "method": "rules"
            }
```
- Temps estimé: 12h
- Priorité: CRITIQUE
- Dépendances: T1.4
- Livrable: intent_classifier.py complet avec tests

**T1.22 - STT Engine (stt_engine.py)**
```python
# Fichier: backend/ai/stt_engine.py
# Speech-to-Text avec Whisper

import whisper
import base64
import io
from pydub import AudioSegment

class STTEngine:
    def __init__(self, model_size: str = "base"):
        """Model sizes: tiny, base, small, medium, large"""
        self.model = whisper.load_model(model_size)
    
    def transcribe(self, audio_data: str, audio_format: str = "wav") -> dict:
        """
        Transcription audio → texte
        Référence: Section 12.2 Fichier 02
        """
        audio_bytes = base64.b64decode(audio_data)
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=audio_format)
        
        temp_file = "/tmp/temp_audio.wav"
        audio.export(temp_file, format="wav")
        
        import time
        start = time.time()
        result = self.model.transcribe(temp_file, language="fr")
        duration_ms = int((time.time() - start) * 1000)
        
        return {
            "text": result["text"],
            "confidence": result.get("confidence", 0.9),
            "language": result.get("language", "fr"),
            "processing_time_ms": duration_ms
        }
```
- Temps estimé: 10h
- Priorité: CRITIQUE
- Dépendances: T1.4
- Livrable: stt_engine.py avec tests audio

**T1.23 - TTS Engine (tts_engine.py)**
```python
# Fichier: backend/ai/tts_engine.py
# Text-to-Speech avec gTTS

from gtts import gTTS
import base64
import io

class TTSEngine:
    def __init__(self, language: str = "fr"):
        self.language = language
    
    def synthesize(self, text: str, config: dict = None) -> dict:
        """
        Synthèse texte → audio
        Référence: Section 13.2 Fichier 02
        """
        config = config or {}
        language = config.get("language", self.language)
        slow = config.get("slow", False)
        
        tts = gTTS(text=text, lang=language, slow=slow)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        audio_bytes = audio_buffer.read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {
            "audio_data": audio_base64,
            "audio_format": "mp3",
            "audio_metadata": {
                "duration_ms": len(text) * 80,
                "size_bytes": len(audio_bytes),
                "sample_rate": 24000,
                "channels": 1
            }
        }
```
- Temps estimé: 8h
- Priorité: HAUTE
- Dépendances: T1.4
- Livrable: tts_engine.py avec tests

**T1.24 - LLM Client Backend (llm_client.py)**
```python
# Fichier: backend/ai/llm_client.py
# Client LLM pour Backend Python

import openai
from typing import Optional

class LLMClient:
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """Client pour communiquer avec LLM"""
        openai.api_key = api_key
        if base_url:
            openai.api_base = base_url
    
    def analyze_intent(self, request: dict) -> dict:
        """
        Analyse d'intention
        Référence: Section 4.2 et 4.3 Fichier 02
        """
        prompt = self._build_intent_prompt(request)
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un assistant d'analyse d'intentions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        result = self._parse_intent_response(response)
        
        return {
            "request_id": request["request_id"],
            "analysis_result": result,
            "llm_metadata": {
                "model_used": "gpt-3.5-turbo",
                "tokens_used": response["usage"]["total_tokens"]
            },
            "status": "success"
        }
    
    def generate_conversation_response(self, request: dict) -> dict:
        """
        Génération réponse conversationnelle
        Référence: Section 3.2 et 3.3 Fichier 02
        """
        prompt = self._build_conversation_prompt(request)
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un assistant conversationnel amical."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        text = response["choices"][0]["message"]["content"]
        
        return {
            "response": {
                "text": text,
                "tts_enabled": True
            },
            "llm_metadata": {
                "tokens_used": response["usage"]["total_tokens"]
            },
            "status": "completed"
        }
    
    def _build_intent_prompt(self, request: dict) -> str:
        """Construire prompt pour analyse intention"""
        pass
    
    def _build_conversation_prompt(self, request: dict) -> str:
        """Construire prompt pour conversation"""
        pass
    
    def _parse_intent_response(self, response) -> dict:
        """Parser réponse LLM en structure JSON"""
        pass
```
- Temps estimé: 14h
- Priorité: CRITIQUE
- Dépendances: T1.4
- Livrable: llm_client.py complet

**T1.25 - LLM Server (llm/llm_server.py)**
```python
# Fichier: llm/llm_server.py
# Serveur LLM dédié (optionnel mais recommandé)

from fastapi import FastAPI
from pydantic import BaseModel
import openai

app = FastAPI()

class IntentAnalysisRequest(BaseModel):
    request_id: str
    input_text: str
    language: str
    context: dict
    analysis_mode: dict

class ConversationRequest(BaseModel):
    conversation_id: str
    input_text: str
    context: dict

@app.post("/analyze/intent")
async def analyze_intent(request: IntentAnalysisRequest):
    """Endpoint analyse d'intention - Section 4 Fichier 02"""
    pass

@app.post("/generate/conversation")
async def generate_conversation(request: ConversationRequest):
    """Endpoint génération conversation - Section 3 Fichier 02"""
    pass

@app.get("/health")
async def health():
    return {"status": "ok"}
```
- Temps estimé: 10h
- Priorité: MOYENNE (optionnel)
- Dépendances: T1.4
- Livrable: llm_server.py fonctionnel

**T1.26 - Prompt Templates (llm/prompt_templates.py)**
```python
# Fichier: llm/prompt_templates.py
# Templates de prompts optimisés

INTENT_ANALYSIS_PROMPT = """
Analyse l'intention de l'utilisateur dans le texte suivant :

Texte : "{input_text}"
Langue : {language}

Détermine :
1. L'intention principale parmi : control_iot, send_email, set_reminder, web_search
2. Les entités extraites (device, location, recipient, subject, etc.)
3. Ton niveau de confiance (0-1)

Réponds au format JSON :
{{
  "intent": "...",
  "intent_confidence": 0.XX,
  "entities": {{...}}
}}
"""

CONVERSATION_PROMPT = """
Tu es un assistant vocal intelligent et amical.

Question utilisateur : "{input_text}"

Réponds de manière naturelle, concise (2-3 phrases max) et amicale.
"""
```
- Temps estimé: 6h
- Priorité: HAUTE
- Dépendances: T1.24, T1.25
- Livrable: prompt_templates.py avec tous les prompts

**T1.27 - Tests Unitaires Modules AI**
```python
# Fichier: tests/test_ai_modules.py

def test_intent_classifier():
    """Tester classification sur 20+ exemples"""
    
def test_stt_engine():
    """Tester avec fichiers audio réels"""
    
def test_tts_engine():
    """Tester génération audio"""
    
def test_llm_client():
    """Tester analyse intention et conversation"""
```
- Temps estimé: 10h
- Priorité: HAUTE
- Dépendances: T1.21-T1.24
- Livrable: Suite tests complète AI

---

#### Phase 3: Intégration (Semaines 5-6)

**T1.14 - Tests Intégration Backend AI (Auto-test)**
```
Tests d'intégration internes:
├── Classification fonctionnelle
├── LLM répond correctement
├── STT/TTS fonctionnent
└── Flux JSON respectés
```
- Temps estimé: 6h (réduit car pas d'interface externe)
- Priorité: HAUTE
- Dépendances: Tous vos modules Backend terminés
- Livrable: Tests unitaires et intégration passants

**T1.15 - Intégration Backend ↔ Amine (n8n)**
```
Tests d'intégration:
├── Envoi ActionJSON vers n8n
├── Réception callbacks
├── Gestion erreurs
└── Validation signatures
```
- Temps estimé: 8h
- Priorité: CRITIQUE
- Dépendances: Amine T5.1-T5.6 (workflows n8n)
- Livrable: Tests passants

**T1.16 - Tests End-to-End**
```
Scénarios complets:
├── Conversation simple
├── Contrôle IoT (ESP32)
├── Envoi email
├── Annulation action
└── Gestion erreurs
```
- Temps estimé: 12h
- Priorité: CRITIQUE
- Dépendances: Tous modules terminés
- Livrable: Suite tests E2E

---

#### Phase 4: Documentation & Soutenance (Semaines 7-8)

**T1.17 - Documentation Technique**
```
Documents à finaliser:
├── README.md principal
├── Guide installation
├── Guide utilisation API
├── Architecture détaillée
└── Diagrammes de flux
```
- Temps estimé: 10h
- Priorité: HAUTE
- Dépendances: Projet terminé
- Livrable: Documentation complète

**T1.18 - Préparation Soutenance**
```
Préparation:
├── Slides présentation
├── Démonstrations
├── Vidéo du système
└── Q&A anticipées
```
- Temps estimé: 12h
- Priorité: HAUTE
- Dépendances: T1.17
- Livrable: Présentation prête

---

### 4.3 Récapitulatif Tâches VOUS

| Phase | Tâches | Temps Total | Priorité |
|-------|--------|-------------|----------|
| **Phase 1** | T1.1 → T1.4 | 11h | CRITIQUE |
| **Phase 2 Core** | T1.5 → T1.13 | 92h | CRITIQUE |
| **Phase 2 AI** | T1.21 → T1.28 | 60h (modules AI) | CRITIQUE |
| **Phase 3** | T1.14 → T1.16 | 26h | CRITIQUE |
| **Phase 4** | T1.17 → T1.18 | 22h | HAUTE |
| **TOTAL** | 28 tâches | **~241h** | - |

**Estimation : 6-7 semaines à temps plein (38h/sem)**
**NOTE :** Charge importante car vous gérez TOUT le Backend Python

---

## 5. Personne 2 - Amine

### 5.1 Rôle et Responsabilités

**Rôle principal :** Développeur Full-Stack + Spécialiste n8n

**Responsabilités :**
- ✅ Tous les workflows n8n (6 workflows {comme debut})
- ✅ Intégrations externes (SMTP, Web, etc.)
- ✅ Validation ActionJSON reçus
- ✅ Communication MQTT avec ESP32
- ✅ Callbacks vers Backend Python
- ✅ Logs et monitoring n8n

---

### 5.2 Tâches Détaillées

#### Phase 1: Setup n8n (Semaine 1)

**T3.1 - Installation n8n**
```bash
Installation et configuration:
├── npm install -g n8n
├── Configuration environnement
├── Setup webhooks
├── Configuration MQTT broker
└── Tests connexions
```
- Temps estimé: 4h
- Priorité: CRITIQUE
- Dépendances: Aucune
- Livrable: n8n opérationnel

**T3.2 - Setup Intégrations Externes**
```
Configuration:
├── SMTP (Gmail ou autre)
├── MQTT Broker (Mosquitto)
├── API Web Search (optionnel)
└── Credentials sécurisées
```
- Temps estimé: 4h
- Priorité: HAUTE
- Dépendances: T3.1
- Livrable: Intégrations testées

---

#### Phase 2: Développement Workflows (Semaines 2-4)

**T3.3 - Workflow Action Router (wf_action_router)**
```
Workflow principal - Point d'entrée

INPUT (Section 8.2 Fichier 02):
├── Webhook POST /webhook/action
├── Body: ActionJSON CONFIRMED complet
└── Headers: Authorization, Signature

ÉTAPES:
1. Validation Structure JSON
   ├── Vérifier champs obligatoires
   ├── Vérifier state="CONFIRMED"
   ├── Vérifier confirmed=true
   └── Vérifier signature HMAC

2. Routage par Intent
   ├── control_iot → wf_control_iot
   ├── send_email → wf_send_email
   ├── set_reminder → wf_set_reminder
   ├── web_search → wf_web_search
   └── log_event → wf_log_event

3. Envoi Acknowledgment Immédiat (Section 8.4 Fichier 02)
   ├── Si validé → status="accepted"
   └── Si rejeté → status="rejected"

4. Appel Workflow Spécialisé
   └── Passer ActionJSON complet

5. Attente Résultat
   └── Timeout 30 secondes

6. Callback Backend Python (Section 11.2 Fichier 02)
   ├── POST /callback/n8n
   └── Body: Résultat exécution

OUTPUT:
└── Résultat exécution vers Backend
```
- Temps estimé: 12h
- Priorité: CRITIQUE
- Dépendances: T3.1
- Livrable: wf_action_router complet

**T3.4 - Workflow Control IoT (wf_control_iot)**
```
Workflow contrôle ESP32

INPUT:
└── ActionJSON avec intent="control_iot"

ÉTAPES:
1. Extraction Payload
   ├── device_id
   ├── command
   ├── target
   └── value

2. Construction Commande ESP32 (Section 9.2 Fichier 02)
   {
     "command_id": "cmd_xxx",
     "device_id": "esp32_kitchen",
     "command": "RELAY_ON",
     "target": "LAMP_1",
     "value": 1,
     "priority": "high",
     "timestamp": unix_timestamp
   }

3. Publication MQTT
   ├── Topic: esp32/command/{device_id}
   ├── QoS: 1 (at least once)
   └── Retain: false

4. Attente Réponse ESP32 (Section 10.2 Fichier 02)
   ├── Subscribe: esp32/status/{device_id}
   ├── Timeout: 5 secondes
   └── Parse résultat

5. Logging Exécution
   └── Stocker dans wf_log_event

OUTPUT (Section 11.2 Fichier 02):
{
  "action_id": "...",
  "execution_status": "SUCCESS|ERROR",
  "module": "ESP32",
  "result_data": {...}
}
```
- Temps estimé: 10h
- Priorité: CRITIQUE
- Dépendances: T3.3, Coordination Omar
- Livrable: wf_control_iot fonctionnel

**T3.5 - Workflow Send Email (wf_send_email)**
```
Workflow envoi email

INPUT:
└── ActionJSON avec intent="send_email"

ÉTAPES:
1. Extraction Payload (Section 6.3 Fichier 02)
   ├── recipient / recipient_email
   ├── subject
   ├── body
   ├── attachments (optionnel)
   └── priority

2. Résolution Email Destinataire
   ├── Si recipient_email fourni → utiliser
   └── Sinon → chercher dans contacts (mock)

3. Construction Email
   ├── From: configured_email
   ├── To: recipient_email
   ├── Subject: subject
   ├── Body: body
   └── Format: plain ou html

4. Envoi via SMTP
   ├── Connexion serveur SMTP
   ├── Authentification
   ├── Envoi message
   └── Récupération message_id

5. Logging
   └── wf_log_event

OUTPUT (Section 11.2 Fichier 02):
{
  "action_id": "...",
  "execution_status": "SUCCESS",
  "module": "EMAIL",
  "result_data": {
    "recipient_email": "jean@example.com",
    "subject": "...",
    "message_id": "msg_abc123",
    "sent_at": "ISO8601"
  }
}
```
- Temps estimé: 10h
- Priorité: HAUTE
- Dépendances: T3.2, T3.3
- Livrable: wf_send_email fonctionnel

**T3.6 - Workflow Set Reminder (wf_set_reminder)**
```
Workflow définition rappel

INPUT:
└── ActionJSON avec intent="set_reminder"

ÉTAPES:
1. Extraction Payload
   ├── title
   ├── description
   ├── reminder_time
   ├── reminder_type (once/daily/weekly)
   └── notification_channels

2. Stockage Rappel
   ├── Base de données simple (JSON file ou SQLite)
   └── Indexé par user_id + reminder_time

3. Planification Exécution
   ├── Cron job n8n
   └── Ou Workflow Schedule Node

4. Logging
   └── wf_log_event

OUTPUT:
{
  "action_id": "...",
  "execution_status": "SUCCESS",
  "module": "REMINDER",
  "result_data": {
    "reminder_id": "rem_123",
    "scheduled_at": "ISO8601"
  }
}
```
- Temps estimé: 10h
- Priorité: MOYENNE
- Dépendances: T3.3
- Livrable: wf_set_reminder fonctionnel

**T3.7 - Workflow Web Search (wf_web_search)**
```
Workflow recherche web

INPUT:
└── ActionJSON avec intent="web_search"

ÉTAPES:
1. Extraction Payload
   ├── query
   ├── search_type (web/images/news)
   ├── max_results
   └── language

2. Appel API Recherche
   ├── Google Custom Search API (ou autre)
   ├── Ou scraping simple (fallback)
   └── Timeout 10 secondes

3. Parse Résultats
   ├── Extraire top N résultats
   ├── Format: title, url, snippet
   └── Générer résumé

4. Logging
   └── wf_log_event

OUTPUT:
{
  "action_id": "...",
  "execution_status": "SUCCESS",
  "module": "WEB",
  "result_data": {
    "query": "...",
    "results": [
      {"title": "...", "url": "...", "snippet": "..."}
    ],
    "summary": "..."
  }
}
```
- Temps estimé: 8h
- Priorité: BASSE (optionnel)
- Dépendances: T3.3
- Livrable: wf_web_search fonctionnel

**T3.8 - Workflow Log Event (wf_log_event)**
```
Workflow logging centralisé

INPUT:
├── Logs de tous les autres workflows
└── Format structuré JSON

ÉTAPES:
1. Réception Event
   ├── action_id
   ├── workflow_name
   ├── status
   ├── timestamp
   └── details

2. Stockage
   ├── Fichier logs/n8n_events.log
   ├── Format: JSON Lines (un JSON par ligne)
   └── Rotation quotidienne

3. Indexation (optionnel)
   └── Elasticsearch ou base simple

OUTPUT:
└── Confirmation logging
```
- Temps estimé: 6h
- Priorité: MOYENNE
- Dépendances: T3.3
- Livrable: wf_log_event fonctionnel

---

#### Phase 3: Tests & Intégration (Semaines 5-6)

**T3.9 - Tests Workflows n8n**
```
Tests à effectuer:
├── Test wf_action_router avec mock ActionJSON
├── Test wf_control_iot avec mock MQTT
├── Test wf_send_email avec SMTP test
├── Test wf_set_reminder
├── Test wf_web_search
├── Test wf_log_event
└── Tests erreurs et timeouts
```
- Temps estimé: 10h
- Priorité: HAUTE
- Dépendances: T3.3-T3.8
- Livrable: Tous workflows testés

**T3.10 - Intégration Backend ↔ n8n**
```
Collaboration avec Vous:
├── Tester envoi ActionJSON depuis Backend
├── Tester réception callbacks
├── Valider formats JSON
└── Corrections bugs
```
- Temps estimé: 8h
- Priorité: CRITIQUE
- Dépendances: Vous T1.11
- Livrable: Intégration réussie

**T3.11 - Intégration n8n ↔ ESP32**
```
Collaboration avec Omar:
├── Tester publication MQTT commandes
├── Tester réception statuts ESP32
├── Valider formats JSON
└── Gérer timeouts
```
- Temps estimé: 6h
- Priorité: CRITIQUE
- Dépendances: Omar T4.3
- Livrable: Communication MQTT stable

---

### 5.3 Récapitulatif Tâches AMINE

| Phase | Tâches | Temps Total | Priorité |
|-------|--------|-------------|----------|
| **Phase 1** | T3.1 → T3.2 | 8h | CRITIQUE |
| **Phase 2** | T3.3 → T3.8 | 56h | CRITIQUE |
| **Phase 3** | T3.9 → T3.11 | 24h | CRITIQUE |
| **TOTAL** | 11 tâches | **88h** | - |

**Estimation : 2.5 semaines à temps plein (38h/sem)**

---

## 6. Personne 3 - Omar

### 6.1 Rôle et Responsabilités

**Rôle principal :** Développeur Embarqué + Spécialiste IoT

**Responsabilités :**
- ✅ Tout le code ESP32 (C++)
- ✅ Communication MQTT (commandes + statuts)
- ✅ Gestion audio (enregistrement + playback)
- ✅ Contrôle hardware (relais, capteurs)
- ✅ Tests sur matériel réel
- ✅ Documentation hardware

---

### 6.2 Tâches Détaillées

#### Phase 1: Setup ESP32 (Semaine 1)

**T4.1 - Setup Environnement Développement**
```bash
Installation:
├── Arduino IDE ou PlatformIO
├── ESP32 Board Manager
├── Bibliothèques:
│   ├── PubSubClient (MQTT)
│   ├── ArduinoJson
│   ├── ESP8266Audio (audio playback)
│   └── WiFi / WiFiClientSecure
└── Pilotes USB ESP32
```
- Temps estimé: 3h
- Priorité: CRITIQUE
- Dépendances: Aucune
- Livrable: IDE prêt

**T4.2 - Configuration Hardware**
```
Matériel nécessaire:
├── ESP32 DevKit
├── Module I2S (MAX98357A pour audio out)
├── Microphone I2S (INMP441)
├── Relais 5V (contrôle lampe)
├── LED test
├── Capteur DHT22 (température/humidité)
└── Câbles, breadboard

Schéma connexions:
├── GPIO pins mapping
├── I2S audio pins
├── Relais control pin
└── Sensor pins
```
- Temps estimé: 4h
- Priorité: HAUTE
- Dépendances: T4.1
- Livrable: Hardware assemblé et testé

---

#### Phase 2: Développement ESP32 (Semaines 2-4)

**T4.3 - MQTT Client (mqtt_client.cpp)**
```cpp
// Fichier: esp32/mqtt_client.cpp
// Communication MQTT bidirectionnelle

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

class MQTTClientESP32 {
private:
    WiFiClient wifiClient;
    PubSubClient mqttClient;
    String deviceId;
    
    // Topics
    String commandTopic;      // esp32/command/{device_id}
    String statusTopic;       // esp32/status/{device_id}
    String audioUploadTopic;  // esp32/audio/upload/{device_id}
    String audioResponseTopic;// esp32/audio/response/{device_id}

public:
    MQTTClientESP32(String devId, String broker, int port);
    
    void connect();
    void disconnect();
    void loop();  // À appeler dans loop() principal
    
    // Callbacks
    void onCommandReceived(void (*callback)(JsonDocument&));
    void onAudioResponseReceived(void (*callback)(JsonDocument&));
    
    // Publications
    void publishStatus(JsonDocument& status);
    void publishAudioUpload(String audioBase64, JsonDocument& metadata);
    
private:
    void messageCallback(char* topic, byte* payload, unsigned int length);
    void reconnect();
};

// Implémentation

MQTTClientESP32::MQTTClientESP32(String devId, String broker, int port) {
    deviceId = devId;
    commandTopic = "esp32/command/" + deviceId;
    statusTopic = "esp32/status/" + deviceId;
    audioUploadTopic = "esp32/audio/upload/" + deviceId;
    audioResponseTopic = "esp32/audio/response/" + deviceId;
    
    mqttClient.setServer(broker.c_str(), port);
    mqttClient.setCallback([this](char* topic, byte* payload, unsigned int length) {
        this->messageCallback(topic, payload, length);
    });
}

void MQTTClientESP32::connect() {
    // Connexion WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected");
    
    // Connexion MQTT
    reconnect();
    
    // Souscription topics
    mqttClient.subscribe(commandTopic.c_str());
    mqttClient.subscribe(audioResponseTopic.c_str());
}

void MQTTClientESP32::messageCallback(char* topic, byte* payload, unsigned int length) {
    // Parser JSON (Section 9.2 ou 13.2 Fichier 02)
    StaticJsonDocument<2048> doc;
    DeserializationError error = deserializeJson(doc, payload, length);
    
    if (error) {
        Serial.println("JSON parse error");
        return;
    }
    
    String topicStr = String(topic);
    
    if (topicStr.startsWith("esp32/command/")) {
        // Commande reçue (Section 9.2)
        if (commandCallback != nullptr) {
            commandCallback(doc);
        }
    } else if (topicStr.startsWith("esp32/audio/response/")) {
        // Réponse audio reçue (Section 13.2)
        if (audioResponseCallback != nullptr) {
            audioResponseCallback(doc);
        }
    }
}

void MQTTClientESP32::publishStatus(JsonDocument& status) {
    // Publication statut (Section 10.2 Fichier 02)
    String output;
    serializeJson(status, output);
    mqttClient.publish(statusTopic.c_str(), output.c_str());
}
```
- Temps estimé: 12h
- Priorité: CRITIQUE
- Dépendances: T4.1, T4.2
- Livrable: mqtt_client.cpp complet

**T4.4 - Device Manager (device_manager.cpp)**
```cpp
// Fichier: esp32/device_manager.cpp
// Gestion commandes hardware

#include <ArduinoJson.h>

class DeviceManager {
private:
    // Pins
    int relayPin;
    int ledPin;
    
public:
    DeviceManager(int relay, int led);
    
    void init();
    
    // Exécution commandes (Section 9.2 Fichier 02)
    JsonDocument executeCommand(JsonDocument& command);
    
private:
    JsonDocument executeRelayOn(String target);
    JsonDocument executeRelayOff(String target);
    JsonDocument executePWMSet(String target, int value);
    JsonDocument readSensor(String target, String type);
};

// Implémentation

JsonDocument DeviceManager::executeCommand(JsonDocument& command) {
    String commandType = command["command"].as<String>();
    String target = command["target"].as<String>();
    
    StaticJsonDocument<1024> result;
    result["command_id"] = command["command_id"];
    result["device_id"] = command["device_id"];
    
    unsigned long startTime = millis();
    
    if (commandType == "RELAY_ON") {
        result = executeRelayOn(target);
    } else if (commandType == "RELAY_OFF") {
        result = executeRelayOff(target);
    } else if (commandType == "PWM_SET") {
        int value = command["value"].as<int>();
        result = executePWMSet(target, value);
    } else if (commandType == "READ_SENSOR") {
        String type = command["value"].as<String>();
        result = readSensor(target, type);
    } else {
        result["status"] = "ERROR";
        result["error"]["code"] = "UNKNOWN_COMMAND";
        result["error"]["message"] = "Commande inconnue: " + commandType;
        result["timestamp"] = millis() / 1000;
        return result;
    }
    
    unsigned long executionTime = millis() - startTime;
    result["details"]["execution_time_ms"] = executionTime;
    result["timestamp"] = millis() / 1000;
    
    return result;
}

JsonDocument DeviceManager::executeRelayOn(String target) {
    StaticJsonDocument<1024> result;
    
    if (target == "RELAY_1") {
        digitalWrite(relayPin, HIGH);
        result["status"] = "SUCCESS";
        result["details"]["command_executed"] = "RELAY_ON";
        result["details"]["target_affected"] = target;
        result["details"]["relay_state"] = "ON";
    } else {
        result["status"] = "ERROR";
        result["error"]["code"] = "INVALID_TARGET";
        result["error"]["message"] = "Target inconnu: " + target;
    }
    
    return result;
}

// Autres méthodes similaires...
```
- Temps estimé: 10h
- Priorité: CRITIQUE
- Dépendances: T4.2, T4.3
- Livrable: device_manager.cpp complet

**T4.5 - Audio Handler (audio_handler.cpp)**
```cpp
// Fichier: esp32/audio_handler.cpp
// Gestion audio (enregistrement + playback)

#include <driver/i2s.h>
#include <base64.h>

class AudioHandler {
private:
    // Configuration I2S
    const int sampleRate = 16000;
    const int bitsPerSample = 16;
    const int channels = 1;
    
    // Buffers
    uint8_t* recordBuffer;
    size_t recordBufferSize;
    
public:
    AudioHandler();
    ~AudioHandler();
    
    void init();
    
    // Enregistrement (Section 12.2 Fichier 02)
    JsonDocument recordAudio(int durationMs);
    
    // Playback (Section 13.2 Fichier 02)
    bool playAudio(String audioBase64, String format);
    
private:
    void initI2SMicrophone();
    void initI2SSpeaker();
    String encodeBase64(uint8_t* data, size_t length);
};

// Implémentation

JsonDocument AudioHandler::recordAudio(int durationMs) {
    StaticJsonDocument<4096> result;
    
    // Calcul taille buffer
    size_t bytesNeeded = (sampleRate * bitsPerSample / 8 * channels) * (durationMs / 1000);
    
    if (recordBuffer == nullptr || recordBufferSize < bytesNeeded) {
        recordBuffer = (uint8_t*)realloc(recordBuffer, bytesNeeded);
        recordBufferSize = bytesNeeded;
    }
    
    // Enregistrement I2S
    size_t bytesRead = 0;
    unsigned long startTime = millis();
    
    while (millis() - startTime < durationMs) {
        size_t bytesToRead = min((size_t)1024, recordBufferSize - bytesRead);
        size_t readNow = 0;
        
        i2s_read(I2S_NUM_0, recordBuffer + bytesRead, bytesToRead, &readNow, portMAX_DELAY);
        bytesRead += readNow;
        
        if (bytesRead >= recordBufferSize) break;
    }
    
    // Encodage base64
    String audioBase64 = encodeBase64(recordBuffer, bytesRead);
    
    // Construction JSON (Section 12.2 Fichier 02)
    result["device_id"] = DEVICE_ID;
    result["audio_data"] = audioBase64;
    result["audio_format"] = "wav";
    
    JsonObject metadata = result.createNestedObject("audio_metadata");
    metadata["sample_rate"] = sampleRate;
    metadata["bit_depth"] = bitsPerSample;
    metadata["channels"] = channels;
    metadata["duration_ms"] = durationMs;
    metadata["size_bytes"] = bytesRead;
    
    JsonObject recordingContext = result.createNestedObject("recording_context");
    recordingContext["wake_word_detected"] = true;
    recordingContext["recording_quality"] = "high";
    
    result["timestamp"] = "2026-01-20T10:00:00Z";  // Format ISO8601
    
    return result;
}

bool AudioHandler::playAudio(String audioBase64, String format) {
    // Décodage base64
    size_t decodedLength = base64_dec_len(audioBase64.c_str(), audioBase64.length());
    uint8_t* decodedAudio = (uint8_t*)malloc(decodedLength);
    base64_decode((char*)decodedAudio, audioBase64.c_str(), audioBase64.length());
    
    // Playback I2S
    size_t bytesWritten = 0;
    i2s_write(I2S_NUM_0, decodedAudio, decodedLength, &bytesWritten, portMAX_DELAY);
    
    free(decodedAudio);
    
    return bytesWritten == decodedLength;
}
```
- Temps estimé: 14h
- Priorité: HAUTE
- Dépendances: T4.2
- Livrable: audio_handler.cpp complet

**T4.6 - Main Program (main.cpp)**
```cpp
// Fichier: esp32/main.cpp
// Programme principal ESP32

#include "mqtt_client.h"
#include "device_manager.h"
#include "audio_handler.h"
#include "config.h"

// Instances globales
MQTTClientESP32* mqttClient;
DeviceManager* deviceManager;
AudioHandler* audioHandler;

// État
bool isRecording = false;
bool wakeWordDetected = false;

void setup() {
    Serial.begin(115200);
    
    // Initialisation modules
    mqttClient = new MQTTClientESP32(DEVICE_ID, MQTT_BROKER, MQTT_PORT);
    deviceManager = new DeviceManager(RELAY_PIN, LED_PIN);
    audioHandler = new AudioHandler();
    
    deviceManager->init();
    audioHandler->init();
    mqttClient->connect();
    
    // Callbacks
    mqttClient->onCommandReceived(handleCommand);
    mqttClient->onAudioResponseReceived(handleAudioResponse);
    
    Serial.println("ESP32 prêt");
}

void loop() {
    // MQTT loop
    mqttClient->loop();
    
    // Détection wake word (simplifiée)
    if (!isRecording && detectWakeWord()) {
        wakeWordDetected = true;
        startRecording();
    }
    
    // Autres tâches...
    delay(10);
}

void handleCommand(JsonDocument& command) {
    // Traitement commande (Section 9.2 Fichier 02)
    String commandType = command["command"].as<String>();
    
    Serial.print("Commande reçue: ");
    Serial.println(commandType);
    
    if (commandType == "PLAY_AUDIO") {
        // Playback audio
        String audioBase64 = command["value"].as<String>();
        bool success = audioHandler->playAudio(audioBase64, "mp3");
        
        // Envoi statut
        StaticJsonDocument<512> status;
        status["command_id"] = command["command_id"];
        status["device_id"] = DEVICE_ID;
        status["status"] = success ? "SUCCESS" : "ERROR";
        status["timestamp"] = millis() / 1000;
        
        mqttClient->publishStatus(status);
        
    } else {
        // Commandes hardware
        JsonDocument result = deviceManager->executeCommand(command);
        mqttClient->publishStatus(result);
    }
}

void handleAudioResponse(JsonDocument& response) {
    // Réception réponse audio (Section 13.2 Fichier 02)
    String audioBase64 = response["audio_data"].as<String>();
    String format = response["audio_format"].as<String>();
    
    Serial.println("Réponse audio reçue");
    audioHandler->playAudio(audioBase64, format);
}

void startRecording() {
    isRecording = true;
    Serial.println("Enregistrement...");
    
    // Enregistrer 3 secondes
    JsonDocument audioData = audioHandler->recordAudio(3000);
    
    // Upload vers Backend Python (Section 12.2 Fichier 02)
    mqttClient->publishAudioUpload(
        audioData["audio_data"].as<String>(),
        audioData
    );
    
    isRecording = false;
    wakeWordDetected = false;
}

bool detectWakeWord() {
    // TODO: Implémenter détection wake word réelle
    // Pour l'instant: bouton physique ou timer
    return digitalRead(BUTTON_PIN) == LOW;
}
```
- Temps estimé: 12h
- Priorité: CRITIQUE
- Dépendances: T4.3, T4.4, T4.5
- Livrable: main.cpp complet

**T4.7 - Configuration (config.h)**
```cpp
// Fichier: esp32/config.h
// Configuration ESP32

#ifndef CONFIG_H
#define CONFIG_H

// Device ID
#define DEVICE_ID "esp32_kitchen"

// WiFi
#define WIFI_SSID "votre_ssid"
#define WIFI_PASSWORD "votre_mot_de_passe"

// MQTT
#define MQTT_BROKER "192.168.1.100"  // IP du broker
#define MQTT_PORT 1883
#define MQTT_USER ""  // Si authentification
#define MQTT_PASSWORD ""

// Pins Hardware
#define RELAY_PIN 25
#define LED_PIN 2
#define BUTTON_PIN 0  // Boot button pour wake word test
#define DHT22_PIN 4

// Pins I2S Microphone
#define I2S_MIC_SERIAL_CLOCK 26
#define I2S_MIC_LEFT_RIGHT_CLOCK 22
#define I2S_MIC_SERIAL_DATA 21

// Pins I2S Speaker
#define I2S_SPK_SERIAL_CLOCK 14
#define I2S_SPK_LEFT_RIGHT_CLOCK 27
#define I2S_SPK_SERIAL_DATA 12

// Audio
#define SAMPLE_RATE 16000
#define BITS_PER_SAMPLE 16

#endif
```
- Temps estimé: 2h
- Priorité: HAUTE
- Dépendances: T4.2
- Livrable: config.h complet

---

#### Phase 3: Tests & Intégration (Semaines 5-6)

**T4.8 - Tests Hardware**
```
Tests à effectuer:
├── Test contrôle relais (ON/OFF)
├── Test PWM LED (intensité variable)
├── Test lecture capteur DHT22
├── Test enregistrement audio (qualité)
├── Test playback audio (volume, clarté)
├── Test wake word detection
└── Tests stabilité (uptime 24h)
```
- Temps estimé: 10h
- Priorité: HAUTE
- Dépendances: T4.6
- Livrable: Hardware validé

**T4.9 - Tests MQTT**
```
Tests communication:
├── Test publication statuts
├── Test réception commandes
├── Test upload audio
├── Test réception audio réponse
├── Tests déconnexion/reconnexion
└── Tests QoS et latence
```
- Temps estimé: 6h
- Priorité: CRITIQUE
- Dépendances: T4.3, Amine T3.4
- Livrable: Communication MQTT stable

**T4.10 - Intégration avec n8n**
```
Collaboration avec Amine:
├── Tester commandes depuis n8n
├── Valider formats JSON
├── Tester timeouts
└── Optimiser latence
```
- Temps estimé: 6h
- Priorité: CRITIQUE
- Dépendances: Amine T3.11
- Livrable: Intégration réussie

---

### 6.3 Récapitulatif Tâches OMAR

| Phase | Tâches | Temps Total | Priorité |
|-------|--------|-------------|----------|
| **Phase 1** | T4.1 → T4.2 | 7h | CRITIQUE |
| **Phase 2** | T4.3 → T4.7 | 50h | CRITIQUE |
| **Phase 3** | T4.8 → T4.10 | 22h | CRITIQUE |
| **TOTAL** | 10 tâches | **79h** | - |

**Estimation : 2 semaines à temps plein (38h/sem)**

---

## 9. Matrice des Dépendances

### 9.1 Vue Globale des Dépendances

```
Semaine 1 (Setup):
├── MONTASSAR (VOUS): T1.1-T1.4 + T1.21-T1.22 (structure + setup AI)
├── AMINE: T3.1-T3.2 (setup n8n, intégrations)
└── OMAR: T4.1-T4.2 (setup ESP32, hardware)
   ↓ Tous indépendants

Semaines 2-4 (Développement Core):
├── MONTASSAR (VOUS): T1.5-T1.27 (Backend Python COMPLET: Core + AI)
│   ├── Phase Core: T1.5-T1.13 (agent, security, clients)
│   ├── Phase AI: T1.21-T1.26 (classifier, STT, TTS, LLM)
│   └── Tout intégré en interne - pas de dépendances externes
│
├── AMINE: T3.3-T3.8 (Workflows n8n)
│   ├── Interface: MONTASSAR T1.11 (n8n_client)
│   └── Interface: OMAR T4.3 (MQTT)
│
└── OMAR: T4.3-T4.7 (Code ESP32)
    └── Interface: AMINE T3.4 (wf_control_iot)

Semaines 5-6 (Intégration):
├── MONTASSAR (VOUS): T1.14 (tests internes Backend)
├── MONTASSAR + AMINE: T1.15 (intégration Backend ↔ n8n)
├── AMINE + OMAR: T3.11 (intégration n8n ↔ ESP32)
└── MONTASSAR (VOUS): T1.16 (tests E2E)

Semaines 7-8 (Documentation):
└── MONTASSAR (VOUS): T1.17-T1.18 (+ aide de tous)
```

### 9.2 D\u00e9pendances Inter-Modules Critiques

| Semaine | Point Sync | Participants | Objectif |
|---------|-----------|--------------|----------|
| **S1** | Fin Setup | Tous | Valider environnements prêts |
| **S2** | Interfaces JSON | Vous + Montassar | Valider Classifier + LLM formats |
| **S3** | Interfaces JSON | Vous + Amine | Valider ActionJSON → n8n |
| **S3** | Interfaces JSON | Amine + Omar | Valider Commandes MQTT |
| **S4** | Review Code | Tous | Review croisé du code |
| **S5** | Intégration 1 | Vous + Montassar | Tests Backend ↔ AI |
| **S5** | Intégration 2 | Vous + Amine | Tests Backend ↔ n8n |
| **S6** | Intégration 3 | Amine + Omar | Tests n8n ↔ ESP32 |
| **S6** | Tests E2E | Tous | Tests scénarios complets |
| **S7** | Documentation | Tous | Rédaction collaborative |
| **S8** | Répétition | Tous | Préparation soutenance |

---

## 8. Planning par Sprint

### 8.1 Sprint 1 - Setup & Architecture (Semaine 1)

**Objectif :** Environnements prêts + Structure projet

| Membre | Tâches | Heures | Livrables |
|--------|--------|--------|-----------|
| **MONTASSAR (VOUS)** | T1.1-T1.4, T1.21-T1.22 | 21h | Structure Backend + Setup AI complet |
| **AMINE** | T3.1-T3.2 | 8h | n8n installé, Intégrations testées |
| **OMAR** | T4.1-T4.2 | 7h | IDE prêt, Hardware assemblé |

**Réunion fin Sprint 1 (Vendredi) :**
- ✅ Tous les environnements fonctionnels
- ✅ Tests de communication basiques (ping/pong)
- ✅ Planning Sprint 2 détaillé

---

### 9.2 Sprint 2 - Modules Indépendants (Semaines 2-3)

**Objectif :** Développer modules indépendants en parallèle

| Membre | Tâches | Heures | Livrables |
|--------|--------|--------|-----------|
| **VOUS** | T1.5-T1.8 | 50h | API, Agent Core, State Manager, Security |
| **MONTASSAR** | T2.3-T2.6 | 44h | Classifier, STT, TTS, LLM Client |
| **AMINE** | T3.3-T3.5 | 32h | Workflows: Router, IoT, Email |
| **OMAR** | T4.3-T4.5 | 36h | MQTT, Device Manager, Audio Handler |

**Point Sync milieu Sprint 2 (Jeudi S2) :**
- Review formats JSON (Classifier, ActionJSON)
- Validation interfaces VOUS ↔ MONTASSAR

**Réunion fin Sprint 2 (Vendredi S3) :**
- ✅ Modules indépendants fonctionnels
- ✅ Tests unitaires passants
- ✅ Démo individuelle de chaque module

---

### 9.3 Sprint 3 - Intégration Interfaces (Semaines 4-5)

**Objectif :** Connecter les modules entre eux

| Membre | Tâches | Heures | Livrables |
|--------|--------|--------|-----------|
| **VOUS** | T1.9-T1.12 | 34h | Action Builder, Confirmation, n8n Client, MQTT |
| **MONTASSAR** | T2.7-T2.8 | 16h | LLM Server, Prompt Templates |
| **AMINE** | T3.6-T3.8 | 24h | Workflows: Reminder, Search, Logging |
| **OMAR** | T4.6-T4.7 | 14h | Main Program, Config |

**Point Sync milieu Sprint 3 (Jeudi S4) :**
- Tests interface Backend ↔ n8n
- Tests interface n8n ↔ ESP32

**Réunion fin Sprint 3 (Vendredi S5) :**
- ✅ Toutes les interfaces connectées
- ✅ Tests d'intégration passants
- ✅ Premier scénario E2E réussi (conversation simple)

---

### 9.4 Sprint 4 - Tests & Stabilisation (Semaine 6)

**Objectif :** Tests complets + Corrections bugs

| Membre | Tâches | Heures | Livrables |
|--------|--------|--------|-----------|
| **VOUS** | T1.13-T1.16 | 36h | Validators, Intégrations, Tests E2E |
| **MONTASSAR** | T2.9-T2.10 | 18h | Tests AI, Intégration Backend |
| **AMINE** | T3.9-T3.11 | 24h | Tests workflows, Intégrations |
| **OMAR** | T4.8-T4.10 | 22h | Tests hardware, Tests MQTT, Intégration |

**Tests E2E à valider :**
1. ✅ Conversation simple
2. ✅ Contrôle IoT (allumer lampe)
3. ✅ Envoi email
4. ✅ Annulation action
5. ✅ Gestion erreur (ESP32 offline)

**Réunion fin Sprint 4 (Vendredi S6) :**
- ✅ Tous les scénarios E2E passants
- ✅ Système stable (pas de crashes)
- ✅ Prêt pour documentation

---

### 9.5 Sprint 5 - Documentation & Soutenance (Semaines 7-8)

**Objectif :** Finaliser documentation + Préparer présentation

| Membre | Tâches | Heures | Livrables |
|--------|--------|--------|-----------|
| **VOUS** | T1.17-T1.18 | 22h | Doc technique complète, Slides |
| **MONTASSAR** | Doc AI | 8h | Documentation modules AI |
| **AMINE** | Doc n8n | 8h | Documentation workflows |
| **OMAR** | Doc ESP32 | 8h | Documentation hardware + schémas |

**Documents à produire :**
- README.md principal
- Guide installation
- Guide utilisation
- Architecture détaillée (diagrammes)
- Documentation API
- Vidéo démo système
- Slides présentation
- Rapport PCD final

**Réunion fin Sprint 5 (Vendredi S8) :**
- ✅ Documentation complète
- ✅ Répétition présentation
- ✅ Système prêt pour démo soutenance

---

## 10. Points de Synchronisation

### 10.1 Réunions Hebdomadaires

**Jour :** Lundi 10h (1h)

**Ordre du jour :**
1. Revue sprint précédent (20 min)
   - Chacun présente ce qui est terminé
   - Démos si possible
2. Blocages et difficultés (15 min)
   - Identifier problèmes
   - Répartir aide si nécessaire
3. Planning semaine (20 min)
   - Objectifs clairs pour chacun
   - Points de sync additionnels
4. Questions diverses (5 min)

---

### 10.2 Points de Sync Techniques (au besoin)

**Format :** Courts (30 min max), ciblés sur un sujet

**Exemples :**
- VOUS + MONTASSAR : Validation formats JSON Classifier
- VOUS + AMINE : Test envoi ActionJSON → n8n
- AMINE + OMAR : Test commandes MQTT
- TOUS : Review architecture globale

**Outil recommandé :** Discord/Teams + partage écran

---

### 10.3 Communication Asynchrone

**Outil :** Groupe Telegram/WhatsApp/Discord

**Règles :**
- Questions bloquantes : @mention personne concernée
- Updates quotidiens : 1 message fin de journée (optionnel)
- Bugs découverts : Décrire + partager logs
- Code review : Via pull requests (si Git utilisé)

---

## 7. Checklist de Validation

### 7.1 Checklist Individuelle par Module

#### Module Backend Python (VOUS + MONTASSAR)

```
Phase Setup:
☐ Structure projet créée
☐ config.py fonctionnel
☐ logger.py avec rotation
☐ requirements.txt complet
☐ Tests environnement passants

Phase Core (VOUS):
☐ API FastAPI 4 routes fonctionnelles
☐ agent_core.py orchestration complète
☐ state_manager.py machine à états
☐ security_manager.py signatures HMAC
☐ action_builder.py 4 payloads
☐ confirmation_handler.py complet
☐ n8n_client.py envoi/callback
☐ mqtt_client.py audio
☐ validators.py tous flux

Phase AI (MONTASSAR):
☐ intent_classifier.py classification précise
☐ stt_engine.py transcription claire
☐ tts_engine.py audio synthèse
☐ llm_client.py analyse intention
☐ llm_server.py endpoints (optionnel)
☐ prompt_templates.py optimisés

Tests:
☐ Tests unitaires > 80% coverage
☐ Tests intégration Backend ↔ AI
☐ Validation formats JSON (Fichier 02)
```

#### Module n8n (AMINE)

```
Phase Setup:
☐ n8n installé et accessible
☐ SMTP configuré et testé
☐ MQTT broker connecté
☐ Credentials sécurisées

Phase Workflows:
☐ wf_action_router validation + routage
☐ wf_control_iot commandes ESP32
☐ wf_send_email envoi SMTP
☐ wf_set_reminder planification
☐ wf_web_search API recherche
☐ wf_log_event stockage logs

Tests:
☐ Tests chaque workflow isolé
☐ Tests avec mock ActionJSON
☐ Tests callbacks vers Backend
☐ Validation formats JSON (Fichier 02)
☐ Tests timeouts et erreurs
```

#### Module ESP32 (OMAR)

```
Phase Setup:
☐ IDE configuré
☐ Hardware assemblé et testé
☐ Pins mappés correctement
☐ WiFi + MQTT connexion stable

Phase Développement:
☐ mqtt_client.cpp pub/sub fonctionnel
☐ device_manager.cpp contrôle relais
☐ device_manager.cpp lecture capteurs
☐ audio_handler.cpp enregistrement
☐ audio_handler.cpp playback
☐ main.cpp intégration complète
☐ config.h paramètres corrects

Tests:
☐ Test contrôle relais ON/OFF
☐ Test PWM LED intensité
☐ Test lecture capteur DHT22
☐ Test enregistrement audio qualité
☐ Test playback audio volume
☐ Test MQTT latence < 500ms
☐ Validation formats JSON (Fichier 02)
☐ Test stabilité 24h uptime
```

---

### 7.2 Checklist Intégration Globale

```
Intégration Backend ↔ AI:
☐ Classification conversation/action fonctionne
☐ LLM répond correctement (intention + entités)
☐ STT transcription précise (français)
☐ TTS audio clair et naturel
☐ Formats JSON respectés

Intégration Backend ↔ n8n:
☐ Envoi ActionJSON CONFIRMED vers n8n
☐ n8n valide signature HMAC
☐ n8n route correctement par intent
☐ Callbacks reçus par Backend
☐ Formats JSON respectés

Intégration n8n ↔ ESP32:
☐ Commandes MQTT reçues par ESP32
☐ ESP32 exécute commandes correctement
☐ Statuts MQTT reçus par n8n
☐ Latence acceptable (< 1s)
☐ Formats JSON respectés

Intégration ESP32 ↔ Backend:
☐ Upload audio vers Backend
☐ Réception audio réponse sur ESP32
☐ Qualité audio acceptable
☐ Formats JSON respectés
```

---

### 7.3 Checklist Scénarios End-to-End

```
Scénario 1: Conversation Simple
☐ Wake word détecté
☐ Audio enregistré et uploadé
☐ STT transcription correcte
☐ Classification = "conversation"
☐ LLM génère réponse appropriée
☐ TTS synthèse vocale
☐ Audio réponse joué sur ESP32
☐ Durée totale < 5 secondes

Scénario 2: Contrôle IoT (Allumer Lampe)
☐ Wake word détecté
☐ Commande vocale "Allume la lampe de la cuisine"
☐ STT transcription correcte
☐ Classification = "action"
☐ LLM extrait intent="control_iot", entities correctes
☐ ActionJSON DRAFT construite
☐ Demande confirmation utilisateur
☐ Utilisateur confirme (vocal)
☐ ActionJSON CONFIRMED signée
☐ Envoi vers n8n
☐ n8n route vers wf_control_iot
☐ Commande MQTT envoyée à ESP32
☐ ESP32 active relais
☐ Statut SUCCESS retourné
☐ Backend notifié
☐ Confirmation vocale à l'utilisateur
☐ Durée totale < 10 secondes

Scénario 3: Envoi Email
☐ Commande vocale "Envoie un email à Jean..."
☐ Classification = "action"
☐ LLM extrait intent="send_email", entities
☐ ActionJSON construite avec payload email
☐ Confirmation utilisateur
☐ Envoi vers n8n
☐ n8n route vers wf_send_email
☐ Email envoyé via SMTP
☐ Confirmation réception message_id
☐ Notification utilisateur
☐ Durée totale < 15 secondes

Scénario 4: Annulation Action
☐ Commande action initiée
☐ Demande confirmation
☐ Utilisateur dit "Non, annule"
☐ Parser détecte "cancel"
☐ State = CANCELED
☐ Aucun envoi vers n8n
☐ Confirmation annulation vocale

Scénario 5: Gestion Erreur (ESP32 Offline)
☐ Commande control_iot
☐ Confirmation utilisateur
☐ Envoi vers n8n
☐ n8n publie MQTT
☐ ESP32 ne répond pas (timeout 5s)
☐ n8n détecte timeout
☐ Callback ERROR vers Backend
☐ Backend log erreur
☐ Notification erreur vocale à utilisateur
☐ State = FAILED
```

---

### 11.4 Checklist Pré-Soutenance

```
Documentation:
☐ README.md clair et complet
☐ Guide installation testé sur machine vierge
☐ Architecture diagrams (Flux JSON, Modules)
☐ Documentation API (Swagger/Postman)
☐ Schémas hardware ESP32
☐ Rapport PCD final

Démonstration:
☐ Vidéo démo (2-3 min) système complet
☐ Slides présentation (15-20 slides)
☐ Environnement démo stable
☐ Scénarios démo répétés (3x minimum)
☐ Plan B si WiFi/Hardware fail

Tests Finaux:
☐ Tous les tests unitaires passent
☐ Tous les tests intégration passent
☐ Tous les scénarios E2E passent
☐ Système stable (uptime 48h sans crash)
☐ Performance acceptable (latence, mémoire)

Préparation Q&A:
☐ Questions anticipées listées
☐ Réponses préparées
☐ Chaque membre connaît sa partie
☐ Répartition présentation claire
```

---

## 📝 Conclusion du Mapping

Ce document définit la **distribution complète des tâches** entre les **3 membres de l'équipe** pour le projet PCD - Agent Intelligent Embarqué.

### Résumé par Personne

| Membre | Heures Totales | Tâches | Modules Principaux |
|--------|---------------|--------|-------------------|
| **MONTASSAR (VOUS)** | 241h | 28 | Backend Python COMPLET (Core + AI/LLM) + Intégration + Documentation |
| **AMINE** | 88h | 11 | n8n Workflows + Orchestration |
| **OMAR** | 79h | 10 | ESP32 + MQTT + Audio + Hardware |
| **TOTAL** | **408h** | **49** | **3 modules complets** |

### Durée Estimée

- **Montassar** : 6-7 semaines (charge importante car vous gérez TOUT le Backend Python)
- **Amine** : 2.5 semaines 
- **Omar** : 2.5 semaines
- **Phase intégration** : 2 semaines (tous ensemble)
- **Phase documentation** : 2 semaines (tous ensemble)
- **TOTAL** : **8-10 semaines**

### Points Clés de Succès

✅ **Indépendance maximale** : Chacun peut développer en parallèle  
✅ **Interfaces JSON claires** : Contrats définis (Fichier 02)  
✅ **Points de sync réguliers** : Éviter les blocages  
✅ **Tests continus** : Validation progressive  
✅ **Documentation au fil de l'eau** : Pas de rush final  
✅ **Montassar centralise Backend** : Architecture cohérente

**Bon courage à toute l'équipe ! 🚀**

---

**Document créé le : 20 janvier 2026**  
**Version : 1.1 - Distribution Équipe CORRIGÉE (3 personnes)**  
**Statut : PRÊT pour exécution**
