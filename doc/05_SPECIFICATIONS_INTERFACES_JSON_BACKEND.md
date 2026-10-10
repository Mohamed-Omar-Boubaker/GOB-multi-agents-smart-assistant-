# 🔌 Spécifications Interfaces JSON - Backend Python
## Distribution Équipe avec Contrats d'Interface

**Version :** 1.0  
**Date :** 20 janvier 2026  
**Objectif :** Spécifier les INPUT/OUTPUT JSON exacts pour chaque composant Backend

---

## 📋 Table des Matières

1. [Principe des contrats d'interface](#1-principe-des-contrats-dinterface)
2. [Vue d'ensemble composants Backend](#2-vue-densemble-composants-backend)
3. [Distribution entre les 3 personnes](#3-distribution-entre-les-3-personnes)
4. [Spécifications détaillées par composant](#4-spécifications-détaillées-par-composant)
5. [Règles de validation et tests](#5-règles-de-validation-et-tests)
6. [Workflow d'assemblage](#6-workflow-dassemblage)

---

## 1. Principe des contrats d'interface

### 1.1 Concept

Chaque composant Backend est une **boîte noire** avec :
- ✅ **INPUT JSON** défini et fixe
- ✅ **OUTPUT JSON** défini et fixe
- ✅ **Fonction/classe** à implémenter
- ✅ **Test simple** pour valider

**Avantages :**
- 🔹 Travail **parallèle** : Chacun code sa partie indépendamment
- 🔹 **Pas d'attente** : Pas besoin des autres composants pour commencer
- 🔹 **GitHub facile** : Chacun push sa partie dans un dossier séparé
- 🔹 **Tests isolés** : Chaque composant testé séparément
- 🔹 **Assemblage final** : On connecte tout à la fin

### 1.2 Structure de travail

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERSONNE 1 (Montassar)                        │
│  Composants: Classifier + Agent Core                             │
│  Input: JSON défini                                              │
│  Output: JSON défini                                             │
│  ├─► Développe en local                                          │
│  ├─► Teste avec JSON mockés                                      │
│  └─► Push sur GitHub → branch feature/classifier                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PERSONNE 2 (Amine)                            │
│  Composants: Action Builder + Security Manager                   │
│  Input: JSON défini                                              │
│  Output: JSON défini                                             │
│  ├─► Développe en local                                          │
│  ├─► Teste avec JSON mockés                                      │
│  └─► Push sur GitHub → branch feature/action-builder            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PERSONNE 3 (Omar)                             │
│  Composants: STT + TTS + MQTT Client                             │
│  Input: JSON défini                                              │
│  Output: JSON défini                                             │
│  ├─► Développe en local                                          │
│  ├─► Teste avec JSON mockés                                      │
│  └─► Push sur GitHub → branch feature/audio                     │
└─────────────────────────────────────────────────────────────────┘

                          ↓ APRÈS 2-3 SEMAINES ↓

┌─────────────────────────────────────────────────────────────────┐
│                    ASSEMBLAGE FINAL (TOUS)                       │
│  ├─► Merge toutes les branches                                  │
│  ├─► Connecter les composants (utiliser les JSON)               │
│  ├─► Tests d'intégration                                         │
│  └─► Backend complet fonctionnel                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Vue d'ensemble composants Backend

### 2.1 Liste complète des composants

| # | Composant | Rôle | Input | Output | Priorité |
|---|-----------|------|-------|--------|----------|
| **1** | **Classifier** | Classer Conversation vs Action | Texte utilisateur | Classification + confidence | 🔴 CRITIQUE |
| **2** | **STT Engine** | Audio → Texte | Audio base64 | Texte transcrit | 🔴 CRITIQUE |
| **3** | **TTS Engine** | Texte → Audio | Texte réponse | Audio base64 | 🟠 HAUTE |
| **4** | **LLM Client** | Analyse linguistique | Texte + contexte | Intent + entités | 🔴 CRITIQUE |
| **5** | **Action Builder** | Construire ActionJSON | Intent + entités | ActionJSON complet | 🔴 CRITIQUE |
| **6** | **Confirmation Handler** | Gérer confirmation | ActionJSON DRAFT | Demande confirmation | 🟠 HAUTE |
| **7** | **State Manager** | Gérer états actions | action_id + transitions | État actuel | 🟠 HAUTE |
| **8** | **Security Manager** | Signer ActionJSON | ActionJSON CONFIRMED | Signature HMAC | 🟠 HAUTE |
| **9** | **n8n Client** | Envoyer vers n8n | ActionJSON signé | Acknowledgment | 🟢 MOYENNE |
| **10** | **MQTT Client** | Communication ESP32 | Commandes/Audio | Publication MQTT | 🟢 MOYENNE |
| **11** | **Agent Core** | Orchestrateur principal | Commande utilisateur | Réponse complète | 🔴 CRITIQUE |

### 2.2 Dépendances entre composants

```
Commande utilisateur
    ↓
┌─────────────────────┐
│   Agent Core        │  ← Orchestrateur (utilise tous les autres)
└─────────┬───────────┘
          │
          ├─► STT Engine (si audio)
          │
          ├─► Classifier
          │      ↓
          │   ┌────────────────┐
          │   │ Conversation?  │ → LLM Client → TTS Engine → FIN
          │   └────────────────┘
          │   ┌────────────────┐
          │   │ Action?        │ → Suite pipeline
          │   └────────────────┘
          │
          ├─► LLM Client (analyse)
          │
          ├─► Action Builder
          │
          ├─► Confirmation Handler
          │
          ├─► State Manager
          │
          ├─► Security Manager
          │
          └─► n8n Client
```

---

## 3. Distribution entre les 3 personnes

### 3.1 Montassar (Lead Backend) - 40% charge

**Composants assignés :**
- ✅ **Classifier** (Classification Conversation/Action)
- ✅ **LLM Client** (Communication avec LLM)
- ✅ **Agent Core** (Orchestrateur principal)
- ✅ **State Manager** (Gestion états)

**Justification :** Lead projet, responsable de la logique décisionnelle centrale

**Temps estimé :** 80-100h

---

### 3.2 Amine (Développeur Full-Stack) - 30% charge

**Composants assignés :**
- ✅ **Action Builder** (Construction ActionJSON)
- ✅ **Confirmation Handler** (Gestion confirmations)
- ✅ **Security Manager** (Signatures HMAC)
- ✅ **n8n Client** (Communication n8n)

**Justification :** Expertise intégrations et workflows

**Temps estimé :** 50-60h

---

### 3.3 Omar (Développeur Embarqué) - 30% charge

**Composants assignés :**
- ✅ **STT Engine** (Speech-to-Text)
- ✅ **TTS Engine** (Text-to-Speech)
- ✅ **MQTT Client** (Communication ESP32)

**Justification :** Expertise audio et communication IoT

**Temps estimé :** 40-50h

---

## 4. Spécifications détaillées par composant

---

## 📦 COMPOSANT 1 - Classifier

**Responsable :** Omar  
**Priorité :** 🔴 CRITIQUE  
**Temps estimé :** 20h

### 📥 INPUT JSON

```json
{
  "request_id": "req_abc123",
  "text": "Allume la lampe du salon",
  "user_id": "user_001",
  "source": "voice",
  "language": "fr",
  "context": {
    "previous_classification": "conversation",
    "timestamp": "2026-01-20T10:30:00Z"
  }
}
```

**Champs obligatoires :**
- `request_id` (string) : ID unique de la requête
- `text` (string) : Texte à classifier
- `user_id` (string) : ID utilisateur
- `source` (string) : "voice" ou "text"
- `language` (string) : Code langue (fr, en, ar)

**Champs optionnels :**
- `context` (object) : Contexte conversation précédente

### 📤 OUTPUT JSON

```json
{
  "request_id": "req_abc123",
  "classification": "action",
  "confidence": 0.92,
  "method": "rules",
  "reasoning": {
    "score_conversation": 0,
    "score_action": 5,
    "keywords_found": {
      "conversation": [],
      "action": ["allume", "lampe"]
    },
    "decision_factors": [
      "Action verb detected: allume",
      "IoT device mentioned: lampe",
      "Location specified: salon"
    ]
  },
  "timestamp": "2026-01-20T10:30:01Z"
}
```

**Champs obligatoires :**
- `request_id` (string) : Même ID que l'input
- `classification` (string) : **"conversation"** ou **"action"**
- `confidence` (float) : 0.0 à 1.0
- `method` (string) : "rules", "ml" ou "llm"

**Champs optionnels :**
- `reasoning` (object) : Détails du raisonnement
- `timestamp` (string) : Date/heure ISO 8601

### 🧪 TEST SIMPLE

**Fichier :** `test_classifier.py`

```python
# Test 1: Classification Conversation
input_1 = {
    "request_id": "test_001",
    "text": "Bonjour, comment vas-tu ?",
    "user_id": "user_test",
    "source": "text",
    "language": "fr"
}

output_1 = classifier.classify(input_1)

assert output_1["classification"] == "conversation"
assert output_1["confidence"] > 0.7
print("✅ Test 1 passed: Conversation detected")

# Test 2: Classification Action
input_2 = {
    "request_id": "test_002",
    "text": "Allume la lampe du salon",
    "user_id": "user_test",
    "source": "text",
    "language": "fr"
}

output_2 = classifier.classify(input_2)

assert output_2["classification"] == "action"
assert output_2["confidence"] > 0.8
print("✅ Test 2 passed: Action detected")
```

**Dataset de test :**

| Texte | Classification attendue | Confidence min |
|-------|------------------------|----------------|
| "Salut, ça va ?" | conversation | 0.7 |
| "Qui es-tu ?" | conversation | 0.7 |
| "Allume la lampe" | action | 0.8 |
| "Envoie un email à Jean" | action | 0.8 |
| "Quelle heure est-il ?" | conversation | 0.6 |
| "Éteins le chauffage" | action | 0.9 |
| "Merci beaucoup" | conversation | 0.8 |
| "Rappelle-moi dans 30 minutes" | action | 0.8 |

**Méthode suggérée :** Classification par **mots-clés et règles** (rapide, MVP)

---

## 📦 COMPOSANT 2 - STT Engine

**Responsable :** Omar  
**Priorité :** 🔴 CRITIQUE  
**Temps estimé :** 15h

### 📥 INPUT JSON

```json
{
  "request_id": "req_audio_001",
  "audio_data": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
  "audio_format": "wav",
  "audio_metadata": {
    "sample_rate": 16000,
    "channels": 1,
    "duration_seconds": 3.5
  },
  "language": "fr",
  "user_id": "user_001"
}
```

**Champs obligatoires :**
- `request_id` (string) : ID unique
- `audio_data` (string) : Audio encodé en **base64**
- `audio_format` (string) : "wav", "mp3", "ogg"
- `language` (string) : Langue pour transcription

**Champs optionnels :**
- `audio_metadata` (object) : Métadonnées audio
- `user_id` (string) : ID utilisateur

### 📤 OUTPUT JSON

```json
{
  "request_id": "req_audio_001",
  "transcription": "Allume la lampe du salon",
  "language": "fr",
  "confidence": 0.95,
  "processing_time_ms": 1247,
  "model_used": "whisper-base",
  "alternatives": [
    {
      "text": "Alumne la lampe du salon",
      "confidence": 0.45
    }
  ],
  "audio_metadata": {
    "duration_seconds": 3.5,
    "detected_silence": false
  },
  "timestamp": "2026-01-20T10:30:02Z"
}
```

**Champs obligatoires :**
- `request_id` (string) : Même ID que l'input
- `transcription` (string) : **Texte transcrit**
- `language` (string) : Langue détectée
- `confidence` (float) : 0.0 à 1.0

**Champs optionnels :**
- `processing_time_ms` (int) : Temps de traitement
- `model_used` (string) : Modèle utilisé
- `alternatives` (array) : Transcriptions alternatives
- `timestamp` (string) : Date/heure ISO 8601

### 🧪 TEST SIMPLE

**Fichier :** `test_stt_engine.py`

```python
import base64

# Test 1: Audio WAV simple
with open("test_audio_bonjour.wav", "rb") as f:
    audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

input_1 = {
    "request_id": "test_stt_001",
    "audio_data": audio_base64,
    "audio_format": "wav",
    "language": "fr"
}

output_1 = stt_engine.transcribe(input_1)

assert "bonjour" in output_1["transcription"].lower()
assert output_1["confidence"] > 0.7
print(f"✅ Test 1 passed: '{output_1['transcription']}'")

# Test 2: Audio avec commande IoT
with open("test_audio_allume_lampe.wav", "rb") as f:
    audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

input_2 = {
    "request_id": "test_stt_002",
    "audio_data": audio_base64,
    "audio_format": "wav",
    "language": "fr"
}

output_2 = stt_engine.transcribe(input_2)

assert "lampe" in output_2["transcription"].lower()
print(f"✅ Test 2 passed: '{output_2['transcription']}'")
```

**Fichiers audio de test nécessaires :**
- `test_audio_bonjour.wav` (1-2 secondes)
- `test_audio_allume_lampe.wav` (2-3 secondes)
- `test_audio_silence.wav` (silence)

**Modèle recommandé :** OpenAI Whisper (model "base" ou "small")

---

## 📦 COMPOSANT 3 - TTS Engine

**Responsable :** Omar  
**Priorité :** 🟠 HAUTE  
**Temps estimé :** 10h

### 📥 INPUT JSON

```json
{
  "request_id": "req_tts_001",
  "text": "La lampe du salon a été allumée avec succès.",
  "language": "fr",
  "voice_config": {
    "gender": "female",
    "speed": 1.0,
    "pitch": 1.0
  },
  "output_format": "mp3",
  "user_id": "user_001"
}
```

**Champs obligatoires :**
- `request_id` (string) : ID unique
- `text` (string) : Texte à synthétiser
- `language` (string) : Langue de synthèse

**Champs optionnels :**
- `voice_config` (object) : Configuration voix
- `output_format` (string) : "mp3", "wav" (défaut: mp3)
- `user_id` (string) : ID utilisateur

### 📤 OUTPUT JSON

```json
{
  "request_id": "req_tts_001",
  "audio_data": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Lj...",
  "audio_format": "mp3",
  "audio_metadata": {
    "size_bytes": 15234,
    "duration_seconds": 3.2,
    "sample_rate": 24000,
    "bitrate": 32000
  },
  "text_length": 48,
  "language": "fr",
  "processing_time_ms": 523,
  "engine_used": "gtts",
  "timestamp": "2026-01-20T10:30:03Z"
}
```

**Champs obligatoires :**
- `request_id` (string) : Même ID que l'input
- `audio_data` (string) : Audio encodé en **base64**
- `audio_format` (string) : Format généré
- `audio_metadata` (object) : Métadonnées audio

**Champs optionnels :**
- `processing_time_ms` (int) : Temps de traitement
- `engine_used` (string) : Moteur utilisé
- `timestamp` (string) : Date/heure ISO 8601

### 🧪 TEST SIMPLE

**Fichier :** `test_tts_engine.py`

```python
import base64

# Test 1: Synthèse française simple
input_1 = {
    "request_id": "test_tts_001",
    "text": "Bonjour, comment allez-vous ?",
    "language": "fr",
    "output_format": "mp3"
}

output_1 = tts_engine.synthesize(input_1)

assert output_1["audio_data"] != ""
assert output_1["audio_format"] == "mp3"
assert output_1["audio_metadata"]["duration_seconds"] > 0

# Sauvegarder pour écoute manuelle
audio_bytes = base64.b64decode(output_1["audio_data"])
with open("test_output_bonjour.mp3", "wb") as f:
    f.write(audio_bytes)

print(f"✅ Test 1 passed: Audio généré ({output_1['audio_metadata']['size_bytes']} bytes)")

# Test 2: Texte plus long
input_2 = {
    "request_id": "test_tts_002",
    "text": "La lampe du salon a été allumée avec succès. Température actuelle : 22 degrés.",
    "language": "fr",
    "output_format": "mp3"
}

output_2 = tts_engine.synthesize(input_2)

assert output_2["audio_metadata"]["duration_seconds"] > 2
print(f"✅ Test 2 passed: Texte long synthétisé")
```

**Moteur recommandé :** gTTS (Google Text-to-Speech) ou pyttsx3

---

## 📦 COMPOSANT 4 - LLM Client

**Responsable :** Montassar  
**Priorité :** 🔴 CRITIQUE  
**Temps estimé :** 25h

### 📥 INPUT JSON (Conversation)

```json
{
  "request_id": "req_llm_001",
  "mode": "conversation",
  "input_text": "Qui es-tu ?",
  "user_id": "user_001",
  "language": "fr",
  "context": {
    "conversation_history": [
      {
        "role": "user",
        "content": "Bonjour"
      },
      {
        "role": "assistant",
        "content": "Bonjour ! Comment puis-je vous aider ?"
      }
    ]
  }
}
```

### 📥 INPUT JSON (Analyse Action)

```json
{
  "request_id": "req_llm_002",
  "mode": "intent_analysis",
  "input_text": "Allume la lampe du salon et ferme les volets",
  "user_id": "user_001",
  "language": "fr",
  "analysis_config": {
    "extract_entities": true,
    "detect_multiple_intents": true,
    "confidence_threshold": 0.7
  }
}
```

**Champs obligatoires :**
- `request_id` (string) : ID unique
- `mode` (string) : **"conversation"** ou **"intent_analysis"**
- `input_text` (string) : Texte à analyser
- `language` (string) : Langue

**Champs optionnels :**
- `user_id` (string) : ID utilisateur
- `context` (object) : Contexte conversation (mode conversation)
- `analysis_config` (object) : Config analyse (mode intent)

### 📤 OUTPUT JSON (Conversation)

```json
{
  "request_id": "req_llm_001",
  "mode": "conversation",
  "response": "Je suis un assistant vocal intelligent conçu pour vous aider dans vos tâches quotidiennes.",
  "model_used": "gpt-3.5-turbo",
  "tokens_used": 45,
  "processing_time_ms": 1234,
  "timestamp": "2026-01-20T10:30:04Z"
}
```

### 📤 OUTPUT JSON (Analyse Action)

```json
{
  "request_id": "req_llm_002",
  "mode": "intent_analysis",
  "primary_intent": "control_iot",
  "confidence": 0.94,
  "entities": {
    "devices": [
      {
        "type": "light",
        "name": "lampe",
        "location": "salon",
        "action": "turn_on"
      },
      {
        "type": "shutter",
        "name": "volets",
        "location": null,
        "action": "close"
      }
    ]
  },
  "secondary_intents": [],
  "language": "fr",
  "model_used": "gpt-3.5-turbo",
  "tokens_used": 78,
  "processing_time_ms": 1567,
  "timestamp": "2026-01-20T10:30:05Z"
}
```

**Champs obligatoires (Conversation) :**
- `request_id` (string) : Même ID que l'input
- `mode` (string) : "conversation"
- `response` (string) : Réponse générée

**Champs obligatoires (Intent Analysis) :**
- `request_id` (string) : Même ID que l'input
- `mode` (string) : "intent_analysis"
- `primary_intent` (string) : Intent détecté ("control_iot", "send_email", "set_reminder", "web_search")
- `confidence` (float) : 0.0 à 1.0
- `entities` (object) : Entités extraites

### 🧪 TEST SIMPLE

**Fichier :** `test_llm_client.py`

```python
# Test 1: Conversation simple
input_1 = {
    "request_id": "test_llm_001",
    "mode": "conversation",
    "input_text": "Bonjour, ça va ?",
    "language": "fr"
}

output_1 = llm_client.process(input_1)

assert output_1["mode"] == "conversation"
assert len(output_1["response"]) > 10
assert "bonjour" in output_1["response"].lower() or "salut" in output_1["response"].lower()
print(f"✅ Test 1 passed: '{output_1['response']}'")

# Test 2: Analyse intent IoT
input_2 = {
    "request_id": "test_llm_002",
    "mode": "intent_analysis",
    "input_text": "Allume la lampe du salon",
    "language": "fr",
    "analysis_config": {
        "extract_entities": True
    }
}

output_2 = llm_client.process(input_2)

assert output_2["primary_intent"] == "control_iot"
assert output_2["confidence"] > 0.7
assert "devices" in output_2["entities"]
assert any("lampe" in d.get("name", "").lower() for d in output_2["entities"]["devices"])
print(f"✅ Test 2 passed: Intent={output_2['primary_intent']}, Entities={output_2['entities']}")

# Test 3: Analyse intent email
input_3 = {
    "request_id": "test_llm_003",
    "mode": "intent_analysis",
    "input_text": "Envoie un email à Jean pour lui dire que je serai en retard",
    "language": "fr"
}

output_3 = llm_client.process(input_3)

assert output_3["primary_intent"] == "send_email"
assert "recipient" in str(output_3["entities"])
print(f"✅ Test 3 passed: Intent={output_3['primary_intent']}")
```

**Modèle recommandé :** OpenAI GPT-3.5-turbo (ou GPT-4 si budget)

---

## 📦 COMPOSANT 5 - Action Builder

**Responsable :** Amine  
**Priorité :** 🔴 CRITIQUE  
**Temps estimé :** 20h

### 📥 INPUT JSON

```json
{
  "request_id": "req_builder_001",
  "user_id": "user_001",
  "intent": "control_iot",
  "entities": {
    "devices": [
      {
        "type": "light",
        "name": "lampe",
        "location": "salon",
        "action": "turn_on"
      }
    ]
  },
  "original_text": "Allume la lampe du salon",
  "confidence": 0.94,
  "language": "fr"
}
```

**Champs obligatoires :**
- `request_id` (string) : ID unique
- `user_id` (string) : ID utilisateur
- `intent` (string) : "control_iot", "send_email", "set_reminder", "web_search"
- `entities` (object) : Entités extraites par LLM
- `original_text` (string) : Commande originale utilisateur

**Champs optionnels :**
- `confidence` (float) : Confiance de l'analyse
- `language` (string) : Langue

### 📤 OUTPUT JSON (ActionJSON COMPLET)

```json
{
  "action_id": "act_abc123xyz",
  "user_id": "user_001",
  "request_id": "req_builder_001",
  "intent": "control_iot",
  "confirmed": false,
  "state": "DRAFT",
  "payload": {
    "device_id": "lamp_salon_001",
    "device_type": "light",
    "action": "turn_on",
    "location": "salon",
    "parameters": {
      "brightness": 100
    }
  },
  "context": {
    "original_command": "Allume la lampe du salon",
    "language": "fr",
    "source": "voice",
    "confidence": 0.94
  },
  "security": {
    "user_token": null,
    "signature": null,
    "signature_algorithm": "HMAC-SHA256"
  },
  "timestamps": {
    "created_at": "2026-01-20T10:30:06Z",
    "updated_at": "2026-01-20T10:30:06Z",
    "confirmed_at": null,
    "executed_at": null
  },
  "metadata": {
    "priority": "normal",
    "timeout_seconds": 30,
    "retry_count": 0,
    "max_retries": 3
  }
}
```

**Champs obligatoires :**
- `action_id` (string) : ID unique généré (format: "act_XXXXX")
- `user_id` (string) : ID utilisateur
- `request_id` (string) : ID requête originale
- `intent` (string) : Type d'action
- `confirmed` (boolean) : **false** (toujours DRAFT initialement)
- `state` (string) : **"DRAFT"** (état initial)
- `payload` (object) : Détails spécifiques à l'intent
- `timestamps` (object) : Horodatages

### 📤 EXEMPLES PAYLOADS PAR INTENT

**Intent: control_iot**
```json
{
  "payload": {
    "device_id": "lamp_kitchen_001",
    "device_type": "light",
    "action": "turn_off",
    "location": "kitchen",
    "parameters": {
      "transition_time": 2
    }
  }
}
```

**Intent: send_email**
```json
{
  "payload": {
    "recipient_email": "jean@example.com",
    "recipient_name": "Jean",
    "subject": "Retard ce matin",
    "body": "Bonjour Jean, je serai en retard ce matin. Désolé.",
    "priority": "normal",
    "attachments": []
  }
}
```

**Intent: set_reminder**
```json
{
  "payload": {
    "title": "Appeler le médecin",
    "description": null,
    "reminder_time": "2026-01-20T14:30:00Z",
    "recurrence": null,
    "notification_channels": ["voice", "push"]
  }
}
```

**Intent: web_search**
```json
{
  "payload": {
    "query": "météo Paris demain",
    "search_type": "weather",
    "max_results": 3,
    "language": "fr"
  }
}
```

### 🧪 TEST SIMPLE

**Fichier :** `test_action_builder.py`

```python
# Test 1: Build ActionJSON pour IoT
input_1 = {
    "request_id": "test_build_001",
    "user_id": "user_test",
    "intent": "control_iot",
    "entities": {
        "devices": [
            {
                "type": "light",
                "name": "lampe",
                "location": "salon",
                "action": "turn_on"
            }
        ]
    },
    "original_text": "Allume la lampe du salon"
}

output_1 = action_builder.build(input_1)

assert output_1["action_id"].startswith("act_")
assert output_1["intent"] == "control_iot"
assert output_1["confirmed"] == False
assert output_1["state"] == "DRAFT"
assert "device_id" in output_1["payload"]
assert output_1["payload"]["action"] == "turn_on"
print(f"✅ Test 1 passed: ActionJSON créé avec action_id={output_1['action_id']}")

# Test 2: Build ActionJSON pour email
input_2 = {
    "request_id": "test_build_002",
    "user_id": "user_test",
    "intent": "send_email",
    "entities": {
        "recipient": "Jean",
        "recipient_email": "jean@example.com",
        "subject": "Réunion",
        "body": "On se voit à 15h"
    },
    "original_text": "Envoie un email à Jean"
}

output_2 = action_builder.build(input_2)

assert output_2["intent"] == "send_email"
assert output_2["payload"]["recipient_email"] == "jean@example.com"
assert output_2["payload"]["subject"] == "Réunion"
print(f"✅ Test 2 passed: Email ActionJSON créé")

# Test 3: Validation structure complète
required_fields = ["action_id", "user_id", "intent", "confirmed", "state", "payload", "timestamps"]
for field in required_fields:
    assert field in output_1, f"Missing field: {field}"

print(f"✅ Test 3 passed: Structure ActionJSON valide")
```

---

## 📦 COMPOSANT 6 - Confirmation Handler

**Responsable :** Amine  
**Priorité :** 🟠 HAUTE  
**Temps estimé :** 15h

### 📥 INPUT JSON

```json
{
  "action_json": {
    "action_id": "act_abc123xyz",
    "user_id": "user_001",
    "intent": "control_iot",
    "payload": {
      "device_id": "lamp_salon_001",
      "action": "turn_on",
      "location": "salon"
    },
    "state": "DRAFT"
  },
  "generate_audio": true,
  "language": "fr"
}
```

**Champs obligatoires :**
- `action_json` (object) : ActionJSON complet en état DRAFT
- `language` (string) : Langue pour génération confirmation

**Champs optionnels :**
- `generate_audio` (boolean) : Générer TTS (défaut: false)

### 📤 OUTPUT JSON (Demande Confirmation)

```json
{
  "action_id": "act_abc123xyz",
  "confirmation_text": "Voulez-vous vraiment allumer la lampe du salon ?",
  "action_summary": {
    "intent": "control_iot",
    "target": "lampe",
    "location": "salon",
    "action": "allumer"
  },
  "options": [
    {
      "response": "oui",
      "action": "confirm"
    },
    {
      "response": "non",
      "action": "cancel"
    },
    {
      "response": "modifier",
      "action": "modify"
    }
  ],
  "timeout_seconds": 30,
  "timestamp": "2026-01-20T10:30:07Z"
}
```

**Champs obligatoires :**
- `action_id` (string) : ID action
- `confirmation_text` (string) : Texte demande confirmation
- `action_summary` (object) : Résumé action
- `options` (array) : Options de réponse

### 📥 INPUT JSON (Réponse Utilisateur)

```json
{
  "action_id": "act_abc123xyz",
  "user_response": "oui",
  "user_id": "user_001",
  "timestamp": "2026-01-20T10:30:15Z"
}
```

### 📤 OUTPUT JSON (Résultat Confirmation)

```json
{
  "action_id": "act_abc123xyz",
  "parsed_response": {
    "intent": "confirm",
    "confidence": 0.98
  },
  "new_state": "CONFIRMED",
  "timestamp": "2026-01-20T10:30:16Z"
}
```

**Valeurs possibles `parsed_response.intent` :**
- **"confirm"** → État devient CONFIRMED
- **"cancel"** → État devient CANCELED
- **"modify"** → Reste DRAFT, demande modification

### 🧪 TEST SIMPLE

**Fichier :** `test_confirmation_handler.py`

```python
# Test 1: Génération demande confirmation
input_1 = {
    "action_json": {
        "action_id": "test_act_001",
        "user_id": "user_test",
        "intent": "control_iot",
        "payload": {
            "device_id": "lamp_001",
            "action": "turn_on",
            "location": "salon"
        },
        "state": "DRAFT"
    },
    "language": "fr"
}

output_1 = confirmation_handler.generate_request(input_1)

assert output_1["action_id"] == "test_act_001"
assert "allumer" in output_1["confirmation_text"].lower() or "allume" in output_1["confirmation_text"].lower()
assert len(output_1["options"]) >= 2
print(f"✅ Test 1 passed: Demande générée: '{output_1['confirmation_text']}'")

# Test 2: Parse réponse "oui"
input_2 = {
    "action_id": "test_act_001",
    "user_response": "oui",
    "user_id": "user_test"
}

output_2 = confirmation_handler.parse_response(input_2)

assert output_2["parsed_response"]["intent"] == "confirm"
assert output_2["new_state"] == "CONFIRMED"
print(f"✅ Test 2 passed: Réponse 'oui' → CONFIRMED")

# Test 3: Parse réponse "non"
input_3 = {
    "action_id": "test_act_001",
    "user_response": "non",
    "user_id": "user_test"
}

output_3 = confirmation_handler.parse_response(input_3)

assert output_3["parsed_response"]["intent"] == "cancel"
assert output_3["new_state"] == "CANCELED"
print(f"✅ Test 3 passed: Réponse 'non' → CANCELED")
```

---

## 📦 COMPOSANT 7 - State Manager

**Responsable :** Montassar  
**Priorité :** 🟠 HAUTE  
**Temps estimé :** 12h

### 📥 INPUT JSON (Créer Action)

```json
{
  "operation": "create",
  "action_json": {
    "action_id": "act_abc123xyz",
    "user_id": "user_001",
    "intent": "control_iot",
    "state": "DRAFT"
  }
}
```

### 📥 INPUT JSON (Mettre à jour état)

```json
{
  "operation": "update_state",
  "action_id": "act_abc123xyz",
  "new_state": "CONFIRMED",
  "reason": "User confirmed action"
}
```

### 📥 INPUT JSON (Récupérer action)

```json
{
  "operation": "get",
  "action_id": "act_abc123xyz"
}
```

**Opérations possibles :**
- `"create"` : Créer nouvelle action
- `"update_state"` : Changer état action
- `"get"` : Récupérer action
- `"list"` : Lister actions utilisateur
- `"delete"` : Supprimer action

### 📤 OUTPUT JSON (Get/Create)

```json
{
  "action_id": "act_abc123xyz",
  "user_id": "user_001",
  "current_state": "CONFIRMED",
  "action_json": {
    "intent": "control_iot",
    "payload": {...}
  },
  "state_history": [
    {
      "state": "DRAFT",
      "timestamp": "2026-01-20T10:30:06Z"
    },
    {
      "state": "PENDING_CONFIRMATION",
      "timestamp": "2026-01-20T10:30:07Z"
    },
    {
      "state": "CONFIRMED",
      "timestamp": "2026-01-20T10:30:16Z",
      "reason": "User confirmed action"
    }
  ],
  "created_at": "2026-01-20T10:30:06Z",
  "updated_at": "2026-01-20T10:30:16Z"
}
```

**États possibles (ordre logique) :**
1. **IDLE** : Aucune action en cours
2. **DRAFT** : Action créée, pas confirmée
3. **PENDING_CONFIRMATION** : En attente confirmation utilisateur
4. **CONFIRMED** : Confirmée, prête pour exécution
5. **EXECUTING** : En cours d'exécution par n8n
6. **COMPLETED** : Exécutée avec succès
7. **FAILED** : Échec d'exécution
8. **CANCELED** : Annulée par utilisateur

### 🧪 TEST SIMPLE

**Fichier :** `test_state_manager.py`

```python
# Test 1: Créer action
input_1 = {
    "operation": "create",
    "action_json": {
        "action_id": "test_state_001",
        "user_id": "user_test",
        "intent": "control_iot",
        "state": "DRAFT"
    }
}

output_1 = state_manager.execute(input_1)

assert output_1["action_id"] == "test_state_001"
assert output_1["current_state"] == "DRAFT"
assert len(output_1["state_history"]) == 1
print(f"✅ Test 1 passed: Action créée en état DRAFT")

# Test 2: Transition valide DRAFT → CONFIRMED
input_2 = {
    "operation": "update_state",
    "action_id": "test_state_001",
    "new_state": "CONFIRMED",
    "reason": "Test confirmation"
}

output_2 = state_manager.execute(input_2)

assert output_2["current_state"] == "CONFIRMED"
assert len(output_2["state_history"]) == 2
print(f"✅ Test 2 passed: Transition DRAFT → CONFIRMED")

# Test 3: Transition invalide (doit échouer)
input_3 = {
    "operation": "update_state",
    "action_id": "test_state_001",
    "new_state": "IDLE"  # Impossible depuis CONFIRMED
}

try:
    output_3 = state_manager.execute(input_3)
    assert False, "Transition invalide devrait lever une exception"
except Exception as e:
    print(f"✅ Test 3 passed: Transition invalide rejetée ({str(e)})")

# Test 4: Récupérer action
input_4 = {
    "operation": "get",
    "action_id": "test_state_001"
}

output_4 = state_manager.execute(input_4)

assert output_4["action_id"] == "test_state_001"
assert output_4["current_state"] == "CONFIRMED"
print(f"✅ Test 4 passed: Action récupérée")
```

**Transitions valides :**
- DRAFT → PENDING_CONFIRMATION → CONFIRMED/CANCELED
- CONFIRMED → EXECUTING → COMPLETED/FAILED

---

## 📦 COMPOSANT 8 - Security Manager

**Responsable :** Amine  
**Priorité :** 🟠 HAUTE  
**Temps estimé :** 10h

### 📥 INPUT JSON (Signer ActionJSON)

```json
{
  "operation": "sign",
  "action_json": {
    "action_id": "act_abc123xyz",
    "user_id": "user_001",
    "intent": "control_iot",
    "state": "CONFIRMED",
    "payload": {...}
  },
  "algorithm": "HMAC-SHA256"
}
```

### 📥 INPUT JSON (Vérifier signature)

```json
{
  "operation": "verify",
  "action_json": {
    "action_id": "act_abc123xyz",
    ...
  },
  "signature": "a3f5d9b2c1e4..."
}
```

**Opérations possibles :**
- `"sign"` : Signer ActionJSON
- `"verify"` : Vérifier signature
- `"generate_token"` : Générer JWT utilisateur
- `"verify_token"` : Vérifier JWT

### 📤 OUTPUT JSON (Sign)

```json
{
  "action_id": "act_abc123xyz",
  "signature": "a3f5d9b2c1e4f7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3",
  "algorithm": "HMAC-SHA256",
  "signed_at": "2026-01-20T10:30:17Z",
  "expires_at": "2026-01-20T11:00:17Z"
}
```

### 📤 OUTPUT JSON (Verify)

```json
{
  "valid": true,
  "action_id": "act_abc123xyz",
  "verified_at": "2026-01-20T10:30:18Z",
  "message": "Signature verified successfully"
}
```

### 🧪 TEST SIMPLE

**Fichier :** `test_security_manager.py`

```python
import json

# Test 1: Signer ActionJSON
input_1 = {
    "operation": "sign",
    "action_json": {
        "action_id": "test_sec_001",
        "user_id": "user_test",
        "intent": "control_iot",
        "state": "CONFIRMED",
        "payload": {
            "device_id": "lamp_001",
            "action": "turn_on"
        }
    },
    "algorithm": "HMAC-SHA256"
}

output_1 = security_manager.execute(input_1)

assert output_1["signature"] != ""
assert len(output_1["signature"]) == 64  # SHA256 = 64 hex chars
print(f"✅ Test 1 passed: Signature générée: {output_1['signature'][:16]}...")

# Test 2: Vérifier signature valide
input_2 = {
    "operation": "verify",
    "action_json": input_1["action_json"],
    "signature": output_1["signature"]
}

output_2 = security_manager.execute(input_2)

assert output_2["valid"] == True
print(f"✅ Test 2 passed: Signature valide")

# Test 3: Vérifier signature invalide
input_3 = {
    "operation": "verify",
    "action_json": input_1["action_json"],
    "signature": "invalid_signature_123"
}

output_3 = security_manager.execute(input_3)

assert output_3["valid"] == False
print(f"✅ Test 3 passed: Signature invalide détectée")

# Test 4: Même ActionJSON → Même signature (déterministe)
output_4 = security_manager.execute(input_1)
assert output_4["signature"] == output_1["signature"]
print(f"✅ Test 4 passed: Signature déterministe")
```

**Algorithme recommandé :** HMAC-SHA256 avec clé secrète

---

## 📦 COMPOSANT 9 - n8n Client

**Responsable :** Amine  
**Priorité :** 🟢 MOYENNE  
**Temps estimé :** 8h

### 📥 INPUT JSON

```json
{
  "action_json": {
    "action_id": "act_abc123xyz",
    "user_id": "user_001",
    "intent": "control_iot",
    "confirmed": true,
    "state": "CONFIRMED",
    "payload": {...},
    "security": {
      "signature": "a3f5d9b2c1e4..."
    }
  },
  "webhook_url": "http://localhost:5678/webhook/action",
  "timeout_seconds": 60
}
```

**Champs obligatoires :**
- `action_json` (object) : ActionJSON CONFIRMED + signé
- `webhook_url` (string) : URL webhook n8n

### 📤 OUTPUT JSON

```json
{
  "action_id": "act_abc123xyz",
  "status": "sent",
  "n8n_response": {
    "execution_id": "n8n_exec_001",
    "status": "accepted",
    "message": "Action received and queued"
  },
  "sent_at": "2026-01-20T10:30:19Z",
  "response_time_ms": 345
}
```

**Statuts possibles :**
- `"sent"` : Envoyé avec succès
- `"failed"` : Échec envoi
- `"timeout"` : Timeout

### 🧪 TEST SIMPLE

**Fichier :** `test_n8n_client.py`

```python
# Test 1: Envoyer ActionJSON (avec n8n mocké)
input_1 = {
    "action_json": {
        "action_id": "test_n8n_001",
        "user_id": "user_test",
        "intent": "control_iot",
        "confirmed": True,
        "state": "CONFIRMED",
        "payload": {
            "device_id": "lamp_001",
            "action": "turn_on"
        },
        "security": {
            "signature": "test_signature_123"
        }
    },
    "webhook_url": "http://localhost:5678/webhook/action",
    "timeout_seconds": 10
}

output_1 = n8n_client.send(input_1)

assert output_1["status"] == "sent"
assert "n8n_response" in output_1
print(f"✅ Test 1 passed: ActionJSON envoyé vers n8n")

# Test 2: Gestion timeout (avec URL invalide)
input_2 = input_1.copy()
input_2["webhook_url"] = "http://invalid-url:9999/webhook"
input_2["timeout_seconds"] = 2

output_2 = n8n_client.send(input_2)

assert output_2["status"] in ["failed", "timeout"]
print(f"✅ Test 2 passed: Timeout géré ({output_2['status']})")
```

**Note :** Pour les tests, vous pouvez mocker le serveur n8n ou utiliser un webhook de test.

---

## 📦 COMPOSANT 10 - MQTT Client

**Responsable :** Omar  
**Priorité :** 🟢 MOYENNE  
**Temps estimé :** 12h

### 📥 INPUT JSON (Publier message)

```json
{
  "operation": "publish",
  "topic": "esp32/command/lamp_001",
  "message": {
    "device_id": "lamp_001",
    "action": "turn_on",
    "timestamp": "2026-01-20T10:30:20Z"
  },
  "qos": 1,
  "retain": false
}
```

### 📥 INPUT JSON (S'abonner à topic)

```json
{
  "operation": "subscribe",
  "topic": "esp32/status/#",
  "qos": 1
}
```

**Opérations possibles :**
- `"publish"` : Publier message
- `"subscribe"` : S'abonner à topic
- `"unsubscribe"` : Se désabonner

### 📤 OUTPUT JSON (Publish)

```json
{
  "status": "published",
  "topic": "esp32/command/lamp_001",
  "message_id": "mqtt_msg_001",
  "published_at": "2026-01-20T10:30:20Z"
}
```

### 📤 OUTPUT JSON (Message reçu - Callback)

```json
{
  "topic": "esp32/status/lamp_001",
  "message": {
    "device_id": "lamp_001",
    "status": "on",
    "timestamp": "2026-01-20T10:30:21Z"
  },
  "received_at": "2026-01-20T10:30:21Z"
}
```

### 🧪 TEST SIMPLE

**Fichier :** `test_mqtt_client.py`

```python
import time

# Test 1: Publier message
input_1 = {
    "operation": "publish",
    "topic": "test/topic",
    "message": {
        "test": "hello",
        "value": 123
    },
    "qos": 1
}

output_1 = mqtt_client.execute(input_1)

assert output_1["status"] == "published"
print(f"✅ Test 1 passed: Message publié sur topic 'test/topic'")

# Test 2: S'abonner et recevoir message
messages_received = []

def callback(message):
    messages_received.append(message)

input_2 = {
    "operation": "subscribe",
    "topic": "test/topic",
    "qos": 1
}

mqtt_client.set_callback(callback)
mqtt_client.execute(input_2)

# Publier message de test
mqtt_client.execute(input_1)

# Attendre réception
time.sleep(1)

assert len(messages_received) > 0
assert messages_received[0]["message"]["test"] == "hello"
print(f"✅ Test 2 passed: Message reçu via callback")
```

**Broker recommandé :** Mosquitto (local ou public test.mosquitto.org)

---

## 📦 COMPOSANT 11 - Agent Core

**Responsable :** Montassar  
**Priorité :** 🔴 CRITIQUE  
**Temps estimé :** 30h

### 📥 INPUT JSON (Commande texte)

```json
{
  "command_type": "text",
  "user_id": "user_001",
  "text": "Allume la lampe du salon",
  "language": "fr",
  "source": "text"
}
```

### 📥 INPUT JSON (Commande audio)

```json
{
  "command_type": "audio",
  "user_id": "user_001",
  "audio_data": "UklGRiQAAABXQVZFZm10...",
  "audio_format": "wav",
  "language": "fr",
  "source": "voice"
}
```

### 📤 OUTPUT JSON

```json
{
  "request_id": "req_abc123",
  "user_id": "user_001",
  "classification": "action",
  "response": {
    "type": "action",
    "action_id": "act_abc123xyz",
    "state": "PENDING_CONFIRMATION",
    "message": "Voulez-vous vraiment allumer la lampe du salon ?",
    "audio_response": "UklGRiQAAABXQVZFZm10..." 
  },
  "processing_time_ms": 2345,
  "timestamp": "2026-01-20T10:30:22Z"
}
```

**OU (si Conversation)**

```json
{
  "request_id": "req_abc124",
  "user_id": "user_001",
  "classification": "conversation",
  "response": {
    "type": "conversation",
    "message": "Bonjour ! Je suis votre assistant vocal. Comment puis-je vous aider ?",
    "audio_response": "UklGRiQAAABXQVZFZm10..."
  },
  "processing_time_ms": 1234,
  "timestamp": "2026-01-20T10:30:23Z"
}
```

### 🧪 TEST SIMPLE

**Fichier :** `test_agent_core.py`

```python
# Test 1: Commande conversation
input_1 = {
    "command_type": "text",
    "user_id": "user_test",
    "text": "Bonjour, comment vas-tu ?",
    "language": "fr"
}

output_1 = agent_core.process(input_1)

assert output_1["classification"] == "conversation"
assert output_1["response"]["type"] == "conversation"
assert len(output_1["response"]["message"]) > 0
print(f"✅ Test 1 passed: Conversation traitée: '{output_1['response']['message']}'")

# Test 2: Commande action
input_2 = {
    "command_type": "text",
    "user_id": "user_test",
    "text": "Allume la lampe du salon",
    "language": "fr"
}

output_2 = agent_core.process(input_2)

assert output_2["classification"] == "action"
assert output_2["response"]["type"] == "action"
assert "action_id" in output_2["response"]
assert output_2["response"]["state"] in ["PENDING_CONFIRMATION", "DRAFT"]
print(f"✅ Test 2 passed: Action créée: {output_2['response']['action_id']}")
```

**Note :** Agent Core utilise TOUS les autres composants. C'est le dernier à implémenter après que tous les autres fonctionnent.

---

## 5. Règles de validation et tests

### 5.1 Règles communes pour tous les composants

**📋 Checklist de validation :**

✅ **INPUT JSON valide**
- Tous les champs obligatoires présents
- Types corrects (string, int, float, boolean, object, array)
- Valeurs dans les plages autorisées

✅ **OUTPUT JSON valide**
- Structure conforme à la spécification
- Champs obligatoires présents
- Format cohérent (timestamps ISO 8601, etc.)

✅ **Gestion erreurs**
- Exceptions levées si INPUT invalide
- Messages d'erreur clairs
- Codes d'erreur standardisés

✅ **Tests unitaires**
- Minimum 3 tests par composant
- Test cas nominal (happy path)
- Test cas d'erreur
- Test edge cases

✅ **Documentation**
- Docstring pour chaque fonction
- README.md avec exemples
- Dépendances listées

### 5.2 Format des tests

**Structure recommandée :**

```python
# test_COMPOSANT.py

import pytest
from composant import Composant

@pytest.fixture
def composant():
    """Fixture pour initialiser le composant."""
    return Composant()

def test_nominal_case(composant):
    """Test cas nominal."""
    input_data = {...}
    output = composant.process(input_data)
    assert output["status"] == "success"

def test_error_case(composant):
    """Test cas d'erreur."""
    input_data = {"invalid": True}
    with pytest.raises(ValidationError):
        composant.process(input_data)

def test_edge_case(composant):
    """Test cas limite."""
    input_data = {"text": ""}  # Texte vide
    output = composant.process(input_data)
    assert "error" in output
```

### 5.3 Données de test mockées

Chaque composant doit inclure un dossier `tests/fixtures/` avec des JSON de test :

```
tests/
├── fixtures/
│   ├── input_conversation.json
│   ├── input_action_iot.json
│   ├── input_action_email.json
│   ├── output_classification.json
│   └── ...
└── test_composant.py
```

---

## 6. Workflow d'assemblage

### 6.1 Structure GitHub

```
pcd-ai-embedded-agent/
├── backend/
│   ├── classifier/
│   │   ├── intent_classifier.py
│   │   ├── tests/
│   │   └── README.md
│   ├── ai/
│   │   ├── stt_engine.py
│   │   ├── tts_engine.py
│   │   ├── llm_client.py
│   │   ├── tests/
│   │   └── README.md
│   ├── actions/
│   │   ├── action_builder.py
│   │   ├── confirmation_handler.py
│   │   ├── tests/
│   │   └── README.md
│   ├── agent/
│   │   ├── agent_core.py
│   │   ├── state_manager.py
│   │   ├── security_manager.py
│   │   ├── tests/
│   │   └── README.md
│   ├── integrations/
│   │   ├── n8n_client.py
│   │   ├── mqtt_client.py
│   │   ├── tests/
│   │   └── README.md
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
└── README.md
```

### 6.2 Branches Git

**Chaque personne travaille sur sa branche :**

```bash
# Montassar
git checkout -b feature/classifier
git checkout -b feature/llm-client
git checkout -b feature/agent-core
git checkout -b feature/state-manager

# Amine
git checkout -b feature/action-builder
git checkout -b feature/confirmation-handler
git checkout -b feature/security-manager
git checkout -b feature/n8n-client

# Omar
git checkout -b feature/stt-engine
git checkout -b feature/tts-engine
git checkout -b feature/mqtt-client
```

### 6.3 Process de merge

**Étape 1 - Développement individuel (Semaines 1-3)**
- Chacun développe ses composants en local
- Tests unitaires valident chaque composant
- Push sur branche feature/XXX

**Étape 2 - Review croisée (Semaine 4)**
- Pull requests créées
- Review de code par les autres membres
- Corrections si nécessaire

**Étape 3 - Intégration progressive (Semaine 5)**
- Merge composants par composants
- Tests d'intégration entre composants
- Résolution conflits

**Étape 4 - Assemblage final (Semaine 6)**
- Agent Core connecte tous les composants
- Tests end-to-end
- Backend complet fonctionnel

---

## 📊 Résumé Distribution

| Personne | Composants | Charge estimée | Priorité |
|----------|-----------|----------------|----------|
| **Montassar** | Classifier, LLM Client, Agent Core, State Manager | 87h | 🔴 CRITIQUE |
| **Amine** | Action Builder, Confirmation Handler, Security Manager, n8n Client | 53h | 🟠 HAUTE |
| **Omar** | STT Engine, TTS Engine, MQTT Client | 37h | 🟠 HAUTE |
| **TOTAL** | 11 composants Backend | **177h** | - |

**Durée estimée :** 6 semaines (3 semaines dev + 1 semaine review + 2 semaines intégration)

---

## ✅ Checklist finale avant soutenance

**Pour chaque composant :**

- [ ] INPUT JSON specs clairement défini
- [ ] OUTPUT JSON specs clairement défini
- [ ] Code implémenté et testé
- [ ] Tests unitaires passants (≥3 tests)
- [ ] README.md avec exemples
- [ ] Pushed sur GitHub
- [ ] Pull request créée
- [ ] Code reviewé par au moins 1 autre personne
- [ ] Intégré dans main branch
- [ ] Tests d'intégration avec autres composants
- [ ] Documentation mise à jour

**Pour le Backend complet :**

- [ ] Tous les composants fonctionnels individuellement
- [ ] Agent Core orchestre tous les composants
- [ ] Tests end-to-end passants
- [ ] Documentation architecture complète
- [ ] API REST fonctionnelle (routes FastAPI)
- [ ] Logs et monitoring opérationnels
- [ ] Gestion erreurs robuste
- [ ] Prêt pour intégration avec n8n et ESP32

---

**Document créé le : 20 janvier 2026**  
**Version : 1.0 - Spécifications Interfaces JSON Backend**  
**Statut : PRÊT pour distribution équipe**

**Bonne chance pour le développement ! 🚀**
