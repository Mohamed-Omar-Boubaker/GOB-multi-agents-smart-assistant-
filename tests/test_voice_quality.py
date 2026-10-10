"""
Script pour tester différents sample rates et trouver le son le plus humain
Basé sur test_piper.py

Usage:
    python test_voice_quality.py
"""

import asyncio
from wyoming.tts import Synthesize
from wyoming.audio import AudioChunk, AudioStop
from wyoming.event import async_write_event, async_read_event
import wave


async def test_voice(text: str, filename: str, sample_rate: int):
    """Test voice synthesis with specific sample rate"""
    reader, writer = await asyncio.open_connection("127.0.0.1", 5002)

    synthesize = Synthesize(text=text)
    await async_write_event(synthesize.event(), writer)
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

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)

    print(f"✅ Audio created: {filename} ({sample_rate} Hz)")


async def run_voice_tests():
    """Test different sample rates to find the most human-like voice"""
    
    test_text = "Hi, I am GOB, your intelligent assistant. How can I help you today?"
    
    # Different sample rates to test
    sample_rates = {
        20000: "voice_deep_20000hz.wav",      # Deep/masculine
        21470: "voice_natural_21470hz.wav",   # Natural (RECOMMENDED)
        22050: "voice_balanced_22050hz.wav",  # Standard CD quality
        24000: "voice_clear_24000hz.wav",     # Clear/bright
        25750: "voice_sharp_25750hz.wav",     # Sharp/high pitch
    }
    
    print("🎤 Testing different voice qualities...")
    print("=" * 60)
    print(f"Test phrase: '{test_text}'")
    print("=" * 60)
    
    for rate, filename in sample_rates.items():
        await test_voice(test_text, filename, rate)
    
    print("\n" + "=" * 60)
    print("✅ All tests complete!")
    print("\n🎧 Listen to each file and choose the best one:")
    print("   - voice_deep_20000hz.wav = Deep/masculine voice")
    print("   - voice_natural_21470hz.wav = Natural (DEFAULT) ⭐")
    print("   - voice_balanced_22050hz.wav = Standard balanced")
    print("   - voice_clear_24000hz.wav = Clear/bright")
    print("   - voice_sharp_25750hz.wav = Sharp/high pitch")
    print("\n📝 To use your favorite, update backend/.env:")
    print("   TTS_SAMPLE_RATE=21470  (change to your preferred value)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_voice_tests())
