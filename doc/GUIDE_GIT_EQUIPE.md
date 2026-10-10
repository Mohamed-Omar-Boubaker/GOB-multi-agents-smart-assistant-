# 📘 Guide Git pour l'Équipe PCD - Agent Intelligent Embarqué

**Projet:** PCD Agent Intelligent Embarqué  
**Équipe:** Montassar (Chef de projet), Amine (Full-Stack), Omar (Embarqué)  
**Date:** 20 janvier 2026

---

## 🎯 Vue d'ensemble des branches

### Branches par membre d'équipe

| Membre | Branches assignées | Modules |
|--------|-------------------|---------|
| **Montassar** | `feature/backend-classifier`<br>`feature/backend-llm-client` | Classifier<br>LLM Client, Agent Core, State Manager |
| **Amine** | `feature/backend-action-builder`<br>`feature/n8n-workflows` | Action Builder, Confirmation, Security, n8n<br>Workflows n8n |
| **Omar** | `feature/backend-stt-tts`<br>`feature/esp32-audio` | STT/TTS Engines, MQTT Client<br>Module ESP32 complet |

### Architecture des branches

```
main (production)
  ├── feature/backend-classifier (Omar)
  ├── feature/backend-llm-client (Montassar)
  ├── feature/backend-action-builder (Amine)
  ├── feature/backend-stt-tts (Montassar)
  ├── feature/n8n-workflows (Amine)
  └── feature/esp32-audio (Omar)
```

## 📥 1. Installation Initiale (PREMIÈRE FOIS UNIQUEMENT)

### Pour Amine et Omar - Cloner le projet

```bash
# 1. Ouvrir PowerShell ou Git Bash

# 2. Naviguer vers votre dossier de travail
cd "C:\Users\VotreNom\Documents\Projets"

# 3. Cloner le projet
git clone https://github.com/Montassarnawara/pcd-ai-embedded-agent.git

# ⚠️ Si erreur "repository not found" ou "permission denied":
# → Vérifier que vous avez accepté l'invitation de Montassar
# → Vérifier que vous êtes connecté au bon compte GitHub
# → Contacter Montassar pour vérifier l'accès

# 4. Entrer dans le dossier
cd pcd-ai-embedded-agent

# 5. Vérifier les branches disponibles
git branch -r
```

**Résultat attendu :**
```
origin/HEAD -> origin/main
origin/feature/backend-action-builder
origin/feature/backend-classifier
origin/feature/backend-llm-client
origin/feature/backend-stt-tts
origin/feature/esp32-audio
origin/feature/n8n-workflows
origin/main

---

## 👨‍💻 2. Pour AMINE - Workflow de Développement

### 2.1 Configuration initiale (après clone)

```bash
# Vérifier branche actuelle
git branch

# Lister toutes les branches
git branch -a

# ⚠️ IMPORTANT : Configurer votre identité Git (OBLIGATOIRE)
# Utiliser votre VRAI nom et email GitHub
git config --global user.name "Amine Votre-Nom"
git config --global user.email "votre-email@example.com"

# Vérifier configuration
git config --global --list
```

**Note :** Cette configuration permet à Git de savoir qui fait les commits. Utilisez le même email que votre compte GitHub.

### 2.2 Travailler sur `feature/backend-action-builder`

```bash
# 1. Basculer vers la branche
git checkout feature/backend-action-builder

# 2. Vérifier que vous êtes sur la bonne branche (doit afficher *)
git branch

# 3. Synchroniser avec la dernière version
git pull origin feature/backend-action-builder

# 4. Commencer à travailler sur vos fichiers
# Ouvrir VS Code dans ce dossier
code .
```

### 2.3 Fichiers à modifier (Amine - Action Builder)

```
backend/
├── actions/
│   ├── action_builder.py          ← TON FICHIER PRINCIPAL
│   ├── confirmation_handler.py    ← TON FICHIER PRINCIPAL
│   └── tests/
│       ├── test_action_builder.py
│       └── test_confirmation_handler.py
│
└── agent/
    └── security_manager.py         ← TON FICHIER PRINCIPAL
```

### 2.4 Après avoir modifié des fichiers

```bash
# 1. Voir les fichiers modifiés
git status

