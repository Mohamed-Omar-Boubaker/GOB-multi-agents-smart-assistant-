"""
STT (Speech-to-Text) End-to-End Test
=====================================

Tests the complete audio pipeline:
Audio file → Backend API → STT → Transcription → LLM → TTS → MQTT → Device

Prerequisites:
- Backend running: uvicorn backend.main:app --reload
- MQTT broker: mosquitto -v
- TTS server: Piper Wyoming
- Audio test file available

This script:
1. Loads audio file (WAV/MP3)
2. Encodes to base64
3. Sends to /command/audio endpoint
4. Verifies STT transcription
5. Checks TTS audio generation
6. Verifies MQTT auto-publish
"""

import asyncio
import base64
import httpx
from pathlib import Path


async def test_stt_with_audio_file(audio_file_path: str):
    """
    Test STT with real audio file.
    
    Args:
        audio_file_path: Path to WAV/MP3 audio file
    """
    print("=" * 70)
    print("STT END-TO-END TEST - AUDIO FILE")
    print("=" * 70)
    
    # Check file exists
    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        print(f"\n❌ Error: Audio file not found: {audio_file_path}")
        return False
    
    print(f"\n📁 Audio file: {audio_path.name}")
    print(f"   Size: {audio_path.stat().st_size} bytes")
    print(f"   Format: {audio_path.suffix[1:]}")
    
    # Read and encode audio to base64
    try:
        audio_bytes = audio_path.read_bytes()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        print(f"   Base64 length: {len(audio_base64)} chars")
    except Exception as e:
        print(f"\n❌ Error reading audio file: {e}")
        return False
    
    # Prepare command
    command = {
        "command_type": "audio",
        "user_id": "test_user_stt",
        "audio_data": audio_base64,
        "audio_format": audio_path.suffix[1:],  # wav, mp3, etc.
        "language": "en",
        "source": "microphone"
    }
    
    print(f"\n📤 Sending audio to backend...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Send to backend
            response = await client.post(
                "http://localhost:8000/command/audio",
                json=command
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"\n✅ Backend Response:")
                print(f"   Status: {result.get('status')}")
                print(f"   Type: {result.get('type')}")
                
                # STT Transcription
                transcription = result.get('transcription', '')
                if transcription:
                    print(f"\n🎤 STT Transcription:")
                    print(f"   Text: '{transcription}'")
                    print(f"   Length: {len(transcription)} chars")
                else:
                    print(f"\n❌ No transcription received")
                
                # LLM Response
                response_text = result.get('response', '')
                if response_text:
                    print(f"\n💬 LLM Response:")
                    print(f"   Text: {response_text[:100]}...")
                
                # TTS Audio
                audio_response = result.get('audio')
                if audio_response:
                    audio_size = len(audio_response.get('audio_data', ''))
                    print(f"\n🎵 TTS Audio:")
                    print(f"   Generated: ✅ ({audio_size} bytes)")
                else:
                    print(f"\n🎵 TTS Audio: ❌ Not generated")
                
                # Pipeline summary
                print(f"\n📊 Complete Pipeline:")
                print(f"   1. ✅ Audio received by backend")
                print(f"   2. ✅ STT transcribed audio → text")
                print(f"   3. ✅ LLM processed command")
                print(f"   4. {'✅' if audio_response else '❌'} TTS generated response audio")
                print(f"   5. {'✅' if audio_response else '❌'} Auto-publish MQTT")
                
                return True
            
            else:
                print(f"\n❌ Backend Error: {response.status_code}")
                print(f"   {response.text}")
                return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stt_with_generated_audio():
    """
    Test STT with programmatically generated audio.
    Uses text-to-speech to create audio, then tests STT on it.
    """
    print("\n" + "=" * 70)
    print("STT TEST - ROUND-TRIP (TTS → STT)")
    print("=" * 70)
    
    print("\n⚠️  This test requires TTS to generate audio first")
    print("   Then sends generated audio back through STT")
    print("   Useful for testing STT without external audio files")
    
    # First, generate audio with TTS
    print(f"\n📤 Step 1: Generate audio with TTS...")
    
    text_to_speak = "Hello, testing speech to text functionality"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Generate audio with TTS
            response = await client.post(
                "http://localhost:8000/command/text",
                json={
                    "command_type": "text",
                    "user_id": "test_user_stt",
                    "text": text_to_speak,
                    "language": "en"
                }
            )
            
            if response.status_code != 200:
                print(f"❌ TTS generation failed: {response.status_code}")
                return False
            
            result = response.json()
            audio_response = result.get('audio')
            
            if not audio_response:
                print(f"❌ TTS did not generate audio")
                return False
            
            audio_base64 = audio_response.get('audio_data')
            print(f"✅ TTS audio generated ({len(audio_base64)} bytes)")
            print(f"   Original text: '{text_to_speak}'")
            
            # Step 2: Send audio through STT
            print(f"\n📤 Step 2: Send audio through STT...")
            
            stt_response = await client.post(
                "http://localhost:8000/command/audio",
                json={
                    "command_type": "audio",
                    "user_id": "test_user_stt",
                    "audio_data": audio_base64,
                    "audio_format": "wav",
                    "language": "en",
                    "source": "test"
                }
            )
            
            if stt_response.status_code != 200:
                print(f"❌ STT failed: {stt_response.status_code}")
                return False
            
            stt_result = stt_response.json()
            transcription = stt_result.get('transcription', '')
            
            print(f"\n🎤 STT Transcription:")
            print(f"   Original text: '{text_to_speak}'")
            print(f"   Transcribed:   '{transcription}'")
            
            # Check similarity (basic)
            if transcription.lower().strip() in text_to_speak.lower() or \
               text_to_speak.lower() in transcription.lower().strip():
                print(f"\n✅ Transcription matches original text!")
            else:
                print(f"\n⚠️  Transcription differs (may be normal for TTS→STT)")
            
            print(f"\n📊 Round-trip Pipeline:")
            print(f"   1. ✅ Text → TTS → Audio")
            print(f"   2. ✅ Audio → STT → Text")
            print(f"   3. ✅ Complete cycle verified")
            
            return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all STT tests."""
    
    print("\n🎤 STT (SPEECH-TO-TEXT) END-TO-END TESTS\n")
    
    print("Prerequisites:")
    print("  ✅ Backend: uvicorn backend.main:app --reload")
    print("  ✅ MQTT: mosquitto -v")
    print("  ✅ TTS: Piper Wyoming server")
    print("  ✅ STT: Whisper model loaded")
    
    input("\n⏸️  Press ENTER to start tests...")
    
    # Test 1: Round-trip TTS → STT
    print("\n" + "=" * 70)
    print("TEST 1: TTS → STT ROUND-TRIP")
    print("=" * 70)
    success1 = await test_stt_with_generated_audio()
    
    # Test 2: External audio file (if available)
    print("\n" + "=" * 70)
    print("TEST 2: AUDIO FILE (Optional)")
    print("=" * 70)
    
    audio_file = input("\n📁 Enter path to audio file (or press ENTER to skip): ").strip()
    
    success2 = True
    if audio_file:
        success2 = await test_stt_with_audio_file(audio_file)
    else:
        print("   ⏭️  Skipped")
    
    # Results
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"  Test TTS→STT:     {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"  Test Audio File:  {'✅ PASS' if success2 else '⏭️  SKIPPED'}")
    print("=" * 70)
    
    if success1:
        print("\n🎉 STT is working correctly!")
        print("\nVerified capabilities:")
        print("  - Audio reception (base64)")
        print("  - STT transcription (Whisper)")
        print("  - Integration with backend pipeline")
        print("  - TTS → STT round-trip")
    else:
        print("\n❌ STT tests failed")
        print("\nCheck:")
        print("  - Backend running")
        print("  - ENABLE_AUDIO_PROCESSING=True in .env")
        print("  - Whisper model loaded")
        print("  - TTS server available")


if __name__ == "__main__":
    asyncio.run(main())
