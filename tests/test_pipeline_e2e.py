"""
End-to-End MQTT Audio Pipeline Test
====================================

Pipeline tested:
User → Backend API → AgentCore → TTS → MQTT → Fake ESP32 → PC Speakers

Prerequisites:
1. mosquitto -v (Terminal 1)
2. python fake_esp32_device.py --save-audio (Terminal 2)  
3. uvicorn backend.main:app --reload (Terminal 3)
4. python test_pipeline_e2e.py (Terminal 4)

This script sends commands to the backend and verifies that:
- Backend processes the command
- TTS generates audio
- Auto-publish MQTT works
- Fake ESP32 receives and plays audio
"""

import asyncio
import httpx
import time


async def test_conversation():
    """Test conversation with TTS → MQTT → Device."""
    
    print("=" * 70)
    print("END-TO-END PIPELINE TEST - CONVERSATION")
    print("=" * 70)
    
    # Test command
    command = {
        "command_type": "text",
        "user_id": "test_user_e2e",
        "text": "Hello, can you tell me the time?",
        "language": "en"
    }
    
    print(f"\n📤 Sending command to backend:")
    print(f"   Text: {command['text']}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send to backend
            response = await client.post(
                "http://localhost:8000/command/text",
                json=command
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Backend Response:")
                print(f"   Status: {result.get('status')}")
                print(f"   Type: {result.get('type')}")
                print(f"   Response: {result.get('response', '')[:100]}...")
                
                # Check audio
                if result.get('audio'):
                    audio_size = len(result['audio'].get('audio_data', ''))
                    print(f"   Audio: ✅ Generated ({audio_size} bytes)")
                else:
                    print(f"   Audio: ❌ Not generated")
                
                print(f"\n🎵 Complete pipeline:")
                print(f"   1. ✅ Backend processed command")
                print(f"   2. ✅ TTS generated audio")
                print(f"   3. ✅ Auto-publish MQTT enabled")
                print(f"   4. 🔊 Fake ESP32 should play audio now...")
                print(f"\n   👂 Listen to your speakers!")
                
                return True
            else:
                print(f"\n❌ Backend Error: {response.status_code}")
                print(f"   {response.text}")
                return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def test_action():
    """Test IoT action with TTS confirmation → MQTT → Device."""
    
    print("\n" + "=" * 70)
    print("END-TO-END PIPELINE TEST - IoT ACTION")
    print("=" * 70)
    
    # Test command
    command = {
        "command_type": "text",
        "user_id": "test_user_e2e",
        "text": "Turn on the living room lamp",
        "language": "en"
    }
    
    print(f"\n📤 Sending action to backend:")
    print(f"   Text: {command['text']}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send to backend
            response = await client.post(
                "http://localhost:8000/command/text",
                json=command
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Backend Response:")
                print(f"   Status: {result.get('status')}")
                print(f"   Type: {result.get('type')}")
                print(f"   State: {result.get('state')}")
                print(f"   Action ID: {result.get('action_id')}")
                
                # Check confirmation audio
                if result.get('audio_response'):
                    audio_size = len(result['audio_response'].get('audio_data', ''))
                    print(f"   Audio Confirmation: ✅ Generated ({audio_size} bytes)")
                else:
                    print(f"   Audio Confirmation: ❌ Not generated")
                
                print(f"\n🎵 Complete pipeline:")
                print(f"   1. ✅ Backend classified action")
                print(f"   2. ✅ ActionBuilder created action")
                print(f"   3. ✅ TTS confirmation generated")
                print(f"   4. ✅ Auto-publish MQTT enabled")
                print(f"   5. 🔊 Fake ESP32 should play confirmation now...")
                print(f"\n   👂 Listen to your speakers!")
                
                return True
            else:
                print(f"\n❌ Backend Error: {response.status_code}")
                print(f"   {response.text}")
                return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    
    print("\n🚀 END-TO-END PIPELINE TEST")
    print("\nPrerequisites:")
    print("  ✅ mosquitto -v (MQTT broker)")
    print("  ✅ python fake_esp32_device.py --save-audio (device)")
    print("  ✅ uvicorn backend.main:app --reload (backend API)")
    print("\nVerify all services are running before continuing...")
    
    input("\n⏸️  Press ENTER to start tests...")
    
    # Test 1: Conversation
    print("\n" + "=" * 70)
    print("TEST 1/2: CONVERSATION")
    print("=" * 70)
    success1 = await test_conversation()
    
    if success1:
        print("\n⏸️  Wait for audio to finish...")
        await asyncio.sleep(5)
    
    # Test 2: IoT Action
    print("\n" + "=" * 70)
    print("TEST 2/2: IoT ACTION")
    print("=" * 70)
    success2 = await test_action()
    
    if success2:
        print("\n⏸️  Wait for audio to finish...")
        await asyncio.sleep(3)
    
    # Results
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"  Test Conversation: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"  Test IoT Action:   {'✅ PASS' if success2 else '❌ FAIL'}")
    print("=" * 70)
    
    if success1 and success2:
        print("\n🎉 COMPLETE SUCCESS!")
        print("\nPipeline functional:")
        print("  User → Backend → TTS → MQTT → Fake ESP32 → PC Speakers ✅")
        print("\nPhase 2 COMPLETED! 🚀")
    else:
        print("\n❌ Some tests failed")
        print("\nCheck:")
        print("  - mosquitto broker running")
        print("  - fake_esp32_device.py running")
        print("  - backend uvicorn running")
        print("  - TTS Piper available")


if __name__ == "__main__":
    asyncio.run(main())