# 2. Ajouter les fichiers modifiés
git add backend/actions/action_builder.py
git add backend/actions/confirmation_handler.py

# OU ajouter tous les fichiers modifiés
git add .

# 3. Créer un commit avec message clair
git commit -m "feat(actions): implémentation ActionBuilder avec tests unitaires"

# 4. Envoyer vers GitHub
git push origin feature/backend-action-builder
```

### 2.5 Exemples de messages de commit (Amine)

```bash
# Feature
git commit -m "feat(action-builder): construction ActionJSON pour intent control_iot"
git commit -m "feat(confirmation): génération demandes confirmation utilisateur"
git commit -m "feat(security): signature HMAC-SHA256 ActionJSON"

# Tests
git commit -m "test(action-builder): ajout 5 tests unitaires IoT/Email/Reminder"

# Fix
git commit -m "fix(confirmation): correction parsing réponse 'oui/non'"

# Documentation
git commit -m "docs(actions): ajout documentation API ActionBuilder"
```

### 2.6 Travailler sur `feature/n8n-workflows` (Amine)

```bash
# 1. Basculer vers la branche n8n
git checkout feature/n8n-workflows

# 2. Synchroniser
git pull origin feature/n8n-workflows

# 3. Modifier les workflows n8n
# Fichiers: n8n/wf_*.json

# 4. Commiter et pusher
git add n8n/
git commit -m "feat(n8n): workflow send_email avec validation SMTP"
git push origin feature/n8n-workflows
```

### 2.7 Changer de branche (Amine)

```bash
# Passer de action-builder à n8n-workflows
git checkout feature/n8n-workflows

# Passer de n8n-workflows à action-builder
git checkout feature/backend-action-builder

# Retour à main (pour voir état production)
git checkout main

# IMPORTANT: Toujours commit ou stash avant de changer de branche !
```

---

## 👨‍💻 3. Pour OMAR - Workflow de Développement

### 3.1 Configuration initiale (après clone)

```bash
# Vérifier branche actuelle
git branch

# ⚠️ IMPORTANT : Configurer votre identité Git (OBLIGATOIRE)
# Utiliser votre VRAI nom et email GitHub
git config --global user.name "Omar Votre-Nom"
git config --global user.email "votre-email@example.com"

# Vérifier configuration
git config --global --list
```

**Note :** Cette configuration permet à Git de savoir qui fait les commits. Utilisez le même email que votre compte GitHub.

### 3.2 Travailler sur `feature/backend-stt-tts`

```bash
# 1. Basculer vers la branche
git checkout feature/backend-stt-tts

# 2. Vérifier branche active
git branch

# 3. Synchroniser avec GitHub
git pull origin feature/backend-stt-tts

# 4. Ouvrir projet dans VS Code
code .
```

### 3.3 Fichiers à modifier (Omar - STT/TTS)

```
backend/
├── ai/
│   ├── stt_engine.py              ← TON FICHIER PRINCIPAL
│   ├── tts_engine.py              ← TON FICHIER PRINCIPAL
│   └── tests/
│       ├── test_stt_engine.py
│       └── test_tts_engine.py
│
└── integrations/
    └── mqtt_client.py              ← TON FICHIER PRINCIPAL
```

### 3.4 Après avoir modifié des fichiers

```bash
# 1. Voir modifications
git status

# 2. Ajouter fichiers
git add backend/ai/stt_engine.py
git add backend/ai/tts_engine.py
git add backend/integrations/mqtt_client.py

# OU tout ajouter
git add .

# 3. Commit avec message
git commit -m "feat(audio): implémentation STT avec Whisper base model"

# 4. Push vers GitHub
git push origin feature/backend-stt-tts
```

### 3.5 Exemples de messages de commit (Omar)

```bash
# Feature
git commit -m "feat(stt): intégration Whisper pour transcription audio"
git commit -m "feat(tts): synthèse vocale gTTS français"
git commit -m "feat(mqtt): client MQTT pour communication ESP32"

# Tests
git commit -m "test(stt): tests transcription audio WAV/MP3"

# Fix
git commit -m "fix(tts): correction encodage base64 audio"

