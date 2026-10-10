# Classifier Module

**Responsable:** Montassar  
**Priorité:** 🔴 CRITIQUE  
**Temps estimé:** 20h

## Rôle

Classifier les commandes utilisateur en deux catégories:
- **Conversation** : Small talk ("Bonjour", "Qui es-tu?")
- **Action** : Exécution réelle ("Allume la lampe", "Envoie un email")

## Fichiers

- `intent_classifier.py` : Classe principale IntentClassifier
- `tests/test_classifier.py` : Tests unitaires

## INPUT/OUTPUT

Voir fichier `05_SPECIFICATIONS_INTERFACES_JSON_BACKEND.md` section "COMPOSANT 1 - Classifier"

## Tests

```bash
pytest backend/classifier/tests/ -v
```

## Dataset de test

| Texte | Classification | Confidence min |
|-------|---------------|----------------|
| "Salut, ça va ?" | conversation | 0.7 |
| "Allume la lampe" | action | 0.8 |
| "Envoie un email" | action | 0.8 |
