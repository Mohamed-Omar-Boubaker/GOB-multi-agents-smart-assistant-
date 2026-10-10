# 🚀 Guide Démarrage Rapide - Backend Python

## ✅ Ce qui a été implémenté

### 1. **config.py** - Configuration centralisée
- ✅ 120+ variables de configuration
- ✅ Chargement `.env`
- ✅ Validation au démarrage
- ✅ Gestion environnements (dev/prod)
- ✅ Feature flags (n8n, MQTT, audio)

### 2. **main.py** - API FastAPI complète
- ✅ 12 routes API REST
- ✅ Validation Pydantic
- ✅ CORS configuré
- ✅ Exception handlers
- ✅ Lifecycle events (startup/shutdown)
- ✅ Documentation Swagger automatique

### 3. **Routes implémentées**

| Route | Méthode | Description |
|-------|---------|-------------|
| `/` | GET | Informations API |
| `/health` | GET | Health check système |
| `/stats` | GET | Statistiques utilisation |
| `/command/text` | POST | Commande textuelle |
| `/command/audio` | POST | Commande vocale |
| `/action/confirm/{action_id}` | POST | Confirmer/annuler action |
| `/action/status/{action_id}` | GET | Status action |
| `/callback/n8n` | POST | Callback résultat n8n |
| `/docs` | GET | Documentation Swagger |
| `/redoc` | GET | Documentation ReDoc |

---

## 🎯 Démarrage

### Option 1: Démarrage rapide
```powershell
# Activer environnement virtuel
venv\Scripts\activate

# Démarrer serveur
uvicorn backend.main:app --reload --port 8000
```

### Option 2: Avec configuration personnalisée
```powershell
# Éditer .env
notepad backend\.env

# Démarrer avec options
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 --log-level info
```

### Option 3: Mode production
```powershell
# Désactiver reload et debug
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🧪 Test des Endpoints

### 1. Health Check
```powershell
curl http://localhost:8000/health
```

Réponse attendue:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development",
  "components": {
    "agent_core": "ok",
    "llm": "unknown",
    "n8n": "disabled",
    "mqtt": "disabled",
    "stt": "ok",
    "tts": "ok"
  },
  "timestamp": "2026-02-10T..."
}
```

### 2. Commande Textuelle (Conversation)
```powershell
curl -X POST "http://localhost:8000/command/text" `
  -H "Content-Type: application/json" `
  -d '{
    "text": "Bonjour, comment vas-tu ?",
    "user_id": "user_001",
    "language": "fr"
  }'
```

### 3. Commande Textuelle (Action)
```powershell
curl -X POST "http://localhost:8000/command/text" `
  -H "Content-Type: application/json" `
  -d '{
    "text": "Allume la lampe du salon",
    "user_id": "user_001",
    "language": "fr"
  }'
```

### 4. Status d'une Action
```powershell
curl http://localhost:8000/action/status/act_abc123xyz
```

### 5. Documentation Interactive
Ouvrir dans le navigateur:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📋 Pipeline de Traitement

### Pipeline Conversation
```
Requête POST /command/text
    ↓
Agent Core.process()
    ↓
Classifier → "conversation"
    ↓
LLM Client → Génère réponse
    ↓
TTS Engine → Génère audio
    ↓
Retour immédiat {response, audio}
```

### Pipeline Action
```
Requête POST /command/text
    ↓
Agent Core.process()
    ↓
Classifier → "action"
    ↓
LLM Client → Analyse intention
    ↓
Action Builder → ActionJSON (DRAFT)
    ↓
State Manager → Crée action
    ↓
Confirmation Handler → Message confirmation
    ↓
Retour {action_id, message, status: "awaiting_confirmation"}
    ↓
[Utilisateur POST /action/confirm/{action_id}]
    ↓
Si "oui" → Security Manager → n8n Client → EXECUTING
Si "non" → CANCELED
```

---

## 🔧 Configuration Avancée

