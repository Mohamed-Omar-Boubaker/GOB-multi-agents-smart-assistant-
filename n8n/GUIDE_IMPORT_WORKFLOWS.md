# 🚀 Guide d'Import Workflows n8n - Instructions Détaillées

**Date:** 16 février 2026  
**Durée estimée:** 10 minutes

---

## 📋 Fichiers à Importer

Les workflows suivants ont été créés et sont prêts à importer:

1. ✅ **wf_action_router_COMPLETE.json** (Priorité 1 - CRITIQUE)
   - Routeur principal qui reçoit toutes les actions
   - Validation HMAC signature
   - Routing vers workflows spécialisés

2. ✅ **wf_control_iot_COMPLETE.json** (Priorité 1 - CRITIQUE)
   - Contrôle des appareils IoT
   - Publication MQTT vers devices
   - Callback backend avec résultat

3. ⚠️ **wf_send_email.json** (Optionnel - pour démo complète)
4. ⚠️ **wf_set_reminder.json** (Optionnel)
5. ⚠️ **wf_web_search.json** (Optionnel)

**Recommandation:** Importer SEULEMENT les 2 premiers pour la démo téléphone MQTT.

---

## 🔧 Étapes d'Import

### 1. Ouvrir n8n UI

```
Ouvrir navigateur → http://localhost:5678
```

**Si demande de login:**
- Username: `admin` (ou créer compte)
- Password: (votre mot de passe)

---

### 2. Importer Workflow Routeur

1. **Dans n8n UI:**
   - Cliquer sur **"Workflows"** (menu gauche)
   - Cliquer sur **"+ Add workflow"** (bouton en haut)
   - Cliquer sur menu **"..." (3 points)** en haut à droite
   - Sélectionner **"Import from File..."**

2. **Sélectionner fichier:**
   ```
   C:\Users\lapte\OneDrive - ensi-uma.tn\Bureau\GOB agint\pcd-ai-embedded-agent\n8n\wf_action_router_COMPLETE.json
   ```

3. **Vérifier import:**
   - ✅ Vous devez voir 11 nodes connectés
   - ✅ Flow: Webhook → Validate HMAC → Switch → HTTP Requests → Merge → Callback
   - ✅ Nom du workflow: "Action Router - Routeur Principal"

4. **Sauvegarder:**
   - Cliquer **"Save"** bouton en haut à droite
   - **NE PAS ACTIVER** le workflow pour l'instant

5. **Noter l'URL webhook:**
   - Cliquer sur le node "Webhook - Receive ActionJSON"
   - Copier l'URL (ex: `http://localhost:5678/webhook/action`)
   - ✅ Cette URL doit correspondre à celle dans backend/.env

---

### 3. Importer Workflow Control IoT

1. **Créer nouveau workflow:**
   - Retour à **"Workflows"**
   - Cliquer **"+ Add workflow"**
   - Menu **"..." → "Import from File..."**

2. **Sélectionner fichier:**
   ```
   C:\Users\lapte\OneDrive - ensi-uma.tn\Bureau\GOB agint\pcd-ai-embedded-agent\n8n\wf_control_iot_COMPLETE.json
   ```

3. **Vérifier import:**
   - ✅ Vous devez voir 7 nodes connectés
   - ✅ Flow: Webhook → Extract Command → MQTT Publish → Wait → Build Result → Callback
   - ✅ Node MQTT avec config `localhost:1883`

4. **Configurer MQTT node:**
   - Cliquer sur le node **"Publish MQTT Command"**
   - Vérifier paramètres:
     - Protocol: `mqtt`
     - Host: `localhost`
     - Port: `1883`
     - Topic: `={{ $json.mqtt_topic }}` (dynamique)
     - QoS: `1`
   - ✅ Si tout est bon, cliquer **"Save"**

5. **Sauvegarder workflow:**
   - Cliquer **"Save"**

---

### 4. Activer les Workflows

**Important:** Activer dans cet ordre!

1. **Activer wf_control_iot:**
   - Ouvrir le workflow "Control IoT - Contrôle Domotique"
   - Toggle switch **"Active"** en haut à droite → **ON** (vert)
   - ✅ Webhook devient accessible: `http://localhost:5678/webhook/control_iot`

2. **Activer wf_action_router:**
   - Ouvrir le workflow "Action Router - Routeur Principal"
   - Toggle switch **"Active"** → **ON** (vert)
   - ✅ Webhook devient accessible: `http://localhost:5678/webhook/action`

**Vérification:**
```
Dans n8n, menu "Workflows" → vous devez voir:
✅ Action Router - Routeur Principal (Active)
✅ Control IoT - Contrôle Domotique (Active)
```

---

## 🧪 Test Rapide

### Test 1: Webhook Routeur Accessible

```powershell
# Dans PowerShell
curl http://localhost:5678/webhook/action
```

**Résultat attendu:** Erreur 400 ou 405 (normal, on n'a pas envoyé de données)

### Test 2: Workflow IoT Accessible

```powershell
curl http://localhost:5678/webhook/control_iot
```

**Résultat attendu:** Erreur 400 ou 405 (normal)

---

## ⚠️ Problèmes Courants

### Problème 1: "MQTT node error"

**Cause:** Broker MQTT pas accessible

**Solution:**
```powershell
# Vérifier MQTT service Windows
Get-Service -Name "*mqtt*" | Format-List

# Ou tester connexion
Test-NetConnection -ComputerName localhost -Port 1883
```

### Problème 2: "Cannot import workflow"

**Cause:** Version n8n incompatible

**Solution:**
- Version minimale requise: n8n v0.200+
- Vérifier version: coin bas droite de n8n UI
- Mettre à jour Docker: `docker pull n8nio/n8n:latest`

### Problème 3: "Webhook not found"

**Cause:** Workflow pas activé

**Solution:**
- Vérifier que le toggle "Active" est sur **ON** (vert)
- Redémarrer n8n: `docker restart n8n`

---

## ✅ Validation Finale

Après import, vous devez avoir:

1. ✅ 2 workflows importés et **ACTIFS**
2. ✅ Webhook routeur: `http://localhost:5678/webhook/action`
3. ✅ Webhook IoT: `http://localhost:5678/webhook/control_iot`
4. ✅ MQTT node configuré avec `localhost:1883`
5. ✅ Aucune erreur dans les nodes

---

## 🎯 Prochaine Étape

Après validation de l'import:
1. ✅ Vérifier que backend est lancé (`uvicorn main:app --reload`)
2. ✅ Vérifier que frontend est lancé (`npm run dev`)
3. ✅ Configurer app mobile MQTT
4. ✅ Lancer test end-to-end complet

---

**Questions?** Voir [PLAN_IMPLEMENTATION_N8N.md](./PLAN_IMPLEMENTATION_N8N.md) section "Problèmes Courants"
