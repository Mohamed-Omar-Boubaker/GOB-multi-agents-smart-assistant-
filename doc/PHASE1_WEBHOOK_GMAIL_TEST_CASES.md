# Phase 1 - Webhook Gmail Notification: cas de test complets

## Objectif

Valider le workflow notification refait:
- Webhook Gmail entrant
- Normalisation du payload
- Génération TTS
- Publication MQTT vers ESP32 audio
- Réponse webhook

Workflow ciblé:
- n8n: `/webhook/gmail_notification`

---

## Pré-requis

1. n8n actif sur `http://localhost:5678`
2. Workflow notification activé
3. Service TTS actif sur `http://127.0.0.1:8005/tts`
4. Broker MQTT actif
5. ESP32 audio connecté (optionnel pour valider juste le webhook)

## Regle reseau importante (localhost vs Docker vs ESP32)

Tu avais raison: `localhost` n'est pas le meme selon le contexte.

| Contexte appelant | URL correcte a utiliser | Pourquoi |
|---|---|---|
| PowerShell sur ton PC | `http://localhost:5678` (n8n) et `http://127.0.0.1:8005/tts` (TTS) | L'appel part de ta machine Windows |
| Node n8n dans Docker -> service sur PC | `http://host.docker.internal:8005/tts` | Depuis le container, `localhost` pointe le container |
| ESP32 -> recuperer WAV | `http://192.168.1.3:8005/audio/...wav` | ESP32 doit joindre ton PC via IP LAN |

Conclusion pratique:
- `localhost` est OK pour les tests PowerShell locaux.
- `host.docker.internal` est requis pour les appels faits depuis n8n Docker vers des services sur le host.
- `192.168.1.3` est requis dans les URLs envoyees a l'ESP32.

### Config obligatoire cote TTS

Le service TTS doit renvoyer une URL LAN pour l'ESP32.

PowerShell (session courante):

```powershell
$env:TTS_PUBLIC_BASE_URL = "http://192.168.1.3:8005"
```

Puis lancer le service TTS dans cette meme session.

---

## Format payload supporté

Champs supportés:
- `action_id` (optionnel)
- `user_id` (optionnel)
- `status`: `success` ou `failed` (optionnel, défaut: `success`)
- `language` ou `lang`: `fr|en|ar` (optionnel, défaut: `fr`)
- `recipient` ou `target` (optionnel)
- `message` (optionnel)

Si `message` est absent, le workflow construit automatiquement un message localisé selon `status` + `language`.

---

## Réponse attendue (succès)

```json
{
  "status": "ok",
  "action_id": "...",
  "language": "fr",
  "audio_url": "http://.../audio/...wav",
  "ts": "2026-..."
}
```

---

## Cas de test PowerShell

Remplacer si besoin l’URL n8n:
- `http://localhost:5678/webhook/gmail_notification`

Astuce:
- Tu peux definir une variable unique pour eviter les erreurs:

```powershell
$N8N_URL = "http://localhost:5678/webhook/gmail_notification"
```

Et utiliser `-Uri $N8N_URL` dans tous les tests.

### Cas 1 - Success FR (message auto)

```powershell
$payload = @'
{
  "action_id": "act_notif_fr_success_001",
  "user_id": "web_user_001",
  "status": "success",
  "language": "fr",
  "recipient": "Ahmed"
}
'@

Invoke-RestMethod -Uri $N8N_URL -Method POST -ContentType "application/json" -Body $payload
```

Attendu:
- `status = ok`
- `language = fr`
- message interne: `L'email a ete envoye a Ahmed.`
- MQTT publié sur `gob/audio/tts/request`

### Cas 2 - Failed FR (message auto)

```powershell
$payload = @'
{
  "action_id": "act_notif_fr_fail_001",
  "user_id": "web_user_001",
  "status": "failed",
  "language": "fr",
  "recipient": "Ahmed"
}
'@

Invoke-RestMethod -Uri $N8N_URL -Method POST -ContentType "application/json" -Body $payload
```

Attendu:
- message interne: `L'email n'a pas ete envoye a Ahmed.`

### Cas 3 - Success EN (message auto)

