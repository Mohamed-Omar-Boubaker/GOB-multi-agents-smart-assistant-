# 📋 PLAN D'INTÉGRATION DES MODÈLES AI

**Date**: 10 février 2026  
**Responsable**: Montassar  
**Status**: PLAN DÉTAILLÉ - À VALIDER AVANT IMPLÉMENTATION

---

## 🎯 OBJECTIF

Intégrer les modèles AI testés et fonctionnels dans le backend Agent Core :
1. **STT** : faster-whisper (modèle tiny)
2. **TTS** : Piper via Wyoming protocol
3. **LLM** : OpenRouter API avec Mistral-7B

---

## 📊 ANALYSE DES TESTS EXISTANTS

### Test 1 : LLM (testLLM.py)
```python
✅ FONCTIONNEL
- API: OpenRouter (https://openrouter.ai/api/v1/chat/completions)
- Modèle: mistralai/mistral-7b-instruct
- Clé API: [REDACTED_OPENROUTER_API_KEY]
- Température: 0.2 (réponses précises)
- Timeout: 20 secondes
- Mémoire: Liste messages[] avec historique conversation
- Performance: ~2-3 secondes par réponse
```

### Test 2 : STT (testWisper.py)
```python
✅ FONCTIONNEL
- Librairie: faster-whisper
- Modèle: tiny (86MB, rapide)
- Device: CPU
- Compute type: int8 (optimisé)
- beam_size: 1 (plus rapide)
- Performance: ~1-2 secondes pour 5-10 secondes audio
- Temps chargement: ~2 secondes
```

### Test 3 : TTS (test_piper.py)
```python
✅ FONCTIONNEL
- Serveur: Wyoming protocol (localhost:5002)
- Format: asyncio + wyoming library
- Output: WAV (1 channel, 21470 Hz sample rate)
- Qualité: Excellente pour voix française
- Performance: Temps réel (~1 seconde pour phrase courte)
```

---

## 🗂️ STRUCTURE ACTUELLE vs CIBLE

### Backend Actuel
```
backend/
├── agent/
│   ├── agent_core.py        ✅ COMPLET (avec injection dépendances)
│   ├── logger.py            ✅ COMPLET
│   ├── state_manager.py     ✅ COMPLET
│   └── security_manager.py  ✅ COMPLET
├── ai/
│   ├── stt_engine.py        ❌ SKELETON (à implémenter)
│   ├── tts_engine.py        ❌ SKELETON (à implémenter)
│   └── llm_client.py        ❌ SKELETON (à implémenter)
└── classifier/
    └── intent_classifier.py ❌ SKELETON (à implémenter)
```

### Module LLM Séparé
```
llm/
├── llm_server.py            ❌ SKELETON (à implémenter FastAPI)
├── config.py                ✅ COMPLET
├── prompt_templates.py      ⚠️ BASIQUE (à enrichir)
└── README.md                ✅ COMPLET
```

---

## 📝 PLAN D'IMPLÉMENTATION - ÉTAPES DÉTAILLÉES

### 🔴 PHASE 1 : STT Engine (Speech-to-Text)
**Fichier**: `backend/ai/stt_engine.py`  
**Durée estimée**: 2-3 heures

#### Étape 1.1 : Imports et Configuration
```python
from faster_whisper import WhisperModel
import base64
import io
import wave
import time
from datetime import datetime, UTC
```

#### Étape 1.2 : Classe STTEngine
- **Constructeur** :
  - Charger modèle "tiny" au démarrage
  - Device: CPU, compute_type: int8
  - Logger : temps chargement
  
- **Méthode async transcribe()** :
  1. Recevoir audio_base64 + audio_format
  2. Décoder base64 → bytes
  3. Sauver temporairement en fichier WAV
  4. Appeler model.transcribe() avec beam_size=1
  5. Joindre segments
  6. Retourner JSON avec transcription + confidence + temps

#### Étape 1.3 : Gestion Erreurs
- Audio vide
- Format non supporté
- Erreur décodage base64
- Timeout transcription

#### Étape 1.4 : Tests Unitaires
- Test audio valide
- Test base64 invalide
- Test format non supporté

---

### 🟠 PHASE 2 : TTS Engine (Text-to-Speech)
**Fichier**: `backend/ai/tts_engine.py`  
**Durée estimée**: 3-4 heures

