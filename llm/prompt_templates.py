"""
Prompt Templates - Templates système pour LLM
Responsable: Équipe Backend

Rôle:
- Définir prompts système pour analyse d'intentions
- Définir prompts pour génération conversationnelle
- Standardiser les formats de réponse

Templates:
1. INTENT_ANALYSIS_PROMPT : Extraction intent + entités
2. CONVERSATION_PROMPT : Génération réponse sociale
3. ENTITY_EXTRACTION_PROMPT : Extraction entités détaillées
"""

# TODO: Implémenter les templates de prompts
# Exemple dans section 4.3 du document architecture

INTENT_ANALYSIS_PROMPT = """
Tu es un assistant intelligent. Analyse la commande suivante et extrais :
- L'intention principale (intent)
- Les entités mentionnées (entities)

Commande : {user_input}

Réponds au format JSON :
{{
  "intent": "...",
  "entities": {{}},
  "confidence": 0.0-1.0
}}
"""

CONVERSATION_PROMPT = """
Tu es un assistant vocal amical et naturel.
Réponds de manière conversationnelle à : {user_input}

Règles :
- Réponses courtes (1-2 phrases)
- Ton naturel et chaleureux
- Pas d'action, juste de la conversation
"""
