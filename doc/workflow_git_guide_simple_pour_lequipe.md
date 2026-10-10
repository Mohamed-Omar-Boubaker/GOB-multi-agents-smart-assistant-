# Workflow Git – Guide simple pour l’équipe

Ce document explique **pas à pas** comment chaque membre de l’équipe doit travailler avec Git, depuis le début jusqu’au développement et l’envoi du code.

---

## 🔁 Les 4 étapes de base (OBLIGATOIRES)

### Étape 1 — Cloner le projet (une seule fois)
```bash
git clone https://github.com/Montassarnawara/pcd-ai-embedded-agent.git
cd pcd-ai-embedded-agent
```
➡️ À ce moment, vous êtes automatiquement sur la branche `main`.

---

### Étape 2 — Récupérer toutes les branches existantes
```bash
git fetch origin
```
➡️ Cette commande permet de voir toutes les branches créées sur GitHub.

---

### Étape 3 — Se placer sur sa branche de travail
⚠️ **On ne développe jamais sur `main`.**

Chaque membre travaille uniquement sur **sa branche**.

---

### Étape 4 — Développement + Git add / commit / push
Une fois sur la bonne branche, vous pouvez coder normalement.

Cycle standard :
```bash
git status
git add .
git commit -m "Message clair du changement"
git push
```

---

# 👤 Exemple 1 — Romual (Backend Action Builder)

### 1️⃣ Cloner le projet
```bash
git clone https://github.com/Montassarnawara/pcd-ai-embedded-agent.git
cd pcd-ai-embedded-agent
```

### 2️⃣ Récupérer les branches
```bash
git fetch origin
```

### 3️⃣ Se placer sur la branche assignée
```bash
git checkout feature/backend-action-builder
```

### 4️⃣ Développement
Romual modifie uniquement les fichiers liés au **backend / action builder**.

### 5️⃣ Enregistrer le travail
```bash
git add .
git commit -m "Add action builder logic"
git push
```

---

# 👤 Exemple 2 — Emile (ESP32 Audio)

### 1️⃣ Cloner le projet
```bash
git clone https://github.com/Montassarnawara/pcd-ai-embedded-agent.git
cd pcd-ai-embedded-agent
```

### 2️⃣ Récupérer les branches
```bash
git fetch origin
```

### 3️⃣ Se placer sur la branche assignée
```bash
git checkout feature/esp32-audio
```

### 4️⃣ Développement
Emile modifie uniquement les fichiers liés au **code ESP32 / audio**.

### 5️⃣ Enregistrer le travail
```bash
git add .
git commit -m "Implement ESP32 audio capture"
git push
```

---

## ❌ Règles importantes à respecter
- ❌ Ne jamais coder sur `main`
- ❌ Ne jamais faire `git checkout -b` sans autorisation
- ✅ Toujours travailler sur sa branche
- ✅ Toujours faire des commits clairs

---

## ✅ Résumé rapide
1. `git clone`
2. `git fetch origin`
3. `git checkout feature/...`
4. coder → `git add` → `git commit` → `git push`

👉 Si tout le monde suit ce workflow, il n’y aura **aucun conflit** et le projet avancera proprement.