#### Étape 2.1 : Imports et Configuration
```python
import asyncio
from wyoming.tts import Synthesize
from wyoming.audio import AudioChunk, AudioStop
from wyoming.event import async_write_event, async_read_event
import base64
import io
import wave
```

#### Étape 2.2 : Classe TTSEngine
- **Constructeur** :
  - Host: 127.0.0.1
  - Port: 5002 (serveur Piper Wyoming)
  - Sample rate: 21470 Hz (testé et validé)
  
- **Méthode async synthesize()** :
  1. Recevoir text + language
  2. Ouvrir connexion Wyoming
  3. Envoyer Synthesize event
  4. Collecter AudioChunk events
  5. Créer WAV en mémoire
  6. Encoder en base64
  7. Retourner JSON avec audio_data

#### Étape 2.3 : Gestion Erreurs
- Serveur Piper non disponible
- Timeout connexion
- Texte vide
- Erreur encodage

#### Étape 2.4 : Tests Unitaires
- Test avec serveur Piper actif
- Test texte court / long
- Test serveur indisponible

---

### 🔵 PHASE 3 : LLM Client (OpenRouter API)
**Fichier**: `backend/ai/llm_client.py`  
**Durée estimée**: 4-5 heures

#### Étape 3.1 : Imports et Configuration
```python
import httpx
import time
from typing import Dict, List
from datetime import datetime, UTC
```

#### Étape 3.2 : Classe LLMClient
- **Constructeur** :
  - API Key: [REDACTED_OPENROUTER_API_KEY]
  - URL: https://openrouter.ai/api/v1/chat/completions
  - Modèle: mistralai/mistral-7b-instruct
  - Temperature: 0.2
  - Session httpx persistante
  - Mémoire conversations (dict par user_id)

#### Étape 3.3 : Méthode async generate_conversation_response()
1. Récupérer historique user
2. Ajouter prompt système si première conversation
3. Ajouter message user
4. POST vers OpenRouter
5. Extraire réponse
6. Sauver dans historique
7. Retourner JSON avec response + confidence

#### Étape 3.4 : Méthode async analyze_intent()
1. Construire prompt spécial pour extraction (depuis prompt_templates)
2. Demander format JSON structuré
3. Parser réponse LLM
4. Extraire intent + entities + confidence
5. Retourner JSON structuré

#### Étape 3.5 : Gestion Mémoire
- Limiter historique à 10 derniers messages par user
- Clear automatique après inactivité
- Méthode clear_history(user_id)

#### Étape 3.6 : Gestion Erreurs
- API Key invalide
- Timeout (20s)
- Rate limiting
- Parsing JSON échoué

#### Étape 3.7 : Tests Unitaires
- Test conversation simple
- Test analyse intent
- Test mémoire conversations
- Test erreur API

---

### 🟣 PHASE 4 : Intent Classifier
**Fichier**: `backend/classifier/intent_classifier.py`  
**Durée estimée**: 2-3 heures

#### Étape 4.1 : Approche Hybride
**Méthode 1 : Règles (Rapide)**
```python
ACTION_KEYWORDS = ["allume", "éteins", "ouvre", "ferme", "lance", "démarre", 
                   "arrête", "mets", "active", "désactive", "règle"]
CONVERSATION_KEYWORDS = ["bonjour", "salut", "comment", "qui es-tu", 
                         "merci", "au revoir"]
```

**Méthode 2 : LLM (Précis)**
- Prompt spécial classification
- Retour: "conversation" ou "action" + confidence

#### Étape 4.2 : Classe IntentClassifier
- **async classify()** :
  1. Vérifier règles simples (rapide)
  2. Si confidence < 0.8 → appel LLM
  3. Retourner type + confidence + method utilisée

---

### 🟢 PHASE 5 : LLM Server (Module Séparé)
**Fichier**: `llm/llm_server.py`  
**Durée estimée**: 3-4 heures

