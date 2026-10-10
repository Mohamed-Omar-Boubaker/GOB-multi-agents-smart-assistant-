# API Reference - GOB Agent

Documentation complète de tous les endpoints de l'API Backend.

---

## 🌐 Base URL

```
Development: http://localhost:8000
Production:  https://api.yourdomain.com
```

**Format**: REST API avec JSON  
**Authentication**: Aucune (TODO: JWT tokens)  
**CORS**: Activé pour localhost:5173

---

## 📡 Endpoints

### 🏥 Health & Info

#### GET /health

Vérifier l'état du serveur.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response: 200 OK**
```json
{
  "status": "ok",
  "timestamp": "2026-02-14T15:30:00Z",
  "services": {
    "stt": "online",
    "llm": "online",
    "tts": "online",
    "database": "online"
  }
}
```

#### GET /

Informations sur l'API.

**Response: 200 OK**
```json
{
  "service": "GOB Agent - API Backend",
  "version": "1.0.0",
  "description": "Agent vocal intelligent avec classification Conversation/Action",
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "commands": ["/command/text", "/command/audio"],
    "actions": ["/action/confirm/{action_id}", "/action/status/{action_id}"],
    "memory": ["/memory/{user_id}"],
    "actions_list": ["/actions/{user_id}"]
  }
}
```

---

### 💬 Commandes

#### POST /command/text

Envoyer une commande texte.

**Request:**
```json
{
  "text": "Hello, how are you?",
  "user_id": "web_user_001",
  "language": "en",
  "source": "react_web"
}
```

**Response: 200 OK (Conversation)**
```json
{
  "request_id": "req_abc123",
  "user_id": "web_user_001",
  "classification": "conversation",
  "type": "conversation",
  "response": "I'm doing great! How can I help you today?",
  "audio": {
    "audio_data": "base64_encoded_audio_data",
    "audio_format": "wav"
  },
  "metadata": {
    "entities": [
      {
        "type": "emotion",
        "name": "greeting",
        "confidence": 0.95
      }
    ],
    "emotion": "friendly",
    "intent": "greeting",
    "summary": "User greeted the agent"
  },
  "processing_time_ms": 1850
}
```

**Response: 200 OK (Action)**
```json
{
  "request_id": "req_def456",
  "user_id": "web_user_001",
  "classification": "action",
  "type": "action",
  "action_id": "act_xyz789",
  "status": "awaiting_confirmation",
  "state": "PENDING_CONFIRMATION",
  "message": "Do you want to turn on the lamp in the living room?",
  "audio_response": {
    "audio_data": "base64_audio",
    "audio_format": "wav"
  },
  "action_details": {
    "action_id": "act_xyz789",
    "user_id": "web_user_001",
    "intent": "control_iot",
    "entities": {
      "device_type": "lamp",
      "action": "turn_on",
      "location": "living_room"
    },
    "original_text": "Turn on the lamp in the living room",
    "language": "en",
    "timestamp": "2026-02-14T15:30:00Z"
  },
  "processing_time_ms": 2100
}
```

**Error Responses:**

```json
// 400 Bad Request - Missing field
{
  "detail": "Missing required field: text"
}

// 503 Service Unavailable - Agent Core not ready
{
  "detail": "Agent Core not initialized"
}
```

---

#### POST /command/audio

Envoyer une commande vocale (audio).

**Request:**
```json
{
  "audio_data": "base64_encoded_audio_data",
  "audio_format": "webm",
  "user_id": "web_user_001",
  "language": "en",
  "source": "react_web"
}
```

**Notes:**
- `audio_data`: Audio encodé en base64 (sans préfixe `data:audio/webm;base64,`)
- `audio_format`: `webm`, `wav`, `mp3` supportés
- Pipeline: Audio → STT (Whisper) → Classification → LLM → TTS

**Response:** Identique à `/command/text` + champ `transcription`

```json
{
  "transcription": "Turn on the lamp in the living room",
  // ... (reste identique à /command/text)
}
```

**Error Responses:**

```json
// 501 Not Implemented - Audio désactivé
{
  "detail": "Audio processing is disabled"
}

// 500 Internal Server Error - STT failed
{
  "detail": "Speech-to-text conversion failed"
}
```

---

### ⚙️ Actions

#### POST /action/confirm/{action_id}

Confirmer ou annuler une action.

**Path Parameters:**
- `action_id`: ID de l'action (ex: `act_xyz789`)

**Request:**
```json
{
  "response": "yes",
  "user_id": "web_user_001"
}
```

