"""
reminder_service.py
─────────────────────────────────────────────────────────────────────────────
Core business logic for the Reminder System with ICS calendar support.

Responsibilities
────────────────
1. Validate and enrich reminder payloads.
2. Dispatch to n8n via N8NReminderClient.
3. Handle "reminder_created" callback → TTS confirmation + ICS file generation.
4. Handle "reminder_fired" callback   → TTS alert + MQTT to ESP32.

Fully standalone — inject TTSStub / MQTTStub (or None) via the constructor.
All external calls are guarded with try/except.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class ReminderService:
    """
    Orchestrates the full reminder lifecycle with ICS calendar support.

    Pipeline
    ────────
    schedule()
      └─► n8n webhook (creates ICS file + wait node)
              │
        ┌─────┴──────────────────────────┐
        │                                │
    callback_created                callback_fired
    (immediate after ICS gen)      (at exact datetime)
        │                                │
    TTS confirmation              TTS alert + MQTT ESP32
    """

    def __init__(
        self,
        n8n_client,                    # N8NReminderClient
        tts=None,                      # TTSStub | None
        mqtt=None,                     # MQTTStub | None
        callback_url: str = "http://localhost:8000/callback/n8n",
    ):
        self.n8n_client   = n8n_client
        self.tts          = tts
        self.mqtt         = mqtt
        self.callback_url = callback_url

    # ── Public API ────────────────────────────────────────────────────────

    async def schedule(self, payload) -> dict:
        """
        Validate and dispatch a ReminderPayload to n8n.

        Returns  : dict from n8n (or mock)
        Raises   : ValueError  — validation failed
                   RuntimeError — n8n unreachable
        """
        self._validate_datetime(payload.reminder_datetime)
        payload.callback_url = self.callback_url

        logger.info(
            "ReminderService.schedule",
            extra={"action_id": payload.action_id, "dt": payload.reminder_datetime},
        )
        return await self.n8n_client.send_reminder(payload.to_dict())

    async def handle_created_callback(self, data: dict) -> dict:
        """
        Called when n8n confirms ICS file was generated.
        Speaks a TTS confirmation if TTS is available.
        """
        action_id       = data.get("action_id", "")
        confirm_message = data.get("confirm_message") or self._default_confirm(data)
        user_id         = data.get("user_id", "")
        language        = data.get("language", "fr")
        ics_download_url = data.get("ics_download_url", "")

        logger.info("ReminderService: reminder_created (ICS generated)",
                    extra={"action_id": action_id})

        audio_b64 = self._speak(confirm_message, language, user_id)

        return {
            "status":            "ok",
            "event":             "reminder_created",
            "action_id":         action_id,
            "confirm_message":   confirm_message,
            "audio":             audio_b64,
            "ics_download_url":  ics_download_url,
        }

    async def handle_fired_callback(self, data: dict) -> dict:
        """
        Called when the n8n Wait node wakes up (reminder time reached).
        Speaks TTS alert and publishes MQTT command to ESP32.
        """
        action_id       = data.get("action_id", "")
        tts_text        = data.get("tts_text") or self._default_alert(data)
        mqtt_topic      = data.get("mqtt_topic", f"device/reminder/{data.get('user_id','default')}")
        mqtt_payload_str = data.get("mqtt_payload", "{}")
        user_id         = data.get("user_id", "")
        language        = data.get("language", "fr")

        logger.info("ReminderService: reminder_FIRED", extra={"action_id": action_id})

        result = {"status": "ok", "event": "reminder_fired", "action_id": action_id}

        # 1. Speak TTS alert
        audio_b64 = self._speak(tts_text, language, user_id)
        result["audio"] = audio_b64

        # 2. Publish MQTT alert command to ESP32
        if self.mqtt and self.mqtt.is_connected():
            try:
                import json
                payload_dict = json.loads(mqtt_payload_str) if mqtt_payload_str else {}
                self.mqtt.publish(mqtt_topic, payload_dict, qos=1)
                result["mqtt_published"] = True
                logger.info("MQTT: reminder alert published", extra={"topic": mqtt_topic})
            except Exception as e:
                logger.error(f"MQTT publish error: {e}")
                result["mqtt_published"] = False
                result["mqtt_error"]     = str(e)
        else:
            result["mqtt_published"] = False
            logger.debug("MQTT skipped (not connected or disabled)")

        return result

    # ── Factory ───────────────────────────────────────────────────────────

    @staticmethod
    def build_payload(
        entities: dict,
        user_id: str,
        action_id: Optional[str] = None,
        language: str = "fr",
        callback_url: str = "http://localhost:8000/callback/n8n",
    ):
        """
        Build a ReminderPayload from LLM-extracted entities.

        Expected entity keys (at least one datetime key required):
            title             : str   — reminder label
            reminder_datetime : str   — ISO 8601 datetime string
            description       : str   — optional note
            timezone          : str   — optional, default Africa/Tunis

        Usage
        ─────
            payload = ReminderService.build_payload(
                entities  = {"title": "Call Ahmed", "reminder_datetime": "2026-04-28T15:00:00+01:00"},
                user_id   = "user_001",
                action_id = "action_abc",
                language  = "fr",
            )
        """
        from models import ReminderPayload

        title = (
            entities.get("title")
            or entities.get("reminder_title")
            or "Rappel"
        )

        reminder_datetime = (
            entities.get("reminder_datetime")
            or entities.get("datetime")
            or entities.get("date")
        )

        if not reminder_datetime:
            raise ValueError(
                "Entities missing 'reminder_datetime'. "
                "Ask the user to specify a date and time."
            )

        return ReminderPayload(
            title             = title,
            reminder_datetime = reminder_datetime,
            user_id           = user_id,
            action_id         = action_id,
            description       = entities.get("description", ""),
            timezone          = entities.get("timezone", "Africa/Tunis"),
            language          = language,
            callback_url      = callback_url,
        )

    # ─── Private helpers ───────────────────────────────────────────────────

    def _speak(self, text: str, language: str, user_id: str) -> Optional[str]:
        """Synthesize text via TTS and optionally stream audio to MQTT."""
        if not self.tts:
            return None
        try:
            result = self.tts.synthesize(text, language)
            # Auto-publish TTS audio to MQTT so ESP32 speaker plays it
            if self.mqtt and self.mqtt.is_connected():
                self.mqtt.publish_audio(result.audio_data, user_id)
            return result.audio_data
        except Exception as e:
            logger.warning(f"TTS failed: {e}")
            return None

    @staticmethod
    def _validate_datetime(dt_str: str) -> None:
        """Validates ISO 8601 format and ensures datetime is in the future."""
        if not dt_str:
            raise ValueError("reminder_datetime is required")
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid ISO 8601 datetime: {dt_str!r}")

        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # 30-second buffer
        if dt <= now + timedelta(seconds=30):
            raise ValueError(
                f"reminder_datetime must be at least 30 seconds in the future. Got: {dt_str}"
            )

    @staticmethod
    def _default_confirm(data: dict) -> str:
        title = data.get("title", "votre rappel")
        lang  = data.get("language", "fr")
        ics_link = data.get("ics_download_url", "")
        msgs  = {
            "fr": f"Rappel programmé : {title}. Calendrier: {ics_link}" if ics_link else f"Rappel programmé : {title}",
            "en": f"Reminder set: {title}. Calendar: {ics_link}" if ics_link else f"Reminder set: {title}",
            "ar": f"تم ضبط التذكير: {title}",
        }
        return msgs.get(lang, msgs["fr"])

    @staticmethod
    def _default_alert(data: dict) -> str:
        title = data.get("title", "Rappel")
        lang  = data.get("language", "fr")
        msgs  = {
            "fr": f"Rappel ! {title}. Il est l'heure.",
            "en": f"Reminder! {title}. It's time.",
            "ar": f"تذكير! {title}. حان الوقت.",
        }
        return msgs.get(lang, msgs["fr"])