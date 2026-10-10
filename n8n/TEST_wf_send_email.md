# 📧 Test Workflow - wf_send_email

## 1. Configuration Gmail SMTP

### Variables d'environnement à configurer dans n8n

Dans n8n, allez dans **Settings > Variables** et ajoutez :

```
GMAIL_USER = votre-email@gmail.com
GMAIL_APP_PASSWORD = votre-mot-de-passe-application
```

### Comment obtenir un mot de passe d'application Gmail

1. **Activer la validation en 2 étapes** sur votre compte Google
2. Aller sur : https://myaccount.google.com/apppasswords
3. Créer un nouveau mot de passe d'application pour "n8n Email"
4. Copier le mot de passe généré (16 caractères sans espaces)
5. Utiliser ce mot de passe dans `GMAIL_APP_PASSWORD`

---

## 2. Test du Workflow SEUL (Sans Backend)

### Étape 1 : Importer le workflow

1. Ouvrir n8n : `http://localhost:5678`
2. Créer un nouveau workflow
3. Menu **...** > **Import from File**
4. Sélectionner : `wf_send_email.json`

### Étape 2 : Tester avec cURL

Ouvrez PowerShell et exécutez :

```powershell
# Test 1 - Email simple avec ActionJSON complet
curl.exe -X POST http://localhost:5678/webhook/send_email `
  -H "Content-Type: application/json" `
  -d '{
    "action_id": "act_test_001",
    "intent": "send_email",
    "state": "CONFIRMED",
    "payload": {
      "recipient": "John Doe",
      "recipient_email": "votre-email-test@gmail.com",
      "subject": "Test n8n Email Workflow",
      "body": "Ceci est un email de test envoyé depuis le workflow n8n.\n\nSi vous recevez ce message, le workflow fonctionne correctement !",
      "body_format": "plain",
      "cc": [],
      "bcc": [],
      "priority": "normal"
    },
    "context": {
      "user_id": "user_test",
      "language": "fr",
      "channel": "test"
    },
    "metadata": {
      "request_id": "req_test_001"
    },
    "timestamps": {
      "created_at": "2026-01-20T10:00:00Z"
    }
  }'
```

### Étape 3 : Vérifier les résultats

**✅ Succès attendu :**
```json
{
  "action_id": "act_test_001",
  "state": "SUCCESS",
  "result": {
    "status": "sent",
    "recipient": "John Doe",
    "recipient_email": "votre-email-test@gmail.com",
    "subject": "Test n8n Email Workflow",
    "sent_at": "2026-01-20T10:00:05Z"
  }
}
```

**❌ Erreurs possibles :**

| Erreur | Cause | Solution |
|--------|-------|----------|
| `Invalid credentials` | Mot de passe application incorrect | Regénérer mot de passe app Gmail |
| `Missing recipient_email` | Payload invalide | Vérifier structure ActionJSON |
| `Invalid email format` | Email malformé | Corriger format email |
| `Connection timeout` | Firewall/réseau | Vérifier port 587 ouvert |

---

## 3. Test avec le Backend Python

### Étape 1 : Vérifier que le backend tourne

```powershell
# Backend doit être actif sur port 8000
curl http://localhost:8000/health
```

### Étape 2 : Tester l'envoi depuis le backend

Le backend doit envoyer une ActionJSON au routeur :

```python
# Dans backend Python - Test manuel
import requests

action_json = {
    "action_id": "act_backend_001",
    "intent": "send_email",
    "state": "CONFIRMED",
    "payload": {
        "recipient": "Jean Martin",
        "recipient_email": "jean@example.com",
        "subject": "Test Backend → n8n",
        "body": "Email envoyé depuis le backend Python via n8n",
        "body_format": "plain"
    },
    "context": {"user_id": "user_42"},
    "metadata": {"request_id": "req_backend_001"},
    "timestamps": {"created_at": "2026-01-20T10:00:00Z"}
}

# Envoyer au routeur
response = requests.post(
    "http://localhost:5678/webhook/action",  # wf_action_router
    json=action_json
)

print(response.json())
```

