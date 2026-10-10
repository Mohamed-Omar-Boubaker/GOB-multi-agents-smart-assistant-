# 🔔 GOB AI Reminder System

Standalone Python + n8n reminder service with Google Calendar push notifications and MQTT ESP32 alerts.

---

## Folder Structure

```
reminder_system/
├── app.py                  ← FastAPI app (run this)
├── config.py               ← All configuration (reads .env)
├── models.py               ← Pydantic request/response models + ReminderPayload
├── reminder_service.py     ← Core business logic
├── n8n_reminder_client.py  ← HTTP client for n8n webhook
├── tts_stub.py             ← TTS wrapper (real Piper or silent mock)
├── mqtt_stub.py            ← MQTT wrapper (real broker or no-op mock)
├── test_reminder.py        ← Full test suite (60+ tests, no mocks needed)
├── wf_set_reminder.json    ← n8n workflow (import directly)
├── requirements.txt        ← Python dependencies
├── .env.example            ← Config template
└── README.md               ← This file
```

---

## How It Works

```
User says "remind me to call Ahmed tomorrow at 3pm"
                    │
             [AgentCore / you]
                    │
          POST /webhook/reminder
          { title, reminder_datetime, user_id, ... }
                    │
         ┌──────────┴─────────────────────────────────────┐
         │          n8n  wf_set_reminder                  │
         │                                                 │
         │  [Parse & Validate]                             │
         │       │                                         │
         │  ┌────┴──────────────────────┐                  │
         │  ▼                           ▼                  │
         │ [Google Calendar]    [Wait Until Time]           │
         │  Create event +      (zero CPU, persisted)      │
         │  native push notif         │                    │
         │       │               (time reached)            │
         │  [Callback: created]  [Build Alert Payload]      │
         │  POST /callback/n8n        │                    │
         │       │               [Callback: fired]         │
         │  [Respond to Backend] POST /callback/n8n         │
         └──────────────────────────────────────────────── ┘
                    │                      │
             TTS: "Rappel programmé"  TTS: "Rappel! Il est l'heure."
                                           │
                                      MQTT → ESP32
                                      (LED blink + tone)
```

### Why zero polling?

| Mechanism | How |
|---|---|
| **n8n Wait node** | Serialises execution to DB, resumes at exact ms. Zero CPU between create and fire. Survives restarts. |
| **Google Calendar** | Native Android/iOS push notification fires at reminder time. Works even if GOB app is closed. No custom push server needed. |

---

## Quick Start

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### 2 — Configure

```bash
cp .env.example .env
# Edit .env — at minimum set:
#   N8N_WEBHOOK_REMINDER_URL
#   BACKEND_CALLBACK_URL (must be reachable from n8n)
```

### 3 — Run in Demo Mode (no n8n, no TTS, no MQTT needed)

```bash
DEMO_MODE=true python app.py
```

Open http://localhost:8000/docs to see the interactive API.

### 4 — Run tests

```bash
pytest test_reminder.py -v
```

### 5 — Run with full n8n integration

```bash
# Start n8n
docker run -it --rm -p 5678:5678 n8nio/n8n

# Import workflow: n8n UI → Import from file → wf_set_reminder.json
# Configure Google Calendar credentials in n8n
# Activate the workflow

# Start backend
python app.py
```

---

## API Reference

### `POST /webhook/reminder`

Schedule a reminder.

```bash
curl -X POST http://localhost:8000/webhook/reminder \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Call Ahmed",
    "reminder_datetime": "2026-04-28T15:00:00+01:00",
    "user_id": "user_001",
    "language": "fr"
  }'
```

**Response:**
```json
{
  "status": "success",
  "action_id": "reminder_abc123",
  "message": "Rappel programmé : \"Call Ahmed\" le ...",
  "reminder_datetime": "2026-04-28T15:00:00+01:00",
  "gcal_event_id": "abc123xyz",
  "gcal_html_link": "https://calendar.google.com/event?eid=..."
}
```

---

### `POST /callback/n8n`

Called automatically by n8n. Two event types:

**`reminder_created`** — immediately after GCal event creation:
```json
{
  "action_id": "reminder_abc123",
  "status": "confirmed",
  "event": "reminder_created",
  "confirm_message": "Rappel programmé : \"Call Ahmed\"",
  "user_id": "user_001",
  "language": "fr"
}
```

