# AI Module

## Composants

### STT Engine (Speech-to-Text)
**Responsable:** Omar  
**Priorité:** 🔴 CRITIQUE  
**Temps:** 15h

Convertit audio → texte via Whisper

### TTS Engine (Text-to-Speech)
**Responsable:** Omar  
**Priorité:** 🟠 HAUTE  
**Temps:** 10h

Convertit texte → audio via gTTS

### LLM Client
**Responsable:** Montassar  
**Priorité:** 🔴 CRITIQUE  
**Temps:** 25h

Communication avec LLM pour:
- Conversation (small talk)
- Analyse intentions et extraction entités

## Tests

```bash
pytest backend/ai/tests/ -v
```
