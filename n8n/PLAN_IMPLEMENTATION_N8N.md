# 📋 Plan d'Implémentation n8n - À VALIDER AVANT EXÉCUTION

**Date:** 16 février 2026  
**Status:** 🔴 EN ATTENTE DE VALIDATION

---

## 📊 État Actuel (Ce qui existe déjà)

### ✅ Backend Python (PRÊT)
```python
# backend/integrations/n8n_client.py
- Client async fonctionnel
- Envoie ActionJSON vers n8n webhook
- Validation automatique avant envoi
- Gestion timeout et erreurs
- Configuration via .env (ENABLE_N8N_INTEGRATION, N8N_WEBHOOK_URL)
```

**Conclusion:** Backend est 100% prêt, aucune modification nécessaire.

### ⚠️ Workflows n8n (INCOMPLETS)
```
n8n/
├── wf_action_router.json      ✅ Structure OK, ❌ Nodes pas connectés, ❌ Code TODO
├── wf_control_iot.json        ✅ Structure OK, ❌ Nodes pas connectés, ❌ Code TODO  
├── wf_send_email.json         ✅ Existe, ❌ À compléter
├── wf_set_reminder.json       ✅ Existe, ❌ À compléter
├── wf_web_search.json         ✅ Existe, ❌ À compléter
├── wf_log_event.json          ✅ Existe, ❌ À compléter
└── wf_notification.json       ✅ Existe, ❌ À compléter
```

**Problèmes:**
1. Nodes ne sont PAS connectés entre eux (connections: {})
2. Code JavaScript contient des TODO
3. Configuration MQTT/SMTP manquante
4. Pas de validation HMAC implémentée
5. Callback vers backend manquant

### ❓ Installation n8n
- ✅ Installé sur Docker
- ❓ Version exacte? (besoin pour compatibilité workflows)
- ❓ Port 5678 accessible?
- ❓ Données persistées? (volume Docker monté?)

---

## 🎯 Objectif Final

Pipeline complet fonctionnel:

```
User: "Turn on the lamp"
   ↓
Frontend → Backend Python
   ↓
Backend: Classification → ACTION détectée
   ↓
Backend: Créer ActionJSON → PENDING_CONFIRMATION
   ↓
Backend: User confirm "yes" → CONFIRMED
   ↓
Backend: N8NClient.send_action() → POST http://localhost:5678/webhook/action
   ↓
n8n: wf_action_router reçoit ActionJSON
   ↓
n8n: Valide signature HMAC ✅
   ↓
n8n: Route vers wf_control_iot (intent = "control_iot")
   ↓
n8n: wf_control_iot extrait device_id, command
   ↓
n8n: Publish MQTT → Topic: gob/actions/lamp_001/command
   ↓
MQTT Broker (Mosquitto) → Téléphone reçoit commande 📱
   ↓
n8n: Callback Backend → POST http://localhost:8000/action/status/act_123
   ↓
Backend: Transition EXECUTING → COMPLETED ✅
   ↓
ActionPanel Frontend: Affiche COMPLETED avec icône verte 🟢
```

---

## 📝 Plan d'Action Détaillé (7 Étapes)

### ✅ ÉTAPE 1: Vérification Installation n8n (5 min)

**Ce que je vais faire:**
1. Vérifier Docker `docker ps | Select-String "n8n"`
2. Vérifier accès `http://localhost:5678`
3. Obtenir version n8n affichée dans UI
4. Vérifier si données persistées (volume monté)

**Ce que VOUS devez faire:**
- Me donner la version n8n dans l'UI (coin bas droite)
- Confirmer que port 5678 est accessible
- Me dire si vous avez un volume Docker monté (données sauvegardées)

**Commande Docker attendue:**
```powershell
docker run -d --name n8n `
  -p 5678:5678 `
  -v C:\Users\lapte\.n8n:/home/node/.n8n `
  n8nio/n8n
```

---

### 🔨 ÉTAPE 2: Créer Workflow Routeur Principal (30 min)

**Fichier:** `wf_action_router.json` (COMPLET)

**Ce que je vais faire:**
1. ✅ Webhook node: `/webhook/action` (POST)
2. ✅ Function node "Validate HMAC Signature":
   ```javascript
   const crypto = require('crypto');
   const secret = 'changeme-secret-key-production-MUST-BE-SECURE'; // Même que backend
   
   const actionJson = $input.item.json;
   const receivedSignature = actionJson.signature;
   
   // Extraire signature et recalculer
   const { signature, signed_at, ...payload } = actionJson;
   const calculatedSig = crypto
     .createHmac('sha256', secret)
     .update(JSON.stringify(payload))
     .digest('hex');
   
   if (receivedSignature !== calculatedSig) {
     throw new Error('❌ Invalid HMAC signature');
   }
   
   return { json: actionJson };
   ```

3. ✅ Switch node "Route by Intent":
   ```
   Conditions:
   - intent == "control_iot" → Output 0
   - intent == "send_email" → Output 1
   - intent == "set_reminder" → Output 2
   - intent == "web_search" → Output 3
   ```

4. ✅ HTTP Request nodes (pour appeler workflows):
   - Output 0 → POST `http://localhost:5678/webhook/control_iot`
   - Output 1 → POST `http://localhost:5678/webhook/send_email`
   - etc.