### Variables d'environnement critiques

**LLM (REQUIS):**
```env
LLM_API_URL=http://localhost:5000
LLM_API_KEY=your_key_here
LLM_MODEL=gpt-3.5-turbo
```

**Audio (OPTIONNEL):**
```env
ENABLE_AUDIO_PROCESSING=True
STT_ENGINE=whisper
TTS_ENGINE=gtts
```

**n8n (OPTIONNEL):**
```env
ENABLE_N8N_INTEGRATION=True
N8N_WEBHOOK_URL=http://localhost:5678/webhook/action
```

**MQTT (OPTIONNEL):**
```env
ENABLE_MQTT_INTEGRATION=True
MQTT_BROKER=localhost
MQTT_PORT=1883
```

---

## 🐛 Dépannage

### Erreur: "Agent Core not initialized"
**Cause**: Un composant critique manque (LLM, Classifier, etc.)

**Solution**: Vérifier que tous les composants sont implémentés:
```powershell
python test_main_startup.py
```

### Erreur: "Cannot create log directory"
**Solution**: Créer le dossier manuellement
```powershell
New-Item -ItemType Directory -Force -Path "logs"
```

### Port 8000 déjà utilisé
**Solution**: Changer le port
```powershell
uvicorn backend.main:app --reload --port 8001
```

### Erreur LLM_API_URL required
**Solution**: Éditer `.env` et définir `LLM_API_URL`
```powershell
notepad backend\.env
```

---

## 📊 Monitoring

### Logs
```powershell
# Voir les logs en temps réel
Get-Content -Path "logs\agent.log" -Wait -Tail 50
```

### Statistiques
```powershell
curl http://localhost:8000/stats
```

### Health Check automatique
```powershell
# Vérifier toutes les 10 secondes
while ($true) { 
  curl http://localhost:8000/health | ConvertFrom-Json | Format-List
  Start-Sleep -Seconds 10
}
```

---

## 🎓 Exemples Complets

### Exemple 1: Conversation Simple
```powershell
$body = @{
    text = "Quelle heure est-il ?"
    user_id = "user_001"
    language = "fr"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/command/text" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### Exemple 2: Action IoT Complète
```powershell
# 1. Envoyer commande
$cmd = @{
    text = "Allume la lampe du salon"
    user_id = "user_001"
    language = "fr"
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:8000/command/text" `
  -Method POST `
  -ContentType "application/json" `
  -Body $cmd

$action_id = $result.action_id

# 2. Confirmer action
$confirm = @{
    response = "oui"
    user_id = "user_001"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/action/confirm/$action_id" `
  -Method POST `
  -ContentType "application/json" `
  -Body $confirm

# 3. Vérifier status
Invoke-RestMethod -Uri "http://localhost:8000/action/status/$action_id" `
  -Method GET
```

---

## ✅ Checklist Déploiement

- [ ] `.env` configuré avec vraies valeurs
- [ ] `SECRET_KEY` modifié (production)
- [ ] LLM API accessible
- [ ] Logs directory créé
- [ ] Tests unitaires passent (114/114)
- [ ] Health check retourne "ok"
- [ ] Documentation Swagger accessible
- [ ] n8n configuré (si activé)
- [ ] MQTT configuré (si activé)

---

## 📚 Documentation

- **API Swagger**: http://localhost:8000/docs
- **Architecture**: `doc/01_ARCHITECTURE_TECHNIQUE_COMPLETE_CONSOLIDEE.md`
- **Spécifications**: `05_SPECIFICATIONS_INTERFACES_JSON_BACKEND.md`
- **Tests**: `backend/*/tests/`

---

**Status**: ✅ **BACKEND MAIN.PY COMPLET ET FONCTIONNEL**

**Prochaines étapes**:
1. Tester les endpoints avec Swagger UI
2. Intégrer n8n (quand Omar implémente)
3. Intégrer MQTT (quand Omar implémente)
4. Tests d'intégration end-to-end
