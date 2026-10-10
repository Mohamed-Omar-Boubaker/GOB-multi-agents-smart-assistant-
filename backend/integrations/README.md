# Integrations Module

## Composants

### n8n Client
**Responsable:** OMAR  
**Priorité:** 🟢 MOYENNE  
**Temps:** infini

Envoie ActionJSON CONFIRMED vers n8n webhook

### MQTT Client
**Responsable:** Omar  
**Priorité:** 🟢 MOYENNE  
**Temps:** 12h

Communication avec ESP32 via MQTT:
- Publier commandes IoT
- Recevoir statuts devices
- Gérer audio (upload/response)

## Tests

```bash
pytest backend/integrations/tests/ -v
```
