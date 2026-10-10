# 🎙️ Architecture Wake Word avec Whisper (Mobile Compatible)

## 📋 Vue d'ensemble

**Problème actuel:** Web Speech API (Google) ne fonctionne pas dans l'app mobile Capacitor

**Solution:** Créer un serveur Wake Word qui utilise Whisper pour détecter le mot-clé

---

## 🏗️ Architecture Proposée

```
┌─────────────────────────────────────────────────────────────┐
│                     APP MOBILE (React)                       │
│                                                               │
│  1. Enregistrement audio continu (petits chunks 2-3 sec)    │
│  2. Envoi au serveur Wake Word via WebSocket/HTTP            │
│  3. Réception notification "Wake Word Detected"              │
│  4. Démarrage enregistrement commande complète               │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          BACKEND PYTHON - Wake Word Service                  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  FastAPI Endpoint: /wake-word/detect                  │  │
│  │  - Reçoit audio chunks (base64)                       │  │
│  │  - Transcription Whisper rapide                       │  │
│  │  - Détection mot-clé dans transcription               │  │
│  │  - Retourne: {"detected": true/false}                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  WakeWordDetector (Classe Python)                     │  │
│  │  - Utilise Whisper "tiny" (ultra-rapide)             │  │
│  │  - Normalise transcription                            │  │
│  │  - Compare avec wake word configuré                   │  │
│  │  - Scoring de similarité                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure des Fichiers

```
backend/
├── ai/
│   ├── stt_engine.py              # Existant (STT complet)
│   └── wake_word_detector.py      # 🆕 NOUVEAU (Wake Word)
├── main.py                         # Ajouter routes Wake Word
└── config.py                       # Ajouter config Wake Word

agent-ui/src/
├── services/
│   ├── wakeWordService.ts         # Existant (à modifier)
│   └── audioStreamService.ts      # 🆕 NOUVEAU (Stream audio)
└── config/
    └── api.config.ts               # Ajouter endpoint Wake Word
```

---

## 🔧 Composants à Développer

### 1️⃣ Backend - Wake Word Detector (`wake_word_detector.py`)

**Rôle:** Classe Python qui détecte le wake word dans un audio court

**Fonctionnalités:**
- Utilise Whisper "tiny" (la plus rapide)
- Transcription audio court (2-3 secondes)
- Normalisation texte (lowercase, pas de ponctuation)
- Comparaison avec wake word configuré
- Support plusieurs langues

**API:**
```python
class WakeWordDetector:
    def __init__(self, wake_word: str, language: str = "en")
    def detect(self, audio_data: str, audio_format: str = "wav") -> Dict
    def set_wake_word(self, wake_word: str)
```

**Exemple Output:**
```json
{
  "detected": true,
  "confidence": 0.92,
  "transcription": "hey gob",
  "processing_time_ms": 234
}
```

---

### 2️⃣ Backend - FastAPI Routes (`main.py`)

**Route 1: Détection Wake Word**
```
POST /wake-word/detect
Body: {
  "audio_data": "base64...",
  "audio_format": "webm",
  "user_id": "user_001"
}
Response: {
  "detected": boolean,
  "confidence": float,
  "transcription": string
}
```

**Route 2: Configuration Wake Word**
```
POST /wake-word/config
Body: {
  "wake_word": "hey gob",
  "language": "en",
  "user_id": "user_001"
}
```

**Route 3: Test Wake Word**
```
GET /wake-word/test
Response: {
  "current_wake_word": "hey gob",
  "language": "en",
  "model": "whisper-tiny"
}
```

---

### 3️⃣ Frontend - Audio Stream Service (`audioStreamService.ts`)

**Rôle:** Service React qui enregistre et envoie audio en continu

**Fonctionnalités:**
- Enregistrement continu par chunks (2-3 secondes)
- Envoi automatique au backend
- Gestion callback "wake word detected"
- Compatible mobile Capacitor

**API:**
```typescript
class AudioStreamService {
  startContinuousListening(onWakeWordDetected: () => void)
  stopContinuousListening()
  isListening(): boolean
}
```

**Flux:**
```
1. start() → Enregistre 2 secondes
2. Envoie chunk au backend /wake-word/detect
3. Backend répond: detected = true/false
4. Si detected = true → Callback onWakeWordDetected()
5. Sinon, répéter step 1
```

---

### 4️⃣ Frontend - Modification Wake Word Service (`wakeWordService.ts`)

**Changements:**
- Détecter si mobile (Capacitor)
- Si web → Utiliser Web Speech API (actuel)
- Si mobile → Utiliser audioStreamService (nouveau)

```typescript
class WakeWordService {
  private isCapacitor(): boolean
  