### Étape 3 : Flux complet à tester

```
Backend Python (ActionJSON)
    ↓ POST /webhook/action
wf_action_router (Route par intent: send_email)
    ↓ POST /webhook/send_email
wf_send_email (Extraction → Validation → Envoi Gmail)
    ↓ POST /callback/n8n
Backend Python (Résultat SUCCESS/FAILED)
```

---

## 4. Données de Test (Exemples)

### Test 1 - Email simple

```json
{
  "action_id": "act_001",
  "intent": "send_email",
  "state": "CONFIRMED",
  "payload": {
    "recipient": "Alice",
    "recipient_email": "alice@test.com",
    "subject": "Hello World",
    "body": "Ceci est un test",
    "body_format": "plain"
  }
}
```

### Test 2 - Email avec CC et BCC

```json
{
  "action_id": "act_002",
  "intent": "send_email",
  "state": "CONFIRMED",
  "payload": {
    "recipient": "Team",
    "recipient_email": "team@company.com",
    "cc": ["bob@company.com", "charlie@company.com"],
    "bcc": ["manager@company.com"],
    "subject": "Réunion demain",
    "body": "La réunion est confirmée pour demain 14h",
    "body_format": "plain",
    "priority": "high"
  }
}
```

### Test 3 - Email invalide (pour tester validation)

```json
{
  "action_id": "act_003",
  "intent": "send_email",
  "state": "CONFIRMED",
  "payload": {
    "recipient": "Invalid",
    "recipient_email": "invalid-email-format",
    "subject": "Test erreur",
    "body": "Ceci devrait échouer"
  }
}
```

**Résultat attendu :** Erreur `Format email invalide: invalid-email-format`

---

## 5. Logs et Debugging

### Dans n8n

Cliquez sur chaque nœud après exécution pour voir :
- **Extract Email Data** : Vérifier extraction du payload
- **Validate Recipient** : Vérifier validation email
- **Send Email via Gmail SMTP** : Vérifier connexion SMTP
- **Log Success/Handle Error** : Vérifier logs

### Console n8n (Terminal)

```bash
# Si n8n lancé en mode développement
npm run start

# Voir les logs en temps réel
📧 [Email Workflow] Données reçues: {...}
📋 Email extrait:
  - Destinataire: John Doe
  - Email: john@example.com
  - Sujet: Test Email
✅ [Validation] Email valide: john@example.com
✅ [Email] Envoi réussi!
```

---

## 6. Configuration Alternative (Free.fr SMTP)

Si vous voulez utiliser Free au lieu de Gmail :

```javascript
// Dans le nœud "Send Email via Gmail SMTP"
// Modifier les parameters:
{
  "transporterOptions": {
    "host": "smtp.free.fr",
    "port": 465,
    "secure": true,  // SSL au lieu de TLS
    "auth": {
      "user": "={{$env.FREE_USER}}",     // username@free.fr
      "pass": "={{$env.FREE_PASSWORD}}"
    }
  }
}
```

Variables d'environnement pour Free :
```
FREE_USER = votre-username@free.fr
FREE_PASSWORD = votre-mot-de-passe
```

---

## 7. Checklist de Vérification

Avant de tester l'intégration complète :

- [ ] Variables d'environnement configurées dans n8n
- [ ] Workflow importé et activé
- [ ] Test cURL réussi (email reçu)
- [ ] wf_action_router pointe vers `/webhook/send_email`
- [ ] Backend Python a endpoint `/callback/n8n`
- [ ] Port 587 (Gmail) ou 465 (Free) accessible

---

## 8. Prochaines Étapes

Une fois le workflow validé :

1. **Intégration routeur** : Vérifier que `wf_action_router` route correctement
2. **Test backend complet** : Envoyer ActionJSON depuis Python
3. **Test vocal** : Commande vocale → Email envoyé
4. **Callback** : Vérifier que le backend reçoit le résultat

---

**Prêt pour les tests !** 🚀
