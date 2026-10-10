# Agent Module

**Responsable:** Montassar (+ Amine pour Security)

## Composants

### Agent Core
**Priorité:** 🔴 CRITIQUE  
**Temps:** 30h  
**Responsable:** Montassar

Orchestrateur principal qui utilise TOUS les autres composants.

### State Manager
**Priorité:** 🟠 HAUTE  
**Temps:** 12h  
**Responsable:** Montassar

Gère le cycle de vie des actions (DRAFT → CONFIRMED → EXECUTING → COMPLETED)

### Security Manager
**Priorité:** 🟠 HAUTE  
**Temps:** 10h  
**Responsable:** Amine

Signatures HMAC et tokens JWT

### Logger
**Priorité:** 🟠 HAUTE  
**Temps:** 6h  
**Responsable:** Montassar

Journalisation centralisée JSON structuré

## Tests

```bash
pytest backend/agent/tests/ -v
```
