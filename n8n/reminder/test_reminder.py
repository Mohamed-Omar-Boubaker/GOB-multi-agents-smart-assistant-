"""
test_reminder.py
─────────────────────────────────────────────────────────────────────────────
Complete standalone test suite for the GOB AI Reminder System.

Covers
──────
  1. ReminderPayload           — serialization & auto-ID
  2. ReminderService validation — datetime rules
  3. ReminderService.build_payload — entity parsing
  4. N8NReminderClient         — mock mode, validation, HTTP success/failure
  5. ReminderService.schedule  — end-to-end with mocked n8n
  6. handle_created_callback   — TTS call, state update, graceful TTS failure
  7. handle_fired_callback     — TTS + MQTT publish, MQTT disconnected case
  8. FastAPI /health            — liveness
  9. FastAPI POST /webhook/reminder — success, 422 validation, 502 n8n error
 10. FastAPI POST /callback/n8n    — created event, fired event, unknown event
 11. FastAPI GET  /reminders       — store listing
 12. FastAPI DELETE /reminders/{id} — cancel flow
 13. TTSStub                   — mock audio shape
 14. MQTTStub                  — disabled mode, publish shape

Run
───
  pytest test_reminder.py -v
  pytest test_reminder.py -v --cov=. --cov-report=term-missing
"""

from __future__ import annotations

import asyncio
import base64
import json
import struct
import sys
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Make sure all local modules resolve when running from this folder ─────────
sys.path.insert(0, os.path.dirname(__file__))

# ─── Datetime helpers ─────────────────────────────────────────────────────────

def future_dt(minutes: int = 60) -> str:
    """ISO 8601 datetime N minutes in the future (UTC with offset)."""
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def past_dt(minutes: int = 5) -> str:
    """ISO 8601 datetime N minutes in the past."""
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


def near_future_dt(seconds: int = 20) -> str:
    """ISO 8601 datetime N seconds in the future (< 30s buffer → should fail)."""
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


# ─── Async helper ─────────────────────────────────────────────────────────────

