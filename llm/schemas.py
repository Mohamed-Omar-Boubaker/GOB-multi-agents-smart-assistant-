"""
JSON Schemas - Schémas de validation
Responsable: Équipe Backend

Rôle:
- Définir schémas JSON pour validation
- Valider INPUT (requêtes Backend → LLM)
- Valider OUTPUT (réponses LLM → Backend)
"""

# TODO: Implémenter les schémas de validation

# Schéma INPUT - Analyse d'intention
INTENT_ANALYSIS_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["request_id", "user_input", "language", "mode"],
    "properties": {
        "request_id": {"type": "string"},
        "user_input": {"type": "string"},
        "user_id": {"type": "string"},
        "language": {"type": "string", "enum": ["fr", "en", "ar"]},
        "context": {"type": "object"},
        "mode": {"type": "string", "enum": ["intent_analysis", "conversation"]}
    }
}

# Schéma OUTPUT - Analyse d'intention
INTENT_ANALYSIS_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["request_id", "intent", "confidence"],
    "properties": {
        "request_id": {"type": "string"},
        "intent": {"type": "string"},
        "entities": {"type": "object"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "processing_time_ms": {"type": "integer"}
    }
}

# Schéma OUTPUT - Conversation
CONVERSATION_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["request_id", "response"],
    "properties": {
        "request_id": {"type": "string"},
        "response": {"type": "string"},
        "model_used": {"type": "string"},
        "tokens_used": {"type": "integer"}
    }
}
