# 🏗️ Architecture Technique Complète et Consolidée
## Projet PCD – Agent Intelligent Embarqué

**Version :** 2.0 Consolidée  
**Date :** 20 janvier 2026  
**Statut :** Document de référence technique officiel

---

## 📋 Table des Matières

1. [Vue d'ensemble de l'organisation du projet](#1-vue-densemble-de-lorganisation-du-projet)
2. [Principe fondamental – Séparation Conversation / Action](#2-principe-fondamental--séparation-conversation--action)
3. [Module 1 – Backend Python (Agent Intelligent)](#3-module-1--backend-python-agent-intelligent)
4. [Module 2 – Moteur IA / LLM](#4-module-2--moteur-ia--llm)
5. [Module 3 – Orchestrateur n8n](#5-module-3--orchestrateur-n8n)
6. [Module 4 – Système embarqué ESP32](#6-module-4--système-embarqué-esp32)
7. [Gestion complète des flux JSON entre modules](#7-gestion-complète-des-flux-json-entre-modules)
8. [Description des interactions entre modules](#8-description-des-interactions-entre-modules)
9. [Mise à jour du cahier des charges (Addendum)](#9-mise-à-jour-du-cahier-des-charges-addendum)
10. [Règles d'or du système](#10-règles-dor-du-système)

---

## 1. Vue d'ensemble de l'organisation du projet

Le projet **PCD – Agent Intelligent Embarqué** est structuré autour de **4 grands modules techniques**, chacun ayant une responsabilité claire et bien délimitée :

### 1.1 Les 4 modules principaux

| Module | Rôle | Responsabilité |
|--------|------|----------------|
| **Backend Python** | Cerveau du système | Décisions, coordination, gestion états |
| **Moteur IA / LLM** | Compréhension linguistique | Analyse NLP, extraction intentions |
| **Orchestrateur n8n** | Exécution contrôlée | Workflows, actions confirmées |
| **Système ESP32** | Exécution physique | IoT, capteurs, actionneurs |

### 1.2 Principes architecturaux fondamentaux

Chaque module est **indépendant**, **faiblement couplé**, et communique **exclusivement via des messages JSON standardisés**.

Cette architecture garantit :

✅ **Développement séparé** : chaque module peut être développé et testé indépendamment  
✅ **Maintenance facilitée** : modification d'un module sans impact sur les autres  
✅ **Évolutivité progressive** : ajout de nouvelles fonctionnalités sans refonte  
✅ **Conformité académique** : structure claire pour un PCD/PFE  
✅ **Traçabilité complète** : tous les échanges sont journalisés  
✅ **Sécurité renforcée** : séparation stricte intelligence / exécution

### 1.3 Schéma architectural global

```
┌─────────────────────────────────────────────────────────────────┐
│                         UTILISATEUR                              │
│                    (Commandes vocales/texte)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │       ESP32 (Interface)      │
              │  • Microphone + Haut-parleur │
              │  • Capteurs IoT              │
              │  • Transmission audio brute  │
              └──────────────┬───────────────┘
                             │ Audio/JSON
                             ▼
        ┌────────────────────────────────────────────┐
        │      BACKEND PYTHON (Cerveau)              │
        │  ┌──────────────────────────────────────┐  │
        │  │  1. STT (Speech-to-Text)             │  │
        │  │  2. Classification                   │  │
        │  │     ├─► Conversation → Réponse       │  │
        │  │     └─► Action → Pipeline            │  │
        │  │  3. LLM (Analyse linguistique)       │  │
        │  │  4. State Manager (DRAFT/CONFIRMED)  │  │
        │  │  5. Security Manager                 │  │
        │  │  6. Action Builder (JSON officiel)   │  │
        │  │  7. TTS (Text-to-Speech)             │  │
        │  └──────────────────────────────────────┘  │
        └────────────┬───────────────────────────────┘
                     │ ActionJSON confirmée
                     ▼
          ┌─────────────────────────┐
          │    MODULE LLM           │
          │  (Compréhension NLP)    │
          │  • Analyse intentions   │
          │  • Extraction entités   │
          │  • AUCUNE exécution     │
          └─────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │     ORCHESTRATEUR n8n          │
        │  • Validation JSON             │
        │  • Routage workflows           │
        │  • Exécution contrôlée         │
        │  ├─► wf_send_email             │
        │  ├─► wf_control_iot            │
        │  ├─► wf_web_search             │
        │  └─► wf_log_event              │
        └────────────┬───────────────────┘
                     │ Commandes physiques
                     ▼
              ┌─────────────────┐
              │   ESP32 (IoT)   │
              │  • Relais       │
              │  • Moteurs      │
              │  • LED          │
              │  • Capteurs     │
              └─────────────────┘
```

---

## 2. Principe fondamental – Séparation Conversation / Action

### 2.1 Introduction de la distinction

Le système introduit **explicitement** une séparation logique entre **deux types d'interactions utilisateur**, sans modifier l'architecture initiale.

Cette séparation est **ajoutée** au backend Python et reste **totalement compatible** avec :
- le moteur IA / LLM existant,
- l'orchestrateur n8n,
- le module ESP32.

### 2.2 Type A – Conversation sociale (Small Talk)

#### Définition
Interaction **sans impact réel** sur le système, destinée à établir une communication naturelle entre l'utilisateur et l'agent.

#### Exemples
- *"Bonjour, ça va ?"*
- *"Qui es-tu ?"*
- *"Que fais-tu en ce moment ?"*
- *"Raconte-moi une blague"*
- *"Quelle heure est-il ?"*

#### Caractéristiques techniques

| Aspect | Comportement |
|--------|--------------|
| **Action externe** | ❌ Aucune |
| **Orchestration n8n** | ❌ Jamais impliqué |
| **Modification état système** | ❌ Aucune |
| **Confirmation utilisateur** | ❌ Non nécessaire |
| **Traçabilité** | ✅ Journalisation simple |
| **Réponse** | ✅ Immédiate et conversationnelle |
| **Module traitement** | ✅ Backend Python uniquement |

#### Pipeline de traitement Conversation

```
Audio utilisateur
    ↓
ESP32 → Backend Python
    ↓
STT (Speech-to-Text)
    ↓
Classification → Type: CONVERSATION
    ↓
Module LLM (génération réponse sociale)
    ↓
TTS (Text-to-Speech)
    ↓
ESP32 → Utilisateur
    ↓
FIN (aucun workflow n8n)
```

#### Besoins fonctionnels satisfaits
- **BF1** : Communication naturelle
- **BF3** : Recherche d'informations simples
- **BF4** : Lecture/synthèse de contenu
- **BF13** : Suggestions contextuelles

---

### 2.3 Type B – Action intelligente

#### Définition
Interaction nécessitant une **exécution réelle**, interne ou externe au système, avec impact observable.

#### Exemples
- *"Envoie un email à amin"*
- *"Allume la lampe de la cuisine"*
- *"Rappelle-moi dans 30 minutes"*
- *"Recherche les horaires de train"*
- *"Quelle est la météo demain ?"*
- *"Éteins le climatiseur"*

#### Caractéristiques techniques

| Aspect | Comportement |
|--------|--------------|
| **Action externe** | ✅ Exécution réelle requise |
| **Orchestration n8n** | ✅ Toujours impliqué |
| **Modification état système** | ✅ Possible (domotique, BD, etc.) |
| **Confirmation utilisateur** | ✅ OBLIGATOIRE |
| **Traçabilité** | ✅ Journalisation complète |
| **Réponse** | ✅ Après exécution confirmée |
| **Sécurité** | ✅ Validation + signature |

#### Pipeline de traitement Action

```
Audio utilisateur
    ↓
ESP32 → Backend Python
    ↓
STT (Speech-to-Text)
    ↓
Classification → Type: ACTION
    ↓
Module LLM (extraction intention + entités)
    ↓
Action Builder → ActionJSON (état: DRAFT)
    ↓
Confirmation Handler → TTS → ESP32 → Utilisateur
    ↓
Réponse utilisateur (Oui/Non/Correction)
    ↓
Si OUI → État: CONFIRMED
Si NON → État: CANCELED (fin)
Si CORRECTION → Retour à DRAFT (mise à jour)
    ↓
ActionJSON CONFIRMED → Security Manager (signature)
    ↓
n8n Client → Envoi vers n8n
    ↓
n8n → Workflow spécialisé → Exécution
    ↓
n8n → Backend Python (résultat)
    ↓
Backend → TTS → ESP32 → Utilisateur
    ↓
FIN (journalisation complète)
```

#### Besoins fonctionnels satisfaits
- **BF2** : Exécution d'actions via instructions naturelles
- **BF5** : Envoi d'emails
- **BF6** : Appels vocaux
- **BF7** : Notifications intelligentes
- **BF8** : Rappels et alarmes
- **BF9** : Contrôle domotique
- **BF10** : Gestion permissions
- **BF11** : Personnalisation
- **BF12** : Historique interactions

---

### 2.4 Flux décisionnel global

```
┌─────────────────────────────────────────────────────────────────┐
│                      Commande utilisateur                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │  Wake word détecté │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  Enregistrement    │
                    │  audio segment     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  ESP32 → Backend   │
                    │  (transmission)    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  STT (Whisper)     │
                    │  Audio → Texte     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  CLASSIFICATION    │
                    │  Intent Classifier │
                    └─────────┬──────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌──────────────────────┐    ┌──────────────────────┐
    │  Type: CONVERSATION  │    │    Type: ACTION      │
    └──────────┬───────────┘    └──────────┬───────────┘
               │                            │
               ▼                            ▼
    ┌──────────────────────┐    ┌──────────────────────┐
    │  LLM                 │    │  LLM                 │
    │  Réponse sociale     │    │  Analyse intention   │
    └──────────┬───────────┘    │  + Extraction        │
               │                │  entités             │
               ▼                └──────────┬───────────┘
    ┌──────────────────────┐              │
    │  TTS                 │              ▼
    │  Génération vocale   │    ┌──────────────────────┐
    └──────────┬───────────┘    │  Action Builder      │
               │                │  ActionJSON (DRAFT)  │
               ▼                └──────────┬───────────┘
    ┌──────────────────────┐              │
    │  ESP32 → Utilisateur │              ▼
    └──────────────────────┘    ┌──────────────────────┐
                                │  Confirmation        │
                                │  Handler             │
                                └──────────┬───────────┘
                                           │
                              ┌────────────┴────────────┐
                              │                         │
                              ▼                         ▼
                    ┌──────────────────┐    ┌──────────────────┐
                    │  CONFIRMED       │    │  CANCELED        │
                    └────────┬─────────┘    └──────────────────┘
                             │                        │
                             ▼                        ▼
                    ┌──────────────────┐            FIN
                    │  Security Manager│
                    │  (signature)     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  n8n Client      │
                    │  (envoi webhook) │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  n8n Workflow    │
                    │  (exécution)     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Services        │
                    │  externes/ESP32  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Résultat →      │
                    │  Backend Python  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  TTS → ESP32     │
                    │  → Utilisateur   │
                    └──────────────────┘
```

---

## 3. Module 1 – Backend Python (Agent Intelligent)

### 3.1 Rôle du module

Le backend Python constitue le **cerveau central et décisionnel du système**. 

#### Responsabilités principales

Le backend Python **ne déclenche AUCUNE action réelle directement**, mais orchestre toute la logique décisionnelle et coordonne les autres modules.

| Responsabilité | Description | Composant |
|----------------|-------------|-----------|
| **Réception commandes** | Texte ou audio utilisateur | `agent_core.py` |
| **Conversion STT** | Audio → Texte | `stt_engine.py` |
| **Classification** | Conversation vs Action | `intent_classifier.py` |
| **Communication LLM** | Analyse linguistique | `llm_client.py` |
| **Gestion états** | DRAFT → CONFIRMED | `state_manager.py` |
| **Confirmation humaine** | Validation explicite | `confirmation_handler.py` |
| **Construction ActionJSON** | Format standardisé | `action_builder.py` |
| **Sécurité** | Auth + signature | `security_manager.py` |
| **Envoi vers n8n** | Actions confirmées uniquement | `n8n_client.py` |
| **Réception résultats** | Retours d'exécution | `n8n_client.py` |
| **Synthèse vocale** | Texte → Audio | `tts_engine.py` |
| **Communication ESP32** | Protocole MQTT/HTTP | `mqtt_client.py` |
| **Journalisation** | Traçabilité complète | `logger.py` |

---

### 3.2 Organisation des fichiers – Backend Python

```
backend/
│
├── main.py                          # Point d'entrée principal
├── config.py                        # Configuration centralisée
├── requirements.txt                 # Dépendances Python
├── .env.example                     # Template variables environnement
├── README.md                        # Documentation module
│
├── agent/                           # Cœur logique de l'agent
│   ├── __init__.py
│   ├── agent_core.py                # Logique principale agent
│   ├── state_manager.py             # Gestion cycle de vie commandes
│   ├── security_manager.py          # Authentification + sécurité
│   └── logger.py                    # Journalisation centralisée
│
├── ai/                              # Moteurs d'intelligence artificielle
│   ├── __init__.py
│   ├── llm_client.py                # Interface avec LLM
│   ├── stt_engine.py                # Speech-to-Text (Whisper)
│   └── tts_engine.py                # Text-to-Speech (gTTS/pyttsx3)
│
├── classifier/                      # ⭐ NOUVEAU MODULE
│   ├── __init__.py
│   └── intent_classifier.py         # Classification Conversation/Action
│
├── actions/                         # Gestion des actions
│   ├── __init__.py
│   ├── action_builder.py            # Construction ActionJSON
│   ├── confirmation_handler.py      # Gestion confirmation utilisateur
│   └── action_models.py             # Modèles de données actions
│
├── integrations/                    # Intégrations externes
│   ├── __init__.py
│   ├── n8n_client.py                # Communication avec n8n
│   └── mqtt_client.py               # Communication IoT (ESP32)
│
└── utils/                           # Utilitaires transversaux
    ├── __init__.py
    ├── validators.py                # Validation schémas JSON
    ├── serializers.py               # Sérialisation Python ↔ JSON
    └── exceptions.py                # Exceptions personnalisées
```

---

### 3.3 Description détaillée des fichiers – Backend Python

#### 📄 `main.py` – Point d'entrée principal

**Rôle** : Initialise et démarre le serveur HTTP de l'agent intelligent.

**Technologies** : FastAPI (recommandé) ou Flask

**Responsabilités** :
- Initialisation de l'application
- Configuration du logging
- Enregistrement des routes API
- Démarrage du serveur HTTP
- Gestion du cycle de vie de l'application

**Routes exposées** :

| Route | Méthode | Description | Corps de requête |
|-------|---------|-------------|------------------|
| `/command/text` | POST | Commande textuelle | `{"text": "...", "user_id": "..."}` |
| `/command/audio` | POST | Commande vocale | `{"audio": "base64...", "user_id": "..."}` |
| `/callback/n8n` | POST | Retour d'exécution n8n | `{"action_id": "...", "status": "...", ...}` |
| `/status` | GET | Santé du système | - |
| `/history` | GET | Historique commandes | `?user_id=...` |

**Code structure exemple** :

```python
from fastapi import FastAPI, HTTPException
from agent.agent_core import AgentCore
from agent.logger import Logger
from config import Config

app = FastAPI(title="Backend Python - Agent Intelligent")
logger = Logger()
agent = AgentCore()

@app.post("/command/text")
async def process_text_command(data: dict):
    """
    Traite une commande textuelle utilisateur.
    
    Args:
        data: {
            "text": str,
            "user_id": str,
            "language": str (optional)
        }
    
    Returns:
        {
            "response": str,
            "type": "conversation" | "action",
            "action_id": str (if type=action),
            "status": str
        }
    """
    try:
        result = await agent.process_command(
            text=data["text"],
            user_id=data["user_id"],
            language=data.get("language", "fr")
        )
        return result
    except Exception as e:
        logger.error(f"Error processing text command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/command/audio")
async def process_audio_command(data: dict):
    """
    Traite une commande vocale utilisateur.
    
    Args:
        data: {
            "audio": str (base64),
            "user_id": str,
            "format": str (optional, default: "wav")
        }
    
    Returns:
        {
            "response": str,
            "transcription": str,
            "type": "conversation" | "action",
            "action_id": str (if type=action),
            "status": str
        }
    """
    try:
        result = await agent.process_audio_command(
            audio_base64=data["audio"],
            user_id=data["user_id"],
            audio_format=data.get("format", "wav")
        )
        return result
    except Exception as e:
        logger.error(f"Error processing audio command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/callback/n8n")
async def handle_n8n_callback(data: dict):
    """
    Reçoit les résultats d'exécution de n8n.
    
    Args:
        data: {
            "action_id": str,
            "execution_status": str,
            "module": str,
            "details": dict,
            "timestamp": str
        }
    
    Returns:
        {"status": "received"}
    """
    try:
        await agent.handle_execution_result(data)
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error handling n8n callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Vérifie la santé du système."""
    return {
        "status": "online",
        "version": "2.0",
        "modules": {
            "llm": agent.check_llm_status(),
            "n8n": agent.check_n8n_status(),
            "mqtt": agent.check_mqtt_status()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level=Config.LOG_LEVEL
    )
```

---

#### 📄 `config.py` – Configuration centralisée

**Rôle** : Centralise toute la configuration du système.

**Responsabilités** :
- URLs des services externes
- Clés API et secrets (chargés depuis `.env`)
- Paramètres de sécurité
- Modes debug/production
- Timeouts et limites

**Code structure exemple** :

```python
import os
from dotenv import load_load_env()

class Config:
    """Configuration centralisée du backend Python."""
    
    # Serveur
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Module LLM
    LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:5000")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 30))
    
    # Module STT (Speech-to-Text)
    STT_ENGINE = os.getenv("STT_ENGINE", "whisper")  # whisper|google|vosk
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    
    # Module TTS (Text-to-Speech)
    TTS_ENGINE = os.getenv("TTS_ENGINE", "gtts")  # gtts|pyttsx3
    TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "fr")
    TTS_VOICE = os.getenv("TTS_VOICE", "female")
    
    # Module n8n
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/action")
    N8N_API_KEY = os.getenv("N8N_API_KEY", "")
    N8N_TIMEOUT = int(os.getenv("N8N_TIMEOUT", 60))
    
    # Module MQTT (ESP32)
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
    MQTT_TOPIC_COMMAND = os.getenv("MQTT_TOPIC_COMMAND", "esp32/command")
    MQTT_TOPIC_STATUS = os.getenv("MQTT_TOPIC_STATUS", "esp32/status")
    
    # Sécurité
    SECRET_KEY = os.getenv("SECRET_KEY", "changeme-secret-key-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", 3600))  # secondes
    
    # Base de données (optionnel)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///agent.db")
    
    # Classifier
    CLASSIFIER_METHOD = os.getenv("CLASSIFIER_METHOD", "rules")  # rules|ml|llm
    CLASSIFIER_THRESHOLD = float(os.getenv("CLASSIFIER_THRESHOLD", 0.8))
    
    # Limites
    MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", 10))
    MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 1000))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    
    # Journalisation
    LOG_FILE = os.getenv("LOG_FILE", "logs/agent.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))

# Validation au démarrage
def validate_config():
    """Valide la configuration critique."""
    required_vars = ["LLM_API_URL", "N8N_WEBHOOK_URL"]
    missing = [var for var in required_vars if not getattr(Config, var)]
    if missing:
        raise ValueError(f"Configuration incomplète: {', '.join(missing)}")

validate_config()
```

---

#### 📄 `requirements.txt` – Dépendances Python

```txt
# Framework Web
fastapi==0.108.0
uvicorn[standard]==0.25.0
python-multipart==0.0.6

# Intelligence Artificielle
openai==1.6.1
transformers==4.36.0
torch==2.1.0

# Speech Processing
openai-whisper==20231117
SpeechRecognition==3.10.0
gTTS==2.5.0
pyttsx3==2.90

# Communication
requests==2.31.0
paho-mqtt==1.6.1
httpx==0.26.0

# Base de données
sqlalchemy==2.0.23
alembic==1.13.0

# Sécurité
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Utilitaires
pydantic==2.5.0
python-json-logger==2.0.7
jsonschema==4.20.0
```

---

### 3.4 Dossier `agent/` – Cœur logique

#### 📄 `agent/agent_core.py` – Cerveau de l'agent

**Rôle** : Orchestre l'ensemble du processus de traitement des commandes utilisateur.

**Responsabilités** :
1. Réception commande utilisateur (texte/audio)
2. Appel du STT si nécessaire
3. Classification Conversation/Action
4. Routage vers le pipeline approprié
5. Coordination avec les autres modules
6. Gestion du cycle de vie complet

**Code structure détaillé** :

```python
from typing import Dict, Optional
from ai.stt_engine import STTEngine
from ai.tts_engine import TTSEngine
from ai.llm_client import LLMClient
from classifier.intent_classifier import IntentClassifier
from actions.action_builder import ActionBuilder
from actions.confirmation_handler import ConfirmationHandler
from integrations.n8n_client import N8NClient
from integrations.mqtt_client import MQTTClient
from agent.state_manager import StateManager
from agent.security_manager import SecurityManager
from agent.logger import Logger
from config import Config

class AgentCore:
    """
    Cœur logique de l'agent intelligent.
    Orchestre tous les modules et gère le flux décisionnel.
    """
    
    def __init__(self):
        """Initialise tous les composants de l'agent."""
        self.logger = Logger()
        self.stt = STTEngine()
        self.tts = TTSEngine()
        self.llm = LLMClient()
        self.classifier = IntentClassifier()
        self.action_builder = ActionBuilder()
        self.confirmation_handler = ConfirmationHandler()
        self.n8n_client = N8NClient()
        self.mqtt_client = MQTTClient()
        self.state_manager = StateManager()
        self.security_manager = SecurityManager()
        
        self.logger.info("AgentCore initialized successfully")
    
    async def process_command(
        self,
        text: str,
        user_id: str,
        language: str = "fr"
    ) -> Dict:
        """
        Point d'entrée principal pour traiter une commande textuelle.
        
        Args:
            text: Texte de la commande utilisateur
            user_id: Identifiant utilisateur
            language: Langue de la commande
        
        Returns:
            Dictionnaire avec la réponse et les métadonnées
        """
        self.logger.info(f"Processing text command: '{text}' from user {user_id}")
        
        try:
            # 1. Classification Conversation vs Action
            classification = await self.classifier.classify(text)
            
            self.logger.info(f"Classification result: {classification['type']} "
                           f"(confidence: {classification['confidence']})")
            
            # 2. Routage selon le type
            if classification["type"] == "conversation":
                return await self._handle_conversation(text, user_id, language)
            else:
                return await self._handle_action(text, user_id, language, classification)
        
        except Exception as e:
            self.logger.error(f"Error in process_command: {e}", exc_info=True)
            return {
                "response": "Désolé, une erreur s'est produite.",
                "status": "error",
                "error": str(e)
            }
    
    async def process_audio_command(
        self,
        audio_base64: str,
        user_id: str,
        audio_format: str = "wav"
    ) -> Dict:
        """
        Traite une commande vocale utilisateur.
        
        Args:
            audio_base64: Audio encodé en base64
            user_id: Identifiant utilisateur
            audio_format: Format audio (wav, mp3, etc.)
        
        Returns:
            Dictionnaire avec la réponse et les métadonnées
        """
        self.logger.info(f"Processing audio command from user {user_id}")
        
        try:
            # 1. Conversion Audio → Texte (STT)
            transcription = await self.stt.transcribe(audio_base64, audio_format)
            
            if not transcription or not transcription.strip():
                return {
                    "response": "Je n'ai pas compris, pouvez-vous répéter ?",
                    "status": "error",
                    "error": "empty_transcription"
                }
            
            self.logger.info(f"Transcription: '{transcription}'")
            
            # 2. Traitement du texte transcrit
            result = await self.process_command(
                text=transcription,
                user_id=user_id,
                language="fr"
            )
            
            # 3. Ajout de la transcription au résultat
            result["transcription"] = transcription
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error in process_audio_command: {e}", exc_info=True)
            return {
                "response": "Erreur lors du traitement audio.",
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_conversation(
        self,
        text: str,
        user_id: str,
        language: str
    ) -> Dict:
        """
        Gère une interaction de type Conversation (Small Talk).
        Pipeline: LLM → TTS → Réponse immédiate
        
        Args:
            text: Texte de la conversation
            user_id: ID utilisateur
            language: Langue
        
        Returns:
            Réponse conversationnelle
        """
        self.logger.info(f"Handling conversation: '{text}'")
        
        try:
            # 1. Génération réponse par LLM (mode conversation)
            llm_response = await self.llm.generate_conversation_response(
                user_input=text,
                user_id=user_id,
                language=language
            )
            
            response_text = llm_response.get("response", "Je n'ai pas de réponse.")
            
            # 2. Génération audio (TTS)
            audio_response = await self.tts.synthesize(response_text, language)
            
            # 3. Journalisation conversation
            self.logger.log_conversation(
                user_id=user_id,
                input_text=text,
                response_text=response_text
            )
            
            # 4. Retour immédiat (pas d'orchestration n8n)
            return {
                "type": "conversation",
                "response": response_text,
                "audio": audio_response,
                "status": "completed"
            }
        
        except Exception as e:
            self.logger.error(f"Error handling conversation: {e}", exc_info=True)
            return {
                "response": "Désolé, je n'ai pas pu traiter votre message.",
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_action(
        self,
        text: str,
        user_id: str,
        language: str,
        classification: Dict
    ) -> Dict:
        """
        Gère une interaction de type Action.
        Pipeline: LLM → DRAFT → Confirmation → CONFIRMED → n8n
        
        Args:
            text: Texte de l'action
            user_id: ID utilisateur
            language: Langue
            classification: Résultat de la classification
        
        Returns:
            Résultat du traitement de l'action
        """
        self.logger.info(f"Handling action: '{text}'")
        
        try:
            # 1. Analyse linguistique par LLM
            llm_analysis = await self.llm.analyze_intent(
                user_input=text,
                language=language
            )
            
            if llm_analysis.get("confidence", 0) < Config.CLASSIFIER_THRESHOLD:
                return {
                    "response": "Je ne suis pas sûr d'avoir compris. Pouvez-vous reformuler ?",
                    "status": "low_confidence"
                }
            
            # 2. Construction ActionJSON (état: DRAFT)
            action_json = await self.action_builder.build_action(
                intent=llm_analysis["intent"],
                entities=llm_analysis["entities"],
                user_id=user_id,
                language=language
            )
            
            action_id = action_json["action_id"]
            
            # 3. Enregistrement de l'action en état DRAFT
            await self.state_manager.create_action(action_id, action_json, state="DRAFT")
            
            # 4. Génération de la confirmation
            confirmation_text = await self.confirmation_handler.generate_confirmation(
                action_json
            )
            
            confirmation_audio = await self.tts.synthesize(confirmation_text, language)
            
            self.logger.info(f"Action {action_id} en attente de confirmation")
            
            # 5. Retour pour confirmation utilisateur
            return {
                "type": "action",
                "action_id": action_id,
                "status": "awaiting_confirmation",
                "confirmation_text": confirmation_text,
                "confirmation_audio": confirmation_audio,
                "action_details": action_json
            }
        
        except Exception as e:
            self.logger.error(f"Error handling action: {e}", exc_info=True)
            return {
                "response": "Erreur lors du traitement de l'action.",
                "status": "error",
                "error": str(e)
            }
    
    async def confirm_action(
        self,
        action_id: str,
        user_response: str
    ) -> Dict:
        """
        Traite la réponse de confirmation de l'utilisateur.
        
        Args:
            action_id: ID de l'action
            user_response: Réponse utilisateur (oui/non/correction)
        
        Returns:
            Résultat de la confirmation
        """
        self.logger.info(f"Confirming action {action_id}: '{user_response}'")
        
        try:
            # 1. Récupération de l'action
            action = await self.state_manager.get_action(action_id)
            
            if not action:
                return {
                    "status": "error",
                    "error": "Action not found"
                }
            
            # 2. Analyse de la réponse
            response_type = await self.confirmation_handler.parse_response(
                user_response
            )
            
            if response_type == "confirm":
                # CONFIRMATION → Passage à CONFIRMED
                return await self._execute_confirmed_action(action_id, action)
            
            elif response_type == "cancel":
                # ANNULATION
                await self.state_manager.update_state(action_id, "CANCELED")
                return {
                    "status": "canceled",
                    "response": "Action annulée."
                }
            
            elif response_type == "correction":
                # CORRECTION → Retour à DRAFT
                # TODO: Implémenter logique de correction
                return {
                    "status": "correction_needed",
                    "response": "Quelle correction souhaitez-vous apporter ?"
                }
        
        except Exception as e:
            self.logger.error(f"Error confirming action: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _execute_confirmed_action(
        self,
        action_id: str,
        action_json: Dict
    ) -> Dict:
        """
        Exécute une action confirmée via n8n.
        
        Args:
            action_id: ID de l'action
            action_json: JSON de l'action
        
        Returns:
            Résultat de l'exécution
        """
        self.logger.info(f"Executing confirmed action {action_id}")
        
        try:
            # 1. Authentification et signature
            signed_action = await self.security_manager.sign_action(action_json)
            
            # 2. Mise à jour état → CONFIRMED
            await self.state_manager.update_state(action_id, "CONFIRMED")
            
            # 3. Envoi vers n8n
            n8n_response = await self.n8n_client.send_action(signed_action)
            
            # 4. Mise à jour état → EXECUTING
            await self.state_manager.update_state(action_id, "EXECUTING")
            
            self.logger.info(f"Action {action_id} sent to n8n successfully")
            
            return {
                "status": "executing",
                "action_id": action_id,
                "response": "Action en cours d'exécution...",
                "n8n_response": n8n_response
            }
        
        except Exception as e:
            self.logger.error(f"Error executing action: {e}", exc_info=True)
            await self.state_manager.update_state(action_id, "FAILED")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_execution_result(self, result_data: Dict) -> None:
        """
        Traite le résultat d'exécution renvoyé par n8n.
        
        Args:
            result_data: Données de résultat de n8n
        """
        action_id = result_data.get("action_id")
        execution_status = result_data.get("execution_status")
        
        self.logger.info(f"Received execution result for {action_id}: {execution_status}")
        
        try:
            if execution_status == "SUCCESS":
                await self.state_manager.update_state(action_id, "COMPLETED")
                # TODO: Notifier utilisateur du succès
            else:
                await self.state_manager.update_state(action_id, "FAILED")
                # TODO: Notifier utilisateur de l'échec
            
            # Journalisation du résultat
            await self.logger.log_execution_result(action_id, result_data)
        
        except Exception as e:
            self.logger.error(f"Error handling execution result: {e}", exc_info=True)
    
    # Méthodes de vérification d'état des modules
    
    def check_llm_status(self) -> str:
        """Vérifie la disponibilité du LLM."""
        try:
            # Ping LLM
            return "online"
        except:
            return "offline"
    
    def check_n8n_status(self) -> str:
        """Vérifie la disponibilité de n8n."""
        try:
            # Ping n8n
            return "online"
        except:
            return "offline"
    
    def check_mqtt_status(self) -> str:
        """Vérifie la connexion MQTT."""
        try:
            return "connected" if self.mqtt_client.is_connected() else "disconnected"
        except:
            return "error"
```

---

#### 📄 `agent/state_manager.py` – Gestion des états

**Rôle** : Gérer le cycle de vie complet des commandes et actions.

**États possibles** :

```
IDLE → DRAFT → CONFIRMED → EXECUTING → COMPLETED
                    ↓
                 CANCELED
                    ↓
                 FAILED
```

**Code structure détaillé** :

```python
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum

class ActionState(Enum):
    """États possibles d'une action."""
    IDLE = "idle"
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"

class StateManager:
    """
    Gère le cycle de vie et les états des actions.
    Maintient une base de données en mémoire (ou persistante) des actions.
    """
    
    def __init__(self):
        """Initialise le gestionnaire d'états."""
        # Base de données en mémoire (remplacer par DB réelle en production)
        self.actions: Dict[str, Dict] = {}
        self.state_history: Dict[str, List[Dict]] = {}
    
    async def create_action(
        self,
        action_id: str,
        action_json: Dict,
        state: str = "DRAFT"
    ) -> Dict:
        """
        Crée une nouvelle action avec son état initial.
        
        Args:
            action_id: ID unique de l'action
            action_json: JSON complet de l'action
            state: État initial (défaut: DRAFT)
        
        Returns:
            Action créée
        """
        action_data = {
            "action_id": action_id,
            "action_json": action_json,
            "state": state,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "history": [{
                "state": state,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "Action created"
            }]
        }
        
        self.actions[action_id] = action_data
        self.state_history[action_id] = action_data["history"]
        
        return action_data
    
    async def get_action(self, action_id: str) -> Optional[Dict]:
        """
        Récupère une action par son ID.
        
        Args:
            action_id: ID de l'action
        
        Returns:
            Données de l'action ou None
        """
        return self.actions.get(action_id)
    
    async def update_state(
        self,
        action_id: str,
        new_state: str,
        reason: str = ""
    ) -> Dict:
        """
        Met à jour l'état d'une action.
        
        Args:
            action_id: ID de l'action
            new_state: Nouvel état
            reason: Raison du changement d'état
        
        Returns:
            Action mise à jour
        """
        if action_id not in self.actions:
            raise ValueError(f"Action {action_id} not found")
        
        action = self.actions[action_id]
        old_state = action["state"]
        
        # Validation de la transition d'état
        if not self._is_valid_transition(old_state, new_state):
            raise ValueError(
                f"Invalid state transition: {old_state} → {new_state}"
            )
        
        # Mise à jour de l'état
        action["state"] = new_state
        action["updated_at"] = datetime.utcnow().isoformat()
        
        # Ajout dans l'historique
        history_entry = {
            "state": new_state,
            "previous_state": old_state,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason or f"State changed to {new_state}"
        }
        
        action["history"].append(history_entry)
        self.state_history[action_id].append(history_entry)
        
        return action
    
    def _is_valid_transition(self, old_state: str, new_state: str) -> bool:
        """
        Valide si une transition d'état est autorisée.
        
        Args:
            old_state: État actuel
            new_state: État cible
        
        Returns:
            True si la transition est valide
        """
        valid_transitions = {
            "IDLE": ["DRAFT"],
            "DRAFT": ["CONFIRMED", "CANCELED"],
            "CONFIRMED": ["EXECUTING", "CANCELED"],
            "EXECUTING": ["COMPLETED", "FAILED"],
            "COMPLETED": [],  # État terminal
            "CANCELED": [],   # État terminal
            "FAILED": ["DRAFT"]  # Permet de réessayer
        }
        
        return new_state in valid_transitions.get(old_state, [])
    
    async def get_actions_by_state(self, state: str) -> List[Dict]:
        """
        Récupère toutes les actions dans un état donné.
        
        Args:
            state: État recherché
        
        Returns:
            Liste des actions
        """
        return [
            action for action in self.actions.values()
            if action["state"] == state
        ]
    
    async def get_user_actions(self, user_id: str) -> List[Dict]:
        """
        Récupère toutes les actions d'un utilisateur.
        
        Args:
            user_id: ID utilisateur
        
        Returns:
            Liste des actions de l'utilisateur
        """
        return [
            action for action in self.actions.values()
            if action["action_json"].get("context", {}).get("user_id") == user_id
        ]
    
    async def get_state_history(self, action_id: str) -> List[Dict]:
        """
        Récupère l'historique complet des états d'une action.
        
        Args:
            action_id: ID de l'action
        
        Returns:
            Historique des états
        """
        return self.state_history.get(action_id, [])
    
    async def cleanup_old_actions(self, days: int = 30) -> int:
        """
        Nettoie les actions terminées depuis plus de X jours.
        
        Args:
            days: Nombre de jours
        
        Returns:
            Nombre d'actions supprimées
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        to_delete = []
        
        for action_id, action in self.actions.items():
            if action["state"] in ["COMPLETED", "CANCELED", "FAILED"]:
                updated_at = datetime.fromisoformat(action["updated_at"])
                if updated_at < cutoff_date:
                    to_delete.append(action_id)
        
        for action_id in to_delete:
            del self.actions[action_id]
            del self.state_history[action_id]
        
        return len(to_delete)
```

---

#### 📄 `agent/security_manager.py` – Sécurité et authentification

**Rôle** : Assurer la sécurité du système (authentification, signatures, validation).

**Code structure détaillé** :

```python
import hashlib
import hmac
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from config import Config

class SecurityManager:
    """
    Gère la sécurité du système :
    - Authentification utilisateur
    - Signature des actions
    - Validation des permissions
    """
    
    def __init__(self):
        """Initialise le gestionnaire de sécurité."""
        self.secret_key = Config.SECRET_KEY
        self.algorithm = Config.JWT_ALGORITHM
    
    def generate_jwt_token(self, user_id: str, auth_level: int = 1) -> str:
        """
        Génère un token JWT pour un utilisateur.
        
        Args:
            user_id: ID utilisateur
            auth_level: Niveau d'autorisation (1=basic, 2=admin)
        
        Returns:
            Token JWT
        """
        payload = {
            "user_id": user_id,
            "auth_level": auth_level,
            "exp": datetime.utcnow() + timedelta(seconds=Config.JWT_EXPIRATION),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """
        Vérifie et décode un token JWT.
        
        Args:
            token: Token JWT
        
        Returns:
            Payload du token ou None si invalide
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def sign_action(self, action_json: Dict) -> Dict:
        """
        Signe une action avec HMAC pour garantir son intégrité.
        
        Args:
            action_json: JSON de l'action
        
        Returns:
            Action signée
        """
        # Création d'une signature HMAC
        message = f"{action_json['action_id']}{action_json['intent']}{action_json['timestamp']}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Ajout de la signature
        action_json["security"]["signature"] = signature
        action_json["security"]["signed_at"] = datetime.utcnow().isoformat()
        
        return action_json
    
    def verify_action_signature(self, action_json: Dict) -> bool:
        """
        Vérifie la signature d'une action.
        
        Args:
            action_json: JSON de l'action
        
        Returns:
            True si la signature est valide
        """
        stored_signature = action_json.get("security", {}).get("signature")
        if not stored_signature:
            return False
        
        # Recalcul de la signature
        message = f"{action_json['action_id']}{action_json['intent']}{action_json['timestamp']}"
        expected_signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(stored_signature, expected_signature)
    
    def check_permission(
        self,
        user_id: str,
        action_intent: str,
        auth_level: int
    ) -> bool:
        """
        Vérifie si un utilisateur a la permission d'exécuter une action.
        
        Args:
            user_id: ID utilisateur
            action_intent: Type d'action
            auth_level: Niveau d'autorisation utilisateur
        
        Returns:
            True si autorisé
        """
        # Définition des permissions requises par action
        permission_map = {
            "send_email": 1,
            "control_iot": 1,
            "web_search": 1,
            "system_config": 2,  # Requiert admin
            "delete_data": 2
        }
        
        required_level = permission_map.get(action_intent, 1)
        return auth_level >= required_level
    
    def sanitize_input(self, user_input: str) -> str:
        """
        Nettoie l'entrée utilisateur pour éviter les injections.
        
        Args:
            user_input: Texte utilisateur
        
        Returns:
            Texte nettoyé
        """
        # Suppression des caractères dangereux
        dangerous_chars = ["<", ">", '"', "'", ";", "--", "/*", "*/"]
        sanitized = user_input
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        return sanitized.strip()
```

---

#### 📄 `agent/logger.py` – Journalisation

**Rôle** : Journalisation centralisée de tous les événements du système.

**Code structure détaillé** :

```python
import logging
import json
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from config import Config

class Logger:
    """
    Système de journalisation centralisé.
    Supporte logs structurés (JSON) et rotation automatique.
    """
    
    def __init__(self):
        """Initialise le logger."""
        self.logger = logging.getLogger("AgentIntelligent")
        self.logger.setLevel(logging.INFO if not Config.DEBUG else logging.DEBUG)
        
        # Création du dossier logs si nécessaire
        log_dir = Path(Config.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Handler fichier avec rotation
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT
        )
        
        # Format JSON pour les logs
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        file_handler.setFormatter(formatter)
        
        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        ))
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """Log de niveau INFO."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de niveau WARNING."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info=False, **kwargs):
        """Log de niveau ERROR."""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log de niveau DEBUG."""
        self.logger.debug(message, extra=kwargs)
    
    def log_conversation(
        self,
        user_id: str,
        input_text: str,
        response_text: str
    ):
        """
        Journalise une conversation.
        
        Args:
            user_id: ID utilisateur
            input_text: Texte d'entrée
            response_text: Réponse générée
        """
        self.info("Conversation logged", extra={
            "event_type": "conversation",
            "user_id": user_id,
            "input": input_text,
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_action_created(self, action_id: str, action_json: dict):
        """Journalise la création d'une action."""
        self.info(f"Action created: {action_id}", extra={
            "event_type": "action_created",
            "action_id": action_id,
            "intent": action_json.get("intent"),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def log_execution_result(self, action_id: str, result_data: dict):
        """Journalise le résultat d'exécution d'une action."""
        self.info(f"Execution result: {action_id}", extra={
            "event_type": "execution_result",
            "action_id": action_id,
            "status": result_data.get("execution_status"),
            "details": result_data,
            "timestamp": datetime.utcnow().isoformat()
        })
```

---

### 3.5 Dossier `ai/` – Moteurs IA

#### 📄 `ai/llm_client.py` – Interface LLM

**Rôle** : Communication avec le moteur LLM pour analyse linguistique.

**Code structure** :

```python
import httpx
from typing import Dict
from config import Config

class LLMClient:
    """Client pour communiquer avec le moteur LLM."""
    
    def __init__(self):
        self.api_url = Config.LLM_API_URL
        self.api_key = Config.LLM_API_KEY
        self.timeout = Config.LLM_TIMEOUT
    
    async def analyze_intent(
        self,
        user_input: str,
        language: str = "fr"
    ) -> Dict:
        """
        Analyse l'intention d'une commande utilisateur.
        
        Returns:
            {
                "intent": "control_iot",
                "entities": {...},
                "confidence": 0.95
            }
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/analyze",
                json={
                    "text": user_input,
                    "language": language
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
    
    async def generate_conversation_response(
        self,
        user_input: str,
        user_id: str,
        language: str = "fr"
    ) -> Dict:
        """
        Génère une réponse conversationnelle.
        
        Returns:
            {
                "response": "Je vais bien, merci !",
                "confidence": 0.98
            }
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/conversation",
                json={
                    "text": user_input,
                    "user_id": user_id,
                    "language": language
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
```

---

#### 📄 `ai/stt_engine.py` – Speech-to-Text

**Rôle** : Conversion audio → texte.

**Code structure** :

```python
import base64
import whisper
from typing import Optional

class STTEngine:
    """Moteur de reconnaissance vocale (Speech-to-Text)."""
    
    def __init__(self):
        self.model = whisper.load_model("base")
    
    async def transcribe(
        self,
        audio_base64: str,
        audio_format: str = "wav"
    ) -> Optional[str]:
        """
        Transcrit un audio en texte.
        
        Args:
            audio_base64: Audio encodé en base64
            audio_format: Format audio
        
        Returns:
            Texte transcrit ou None
        """
        # Décodage base64
        audio_bytes = base64.b64decode(audio_base64)
        
        # Sauvegarde temporaire
        temp_file = "/tmp/audio_temp.wav"
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)
        
        # Transcription Whisper
        result = self.model.transcribe(temp_file, language="fr")
        
        return result.get("text", "").strip()
```

---

#### 📄 `ai/tts_engine.py` – Text-to-Speech

**Rôle** : Conversion texte → audio.

**Code structure** :

```python
from gtts import gTTS
import base64

class TTSEngine:
    """Moteur de synthèse vocale (Text-to-Speech)."""
    
    async def synthesize(
        self,
        text: str,
        language: str = "fr"
    ) -> str:
        """
        Convertit du texte en audio.
        
        Args:
            text: Texte à synthétiser
            language: Langue
        
        Returns:
            Audio encodé en base64
        """
        tts = gTTS(text=text, lang=language)
        
        # Sauvegarde temporaire
        temp_file = "/tmp/tts_output.mp3"
        tts.save(temp_file)
        
        # Lecture et encodage base64
        with open(temp_file, "rb") as f:
            audio_bytes = f.read()
        
        return base64.b64encode(audio_bytes).decode()
```

---

### 3.6 Dossier `classifier/` – ⭐ NOUVEAU MODULE

#### 📄 `classifier/intent_classifier.py` – Classification Conversation/Action

**Rôle** : Déterminer si une commande est de type Conversation ou Action.

**Méthodes possibles** :
1. **Règles simples** (mots-clés)
2. **Modèle ML** (classificateur entraîné)
3. **LLM** (utilisation du LLM pour classification)

**Code structure détaillé** :

```python
from typing import Dict
from config import Config

class IntentClassifier:
    """
    Classifie les commandes utilisateur en Conversation ou Action.
    """
    
    def __init__(self):
        self.method = Config.CLASSIFIER_METHOD  # rules|ml|llm
        self.threshold = Config.CLASSIFIER_THRESHOLD
        
        # Mots-clés pour détection Conversation
        self.conversation_keywords = [
            "bonjour", "salut", "ça va", "comment", "qui es-tu",
            "quelle heure", "merci", "au revoir", "parle", "raconte"
        ]
        
        # Mots-clés pour détection Action
        self.action_keywords = [
            "envoie", "allume", "éteins", "rappelle", "cherche",
            "active", "désactive", "ouvre", "ferme", "contrôle",
            "lance", "arrête", "démarre", "programme"
        ]
    
    async def classify(self, text: str) -> Dict:
        """
        Classifie une commande utilisateur.
        
        Args:
            text: Texte de la commande
        
        Returns:
            {
                "type": "conversation" | "action",
                "confidence": float,
                "method": str
            }
        """
        text_lower = text.lower()
        
        if self.method == "rules":
            return self._classify_by_rules(text_lower)
        elif self.method == "ml":
            return await self._classify_by_ml(text_lower)
        elif self.method == "llm":
            return await self._classify_by_llm(text_lower)
        else:
            # Fallback: règles simples
            return self._classify_by_rules(text_lower)
    
    def _classify_by_rules(self, text: str) -> Dict:
        """Classification par règles de mots-clés."""
        # Comptage des mots-clés
        conv_count = sum(
            1 for keyword in self.conversation_keywords
            if keyword in text
        )
        
        action_count = sum(
            1 for keyword in self.action_keywords
            if keyword in text
        )
        
        # Décision
        if action_count > conv_count:
            return {
                "type": "action",
                "confidence": 0.85,
                "method": "rules"
            }
        else:
            return {
                "type": "conversation",
                "confidence": 0.75,
                "method": "rules"
            }
    
    async def _classify_by_ml(self, text: str) -> Dict:
        """Classification par modèle ML (à implémenter)."""
        # TODO: Charger et utiliser modèle ML entraîné
        pass
    
    async def _classify_by_llm(self, text: str) -> Dict:
        """Classification via LLM."""
        # TODO: Appeler LLM pour classification
        pass
```

---

### 3.7 Dossier `actions/` – Gestion des actions

#### 📄 `actions/action_builder.py` – Construction ActionJSON

**Rôle** : Construire le JSON d'action standardisé.

**Code structure** :

```python
from typing import Dict
from datetime import datetime
import uuid

class ActionBuilder:
    """Constructeur d'ActionJSON standardisé."""
    
    async def build_action(
        self,
        intent: str,
        entities: Dict,
        user_id: str,
        language: str = "fr"
    ) -> Dict:
        """
        Construit un ActionJSON complet.
        
        Returns:
            ActionJSON structuré selon spécification
        """
        action_id = f"act_{uuid.uuid4().hex[:8]}"
        
        return {
            "action_id": action_id,
            "type": "action",
            "origin": "python_agent",
            "intent": intent,
            "confirmed": False,
            "priority": self._determine_priority(intent),
            "payload": self._build_payload(intent, entities),
            "context": {
                "user_id": user_id,
                "language": language,
                "channel": "voice",
                "timestamp": datetime.utcnow().isoformat()
            },
            "security": {
                "auth_level": 1,
                "signature": "pending"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _determine_priority(self, intent: str) -> str:
        """Détermine la priorité d'une action."""
        high_priority = ["emergency", "alarm", "security"]
        return "high" if intent in high_priority else "normal"
    
    def _build_payload(self, intent: str, entities: Dict) -> Dict:
        """Construit le payload selon l'intention."""
        # Logique spécifique par type d'action
        if intent == "send_email":
            return {
                "to": entities.get("recipient"),
                "subject": entities.get("subject"),
                "body": entities.get("body")
            }
        elif intent == "control_iot":
            return {
                "device_id": entities.get("device"),
                "command": entities.get("command"),
                "target": entities.get("target"),
                "value": entities.get("value")
            }
        else:
            return entities
```

---

#### 📄 `actions/confirmation_handler.py` – Gestion confirmation

**Rôle** : Gérer le processus de confirmation utilisateur.

**Code structure** :

```python
from typing import Dict

class ConfirmationHandler:
    """Gestion de la confirmation utilisateur."""
    
    async def generate_confirmation(self, action_json: Dict) -> str:
        """
        Génère un texte de confirmation clair.
        
        Args:
            action_json: JSON de l'action
        
        Returns:
            Texte de confirmation
        """
        intent = action_json["intent"]
        payload = action_json["payload"]
        
        if intent == "send_email":
            return (
                f"Je vais envoyer un email à {payload['to']} "
                f"avec le sujet '{payload['subject']}'. "
                "Voulez-vous confirmer ?"
            )
        
        elif intent == "control_iot":
            device = payload.get("target", "appareil")
            action = "allumer" if payload["command"] == "ON" else "éteindre"
            return (
                f"Je vais {action} le {device}. "
                "Voulez-vous confirmer ?"
            )
        
        else:
            return "Voulez-vous confirmer cette action ?"
    
    async def parse_response(self, user_response: str) -> str:
        """
        Analyse la réponse de l'utilisateur.
        
        Args:
            user_response: Réponse utilisateur
        
        Returns:
            "confirm" | "cancel" | "correction"
        """
        response_lower = user_response.lower()
        
        # Mots de confirmation
        if any(word in response_lower for word in ["oui", "confirme", "ok", "valide", "d'accord"]):
            return "confirm"
        
        # Mots d'annulation
        if any(word in response_lower for word in ["non", "annule", "stop", "pas"]):
            return "cancel"
        
        # Correction
        if any(word in response_lower for word in ["corrige", "modifie", "change"]):
            return "correction"
        
        # Par défaut : demander clarification
        return "unknown"
```

---

### 3.8 Dossier `integrations/` – Intégrations externes

#### 📄 `integrations/n8n_client.py` – Communication n8n

**Rôle** : Envoyer les actions confirmées vers n8n.

**Code structure** :

```python
import httpx
from typing import Dict
from config import Config

class N8NClient:
    """Client pour communiquer avec n8n."""
    
    def __init__(self):
        self.webhook_url = Config.N8N_WEBHOOK_URL
        self.timeout = Config.N8N_TIMEOUT
    
    async def send_action(self, action_json: Dict) -> Dict:
        """
        Envoie une action confirmée vers n8n.
        
        Args:
            action_json: JSON de l'action signée
        
        Returns:
            Réponse de n8n
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.webhook_url,
                json=action_json
            )
            return response.json()
```

---

#### 📄 `integrations/mqtt_client.py` – Communication MQTT

**Rôle** : Communiquer avec ESP32 via MQTT.

**Code structure** :

```python
import paho.mqtt.client as mqtt
from config import Config

class MQTTClient:
    """Client MQTT pour communication IoT."""
    
    def __init__(self):
        self.broker = Config.MQTT_BROKER
        self.port = Config.MQTT_PORT
        self.client = mqtt.Client()
        
        if Config.MQTT_USERNAME:
            self.client.username_pw_set(
                Config.MQTT_USERNAME,
                Config.MQTT_PASSWORD
            )
        
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
    
    def publish_command(self, command: Dict):
        """Publie une commande vers ESP32."""
        self.client.publish(
            Config.MQTT_TOPIC_COMMAND,
            json.dumps(command)
        )
    
    def is_connected(self) -> bool:
        """Vérifie la connexion MQTT."""
        return self.client.is_connected()
```

---

## 4. Module 2 – Moteur IA / LLM

### 4.1 Rôle du module

Le moteur IA / LLM est utilisé **uniquement pour la compréhension et la génération linguistique**.

**Responsabilités** :
- Compréhension du langage naturel
- Extraction des intentions
- Extraction des entités
- Génération de réponses conversationnelles

**Principe fondamental** : Le LLM **ne déclenche JAMAIS d'action**. Il ne fait qu'analyser et interpréter.

---

### 4.2 Organisation des fichiers

```
llm/
├── llm_server.py              # Serveur LLM
├── prompt_templates.py        # Templates de prompts
├── response_formatter.py      # Formatage des réponses
└── schemas.py                 # Schémas JSON
```

---

### 4.3 Description des fichiers

#### 📄 `llm/llm_server.py` – Serveur LLM

**Rôle** : Serveur HTTP exposant les fonctionnalités LLM.

**Routes** :
- `/analyze` : Analyse d'intention
- `/conversation` : Génération réponse conversationnelle

---

#### 📄 `llm/prompt_templates.py` – Templates de prompts

**Rôle** : Définit les prompts système pour le LLM.

**Code exemple** :

```python
INTENT_ANALYSIS_PROMPT = """
Tu es un assistant intelligent. Analyse la commande suivante et extrais :
- L'intention principale (intent)
- Les entités mentionnées (entities)

Commande : {user_input}

Réponds au format JSON :
{{
  "intent": "...",
  "entities": {{ ... }},
  "confidence": 0.0-1.0
}}
"""

CONVERSATION_PROMPT = """
Tu es un assistant vocal amical et naturel.
Réponds de manière conversationnelle à : {user_input}

Règles :
- Réponses courtes (1-2 phrases)
- Ton naturel et chaleureux
- Pas d'action, juste de la conversation
"""
```

---

## 5. Module 3 – Orchestrateur n8n

### 5.1 Rôle du module

n8n est le **moteur d'exécution contrôlée et traçable**.

**Responsabilités** :
- Réception des actions confirmées uniquement
- Validation de la structure JSON
- Routage vers le workflow approprié
- Exécution de l'action
- Retour du résultat au backend Python

**Principe fondamental** : n8n **n'effectue aucune décision intelligente**. Il exécute uniquement les actions pré-validées.

---

### 5.2 Workflows essentiels

```
n8n/
├── wf_action_router.json          # Routeur principal
├── wf_send_email.json             # Envoi d'emails
├── wf_control_iot.json            # Contrôle IoT
├── wf_web_search.json             # Recherches web
├── wf_log_event.json              # Journalisation
├── wf_set_reminder.json           # Rappels
└── wf_notification.json           # Notifications
```

---

### 5.3 Description des workflows

#### 📋 `wf_action_router` – Routeur principal

**Rôle** : Recevoir toutes les actions et les router vers le workflow approprié.

**Logique** :

```
Webhook (receive ActionJSON)
    ↓
Validate JSON schema
    ↓
Extract intent
    ↓
Route selon intent:
    ├─► send_email → wf_send_email
    ├─► control_iot → wf_control_iot
    ├─► web_search → wf_web_search
    └─► ... autres workflows
    ↓
Return result to Backend Python
```

---

#### 📋 `wf_send_email` – Envoi d'emails

**Rôle** : Envoyer un email via service SMTP.

**Nœuds** :
1. Extraction des données (to, subject, body)
2. Validation destinataire
3. Connexion SMTP
4. Envoi email
5. Log succès/échec
6. Callback Backend Python

---

#### 📋 `wf_control_iot` – Contrôle IoT

**Rôle** : Envoyer commandes vers ESP32 via MQTT.

**Nœuds** :
1. Extraction device_id, command
2. Validation commande
3. Publication MQTT
4. Attente confirmation ESP32
5. Log état
6. Callback Backend Python

---

## 6. Module 4 – Système embarqué ESP32

### 6.1 Rôle du module

L'ESP32 agit comme **interface physique** entre l'utilisateur et le système.

**Responsabilités** :
- Capture audio (microphone)
- Restitution audio (haut-parleur)
- Exécution commandes physiques (relais, LED, moteurs)
- Remontée d'états capteurs

**Principe fondamental** : L'ESP32 **n'effectue AUCUN traitement intelligent**. Il est un simple exécuteur.

---

### 6.2 Organisation des fichiers ESP32

```
esp32/
├── main.cpp                   # Programme principal
├── mqtt_client.cpp            # Client MQTT
├── device_manager.cpp         # Gestion appareils
├── sensors.cpp                # Lecture capteurs
├── actuators.cpp              # Contrôle actionneurs
├── audio_handler.cpp          # ⭐ NOUVEAU : Gestion audio
└── config.h                   # Configuration
```

---

### 6.3 Description des fichiers

#### 📄 `esp32/main.cpp` – Programme principal

**Responsabilités** :
- Initialisation matérielle
- Connexion WiFi
- Connexion MQTT
- Boucle principale
- Gestion wake word

---

#### 📄 `esp32/audio_handler.cpp` – ⭐ Gestion audio

**Responsabilités** :
- Détection wake word
- Enregistrement segment audio
- Transmission audio vers Backend Python
- Réception et lecture réponses vocales

---

## 7. Gestion complète des flux JSON entre modules

### 7.1 Principe fondamental

Tous les modules du système communiquent **exclusivement via des objets JSON**.

**Règles** :
- Aucun partage de logique interne
- Aucun partage d'état mémoire
- Aucun accès direct aux services d'un autre module

👉 **Le JSON est le contrat unique du système.**

---

### 7.2 Flux 0 – Classification interne Python

**Objectif** : Classifier toute commande utilisateur après STT.

**JSON interne de classification** :

```json
{
  "request_id": "req_001",
  "raw_text": "Ça va ?",
  "classification": "conversation",
  "confidence": 0.98,
  "method": "rules",
  "timestamp": "2026-01-20T10:00:00Z"
}
```

---

### 7.3 Flux Conversation – Backend uniquement

**Objectif** : Gérer les échanges sociaux **sans orchestration n8n**.

**ConversationJSON** :

```json
{
  "conversation_id": "conv_101",
  "type": "conversation",
  "input_text": "Ça va ?",
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice"
  },
  "response": {
    "text": "Oui, je vais très bien, merci ! 😊",
    "tts": true
  },
  "timestamp": "2026-01-20T10:00:05Z"
}
```

👉 Ce flux **ne quitte jamais le backend Python**.

---

### 7.4 Flux 1 – Python → LLM (Analyse linguistique)

**Objectif** : Envoyer une commande au LLM pour analyse.

**JSON envoyé par Python au LLM** :

```json
{
  "request_id": "req_002",
  "input_text": "Allume la lampe de la cuisine",
  "language": "fr",
  "context": {
    "user_id": "user_42",
    "channel": "voice"
  },
  "mode": "intent_analysis"
}
```

---

### 7.5 Flux 2 – LLM → Python (Résultat d'analyse)

**Objectif** : Retourner une structure interprétée, **sans prise de décision**.

**JSON retourné par le LLM** :

```json
{
  "request_id": "req_002",
  "intent": "control_iot",
  "entities": {
    "device": "lamp",
    "location": "kitchen",
    "action": "on"
  },
  "confidence": 0.93,
  "processing_time_ms": 245
}
```

---

### 7.6 Flux 3 – Python → Python (Construction ActionJSON)

**Objectif** : Transformer la sortie du LLM en **ActionJSON officielle**.

**ActionJSON construite (état: DRAFT)** :

```json
{
  "action_id": "act_1001",
  "type": "action",
  "origin": "python_agent",
  "intent": "control_iot",
  "confirmed": false,
  "priority": "high",
  "payload": {
    "device_id": "esp32_kitchen",
    "command": "RELAY_ON",
    "target": "LAMP_1",
    "value": 1
  },
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice",
    "location": "kitchen"
  },
  "security": {
    "auth_level": 1,
    "signature": "pending"
  },
  "timestamp": "2026-01-20T10:00:00Z"
}
```

---

### 7.7 Flux 4 – Confirmation utilisateur

**Objectif** : Obtenir validation humaine explicite.

**Confirmation générée** :

```json
{
  "action_id": "act_1001",
  "confirmation_text": "Je vais allumer la lampe de la cuisine. Voulez-vous confirmer ?",
  "confirmation_audio": "base64_encoded_audio",
  "options": ["Oui", "Non", "Annuler"]
}
```

**Mise à jour après confirmation** :

```json
{
  "action_id": "act_1001",
  "confirmed": true,
  "confirmed_at": "2026-01-20T10:00:10Z",
  "security": {
    "auth_level": 1,
    "signature": "HMAC_8f92aa3b..."
  }
}
```

---

### 7.8 Flux 5 – Python → n8n (Exécution contrôlée)

**Objectif** : Envoyer une action **confirmée uniquement** vers n8n.

**JSON envoyé à n8n** :

```json
{
  "action_id": "act_1001",
  "type": "action",
  "origin": "python_agent",
  "intent": "control_iot",
  "confirmed": true,
  "priority": "high",
  "payload": {
    "device_id": "esp32_kitchen",
    "command": "RELAY_ON",
    "target": "LAMP_1",
    "value": 1
  },
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice"
  },
  "security": {
    "auth_level": 1,
    "signature": "HMAC_8f92aa3b..."
  },
  "timestamp": "2026-01-20T10:00:10Z"
}
```

---

### 7.9 Flux 6 – n8n → ESP32 (Commande physique)

**Objectif** : Transmettre une commande simple et déterministe à l'ESP32.

**JSON envoyé à ESP32** :

```json
{
  "device_id": "esp32_kitchen",
  "command": "RELAY_ON",
  "target": "LAMP_1",
  "value": 1,
  "timestamp": 1705754410
}
```

---

### 7.10 Flux 7 – ESP32 → n8n (Retour d'état)

**Objectif** : Confirmer l'exécution de la commande.

**JSON retourné par ESP32** :

```json
{
  "device_id": "esp32_kitchen",
  "status": "SUCCESS",
  "details": {
    "relay_state": "ON",
    "target": "LAMP_1",
    "execution_time_ms": 45
  },
  "timestamp": 1705754420
}
```

---

### 7.11 Flux 8 – n8n → Python (Résultat final)

**Objectif** : Informer le backend du résultat d'exécution.

**JSON de résultat** :

```json
{
  "action_id": "act_1001",
  "execution_status": "SUCCESS",
  "module": "ESP32",
  "details": {
    "relay_state": "ON",
    "device_id": "esp32_kitchen"
  },
  "execution_time_ms": 245,
  "timestamp": "2026-01-20T10:00:20Z"
}
```

---

## 8. Description des interactions entre modules

### 8.1 Scénario complet – Envoi d'email

```
1. UTILISATEUR
   └─► "Envoie un email à Jean pour lui dire que la réunion est reportée"

2. ESP32
   └─► Capture audio → Transmission Backend Python

3. BACKEND PYTHON
   ├─► STT : Audio → Texte
   ├─► Classification : Type = ACTION
   ├─► LLM : Analyse intention + entités
   ├─► Action Builder : Création ActionJSON (DRAFT)
   ├─► Confirmation Handler : Génération confirmation
   └─► TTS : Texte → Audio → ESP32 → Utilisateur
       "Je vais envoyer un email à Jean avec le message 'La réunion est reportée'. Confirmer ?"

4. UTILISATEUR
   └─► "Oui, envoie"

5. BACKEND PYTHON
   ├─► Confirmation Handler : Parse réponse → CONFIRM
   ├─► State Manager : DRAFT → CONFIRMED
   ├─► Security Manager : Signature action
   └─► n8n Client : Envoi ActionJSON signée

6. N8N
   ├─► Validation JSON
   ├─► Routage : intent = send_email → wf_send_email
   ├─► Workflow send_email : Connexion SMTP → Envoi
   └─► Callback Backend Python : Résultat SUCCESS

7. BACKEND PYTHON
   ├─► State Manager : EXECUTING → COMPLETED
   ├─► Logger : Journalisation
   ├─► TTS : "Email envoyé avec succès à Jean"
   └─► ESP32 → Utilisateur

8. FIN
```

---

### 8.2 Scénario complet – Conversation simple

```
1. UTILISATEUR
   └─► "Bonjour, ça va ?"

2. ESP32
   └─► Capture audio → Transmission Backend Python

3. BACKEND PYTHON
   ├─► STT : Audio → Texte
   ├─► Classification : Type = CONVERSATION
   ├─► LLM : Génération réponse conversationnelle
   ├─► TTS : "Bonjour ! Oui, je vais très bien, merci !"
   └─► ESP32 → Utilisateur

4. FIN (aucune orchestration n8n)
```

---

### 8.3 Scénario complet – Contrôle IoT

```
1. UTILISATEUR
   └─► "Allume la lampe de la cuisine"

2. ESP32
   └─► Capture audio → Backend Python

3. BACKEND PYTHON
   ├─► STT + Classification (ACTION)
   ├─► LLM : intent = control_iot
   ├─► Action Builder : ActionJSON DRAFT
   ├─► Confirmation : "Allumer lampe cuisine ?"
   └─► Utilisateur : "Oui"

4. BACKEND PYTHON
   ├─► Signature + CONFIRMED
   └─► n8n Client : Envoi

5. N8N
   ├─► wf_control_iot
   ├─► Publication MQTT → ESP32
   └─► Attente confirmation

6. ESP32
   ├─► Réception commande MQTT
   ├─► Exécution : Relais ON
   └─► Retour état SUCCESS

7. N8N
   └─► Callback Backend Python

8. BACKEND PYTHON
   ├─► COMPLETED
   └─► TTS : "Lampe allumée"

9. FIN
```

---

## 9. Mise à jour du cahier des charges (Addendum)

### 9.1 Clarification du périmètre fonctionnel

Le système distingue désormais **deux catégories d'interactions** :

#### 9.1.1 Interaction de type Conversation

**Définition** : Échange social ou informatif **sans déclenchement d'action réelle**.

**Exemples** :
- Salutations : "bonjour", "ça va ?"
- Questions générales : "qui es-tu ?", "que fais-tu ?"
- Discussion courte sans impact système

**Caractéristiques** :
- ❌ Aucune confirmation requise
- ❌ Aucune transmission vers n8n
- ✅ Traitement **exclusivement dans Backend Python**
- ✅ Réponse textuelle/vocale immédiate

**Besoins satisfaits** : BF1, BF3, BF4, BF13

---

#### 9.1.2 Interaction de type Action

**Définition** : Commande nécessitant **exécution réelle** avec impact observable.

**Exemples** :
- Envoi d'email
- Contrôle IoT
- Création rappel
- Appel service externe

**Caractéristiques** :
- ✅ Analyse linguistique complète
- ✅ Confirmation OBLIGATOIRE
- ✅ Transmission structurée vers n8n
- ✅ Traçabilité complète

**Besoins satisfaits** : BF2, BF5-BF12

---

### 9.2 Ajout besoin fonctionnel transversal

**BF-T1** – Le système doit **classifier automatiquement** chaque commande utilisateur après transcription, pour déterminer si l'interaction relève d'une *conversation* ou d'une *action*.

Cette classification est réalisée par le Backend Python à l'aide de :
- Règles linguistiques
- Et/ou modèles IA
- Et/ou module LLM en mode interprétation

---

### 9.3 Impact sur les modules existants

#### Backend Python
- Intègre module de classification en amont
- Si Conversation → réponse directe
- Si Action → pipeline standard (DRAFT → CONFIRMED → n8n)

#### Module LLM
- Reste limité à compréhension linguistique
- Ne décide jamais de l'exécution
- Ne remplace pas la classification backend

#### Module n8n
- Exécute uniquement actions confirmées
- Conversations jamais transmises
- Réduit charge d'exécution
- Améliore sécurité et traçabilité

---

## 10. Règles d'or du système

### ❌ Interdictions strictes

1. **Le LLM n'exécute jamais d'action**
2. **L'ESP32 ne reçoit jamais de JSON complexe**
3. **Les conversations ne passent jamais par n8n**
4. **Aucune action sans confirmation utilisateur**
5. **Aucun partage de logique entre modules**

### ✅ Obligations strictes

1. **Toute action passe par n8n**
2. **Toute action est confirmée par l'utilisateur**
3. **Tous les échanges sont journalisés**
4. **Tous les modules communiquent via JSON uniquement**
5. **Séparation stricte Intelligence / Décision / Exécution**

---

## 11. Conclusion générale

Cette architecture technique complète et consolidée définit :

✅ **Organisation modulaire** claire et professionnelle  
✅ **Séparation Conversation / Action** explicite et justifiée  
✅ **Flux JSON** complets et standardisés  
✅ **Sécurité** renforcée avec validation humaine  
✅ **Traçabilité** totale des actions  
✅ **Évolutivité** facilitée par découplage fort  
✅ **Conformité académique** pour PCD/PFE  

Cette documentation constitue la **base technique officielle** pour l'implémentation du projet.

---

**Document consolidé le : 20 janvier 2026**  
**Version : 2.0 Complète**