```powershell
$payload = @'
{
  "action_id": "act_notif_en_success_001",
  "user_id": "web_user_001",
  "status": "success",
  "language": "en",
  "recipient": "Ahmed"
}
'@

Invoke-RestMethod -Uri $N8N_URL -Method POST -ContentType "application/json" -Body $payload
```

Attendu:
- message interne: `The email was sent to Ahmed.`

### Cas 4 - Failed EN (message auto)

```powershell
$payload = @'
{
  "action_id": "act_notif_en_fail_001",
  "user_id": "web_user_001",
  "status": "failed",
  "language": "en",
  "recipient": "Ahmed"
}
'@

Invoke-RestMethod -Uri $N8N_URL -Method POST -ContentType "application/json" -Body $payload
```

Attendu:
- message interne: `The email was not sent to Ahmed.`

### Cas 5 - Success AR (message auto)

```powershell
$payload = @'
{
  "action_id": "act_notif_ar_success_001",
  "user_id": "web_user_001",
  "status": "success",
  "language": "ar",
  "recipient": "Ahmed"
}
'@

Invoke-RestMethod -Uri $N8N_URL -Method POST -ContentType "application/json" -Body $payload
```

Attendu:
- message arabe auto de succès

### Cas 6 - Message forcé (prioritaire)

```powershell
$payload = @'
{
  "action_id": "act_notif_custom_001",
  "user_id": "web_user_001",
  "status": "success",
  "language": "fr",
  "recipient": "Ahmed",
  "message": "Message personalisé de test depuis Gmail webhook."
}
'@

Invoke-RestMethod -Uri $N8N_URL -Method POST -ContentType "application/json" -Body $payload
```

Attendu:
- le workflow utilise exactement `message` fourni

### Cas 7 - Fallback langue (language absent)

```powershell
$payload = @'
{
  "action_id": "act_notif_fallback_001",
  "user_id": "web_user_001",
  "status": "success",
  "recipient": "Ahmed"
}
'@

Invoke-RestMethod -Uri $N8N_URL -Method POST -ContentType "application/json" -Body $payload
```

Attendu:
- fallback langue vers `fr`

### Cas 8 - Payload minimal

```powershell
$payload = @'
{
  "status": "success"
}
'@

Invoke-RestMethod -Uri $N8N_URL -Method POST -ContentType "application/json" -Body $payload
```

Attendu:
- `action_id` auto
- `user_id` = `unknown`
- message FR auto

---

## Vérifier la publication MQTT

Abonnement test:

```powershell
mosquitto_sub -h 127.0.0.1 -t gob/audio/tts/request -v
```

Chaque appel webhook doit publier un JSON avec:
- `request_id`
- `action_id`
- `lang`
- `text`
- `url`
- `ts`

---

## Vérifier les ACK ESP32 (si device connecté)

```powershell
mosquitto_sub -h 127.0.0.1 -t gob/audio/tts/ack -v
```

Séquence attendue:
1. `started`
2. `done` ou `error`

---

## Erreurs courantes et correction

### 1) `audio_url` vide
Cause probable:
- service TTS down

Correction:
- relancer service TTS
- tester:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8005/tts" -Method POST -ContentType "application/json" -Body '{"text":"test"}'
```

### 2) Webhook 404
Cause probable:
- workflow non activé ou path différent

Correction:
- vérifier activation workflow
- vérifier path exact: `/webhook/gmail_notification`

### 3) MQTT non publié
Cause probable:
- credentials MQTT n8n incorrectes

Correction:
- vérifier credentials node `Publish Voice MQTT`
- vérifier broker en écoute

---

## Checklist validation finale

- [ ] Webhook répond `status: ok`
- [ ] `audio_url` présent
- [ ] MQTT publié sur `gob/audio/tts/request`
- [ ] ESP32 joue l’audio
- [ ] ACK reçu sur `gob/audio/tts/ack`
- [ ] FR/EN/AR correct sans mélange

---

## Fichiers concernés Phase 1

- `service/piper_tts_service.py`
- `n8n/wf_control_iot.json`
- `n8n/wf_send_email.json`
- `n8n/wf_notification.json`
- `n8n/wf_action_router.json`
- `cpp_prototypeage/haut_parleur.cpp`
