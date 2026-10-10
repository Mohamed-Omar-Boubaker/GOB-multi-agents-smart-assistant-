# Module LLM - Moteur IA

**Responsable:** Équipe Backend (interface)  
**Priorité:** 🔴 CRITIQUE  
**Phase:** Semaine 4-5 (après Backend Python)

## Rôle

Le module LLM est **uniquement pour la compréhension linguistique**. Il ne déclenche JAMAIS d'action.

**Responsabilités:**
- Analyse du langage naturel
- Extraction d'intentions
- Extraction d'entités
- Génération de réponses conversationnelles

## Architecture

```
llm/
├── llm_server.py          # Serveur HTTP FastAPI
├── prompt_templates.py    # Templates de prompts
├── response_formatter.py  # Formatage réponses
├── schemas.py            # Schémas JSON validation
├── config.py             # Configuration
├── requirements.txt      # Dépendances
├── .env.example          # Template config
└── README.md             # Documentation
```

## API Endpoints

### POST /analyze
Analyse d'intention et extraction d'entités

**INPUT:**
```json
{
  "request_id": "req_002",
  "user_input": "Allume la lampe du salon",
  "language": "fr",
  "mode": "intent_analysis"
}
```

**OUTPUT:**
```json
{
  "request_id": "req_002",
  "intent": "control_iot",
  "entities": {
    "devices": [{"type": "light", "location": "salon", "action": "turn_on"}]
  },
  "confidence": 0.94
}
```

### POST /conversation
Génération de réponse conversationnelle

**INPUT:**
```json
{
  "request_id": "req_003",
  "user_input": "Bonjour, comment vas-tu ?",
  "language": "fr",
  "mode": "conversation"
}
```

**OUTPUT:**
```json
{
  "request_id": "req_003",
  "response": "Bonjour ! Je vais très bien, merci. Comment puis-je t'aider aujourd'hui ?",
  "model_used": "gpt-3.5-turbo"
}
```

## Communication avec Backend Python

Le Backend Python communique avec le module LLM via HTTP :

```python
# Dans backend/ai/llm_client.py
import httpx

response = httpx.post(
    "http://localhost:5000/analyze",
    json={"user_input": "...", "mode": "intent_analysis"}
)
```

## Installation

```bash
cd llm
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec votre API key OpenAI

# Lancer le serveur
python llm_server.py
```

## Tests

```bash
# Test santé
curl http://localhost:5000/health

# Test analyse
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Allume la lampe", "mode": "intent_analysis"}'
```

## Providers supportés

- **OpenAI** (GPT-3.5-turbo, GPT-4)
- **Hugging Face** (modèles open-source)
- **Local** (modèles locaux via transformers)

## Documentation

Voir [01_ARCHITECTURE_TECHNIQUE_COMPLETE_CONSOLIDEE.md](../doc/01_ARCHITECTURE_TECHNIQUE_COMPLETE_CONSOLIDEE.md) Section 4 pour détails complets.
