"""
mqtt_stub.py
─────────────────────────────────────────────────────────────────────────────
Lightweight MQTT wrapper used by the standalone Reminder System.

- If ENABLE_MQTT=true  → tries to connect to real Mosquitto broker.
- If ENABLE_MQTT=false → all publish calls are no-ops (logged only).

Fully self-contained — no dependency on the full GOB MQTTClient.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MQTTStub:
    """
    Thin MQTT publisher. Publishes reminder alerts and audio to ESP32.
    Gracefully degrades to mock if broker is unreachable.
    """

    def __init__(
        self,
        broker: str    = "localhost",
        port: int      = 1883,
        username: str  = "",
        password: str  = "",
        enabled: bool  = True,
    ):
        self.broker   = broker
        self.port     = port
        self.username = username
        self.password = password
        self.enabled  = enabled
        self._client  = None
        self._connected = False

        if self.enabled:
            self._init()

    # ── Public API ────────────────────────────────────────────────────────

    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        if not self.enabled:
            return False
        try:
            self._client.connect(self.broker, self.port, keepalive=60)
            self._client.loop_start()
            self._connected = True
            logger.info(f"MQTTStub: connected to {self.broker}:{self.port}")
            return True
        except Exception as e:
            logger.warning(f"MQTTStub: cannot connect to broker ({e}) — using mock mode")
            self._connected = False
            return False

    def publish(self, topic: str, payload: dict, qos: int = 1) -> dict:
        """Publish a dict payload to a MQTT topic."""
        msg = json.dumps(payload)
        if not self.enabled or not self._connected:
            logger.info(f"MQTTStub [MOCK] publish → {topic}: {msg[:80]}")
            return {"status": "mock", "topic": topic}

        try:
            result = self._client.publish(topic, msg, qos=qos)
            logger.info(f"MQTTStub: published to {topic} (mid={result.mid})")
            return {"status": "published", "topic": topic, "mid": result.mid}
        except Exception as e:
            logger.error(f"MQTTStub: publish failed on {topic}: {e}")
            return {"status": "error", "error": str(e)}

    def publish_audio(self, audio_b64: str, user_id: str) -> dict:
        """Publish base64-encoded WAV audio to device/audio/{user_id}."""
        topic = f"device/audio/{user_id}"
        return self.publish(topic, {"audio_data": audio_b64, "format": "wav"}, qos=0)

    def disconnect(self):
        if self._client and self._connected:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("MQTTStub: disconnected")

    # ── Private ───────────────────────────────────────────────────────────

    def _init(self):
        try:
            import paho.mqtt.client as mqtt

            self._client = mqtt.Client(client_id=f"reminder_system_{id(self)}")
            if self.username:
                self._client.username_pw_set(self.username, self.password)

            self._client.on_connect    = self._on_connect
            self._client.on_disconnect = self._on_disconnect

        except ImportError:
            logger.warning("MQTTStub: paho-mqtt not installed — MQTT disabled")
            self.enabled = False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info("MQTTStub: broker connection established")
        else:
            logger.warning(f"MQTTStub: broker refused connection (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        logger.info(f"MQTTStub: disconnected (rc={rc})")
