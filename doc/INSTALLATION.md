# Guide d'Installation - GOB Agent

Installation complète du projet étape par étape.

---

## 📋 Prérequis Système

### Logiciels Requis

- **Python 3.11+** ([Télécharger](https://www.python.org/downloads/))
- **Node.js 18+** ([Télécharger](https://nodejs.org/))
- **Docker Desktop** ([Télécharger](https://www.docker.com/products/docker-desktop/))
- **Git** (pour cloner le repo)
- **Un navigateur moderne** (Chrome, Firefox, Edge)

### Matériel

- **RAM**: 8 GB minimum (16 GB recommandé)
- **Espace disque**: 10 GB libres
- **Microphone**: Pour l'interaction vocale
- **Haut-parleurs/Casque**: Pour l'audio de réponse

---

## 🚀 Installation Complète

### Étape 1: Cloner le Projet

```bash
git clone https://github.com/Montassarnawara/pcd-ai-embedded-agent.git
cd pcd-ai-embedded-agent
```

### Étape 2: Installer Ollama + Modèle

#### Windows

```powershell
# Télécharger Ollama depuis https://ollama.ai/download
# Installer l'exécutable

# Télécharger le modèle mistral:7b
ollama pull mistral:7b

# Vérifier l'installation
ollama list
```

#### Linux/Mac

```bash
curl https://ollama.ai/install.sh | sh
ollama pull mistral:7b
ollama list
```

### Étape 3: Setup Backend Python

```bash
cd pcd-ai-embedded-agent

# Créer environnement virtuel
python -m venv venv

# Activer (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activer (Linux/Mac)
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

#### Dépendances Backend Principales

```txt
fastapi==0.104.1          # Framework API
uvicorn[standard]==0.24.0 # Serveur ASGI
faster-whisper==0.9.0     # STT Whisper optimisé
ollama==0.1.7             # Client Ollama LLM
wyoming==1.5.0            # Protocol TTS Piper
paho-mqtt==1.6.1          # Client MQTT
pydantic==2.5.0           # Validation données
python-multipart==0.0.6   # Upload fichiers
python-dotenv==1.0.0      # Variables ENV
```

### Étape 4: Configuration Backend

```bash
# Copier le template .env
cp backend/.env.example backend/.env

# Éditer backend/.env avec vos paramètres
```

**Fichier `backend/.env`:**

```bash
# === LLM Configuration ===
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=500

# === STT Configuration ===
STT_PROVIDER=faster_whisper
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=en

# === TTS Configuration ===
TTS_PROVIDER=piper
PIPER_HOST=localhost
PIPER_PORT=5002
TTS_SAMPLE_RATE=22050

# === Database ===
DATABASE_PATH=data/agent_memory.db

# === MQTT (Optionnel) ===
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_ENABLED=false

# === n8n (Optionnel) ===
N8N_ENABLED=false
N8N_WEBHOOK_URL=http://localhost:5678/webhook/action-router

# === Logging ===
LOG_LEVEL=INFO
```

### Étape 5: Initialiser la Base de Données

```bash
# Créer le dossier data
mkdir data

# La base SQLite sera créée automatiquement au premier démarrage
# Fichier: data/agent_memory.db
```

### Étape 6: Démarrer Piper TTS (Docker)

```bash
# Pull l'image Docker Piper
docker pull rhasspy/wyoming-piper

# Démarrer Piper avec voix anglaise
docker run -d \
  --name piper \
  -p 5002:5002 \
  rhasspy/wyoming-piper \
  --voice en_US-lessac-medium \
  --uri tcp://0.0.0.0:5002 \
  --length-scale 1.0
```

**Voix disponibles:**

| Langue | Code Voix | Commande Docker |
|--------|-----------|-----------------|
| Anglais 🇬🇧 | `en_US-lessac-medium` | `--voice en_US-lessac-medium` |
| Français 🇫🇷 | `fr_FR-siwis-medium` | `--voice fr_FR-siwis-medium` |
| Arabe 🇸🇦 | `ar_JO-kareem-medium` | `--voice ar_JO-kareem-medium` |

**Changer de voix:**

```bash
# Arrêter le conteneur actuel
docker stop piper
docker rm piper

# Redémarrer avec une autre voix (ex: français)
docker run -d --name piper -p 5002:5002 \
  rhasspy/wyoming-piper \
  --voice fr_FR-siwis-medium \
  --uri tcp://0.0.0.0:5002
```

### Étape 7: Setup Frontend React

```bash
# Aller dans le dossier frontend
cd agent-ui

# Installer les dépendances
npm install
```

#### Dépendances Frontend Principales

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "typescript": "^5.2.2",
  "vite": "^5.0.0",
  "zustand": "^4.4.7",
  "lottie-react": "^2.4.0"
}
```

### Étape 8: Configuration Frontend

**Fichier `agent-ui/vite.config.ts` (déjà configuré):**

```typescript
export default defineConfig({
  server: {
    port: 5173,
    https: false, // Ou true si certificats SSL
    open: true
  }
})
```

---

## 🎯 Démarrage du Système

### Terminal 1: Backend

```bash
cd pcd-ai-embedded-agent
.\venv\Scripts\Activate.ps1  # Windows
# ou: source venv/bin/activate  # Linux/Mac

uvicorn backend.main:app --reload --port 8000
```

**Logs attendus:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Vérifier le health:**
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

### Terminal 2: Frontend

```bash
cd agent-ui
npm run dev
```

**Logs attendus:**
```
VITE v5.0.0  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Terminal 3: Piper TTS (Docker)

```bash
# Déjà démarré à l'étape 6
# Vérifier qu'il tourne:
docker ps | grep piper

# Logs Piper:
docker logs -f piper
```

---

## ✅ Vérification Installation

### 1. Backend Health Check

```bash
# Test health
curl http://localhost:8000/health

# Test docs API
# Ouvrir: http://localhost:8000/docs
```

### 2. Piper TTS Check

```bash
# Test connexion Piper
curl http://localhost:5002
# Devrait retourner des infos Wyoming
```

### 3. Ollama Check

```bash
ollama list
# Doit afficher: mistral:7b

ollama run mistral:7b "Hello"
# Doit générer une réponse
```

### 4. Frontend Check

1. Ouvrir http://localhost:5173
2. Autoriser le microphone
3. Voir "✅ System Ready"
4. Bouton micro visible

---

## 🐛 Dépannage

### Problème: Backend ne démarre pas

**Erreur**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
# Vérifier que venv est activé
.\venv\Scripts\Activate.ps1

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Problème: Ollama not found

**Erreur**: `Connection refused to localhost:11434`

**Solution**:
```bash
# Démarrer Ollama manuellement
ollama serve

# Dans un autre terminal
ollama pull mistral:7b
```

### Problème: Piper TTS ne répond pas

**Erreur**: `Cannot connect to Piper on port 5002`

**Solution**:
```bash
# Vérifier que Docker tourne
docker ps

# Redémarrer Piper
docker restart piper

# Voir les logs
docker logs piper
```

### Problème: Microphone ne fonctionne pas

**Erreur**: `Permission denied for microphone`

**Solution**:
1. Chrome: Settings → Privacy and Security → Site Settings → Microphone
2. Autoriser localhost:5173
3. Rafraîchir la page (F5)

### Problème: Audio ne joue pas

**Solution**:
```bash
# Vérifier le toggle audio dans Settings (⚙️)
# Doit être ON (vert)

# Vérifier le volume système
# Windows: Icône volume en bas à droite
```

### Problème: CORS Error

**Erreur**: `Access to fetch blocked by CORS policy`

**Solution**:
```python
# backend/main.py est déjà configuré avec CORS
# Vérifier que le backend tourne sur port 8000
# Vérifier que le frontend tourne sur port 5173
```

---

## 🔧 Configuration Avancée

### Mode Production

#### Backend Production

```bash
# Installer gunicorn
pip install gunicorn

# Démarrer avec gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend Production

```bash
cd agent-ui

# Build
npm run build

# Le dossier dist/ contient les fichiers statiques
# Servir avec nginx ou Apache
```

### Docker Compose (Optionnel)

**Fichier `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  piper:
    image: rhasspy/wyoming-piper
    ports:
      - "5002:5002"
    command: --voice en_US-lessac-medium --uri tcp://0.0.0.0:5002

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PIPER_HOST=piper
      - PIPER_PORT=5002
    depends_on:
      - piper

  frontend:
    build: ./agent-ui
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

**Démarrer tout:**
```bash
docker-compose up -d
```

---

## 📊 Performances

### Optimisations Backend

```python
# backend/.env

# CPU faible: Whisper tiny
WHISPER_MODEL_SIZE=tiny

# CPU moyen: Whisper base (par défaut)
WHISPER_MODEL_SIZE=base

# GPU disponible: Whisper medium + CUDA
WHISPER_MODEL_SIZE=medium
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```

### Optimisations Frontend

```bash
# Vite build avec optimisations
npm run build -- --mode production

# Analyse du bundle
npm run build -- --mode production --report
```

---

## 🔐 Sécurité Production

### Backend

```python
# backend/.env

# Désactiver debug
DEBUG=false

# Limiter CORS
CORS_ORIGINS=https://yourdomain.com

# Activer HTTPS
USE_HTTPS=true
```

### Frontend

```typescript
// agent-ui/src/services/api.ts

// Utiliser HTTPS en production
const API_URL = import.meta.env.PROD 
  ? 'https://api.yourdomain.com'
  : 'http://localhost:8000';
```

---

## 📝 Checklist Post-Installation

- [ ] Backend démarre sans erreur
- [ ] Frontend accessible sur http://localhost:5173
- [ ] Piper TTS répond (docker ps)
- [ ] Ollama mistral:7b téléchargé
- [ ] Microphone autorisé dans le navigateur
- [ ] Test vocal : "Hello" → réponse OK
- [ ] Test action : "Turn on the lamp" → confirmation
- [ ] Settings (⚙️) accessible
- [ ] Dark mode fonctionne
- [ ] Memory panel affiche les données

---

## 🆘 Support

**Documentation complète**: `/doc/README.md`  
**API Reference**: `/doc/API.md`  
**GitHub Issues**: https://github.com/Montassarnawara/pcd-ai-embedded-agent/issues

---

**Version**: 1.0.0  
**Dernière mise à jour**: 14 février 2026
