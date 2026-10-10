# PHASE 1 - Integration Embarquee ESP32 (Audio Action)

## 1. Objectif

Cette phase relie l'execution des actions (IoT + Email) a la sortie vocale sur ESP32 haut-parleur.

Resultat attendu:
- L'utilisateur lance une action depuis Web/Mobile.
- L'action est executee via n8n.
- Un message vocal de confirmation est genere.
- L'ESP32 joue ce message.
- L'ESP32 renvoie un ACK MQTT (`started`, `done`, `error`).

## 2. Hors Perimetre (Phase 2)

Non inclus dans Phase 1:
- Animations servo selon etats UX (`sleep`, `listening`, `thinking`, etc.).
- Synchronisation mecanique robot complete.

Ces elements seront traites en Phase 2.

## 3. Architecture Cible (Phase 1)

Flux global:
1. UX (Web/Mobile) envoie commande au backend.
2. Backend classifie, confirme, execute via n8n.
3. n8n execute l'action (`wf_control_iot` ou `wf_send_email`).
4. n8n fait un test `success/failure` juste apres le noeud d'execution.
5. n8n construit un message vocal simple selon le resultat.
6. n8n appelle `piper_tts_service` pour obtenir `audio_url`.
7. n8n publie MQTT sur `gob/audio/tts/request`.
8. ESP32 haut-parleur recoit, telecharge WAV, joue audio.
9. ESP32 publie ACK sur `gob/audio/tts/ack`.
10. n8n peut aussi declencher une notification utilisateur (email) via `wf_notification`.
11. Backend/n8n journalise l'ACK.

## 4. Contrat MQTT Standard

### 4.1 Topic Request
`gob/audio/tts/request`

Payload:
```json
{
  "request_id": "req_abc123",
  "action_id": "act_xyz789",
  "user_id": "web_user_001",
  "lang": "fr",
  "text": "La lumiere de la chambre est eteinte.",
  "url": "http://10.93.177.189:8005/audio/abcd.wav",
  "ts": 1711111111
}
```

### 4.2 Topic ACK
`gob/audio/tts/ack`

Payload:
```json
{
  "request_id": "req_abc123",
  "action_id": "act_xyz789",
  "device_id": "esp32_speaker_01",
  "status": "started",
  "error": "",
  "ts": 1711111112
}
```

`status` possibles:
- `started`
- `done`
- `error`

## 5. Regles de Message Vocal

- Message court (1 phrase).
- Pas de melange de langues.
- Langue prioritaire = langue de l'action (`context.language` si disponible).
- Fallback langue = `fr`.

Exemples:
- FR: `La lumiere du salon est allumee.`
- FR: `L'email a ete envoye a Ahmed.`
- EN: `Living room light turned on.`
- AR: `تم تشغيل ضوء غرفة الجلوس.`

## 6. Fichiers Qui Seront Modifies

1. `service/piper_tts_service.py`
2. `n8n/wf_action_router.json`
3. `n8n/wf_control_iot.json`
4. `n8n/wf_send_email.json`
5. `cpp_prototypeage/haut_parleur.cpp`
6. `n8n/wf_notification.json`

## 7. Modifications Prevues Par Fichier

### 7.1 `service/piper_tts_service.py`

Objectif:
- Retourner une URL audio accessible depuis ESP32 (IP LAN), pas `localhost`.

A faire:
- Ajouter variable config `TTS_PUBLIC_BASE_URL` (ex: `http://10.93.177.189:8005`).
- Construire `audio_url` depuis cette variable.
- Ajouter validation simple (`text` non vide, fichier genere).
- Ajouter log minimal (`request_id`, `action_id` si fournis).

### 7.2 `n8n/wf_action_router.json`

Objectif:
- Preserver les champs utiles vers les sous-workflows.

A faire:
- Verifier que `action_id`, `user_id`, `intent`, `payload`, `context.language` sont bien propages.
- Uniformiser le body JSON (`={{$json}}` quand possible).

### 7.3 `n8n/wf_control_iot.json`