5. ✅ Merge node: Rassembler résultats
6. ✅ HTTP Request node "Callback Backend":
   ```
   URL: http://localhost:8000/action/status/{{ $json.action_id }}
   Method: PATCH
   Body:
   {
     "state": "EXECUTING",
     "n8n_execution_id": "{{ $execution.id }}",
     "updated_at": "{{ $now.toISO() }}"
   }
   ```

7. ✅ CONNECTER tous les nodes (connections)

**Résultat attendu:**
- Workflow importable dans n8n
- Test: `curl -X POST http://localhost:5678/webhook/action -d @test_action.json`

---

### 🔨 ÉTAPE 3: Créer Workflow Control IoT (45 min)

**Fichier:** `wf_control_iot.json` (COMPLET)

**Ce que je vais faire:**
1. ✅ Webhook node: `/webhook/control_iot` (POST)
2. ✅ Function node "Extract Device Command":
   ```javascript
   const action = $input.item.json;
   const payload = action.payload;
   
   return {
     json: {
       action_id: action.action_id,
       device_id: payload.device_id,
       device_type: payload.device_type,
       command: payload.action,  // turn_on, turn_off, etc.
       location: payload.location,
       mqtt_topic: `gob/actions/${payload.device_id}/command`,
       mqtt_payload: {
         device_id: payload.device_id,
         command: payload.action,
         timestamp: Math.floor(Date.now() / 1000),
         action_id: action.action_id
       }
     }
   };
   ```

3. ✅ MQTT node "Publish Command":
   ```
   Broker: localhost:1883
   Topic: {{ $json.mqtt_topic }}
   Message: {{ JSON.stringify($json.mqtt_payload) }}
   QoS: 1
   ```

4. ✅ Wait node: 5 secondes (attente confirmation device)

5. ✅ Function node "Build Callback":
   ```javascript
   return {
     json: {
       action_id: $input.item.json.action_id,
       state: "COMPLETED",
       result: {
         device_id: $input.item.json.device_id,
         command: $input.item.json.command,
         status: "success",
         executed_at: new Date().toISOString()
       }
     }
   };
   ```

6. ✅ HTTP Request node "Callback Backend":
   ```
   URL: http://localhost:8000/action/status/{{ $json.action_id }}
   Method: PATCH
   Body: {{ $json }}
   ```

7. ✅ CONNECTER tous les nodes

**Résultat attendu:**
- Workflow complet IoT
- Publie MQTT vers device
- Callback backend avec résultat

---

### 🔨 ÉTAPE 4: Lancer Broker MQTT Mosquitto (5 min)

**Ce que je vais faire:**

Créer commande Docker pour Mosquitto:
```powershell
docker run -d --name mqtt-broker `
  -p 1883:1883 `
  -p 9001:9001 `
  eclipse-mosquitto:latest
```

**Configuration basique Mosquitto:**
```
# mosquitto.conf (si nécessaire)
listener 1883
allow_anonymous true
```

**Test:**
```powershell
# Test publish
docker exec -it mqtt-broker mosquitto_pub -h localhost -t test -m "hello"

# Test subscribe
docker exec -it mqtt-broker mosquitto_sub -h localhost -t test
```

---

### 🔨 ÉTAPE 5: Configuration Backend .env (2 min)

**Fichier:** `backend/.env`

**Ce que je vais ajouter/modifier:**
```env
# ==================== N8N ====================
ENABLE_N8N_INTEGRATION=true
N8N_WEBHOOK_URL=http://localhost:5678/webhook/action
N8N_TIMEOUT=60

