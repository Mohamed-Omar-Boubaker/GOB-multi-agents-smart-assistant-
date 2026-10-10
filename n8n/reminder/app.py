"""
app.py
─────────────────────────────────────────────────────────────────────────────
Standalone FastAPI application for the GOB AI Reminder System
with ICS calendar file support (no Google Calendar credentials needed).

Endpoints
─────────
  GET  /health                              → liveness check
  POST /webhook/reminder                    → schedule a reminder (AgentCore calls this)
  POST /callback/n8n                        → n8n calls back on created / fired events
  GET  /download/reminder/{action_id}.ics   → download ICS calendar file
  GET  /add-to-calendar/{action_id}         → user-friendly calendar add page
  GET  /reminders                           → list all in-memory reminders (debug)
  DELETE /reminders/{action_id}             → cancel a reminder (debug)

Run
───
  python app.py
  or
  uvicorn app:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Dict
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, HTMLResponse

from config import Config
from models import (
    ScheduleReminderRequest,
    ScheduleReminderResponse,
    N8NCallbackRequest,
    N8NCallbackResponse,
    ReminderPayload,
)
from n8n_reminder_client import N8NReminderClient
from reminder_service import ReminderService
from tts_stub import TTSStub
from mqtt_stub import MQTTStub

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("reminder_system")


# ─── In-memory reminder store (for /reminders debug endpoint) ─────────────────
_reminders: Dict[str, dict] = {}


# ─── ICS File Generator ──────────────────────────────────────────────────────
def generate_ics_content(reminder: dict) -> str:
    """Generate standard ICS calendar file content for a reminder."""
    dt_str = reminder["reminder_datetime"].replace('Z', '+00:00')
    dt_start = datetime.fromisoformat(dt_str)
    if dt_start.tzinfo is None:
        dt_start = dt_start.replace(tzinfo=timezone.utc)
    dt_end = dt_start + timedelta(minutes=30)
    
    now_utc = datetime.now(timezone.utc)
    action_id = reminder.get("action_id", "unknown")
    title = reminder.get("title", "GOB Reminder").replace(',', '\\,')
    
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//GOB AI Reminder System//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:GOB Reminders
X-WR-TIMEZONE:Africa/Tunis
BEGIN:VEVENT
UID:{action_id}@gob-reminder
DTSTAMP:{now_utc.strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{dt_start.strftime('%Y%m%dT%H%M%S')}
DTEND:{dt_end.strftime('%Y%m%dT%H%M%S')}
SUMMARY:🔔 {title}
DESCRIPTION:{title}\\n\\nAction ID: {action_id}\\nScheduled: {reminder.get('reminder_datetime')}
LOCATION:GOB AI Reminder System
BEGIN:VALARM
TRIGGER:-PT10M
ACTION:DISPLAY
DESCRIPTION:🔔 {title} in 10 minutes
END:VALARM
BEGIN:VALARM
TRIGGER:-PT5M
ACTION:DISPLAY
DESCRIPTION:⏰ {title} in 5 minutes
END:VALARM
BEGIN:VALARM
TRIGGER:PT0S
ACTION:DISPLAY
DESCRIPTION:⏰ {title} - Time's up!
END:VALARM
END:VEVENT
END:VCALENDAR"""


# ─── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Reminder System starting up (ICS Calendar Mode) ===")
    logger.info(f"  n8n URL    : {Config.N8N_WEBHOOK_URL}")
    logger.info(f"  n8n enabled: {Config.ENABLE_N8N}")
    logger.info(f"  MQTT       : {Config.MQTT_BROKER}:{Config.MQTT_PORT} (enabled={Config.ENABLE_MQTT})")
    logger.info(f"  TTS        : {Config.TTS_HOST}:{Config.TTS_PORT} (enabled={Config.ENABLE_TTS})")
    logger.info(f"  Callback   : {Config.CALLBACK_URL}")
    logger.info(f"  Demo mode  : {Config.DEMO_MODE}")
    logger.info(f"  Calendar   : ICS files (no Google auth required)")

    # ── TTS ──────────────────────────────────────────────────────────────
    tts = TTSStub(
        host    = Config.TTS_HOST,
        port    = Config.TTS_PORT,
        enabled = Config.ENABLE_TTS and not Config.DEMO_MODE,
    )

    # ── MQTT ─────────────────────────────────────────────────────────────
    mqtt = MQTTStub(
        broker   = Config.MQTT_BROKER,
        port     = Config.MQTT_PORT,
        username = Config.MQTT_USER,
        password = Config.MQTT_PASS,
        enabled  = Config.ENABLE_MQTT and not Config.DEMO_MODE,
    )
    if mqtt.enabled:
        mqtt.connect()

    # ── n8n client ────────────────────────────────────────────────────────
    n8n_client = N8NReminderClient(
        webhook_url = Config.N8N_WEBHOOK_URL,
        timeout     = Config.N8N_TIMEOUT,
        enabled     = Config.ENABLE_N8N and not Config.DEMO_MODE,
    )

    # ── Reminder Service ──────────────────────────────────────────────────
    service = ReminderService(
        n8n_client   = n8n_client,
        tts          = tts,
        mqtt         = mqtt,
        callback_url = Config.CALLBACK_URL,
    )

    # Inject into app.state
    app.state.tts             = tts
    app.state.mqtt            = mqtt
    app.state.n8n_client      = n8n_client
    app.state.reminder_service = service

    logger.info("=== Reminder System ready ===")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    logger.info("=== Reminder System shutting down ===")
    if mqtt.enabled:
        mqtt.disconnect()