# Documentation
git commit -m "docs(audio): guide installation Whisper"
```

### 3.6 Travailler sur `feature/esp32-audio` (Omar)

```bash
# 1. Basculer vers branche ESP32
git checkout feature/esp32-audio

# 2. Synchroniser
git pull origin feature/esp32-audio

# 3. Modifier fichiers ESP32
# Fichiers: esp32/*.cpp, esp32/*.h

# 4. Commiter et pusher
git add esp32/
git commit -m "feat(esp32): implémentation audio handler I2S"
git push origin feature/esp32-audio
```

### 3.7 Changer de branche (Omar)

```bash
# Passer de backend-stt-tts à esp32-audio
git checkout feature/esp32-audio

# Passer de esp32-audio à backend-stt-tts
git checkout feature/backend-stt-tts

# Retour à main
git checkout main
```

---

## 🔄 4. Workflow Quotidien (TOUS)

### Début de journée

```bash
# 1. Aller sur votre branche
git checkout feature/votre-branche

# 2. Récupérer dernières modifications
git pull origin feature/votre-branche

# 3. Commencer à coder
```

### Pendant le travail

```bash
# Vérifier status souvent
git status

# Voir différences
git diff

# Ajouter fichiers progressivement
git add fichier1.py
git add fichier2.py
```

### Fin de journée (ou après chaque feature)

```bash
# 1. Vérifier modifications
git status

# 2. Ajouter tous les fichiers
git add .

# 3. Commit avec message clair
git commit -m "feat(module): description claire de ce qui a été fait"

# 4. Envoyer vers GitHub
git push origin feature/votre-branche
```

---

## 🚨 5. Situations Courantes et Solutions

### 5.1 Erreur "Please commit your changes or stash them"

**Problème:** Vous avez des modifications non commitées et voulez changer de branche.

**Solution 1 (Commit):**
```bash
git add .
git commit -m "WIP: travail en cours sur action_builder"
git checkout autre-branche
```

**Solution 2 (Stash - mettre de côté):**
```bash
git stash
git checkout autre-branche
# Plus tard, pour récupérer:
git checkout votre-branche
git stash pop
```

### 5.2 Erreur "Updates were rejected"

**Problème:** Quelqu'un d'autre a push avant vous.

**Solution:**
```bash
# 1. Récupérer les dernières modifications
git pull origin feature/votre-branche

# 2. Résoudre conflits si nécessaire (voir section 5.3)

# 3. Re-pusher
git push origin feature/votre-branche
```

### 5.3 Conflit de merge (CONFLICT)

**Problème:** Fichier modifié par 2 personnes différemment.

**Solution:**
```bash
# 1. Git vous indique les fichiers en conflit
git status

# 2. Ouvrir fichier, vous verrez:
<<<<<<< HEAD
votre code
=======
code de l'autre personne
>>>>>>> branch

# 3. Éditer manuellement pour garder la bonne version

# 4. Marquer comme résolu
git add fichier-resolu.py

# 5. Finaliser le merge
git commit -m "merge: résolution conflit action_builder"

# 6. Pusher
git push origin feature/votre-branche
```

### 5.4 Annuler un commit (PAS ENCORE PUSHÉ)

```bash
# Annuler le dernier commit (garde modifications)
git reset --soft HEAD~1

# Annuler le dernier commit (SUPPRIME modifications)
git reset --hard HEAD~1
```

### 5.5 Voir l'historique des commits

```bash
# Voir tous les commits
git log

# Voir commits de manière compacte
git log --oneline

