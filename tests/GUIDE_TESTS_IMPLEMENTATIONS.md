# 📋 Guide de Tests - Implémentations Backend

## ✅ Conformité aux Spécifications

Date : 11 février 2026  
**Status** : ✅ 100% CONFORME

---

## 📊 Résumé des Corrections

### 1. **validators.py** - ✅ COMPLET (10 validateurs)

Ajouts effectués :
- ✅ `validate_classification_input()` - Valider Flux 0 INPUT
- ✅ `validate_classification_output()` - Valider Flux 0 OUTPUT
- ✅ `validate_confirmation_request()` - Valider demande confirmation
- ✅ `validate_confirmation_response()` - Valider réponse confirmation
- ✅ `validate_n8n_callback()` - Valider callback n8n
- ✅ `_validate_control_iot_payload()` - Valider payload control_iot
- ✅ `_validate_send_email_payload()` - Valider payload send_email
- ✅ `validate_action_json_complete()` - Validation complète ActionJSON

**Référence** : [05_SPECIFICATIONS_INTERFACES_JSON_BACKEND.md](../05_SPECIFICATIONS_INTERFACES_JSON_BACKEND.md)

### 2. **mqtt_client.py** - ✅ CONFORME

Interface JSON complète :
- ✅ Méthode `execute(input_data: dict) -> dict`
- ✅ INPUT JSON avec "operation": "publish"/"subscribe"
- ✅ OUTPUT JSON avec status, message_id, published_at
- ✅ Callbacks pour messages reçus

