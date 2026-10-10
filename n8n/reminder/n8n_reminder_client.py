"""
n8n_reminder_client.py
─────────────────────────────────────────────────────────────────────────────
Async HTTP client that dispatches reminder payloads to the n8n
wf_set_reminder webhook.

Responsibilities
────────────────
- Validate payload before sending
- POST to n8n with proper headers
- Handle timeouts, HTTP errors and connection failures
- Return mock response when n8n is disabled (DEMO_MODE / testing)
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class N8NReminderClient:
    """
    Thin async HTTP client for the n8n wf_set_reminder webhook.

    Standalone usage
    ────────────────
        client = N8NReminderClient(
            webhook_url = "http://localhost:5678/webhook/reminder",
            enabled     = True,
        )
        result = await client.send_reminder(payload.to_dict())
    """

    REQUIRED_FIELDS = {"title", "reminder_datetime", "user_id", "callback_url"}

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        timeout: int = 15,
        enabled: bool = True,
    ):
        from config import Config

        self.webhook_url = webhook_url or Config.N8N_WEBHOOK_URL
        self.timeout     = timeout
        self.enabled     = enabled and bool(self.webhook_url)

        if not self.enabled:
            logger.warning(
                "N8NReminderClient: n8n integration DISABLED — running in mock mode"
            )

    # ── Public ────────────────────────────────────────────────────────────

    async def send_reminder(self, payload: dict) -> dict:
        """
        POST reminder payload to n8n webhook.

        Returns
        ───────
        dict  — n8n response body (or mock dict when disabled)

        Raises
        ──────
        ValueError   — required field missing or datetime empty
        RuntimeError — n8n returned non-200 / connection refused / timeout
        """
        self._validate(payload)

        if not self.enabled:
            return self._mock(payload)

        action_id = payload.get("action_id", "unknown")
        logger.info(
            "N8NReminderClient.send_reminder",
            extra={"action_id": action_id, "url": self.webhook_url},
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={
                        "Content-Type":  "application/json",
                        "X-GOB-Source":  "reminder-system",
                        "X-Action-ID":   action_id,
                    },
                )

            if resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"n8n returned HTTP {resp.status_code}: {resp.text[:300]}"
                )

            result = resp.json()
            logger.info(
                "N8NReminderClient: dispatched successfully",
                extra={"action_id": action_id, "n8n_status": result.get("status")},
            )
            return result

        except httpx.TimeoutException:
            raise RuntimeError(f"n8n webhook timed out after {self.timeout}s")
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Cannot connect to n8n at {self.webhook_url}: {e}"
            )

    # ── Private ───────────────────────────────────────────────────────────

    def _validate(self, payload: dict) -> None:
        missing = self.REQUIRED_FIELDS - set(payload.keys())
        if missing:
            raise ValueError(f"Payload missing required fields: {sorted(missing)}")
        if not payload.get("reminder_datetime"):
            raise ValueError("reminder_datetime is empty")

    @staticmethod
    def _mock(payload: dict) -> dict:
        """Return a mock success response — used in tests and DEMO_MODE."""
        return {
            "status":            "mock",
            "message":           f"[MOCK] Rappel simulé: \"{payload.get('title')}\"",
            "action_id":         payload.get("action_id", f"mock_{uuid.uuid4().hex[:8]}"),
            "reminder_datetime": payload.get("reminder_datetime"),
            "gcal_event_id":     "mock_gcal_event_id_000",
            "gcal_html_link":    "https://calendar.google.com/mock",
        }
