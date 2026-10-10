# 📋 Spécification Complète des Formats JSON - Contrats Inter-Modules
## Projet PCD – Agent Intelligent Embarqué

**Version :** 3.0 - Référentiel Complet  
**Date :** 20 janvier 2026  
**Objectif :** Document de référence pour tous les formats JSON échangés entre modules

---

## 📑 Table des Matières

1. [Principe fondamental des échanges](#1-principe-fondamental-des-échanges)
2. [Flux 0 - Classification Interne Python](#2-flux-0---classification-interne-python)
3. [Flux Conversation - Backend Uniquement](#3-flux-conversation---backend-uniquement)
4. [Flux 1 - Python → LLM (Analyse Linguistique)](#4-flux-1---python--llm-analyse-linguistique)
5. [Flux 2 - LLM → Python (Résultat Analyse)](#5-flux-2---llm--python-résultat-analyse)
6. [Flux 3 - Python Interne (Construction ActionJSON)](#6-flux-3---python-interne-construction-actionjson)
7. [Flux 4 - Confirmation Utilisateur](#7-flux-4---confirmation-utilisateur)
8. [Flux 5 - Python → n8n (Exécution Contrôlée)](#8-flux-5---python--n8n-exécution-contrôlée)
9. [Flux 6 - n8n → ESP32 (Commande Physique)](#9-flux-6---n8n--esp32-commande-physique)
10. [Flux 7 - ESP32 → n8n (Retour État)](#10-flux-7---esp32--n8n-retour-état)
11. [Flux 8 - n8n → Python (Résultat Final)](#11-flux-8---n8n--python-résultat-final)
12. [Flux ESP32 → Python (Audio Brut)](#12-flux-esp32--python-audio-brut)
13. [Flux Python → ESP32 (Audio Réponse)](#13-flux-python--esp32-audio-réponse)
14. [Schémas JSON Réutilisables](#14-schémas-json-réutilisables)
15. [Règles de Validation](#15-règles-de-validation)
16. [Exemples Complets par Scénario](#16-exemples-complets-par-scénario)

---

## 1. Principe fondamental des échanges

### 1.1 Contrat JSON unique

Tous les modules du système communiquent **EXCLUSIVEMENT via des objets JSON**.

**Interdictions strictes :**
- ❌ Aucun partage de logique interne
- ❌ Aucun partage d'état mémoire
- ❌ Aucun accès direct aux services d'un autre module
- ❌ Aucune modification de JSON par un module intermédiaire

**Obligations strictes :**
- ✅ Format JSON strictement validé
- ✅ Tous les champs typés et documentés
- ✅ Traçabilité complète (timestamps, IDs uniques)
- ✅ Signature pour actions sensibles

### 1.2 Convention de nommage

| Élément | Convention | Exemple |
|---------|------------|---------|
| **Champs** | snake_case | `user_id`, `action_id` |
| **IDs** | Préfixe + underscore + hash | `req_001`, `act_a7b2c`, `conv_1f3e` |
| **Timestamps** | ISO 8601 UTC | `2026-01-20T10:00:00Z` |
| **Énumérations** | UPPER_SNAKE_CASE | `DRAFT`, `CONFIRMED`, `SUCCESS` |

### 1.3 Champs communs (standards)

Champs présents dans **TOUS** les JSON d'échange :

```json
{
  "request_id": "string",           // ID unique de la requête (obligatoire)
  "timestamp": "ISO8601",            // Date/heure UTC (obligatoire)
  "origin": "string",                // Module émetteur (obligatoire)
  "version": "string"                // Version du format (optionnel, défaut: "1.0")
}
```

---

## 2. Flux 0 - Classification Interne Python

### 2.1 Description

**Module émetteur :** Backend Python - STT Engine  
**Module récepteur :** Backend Python - Intent Classifier  
**Objectif :** Classifier une commande utilisateur en `conversation` ou `action`  
**Fréquence :** Après chaque transcription vocale ou réception texte

---

### 2.2 INPUT - Texte transcrit vers Classifier

#### Structure JSON

```json
{
  "request_id": "string",              // ID unique de la requête
  "raw_text": "string",                // Texte brut transcrit ou saisi
  "source": "enum",                    // "voice" | "text" | "keyboard"
  "user_id": "string",                 // ID utilisateur
  "context": {                         // Contexte additionnel
    "language": "string",              // Code ISO 639-1 (ex: "fr", "en")
    "channel": "enum",                 // "voice" | "text" | "mobile" | "web"
    "session_id": "string",            // ID de session utilisateur (optionnel)
    "previous_classification": "enum"  // Classification précédente (optionnel)
  },
  "metadata": {                        // Métadonnées techniques
    "audio_duration_ms": "integer",    // Durée audio si voice (optionnel)
    "confidence_stt": "float"          // Confiance STT si voice (0.0-1.0, optionnel)
  },
  "timestamp": "ISO8601"               // Date/heure de la transcription
}
```

#### Exemple concret

```json
{
  "request_id": "req_20260120_100001",
  "raw_text": "Bonjour, ça va ?",
  "source": "voice",
  "user_id": "user_42",
  "context": {
    "language": "fr",
    "channel": "voice",
    "session_id": "session_abc123",
    "previous_classification": null
  },
  "metadata": {
    "audio_duration_ms": 1850,
    "confidence_stt": 0.94
  },
  "timestamp": "2026-01-20T10:00:01Z"
}
```

#### Contraintes de validation

| Champ | Type | Obligatoire | Contraintes |
|-------|------|-------------|-------------|
| `request_id` | string | ✅ Oui | Pattern: `req_[0-9]{14}_[0-9]{6}` |
| `raw_text` | string | ✅ Oui | Min: 1 char, Max: 1000 chars |
| `source` | enum | ✅ Oui | Valeurs: `voice`, `text`, `keyboard` |
| `user_id` | string | ✅ Oui | Pattern: `user_[0-9]+` |
| `context.language` | string | ✅ Oui | ISO 639-1 (2 lettres) |
| `context.channel` | enum | ✅ Oui | Valeurs: `voice`, `text`, `mobile`, `web` |
| `timestamp` | ISO8601 | ✅ Oui | Format UTC strict |

---

### 2.3 OUTPUT - Résultat Classification

#### Structure JSON

```json
{
  "request_id": "string",              // ID de la requête source (référence)
  "classification": "enum",            // "conversation" | "action"
  "confidence": "float",               // Score de confiance (0.0 - 1.0)
  "method": "enum",                    // "rules" | "ml" | "llm"
  "reasoning": {                       // Justification de la classification
    "matched_keywords": ["string"],    // Mots-clés détectés (optionnel)
    "score_conversation": "float",     // Score brut conversation (0.0-1.0)
    "score_action": "float",           // Score brut action (0.0-1.0)
    "decision_threshold": "float"      // Seuil utilisé pour la décision
  },
  "intent_hint": "string",             // Intention probable si action (optionnel)
  "processing_time_ms": "integer",     // Temps de traitement en ms
  "timestamp": "ISO8601"               // Date/heure de la classification
}
```

#### Exemple concret - Conversation détectée

```json
{
  "request_id": "req_20260120_100001",
  "classification": "conversation",
  "confidence": 0.92,
  "method": "rules",
  "reasoning": {
    "matched_keywords": ["bonjour", "ça va"],
    "score_conversation": 0.92,
    "score_action": 0.08,
    "decision_threshold": 0.75
  },
  "intent_hint": null,
  "processing_time_ms": 15,
  "timestamp": "2026-01-20T10:00:01Z"
}
```

#### Exemple concret - Action détectée

```json
{
  "request_id": "req_20260120_100015",
  "classification": "action",
  "confidence": 0.95,
  "method": "rules",
  "reasoning": {
    "matched_keywords": ["allume", "lampe", "cuisine"],
    "score_conversation": 0.05,
    "score_action": 0.95,
    "decision_threshold": 0.75
  },
  "intent_hint": "control_iot",
  "processing_time_ms": 18,
  "timestamp": "2026-01-20T10:00:15Z"
}
```

#### Contraintes de validation

| Champ | Type | Obligatoire | Contraintes |
|-------|------|-------------|-------------|
| `request_id` | string | ✅ Oui | Référence à l'input |
| `classification` | enum | ✅ Oui | Valeurs: `conversation`, `action` |
| `confidence` | float | ✅ Oui | Range: 0.0 - 1.0 |
| `method` | enum | ✅ Oui | Valeurs: `rules`, `ml`, `llm` |
| `reasoning.score_conversation` | float | ❌ Non | Range: 0.0 - 1.0 |
| `reasoning.score_action` | float | ❌ Non | Range: 0.0 - 1.0 |
| `processing_time_ms` | integer | ✅ Oui | Min: 0 |

---

## 3. Flux Conversation - Backend Uniquement

### 3.1 Description

**Module émetteur :** Backend Python - Agent Core  
**Module récepteur :** Backend Python - LLM Client (puis TTS)  
**Objectif :** Traiter une conversation sociale sans exécution d'action  
**Particularité :** **Ce flux ne quitte JAMAIS le backend Python** (n8n non impliqué)

---

### 3.2 INPUT - Requête Conversation vers LLM

#### Structure JSON

```json
{
  "request_id": "string",              // ID unique de la requête
  "conversation_id": "string",         // ID de la conversation (session)
  "type": "conversation",              // Type fixe
  "input_text": "string",              // Texte de l'utilisateur
  "context": {                         // Contexte conversationnel
    "user_id": "string",               // ID utilisateur
    "language": "string",              // Langue (ISO 639-1)
    "channel": "enum",                 // "voice" | "text" | "mobile" | "web"
    "conversation_history": [          // Historique récent (optionnel)
      {
        "role": "enum",                // "user" | "assistant"
        "content": "string",           // Message
        "timestamp": "ISO8601"         // Date du message
      }
    ],
    "user_preferences": {              // Préférences utilisateur (optionnel)
      "tone": "enum",                  // "formal" | "casual" | "friendly"
      "response_length": "enum"        // "short" | "medium" | "long"
    }
  },
  "llm_config": {                      // Configuration LLM (optionnel)
    "model": "string",                 // Modèle à utiliser (ex: "gpt-3.5-turbo")
    "temperature": "float",            // Créativité (0.0-2.0, défaut: 0.7)
    "max_tokens": "integer"            // Nombre max de tokens (défaut: 150)
  },
  "timestamp": "ISO8601"               // Date/heure de la requête
}
```

#### Exemple concret

```json
{
  "request_id": "req_20260120_100001",
  "conversation_id": "conv_abc123",
  "type": "conversation",
  "input_text": "Bonjour, ça va ?",
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice",
    "conversation_history": [
      {
        "role": "user",
        "content": "Salut",
        "timestamp": "2026-01-20T09:55:00Z"
      },
      {
        "role": "assistant",
        "content": "Bonjour ! Comment puis-je vous aider ?",
        "timestamp": "2026-01-20T09:55:01Z"
      }
    ],
    "user_preferences": {
      "tone": "friendly",
      "response_length": "short"
    }
  },
  "llm_config": {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 100
  },
  "timestamp": "2026-01-20T10:00:01Z"
}
```

#### Contraintes de validation

| Champ | Type | Obligatoire | Contraintes |
|-------|------|-------------|-------------|
| `request_id` | string | ✅ Oui | Unique par requête |
| `conversation_id` | string | ✅ Oui | Pattern: `conv_[a-z0-9]+` |
| `type` | enum | ✅ Oui | Valeur fixe: `conversation` |
| `input_text` | string | ✅ Oui | Min: 1 char, Max: 1000 chars |
| `context.user_id` | string | ✅ Oui | Référence utilisateur valide |
| `context.language` | string | ✅ Oui | ISO 639-1 |
| `llm_config.temperature` | float | ❌ Non | Range: 0.0 - 2.0 |

---

### 3.3 OUTPUT - Réponse Conversationnelle

#### Structure JSON

```json
{
  "request_id": "string",              // ID de la requête source
  "conversation_id": "string",         // ID de la conversation
  "type": "conversation",              // Type fixe
  "response": {                        // Réponse générée
    "text": "string",                  // Texte de la réponse
    "tts_enabled": "boolean",          // Si synthèse vocale activée
    "audio_base64": "string",          // Audio encodé (si tts_enabled=true)
    "audio_format": "enum",            // "mp3" | "wav" | "ogg" (si audio présent)
    "audio_duration_ms": "integer"     // Durée audio en ms (si audio présent)
  },
  "llm_metadata": {                    // Métadonnées LLM
    "model_used": "string",            // Modèle utilisé
    "tokens_used": "integer",          // Nombre de tokens consommés
    "finish_reason": "enum",           // "stop" | "length" | "content_filter"
    "processing_time_ms": "integer"    // Temps de traitement LLM
  },
  "status": "enum",                    // "completed" | "error"
  "error": {                           // Si status="error" (optionnel)
    "code": "string",                  // Code erreur
    "message": "string"                // Message d'erreur
  },
  "timestamp": "ISO8601"               // Date/heure de la réponse
}
```

#### Exemple concret - Succès

```json
{
  "request_id": "req_20260120_100001",
  "conversation_id": "conv_abc123",
  "type": "conversation",
  "response": {
    "text": "Oui, je vais très bien, merci ! Et vous, comment allez-vous ?",
    "tts_enabled": true,
    "audio_base64": "//NExAAAAAANIAAAAASMZI...base64_audio_data...",
    "audio_format": "mp3",
    "audio_duration_ms": 2340
  },
  "llm_metadata": {
    "model_used": "gpt-3.5-turbo",
    "tokens_used": 42,
    "finish_reason": "stop",
    "processing_time_ms": 850
  },
  "status": "completed",
  "timestamp": "2026-01-20T10:00:02Z"
}
```

#### Exemple concret - Erreur

```json
{
  "request_id": "req_20260120_100001",
  "conversation_id": "conv_abc123",
  "type": "conversation",
  "response": {
    "text": "",
    "tts_enabled": false
  },
  "llm_metadata": {
    "model_used": "gpt-3.5-turbo",
    "tokens_used": 0,
    "finish_reason": "error",
    "processing_time_ms": 120
  },
  "status": "error",
  "error": {
    "code": "LLM_TIMEOUT",
    "message": "Le service LLM n'a pas répondu dans le délai imparti"
  },
  "timestamp": "2026-01-20T10:00:02Z"
}
```

#### Contraintes de validation

| Champ | Type | Obligatoire | Contraintes |
|-------|------|-------------|-------------|
| `request_id` | string | ✅ Oui | Référence à l'input |
| `response.text` | string | ✅ Oui | Min: 0 chars (vide si erreur) |
| `response.tts_enabled` | boolean | ✅ Oui | - |
| `response.audio_base64` | string | ❌ Non | Requis si tts_enabled=true |
| `llm_metadata.tokens_used` | integer | ✅ Oui | Min: 0 |
| `status` | enum | ✅ Oui | Valeurs: `completed`, `error` |
| `error` | object | ❌ Non | Obligatoire si status="error" |

---

## 4. Flux 1 - Python → LLM (Analyse Linguistique)

### 4.1 Description

**Module émetteur :** Backend Python - Agent Core  
**Module récepteur :** Module LLM - LLM Server  
**Objectif :** Analyser une commande utilisateur pour extraire intention et entités  
**Condition :** Classification = `action`

---

### 4.2 INPUT - Requête Analyse vers LLM

#### Structure JSON

```json
{
  "request_id": "string",              // ID unique de la requête
  "type": "intent_analysis",           // Type de requête LLM
  "input_text": "string",              // Texte à analyser
  "language": "string",                // Langue ISO 639-1
  "context": {                         // Contexte utilisateur
    "user_id": "string",               // ID utilisateur
    "channel": "enum",                 // "voice" | "text" | "mobile" | "web"
    "session_id": "string",            // ID de session (optionnel)
    "location": "string",              // Localisation utilisateur (optionnel)
    "time_of_day": "enum",             // "morning" | "afternoon" | "evening" | "night"
    "previous_intent": "string"        // Intention précédente (optionnel)
  },
  "analysis_mode": {                   // Configuration de l'analyse
    "extract_intent": "boolean",       // Extraire l'intention (défaut: true)
    "extract_entities": "boolean",     // Extraire les entités (défaut: true)
    "extract_sentiment": "boolean",    // Analyser le sentiment (défaut: false)
    "allowed_intents": ["string"]      // Liste d'intentions possibles (optionnel)
  },
  "llm_config": {                      // Configuration LLM
    "model": "string",                 // Modèle à utiliser
    "temperature": "float",            // Créativité (0.0-2.0, défaut: 0.3)
    "max_tokens": "integer"            // Max tokens (défaut: 300)
  },
  "timestamp": "ISO8601"               // Date/heure de la requête
}
```

#### Exemple concret - Contrôle IoT

```json
{
  "request_id": "req_20260120_100015",
  "type": "intent_analysis",
  "input_text": "Allume la lampe de la cuisine s'il te plaît",
  "language": "fr",
  "context": {
    "user_id": "user_42",
    "channel": "voice",
    "session_id": "session_abc123",
    "location": "home",
    "time_of_day": "evening",
    "previous_intent": null
  },
  "analysis_mode": {
    "extract_intent": true,
    "extract_entities": true,
    "extract_sentiment": false,
    "allowed_intents": [
      "control_iot",
      "send_email",
      "set_reminder",
      "web_search"
    ]
  },
  "llm_config": {
    "model": "gpt-3.5-turbo",
    "temperature": 0.3,
    "max_tokens": 200
  },
  "timestamp": "2026-01-20T10:00:15Z"
}
```

#### Exemple concret - Envoi Email

```json
{
  "request_id": "req_20260120_100030",
  "type": "intent_analysis",
  "input_text": "Envoie un email à Jean pour lui dire que la réunion est reportée à demain 14h",
  "language": "fr",
  "context": {
    "user_id": "user_42",
    "channel": "voice",
    "session_id": "session_abc123",
    "location": "office",
    "time_of_day": "morning",
    "previous_intent": null
  },
  "analysis_mode": {
    "extract_intent": true,
    "extract_entities": true,
    "extract_sentiment": false
  },
  "llm_config": {
    "model": "gpt-4",
    "temperature": 0.2,
    "max_tokens": 300
  },
  "timestamp": "2026-01-20T10:00:30Z"
}
```

#### Contraintes de validation

| Champ | Type | Obligatoire | Contraintes |
|-------|------|-------------|-------------|
| `request_id` | string | ✅ Oui | Unique |
| `type` | enum | ✅ Oui | Valeur: `intent_analysis` |
| `input_text` | string | ✅ Oui | Min: 1 char, Max: 1000 chars |
| `language` | string | ✅ Oui | ISO 639-1 |
| `context.user_id` | string | ✅ Oui | Valide |
| `llm_config.temperature` | float | ❌ Non | Range: 0.0 - 2.0 |

---

### 4.3 OUTPUT - Résultat Analyse Intention

#### Structure JSON

```json
{
  "request_id": "string",              // ID de la requête source
  "type": "intent_analysis",           // Type de réponse
  "analysis_result": {                 // Résultat de l'analyse
    "intent": "string",                // Intention principale détectée
    "intent_confidence": "float",      // Confiance sur l'intention (0.0-1.0)
    "entities": {                      // Entités extraites (clés variables)
      "key1": "value1",
      "key2": "value2"
    },
    "entities_details": [              // Détails des entités (optionnel)
      {
        "entity_type": "string",       // Type d'entité (ex: "device", "person")
        "entity_value": "string",      // Valeur extraite
        "confidence": "float",         // Confiance (0.0-1.0)
        "position": {                  // Position dans le texte (optionnel)
          "start": "integer",
          "end": "integer"
        }
      }
    ],
    "sentiment": {                     // Sentiment (si extract_sentiment=true)
      "polarity": "enum",              // "positive" | "neutral" | "negative"
      "score": "float"                 // Score (-1.0 à 1.0)
    },
    "alternative_intents": [           // Intentions alternatives (optionnel)
      {
        "intent": "string",
        "confidence": "float"
      }
    ]
  },
  "llm_metadata": {                    // Métadonnées LLM
    "model_used": "string",            // Modèle utilisé
    "tokens_used": "integer",          // Tokens consommés
    "processing_time_ms": "integer",   // Temps de traitement
    "finish_reason": "enum"            // "stop" | "length" | "error"
  },
  "status": "enum",                    // "success" | "error"
  "error": {                           // Si status="error" (optionnel)
    "code": "string",
    "message": "string"
  },
  "timestamp": "ISO8601"               // Date/heure de la réponse
}
```

#### Exemple concret - Contrôle IoT (Succès)

```json
{
  "request_id": "req_20260120_100015",
  "type": "intent_analysis",
  "analysis_result": {
    "intent": "control_iot",
    "intent_confidence": 0.96,
    "entities": {
      "device": "lamp",
      "location": "kitchen",
      "action": "on",
      "device_type": "light"
    },
    "entities_details": [
      {
        "entity_type": "device",
        "entity_value": "lamp",
        "confidence": 0.98,
        "position": {
          "start": 11,
          "end": 16
        }
      },
      {
        "entity_type": "location",
        "entity_value": "kitchen",
        "confidence": 0.94,
        "position": {
          "start": 23,
          "end": 30
        }
      },
      {
        "entity_type": "action",
        "entity_value": "on",
        "confidence": 0.99,
        "position": {
          "start": 0,
          "end": 6
        }
      }
    ],
    "alternative_intents": [
      {
        "intent": "set_scene",
        "confidence": 0.12
      }
    ]
  },
  "llm_metadata": {
    "model_used": "gpt-3.5-turbo",
    "tokens_used": 85,
    "processing_time_ms": 420,
    "finish_reason": "stop"
  },
  "status": "success",
  "timestamp": "2026-01-20T10:00:16Z"
}
```

#### Exemple concret - Envoi Email (Succès)

```json
{
  "request_id": "req_20260120_100030",
  "type": "intent_analysis",
  "analysis_result": {
    "intent": "send_email",
    "intent_confidence": 0.98,
    "entities": {
      "recipient": "Jean",
      "recipient_type": "person",
      "subject": "Report de réunion",
      "body": "La réunion est reportée à demain 14h",
      "action_date": "tomorrow",
      "action_time": "14:00"
    },
    "entities_details": [
      {
        "entity_type": "recipient",
        "entity_value": "Jean",
        "confidence": 0.99,
        "position": {
          "start": 17,
          "end": 21
        }
      },
      {
        "entity_type": "body",
        "entity_value": "la réunion est reportée à demain 14h",
        "confidence": 0.97,
        "position": {
          "start": 36,
          "end": 73
        }
      }
    ],
    "alternative_intents": [
      {
        "intent": "send_message",
        "confidence": 0.15
      }
    ]
  },
  "llm_metadata": {
    "model_used": "gpt-4",
    "tokens_used": 128,
    "processing_time_ms": 680,
    "finish_reason": "stop"
  },
  "status": "success",
  "timestamp": "2026-01-20T10:00:31Z"
}
```

#### Exemple concret - Erreur (Confiance faible)

```json
{
  "request_id": "req_20260120_100045",
  "type": "intent_analysis",
  "analysis_result": {
    "intent": "unknown",
    "intent_confidence": 0.42,
    "entities": {},
    "entities_details": []
  },
  "llm_metadata": {
    "model_used": "gpt-3.5-turbo",
    "tokens_used": 65,
    "processing_time_ms": 380,
    "finish_reason": "stop"
  },
  "status": "error",
  "error": {
    "code": "LOW_CONFIDENCE",
    "message": "Confiance insuffisante pour déterminer l'intention (0.42 < 0.70)"
  },
  "timestamp": "2026-01-20T10:00:46Z"
}
```

#### Contraintes de validation

| Champ | Type | Obligatoire | Contraintes |
|-------|------|-------------|-------------|
| `request_id` | string | ✅ Oui | Référence à l'input |
| `analysis_result.intent` | string | ✅ Oui | Non vide |
| `analysis_result.intent_confidence` | float | ✅ Oui | Range: 0.0 - 1.0 |
| `analysis_result.entities` | object | ✅ Oui | Peut être vide {} |
| `llm_metadata.tokens_used` | integer | ✅ Oui | Min: 0 |
| `status` | enum | ✅ Oui | Valeurs: `success`, `error` |

---

## 5. Flux 2 - LLM → Python (Résultat Analyse)

**Note :** Ce flux est identique au OUTPUT du Flux 1. Voir section 4.3 ci-dessus.

Le Backend Python reçoit le JSON de résultat d'analyse et le traite pour construire l'ActionJSON.

---

## 6. Flux 3 - Python Interne (Construction ActionJSON)

### 6.1 Description

**Module émetteur :** Backend Python - Action Builder  
**Module récepteur :** Backend Python - State Manager  
**Objectif :** Créer une ActionJSON officielle à partir de l'analyse LLM  
**État initial :** `DRAFT` (brouillon, non confirmé)

---

### 6.2 OUTPUT - ActionJSON Construite (État DRAFT)

#### Structure JSON Complète

```json
{
  "action_id": "string",               // ID unique de l'action
  "type": "action",                    // Type fixe
  "origin": "python_agent",            // Module émetteur (fixe)
  "intent": "string",                  // Intention extraite par LLM
  "state": "DRAFT",                    // État initial (fixe)
  "confirmed": false,                  // Non confirmé (fixe)
  "priority": "enum",                  // "low" | "normal" | "high" | "urgent"
  "payload": {                         // Données spécifiques à l'intention
    // Structure variable selon intent
    // Voir section 6.3 pour détails par intent
  },
  "context": {                         // Contexte d'exécution
    "user_id": "string",               // ID utilisateur
    "language": "string",              // Langue ISO 639-1
    "channel": "enum",                 // "voice" | "text" | "mobile" | "web"
    "session_id": "string",            // ID de session
    "location": "string",              // Localisation (optionnel)
    "time_of_day": "enum",             // "morning" | "afternoon" | "evening" | "night"
    "device_info": {                   // Info appareil (optionnel)
      "device_id": "string",
      "device_type": "string",
      "os": "string"
    }
  },
  "security": {                        // Informations de sécurité
    "auth_level": "integer",           // Niveau autorisation (1=user, 2=admin)
    "signature": "pending",            // Signature HMAC (pending avant confirmation)
    "signed_at": null,                 // Date signature (null avant confirmation)
    "requires_confirmation": "boolean",// Si confirmation explicite requise
    "permissions_required": ["string"] // Permissions nécessaires (optionnel)
  },
  "metadata": {                        // Métadonnées techniques
    "request_id": "string",            // ID de la requête source
    "llm_confidence": "float",         // Confiance LLM (0.0-1.0)
    "classification_confidence": "float", // Confiance classification
    "retry_count": "integer",          // Nombre de tentatives (défaut: 0)
    "parent_action_id": "string"       // ID action parente (si correction, optionnel)
  },
  "timestamps": {                      // Horodatages
    "created_at": "ISO8601",           // Date création
    "updated_at": "ISO8601",           // Date dernière mise à jour
    "expires_at": "ISO8601"            // Date expiration (optionnel)
  },
  "version": "string"                  // Version du format ActionJSON (ex: "2.0")
}
```

---

### 6.3 Structures Payload par Intent

#### Intent: `control_iot` - Contrôle IoT

```json
{
  "intent": "control_iot",
  "payload": {
    "device_id": "string",             // ID du dispositif (ex: "esp32_kitchen")
    "device_type": "enum",             // "light" | "switch" | "thermostat" | "door" | "sensor"
    "command": "enum",                 // "ON" | "OFF" | "TOGGLE" | "SET_VALUE"
    "target": "string",                // Cible spécifique (ex: "LAMP_1", "RELAY_2")
    "value": "integer|float|string",   // Valeur à appliquer (optionnel)
    "unit": "string",                  // Unité de la valeur (ex: "celsius", "percent")
    "location": "string",              // Localisation (ex: "kitchen", "bedroom")
    "duration_seconds": "integer",     // Durée (si commande temporaire, optionnel)
    "condition": {                     // Condition d'exécution (optionnel)
      "type": "enum",                  // "time" | "sensor" | "state"
      "value": "string"
    }
  }
}
```

**Exemple concret :**

```json
{
  "action_id": "act_1001a7b2",
  "type": "action",
  "origin": "python_agent",
  "intent": "control_iot",
  "state": "DRAFT",
  "confirmed": false,
  "priority": "high",
  "payload": {
    "device_id": "esp32_kitchen",
    "device_type": "light",
    "command": "ON",
    "target": "LAMP_1",
    "value": 1,
    "unit": null,
    "location": "kitchen",
    "duration_seconds": null,
    "condition": null
  },
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice",
    "session_id": "session_abc123",
    "location": "home",
    "time_of_day": "evening"
  },
  "security": {
    "auth_level": 1,
    "signature": "pending",
    "signed_at": null,
    "requires_confirmation": true,
    "permissions_required": ["iot.control"]
  },
  "metadata": {
    "request_id": "req_20260120_100015",
    "llm_confidence": 0.96,
    "classification_confidence": 0.95,
    "retry_count": 0,
    "parent_action_id": null
  },
  "timestamps": {
    "created_at": "2026-01-20T10:00:16Z",
    "updated_at": "2026-01-20T10:00:16Z",
    "expires_at": "2026-01-20T10:05:16Z"
  },
  "version": "2.0"
}
```

---

#### Intent: `send_email` - Envoi Email

```json
{
  "intent": "send_email",
  "payload": {
    "recipient": "string",             // Destinataire principal
    "recipient_email": "string",       // Email si connu (optionnel)
    "cc": ["string"],                  // Destinataires en copie (optionnel)
    "bcc": ["string"],                 // Destinataires en copie cachée (optionnel)
    "subject": "string",               // Sujet de l'email
    "body": "string",                  // Corps du message
    "body_format": "enum",             // "plain" | "html" (défaut: "plain")
    "attachments": [                   // Pièces jointes (optionnel)
      {
        "filename": "string",
        "content_type": "string",
        "content_base64": "string"
      }
    ],
    "priority": "enum",                // "low" | "normal" | "high"
    "reply_to": "string",              // Email de réponse (optionnel)
    "send_at": "ISO8601"               // Envoi différé (optionnel)
  }
}
```

**Exemple concret :**

```json
{
  "action_id": "act_2002b8c3",
  "type": "action",
  "origin": "python_agent",
  "intent": "send_email",
  "state": "DRAFT",
  "confirmed": false,
  "priority": "normal",
  "payload": {
    "recipient": "Jean",
    "recipient_email": "jean@example.com",
    "cc": [],
    "bcc": [],
    "subject": "Report de réunion",
    "body": "Bonjour Jean,\n\nLa réunion prévue aujourd'hui est reportée à demain 14h.\n\nCordialement",
    "body_format": "plain",
    "attachments": [],
    "priority": "normal",
    "reply_to": null,
    "send_at": null
  },
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice",
    "session_id": "session_abc123",
    "location": "office",
    "time_of_day": "morning"
  },
  "security": {
    "auth_level": 1,
    "signature": "pending",
    "signed_at": null,
    "requires_confirmation": true,
    "permissions_required": ["email.send"]
  },
  "metadata": {
    "request_id": "req_20260120_100030",
    "llm_confidence": 0.98,
    "classification_confidence": 0.95,
    "retry_count": 0,
    "parent_action_id": null
  },
  "timestamps": {
    "created_at": "2026-01-20T10:00:31Z",
    "updated_at": "2026-01-20T10:00:31Z",
    "expires_at": "2026-01-20T10:10:31Z"
  },
  "version": "2.0"
}
```

---

#### Intent: `set_reminder` - Définir Rappel

```json
{
  "intent": "set_reminder",
  "payload": {
    "title": "string",                 // Titre du rappel
    "description": "string",           // Description (optionnel)
    "reminder_time": "ISO8601",        // Date/heure du rappel
    "reminder_type": "enum",           // "once" | "daily" | "weekly" | "monthly"
    "recurrence": {                    // Récurrence (si type != "once")
      "frequency": "enum",             // "daily" | "weekly" | "monthly"
      "interval": "integer",           // Intervalle (ex: tous les 2 jours)
      "days_of_week": ["integer"],     // Jours semaine (1=Lundi, 7=Dimanche)
      "end_date": "ISO8601"            // Date fin récurrence (optionnel)
    },
    "notification_channels": ["enum"], // "push" | "email" | "sms" | "voice"
    "priority": "enum",                // "low" | "normal" | "high"
    "location_based": {                // Rappel basé localisation (optionnel)
      "enabled": "boolean",
      "location": "string",
      "radius_meters": "integer"
    }
  }
}
```

**Exemple concret :**

```json
{
  "action_id": "act_3003c9d4",
  "type": "action",
  "origin": "python_agent",
  "intent": "set_reminder",
  "state": "DRAFT",
  "confirmed": false,
  "priority": "normal",
  "payload": {
    "title": "Rendez-vous dentiste",
    "description": "N'oublie pas le rendez-vous chez le dentiste demain à 14h",
    "reminder_time": "2026-01-21T13:45:00Z",
    "reminder_type": "once",
    "recurrence": null,
    "notification_channels": ["push", "voice"],
    "priority": "high",
    "location_based": null
  },
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice",
    "session_id": "session_abc123",
    "location": "home",
    "time_of_day": "evening"
  },
  "security": {
    "auth_level": 1,
    "signature": "pending",
    "signed_at": null,
    "requires_confirmation": true,
    "permissions_required": ["reminder.create"]
  },
  "metadata": {
    "request_id": "req_20260120_100045",
    "llm_confidence": 0.94,
    "classification_confidence": 0.92,
    "retry_count": 0,
    "parent_action_id": null
  },
  "timestamps": {
    "created_at": "2026-01-20T10:00:46Z",
    "updated_at": "2026-01-20T10:00:46Z",
    "expires_at": "2026-01-20T10:10:46Z"
  },
  "version": "2.0"
}
```

---

#### Intent: `web_search` - Recherche Web

```json
{
  "intent": "web_search",
  "payload": {
    "query": "string",                 // Requête de recherche
    "search_type": "enum",             // "web" | "images" | "news" | "videos"
    "language": "string",              // Langue résultats (ISO 639-1)
    "region": "string",                // Région géographique (ISO 3166-1)
    "max_results": "integer",          // Nombre max de résultats (défaut: 5)
    "safe_search": "boolean",          // Filtrage contenu adulte
    "time_range": "enum",              // "any" | "day" | "week" | "month" | "year"
    "result_format": "enum"            // "summary" | "full" | "links_only"
  }
}
```

**Exemple concret :**

```json
{
  "action_id": "act_4004d0e5",
  "type": "action",
  "origin": "python_agent",
  "intent": "web_search",
  "state": "DRAFT",
  "confirmed": false,
  "priority": "normal",
  "payload": {
    "query": "météo Paris demain",
    "search_type": "web",
    "language": "fr",
    "region": "FR",
    "max_results": 3,
    "safe_search": true,
    "time_range": "day",
    "result_format": "summary"
  },
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice",
    "session_id": "session_abc123",
    "location": "home",
    "time_of_day": "morning"
  },
  "security": {
    "auth_level": 1,
    "signature": "pending",
    "signed_at": null,
    "requires_confirmation": false,
    "permissions_required": ["web.search"]
  },
  "metadata": {
    "request_id": "req_20260120_100060",
    "llm_confidence": 0.97,
    "classification_confidence": 0.94,
    "retry_count": 0,
    "parent_action_id": null
  },
  "timestamps": {
    "created_at": "2026-01-20T10:01:00Z",
    "updated_at": "2026-01-20T10:01:00Z",
    "expires_at": "2026-01-20T10:06:00Z"
  },
  "version": "2.0"
}
```

---

## 7. Flux 4 - Confirmation Utilisateur

### 7.1 Description

**Module émetteur :** Backend Python - Confirmation Handler  
**Module récepteur :** Utilisateur (via ESP32)  
**Objectif :** Demander validation explicite avant exécution  
**Condition :** `security.requires_confirmation = true`

---

### 7.2 OUTPUT - Demande de Confirmation

#### Structure JSON

```json
{
  "action_id": "string",               // ID de l'action à confirmer
  "confirmation_request": {            // Demande de confirmation
    "text": "string",                  // Texte de confirmation (français naturel)
    "tts_enabled": "boolean",          // Si synthèse vocale activée
    "audio_base64": "string",          // Audio encodé (si tts=true)
    "audio_format": "enum",            // "mp3" | "wav" | "ogg"
    "audio_duration_ms": "integer"     // Durée audio
  },
  "action_summary": {                  // Résumé de l'action
    "intent": "string",                // Intention
    "description": "string",           // Description courte
    "key_parameters": {                // Paramètres clés à confirmer
      "key1": "value1",
      "key2": "value2"
    }
  },
  "response_options": [                // Options de réponse
    {
      "value": "enum",                 // "confirm" | "cancel" | "modify"
      "label_fr": "string",            // Label français
      "keywords": ["string"]           // Mots-clés détection vocale
    }
  ],
  "timeout_seconds": "integer",        // Temps avant annulation auto (défaut: 60)
  "timestamp": "ISO8601"               // Date/heure demande
}
```

#### Exemple concret - Contrôle IoT

```json
{
  "action_id": "act_1001a7b2",
  "confirmation_request": {
    "text": "Je vais allumer la lampe de la cuisine. Voulez-vous confirmer ?",
    "tts_enabled": true,
    "audio_base64": "//NExAAAAAANIAAAAASMZI...base64...",
    "audio_format": "mp3",
    "audio_duration_ms": 3120
  },
  "action_summary": {
    "intent": "control_iot",
    "description": "Allumer lampe cuisine",
    "key_parameters": {
      "device": "LAMP_1",
      "location": "cuisine",
      "action": "allumer"
    }
  },
  "response_options": [
    {
      "value": "confirm",
      "label_fr": "Oui, confirme",
      "keywords": ["oui", "confirme", "ok", "valide", "d'accord", "vas-y"]
    },
    {
      "value": "cancel",
      "label_fr": "Non, annule",
      "keywords": ["non", "annule", "stop", "pas maintenant", "laisse tomber"]
    },
    {
      "value": "modify",
      "label_fr": "Modifier",
      "keywords": ["modifie", "change", "corrige", "plutôt"]
    }
  ],
  "timeout_seconds": 60,
  "timestamp": "2026-01-20T10:00:17Z"
}
```

#### Exemple concret - Envoi Email

```json
{
  "action_id": "act_2002b8c3",
  "confirmation_request": {
    "text": "Je vais envoyer un email à Jean avec le sujet 'Report de réunion'. Le message dit : 'La réunion est reportée à demain 14h'. Voulez-vous confirmer l'envoi ?",
    "tts_enabled": true,
    "audio_base64": "//NExAAAAAANIAAAAASMZI...base64...",
    "audio_format": "mp3",
    "audio_duration_ms": 5800
  },
  "action_summary": {
    "intent": "send_email",
    "description": "Envoi email à Jean",
    "key_parameters": {
      "destinataire": "Jean",
      "sujet": "Report de réunion",
      "message_preview": "La réunion est reportée à demain 14h"
    }
  },
  "response_options": [
    {
      "value": "confirm",
      "label_fr": "Oui, envoie",
      "keywords": ["oui", "envoie", "confirme", "ok", "vas-y"]
    },
    {
      "value": "cancel",
      "label_fr": "Non, annule",
      "keywords": ["non", "annule", "stop", "pas maintenant"]
    },
    {
      "value": "modify",
      "label_fr": "Modifier",
      "keywords": ["modifie", "change", "corrige", "reformule"]
    }
  ],
  "timeout_seconds": 90,
  "timestamp": "2026-01-20T10:00:32Z"
}
```

---

### 7.3 INPUT - Réponse Utilisateur

#### Structure JSON

```json
{
  "action_id": "string",               // ID de l'action concernée
  "user_response": {                   // Réponse utilisateur
    "type": "enum",                    // "voice" | "text" | "button"
    "raw_input": "string",             // Input brut (transcription si voice)
    "parsed_value": "enum",            // "confirm" | "cancel" | "modify" | "unknown"
    "confidence": "float",             // Confiance parsing (0.0-1.0)
    "audio_input": "string"            // Audio encodé (si type=voice, optionnel)
  },
  "modification_request": {            // Si parsed_value="modify" (optionnel)
    "field_to_modify": "string",       // Champ à modifier
    "new_value": "string"              // Nouvelle valeur
  },
  "user_id": "string",                 // ID utilisateur
  "response_time_seconds": "integer",  // Temps de réponse
  "timestamp": "ISO8601"               // Date/heure réponse
}
```

#### Exemple concret - Confirmation

```json
{
  "action_id": "act_1001a7b2",
  "user_response": {
    "type": "voice",
    "raw_input": "Oui, vas-y allume la lampe",
    "parsed_value": "confirm",
    "confidence": 0.96,
    "audio_input": "//NExAAAAAANIAAAAASMZI...base64..."
  },
  "modification_request": null,
  "user_id": "user_42",
  "response_time_seconds": 3,
  "timestamp": "2026-01-20T10:00:20Z"
}
```

#### Exemple concret - Annulation

```json
{
  "action_id": "act_2002b8c3",
  "user_response": {
    "type": "voice",
    "raw_input": "Non finalement, annule l'email",
    "parsed_value": "cancel",
    "confidence": 0.98,
    "audio_input": "//NExAAAAAANIAAAAASMZI...base64..."
  },
  "modification_request": null,
  "user_id": "user_42",
  "response_time_seconds": 5,
  "timestamp": "2026-01-20T10:00:37Z"
}
```

#### Exemple concret - Modification

```json
{
  "action_id": "act_2002b8c3",
  "user_response": {
    "type": "voice",
    "raw_input": "Non, change le destinataire, envoie plutôt à Marie",
    "parsed_value": "modify",
    "confidence": 0.89,
    "audio_input": "//NExAAAAAANIAAAAASMZI...base64..."
  },
  "modification_request": {
    "field_to_modify": "recipient",
    "new_value": "Marie"
  },
  "user_id": "user_42",
  "response_time_seconds": 7,
  "timestamp": "2026-01-20T10:00:39Z"
}
```

---

### 7.4 OUTPUT - ActionJSON Mise à Jour (État CONFIRMED)

#### Structure JSON (après confirmation)

```json
{
  "action_id": "string",               // ID de l'action (inchangé)
  "state": "CONFIRMED",                // État mis à jour
  "confirmed": true,                   // Confirmé (mis à jour)
  "confirmation_details": {            // Détails de la confirmation (NOUVEAU)
    "confirmed_at": "ISO8601",         // Date/heure confirmation
    "confirmed_by": "string",          // ID utilisateur
    "confirmation_method": "enum",     // "voice" | "text" | "button"
    "response_time_seconds": "integer" // Temps de réponse
  },
  "security": {                        // Sécurité mise à jour
    "auth_level": "integer",
    "signature": "string",             // Signature HMAC générée
    "signed_at": "ISO8601",            // Date signature
    "requires_confirmation": "boolean",
    "permissions_required": ["string"]
  },
  "timestamps": {
    "created_at": "ISO8601",
    "updated_at": "ISO8601",           // Mise à jour
    "confirmed_at": "ISO8601",         // NOUVEAU
    "expires_at": "ISO8601"
  }
  // ... autres champs inchangés ...
}
```

#### Exemple concret complet

```json
{
  "action_id": "act_1001a7b2",
  "type": "action",
  "origin": "python_agent",
  "intent": "control_iot",
  "state": "CONFIRMED",
  "confirmed": true,
  "priority": "high",
  "payload": {
    "device_id": "esp32_kitchen",
    "device_type": "light",
    "command": "ON",
    "target": "LAMP_1",
    "value": 1,
    "location": "kitchen"
  },
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice",
    "session_id": "session_abc123",
    "location": "home",
    "time_of_day": "evening"
  },
  "confirmation_details": {
    "confirmed_at": "2026-01-20T10:00:20Z",
    "confirmed_by": "user_42",
    "confirmation_method": "voice",
    "response_time_seconds": 3
  },
  "security": {
    "auth_level": 1,
    "signature": "HMAC_8f92aa3b7e5c1d4f9a2b6c8e0d3f5a7b",
    "signed_at": "2026-01-20T10:00:20Z",
    "requires_confirmation": true,
    "permissions_required": ["iot.control"]
  },
  "metadata": {
    "request_id": "req_20260120_100015",
    "llm_confidence": 0.96,
    "classification_confidence": 0.95,
    "retry_count": 0,
    "parent_action_id": null
  },
  "timestamps": {
    "created_at": "2026-01-20T10:00:16Z",
    "updated_at": "2026-01-20T10:00:20Z",
    "confirmed_at": "2026-01-20T10:00:20Z",
    "expires_at": "2026-01-20T10:05:16Z"
  },
  "version": "2.0"
}
```

---

## 8. Flux 5 - Python → n8n (Exécution Contrôlée)

### 8.1 Description

**Module émetteur :** Backend Python - n8n Client  
**Module récepteur :** Orchestrateur n8n - Webhook Action Router  
**Objectif :** Envoyer une action **CONFIRMÉE uniquement** pour exécution  
**Condition :** `state = "CONFIRMED"` ET `confirmed = true` ET `signature != "pending"`

---

### 8.2 INPUT - ActionJSON vers n8n

#### Structure JSON Envoyée

C'est l'ActionJSON complète à l'état CONFIRMED (voir section 7.4).

**Champs critiques pour n8n :**

```json
{
  "action_id": "string",               // ID unique (OBLIGATOIRE)
  "type": "action",                    // Type fixe (OBLIGATOIRE)
  "origin": "python_agent",            // Origine (OBLIGATOIRE)
  "intent": "string",                  // Intention (OBLIGATOIRE pour routage)
  "confirmed": true,                   // DOIT être true (VALIDATION)
  "state": "CONFIRMED",                // DOIT être CONFIRMED (VALIDATION)
  "priority": "enum",                  // Priorité (pour file d'attente)
  "payload": { ... },                  // Données action (OBLIGATOIRE)
  "security": {
    "signature": "string"              // Signature HMAC (OBLIGATOIRE pour validation)
  },
  "timestamps": {
    "confirmed_at": "ISO8601"          // Date confirmation (OBLIGATOIRE)
  }
  // ... autres champs transmis mais non utilisés par n8n ...
}
```

#### Exemple concret complet

```json
{
  "action_id": "act_1001a7b2",
  "type": "action",
  "origin": "python_agent",
  "intent": "control_iot",
  "state": "CONFIRMED",
  "confirmed": true,
  "priority": "high",
  "payload": {
    "device_id": "esp32_kitchen",
    "device_type": "light",
    "command": "ON",
    "target": "LAMP_1",
    "value": 1,
    "location": "kitchen"
  },
  "context": {
    "user_id": "user_42",
    "language": "fr",
    "channel": "voice",
    "session_id": "session_abc123"
  },
  "confirmation_details": {
    "confirmed_at": "2026-01-20T10:00:20Z",
    "confirmed_by": "user_42",
    "confirmation_method": "voice"
  },
  "security": {
    "auth_level": 1,
    "signature": "HMAC_8f92aa3b7e5c1d4f9a2b6c8e0d3f5a7b",
    "signed_at": "2026-01-20T10:00:20Z",
    "requires_confirmation": true,
    "permissions_required": ["iot.control"]
  },
  "metadata": {
    "request_id": "req_20260120_100015",
    "llm_confidence": 0.96
  },
  "timestamps": {
    "created_at": "2026-01-20T10:00:16Z",
    "updated_at": "2026-01-20T10:00:20Z",
    "confirmed_at": "2026-01-20T10:00:20Z",
    "expires_at": "2026-01-20T10:05:16Z"
  },
  "version": "2.0"
}
```

---

### 8.3 Validation par n8n

n8n effectue les validations suivantes **AVANT** routage :

```json
{
  "validation_checks": [
    {
      "check": "action_id_present",
      "required": true,
      "description": "action_id doit être présent et non vide"
    },
    {
      "check": "type_equals_action",
      "required": true,
      "description": "type doit être exactement 'action'"
    },
    {
      "check": "confirmed_is_true",
      "required": true,
      "description": "confirmed doit être true"
    },
    {
      "check": "state_is_confirmed",
      "required": true,
      "description": "state doit être 'CONFIRMED'"
    },
    {
      "check": "signature_valid",
      "required": true,
      "description": "signature HMAC doit être valide"
    },
    {
      "check": "intent_recognized",
      "required": true,
      "description": "intent doit correspondre à un workflow existant"
    },
    {
      "check": "payload_structure_valid",
      "required": true,
      "description": "payload doit correspondre au schéma de l'intent"
    },
    {
      "check": "not_expired",
      "required": true,
      "description": "expires_at doit être dans le futur"
    }
  ]
}
```

---

### 8.4 OUTPUT - Réponse Immédiate n8n (Acknowledgment)

#### Structure JSON

```json
{
  "action_id": "string",               // ID de l'action reçue
  "status": "enum",                    // "accepted" | "rejected"
  "message": "string",                 // Message descriptif
  "validation_results": [              // Résultats validations
    {
      "check": "string",
      "passed": "boolean",
      "message": "string"
    }
  ],
  "workflow_assigned": "string",       // Nom du workflow routé (si accepted)
  "execution_id": "string",            // ID d'exécution n8n (si accepted)
  "estimated_duration_seconds": "integer", // Durée estimée
  "timestamp": "ISO8601"               // Date/heure réponse
}
```

#### Exemple concret - Accepté

```json
{
  "action_id": "act_1001a7b2",
  "status": "accepted",
  "message": "Action acceptée et routée vers workflow control_iot",
  "validation_results": [
    {
      "check": "action_id_present",
      "passed": true,
      "message": "OK"
    },
    {
      "check": "confirmed_is_true",
      "passed": true,
      "message": "OK"
    },
    {
      "check": "signature_valid",
      "passed": true,
      "message": "OK"
    }
  ],
  "workflow_assigned": "wf_control_iot",
  "execution_id": "exec_n8n_9a7b2c5d",
  "estimated_duration_seconds": 5,
  "timestamp": "2026-01-20T10:00:21Z"
}
```

#### Exemple concret - Rejeté

```json
{
  "action_id": "act_9999error",
  "status": "rejected",
  "message": "Action rejetée : signature invalide",
  "validation_results": [
    {
      "check": "action_id_present",
      "passed": true,
      "message": "OK"
    },
    {
      "check": "signature_valid",
      "passed": false,
      "message": "Signature HMAC invalide ou expirée"
    }
  ],
  "workflow_assigned": null,
  "execution_id": null,
  "estimated_duration_seconds": 0,
  "timestamp": "2026-01-20T10:00:21Z"
}
```

---

## 9. Flux 6 - n8n → ESP32 (Commande Physique)

### 9.1 Description

**Module émetteur :** Orchestrateur n8n - Workflow spécialisé  
**Module récepteur :** ESP32 - MQTT Client  
**Protocole :** MQTT (publish/subscribe)  
**Topic MQTT :** `esp32/command/{device_id}`  
**Objectif :** Transmettre une commande simple et légère à l'ESP32

---

### 9.2 OUTPUT - Commande vers ESP32

#### Structure JSON (Simplifiée pour ESP32)

```json
{
  "command_id": "string",              // ID unique de la commande
  "device_id": "string",               // ID du dispositif ESP32
  "command": "enum",                   // Commande à exécuter
  "target": "string",                  // Cible spécifique (pin, relais, etc.)
  "value": "integer|float|string",     // Valeur à appliquer
  "duration_seconds": "integer",       // Durée (optionnel)
  "priority": "enum",                  // "low" | "normal" | "high" | "urgent"
  "timestamp": "integer"               // Unix timestamp (secondes)
}
```

**Commandes possibles** :

| Command | Description | Value Type | Exemples |
|---------|-------------|------------|----------|
| `RELAY_ON` | Activer relais | integer (1) | Allumer lampe |
| `RELAY_OFF` | Désactiver relais | integer (0) | Éteindre lampe |
| `RELAY_TOGGLE` | Basculer relais | null | Toggle switch |
| `PWM_SET` | Régler PWM | integer (0-255) | Intensité LED |
| `SERVO_ANGLE` | Angle servo | integer (0-180) | Position servo |
| `READ_SENSOR` | Lire capteur | string (sensor_name) | Température |
| `PLAY_AUDIO` | Jouer audio | string (base64) | Confirmation vocale |
| `REBOOT` | Redémarrer ESP32 | null | Maintenance |

#### Exemple concret - Contrôle Relais

```json
{
  "command_id": "cmd_a7b2c5d3",
  "device_id": "esp32_kitchen",
  "command": "RELAY_ON",
  "target": "RELAY_1",
  "value": 1,
  "duration_seconds": null,
  "priority": "high",
  "timestamp": 1705754420
}
```

#### Exemple concret - Réglage PWM (Intensité LED)

```json
{
  "command_id": "cmd_b8c3d6e4",
  "device_id": "esp32_bedroom",
  "command": "PWM_SET",
  "target": "LED_1",
  "value": 180,
  "duration_seconds": null,
  "priority": "normal",
  "timestamp": 1705754480
}
```

#### Exemple concret - Lecture Capteur

```json
{
  "command_id": "cmd_c9d4e7f5",
  "device_id": "esp32_living_room",
  "command": "READ_SENSOR",
  "target": "DHT22",
  "value": "temperature",
  "duration_seconds": null,
  "priority": "normal",
  "timestamp": 1705754500
}
```

#### Exemple concret - Audio Playback

```json
{
  "command_id": "cmd_d0e5f8g6",
  "device_id": "esp32_kitchen",
  "command": "PLAY_AUDIO",
  "target": "SPEAKER",
  "value": "//NExAAAAAANIAAAAASMZI...base64_audio...",
  "duration_seconds": 3,
  "priority": "urgent",
  "timestamp": 1705754520
}
```

#### Contraintes de validation

| Champ | Type | Obligatoire | Contraintes |
|-------|------|-------------|-------------|
| `command_id` | string | ✅ Oui | Pattern: `cmd_[a-z0-9]+` |
| `device_id` | string | ✅ Oui | Doit correspondre à un ESP32 enregistré |
| `command` | enum | ✅ Oui | Commande valide |
| `target` | string | ✅ Oui | Non vide |
| `value` | mixed | ❌ Non | Type selon command |
| `priority` | enum | ✅ Oui | `low`, `normal`, `high`, `urgent` |
| `timestamp` | integer | ✅ Oui | Unix timestamp valide |

---

## 10. Flux 7 - ESP32 → n8n (Retour État)

### 10.1 Description

**Module émetteur :** ESP32 - MQTT Client  
**Module récepteur :** Orchestrateur n8n - MQTT Subscriber  
**Protocole :** MQTT (publish/subscribe)  
**Topic MQTT :** `esp32/status/{device_id}`  
**Objectif :** Informer du résultat d'exécution de la commande

---

### 10.2 OUTPUT - Statut depuis ESP32

#### Structure JSON

```json
{
  "command_id": "string",              // ID de la commande exécutée
  "device_id": "string",               // ID du dispositif ESP32
  "status": "enum",                    // "SUCCESS" | "ERROR" | "TIMEOUT" | "IN_PROGRESS"
  "details": {                         // Détails d'exécution
    "command_executed": "string",      // Commande exécutée
    "target_affected": "string",       // Cible affectée
    "value_applied": "mixed",          // Valeur appliquée
    "execution_time_ms": "integer",    // Temps d'exécution en ms
    "sensor_reading": "mixed"          // Lecture capteur (si READ_SENSOR)
  },
  "error": {                           // Si status="ERROR" (optionnel)
    "code": "string",                  // Code erreur
    "message": "string",               // Message d'erreur
    "retry_possible": "boolean"        // Si retry possible
  },
  "hardware_state": {                  // État matériel (optionnel)
    "cpu_temp_celsius": "float",       // Température CPU
    "free_heap_bytes": "integer",      // Mémoire libre
    "wifi_signal_strength": "integer", // Signal WiFi (dBm)
    "uptime_seconds": "integer"        // Uptime
  },
  "timestamp": "integer"               // Unix timestamp réponse
}
```

#### Exemple concret - Succès

```json
{
  "command_id": "cmd_a7b2c5d3",
  "device_id": "esp32_kitchen",
  "status": "SUCCESS",
  "details": {
    "command_executed": "RELAY_ON",
    "target_affected": "RELAY_1",
    "value_applied": 1,
    "execution_time_ms": 45,
    "sensor_reading": null
  },
  "error": null,
  "hardware_state": {
    "cpu_temp_celsius": 42.5,
    "free_heap_bytes": 85632,
    "wifi_signal_strength": -58,
    "uptime_seconds": 3247
  },
  "timestamp": 1705754425
}
```

#### Exemple concret - Lecture Capteur

```json
{
  "command_id": "cmd_c9d4e7f5",
  "device_id": "esp32_living_room",
  "status": "SUCCESS",
  "details": {
    "command_executed": "READ_SENSOR",
    "target_affected": "DHT22",
    "value_applied": "temperature",
    "execution_time_ms": 120,
    "sensor_reading": {
      "temperature_celsius": 22.4,
      "humidity_percent": 58.2,
      "timestamp": 1705754505
    }
  },
  "error": null,
  "hardware_state": {
    "cpu_temp_celsius": 41.8,
    "free_heap_bytes": 87124,
    "wifi_signal_strength": -62,
    "uptime_seconds": 3327
  },
  "timestamp": 1705754506
}
```

#### Exemple concret - Erreur

```json
{
  "command_id": "cmd_error123",
  "device_id": "esp32_bedroom",
  "status": "ERROR",
  "details": {
    "command_executed": "PWM_SET",
    "target_affected": "LED_1",
    "value_applied": null,
    "execution_time_ms": 20
  },
  "error": {
    "code": "PIN_NOT_CONFIGURED",
    "message": "Le pin LED_1 n'est pas configuré en mode PWM",
    "retry_possible": false
  },
  "hardware_state": {
    "cpu_temp_celsius": 43.1,
    "free_heap_bytes": 84512,
    "wifi_signal_strength": -65,
    "uptime_seconds": 3350
  },
  "timestamp": 1705754530
}
```

#### Contraintes de validation

| Champ | Type | Obligatoire | Contraintes |
|-------|------|-------------|-------------|
| `command_id` | string | ✅ Oui | Référence commande reçue |
| `device_id` | string | ✅ Oui | ID ESP32 |
| `status` | enum | ✅ Oui | `SUCCESS`, `ERROR`, `TIMEOUT`, `IN_PROGRESS` |
| `details.execution_time_ms` | integer | ✅ Oui | Min: 0 |
| `error` | object | ❌ Non | Obligatoire si status="ERROR" |
| `timestamp` | integer | ✅ Oui | Unix timestamp |

---

## 11. Flux 8 - n8n → Python (Résultat Final)

### 11.1 Description

**Module émetteur :** Orchestrateur n8n - Workflow terminal  
**Module récepteur :** Backend Python - Callback Handler  
**Route API :** `POST /callback/n8n`  
**Objectif :** Notifier le backend du résultat d'exécution final

---

### 11.2 OUTPUT - Résultat Exécution vers Python

#### Structure JSON

```json
{
  "action_id": "string",               // ID de l'action source
  "execution_status": "enum",          // "SUCCESS" | "ERROR" | "PARTIAL" | "TIMEOUT"
  "module": "string",                  // Module ayant exécuté ("ESP32", "EMAIL", "WEB")
  "execution_details": {               // Détails d'exécution
    "workflow_name": "string",         // Nom du workflow n8n
    "execution_id": "string",          // ID d'exécution n8n
    "steps_executed": "integer",       // Nombre d'étapes exécutées
    "total_duration_ms": "integer",    // Durée totale
    "steps_details": [                 // Détails des étapes (optionnel)
      {
        "step_name": "string",
        "status": "enum",              // "success" | "error" | "skipped"
        "duration_ms": "integer",
        "output": "mixed"
      }
    ]
  },
  "result_data": {                     // Données de résultat (optionnel)
    // Structure variable selon intent
  },
  "error": {                           // Si execution_status="ERROR" (optionnel)
    "code": "string",                  // Code erreur
    "message": "string",               // Message détaillé
    "step_failed": "string",           // Étape en échec
    "retry_possible": "boolean",       // Si retry possible
    "retry_count": "integer"           // Nombre de tentatives
  },
  "timestamp": "ISO8601"               // Date/heure résultat
}
```

#### Exemple concret - Succès Contrôle IoT

```json
{
  "action_id": "act_1001a7b2",
  "execution_status": "SUCCESS",
  "module": "ESP32",
  "execution_details": {
    "workflow_name": "wf_control_iot",
    "execution_id": "exec_n8n_9a7b2c5d",
    "steps_executed": 4,
    "total_duration_ms": 1245,
    "steps_details": [
      {
        "step_name": "validate_action",
        "status": "success",
        "duration_ms": 45,
        "output": {"valid": true}
      },
      {
        "step_name": "publish_mqtt",
        "status": "success",
        "duration_ms": 120,
        "output": {"published": true}
      },
      {
        "step_name": "wait_esp32_response",
        "status": "success",
        "duration_ms": 850,
        "output": {"response_received": true}
      },
      {
        "step_name": "log_execution",
        "status": "success",
        "duration_ms": 230,
        "output": {"logged": true}
      }
    ]
  },
  "result_data": {
    "device_id": "esp32_kitchen",
    "command_executed": "RELAY_ON",
    "target": "LAMP_1",
    "final_state": "ON",
    "execution_time_ms": 45
  },
  "error": null,
  "timestamp": "2026-01-20T10:00:23Z"
}
```

#### Exemple concret - Succès Envoi Email

```json
{
  "action_id": "act_2002b8c3",
  "execution_status": "SUCCESS",
  "module": "EMAIL",
  "execution_details": {
    "workflow_name": "wf_send_email",
    "execution_id": "exec_n8n_b8c3d6e4",
    "steps_executed": 5,
    "total_duration_ms": 2840,
    "steps_details": [
      {
        "step_name": "validate_action",
        "status": "success",
        "duration_ms": 35,
        "output": {"valid": true}
      },
      {
        "step_name": "resolve_recipient_email",
        "status": "success",
        "duration_ms": 180,
        "output": {"email": "jean@example.com"}
      },
      {
        "step_name": "connect_smtp",
        "status": "success",
        "duration_ms": 520,
        "output": {"connected": true}
      },
      {
        "step_name": "send_email",
        "status": "success",
        "duration_ms": 1850,
        "output": {"sent": true, "message_id": "msg_abc123"}
      },
      {
        "step_name": "log_execution",
        "status": "success",
        "duration_ms": 255,
        "output": {"logged": true}
      }
    ]
  },
  "result_data": {
    "recipient_email": "jean@example.com",
    "subject": "Report de réunion",
    "message_id": "msg_abc123",
    "sent_at": "2026-01-20T10:00:38Z"
  },
  "error": null,
  "timestamp": "2026-01-20T10:00:38Z"
}
```

#### Exemple concret - Erreur

```json
{
  "action_id": "act_error999",
  "execution_status": "ERROR",
  "module": "ESP32",
  "execution_details": {
    "workflow_name": "wf_control_iot",
    "execution_id": "exec_n8n_error999",
    "steps_executed": 2,
    "total_duration_ms": 5850,
    "steps_details": [
      {
        "step_name": "validate_action",
        "status": "success",
        "duration_ms": 50,
        "output": {"valid": true}
      },
      {
        "step_name": "publish_mqtt",
        "status": "success",
        "duration_ms": 100,
        "output": {"published": true}
      },
      {
        "step_name": "wait_esp32_response",
        "status": "error",
        "duration_ms": 5700,
        "output": {"timeout": true}
      }
    ]
  },
  "result_data": null,
  "error": {
    "code": "ESP32_TIMEOUT",
    "message": "L'ESP32 'esp32_bedroom' n'a pas répondu dans le délai de 5 secondes",
    "step_failed": "wait_esp32_response",
    "retry_possible": true,
    "retry_count": 1
  },
  "timestamp": "2026-01-20T10:01:05Z"
}
```

#### Contraintes de validation

| Champ | Type | Obligatoire | Contraintes |
|-------|------|-------------|-------------|
| `action_id` | string | ✅ Oui | Référence action source |
| `execution_status` | enum | ✅ Oui | `SUCCESS`, `ERROR`, `PARTIAL`, `TIMEOUT` |
| `module` | string | ✅ Oui | Non vide |
| `execution_details.total_duration_ms` | integer | ✅ Oui | Min: 0 |
| `error` | object | ❌ Non | Obligatoire si status="ERROR" |
| `timestamp` | ISO8601 | ✅ Oui | Format UTC |

---

## 12. Flux ESP32 → Python (Audio Brut)

### 12.1 Description

**Module émetteur :** ESP32 - Audio Handler  
**Module récepteur :** Backend Python - Audio Endpoint  
**Route API :** `POST /audio/upload`  
**Objectif :** Transmettre un enregistrement audio brut pour transcription

---

### 12.2 INPUT - Upload Audio vers Python

#### Structure JSON

```json
{
  "device_id": "string",               // ID ESP32 émetteur
  "user_id": "string",                 // ID utilisateur (si connu)
  "audio_data": "string",              // Audio encodé base64
  "audio_format": "enum",              // "wav" | "mp3" | "opus" | "raw"
  "audio_metadata": {                  // Métadonnées audio
    "sample_rate": "integer",          // Fréquence échantillonnage (Hz)
    "bit_depth": "integer",            // Profondeur bits (8, 16, 24, 32)
    "channels": "integer",             // Nombre canaux (1=mono, 2=stereo)
    "duration_ms": "integer",          // Durée enregistrement (ms)
    "size_bytes": "integer"            // Taille fichier
  },
  "recording_context": {               // Contexte enregistrement
    "wake_word_detected": "boolean",   // Si wake word détecté
    "wake_word": "string",             // Wake word utilisé (optionnel)
    "ambient_noise_level": "integer",  // Niveau bruit ambiant (dB)
    "recording_quality": "enum"        // "low" | "medium" | "high"
  },
  "timestamp": "ISO8601"               // Date/heure enregistrement
}
```

#### Exemple concret

```json
{
  "device_id": "esp32_kitchen",
  "user_id": "user_42",
  "audio_data": "//NExAAAAAANIAAAAASMZI...base64_encoded_audio_data...",
  "audio_format": "wav",
  "audio_metadata": {
    "sample_rate": 16000,
    "bit_depth": 16,
    "channels": 1,
    "duration_ms": 3500,
    "size_bytes": 112000
  },
  "recording_context": {
    "wake_word_detected": true,
    "wake_word": "jarvis",
    "ambient_noise_level": 45,
    "recording_quality": "high"
  },
  "timestamp": "2026-01-20T10:00:00Z"
}
```

---

## 13. Flux Python → ESP32 (Audio Réponse)

### 13.1 Description

**Module émetteur :** Backend Python - TTS Engine  
**Module récepteur :** ESP32 - Audio Handler  
**Protocole :** MQTT ou HTTP POST  
**Objectif :** Envoyer une réponse vocale à l'utilisateur

---

### 13.2 OUTPUT - Audio Réponse vers ESP32

#### Structure JSON

```json
{
  "response_id": "string",             // ID unique réponse
  "device_id": "string",               // ESP32 destinataire
  "audio_data": "string",              // Audio encodé base64
  "audio_format": "enum",              // "mp3" | "wav" | "opus"
  "audio_metadata": {                  // Métadonnées audio
    "sample_rate": "integer",          // Fréquence (Hz)
    "bit_depth": "integer",            // Bits
    "channels": "integer",             // Canaux
    "duration_ms": "integer",          // Durée (ms)
    "size_bytes": "integer"            // Taille
  },
  "playback_config": {                 // Configuration lecture
    "volume_percent": "integer",       // Volume (0-100)
    "speed_multiplier": "float",       // Vitesse (0.5-2.0)
    "interrupt_current": "boolean"     // Interrompre audio en cours
  },
  "response_type": "enum",             // "conversation" | "confirmation" | "notification"
  "priority": "enum",                  // "low" | "normal" | "high" | "urgent"
  "timestamp": "ISO8601"               // Date/heure génération
}
```

#### Exemple concret

```json
{
  "response_id": "resp_a1b2c3d4",
  "device_id": "esp32_kitchen",
  "audio_data": "//NExAAAAAANIAAAAASMZI...base64_encoded_audio...",
  "audio_format": "mp3",
  "audio_metadata": {
    "sample_rate": 24000,
    "bit_depth": 16,
    "channels": 1,
    "duration_ms": 3120,
    "size_bytes": 93600
  },
  "playback_config": {
    "volume_percent": 75,
    "speed_multiplier": 1.0,
    "interrupt_current": true
  },
  "response_type": "confirmation",
  "priority": "high",
  "timestamp": "2026-01-20T10:00:17Z"
}
```

---

## 14. Schémas JSON Réutilisables

### 14.1 Schéma Context (Contexte utilisateur)

```json
{
  "context": {
    "user_id": "string",               // ID utilisateur (OBLIGATOIRE)
    "language": "string",              // ISO 639-1 (OBLIGATOIRE)
    "channel": "enum",                 // "voice"|"text"|"mobile"|"web" (OBLIGATOIRE)
    "session_id": "string",            // ID session (optionnel)
    "location": "string",              // Localisation (optionnel)
    "time_of_day": "enum",             // "morning"|"afternoon"|"evening"|"night"
    "device_info": {                   // Info appareil (optionnel)
      "device_id": "string",
      "device_type": "string",
      "os": "string",
      "app_version": "string"
    },
    "previous_intent": "string"        // Intention précédente (optionnel)
  }
}
```

---

### 14.2 Schéma Security (Sécurité)

```json
{
  "security": {
    "auth_level": "integer",           // 1=user, 2=admin (OBLIGATOIRE)
    "signature": "string",             // HMAC signature (OBLIGATOIRE)
    "signed_at": "ISO8601",            // Date signature (si signé)
    "requires_confirmation": "boolean",// Si confirmation nécessaire
    "permissions_required": ["string"],// Permissions requises
    "token": "string"                  // JWT token (optionnel)
  }
}
```

---

### 14.3 Schéma Timestamps (Horodatages)

```json
{
  "timestamps": {
    "created_at": "ISO8601",           // Création (OBLIGATOIRE)
    "updated_at": "ISO8601",           // Dernière MAJ (OBLIGATOIRE)
    "confirmed_at": "ISO8601",         // Confirmation (si action)
    "executed_at": "ISO8601",          // Exécution (si action)
    "completed_at": "ISO8601",         // Complétion (si action)
    "expires_at": "ISO8601"            // Expiration (optionnel)
  }
}
```

---

### 14.4 Schéma Error (Erreur)

```json
{
  "error": {
    "code": "string",                  // Code erreur (OBLIGATOIRE)
    "message": "string",               // Message détaillé (OBLIGATOIRE)
    "details": "mixed",                // Détails additionnels (optionnel)
    "step_failed": "string",           // Étape en échec (optionnel)
    "retry_possible": "boolean",       // Si retry possible
    "retry_count": "integer",          // Nombre tentatives
    "stack_trace": "string"            // Stack trace (debug uniquement)
  }
}
```

---

## 15. Règles de Validation

### 15.1 Règles Générales

| Règle | Description | Criticité |
|-------|-------------|-----------|
| **Type Safety** | Tous les champs doivent respecter leur type déclaré | Critique |
| **Required Fields** | Tous les champs obligatoires doivent être présents | Critique |
| **Enum Values** | Les valeurs enum doivent correspondre exactement | Critique |
| **Timestamps** | Format ISO 8601 strict UTC (ex: `2026-01-20T10:00:00Z`) | Critique |
| **IDs Format** | Pattern spécifique selon type (ex: `req_`, `act_`, `conv_`) | Important |
| **Max Length** | Respecter longueurs max (ex: texte 1000 chars) | Important |
| **No SQL Injection** | Nettoyage inputs utilisateur | Critique |
| **Signature HMAC** | Actions confirmées doivent avoir signature valide | Critique |

---

### 15.2 Codes Erreur Standardisés

| Code | Description | Action recommandée |
|------|-------------|-------------------|
| `INVALID_JSON` | JSON malformé | Rejeter avec message |
| `MISSING_REQUIRED_FIELD` | Champ obligatoire manquant | Rejeter avec détails |
| `INVALID_TYPE` | Type incorrect | Rejeter avec détails |
| `INVALID_ENUM_VALUE` | Valeur enum invalide | Rejeter avec valeurs valides |
| `SIGNATURE_INVALID` | Signature HMAC invalide | Rejeter immédiatement |
| `SIGNATURE_EXPIRED` | Signature expirée | Rejeter avec expiration |
| `UNAUTHORIZED` | Utilisateur non autorisé | Authentification requise |
| `PERMISSION_DENIED` | Permission insuffisante | Rejeter avec permission requise |
| `ACTION_EXPIRED` | Action expirée | Rejeter avec nouvelle demande |
| `DUPLICATE_ID` | ID déjà existant | Rejeter avec nouvel ID |
| `LLM_TIMEOUT` | LLM n'a pas répondu | Retry avec backoff |
| `ESP32_TIMEOUT` | ESP32 n'a pas répondu | Retry ou notification |
| `LOW_CONFIDENCE` | Confiance < seuil | Demander clarification |

---

## 16. Exemples Complets par Scénario

### 16.1 Scénario Complet : Contrôle IoT (Allumer Lampe)

#### Étape 1 : ESP32 → Python (Audio)

```json
{
  "device_id": "esp32_kitchen",
  "user_id": "user_42",
  "audio_data": "//NExAAAAAANIAAAAASMZI...base64...",
  "audio_format": "wav",
  "audio_metadata": {
    "sample_rate": 16000,
    "bit_depth": 16,
    "channels": 1,
    "duration_ms": 2800,
    "size_bytes": 89600
  },
  "recording_context": {
    "wake_word_detected": true,
    "wake_word": "jarvis",
    "ambient_noise_level": 42,
    "recording_quality": "high"
  },
  "timestamp": "2026-01-20T10:00:00Z"
}
```

#### Étape 2 : Classification Interne

```json
{
  "request_id": "req_20260120_100001",
  "classification": "action",
  "confidence": 0.95,
  "method": "rules",
  "reasoning": {
    "matched_keywords": ["allume", "lampe", "cuisine"],
    "score_action": 0.95,
    "score_conversation": 0.05
  },
  "intent_hint": "control_iot",
  "processing_time_ms": 18,
  "timestamp": "2026-01-20T10:00:01Z"
}
```

#### Étape 3 : Python → LLM (Analyse)

```json
{
  "request_id": "req_20260120_100001",
  "type": "intent_analysis",
  "input_text": "Allume la lampe de la cuisine",
  "language": "fr",
  "context": {
    "user_id": "user_42",
    "channel": "voice",
    "session_id": "session_abc123"
  },
  "analysis_mode": {
    "extract_intent": true,
    "extract_entities": true
  },
  "timestamp": "2026-01-20T10:00:01Z"
}
```

#### Étape 4 : LLM → Python (Résultat)

```json
{
  "request_id": "req_20260120_100001",
  "analysis_result": {
    "intent": "control_iot",
    "intent_confidence": 0.96,
    "entities": {
      "device": "lamp",
      "location": "kitchen",
      "action": "on"
    }
  },
  "status": "success",
  "timestamp": "2026-01-20T10:00:02Z"
}
```

#### Étape 5 : ActionJSON DRAFT

```json
{
  "action_id": "act_1001a7b2",
  "intent": "control_iot",
  "state": "DRAFT",
  "confirmed": false,
  "payload": {
    "device_id": "esp32_kitchen",
    "command": "RELAY_ON",
    "target": "LAMP_1",
    "value": 1
  },
  "security": {
    "signature": "pending",
    "requires_confirmation": true
  },
  "timestamps": {
    "created_at": "2026-01-20T10:00:02Z"
  }
}
```

#### Étape 6 : Demande Confirmation

```json
{
  "action_id": "act_1001a7b2",
  "confirmation_request": {
    "text": "Je vais allumer la lampe de la cuisine. Confirmer ?",
    "tts_enabled": true,
    "audio_base64": "//NExAAAAAANIAAAAASMZI...base64..."
  },
  "timestamp": "2026-01-20T10:00:03Z"
}
```

#### Étape 7 : Réponse Utilisateur

```json
{
  "action_id": "act_1001a7b2",
  "user_response": {
    "raw_input": "Oui, vas-y",
    "parsed_value": "confirm",
    "confidence": 0.98
  },
  "timestamp": "2026-01-20T10:00:05Z"
}
```

#### Étape 8 : ActionJSON CONFIRMED

```json
{
  "action_id": "act_1001a7b2",
  "state": "CONFIRMED",
  "confirmed": true,
  "security": {
    "signature": "HMAC_8f92aa3b7e5c1d4f9a2b6c8e0d3f5a7b",
    "signed_at": "2026-01-20T10:00:05Z"
  },
  "timestamps": {
    "confirmed_at": "2026-01-20T10:00:05Z"
  }
}
```

#### Étape 9 : Python → n8n

```json
{
  "action_id": "act_1001a7b2",
  "intent": "control_iot",
  "confirmed": true,
  "payload": {
    "device_id": "esp32_kitchen",
    "command": "RELAY_ON",
    "target": "LAMP_1"
  },
  "security": {
    "signature": "HMAC_8f92aa3b7e5c1d4f9a2b6c8e0d3f5a7b"
  }
}
```

#### Étape 10 : n8n → ESP32

```json
{
  "command_id": "cmd_a7b2c5d3",
  "device_id": "esp32_kitchen",
  "command": "RELAY_ON",
  "target": "RELAY_1",
  "value": 1,
  "timestamp": 1705754406
}
```

#### Étape 11 : ESP32 → n8n

```json
{
  "command_id": "cmd_a7b2c5d3",
  "device_id": "esp32_kitchen",
  "status": "SUCCESS",
  "details": {
    "execution_time_ms": 45
  },
  "timestamp": 1705754407
}
```

#### Étape 12 : n8n → Python (Résultat)

```json
{
  "action_id": "act_1001a7b2",
  "execution_status": "SUCCESS",
  "module": "ESP32",
  "result_data": {
    "command_executed": "RELAY_ON",
    "final_state": "ON"
  },
  "timestamp": "2026-01-20T10:00:08Z"
}
```

#### Étape 13 : Python → ESP32 (Réponse Vocale)

```json
{
  "response_id": "resp_success1",
  "device_id": "esp32_kitchen",
  "audio_data": "//NExAAAAAANIAAAAASMZI...base64...",
  "audio_format": "mp3",
  "response_type": "confirmation",
  "timestamp": "2026-01-20T10:00:09Z"
}
```

---

### 16.2 Scénario Complet : Conversation Simple

#### Étape 1 : ESP32 → Python (Audio)

```json
{
  "device_id": "esp32_living_room",
  "user_id": "user_42",
  "audio_data": "//NExAAAAAANIAAAAASMZI...base64...",
  "audio_format": "wav",
  "timestamp": "2026-01-20T11:30:00Z"
}
```

#### Étape 2 : Classification

```json
{
  "request_id": "req_20260120_113001",
  "classification": "conversation",
  "confidence": 0.94,
  "method": "rules",
  "timestamp": "2026-01-20T11:30:01Z"
}
```

#### Étape 3 : Python → LLM (Conversation)

```json
{
  "request_id": "req_20260120_113001",
  "conversation_id": "conv_xyz789",
  "type": "conversation",
  "input_text": "Bonjour, ça va ?",
  "timestamp": "2026-01-20T11:30:01Z"
}
```

#### Étape 4 : LLM → Python (Réponse)

```json
{
  "request_id": "req_20260120_113001",
  "response": {
    "text": "Bonjour ! Oui, je vais très bien, merci. Et vous ?",
    "tts_enabled": true,
    "audio_base64": "//NExAAAAAANIAAAAASMZI...base64..."
  },
  "status": "completed",
  "timestamp": "2026-01-20T11:30:02Z"
}
```

#### Étape 5 : Python → ESP32 (Audio Réponse)

```json
{
  "response_id": "resp_conv1",
  "device_id": "esp32_living_room",
  "audio_data": "//NExAAAAAANIAAAAASMZI...base64...",
  "response_type": "conversation",
  "timestamp": "2026-01-20T11:30:02Z"
}
```

**FIN - Pas d'interaction avec n8n**

---

## 📝 Conclusion

Ce document constitue la **spécification complète et définitive** de tous les formats JSON échangés entre les modules du système Agent Intelligent Embarqué.

### Points clés :

✅ **14 flux JSON** documentés en détail  
✅ **Structures INPUT/OUTPUT** complètes avec tous les champs  
✅ **Exemples concrets** pour chaque scénario  
✅ **Contraintes de validation** strictes  
✅ **Codes erreur** standardisés  
✅ **Schémas réutilisables** (Context, Security, Timestamps, Error)  
✅ **2 scénarios complets** de bout en bout  

Ce document doit servir de **référence unique** pour l'implémentation de tous les modules.

---

**Document créé le : 20 janvier 2026**  
**Version : 3.0 - Référentiel Complet**  
**Statut : FINAL - Prêt pour implémentation**