**Réponses acceptées:**
- **Confirmer**: `"yes"`, `"oui"`, `"ok"`, `"confirm"`, `"do it"`
- **Annuler**: `"no"`, `"non"`, `"cancel"`, `"stop"`
- **Modifier**: `"change"`, `"modify"`

**Response: 200 OK (Confirmé)**
```json
{
  "action_id": "act_xyz789",
  "status": "confirmed",
  "state": "EXECUTING",
  "n8n_response": {
    "execution_id": "exec_123",
    "status": "running"
  },
  "message": "✅ Lamp turned on successfully!"
}
```

**Response: 200 OK (Annulé)**
```json
{
  "action_id": "act_xyz789",
  "status": "canceled",
  "state": "CANCELED",
  "message": "Action canceled by user"
}
```

**Error Responses:**

```json
// 404 Not Found - Action inexistante
{
  "detail": "Action act_xyz789 not found"
}

// 400 Bad Request - État invalide
{
  "detail": "Action is not in PENDING_CONFIRMATION state"
}
```

---

#### GET /action/status/{action_id}

Obtenir le statut d'une action.

**Path Parameters:**
- `action_id`: ID de l'action

**Request:**
```bash
curl http://localhost:8000/action/status/act_xyz789
```

**Response: 200 OK**
```json
{
  "action_id": "act_xyz789",
  "current_state": "COMPLETED",
  "action_json": {
    "action_id": "act_xyz789",
    "user_id": "web_user_001",
    "intent": "control_iot",
    "entities": {
      "device_type": "lamp",
      "action": "turn_on",
      "location": "living_room"
    },
    "original_text": "Turn on the lamp",
    "language": "en",
    "timestamp": "2026-02-14T15:30:00Z"
  },
  "state_history": [
    {
      "state": "DRAFT",
      "timestamp": "2026-02-14T15:30:00Z",
      "reason": "Action created"
    },
    {
      "state": "PENDING_CONFIRMATION",
      "timestamp": "2026-02-14T15:30:01Z",
      "reason": "Awaiting user confirmation"
    },
    {
      "state": "CONFIRMED",
      "timestamp": "2026-02-14T15:30:05Z",
      "reason": "User confirmed"
    },
    {
      "state": "EXECUTING",
      "timestamp": "2026-02-14T15:30:06Z",
      "reason": "Sent to n8n"
    },
    {
      "state": "COMPLETED",
      "timestamp": "2026-02-14T15:30:08Z",
      "reason": "Execution successful"
    }
  ]
}
```

**États possibles:**
- `DRAFT`: En cours de création
- `PENDING_CONFIRMATION`: Attente confirmation utilisateur
- `CONFIRMED`: Confirmée, prête à exécuter
- `EXECUTING`: En cours d'exécution
- `COMPLETED`: Terminée avec succès
- `CANCELED`: Annulée par l'utilisateur
- `FAILED`: Échouée

---

#### GET /actions/{user_id}

Lister toutes les actions d'un utilisateur.

**Path Parameters:**
- `user_id`: ID utilisateur (ex: `web_user_001`)

**Query Parameters:**
- `limit`: Nombre max d'actions à retourner (défaut: 20)

**Request:**
```bash
curl "http://localhost:8000/actions/web_user_001?limit=10"
```

**Response: 200 OK**
```json
{
  "user_id": "web_user_001",
  "total_actions": 5,
  "actions": [
    {
      "action_id": "act_123",
      "current_state": "COMPLETED",
      "intent": "control_iot",
      "original_text": "Turn on the lamp",
      "timestamp": "2026-02-14T15:30:00Z",
      "entities": {
        "device_type": "lamp",
        "action": "turn_on"
      },
      "language": "en"
    },
    {
      "action_id": "act_124",
      "current_state": "PENDING_CONFIRMATION",
      "intent": "control_iot",
      "original_text": "Close the door",
      "timestamp": "2026-02-14T15:35:00Z",
      "entities": {
        "device_type": "door",
        "action": "close"
      },
      "language": "en"
    }
  ]
}
```

**Tri**: Plus récentes d'abord (par timestamp)

---

### 🧠 Mémoire

#### GET /memory/{user_id}

Récupérer la mémoire stockée pour un utilisateur.

**Path Parameters:**
- `user_id`: ID utilisateur

**Request:**
```bash
curl http://localhost:8000/memory/web_user_001
```