Objectif:
- Ajouter notification vocale post-action.

A faire:
- Ajouter un test juste apres le noeud MQTT (execution IoT):
  - Si succes: message type `La lumiere de la chambre est allumee/eteinte.`
  - Si echec: message type `La commande IoT n'a pas ete executee.`
- Construire `voice_text` localise selon action (`turn_on`, `turn_off`, etc.) et resultat.
- Appeler endpoint TTS pour obtenir `audio_url`.
- Publier request MQTT sur `gob/audio/tts/request`.
- Garder callback backend existant (`/callback/n8n`).

### 7.4 `n8n/wf_send_email.json`

Objectif:
- Ajouter notification vocale post-email.

A faire:
- Ajouter un test juste apres le noeud d'envoi email:
  - Si succes: `L'email a ete envoye a Ahmed.`
  - Si echec: `L'email n'a pas ete envoye a Ahmed.`
- Construire `voice_text` (success/error) dans la langue utilisateur.
- Appeler TTS.
- Publier request MQTT sur `gob/audio/tts/request`.
- Conserver callback backend existant.

### 7.6 `n8n/wf_notification.json`

Objectif:
- Completer le workflow de notification utilisateur (canal email en priorite pour Phase 1).

A faire:
- Ajouter entree standard (`action_id`, `user_id`, `status`, `message`, `channel`).
- Implementer branche `channel=email` pour notifier l'utilisateur apres execution.
- Garder `voice` en option (future extension), sans bloquer la Phase 1.

### 7.5 `cpp_prototypeage/haut_parleur.cpp`

Objectif:
- Stabiliser le client ESP32 audio pour protocole final.

A faire:
- Parse JSON request proprement (`request_id`, `action_id`, `url`, `lang`, `text`).
- Publier ACK `started` avant lecture audio.
- Publier ACK `done` apres lecture audio.
- Publier ACK `error` en cas d'echec HTTP/I2S.
- Conserver limites de volume et lecture WAV.

## 8. Variables de Configuration a Definir

### 8.1 Cote TTS Service
- `TTS_PUBLIC_BASE_URL=http://10.93.177.189:8005`

### 8.2 Cote n8n
- URL service TTS (ex: `http://host.docker.internal:8005/tts` si n8n en Docker).
- Broker MQTT reachable depuis n8n.

### 8.3 Cote ESP32
- SSID / password / MQTT host.
- `device_id` unique pour ACK.

## 9. Plan d'Execution (Ordre Recommande)

1. Corriger `piper_tts_service.py` (URL LAN).
2. Ajouter test success/failure + message vocal dans `wf_control_iot.json`.
3. Ajouter test success/failure + message vocal dans `wf_send_email.json`.
4. Completer `wf_notification.json` pour notification utilisateur email.
5. Normaliser passage de langue dans `wf_action_router.json`.
6. Finaliser `haut_parleur.cpp` avec ACK MQTT.
7. Tester end-to-end.

## 10. Strategie de Tests

### 10.1 Test TTS
- POST `/tts` avec texte.
- Verifier `audio_url` en IP LAN.
- Verifier telechargement fichier WAV depuis un device reseau.

### 10.2 Test MQTT Request
- Publier manuellement une request.
- Verifier reception ESP32 + lecture audio.

### 10.3 Test ACK
- Verifier publications MQTT ACK (`started`, `done`, `error`).

### 10.4 Test End-to-End
- Commande vocale IoT depuis Web/Mobile.
- Action executee via n8n.
- Notification audio jouee sur ESP32.
- ACK visible en logs.

### 10.5 Test Notification Utilisateur
- Si action succes: notification email envoyee a l'utilisateur.
- Si action echec: notification email d'erreur envoyee a l'utilisateur.
- Verifier contenu simple et coherent avec le resultat.

## 11. Criteres de Validation Phase 1

- 100% des actions IoT/Email testees produisent une notification audio.
- Aucune URL `localhost` dans payload vers ESP32.
- ACK MQTT visible pour chaque request (`started` puis `done` ou `error`).
- Message dans la bonne langue (FR/EN/AR), sans melange.
- Notification utilisateur email envoyee sur succes et sur echec.

