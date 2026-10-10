"""
config.py
─────────────────────────────────────────────────────────────────────────────
Centralised configuration for the Reminder System.
Reads from environment variables (or .env file via python-dotenv).
All other modules import from here — never from os.getenv() directly.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Server ─────────────────────────────────────────────────────────────
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # ── n8n ────────────────────────────────────────────────────────────────
    N8N_WEBHOOK_URL: str = os.getenv(
        "N8N_WEBHOOK_REMINDER_URL",
        "http://localhost:5678/webhook/reminder",
    )
    N8N_TIMEOUT: int = int(os.getenv("N8N_REMINDER_TIMEOUT", "15"))
    ENABLE_N8N: bool = os.getenv("ENABLE_N8N_INTEGRATION", "true").lower() == "true"

    # ── Callback ───────────────────────────────────────────────────────────
    # URL n8n will POST back to when reminder is created / fired.
    # Must be reachable FROM n8n (use ngrok or LAN IP when testing remotely).
    CALLBACK_URL: str = os.getenv(
        "BACKEND_CALLBACK_URL",
        f"http://localhost:{os.getenv('PORT', '8000')}/callback/n8n",
    )

    # ── MQTT ───────────────────────────────────────────────────────────────
    MQTT_BROKER: str  = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT: int    = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_USER: str    = os.getenv("MQTT_USERNAME", "")
    MQTT_PASS: str    = os.getenv("MQTT_PASSWORD", "")
    ENABLE_MQTT: bool = os.getenv("ENABLE_MQTT_INTEGRATION", "true").lower() == "true"

    # ── TTS ────────────────────────────────────────────────────────────────
    ENABLE_TTS: bool  = os.getenv("ENABLE_TTS", "true").lower() == "true"
    TTS_HOST: str     = os.getenv("TTS_HOST", "localhost")
    TTS_PORT: int     = int(os.getenv("TTS_PORT", "10200"))

    # ── Defaults ───────────────────────────────────────────────────────────
    DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "Africa/Tunis")
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "fr")

    # ── Demo / Test Mode ───────────────────────────────────────────────────
    # DEMO_MODE=true  → n8n and external services are mocked
    # Automatically true when ENABLE_N8N=false
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