**Response: 200 OK**
```json
{
  "user_id": "web_user_001",
  "total_facts": 15,
  "facts": [
    {
      "fact_id": "fact_abc123",
      "user_id": "web_user_001",
      "fact_type": "person",
      "fact_text": "User's name is Yamin",
      "confidence": 0.95,
      "extracted_at": "2026-02-14T15:20:00Z",
      "source_conversation_id": "conv_xyz"
    },
    {
      "fact_id": "fact_def456",
      "user_id": "web_user_001",
      "fact_type": "preference",
      "fact_text": "User likes pizza",
      "confidence": 0.90,
      "extracted_at": "2026-02-14T15:25:00Z",
      "source_conversation_id": "conv_xyz"
    }
  ],
  "recent_emotions": ["happy", "satisfied", "neutral", "curious", "excited"],
  "preferences": {
    "food": ["pizza", "burger"],
    "drink": ["coffee", "tea"],
    "other": ["music", "sports"]
  }
}
```

**Types de faits:**
- `person`: Informations personnelles (nom, âge, etc.)
- `preference`: Préférences (nourriture, boissons, loisirs)
- `relationship`: Relations avec d'autres personnes
- `location`: Lieux mentionnés
- `emotion`: États émotionnels
- `device`: Dispositifs possédés/utilisés
- `other`: Autres informations

---

## 🔒 Codes d'État HTTP

| Code | Signification | Usage |
|------|--------------|-------|
| 200 | OK | Requête réussie |
| 400 | Bad Request | Paramètres invalides ou manquants |
| 404 | Not Found | Ressource introuvable (action_id, user_id) |
| 500 | Internal Server Error | Erreur serveur (LLM, STT, TTS) |
| 501 | Not Implemented | Feature désactivée (ex: audio) |
| 503 | Service Unavailable | Service non initialisé |

---

## 🔄 Workflow Actions Complet

### 1. Créer une action

```bash
POST /command/text
{
  "text": "Turn on the lamp",
  "user_id": "user_001"
}
```

**→ Response:** `action_id = act_123`, `status = awaiting_confirmation`

### 2. Confirmer l'action

```bash
POST /action/confirm/act_123
{
  "response": "yes",
  "user_id": "user_001"
}
```

**→ Response:** `status = confirmed`, `state = EXECUTING`

### 3. Vérifier le statut

```bash
GET /action/status/act_123
```

**→ Response:** `current_state = COMPLETED`

### 4. Lister toutes les actions

```bash
GET /actions/user_001?limit=10
```

**→ Response:** Liste des 10 dernières actions

---

## 🧪 Exemples de Requêtes

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Text command
curl -X POST http://localhost:8000/command/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "user_id": "test_user", "language": "en"}'

# Action confirmation
curl -X POST http://localhost:8000/action/confirm/act_123 \
  -H "Content-Type: application/json" \
  -d '{"response": "yes", "user_id": "test_user"}'

# Get memory
curl http://localhost:8000/memory/test_user
```

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Text command
response = requests.post(f"{BASE_URL}/command/text", json={
    "text": "Turn on the lamp",
    "user_id": "user_001",
    "language": "en"
})
data = response.json()
print(f"Action ID: {data['action_id']}")

# Confirm action
action_id = data['action_id']
response = requests.post(f"{BASE_URL}/action/confirm/{action_id}", json={
    "response": "yes",
    "user_id": "user_001"
})
print(f"Status: {response.json()['status']}")
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000';

// Text command
const response = await fetch(`${BASE_URL}/command/text`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Turn on the lamp',
    user_id: 'user_001',
    language: 'en'
  })
});

const data = await response.json();
console.log('Action ID:', data.action_id);

// Confirm action
const confirmResponse = await fetch(
  `${BASE_URL}/action/confirm/${data.action_id}`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      response: 'yes',
      user_id: 'user_001'
    })
  }
);

console.log('Status:', (await confirmResponse.json()).status);
```

---

## 📊 Limites & Rate Limiting

**Limites actuelles** (peut changer en production):

- **Max audio size**: 10 MB
- **Max text length**: 1000 caractères
- **Timeout requête**: 30 secondes
- **Rate limit**: Aucun (TODO en production)

**Recommandations:**
- Implémenter rate limiting en production (ex: 100 req/min/user)
- Utiliser queue système pour actions lourdes
- Caching Redis pour réponses fréquentes

---

## 🔐 Sécurité

### Headers Requis (Future)

```http
Authorization: Bearer <JWT_TOKEN>
X-API-Key: <API_KEY>
```

### HMAC Signature (Actions vers n8n)

Les actions sont signées avec HMAC-SHA256 avant envoi à n8n:

```python
import hmac
import hashlib

secret = "your_secret_key"
payload = json.dumps(action_json)
signature = hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()
```

n8n vérifie la signature avant exécution.

---

## 📖 Documentation Interactive

**Swagger UI**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc

---

**Version**: 1.0.0  
**Dernière mise à jour**: 14 février 2026