# Voir derniers 5 commits
git log --oneline -5
```

---

## 📋 6. Checklist avant de Push

### ✅ Avant chaque `git push`

- [ ] J'ai testé mon code localement
- [ ] Mon code compile/exécute sans erreur
- [ ] J'ai ajouté des tests unitaires (si applicable)
- [ ] J'ai vérifié `git status`
- [ ] Mon message de commit est clair et descriptif
- [ ] Je suis sur la BONNE branche (`git branch` pour vérifier)
- [ ] J'ai fait `git pull` pour synchroniser
- [ ] J'ai accepté l'invitation collaborateur de Montassar (première fois)

---

## ⚠️ 6.5 Erreurs d'Accès Courantes

### Erreur : "remote: Repository not found"

**Cause :** Vous n'êtes pas ajouté comme collaborateur OU vous n'avez pas accepté l'invitation.

**Solution :**
1. Vérifier email pour invitation GitHub
2. Accepter l'invitation (lien dans email)
3. Contacter Montassar pour vérifier que vous êtes bien ajouté
4. Vérifier que vous êtes connecté au bon compte GitHub

### Erreur : "permission denied" lors du push

**Cause :** Pas de droits d'écriture sur le dépôt.

**Solution :**
1. Vérifier que vous êtes collaborateur (Montassar peut check dans Settings > Collaborators)
2. Vérifier que votre email Git correspond à votre compte GitHub :
   ```bash
   git config --global user.email
   # Doit être le même que votre compte GitHub
   ```
3. Re-cloner le dépôt si nécessaire

### Erreur : "Authentication failed"

**Cause :** Git ne sait pas qui vous êtes.

**Solution :**
```bash
# Configurer identité Git
git config --global user.name "Votre Nom"
git config --global user.email "votre-email-github@example.com"

# Si Windows, peut nécessiter credential helper
git config --global credential.helper wincred
```

---

## 🔍 7. Commandes Utiles de Référence

### Voir l'état

```bash
git status              # Voir fichiers modifiés
git diff                # Voir différences détaillées
git log --oneline       # Voir historique commits
git branch              # Voir branches locales
git branch -r           # Voir branches distantes
```

### Gérer les fichiers

```bash
git add fichier.py      # Ajouter UN fichier
git add .               # Ajouter TOUS les fichiers
git add backend/        # Ajouter UN dossier
git restore fichier.py  # Annuler modifications (avant add)
git restore --staged f  # Retirer du staging (après add)
```

### Branches

```bash
git checkout branche    # Changer de branche
git checkout -b new     # Créer NOUVELLE branche
git branch -d branche   # Supprimer branche locale
```

### Synchronisation

```bash
git pull origin main           # Récupérer main
git pull origin feature/xxx    # Récupérer votre branche
git push origin feature/xxx    # Envoyer vers GitHub
git fetch origin               # Voir changements sans télécharger
```

---



## 📝 11. Workflow Complet - Exemple Amine

```bash
# === LUNDI MATIN ===
cd pcd-ai-embedded-agent
git checkout feature/backend-action-builder
git pull origin feature/backend-action-builder

# === DÉVELOPPEMENT ===
# Ouvrir VS Code, modifier action_builder.py
code .
# ... coder pendant 2h ...

# === COMMIT 1 ===
git add backend/actions/action_builder.py
git commit -m "feat(action-builder): ajout méthode build() pour intent control_iot"
git push origin feature/backend-action-builder

# === DÉVELOPPEMENT SUITE ===
# ... coder tests ...

# === COMMIT 2 ===
git add backend/actions/tests/test_action_builder.py
git commit -m "test(action-builder): 5 tests unitaires IoT"
git push origin feature/backend-action-builder

# === CHANGEMENT DE BRANCHE ===
git checkout feature/n8n-workflows
git pull origin feature/n8n-workflows

# Modifier workflows n8n
# ...

git add n8n/wf_send_email.json
git commit -m "feat(n8n): workflow send_email avec validation SMTP"
git push origin feature/n8n-workflows

# === FIN DE JOURNÉE ===
# Vérifier que tout est pushé
git status
# Should show: "working tree clean"
```

---

## 🎯 Début Rapide (Quick Start)

### Pour Amine - 1ère fois

```bash
git clone https://github.com/Montassarnawara/pcd-ai-embedded-agent.git
cd pcd-ai-embedded-agent
git checkout feature/backend-action-builder
git pull origin feature/backend-action-builder
code .
```

### Pour Omar - 1ère fois

```bash
git clone https://github.com/Montassarnawara/pcd-ai-embedded-agent.git
cd pcd-ai-embedded-agent
git checkout feature/backend-stt-tts
git pull origin feature/backend-stt-tts
code .
```

---

**Bon développement ! 🚀**