# ==================== MQTT ====================
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC_COMMAND_OUT=gob/actions/+/command
MQTT_TOPIC_STATUS_IN=gob/actions/+/status
MQTT_QOS=1
```

**Vérification:**
```powershell
cd backend
python -c "from config import Config; print(f'N8N enabled: {Config.ENABLE_N8N_INTEGRATION}'); print(f'Webhook: {Config.N8N_WEBHOOK_URL}')"
```

---

### 🔨 ÉTAPE 6: Import Workflows dans n8n UI (10 min)

**Ce que VOUS devez faire:**
1. Ouvrir `http://localhost:5678`
2. Cliquer "Workflows" → "Import from File"
3. Importer dans l'ordre:
   - `wf_action_router.json` (routeur d'abord)
   - `wf_control_iot.json`
   - (optionnel: autres workflows)
4. Pour chaque workflow:
   - Vérifier nodes connectés ✅
   - Cliquer "Save" (ne PAS activer tout de suite)
   - Noter l'URL webhook générée

**Ce que je vais faire:**
- Créer les fichiers JSON complets prêts à importer
- Fournir instructions détaillées d'import

---

### 🔨 ÉTAPE 7: Test End-to-End Complet (15 min)

**Scénario de test:**

1. **Lancer tous les services:**
   ```powershell
   # Terminal 1: Backend
   cd backend
   .\venv\Scripts\Activate.ps1
   uvicorn main:app --reload --port 8000
   
   # Terminal 2: Frontend
   cd agent-ui
   npm run dev
   
   # Vérifier Docker: Piper TTS, n8n, MQTT broker
   docker ps
   ```

2. **Configuration téléphone MQTT:**
   - App: MQTT Dash (ou similar)
   - Broker: `192.168.X.X:1883` (votre IP PC)
   - Subscribe à: `gob/actions/+/command`

3. **Test vocal:**
   ```
   User (Frontend): "Turn on the lamp in the living room"
   
   Expected flow:
   ✅ STT transcribe
   ✅ Classification → ACTION
   ✅ Backend create ActionJSON → PENDING
   ✅ User confirm "yes" → CONFIRMED
   ✅ Backend send to n8n
   ✅ n8n validate HMAC
   ✅ n8n route to wf_control_iot
   ✅ n8n publish MQTT → téléphone reçoit! 📱
   ✅ n8n callback backend
   ✅ Backend → COMPLETED
   ✅ ActionPanel affiche green ✅
   ```

4. **Vérifications:**
   - Backend logs: `📤 Sending action to n8n`
   - n8n logs: Execution success
   - MQTT téléphone: Message reçu
   - Frontend ActionPanel: État COMPLETED

---

## 🔍 Ce que j'ai besoin de VOUS

### Questions AVANT de commencer:

1. **Version n8n:**
   - Quelle version est installée? (voir dans UI coin bas droite)
   - Format attendu: `n8n v1.x.x` ou `n8n v0.x.x`

2. **Docker n8n:**
   - Commande Docker exacte utilisée?
   - Y a-t-il un volume monté? (`-v ...`)
   - Est-ce que les workflows sont sauvegardés entre restarts?

3. **Priorités:**
   - Voulez-vous TOUS les workflows (email, reminder, etc.) ou SEULEMENT control_iot?
   - Réponse attendue: "Seulement control_iot pour la démo" OU "Tous les workflows"

4. **MQTT:**
   - Avez-vous déjà un broker MQTT running?
   - Nom de votre app mobile MQTT?
   - IP de votre PC sur le réseau local? (pour config téléphone)

5. **Timeline:**
   - Combien de temps avant la soutenance?
   - Préférez-vous: aller vite (workflow minimal) ou complet (tous workflows)?

---

## 📊 Estimation Temps Total

| Étape | Temps | Difficulté |
|-------|-------|------------|
| 1. Vérif n8n | 5 min | 🟢 Facile |
| 2. Workflow routeur | 30 min | 🟡 Moyen |
| 3. Workflow IoT | 45 min | 🟡 Moyen |
| 4. MQTT broker | 5 min | 🟢 Facile |
| 5. Config .env | 2 min | 🟢 Facile |
| 6. Import UI | 10 min | 🟢 Facile |
| 7. Test end-to-end | 15 min | 🟠 Complexe |
| **TOTAL** | **~2h** | 🟡 |

**Note:** Si problèmes durant tests, ajouter +30min debug.

---

## 🚨 Risques Identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Version n8n incompatible | 🟡 Moyen | 🔴 Critique | Vérifier avant, adapter JSON |
| MQTT non installé | 🟢 Faible | 🟠 Moyen | Docker Mosquitto simple |
| Backend .env manquant | 🟢 Faible | 🟠 Moyen | Template .env fourni |
| Signature HMAC mismatch | 🟡 Moyen | 🟠 Moyen | Vérifier SECRET_KEY identique |
| Téléphone pas sur même WiFi | 🟡 Moyen | 🟠 Moyen | Utiliser IP locale PC |

---

## ✅ Critères de Succès

Pour valider que l'implémentation est réussie:

1. ✅ Workflow `wf_action_router` importé et fonctionne
2. ✅ Workflow `wf_control_iot` importé et fonctionne
3. ✅ Backend envoie ActionJSON vers n8n sans erreur
4. ✅ n8n valide signature HMAC correctement
5. ✅ n8n publie MQTT vers broker
6. ✅ Téléphone reçoit message MQTT
7. ✅ n8n callback backend avec résultat
8. ✅ ActionPanel affiche COMPLETED
9. ✅ Tout le pipeline en <5 secondes
10. ✅ Logs clairs à chaque étape

---

## 🎯 Prochaine Étape

**À FAIRE MAINTENANT:**
1. Lire ce document en entier ✅
2. Répondre aux 5 questions dans section "Ce que j'ai besoin de VOUS"
3. Me dire: "OK je valide, commence étape 1" OU "Attends, j'ai des questions sur..."

**NE PAS COMMENCER** avant votre validation!

---

**Créé le:** 16 février 2026  
**Par:** GitHub Copilot  
**Pour:** Montassar - Projet PCD Agent Intelligent