**Référence** : [05_SPECIFICATIONS Section MQTT Client](../05_SPECIFICATIONS_INTERFACES_JSON_BACKEND.md#L1464)

### 3. **n8n_client.py** - ✅ CONFORME

Déjà conforme aux specs :
- ✅ Méthode `send_action()` async
- ✅ Gestion timeout/erreurs
- ✅ Mock mode quand désactivé
- ✅ Logging complet

---

## 🧪 Exemples de Tests

### Test 1 : MQTT Client - Publish

```python
from integrations.mqtt_client import MQTTClient

# Créer client (mock si MQTT désactivé)
mqtt = MQTTClient()

# INPUT JSON selon specs
input_publish = {
    "operation": "publish",
    "topic": "esp32/command/lamp_001",
    "message": {
        "device_id": "lamp_001",
        "action": "turn_on",
        "timestamp": "2026-02-11T10:30:00Z"
    },
    "qos": 1,
    "retain": False
}

# Exécuter
result = mqtt.execute(input_publish)

# OUTPUT attendu
print(result)
# {
#   "status": "published",
#   "topic": "esp32/command/lamp_001",
#   "message_id": "mqtt_abc123",
#   "published_at": "2026-02-11T10:30:00Z"
# }
```

### Test 2 : MQTT Client - Subscribe

```python
# INPUT JSON subscribe
input_subscribe = {
    "operation": "subscribe",
    "topic": "esp32/status/#",  # Wildcard pour tous statuts
    "qos": 1
}

# Exécuter
result = mqtt.execute(input_subscribe)

# OUTPUT attendu
print(result)
# {
#   "status": "subscribed",
#   "topic": "esp32/status/#",
#   "qos": 1,
#   "subscribed_at": "2026-02-11T10:30:01Z"
# }

# Définir callback pour messages reçus
def on_message(message_data):
    print(f"Message reçu: {message_data['topic']}")
    print(f"Payload: {message_data['message']}")

mqtt.set_callback(on_message)
```

### Test 3 : Validators - Classification

```python
from utils.validators import JSONValidator
from utils.exceptions import ValidationError

# Test classification INPUT
classification_input = {
    "request_id": "req_001",
    "text": "Allume la lampe du salon",
    "user_id": "user_test",
    "source": "text",
    "language": "fr"
}

try:
    JSONValidator.validate_classification_input(classification_input)
    print("✅ Classification input valide")
except ValidationError as e:
    print(f"❌ Erreur: {e}")

# Test classification OUTPUT
classification_output = {
    "request_id": "req_001",
    "classification": "action",
    "confidence": 0.92
}

try:
    JSONValidator.validate_classification_output(classification_output)
    print("✅ Classification output valide")
except ValidationError as e:
    print(f"❌ Erreur: {e}")
```

### Test 4 : Validators - ActionJSON Complète

```python
# ActionJSON control_iot
action_json = {
    "action_id": "act_123",
    "intent": "control_iot",
    "confirmed": True,
    "payload": {
        "device_id": "lamp_salon",
        "action": "turn_on",
        "location": "salon"
    },
    "context": {
        "user_id": "user_001",
        "language": "fr"
    }
}

try:
    # Validation complète avec payload spécifique
    JSONValidator.validate_action_json_complete(action_json)
    print("✅ ActionJSON complète valide")
except ValidationError as e:
    print(f"❌ Erreur: {e}")
```

### Test 5 : Validators - Confirmation

```python
# Demande de confirmation
confirmation_request = {
    "action_id": "act_123",
    "confirmation_text": "Voulez-vous vraiment allumer la lampe du salon ?",
    "action_summary": {
        "device": "lampe",
        "action": "allumer",
        "location": "salon"
    }
}

try:
    JSONValidator.validate_confirmation_request(confirmation_request)
    print("✅ Confirmation request valide")
except ValidationError as e:
    print(f"❌ Erreur: {e}")

# Réponse de confirmation
confirmation_response = {
    "action_id": "act_123",
    "user_response": "oui",
    "parsed_response": {
        "intent": "confirm",
        "confidence": 0.95
    }
}

try:
    JSONValidator.validate_confirmation_response(confirmation_response)
    print("✅ Confirmation response valide")
except ValidationError as e:
    print(f"❌ Erreur: {e}")
```

### Test 6 : n8n Client - Send Action

```python
from integrations.n8n_client import N8NClient

# Créer client
n8n = N8NClient()

# ActionJSON signée et confirmée
action_json = {
    "action_id": "act_123",
    "user_id": "user_001",
    "intent": "control_iot",
    "confirmed": True,
    "state": "CONFIRMED",
    "payload": {
        "device_id": "lamp_001",
        "action": "turn_on"
    },
    "security": {
        "signature": "a3f5d9b2c1e4..."
    }
}

# Envoyer vers n8n (async)
result = await n8n.send_action(action_json)

# OUTPUT attendu
print(result)
# {
#   "action_id": "act_123",
#   "status": "sent",
#   "n8n_response": {
#       "execution_id": "n8n_exec_001",
#       "status": "accepted"
#   },
#   "sent_at": "2026-02-11T10:30:19Z",
#   "response_time_ms": 345
# }
```

---

## 🧪 Script de Test Automatisé

Exécutez les tests de conformité :

```bash
# Depuis la racine du projet
python tests/test_implementations_compliance.py
```

**Résultat attendu** :
```
╔====================================================================╗
║          TESTS DE CONFORMITÉ AUX SPÉCIFICATIONS                    ║
╚====================================================================╝

🧪 TESTS VALIDATORS
==================================================
✅ TOUS LES TESTS VALIDATORS PASSENT !

🧪 TESTS MQTT CLIENT INTERFACE
==================================================
✅ MQTT CLIENT INTERFACE CONFORME AUX SPECS !

======================================================================
📋 RÉSUMÉ GLOBAL
======================================================================

1. Validators:     ✅ CONFORME
2. MQTT Client:    ✅ CONFORME

🎉 TOUTES LES IMPLÉMENTATIONS SONT CONFORMES AUX SPÉCIFICATIONS !
```

---

## 📝 Tests d'Intégration Recommandés

### 1. Test Backend Complet avec MQTT

```python
# Test flow complet : Commande → MQTT publish
import asyncio
from integrations.mqtt_client import MQTTClient

async def test_backend_mqtt_flow():
    # 1. Créer client MQTT
    mqtt = MQTTClient()
    
    # 2. Publier commande IoT
    command_input = {
        "operation": "publish",
        "topic": "esp32/command/lamp_salon",
        "message": {
            "device_id": "lamp_salon",
            "action": "turn_on",
            "value": None
        },
        "qos": 1
    }
    
    result = mqtt.execute(command_input)
    print(f"✅ Commande publiée: {result['message_id']}")
    
    # 3. S'abonner aux retours ESP32
    status_input = {
        "operation": "subscribe",
        "topic": "esp32/status/#",
        "qos": 1
    }
    
    mqtt.execute(status_input)
    print("✅ Abonné aux statuts ESP32")
    
    # 4. Définir callback
    def on_esp32_status(message):
        print(f"📡 Statut reçu: {message['topic']}")
        print(f"   Données: {message['message']}")
    
    mqtt.set_callback(on_esp32_status)
    
    # 5. Attendre messages (pour test)
    await asyncio.sleep(5)

# Exécuter
asyncio.run(test_backend_mqtt_flow())
```

### 2. Test Validation dans Pipeline

```python
from utils.validators import JSONValidator
from utils.exceptions import ValidationError

def process_command_with_validation(user_text, user_id):
    """Pipeline avec validation à chaque étape"""
    
    # 1. Créer input classification
    classification_input = {
        "request_id": generate_request_id(),
        "text": user_text,
        "user_id": user_id,
        "source": "text",
        "language": "fr"
    }
    
    # Valider INPUT
    try:
        JSONValidator.validate_classification_input(classification_input)
    except ValidationError as e:
        return {"error": f"Invalid input: {e}"}
    
    # 2. Classifier (simulé)
    classification_output = {
        "request_id": classification_input["request_id"],
        "classification": "action",
        "confidence": 0.92
    }
    
    # Valider OUTPUT
    try:
        JSONValidator.validate_classification_output(classification_output)
    except ValidationError as e:
        return {"error": f"Invalid classification: {e}"}
    
    # 3. Si action → créer ActionJSON
    if classification_output["classification"] == "action":
        action_json = build_action_json(user_text, user_id)
        
        # Valider ActionJSON complète
        try:
            JSONValidator.validate_action_json_complete(action_json)
        except ValidationError as e:
            return {"error": f"Invalid ActionJSON: {e}"}
        
        return {"status": "success", "action": action_json}
    
    return {"status": "conversation"}
```

---

## 🔧 Configuration Requise

### packages Python installés

```bash
# Validators
pip install jsonschema

# MQTT Client  
pip install paho-mqtt

# n8n Client
pip install httpx
```

### Variables d'environnement

```env
# MQTT
ENABLE_MQTT_INTEGRATION=false  # true quand broker prêt
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# n8n
ENABLE_N8N_INTEGRATION=false  # true quand n8n installé
N8N_WEBHOOK_URL=http://localhost:5678/webhook/action
N8N_TIMEOUT=60
```

---

## 📚 Références

1. **Spécifications** : [05_SPECIFICATIONS_INTERFACES_JSON_BACKEND.md](../05_SPECIFICATIONS_INTERFACES_JSON_BACKEND.md)
2. **Architecture** : [doc/01_ARCHITECTURE_TECHNIQUE_COMPLETE_CONSOLIDEE.md](../doc/01_ARCHITECTURE_TECHNIQUE_COMPLETE_CONSOLIDEE.md)
3. **Mapping** : [doc/04_MAPPING_SEQUENTIEL_MODULE_PAR_MODULE.md](../doc/04_MAPPING_SEQUENTIEL_MODULE_PAR_MODULE.md)

---

## ✅ Checklist Validation

- [x] Validators - 10 validateurs implémentés
- [x] MQTT Client - Interface JSON conforme
- [x] n8n Client - Déjà conforme
- [x] Tests automatisés - 100% passent
- [x] Documentation - Guide complet
- [x] Exemples - 6 exemples de tests

**Status final** : ✅ **PRÊT POUR TESTS D'INTÉGRATION**

---

## 🚀 Prochaines Étapes

1. **Installer broker MQTT** (Mosquitto)
   ```bash
   # Windows
   choco install mosquitto
   # Puis activer ENABLE_MQTT_INTEGRATION=true
   ```

2. **Installer n8n**
   ```bash
   npm install -g n8n
   n8n start
   # Puis activer ENABLE_N8N_INTEGRATION=true
   ```

3. **Tests d'intégration avec ESP32**
   - Flasher ESP32 avec code MQTT
   - Tester communication bidirectionnelle
   - Valider formats JSON

4. **Tests end-to-end**
   - Commande vocale → Backend → n8n → ESP32
   - Retour ESP32 → Backend → Utilisateur
