"""
models.py
─────────────────────────────────────────────────────────────────────────────
All Pydantic request/response models and internal dataclasses
used across the Reminder System (ICS calendar file support).
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ─── Internal Value Objects ────────────────────────────────────────────────

class ReminderPayload:
    """
    Validated, enriched reminder — ready to be sent to n8n.
    Not a Pydantic model on purpose: built programmatically by the service.
    """

    def __init__(
        self,
        title: str,
        reminder_datetime: str,
        user_id: str,
        action_id: Optional[str] = None,
        description: str = "",
        timezone: str = "Africa/Tunis",
        language: str = "fr",
        callback_url: str = "http://localhost:8000/callback/n8n",
    ):
        import uuid
        self.title             = title.strip()
        self.reminder_datetime = reminder_datetime
        self.user_id           = user_id
        self.action_id         = action_id or f"reminder_{uuid.uuid4().hex[:12]}"
        self.description       = description.strip()
        self.timezone          = timezone
        self.language          = language.lower()
        self.callback_url      = callback_url

    def to_dict(self) -> dict:
        """Serialise to a dict ready for n8n webhook POST body."""
        return {
            "title":             self.title,
            "description":       self.description,
            "reminder_datetime": self.reminder_datetime,
            "user_id":           self.user_id,
            "action_id":         self.action_id,
            "timezone":          self.timezone,
            "language":          self.language,
            "callback_url":      self.callback_url,
        }

    def __repr__(self) -> str:
        return (
            f"ReminderPayload(id={self.action_id!r}, "
            f"title={self.title!r}, dt={self.reminder_datetime!r})"
        )


class AudioResult:
    """Minimal TTS output — mirrors the real TTSEngine.AudioResult."""

    def __init__(self, audio_data: str, audio_format: str = "wav", duration_ms: int = 0):
        self.audio_data   = audio_data
        self.audio_format = audio_format
        self.duration_ms  = duration_ms


# ─── FastAPI Request / Response models ────────────────────────────────────────

class ScheduleReminderRequest(BaseModel):
    """Body for  POST /webhook/reminder"""

    title:             str            = Field(..., min_length=1, max_length=200,
                                             description="Short reminder title")
    reminder_datetime: str            = Field(...,
                                             description="ISO 8601 datetime e.g. 2026-04-28T15:00:00+01:00")
    user_id:           str            = Field(default="default_user")
    action_id:         Optional[str]  = Field(default=None)
    description:       str            = Field(default="")
    timezone:          str            = Field(default="Africa/Tunis")
    language:          str            = Field(default="fr",
                                             description="Response language: fr | en | ar")
    callback_url:      Optional[str]  = Field(default=None,
                                             description="Override callback URL (auto-set if omitted)")

    @field_validator("language")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("fr", "en", "ar"):
            raise ValueError("language must be one of: fr, en, ar")
        return v


class ScheduleReminderResponse(BaseModel):
    status:            str
    action_id:         str
    message:           str
    reminder_datetime: Optional[str] = None
    gcal_event_id:     Optional[str] = None
    gcal_html_link:    Optional[str] = None
    ics_download_url:  Optional[str] = None   # Direct ICS file download link
    audio:             Optional[str] = None    # base64 WAV confirmation speech


class N8NCallbackRequest(BaseModel):
    """
    Body n8n sends to  POST /callback/n8n
    for both 'reminder_created' and 'reminder_fired' events.
    """

    action_id:  str
    status:     str   = Field(description="confirmed | fired | error")
    event:      str   = Field(description="reminder_created | reminder_fired")
    user_id:    str   = "default_user"
    language:   str   = "fr"

    # reminder_created fields
    confirm_message:   Optional[str] = None
    gcal_event_id:     Optional[str] = None
    gcal_html_link:    Optional[str] = None
    ics_download_url:  Optional[str] = None
    reminder_datetime: Optional[str] = None
    title:             Optional[str] = None

    # reminder_fired fields
    tts_text:      Optional[str] = None
    alert_message: Optional[str] = None
    mqtt_topic:    Optional[str] = None
    mqtt_payload:  Optional[str] = None
    fired_at:      Optional[str] = None

    # error field
    error_message: Optional[str] = None


class N8NCallbackResponse(BaseModel):
    status:    str
    event:     str
    action_id: str
    audio:     Optional[str] = None
    detail:    Optional[str] = None