## 12. Livrables de Fin de Phase 1

- Workflows n8n modifies et exportes.
- Service TTS mis a jour.
- Prototype ESP32 haut-parleur stabilise (request + ack).
- Workflow notification complete (`wf_notification`).
- Guide de test rapide (commandes MQTT + endpoints TTS).


////////////////////////////////////////////////////////////////////


## 13. Architecture Phase 2 - Etat UX vers Robot (Servo)

Objectif Phase 2:
- Utiliser les etats deja geres dans l'UX pour animer la partie robot (servo), sans deplacer la logique d'etat vers le backend.

Decision principale:
- Source de verite des etats = UX.
- Le robot recoit seulement un signal d'etat.



### 13.1 Deux options d'integration

Note importante:
- Les options ci-dessous concernent le transport du signal d'etat (UX -> robot).
- Ce ne sont pas les options materielle ESP32.

Option A (recommandee pour demarrage rapide):
- UX publie directement MQTT vers le broker (`gob/robot/state`).
- Avantage: simple, peu de latence.
- Inconvenient: credentials MQTT exposes cote client.

Option B (recommandee pour production):
- UX appelle un endpoint backend (`/robot/state`).
- Backend publie MQTT vers `gob/robot/state`.
- Avantage: plus securise, credentials restent serveur.
- Inconvenient: une couche reseau de plus.

### 13.1.1 Options materielle ESP32 (nouvelle clarification)

Option A (materielle): 2 ESP32 (recommandee)
- ESP32-AUDIO: lecture WAV I2S + ACK audio.
- ESP32-SERVO: animation servo selon etat.
- Avantage: isolation des charges CPU/alimentation.
- Inconvenient: cout/complexite hardware plus eleves.

Option B (materielle): 1 ESP32 audio + servo (possible)
- Faisable pour demo/prototype.
- Risques: timing audio, jitter servo, chute tension si alimentation faible.
- Exigences techniques:
  - scheduler non-bloquant (aucun `delay` long dans la loop principale),
  - priorites claires (audio prioritaire sur servo),
  - machine d'etats interne,
  - limitation de mouvements servo pendant audio,
  - alimentation separee servo recommandee.

### 13.2 Contrat MQTT Phase 2

Topic:
`gob/robot/state`

Payload:
```json
{
  "request_id": "req_abc123",
  "user_id": "web_user_001",
  "state": "listening",
  "lang": "fr",
  "source": "agent_ui",
  "ts": 1711112000
}
```

Etats autorises:
- `idle`
- `sleep`
- `listening`
- `thinking`
- `speaking`
- `happy`
- `error`

### 13.3 Mapping etat -> mouvement servo (v1 simple)

- `sleep`: position repos fixe (servo1=0, servo2=180)
- `idle`: position neutre (servo1=20, servo2=160)
- `listening`: micro-oscillation servo2 (+/-10)
- `thinking`: micro-oscillation servo1 (+/-10)
- `speaking`: oscillation alternante douce des 2 servos
- `happy`: 2 petites oscillations rapides puis retour neutre
- `error`: retour repos + pause 1 seconde

Regle materielle:
- Un seul servo en mouvement a la fois si alimentation limitee.

### 13.4 Fichiers a toucher en Phase 2

Minimum UX seulement:
1. `agent-ui/src/store/agentStore.ts`
2. `agent-ui/src/components/MicButton/MicButton.tsx`
3. `agent-ui/src/screens/FullscreenEyesScreen/FullscreenEyesScreen.tsx`
4. `agent-ui/src/services/robotStatePublisher.ts` (nouveau)

Si option backend relay:
5. `backend/main.py` (endpoint `/robot/state`)
6. `backend/integrations/mqtt_client.py` (publish helper)

ESP32 servo:
7. `cpp_prototypeage/servo_protytpage.cpp`

### 13.5 Sequence d'execution Phase 2

