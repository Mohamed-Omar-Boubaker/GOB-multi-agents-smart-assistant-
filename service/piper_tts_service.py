import asyncio
import wave
import uuid
import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from wyoming.tts import Synthesize
from wyoming.audio import AudioChunk, AudioStop
from wyoming.event import async_write_event, async_read_event

def _read_env_value(env_path: Path, key: str) -> Optional[str]:
    """Read a key from a .env file without external dependencies."""
    if not env_path.exists():
        return None

    try:
        with env_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    except Exception:
        return None

    return None


# Read backend/.env so TTS_PUBLIC_BASE_URL can be configured centrally.
ENV_PATH = Path(__file__).resolve().parent.parent / "backend" / ".env"
ENV_TTS_PUBLIC_BASE_URL = _read_env_value(ENV_PATH, "TTS_PUBLIC_BASE_URL")

PIPER_HOST = "127.0.0.1"
PIPER_PORT = 5002   # port docker piper
TTS_PUBLIC_BASE_URL = os.getenv("TTS_PUBLIC_BASE_URL") or ENV_TTS_PUBLIC_BASE_URL or "http://localhost:8005"

AUDIO_DIR = "tts_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

app = FastAPI()
logger = logging.getLogger("piper_tts_service")

if "localhost" in TTS_PUBLIC_BASE_URL or "127.0.0.1" in TTS_PUBLIC_BASE_URL:
    logger.warning(
        "TTS_PUBLIC_BASE_URL points to localhost. This is not reachable from ESP32; set a LAN URL like http://192.168.1.3:8005"
    )


class TTSRequest(BaseModel):
    text: str
    request_id: Optional[str] = None
    action_id: Optional[str] = None


async def synthesize(text: str) -> str:

    reader, writer = await asyncio.open_connection(PIPER_HOST, PIPER_PORT)

    synth = Synthesize(text=text)
    await async_write_event(synth.event(), writer)
    await writer.drain()

    audio_chunks = []

    while True:
        event = await async_read_event(reader)

        if event is None:
            break

        if AudioChunk.is_type(event.type):
            chunk = AudioChunk.from_event(event)
            audio_chunks.append(chunk.audio)

        elif AudioStop.is_type(event.type):
            break

    writer.close()
    await writer.wait_closed()

    audio_bytes = b"".join(audio_chunks)

    filename = f"{uuid.uuid4()}.wav"
    path = os.path.join(AUDIO_DIR, filename)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(audio_bytes)

    return path


@app.post("/tts")
async def tts(req: TTSRequest):

    text = (req.text or "").strip()
    if not text:
        raise HTTPException(400, "text empty")

    path = await synthesize(text)
    if not os.path.exists(path):
        raise HTTPException(500, "audio generation failed")

    audio_url = f"{TTS_PUBLIC_BASE_URL.rstrip('/')}/audio/{os.path.basename(path)}"
    logger.info(
        "TTS generated",
        extra={
            "request_id": req.request_id,
            "action_id": req.action_id,
            "audio_url": audio_url,
            "text_len": len(text)
        }
    )

    return {
        "audio_url": audio_url,
        "request_id": req.request_id,
        "action_id": req.action_id
    }


@app.get("/audio/{file}")
async def get_audio(file: str):
    return FileResponse(os.path.join(AUDIO_DIR, file))