def run(coro):
    """Run an async coroutine in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ══════════════════════════════════════════════════════════════════════════════
# 1. ReminderPayload
# ══════════════════════════════════════════════════════════════════════════════

class TestReminderPayload:

    def test_to_dict_contains_all_required_fields(self):
        from models import ReminderPayload
        p = ReminderPayload(title="Call Ahmed", reminder_datetime=future_dt(), user_id="u1")
        d = p.to_dict()
        for key in ("title", "reminder_datetime", "user_id", "action_id",
                    "timezone", "language", "callback_url"):
            assert key in d, f"Missing key: {key}"

    def test_auto_generates_action_id_with_prefix(self):
        from models import ReminderPayload
        p = ReminderPayload(title="X", reminder_datetime=future_dt(), user_id="u1")
        assert p.action_id.startswith("reminder_")

    def test_explicit_action_id_preserved(self):
        from models import ReminderPayload
        p = ReminderPayload(title="X", reminder_datetime=future_dt(),
                            user_id="u1", action_id="custom_id_123")
        assert p.action_id == "custom_id_123"

    def test_title_stripped(self):
        from models import ReminderPayload
        p = ReminderPayload(title="  Call Ahmed  ", reminder_datetime=future_dt(), user_id="u1")
        assert p.title == "Call Ahmed"

    def test_default_timezone(self):
        from models import ReminderPayload
        p = ReminderPayload(title="X", reminder_datetime=future_dt(), user_id="u1")
        assert p.timezone == "Africa/Tunis"

    def test_default_language(self):
        from models import ReminderPayload
        p = ReminderPayload(title="X", reminder_datetime=future_dt(), user_id="u1")
        assert p.language == "fr"

    def test_language_normalized_to_lowercase(self):
        from models import ReminderPayload
        p = ReminderPayload(title="X", reminder_datetime=future_dt(),
                            user_id="u1", language="FR")
        assert p.language == "fr"

    def test_repr_contains_id_and_title(self):
        from models import ReminderPayload
        p = ReminderPayload(title="Meeting", reminder_datetime=future_dt(),
                            user_id="u1", action_id="abc")
        assert "abc" in repr(p)
        assert "Meeting" in repr(p)


# ══════════════════════════════════════════════════════════════════════════════
# 2. ReminderService — datetime validation
# ══════════════════════════════════════════════════════════════════════════════

class TestValidateDatetime:

    def test_valid_future_datetime_passes(self):
        from reminder_service import ReminderService
        ReminderService._validate_datetime(future_dt(60))  # should not raise

    def test_past_datetime_raises(self):
        from reminder_service import ReminderService
        with pytest.raises(ValueError, match="future"):
            ReminderService._validate_datetime(past_dt(5))

    def test_near_future_under_buffer_raises(self):
        from reminder_service import ReminderService
        with pytest.raises(ValueError, match="future"):
            ReminderService._validate_datetime(near_future_dt(15))

    def test_invalid_string_raises(self):
        from reminder_service import ReminderService
        with pytest.raises(ValueError, match="Invalid ISO 8601"):
            ReminderService._validate_datetime("tomorrow at 3pm")

    def test_empty_string_raises(self):
        from reminder_service import ReminderService
        with pytest.raises(ValueError, match="required"):
            ReminderService._validate_datetime("")

    def test_none_raises(self):
        from reminder_service import ReminderService
        with pytest.raises((ValueError, AttributeError)):
            ReminderService._validate_datetime(None)

    def test_accepts_z_suffix(self):
        from reminder_service import ReminderService
        dt = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ReminderService._validate_datetime(dt)  # should not raise

    def test_accepts_offset_notation(self):
        from reminder_service import ReminderService
        ReminderService._validate_datetime("2099-01-01T10:00:00+01:00")


# ══════════════════════════════════════════════════════════════════════════════
# 3. ReminderService.build_payload — entity parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestBuildPayload:

    def test_builds_from_minimal_entities(self):
        from reminder_service import ReminderService
        p = ReminderService.build_payload(
            entities={"title": "Doctor", "reminder_datetime": future_dt(120)},
            user_id="u1",
        )
        assert p.title == "Doctor"

    def test_fallback_to_reminder_title_key(self):
        from reminder_service import ReminderService
        p = ReminderService.build_payload(
            entities={"reminder_title": "Meeting", "reminder_datetime": future_dt(60)},
            user_id="u1",
        )
        assert p.title == "Meeting"

    def test_default_title_when_missing(self):
        from reminder_service import ReminderService
        p = ReminderService.build_payload(
            entities={"reminder_datetime": future_dt(60)}, user_id="u1"
        )
        assert p.title == "Rappel"

    def test_raises_if_no_datetime(self):
        from reminder_service import ReminderService
        with pytest.raises(ValueError, match="missing 'reminder_datetime'"):
            ReminderService.build_payload({"title": "X"}, user_id="u1")

    def test_accepts_datetime_key_alias(self):
        from reminder_service import ReminderService
        p = ReminderService.build_payload(
            entities={"title": "X", "datetime": future_dt(60)}, user_id="u1"
        )
        assert p.reminder_datetime is not None

    def test_description_passed_through(self):
        from reminder_service import ReminderService
        p = ReminderService.build_payload(
            entities={"title": "T", "reminder_datetime": future_dt(60), "description": "Note"},
            user_id="u1",
        )
        assert p.description == "Note"

    def test_custom_action_id(self):
        from reminder_service import ReminderService
        p = ReminderService.build_payload(
            entities={"title": "T", "reminder_datetime": future_dt(60)},
            user_id="u1",
            action_id="my_action",
        )
        assert p.action_id == "my_action"


# ══════════════════════════════════════════════════════════════════════════════
# 4. N8NReminderClient
# ══════════════════════════════════════════════════════════════════════════════

class TestN8NReminderClient:

    def _valid_payload(self, **kwargs):
        base = {
            "title":             "Test reminder",
            "reminder_datetime": future_dt(60),
            "user_id":           "user_001",
            "action_id":         "action_123",
            "callback_url":      "http://localhost:8000/callback/n8n",
            "language":          "fr",
        }
        base.update(kwargs)
        return base

    def test_mock_mode_returns_mock_status(self):
        from n8n_reminder_client import N8NReminderClient
        client = N8NReminderClient(enabled=False)
        result = run(client.send_reminder(self._valid_payload()))
        assert result["status"] == "mock"

    def test_mock_mode_contains_action_id(self):
        from n8n_reminder_client import N8NReminderClient
        client = N8NReminderClient(enabled=False)
        result = run(client.send_reminder(self._valid_payload()))
        assert result["action_id"] == "action_123"

    def test_mock_contains_gcal_event_id(self):
        from n8n_reminder_client import N8NReminderClient
        client = N8NReminderClient(enabled=False)
        result = run(client.send_reminder(self._valid_payload()))
        assert "gcal_event_id" in result

    def test_validation_fails_missing_title(self):
        from n8n_reminder_client import N8NReminderClient
        client = N8NReminderClient(enabled=False)
        payload = self._valid_payload()
        del payload["title"]
        with pytest.raises(ValueError, match="missing required fields"):
            run(client.send_reminder(payload))

    def test_validation_fails_missing_datetime(self):
        from n8n_reminder_client import N8NReminderClient
        client = N8NReminderClient(enabled=False)
        payload = self._valid_payload()
        del payload["reminder_datetime"]
        with pytest.raises(ValueError):
            run(client.send_reminder(payload))

    def test_validation_fails_empty_datetime(self):
        from n8n_reminder_client import N8NReminderClient
        client = N8NReminderClient(enabled=False)
        with pytest.raises(ValueError, match="empty"):
            run(client.send_reminder(self._valid_payload(reminder_datetime="")))

    @patch("httpx.AsyncClient.post")
    def test_live_mode_200_response(self, mock_post):
        from n8n_reminder_client import N8NReminderClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success", "action_id": "action_123", "gcal_event_id": "gcal_abc"
        }
        mock_post.return_value = mock_response

        client = N8NReminderClient(webhook_url="http://n8n:5678/webhook/reminder", enabled=True)
        result = run(client.send_reminder(self._valid_payload()))
        assert result["status"] == "success"
        assert result["gcal_event_id"] == "gcal_abc"

    @patch("httpx.AsyncClient.post")
    def test_live_mode_non200_raises(self, mock_post):
        from n8n_reminder_client import N8NReminderClient
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        client = N8NReminderClient(webhook_url="http://n8n:5678/webhook/reminder", enabled=True)
        with pytest.raises(RuntimeError, match="HTTP 500"):
            run(client.send_reminder(self._valid_payload()))

    @patch("httpx.AsyncClient.post", side_effect=__import__("httpx").TimeoutException(""))
    def test_timeout_raises_runtime_error(self, _):
        from n8n_reminder_client import N8NReminderClient
        client = N8NReminderClient(webhook_url="http://n8n:5678/webhook/reminder",
                                   timeout=1, enabled=True)
        with pytest.raises(RuntimeError, match="timed out"):
            run(client.send_reminder(self._valid_payload()))


# ══════════════════════════════════════════════════════════════════════════════
# 5. ReminderService.schedule — end-to-end with mocked n8n
# ══════════════════════════════════════════════════════════════════════════════

class TestReminderServiceSchedule:

    def _make_service(self, n8n_response=None):
        from reminder_service import ReminderService
        mock_n8n = MagicMock()
        mock_n8n.send_reminder = AsyncMock(
            return_value=n8n_response or {
                "status": "success", "action_id": "a1", "gcal_event_id": "gcal_1"
            }
        )
        return ReminderService(n8n_client=mock_n8n), mock_n8n

    def _payload(self, **kwargs):
        from models import ReminderPayload
        defaults = dict(title="Test", reminder_datetime=future_dt(90), user_id="u1")
        defaults.update(kwargs)
        return ReminderPayload(**defaults)

    def test_schedule_returns_n8n_response(self):
        svc, _ = self._make_service()
        result = run(svc.schedule(self._payload()))
        assert result["status"] == "success"

    def test_schedule_calls_n8n_with_correct_fields(self):
        svc, mock_n8n = self._make_service()
        run(svc.schedule(self._payload(title="Call Ahmed")))
        call_kwargs = mock_n8n.send_reminder.call_args[0][0]
        assert call_kwargs["title"] == "Call Ahmed"

    def test_schedule_past_datetime_raises(self):
        svc, _ = self._make_service()
        with pytest.raises(ValueError, match="future"):
            run(svc.schedule(self._payload(reminder_datetime=past_dt())))

    def test_schedule_propagates_n8n_runtime_error(self):
        from reminder_service import ReminderService
        mock_n8n = MagicMock()
        mock_n8n.send_reminder = AsyncMock(side_effect=RuntimeError("n8n unreachable"))
        svc = ReminderService(n8n_client=mock_n8n)
        with pytest.raises(RuntimeError, match="n8n unreachable"):
            run(svc.schedule(self._payload()))


# ══════════════════════════════════════════════════════════════════════════════
# 6. handle_created_callback
# ══════════════════════════════════════════════════════════════════════════════

class TestHandleCreatedCallback:

    def _data(self, **kwargs):
        base = {
            "action_id":       "a1",
            "confirm_message": "Rappel programmé : Call Ahmed",
            "user_id":         "user_001",
            "language":        "fr",
            "gcal_event_id":   "gcal_1",
        }
        base.update(kwargs)
        return base

    def _make_service(self, tts=None, mqtt=None):
        from reminder_service import ReminderService
        return ReminderService(n8n_client=MagicMock(), tts=tts, mqtt=mqtt)

    def test_returns_ok_status(self):
        svc = self._make_service()
        result = run(svc.handle_created_callback(self._data()))
        assert result["status"] == "ok"
        assert result["event"] == "reminder_created"

    def test_returns_action_id(self):
        svc = self._make_service()
        result = run(svc.handle_created_callback(self._data()))
        assert result["action_id"] == "a1"

    def test_calls_tts_with_correct_text(self):
        mock_tts = MagicMock()
        mock_tts.synthesize.return_value = MagicMock(audio_data="base64audio==")
        svc = self._make_service(tts=mock_tts)
        run(svc.handle_created_callback(self._data()))
        mock_tts.synthesize.assert_called_once_with("Rappel programmé : Call Ahmed", "fr")

    def test_audio_returned_when_tts_available(self):
        mock_tts = MagicMock()
        mock_tts.synthesize.return_value = MagicMock(audio_data="audio_base64==")
        svc = self._make_service(tts=mock_tts)
        result = run(svc.handle_created_callback(self._data()))
        assert result["audio"] == "audio_base64=="

    def test_audio_none_when_no_tts(self):
        svc = self._make_service(tts=None)
        result = run(svc.handle_created_callback(self._data()))
        assert result["audio"] is None

    def test_tts_failure_does_not_crash(self):
        mock_tts = MagicMock()
        mock_tts.synthesize.side_effect = Exception("TTS server down")
        svc = self._make_service(tts=mock_tts)
        result = run(svc.handle_created_callback(self._data()))
        assert result["status"] == "ok"
        assert result["audio"] is None

    def test_uses_default_message_when_none_provided(self):
        from reminder_service import ReminderService
        svc = self._make_service()
        result = run(svc.handle_created_callback({
            "action_id": "a1", "user_id": "u1", "language": "fr", "title": "Call Ahmed"
        }))
        assert "Call Ahmed" in result["confirm_message"]

    def test_english_default_message(self):
        from reminder_service import ReminderService
        svc = self._make_service()
        result = run(svc.handle_created_callback({
            "action_id": "a1", "user_id": "u1", "language": "en", "title": "Test"
        }))
        assert "Reminder" in result["confirm_message"]


# ══════════════════════════════════════════════════════════════════════════════
# 7. handle_fired_callback
# ══════════════════════════════════════════════════════════════════════════════

class TestHandleFiredCallback:

    def _data(self, **kwargs):
        base = {
            "action_id":    "a1",
            "tts_text":     "Rappel ! Call Ahmed. Il est l'heure.",
            "mqtt_topic":   "device/reminder/user_001",
            "mqtt_payload": json.dumps({
                "type": "reminder_alert", "led_pattern": "alert_blink", "duration_ms": 5000
            }),
            "user_id":      "user_001",
            "language":     "fr",
            "fired_at":     "2026-04-28T15:00:00Z",
        }
        base.update(kwargs)
        return base

    def _make_service(self, tts=None, mqtt=None):
        from reminder_service import ReminderService
        return ReminderService(n8n_client=MagicMock(), tts=tts, mqtt=mqtt)

    def test_returns_ok_status(self):
        svc = self._make_service()
        result = run(svc.handle_fired_callback(self._data()))
        assert result["status"] == "ok"
        assert result["event"] == "reminder_fired"

    def test_calls_tts_with_correct_text(self):
        mock_tts = MagicMock()
        mock_tts.synthesize.return_value = MagicMock(audio_data="audio==")
        svc = self._make_service(tts=mock_tts)
        run(svc.handle_fired_callback(self._data()))
        mock_tts.synthesize.assert_called_once()
        args = mock_tts.synthesize.call_args[0]
        assert "Call Ahmed" in args[0]

    def test_publishes_mqtt_when_connected(self):
        mock_tts = MagicMock()
        mock_tts.synthesize.return_value = MagicMock(audio_data="audio==")
        mock_mqtt = MagicMock()
        mock_mqtt.is_connected.return_value = True
        svc = self._make_service(tts=mock_tts, mqtt=mock_mqtt)
        result = run(svc.handle_fired_callback(self._data()))
        mock_mqtt.publish.assert_called_once()
        assert result["mqtt_published"] is True

    def test_mqtt_topic_correct(self):
        mock_tts = MagicMock()
        mock_tts.synthesize.return_value = MagicMock(audio_data="a==")
        mock_mqtt = MagicMock()
        mock_mqtt.is_connected.return_value = True
        svc = self._make_service(tts=mock_tts, mqtt=mock_mqtt)
        run(svc.handle_fired_callback(self._data()))
        topic = mock_mqtt.publish.call_args[0][0]
        assert topic == "device/reminder/user_001"

    def test_mqtt_qos_is_1(self):
        mock_tts = MagicMock()
        mock_tts.synthesize.return_value = MagicMock(audio_data="a==")
        mock_mqtt = MagicMock()
        mock_mqtt.is_connected.return_value = True
        svc = self._make_service(tts=mock_tts, mqtt=mock_mqtt)
        run(svc.handle_fired_callback(self._data()))
        kwargs = mock_mqtt.publish.call_args[1]
        assert kwargs.get("qos") == 1

    def test_skips_mqtt_when_disconnected(self):
        mock_mqtt = MagicMock()
        mock_mqtt.is_connected.return_value = False
        svc = self._make_service(mqtt=mock_mqtt)
        result = run(svc.handle_fired_callback(self._data()))
        mock_mqtt.publish.assert_not_called()
        assert result["mqtt_published"] is False

    def test_mqtt_error_does_not_crash(self):
        mock_tts = MagicMock()
        mock_tts.synthesize.return_value = MagicMock(audio_data="a==")
        mock_mqtt = MagicMock()
        mock_mqtt.is_connected.return_value = True
        mock_mqtt.publish.side_effect = Exception("broker gone")
        svc = self._make_service(tts=mock_tts, mqtt=mock_mqtt)
        result = run(svc.handle_fired_callback(self._data()))
        assert result["status"] == "ok"
        assert result["mqtt_published"] is False

    def test_uses_default_alert_when_no_tts_text(self):
        svc = self._make_service()
        data = self._data()
        del data["tts_text"]
        data["title"] = "Meeting"
        result = run(svc.handle_fired_callback(data))
        assert result["status"] == "ok"


# ══════════════════════════════════════════════════════════════════════════════
# 8–12. FastAPI endpoints
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def test_client():
    """
    Create a FastAPI TestClient with all external services mocked.
    n8n, TTS and MQTT are replaced with mock stubs so tests run offline.
    """
    import os
    os.environ["ENABLE_N8N_INTEGRATION"]   = "false"
    os.environ["ENABLE_TTS"]               = "false"
    os.environ["ENABLE_MQTT_INTEGRATION"]  = "false"
    os.environ["DEMO_MODE"]                = "true"

    # Re-import config with env vars applied
    import importlib
    import config as cfg_module
    importlib.reload(cfg_module)

    from fastapi.testclient import TestClient
    from app import app
    with TestClient(app) as client:
        yield client


class TestHealthEndpoint:

    def test_health_returns_200(self, test_client):
        resp = test_client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_ok(self, test_client):
        resp = test_client.get("/health")
        assert resp.json()["status"] == "ok"

    def test_health_shows_demo_mode(self, test_client):
        resp = test_client.get("/health")
        assert resp.json()["demo_mode"] is True


class TestScheduleReminderEndpoint:

    def _body(self, **kwargs):
        base = {
            "title":             "Call Ahmed",
            "reminder_datetime": future_dt(120),
            "user_id":           "user_001",
            "language":          "fr",
        }
        base.update(kwargs)
        return base

    def test_success_returns_200(self, test_client):
        resp = test_client.post("/webhook/reminder", json=self._body())
        assert resp.status_code == 200

    def test_success_contains_action_id(self, test_client):
        resp = test_client.post("/webhook/reminder", json=self._body())
        assert "action_id" in resp.json()

    def test_success_contains_status(self, test_client):
        resp = test_client.post("/webhook/reminder", json=self._body())
        data = resp.json()
        assert data["status"] in ("success", "mock")

    def test_past_datetime_returns_422(self, test_client):
        resp = test_client.post("/webhook/reminder", json=self._body(
            reminder_datetime=past_dt()
        ))
        assert resp.status_code == 422

    def test_missing_title_returns_422(self, test_client):
        body = self._body()
        del body["title"]
        resp = test_client.post("/webhook/reminder", json=body)
        assert resp.status_code == 422

    def test_missing_datetime_returns_422(self, test_client):
        body = self._body()
        del body["reminder_datetime"]
        resp = test_client.post("/webhook/reminder", json=body)
        assert resp.status_code == 422

    def test_invalid_language_returns_422(self, test_client):
        resp = test_client.post("/webhook/reminder", json=self._body(language="de"))
        assert resp.status_code == 422

    def test_reminder_appears_in_store(self, test_client):
        resp = test_client.post("/webhook/reminder", json=self._body(
            title="Store test reminder"
        ))
        assert resp.status_code == 200
        action_id = resp.json()["action_id"]
        store_resp = test_client.get("/reminders")
        ids = [r["action_id"] for r in store_resp.json()["reminders"]]
        assert action_id in ids

    def test_english_language_accepted(self, test_client):
        resp = test_client.post("/webhook/reminder", json=self._body(language="en"))
        assert resp.status_code == 200

    def test_arabic_language_accepted(self, test_client):
        resp = test_client.post("/webhook/reminder", json=self._body(language="ar"))
        assert resp.status_code == 200


class TestN8NCallbackEndpoint:

    def test_reminder_created_returns_200(self, test_client):
        resp = test_client.post("/callback/n8n", json={
            "action_id":       "a1",
            "status":          "confirmed",
            "event":           "reminder_created",
            "confirm_message": "Rappel programmé.",
            "user_id":         "u1",
            "language":        "fr",
        })
        assert resp.status_code == 200

    def test_reminder_created_event_in_response(self, test_client):
        resp = test_client.post("/callback/n8n", json={
            "action_id": "a1", "status": "confirmed",
            "event": "reminder_created", "user_id": "u1", "language": "fr",
        })
        assert resp.json()["event"] == "reminder_created"

    def test_reminder_fired_returns_200(self, test_client):
        resp = test_client.post("/callback/n8n", json={
            "action_id":   "a1",
            "status":      "fired",
            "event":       "reminder_fired",
            "tts_text":    "Rappel ! Il est l'heure.",
            "mqtt_topic":  "device/reminder/u1",
            "mqtt_payload": "{}",
            "user_id":     "u1",
            "language":    "fr",
            "fired_at":    "2026-04-28T15:00:00Z",
        })
        assert resp.status_code == 200

    def test_reminder_fired_event_in_response(self, test_client):
        resp = test_client.post("/callback/n8n", json={
            "action_id": "a1", "status": "fired",
            "event": "reminder_fired", "user_id": "u1", "language": "fr",
        })
        assert resp.json()["event"] == "reminder_fired"

    def test_unknown_event_returns_200_ignored(self, test_client):
        resp = test_client.post("/callback/n8n", json={
            "action_id": "a1", "status": "unknown",
            "event": "totally_unknown_event", "user_id": "u1",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    def test_missing_action_id_returns_422(self, test_client):
        resp = test_client.post("/callback/n8n", json={
            "status": "confirmed", "event": "reminder_created"
        })
        assert resp.status_code == 422


class TestRemindersStoreEndpoints:

    def test_list_reminders_returns_200(self, test_client):
        resp = test_client.get("/reminders")
        assert resp.status_code == 200
        assert "reminders" in resp.json()

    def test_list_reminders_total_field(self, test_client):
        resp = test_client.get("/reminders")
        assert "total" in resp.json()

    def test_delete_nonexistent_returns_404(self, test_client):
        resp = test_client.delete("/reminders/nonexistent_action_id_xyz")
        assert resp.status_code == 404

    def test_delete_existing_reminder(self, test_client):
        # Schedule first
        sched = test_client.post("/webhook/reminder", json={
            "title": "Delete test", "reminder_datetime": future_dt(60),
            "user_id": "u1", "language": "fr",
        })
        action_id = sched.json()["action_id"]

        # Delete it
        del_resp = test_client.delete(f"/reminders/{action_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"

    def test_deleted_reminder_gone_from_store(self, test_client):
        sched = test_client.post("/webhook/reminder", json={
            "title": "Gone soon", "reminder_datetime": future_dt(60),
            "user_id": "u1", "language": "fr",
        })
        action_id = sched.json()["action_id"]
        test_client.delete(f"/reminders/{action_id}")

        store = test_client.get("/reminders")
        ids = [r["action_id"] for r in store.json()["reminders"]]
        assert action_id not in ids


# ══════════════════════════════════════════════════════════════════════════════
# 13. TTSStub
# ══════════════════════════════════════════════════════════════════════════════

class TestTTSStub:

    def test_mock_audio_returns_audio_result(self):
        from tts_stub import TTSStub
        stub = TTSStub(enabled=False)
        result = stub.synthesize("Hello", "fr")
        assert result.audio_data is not None
        assert len(result.audio_data) > 0

    def test_mock_audio_is_valid_base64(self):
        from tts_stub import TTSStub
        stub = TTSStub(enabled=False)
        result = stub.synthesize("Test", "fr")
        decoded = base64.b64decode(result.audio_data)
        assert len(decoded) > 0

    def test_mock_audio_is_wav(self):
        from tts_stub import TTSStub
        stub = TTSStub(enabled=False)
        result = stub.synthesize("Test", "en")
        wav = base64.b64decode(result.audio_data)
        assert wav[:4] == b"RIFF"
        assert wav[8:12] == b"WAVE"

    def test_format_is_wav(self):
        from tts_stub import TTSStub
        stub = TTSStub(enabled=False)
        result = stub.synthesize("Test", "fr")
        assert result.audio_format == "wav"

    def test_clean_removes_emojis(self):
        from tts_stub import TTSStub
        cleaned = TTSStub._clean("Rappel ! 🔔 Il est l'heure.")
        assert "🔔" not in cleaned
        assert "Rappel" in cleaned

    def test_tts_falls_back_to_mock_on_connection_error(self):
        from tts_stub import TTSStub
        stub = TTSStub(host="256.256.256.256", port=9999, enabled=True)
        result = stub.synthesize("Test", "fr")
        assert result.audio_data is not None  # mock fallback

    def test_arabic_text_synthesized(self):
        from tts_stub import TTSStub
        stub = TTSStub(enabled=False)
        result = stub.synthesize("تذكير! حان الوقت.", "ar")
        assert result.audio_data is not None


# ══════════════════════════════════════════════════════════════════════════════
# 14. MQTTStub
# ══════════════════════════════════════════════════════════════════════════════

class TestMQTTStub:

    def test_disabled_stub_not_connected(self):
        from mqtt_stub import MQTTStub
        stub = MQTTStub(enabled=False)
        assert stub.is_connected() is False

    def test_disabled_stub_publish_returns_mock(self):
        from mqtt_stub import MQTTStub
        stub = MQTTStub(enabled=False)
        result = stub.publish("device/reminder/u1", {"type": "alert"}, qos=1)
        assert result["status"] == "mock"

    def test_disabled_stub_publish_audio_returns_mock(self):
        from mqtt_stub import MQTTStub
        stub = MQTTStub(enabled=False)
        result = stub.publish_audio("base64audio==", "user_001")
        assert result["status"] == "mock"

    def test_disabled_topic_correct_in_publish_audio(self):
        from mqtt_stub import MQTTStub
        stub = MQTTStub(enabled=False)
        result = stub.publish_audio("b64==", "user_abc")
        assert result["topic"] == "device/audio/user_abc"

    def test_connect_fails_gracefully_on_bad_broker(self):
        from mqtt_stub import MQTTStub
        stub = MQTTStub(broker="256.256.256.256", port=1883, enabled=True)
        connected = stub.connect()
        assert connected is False
        assert stub.is_connected() is False