1. UX change d'etat interne.
2. UX envoie evenement etat (MQTT direct ou backend relay).
3. ESP32 servo recoit l'etat.
4. ESP32 applique animation associee.
5. (Optionnel) ESP32 publie ACK sur `gob/robot/state/ack`.

### 13.5.1 Sequence interne - Option B materielle (1 ESP32)

1. Reception MQTT event (`audio request` ou `robot state`).
2. Router interne vers queue audio ou queue servo.
3. Tache audio (priorite haute): telechargement WAV + lecture I2S + ACK.
4. Tache servo (priorite moyenne): applique pattern seulement si audio non critique.
5. Watchdog logique: si surcharge, reduire frequence animation servo.

Regle priorite:
- Priorite 1: stabilite audio.
- Priorite 2: animation servo.
- Priorite 3: logs/debug.

### 13.6 Critere de validation Phase 2

- Chaque transition UX visible provoque une reaction robot coherente.
- Aucun blocage servo pendant `speaking`.
- Retour automatique en `idle`/`sleep` apres action.
- Si message invalide, robot ignore proprement (pas de crash).

### 13.7 Reponse a la question "faut-il juste toucher UX ou ajouter signal d'etat ?"

Conclusion:
- Touche UX oui, mais il faut obligatoirement ajouter un signal d'etat sortant (MQTT direct ou backend relay).
- Sans signal sortant, le robot ne peut pas se synchroniser avec les etats UX.

### 13.8 Distribution des fichiers - Option B materielle (1 ESP32)

Objectif:
- Transformer les prototypes en firmware final modulaire avec un `main` unique.

Structure proposee:

`esp32/robot_firmware/`
- `platformio.ini`
- `src/main.cpp`
- `src/app_scheduler.cpp`
- `src/app_scheduler.h`
- `src/app_state_machine.cpp`
- `src/app_state_machine.h`
- `src/audio_player.cpp`
- `src/audio_player.h`
- `src/servo_controller.cpp`
- `src/servo_controller.h`
- `src/mqtt_gateway.cpp`
- `src/mqtt_gateway.h`
- `src/json_protocol.cpp`
- `src/json_protocol.h`
- `src/config.h`
- `src/topics.h`

Roles des modules:
- `main.cpp`: setup global, loop non-bloquante, init modules.
- `app_scheduler.*`: ordonnancement cooperatif, priorites audio/servo.
- `app_state_machine.*`: etats internes du robot.
- `audio_player.*`: HTTP WAV + I2S + ACK audio.
- `servo_controller.*`: mapping state -> mouvement servo.
- `mqtt_gateway.*`: subscribe/publish MQTT centralise.
- `json_protocol.*`: parsing/validation payload MQTT.
- `config.h`: WiFi, broker, device_id, pins.
- `topics.h`: declaration unique des topics.

### 13.9 Distribution des changements repo (Phase 1 + Phase 2)

Phase 1 (audio action):
- Modifier `service/piper_tts_service.py`
- Modifier `n8n/wf_action_router.json`
- Modifier `n8n/wf_control_iot.json`
- Modifier `n8n/wf_send_email.json`
- Modifier `n8n/wf_notification.json`
- Migrer `cpp_prototypeage/haut_parleur.cpp` vers module `audio_player.*`

Phase 2 (etat UX vers servo):
- Modifier `agent-ui/src/store/agentStore.ts`
- Modifier `agent-ui/src/components/MicButton/MicButton.tsx`
- Modifier `agent-ui/src/screens/FullscreenEyesScreen/FullscreenEyesScreen.tsx`
- Ajouter `agent-ui/src/services/robotStatePublisher.ts`
- Option backend relay: modifier `backend/main.py` + `backend/integrations/mqtt_client.py`
- Migrer `cpp_prototypeage/servo_protytpage.cpp` vers module `servo_controller.*`

Livrable firmware final (Option B materielle):
- Un seul firmware ESP32 (`esp32/robot_firmware`) compose de modules + `main.cpp`.
- Les fichiers prototypes sous `cpp_prototypeage` restent reference dev uniquement.

---

Statut: **Ready for Implementation**