# ─── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "GOB AI Agent — Reminder System (ICS Calendar)",
    description = (
        "Standalone reminder service with browser/device calendar integration.\n\n"
        "Schedules reminders via n8n + ICS calendar files, "
        "notifies backend via callbacks, speaks TTS and publishes MQTT."
    ),
    version  = "2.0.0",
    lifespan = lifespan,
    docs_url = "/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ─── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code = 500,
        content     = {"detail": f"Internal server error: {str(exc)}"},
    )


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["System"])
async def health(request: Request):
    """Liveness check — returns service status and component states."""
    svc  = request.app.state.reminder_service
    mqtt = request.app.state.mqtt
    return {
        "status":          "ok",
        "service":         "reminder_system_ics",
        "n8n_enabled":     Config.ENABLE_N8N,
        "mqtt_connected":  mqtt.is_connected() if mqtt else False,
        "tts_enabled":     Config.ENABLE_TTS,
        "demo_mode":       Config.DEMO_MODE,
        "calendar_mode":   "ics_files",
    }


@app.post(
    "/webhook/reminder",
    response_model = ScheduleReminderResponse,
    status_code    = 200,
    tags           = ["Reminder"],
    summary        = "Schedule a reminder via n8n + ICS calendar file",
)
async def schedule_reminder(body: ScheduleReminderRequest, request: Request):
    """
    Accepts a reminder intent and dispatches it to n8n.

    **Flow:**
    1. Validates and enriches the payload.
    2. POSTs to n8n webhook.
    3. n8n generates an ICS calendar file (no Google auth needed).
    4. n8n waits until `reminder_datetime`, then POSTs to `/callback/n8n`.
    5. User gets ICS file download link for device calendar integration.
    """
    svc = request.app.state.reminder_service

    payload = ReminderPayload(
        title             = body.title,
        reminder_datetime = body.reminder_datetime,
        user_id           = body.user_id,
        action_id         = body.action_id,
        description       = body.description,
        timezone          = body.timezone,
        language          = body.language,
        callback_url      = body.callback_url or Config.CALLBACK_URL,
    )

    # Track in memory
    _reminders[payload.action_id] = {
        "action_id":         payload.action_id,
        "title":             payload.title,
        "reminder_datetime": payload.reminder_datetime,
        "user_id":           payload.user_id,
        "status":            "pending",
        "ics_url":           f"/download/reminder/{payload.action_id}.ics",
    }

    logger.info(f"POST /webhook/reminder  action_id={payload.action_id}")

    try:
        result = await svc.schedule(payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"n8n dispatch failed: {e}")

    # Update in-memory store
    if payload.action_id in _reminders:
        _reminders[payload.action_id]["status"]        = result.get("status", "pending")
        _reminders[payload.action_id]["gcal_event_id"] = result.get("gcal_event_id")

    # Generate ICS download URL
    ics_url = f"/download/reminder/{payload.action_id}.ics"

    return ScheduleReminderResponse(
        status            = result.get("status", "success"),
        action_id         = result.get("action_id", payload.action_id),
        message           = result.get("message", f"Rappel programmé : {payload.title}"),
        reminder_datetime = body.reminder_datetime,
        gcal_event_id     = result.get("gcal_event_id"),
        gcal_html_link    = result.get("gcal_html_link"),
        ics_download_url  = ics_url,
    )


