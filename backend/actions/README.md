# Actions Module

**Responsable:** Amine

## Composants

### Action Builder
**Priorité:** 🔴 CRITIQUE  
**Temps:** 20h

Construit ActionJSON complet à partir de:
- Intent détecté
- Entités extraites
- Commande originale

### Confirmation Handler
**Priorité:** 🟠 HAUTE  
**Temps:** 15h

Gère cycle de confirmation:
1. Génère demande ("Voulez-vous...?")
2. Parse réponse ("oui", "non", "modifier")
3. Met à jour état (CONFIRMED, CANCELED, DRAFT)

## Tests

```bash
pytest backend/actions/tests/ -v
```
