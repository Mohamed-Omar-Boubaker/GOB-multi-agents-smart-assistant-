"""
tts_stub.py
─────────────────────────────────────────────────────────────────────────────
Lightweight TTS wrapper used by the standalone Reminder System.

- If ENABLE_TTS=true  → tries to connect to a real Piper/Wyoming TTS server.
- If ENABLE_TTS=false → returns a silent mock AudioResult (for testing/demo).

This keeps the reminder system fully self-contained without needing
the full GOB backend's TTSEngine class.
"""

from __future__ import annotations
import base64
import logging
import os
import socket
import struct
from typing import Optional

from models import AudioResult

logger = logging.getLogger(__name__)


class TTSStub:
    """
    Thin wrapper around a local Piper TTS server (Wyoming protocol).
    Falls back to mock silently if the server is unreachable.
    """

    def __init__(self, host: str = "localhost", port: int = 10200, enabled: bool = True):
        self.host    = host
        self.port    = port
        self.enabled = enabled

    def synthesize(self, text: str, language: str = "fr") -> AudioResult:
        """
        Convert text to speech.
        Returns AudioResult with base64-encoded WAV audio.
        Falls back to silent mock on any error.
        """
        if not self.enabled:
            return self._mock_audio(text)

        try:
            return self._call_piper(text)
        except Exception as e:
            logger.warning(f"TTSStub: synthesis failed ({e}), returning mock audio")
            return self._mock_audio(text)

    # ── Private ───────────────────────────────────────────────────────────

    def _call_piper(self, text: str) -> AudioResult:
        """
        Sends text to local Piper Wyoming server via TCP socket.
        Returns base64-encoded WAV bytes.
        """
        import json

        clean = self._clean(text)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.settimeout(10)

            # Wyoming protocol: send JSON event
            event = json.dumps({"type": "synthesize", "data": {"text": clean}}) + "\n"
            s.sendall(event.encode())

            # Read audio chunks until server closes connection
            audio_bytes = bytearray()
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                audio_bytes.extend(chunk)

        wav = self._build_wav(bytes(audio_bytes))
        return AudioResult(
            audio_data   = base64.b64encode(wav).decode(),
            audio_format = "wav",
            duration_ms  = len(audio_bytes) // 32,   # rough estimate
        )

    @staticmethod
    def _clean(text: str) -> str:
        """Remove emojis and special characters that confuse TTS."""
        import re
        # Remove emoji blocks
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U00002700-\U000027BF"
            "\U0001F900-\U0001F9FF"
            "\u2600-\u26FF"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub("", text).strip()

    @staticmethod
    def _build_wav(raw_pcm: bytes, sample_rate: int = 22050) -> bytes:
        """Wrap raw PCM bytes in a minimal WAV header."""
        num_channels   = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size  = len(raw_pcm)
        chunk_size = 36 + data_size

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", chunk_size, b"WAVE", b"fmt ", 16,
            1, num_channels, sample_rate, byte_rate,
            block_align, bits_per_sample,
            b"data", data_size,
        )
        return header + raw_pcm

    @staticmethod
    def _mock_audio(text: str) -> AudioResult:
        """Return a silent 0.1s WAV — used in tests and demo mode."""
        # 0.1 second of silence at 22050 Hz, 16-bit mono
        silence = bytes(int(22050 * 0.1) * 2)
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", 36 + len(silence), b"WAVE", b"fmt ", 16,
            1, 1, 22050, 44100, 2, 16,
            b"data", len(silence),
        )
        wav_b64 = base64.b64encode(header + silence).decode()
        logger.debug(f"TTSStub._mock_audio: returning silent WAV for: {text[:40]}")
        return AudioResult(audio_data=wav_b64, audio_format="wav", duration_ms=100)