@app.post(
    "/callback/n8n",
    response_model = N8NCallbackResponse,
    tags           = ["Callback"],
    summary        = "Receive n8n execution callbacks",
)
async def n8n_callback(body: N8NCallbackRequest, request: Request):
    """
    Handles two n8n callback events:

    - **reminder_created** — called immediately after ICS file generation.
      Backend speaks TTS confirmation.

    - **reminder_fired** — called when the Wait node wakes up at reminder time.
      Backend speaks TTS alert and publishes MQTT to ESP32.
    """
    svc = request.app.state.reminder_service
    logger.info(f"POST /callback/n8n  event={body.event}  action_id={body.action_id}")

    data = body.model_dump()

    try:
        if body.event == "reminder_created":
            result = await svc.handle_created_callback(data)
            if body.action_id in _reminders:
                _reminders[body.action_id]["status"]        = "confirmed"
                _reminders[body.action_id]["gcal_event_id"] = body.gcal_event_id
                _reminders[body.action_id]["ics_url"]       = f"/download/reminder/{body.action_id}.ics"

        elif body.event == "reminder_fired":
            result = await svc.handle_fired_callback(data)
            if body.action_id in _reminders:
                _reminders[body.action_id]["status"] = "fired"

        else:
            logger.warning(f"Unknown n8n callback event: {body.event!r}")
            result = {"status": "ignored", "detail": f"Unknown event: {body.event}"}

    except Exception as e:
        logger.error(f"Callback handler error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    return N8NCallbackResponse(
        status    = result.get("status", "ok"),
        event     = body.event,
        action_id = body.action_id,
        audio     = result.get("audio"),
        detail    = result.get("detail"),
    )


@app.get(
    "/download/reminder/{action_id}.ics",
    tags=["Calendar"],
    summary="Download ICS calendar file for device calendar",
)
async def download_ics(action_id: str):
    """
    Generate and serve a downloadable .ics calendar file.
    
    This file can be opened by:
    - iPhone/iPad (Apple Calendar)
    - Android (Google Calendar, Samsung Calendar)
    - Windows (Outlook, Windows Calendar)
    - Mac (Apple Calendar)
    - Linux (GNOME Calendar, KOrganizer)
    
    No login or credentials required.
    """
    if action_id not in _reminders:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    reminder = _reminders[action_id]
    ics_content = generate_ics_content(reminder)
    
    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="gob-reminder-{action_id}.ics"',
            "Cache-Control": "no-cache",
        }
    )


@app.get(
    "/add-to-calendar/{action_id}",
    tags=["Calendar"],
    summary="User-friendly page to download reminder to calendar",
)
async def add_to_calendar_page(action_id: str):
    """Simple web page that triggers calendar download on any device."""
    if action_id not in _reminders:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    reminder = _reminders[action_id]
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Reminder to Calendar - GOB AI</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .card {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 450px;
            width: 100%;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .icon {{ font-size: 64px; margin-bottom: 20px; }}
        h1 {{ color: #333; font-size: 28px; margin-bottom: 10px; }}
        .datetime {{ color: #666; font-size: 18px; margin-bottom: 30px; }}
        .btn {{
            display: inline-block;
            padding: 16px 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            margin: 10px 0;
            transition: transform 0.2s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        .btn:hover {{ transform: translateY(-2px); }}
        .btn:active {{ transform: translateY(0); }}
        .info {{
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
            font-size: 14px;
            color: #666;
            line-height: 1.6;
        }}
        .devices {{ font-size: 24px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🔔</div>
        <h1>{reminder['title']}</h1>
        <div class="datetime">📅 {reminder['reminder_datetime']}</div>
        
        <a class="btn" href="/download/reminder/{action_id}.ics" download>
            📥 Add to Calendar
        </a>
        
        <div class="info">
            <strong>Works on all devices:</strong>
            <div class="devices">
                📱 iPhone &amp; iPad &nbsp; 📱 Android<br>
                💻 Windows &amp; Mac &nbsp; 🐧 Linux
            </div>
            <p style="margin-top: 10px;">
                No account needed. Just tap the button and your calendar app will handle the rest.
            </p>
        </div>
    </div>
    
    <script>
        // Auto-download for convenience
        setTimeout(function() {{
            window.location.href = '/download/reminder/{action_id}.ics';
        }}, 1000);
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=html)


@app.get("/reminders", tags=["Debug"], summary="List all scheduled reminders (in-memory)")
async def list_reminders():
    """Returns all reminders tracked since last server start."""
    return {"total": len(_reminders), "reminders": list(_reminders.values())}


@app.delete(
    "/reminders/{action_id}",
    tags    = ["Debug"],
    summary = "Remove a reminder from the in-memory store",
)
async def delete_reminder(action_id: str):
    """
    Removes a reminder from the local store.
    Note: this does NOT cancel the n8n execution.
    Cancel those manually in n8n.
    """
    if action_id not in _reminders:
        raise HTTPException(status_code=404, detail=f"Reminder {action_id!r} not found")
    deleted = _reminders.pop(action_id)
    return {"status": "deleted", "reminder": deleted}


# ─── Dev entrypoint ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host    = Config.HOST,
        port    = Config.PORT,
        reload  = True,
        log_level = "info",
    )