#### Étape 5.1 : FastAPI Setup
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
```

#### Étape 5.2 : Routes
**GET /health**
- Vérifier connexion OpenRouter
- Retourner status

**POST /analyze**
- Recevoir user_input + mode
- Appeler LLMClient.analyze_intent()
- Retourner JSON structuré

**POST /conversation**
- Recevoir user_input + user_id
- Appeler LLMClient.generate_conversation_response()
- Retourner réponse

#### Étape 5.3 : Middleware
- Logging toutes requêtes
- Gestion erreurs
- CORS si nécessaire

---

### 🔵 PHASE 6 : Enrichir Prompt Templates
**Fichier**: `llm/prompt_templates.py`  
**Durée estimée**: 1-2 heures

#### Étape 6.1 : Templates Détaillés

**INTENT_ANALYSIS_PROMPT** (pour extraction précise)
```python
"""
Tu es un expert en analyse linguistique pour domotique IoT.

Analyse la commande utilisateur et extrais :
1. L'INTENTION principale (intent)
2. Les ENTITÉS mentionnées (entities)

COMMANDE : {user_input}

INTENTIONS POSSIBLES :
- control_iot : Contrôle appareil (allumer, éteindre, régler)
- query_status : Demande état appareil
- automation : Création automatisation
- information : Demande info météo, heure, etc.

ENTITÉS À EXTRAIRE :
- device : Type appareil (lampe, climatiseur, TV, etc.)
- location : Localisation (salon, chambre, cuisine, etc.)
- action : Action précise (turn_on, turn_off, set_temperature, etc.)
- parameters : Paramètres additionnels (température, couleur, etc.)

RÉPONDS EN JSON VALIDE :
{{
  "intent": "...",
  "entities": {{
    "device": "...",
    "location": "...",
    "action": "...",
    "parameters": {{}}
  }},
  "confidence": 0.0-1.0
}}
"""
```

**CONVERSATION_PROMPT** (pour dialogue naturel)
```python
"""
Tu es GOB, le premier assistant vocal IA en Tunisie.

PERSONNALITÉ :
- Amical et chaleureux
- Réponses courtes (1-3 phrases max)
- Tutoiement naturel
- Humour léger bienvenu
- Tunisien fier 🇹🇳

RÈGLES :
- NE DÉCLENCHE JAMAIS D'ACTION
- Juste converser naturellement
- Si demande action → "Je peux t'aider ! Dis-moi ce que tu veux faire."

CONTEXTE :
Utilisateur : {user_id}
Historique : {conversation_history}

MESSAGE UTILISATEUR : {user_input}

RÉPONDS NATURELLEMENT :
"""
```

---

### ⚡ PHASE 7 : Intégration dans Agent Core
**Fichier**: `backend/agent/agent_core.py`  
**Durée estimée**: 1-2 heures

#### Étape 7.1 : Modifications Constructor
```python
def __init__(self, ...):
    # Charger composants réels
    from backend.ai.stt_engine import STTEngine
    from backend.ai.tts_engine import TTSEngine
    from backend.ai.llm_client import LLMClient
    from backend.classifier.intent_classifier import IntentClassifier
    
    if stt_engine is None:
        self.stt_engine = STTEngine(model="tiny")
    
    if tts_engine is None:
        self.tts_engine = TTSEngine(host="127.0.0.1", port=5002)
    
    if llm_client is None:
        self.llm_client = LLMClient(
            api_key="sk-or-v1-...",
            model="mistralai/mistral-7b-instruct"
        )
    
    if classifier is None:
        self.classifier = IntentClassifier(llm_client=self.llm_client)
```

#### Étape 7.2 : Validation Pipeline Complet
- Test conversation end-to-end
- Test action end-to-end
- Test audio end-to-end

---

## 📦 DÉPENDANCES À INSTALLER

### requirements.txt (à mettre à jour)
```txt
# Existant
fastapi==0.109.0
uvicorn==0.27.0
pytest==9.0.2
python-dotenv==1.0.0

# STT
faster-whisper==1.0.0

# TTS
wyoming==1.5.0

# LLM
httpx==0.27.0

# Classifier (optionnel)
scikit-learn==1.4.0
```

---

## 🧪 PLAN DE TESTS

### Tests Unitaires par Composant
1. **test_stt_engine.py** : 5 tests
2. **test_tts_engine.py** : 5 tests
3. **test_llm_client.py** : 8 tests
4. **test_intent_classifier.py** : 6 tests

### Tests d'Intégration
1. **test_agent_core_conversation.py** : Pipeline conversation complet
2. **test_agent_core_action.py** : Pipeline action complet
3. **test_agent_core_audio.py** : Audio → Texte → Action → Audio

---

## ⚙️ CONFIGURATION REQUISE

### Variables d'Environnement (.env)
```bash
# LLM
LLM_API_KEY=[REDACTED_OPENROUTER_API_KEY]
LLM_MODEL=mistralai/mistral-7b-instruct
LLM_TEMPERATURE=0.2