  async start() {
    if (this.isCapacitor()) {
      // Utiliser audioStreamService
      audioStreamService.startContinuousListening(...)
    } else {
      // Utiliser Web Speech API (actuel)
      this.recognition.start()
    }
  }
}
```

---

## 📊 Comparaison Solutions

| Critère | Web Speech API | Whisper Wake Word |
|---------|---------------|-------------------|
| **Support Web** | ✅ Oui | ✅ Oui |
| **Support Mobile** | ❌ Non | ✅ Oui |
| **Précision** | ⭐⭐⭐ Bon | ⭐⭐⭐⭐ Excellent |
| **Latence** | ⚡ Instantané | ⏱️ ~200-400ms |
| **Offline** | ❌ Non | ✅ Oui (si local) |
| **Langues** | Limité Google | 99+ langues |
| **Coût** | Gratuit | Gratuit (CPU local) |

---

## 🎯 Plan de Développement

### Phase 1: Backend Wake Word (2-3h)
1. ✅ Créer `wake_word_detector.py`
   - Classe WakeWordDetector
   - Utilise Whisper tiny
   - Détection + normalisation
   
2. ✅ Ajouter routes FastAPI dans `main.py`
   - POST /wake-word/detect
   - POST /wake-word/config
   - GET /wake-word/test

3. ✅ Ajouter config dans `config.py`
   - WAKE_WORD_MODEL = "tiny"
   - WAKE_WORD_THRESHOLD = 0.7
   - WAKE_WORD_LANGUAGE = "en"

4. ✅ Tests Python
   - Tester détection avec fichiers audio
   - Vérifier performance (< 500ms)

---

### Phase 2: Frontend Audio Stream (2-3h)
1. ✅ Créer `audioStreamService.ts`
   - Enregistrement continu
   - Envoi chunks au backend
   - Gestion WebSocket ou polling

2. ✅ Modifier `wakeWordService.ts`
   - Détection Capacitor
   - Switch entre Web Speech / Audio Stream

3. ✅ Modifier `api.config.ts`
   - Ajouter WAKE_WORD_ENDPOINT

4. ✅ Tests Mobile
   - Tester sur téléphone Android
   - Vérifier latence et batterie

---

### Phase 3: Intégration UI (1-2h)
1. ✅ Modifier `MicButton.tsx`
   - Support nouveau service

2. ✅ Modifier `FullscreenEyesScreen.tsx`
   - Support nouveau service

3. ✅ Tests End-to-End
   - Web: Wake word fonctionne
   - Mobile: Wake word fonctionne

---

## ⚙️ Configuration Backend

**Fichier: `backend/config.py`**
```python
# ==================== WAKE WORD DETECTION ====================
WAKE_WORD_ENABLED = os.getenv("WAKE_WORD_ENABLED", "True").lower() == "true"
WAKE_WORD_MODEL = os.getenv("WAKE_WORD_MODEL", "tiny")  # tiny|base
WAKE_WORD_DEFAULT = os.getenv("WAKE_WORD_DEFAULT", "hey assistant")
WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", 0.7))  # 0-1
WAKE_WORD_LANGUAGE = os.getenv("WAKE_WORD_LANGUAGE", "en")
```

**Fichier: `.env`**
```env
# Wake Word Detection
WAKE_WORD_ENABLED=True
WAKE_WORD_MODEL=tiny
WAKE_WORD_DEFAULT=hey gob
WAKE_WORD_THRESHOLD=0.7
WAKE_WORD_LANGUAGE=en
```

---

## 🧪 Tests de Validation

### Test 1: Backend Detection
```python
# test_wake_word.py
detector = WakeWordDetector("hey gob", language="en")

# Test avec audio contenant "hey gob"
result = detector.detect(audio_base64, "wav")
assert result["detected"] == True
assert result["confidence"] > 0.7

