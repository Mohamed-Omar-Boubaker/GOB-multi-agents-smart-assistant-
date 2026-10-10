# n8n Module - Workflow Orchestrator

This folder contains n8n workflows used to execute confirmed actions from the backend.

## Maintainers

- Montassar
- Omar

## Role of n8n in This Project

n8n is the controlled execution layer.

It does not decide user intent. It only:

- receives already-validated actions
- routes by intent type
- executes workflow steps
- sends execution status back to the backend

## Folder Contents

```text
n8n/
|- wf_action_router.json
|- wf_send_email.json
|- wf_control_iot.json
|- wf_notification.json
|- wf_set_reminder.json
|- wf_web_search.json
|- wf_log_event.json
|- test_pipeline.ps1
|- GUIDE_IMPORT_WORKFLOWS.md
```

## Main Workflow Design

### 1) Router workflow

Input: confirmed action payload from backend

Pipeline:

1. Webhook receives payload
2. Validate structure and required fields
3. Verify signature if enabled
4. Route by intent
5. Trigger specialized workflow
6. Send callback to backend

### 2) Specialized workflows

- send_email: SMTP-based email flow
- control_iot: publish control commands through MQTT
- set_reminder: schedule reminders and callbacks
- web_search: external information lookup flow
- notification: user notification channels

## Backend Integration

Backend -> n8n:

- webhook endpoint: http://localhost:5678/webhook/action
- configured from backend .env (N8N_WEBHOOK_URL)

n8n -> backend callback:

- POST /callback/n8n

Typical callback body:

```json
{
  "action_id": "act_1001",
  "status": "success",
  "result": {
    "message": "Done"
  },
  "timestamp": "2026-01-20T10:00:20Z"
}
```

## MQTT/ESP32 Interaction

For IoT workflows, n8n can publish commands that are consumed by ESP32 firmware.

Common topics used by firmware:

- gob/robot/state
- gob/audio/tts/request

Acknowledgments from ESP32:

- gob/robot/state/ack
- gob/audio/tts/ack

## Run n8n

### Option 1: Docker

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

### Option 2: npm global

```bash
npm install -g n8n
n8n
```

Open UI: http://localhost:5678

## Import Workflows

1. Open n8n UI.
2. Import workflow files from this folder.
3. Save each workflow.
4. Activate router and required sub-workflows.

Detailed import steps: GUIDE_IMPORT_WORKFLOWS.md

## Configuration

Recommended n8n environment variables:

```env
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=change-me
```

For email workflow:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-app-password
```

For MQTT workflow:

```env
MQTT_BROKER=localhost
MQTT_PORT=1883
```

## Validation and Tests

Run pipeline validation script:

```powershell
./test_pipeline.ps1
```

This script verifies:

- backend availability
- n8n availability
- MQTT connectivity
- action creation and status progression

## Troubleshooting

### Workflow webhook not found

- Ensure workflow is active in n8n UI.
- Check correct webhook path.

### Backend cannot call n8n

- Verify N8N_WEBHOOK_URL in backend .env.
- Check firewall and port 5678.

### MQTT node errors

- Confirm broker host/port and credentials.
- Test broker with a separate MQTT client.