# STT
STT_MODEL=tiny
STT_DEVICE=cpu
STT_COMPUTE_TYPE=int8

# TTS
TTS_HOST=127.0.0.1
TTS_PORT=5002
TTS_SAMPLE_RATE=21470

# Agent
AGENT_LOG_LEVEL=INFO
```

### Serveur Piper (TTS)
```bash
# Doit être lancé avant
cd piper-data
# Lancer serveur Wyoming avec Piper
# (Commande exacte selon votre setup)
```

---

## 📊 ORDRE D'EXÉCUTION RECOMMANDÉ

### Semaine 1
- ✅ Jour 1-2 : PHASE 1 (STT Engine)
- ✅ Jour 3-4 : PHASE 2 (TTS Engine)

### Semaine 2
- ✅ Jour 1-3 : PHASE 3 (LLM Client)
- ✅ Jour 4 : PHASE 4 (Intent Classifier)

### Semaine 3
- ✅ Jour 1-2 : PHASE 5 (LLM Server)
- ✅ Jour 3 : PHASE 6 (Prompt Templates)
- ✅ Jour 4-5 : PHASE 7 (Intégration Agent Core)

### Semaine 4
- ✅ Tests complets
- ✅ Optimisations
- ✅ Documentation

---

## 🎯 POINTS D'ATTENTION CRITIQUES

### ⚠️ Performance
- **STT** : Charger modèle UNE SEULE FOIS au démarrage (pas à chaque requête)
- **TTS** : Réutiliser connexion Wyoming (pool de connexions)
- **LLM** : Session httpx persistante + mémoire limitée

### ⚠️ Gestion Mémoire
- **LLM** : Limiter historique conversations (max 10 messages/user)
- **STT** : Nettoyer fichiers temporaires audio
- **TTS** : Buffers audio en mémoire

### ⚠️ Erreurs Réseau
- **Timeout LLM** : 20 secondes max
- **Retry** : 3 tentatives avec backoff exponentiel
- **Fallback** : Messages d'erreur utilisateur-friendly

### ⚠️ Sécurité
- **API Key** : JAMAIS dans le code, toujours .env
- **Logs** : NE PAS logger API key ou données sensibles
- **Rate Limiting** : Gérer limites OpenRouter

---

## 📄 FICHIERS À CRÉER/MODIFIER

### À CRÉER
1. `backend/ai/stt_engine.py` (implémentation complète)
2. `backend/ai/tts_engine.py` (implémentation complète)
3. `backend/ai/llm_client.py` (implémentation complète)
4. `backend/classifier/intent_classifier.py` (implémentation complète)
5. `llm/llm_server.py` (serveur FastAPI complet)
6. `backend/ai/tests/test_stt_engine.py`
7. `backend/ai/tests/test_tts_engine.py`
8. `backend/ai/tests/test_llm_client.py`
9. `.env` (avec toutes les variables)

### À MODIFIER
1. `llm/prompt_templates.py` (enrichir templates)
2. `backend/agent/agent_core.py` (imports + init composants)
3. `backend/config.py` (ajouter config AI)
4. `requirements.txt` (ajouter dépendances)

---

## ✅ CRITÈRES DE VALIDATION

### Chaque Phase
- ✅ Code sans erreurs Python
- ✅ Tests unitaires passent
- ✅ Logging approprié
- ✅ Gestion erreurs complète
- ✅ Documentation docstrings

### Intégration Finale
- ✅ Pipeline conversation fonctionne end-to-end
- ✅ Pipeline action fonctionne end-to-end
- ✅ Audio → Texte → Action → Audio fonctionne
- ✅ Temps réponse < 5 secondes (conversation)
- ✅ Temps réponse < 8 secondes (action complète)
- ✅ Pas de memory leaks
- ✅ Logs clairs et traçables

---

## 🚀 PROCHAINE ÉTAPE

**ATTENTE VALIDATION** : Ce plan doit être validé avant de commencer l'implémentation.

**Questions à clarifier** :
1. Confirmer API Key OpenRouter est bien celle-ci ?
2. Serveur Piper est accessible sur localhost:5002 ?
3. Ordre des phases convient ?
4. Budget temps total : ~3-4 semaines acceptable ?

**Après validation** :
→ On commence PHASE 1 (STT Engine) pas à pas

---

**Montassar** - Chef de Projet  
**Date**: 10 février 2026