# Test avec audio aléatoire
result = detector.detect(random_audio, "wav")
assert result["detected"] == False
```

### Test 2: API Endpoint
```bash
# Envoyer audio avec wake word
curl -X POST http://localhost:8000/wake-word/detect \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64...",
    "audio_format": "webm"
  }'

# Réponse attendue
{
  "detected": true,
  "confidence": 0.92,
  "transcription": "hey gob"
}
```

### Test 3: Mobile App
1. Ouvrir app sur téléphone
2. Activer wake mode
3. Dire "hey gob"
4. Vérifier que les yeux s'activent
5. Parler commande
6. Vérifier réponse

---

## 🔋 Optimisations Performance

### Backend
- ✅ Charger modèle Whisper tiny au démarrage (1x)
- ✅ Utiliser beam_size=1 (plus rapide)
- ✅ Cache transcriptions récentes (éviter redondance)
- ✅ Limiter taille audio chunks (max 3 secondes)

### Frontend
- ✅ Envoyer seulement quand audio détecté (silence detection)
- ✅ Utiliser format audio compressé (webm au lieu de wav)
- ✅ Throttle envois (max 1 par seconde)
- ✅ Arrêter écoute quand app en background

---

## 📈 Métriques Cibles

| Métrique | Cible | Critique |
|----------|-------|----------|
| **Latence détection** | < 500ms | < 1000ms |
| **Précision** | > 90% | > 70% |
| **CPU Usage** | < 20% | < 40% |
| **Batterie mobile** | < 5%/h | < 10%/h |
| **Faux positifs** | < 5% | < 15% |
| **Faux négatifs** | < 10% | < 20% |

---

## 🚀 Avantages de cette Solution

1. ✅ **Compatible mobile et web** - Fonctionne partout
2. ✅ **Précision supérieure** - Whisper meilleur que Google
3. ✅ **Multi-langues** - Support 99+ langues
4. ✅ **Offline capable** - Pas besoin d'internet (si local)
5. ✅ **Personnalisable** - Wake word custom facilement
6. ✅ **Open source** - Pas de dépendance Google
7. ✅ **Réutilise Whisper** - Déjà installé pour STT

---

## ❓ Questions à Valider

### Question 1: Architecture Backend
**Option A:** Nouveau fichier `wake_word_detector.py` séparé ✅ RECOMMANDÉ
- Plus propre et modulaire
- Réutilise Whisper mais séparé de STT
- Facile à tester et maintenir

**Option B:** Intégrer dans `stt_engine.py` existant
- Moins de fichiers
- Mais mélange 2 responsabilités différentes

### Question 2: Communication Frontend-Backend
**Option A:** HTTP Polling (requêtes répétées) ✅ SIMPLE
- App envoie chunk toutes les 2 secondes
- Facile à implémenter
- Fonctionne partout

**Option B:** WebSocket (connexion continue)
- Plus efficace (pas de reconnexion)
- Plus complexe à implémenter
- Meilleure performance batterie

### Question 3: Serveur Unique ou Séparé
**Option A:** Intégrer dans `main.py` existant ✅ RECOMMANDÉ
- Un seul serveur (port 8000)
- Facile à gérer
- Partage même config

**Option B:** Serveur séparé (port 8001)
- Isolation complète
- Peut scaler indépendamment
- Plus complexe (2 serveurs)

---

## 📝 Prochaines Étapes

1. **Validation Architecture** ✋ EN ATTENTE
   - Lire ce document
   - Valider les choix (Question 1, 2, 3)
   - Approuver avant dev

2. **Développement Backend** (après validation)
   - Créer `wake_word_detector.py`
   - Ajouter routes dans `main.py`
   - Tests unitaires

3. **Développement Frontend** (après backend)
   - Créer `audioStreamService.ts`
   - Modifier `wakeWordService.ts`
   - Tests mobile

4. **Tests End-to-End**
   - Validation complète web + mobile
   - Optimisations performance

---

## 💬 Conclusion

Cette architecture permet d'avoir un **Wake Word qui fonctionne sur mobile ET web** en réutilisant Whisper déjà installé. C'est une solution:
- ✅ Professionnelle
- ✅ Performante
- ✅ Multi-plateforme
- ✅ Open source
- ✅ Facile à maintenir

**Tu es d'accord avec cette architecture ? On commence le dev ?** 🚀