**`reminder_fired`** — at exact reminder datetime:
```json
{
  "action_id": "reminder_abc123",
  "status": "fired",
  "event": "reminder_fired",
  "tts_text": "Rappel ! Call Ahmed. Il est l'heure.",
  "mqtt_topic": "device/reminder/user_001",
  "mqtt_payload": "{\"type\":\"reminder_alert\",\"led_pattern\":\"alert_blink\"}",
  "user_id": "user_001",
  "fired_at": "2026-04-28T15:00:00.000Z"
}
```

---

### `GET /reminders`

List all reminders in memory (debug).

### `DELETE /reminders/{action_id}`

Remove from in-memory store (debug). Does not cancel n8n execution.

### `GET /health`

```json
{
  "status": "ok",
  "n8n_enabled": true,
  "mqtt_connected": false,
  "tts_enabled": true,
  "demo_mode": false
}
```

---

## Testing

Tests run fully offline — all external services are mocked automatically.

```bash
# All tests
pytest test_reminder.py -v

# With coverage
pytest test_reminder.py -v --cov=. --cov-report=term-missing

# Specific test class
pytest test_reminder.py::TestHandleFiredCallback -v

# Single test
pytest test_reminder.py::TestN8NReminderClient::test_mock_mode_returns_mock_status -v
```

### Test Coverage

| Class | Tests | What's covered |
|---|---|---|
| `TestReminderPayload` | 8 | Serialization, auto-ID, defaults, normalization |
| `TestValidateDatetime` | 8 | Future check, past, near-future buffer, formats |
| `TestBuildPayload` | 7 | Entity parsing, fallbacks, missing datetime |
| `TestN8NReminderClient` | 8 | Mock mode, validation, HTTP 200/500, timeout |
| `TestReminderServiceSchedule` | 4 | End-to-end dispatch, error propagation |
| `TestHandleCreatedCallback` | 8 | TTS call, audio return, graceful failure |
| `TestHandleFiredCallback` | 8 | TTS + MQTT publish, QoS, disconnect case |
| `TestHealthEndpoint` | 3 | Liveness, demo mode flag |
| `TestScheduleReminderEndpoint` | 9 | 200, 422, language validation, store tracking |
| `TestN8NCallbackEndpoint` | 6 | created, fired, unknown event, missing field |
| `TestRemindersStoreEndpoints` | 5 | List, 404, delete, post-delete absence |
| `TestTTSStub` | 7 | WAV shape, base64, emoji cleanup, fallback |
| `TestMQTTStub` | 5 | Disabled mode, topic, publish shape |
| **Total** | **86** | |

---

## Integrating into GOB AgentCore

In `backend/agent/agent_core.py`, inside `_execute_confirmed_action()`:

```python
if intent == "set_reminder":
    from reminder_service import ReminderService

    payload = ReminderService.build_payload(
        entities     = action_json["payload"],
        user_id      = user_id,
        action_id    = action_json["action_id"],
        language     = language,
        callback_url = f"http://localhost:{Config.PORT}/callback/n8n",
    )
    result = await self.reminder_service.schedule(payload)
    return {
        "type":     "action",
        "status":   "confirmed",
        "response": result.get("message", "Rappel programmé."),
    }
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Backend server port |
| `N8N_WEBHOOK_REMINDER_URL` | `http://localhost:5678/webhook/reminder` | n8n webhook URL |
| `ENABLE_N8N_INTEGRATION` | `true` | Set `false` for mock mode |
| `BACKEND_CALLBACK_URL` | `http://localhost:8000/callback/n8n` | URL n8n calls back to |
| `ENABLE_TTS` | `true` | Set `false` to silence TTS |
| `TTS_HOST` / `TTS_PORT` | `localhost:10200` | Piper TTS server |
| `ENABLE_MQTT_INTEGRATION` | `true` | Set `false` to skip MQTT |
| `MQTT_BROKER` / `MQTT_PORT` | `localhost:1883` | Mosquitto broker |
| `DEFAULT_TIMEZONE` | `Africa/Tunis` | Fallback timezone |
| `DEMO_MODE` | `false` | `true` disables ALL external calls |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `422 Unprocessable Entity` on POST | Check `reminder_datetime` is ISO 8601 and at least 30s in future |
| n8n returns 404 | Workflow not imported or not activated |
| GCal event not created | Re-authorize Google Calendar credentials in n8n |
| Callback not received | `BACKEND_CALLBACK_URL` not reachable from n8n — use LAN IP or ngrok |
| TTS silent | `ENABLE_TTS=false` or Piper server not running |
| MQTT not publishing | Broker unreachable — check `MQTT_BROKER` |

---

*GOB AI Embedded Agent — Reminder System v1.0 — April 2026*
