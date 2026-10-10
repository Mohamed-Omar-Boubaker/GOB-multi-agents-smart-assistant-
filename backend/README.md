# Backend Python - Agent Intelligent Embarqué

## Responsables

- Montassar
- Omar
- Amine

## Description

Backend Python orchestrateur pour l'agent intelligent embarqué. Gère la classification des commandes (Conversation vs Action), l'analyse linguistique, la gestion des états, et la coordination avec n8n et ESP32.

## Architecture

```
backend/
├── classifier/       # Classification Conversation/Action (Montassar)
├── ai/              # STT, TTS, LLM Client (Omar + Montassar)
├── actions/         # Action Builder, Confirmation (Montassar + Omar)
├── agent/           # Agent Core, State Manager, Security (Montassar)
├── integrations/    # n8n Client, MQTT Client (Montassar + Omar)
└── utils/           # Utilitaires communs
```

## Distribution Équipe

- **Montassar** : Agent Core, state management, action lifecycle, backend orchestration
- **Omar** : STT/TTS, integrations (MQTT/n8n), AI support modules

## Installation

```bash
# Créer environnement virtuel
python -m venv venv

# Activer environnement
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Copier configuration
cp .env.example .env
# Éditer .env avec vos credentials
```

## Lancer le serveur

```bash
uvicorn backend.main:app --reload
```

## Tests

```bash
# Tous les tests
pytest backend/ -v

# Tests avec couverture
pytest backend/ --cov=backend --cov-report=html
```

## API Endpoints

- `POST /command/text` : Commande textuelle
- `POST /command/audio` : Commande vocale
- `POST /callback/n8n` : Callback résultat n8n
- `GET /health` : Health check
- `GET /status/{action_id}` : Status action

## Documentation

Voir le fichier `05_SPECIFICATIONS_INTERFACES_JSON_BACKEND.md` pour les spécifications complètes des interfaces JSON de chaque composant.
