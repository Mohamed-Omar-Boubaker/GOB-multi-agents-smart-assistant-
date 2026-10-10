# Voice Assistant Client - Complete Solution Guide
## From Push-to-Talk (Phase A) to Wake Word (Phase B)

**Project:** PCD AI Embedded Agent - Voice Interface  
**Objective:** Build voice client that works with PC mic today, easily migrates to ESP32 tomorrow  
**Strategy:** Start simple (A), upgrade to advanced (B)

---

## 🎯 Overview - Two-Phase Approach

### Why Two Phases?

**Professional development approach:**
1. ✅ Build stable MVP first (Phase A)
2. ✅ Validate complete pipeline
3. ✅ Debug issues in isolation
4. ✅ Add advanced features (Phase B)

**NOT recommended:** Build everything at once → debugging nightmare

---

## 📊 Architecture Choice - CRITICAL DECISION

### Current State (What we have now):
```
User → HTTP /command/text → Backend → MQTT device/audio → Fake Device → Speaker ✅
User → HTTP /command/audio → Backend → MQTT device/audio → Fake Device → Speaker ✅
```

**Works perfectly for web/mobile apps.**

### Future State (What we need for voice assistant):
```
Microphone → ??? → Backend → MQTT → Speaker
```

### Two Architecture Options:

#### **Option 1: HTTP-based (Current)**
```
Voice Client (PC Micro)
    ↓ 
HTTP POST /command/audio (base64)
    ↓
Backend API (FastAPI)
    ↓
STT → LLM → TTS
    ↓
MQTT publish device/audio
    ↓
Fake Device / ESP32
    ↓
Speaker plays audio
```

**Pros:**
- ✅ No backend modification needed
- ✅ Uses existing endpoints
- ✅ Simple to implement

**Cons:**
- ❌ ESP32 migration harder (HTTP client complex)
- ❌ Not standard IoT pattern
- ❌ Requires WiFi HTTP stack on ESP32

#### **Option 2: MQTT-based (Recommended)** ⭐
```
Voice Client (PC Micro)
    ↓
MQTT publish device/{id}/audio/input
    ↓
Backend MQTT Listener (new component)
    ↓
STT → LLM → TTS (existing pipeline)
    ↓
MQTT publish device/{id}/audio/output
    ↓
Fake Device / ESP32
    ↓
Speaker plays audio
```

**Pros:**
- ✅ ESP32 migration = TRIVIAL (just MQTT publish/subscribe)
- ✅ Standard IoT architecture
- ✅ Multi-device support automatic
- ✅ Bidirectional audio via MQTT
- ✅ Real-time, low latency
- ✅ Backend keeps HTTP for web/mobile

**Cons:**
- ⚠️ Need to add MQTT listener to backend (~100 lines)

### 🎯 RECOMMENDATION: Use Option 2 (MQTT-based)

**Why?**
- ESP32 code will be ~50 lines (vs 200+ with HTTP)
- Professional IoT architecture
- Future-proof for multiple devices
- Backend modification minimal and clean

---

## 🏗️ MQTT Topics Architecture

### Proposed Topic Structure:
```
device/{device_id}/audio/input      # Microphone audio → Backend
device/{device_id}/audio/output     # TTS audio → Speaker
device/{device_id}/status           # Device status (online, busy, idle)
device/{device_id}/command          # IoT commands (turn on/off, etc.)
```

### Why this structure?
- ✅ Multiple devices support (PC, ESP32, mobile)
- ✅ Each device has unique ID
- ✅ Clear input/output separation
- ✅ Easy to add new topics

### Device IDs:
- PC Microphone client: `device/pc_voice_001/audio/input`
- Fake ESP32: `device/fake_esp32_001/audio/output`
- Real ESP32: `device/esp32_living_room/audio/output`

---

## 📦 Phase A - Push-to-Talk Client (Simple MVP)

### Time Estimate: **2 hours**

### What it does:
1. Press **SPACE** key to start recording
2. Speak while holding SPACE
3. Release SPACE → automatic send to backend
4. Backend processes (STT → LLM → TTS → MQTT)
5. Fake device plays response audio

### Components:
```
voice_client_pushto_talk.py
├─ AudioRecorder            # Record from PC mic
├─ AudioPlayer              # Play via MQTT (subscribe device/audio/output)
├─ BackendClient            # HTTP POST to /command/audio
└─ KeyboardListener         # Detect SPACE press/release
```

### Dependencies:
```bash
pip install sounddevice      # Audio recording
pip install numpy            # Audio processing
pip install paho-mqtt        # MQTT client
pip install pygame           # Audio playback
pip install httpx            # HTTP client
pip install keyboard         # Key detection
```

### Usage:
```bash
# Terminal 1: Backend
uvicorn backend.main:app --reload

# Terminal 2: Fake Device
python fake_esp32_device.py --save-audio

# Terminal 3: Mosquitto
mosquitto -v

# Terminal 4: Voice Client
python voice_client_pushto_talk.py
```

### Features Phase A:
- ✅ Press SPACE to talk
- ✅ Visual feedback (recording indicator)
- ✅ Audio sent to backend via HTTP
- ✅ Response played on PC speakers via MQTT
- ✅ Status display (listening, processing, speaking)
- ✅ Error handling (no mic, no backend, etc.)

### Testing Strategy:
1. Test recording quality
2. Test backend connectivity
3. Test MQTT audio playback
4. Test error cases (disconnect, no mic)
5. **Validate complete pipeline works**

---

## 🚀 Phase B - Wake Word + Always Listening (Advanced)

### Time Estimate: **4-6 hours** (upgrade from Phase A)

### What it does:
1. **Always listening** to microphone
2. Detects **wake word** ("Hey Assistant" or custom)
3. 🔔 Beep confirmation
4. Records until **silence detected** (2-3 seconds)
5. Automatically sends to backend via **MQTT** (not HTTP)
6. Backend processes (STT → LLM → TTS)
7. Response played via MQTT

### New Components:
```
voice_assistant_complete.py
├─ WakeWordDetector         # Porcupine wake word engine
├─ SilenceDetector          # VAD (Voice Activity Detection)
├─ AudioBuffer              # Circular buffer for continuous recording
├─ MQTTAudioClient          # Publish to device/mic/audio
├─ MQTTAudioPlayer          # Subscribe device/speaker/audio
└─ StateMachine             # idle → listening → recording → processing
```

### Additional Dependencies:
```bash
pip install pvporcupine     # Wake word detection (free tier)
pip install webrtcvad       # Voice Activity Detection (silence)
```

### Wake Word Options:

#### Option 1: Porcupine (Recommended)
- ✅ Free tier available
- ✅ Works offline
- ✅ Custom wake words: "Hey Assistant", "Computer", etc.
- ✅ Low CPU usage
- ⚠️ Requires API key (free)

#### Option 2: Vosk (Open Source)
- ✅ Fully free
- ✅ Offline
- ⚠️ Higher CPU usage
- ⚠️ Less accurate

### State Machine:
```
IDLE
  ↓ (wake word detected)
LISTENING (beep sound)
  ↓ (recording audio)
RECORDING
  ↓ (silence detected 2s)
PROCESSING (send to backend via MQTT)
  ↓ (waiting response)
SPEAKING (playing TTS audio)
  ↓ (audio finished)
IDLE
```

### Silence Detection Algorithm:
```python
def is_silence(audio_chunk, threshold=-40dB):
    # Calculate RMS energy
    energy = 20 * log10(rms(audio_chunk))
    
    if energy < threshold:
        silence_duration += chunk_duration
        
        if silence_duration > 2.0:  # 2 seconds
            return True  # End of speech
    else:
        silence_duration = 0  # Reset
        
    return False
```

### Backend Modification - MQTT Listener (New):

Add to `backend/main.py`:
```python
# New component: MQTT Audio Input Listener
mqtt_listener = MQTTAudioInputListener(
    broker="localhost",
    topic="device/+/audio/input",  # Listen all devices
    callback=process_mqtt_audio
)

async def process_mqtt_audio(device_id: str, audio_base64: str):
    """
    Process audio received via MQTT (from voice client or ESP32).
    """
    # Same pipeline as /command/audio
    result = await agent_core.process({
        "command_type": "audio",
        "audio_data": audio_base64,
        "user_id": device_id,
        "language": "en",
        "source": "mqtt"
    })
    
    # TTS audio already auto-published to device/audio/output
    # via existing auto_publish mechanism
```

**Code size:** ~100 lines
**Impact:** Minimal, clean separation of concerns

---

## 🔄 Migration Path: PC → ESP32

### Current Setup (Development):
```
┌─────────────────┐
│  PC Microphone  │ ──MQTT──┐
└─────────────────┘         │
                            ↓
                    ┌──────────────┐
                    │ MQTT Broker  │
                    └──────────────┘
                            ↓
                    ┌──────────────┐
                    │   Backend    │
                    └──────────────┘
                            ↓
                    ┌──────────────┐
                    │ MQTT Broker  │
                    └──────────────┘
                            ↓
┌─────────────────┐         │
│  Fake Device    │ ◄─MQTT──┘
│  (PC Speaker)   │
└─────────────────┘
```

### Production Setup (ESP32):
```
┌─────────────────────┐
│  ESP32 + I2S Micro  │ ──MQTT──┐
└─────────────────────┘         │
                                ↓
                        ┌──────────────┐
                        │ MQTT Broker  │
                        └──────────────┘
                                ↓
                        ┌──────────────┐
                        │   Backend    │
                        │ (NO CHANGE)  │
                        └──────────────┘
                                ↓
                        ┌──────────────┐
                        │ MQTT Broker  │
                        └──────────────┘
                                ↓
┌─────────────────────┐         │
│ ESP32 + I2S Speaker │ ◄─MQTT──┘
└─────────────────────┘
```

### ESP32 Code Preview:
```cpp
// ESP32 Arduino code (simplified)
#include <WiFi.h>
#include <PubSubClient.h>
#include "driver/i2s.h"

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

void setup() {
    // Connect WiFi
    WiFi.begin(SSID, PASSWORD);
    
    // Connect MQTT
    mqtt.setServer(MQTT_BROKER, 1883);
    mqtt.setCallback(onMqttMessage);
    mqtt.connect("esp32_living_room");
    
    // Subscribe to audio output topic
    mqtt.subscribe("device/esp32_living_room/audio/output");
    
    // Setup I2S microphone
    i2s_driver_install(I2S_NUM_0, &i2s_config_mic, 0, NULL);
    
    // Setup I2S speaker
    i2s_driver_install(I2S_NUM_1, &i2s_config_speaker, 0, NULL);
}

void loop() {
    // 1. Record audio from I2S microphone
    size_t bytes_read;
    i2s_read(I2S_NUM_0, audio_buffer, BUFFER_SIZE, &bytes_read, 100);
    
    // 2. Detect wake word (local ESP32 processing)
    if (detectWakeWord(audio_buffer)) {
        // Record 3 seconds
        recordAudio(audio_buffer, 3000);
        
        // Encode base64
        String base64_audio = base64_encode(audio_buffer);
        
        // 3. Publish to MQTT
        mqtt.publish("device/esp32_living_room/audio/input", 
                     base64_audio.c_str());
    }
    
    mqtt.loop();  // Handle incoming messages
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
    // Received TTS audio from backend
    if (strcmp(topic, "device/esp32_living_room/audio/output") == 0) {
        // Decode base64
        decode_base64(payload, audio_output);
        
        // Play on I2S speaker
        i2s_write(I2S_NUM_1, audio_output, length, &bytes_written, 100);
    }
}
```

**Lines of code:** ~150 (with error handling)

### Hardware Components for ESP32:
```
ESP32-DevKitC          ~$10
I2S MEMS Microphone    ~$5  (INMP441)
I2S Speaker/Amplifier  ~$8  (MAX98357A)
Power supply 5V        ~$3
Total:                 ~$26
```

### Migration Steps:
1. ✅ Test complete pipeline with PC (Phase A + B)
2. ✅ Buy ESP32 + microphone + speaker
3. ✅ Copy ESP32 code above
4. ✅ Configure WiFi credentials
5. ✅ Flash to ESP32
6. ✅ **Backend: 0 changes** ✅
7. ✅ Test with real hardware

**Migration time:** 2-3 hours (mostly hardware wiring)

---

## 📋 Development Roadmap

### Week 1: Foundation (DONE ✅)
- [x] Backend AgentCore
- [x] STT (Whisper)
- [x] TTS (Piper)
- [x] LLM integration
- [x] MQTT auto-publish
- [x] Fake ESP32 device
- [x] Pipeline validation tests

### Week 2: Voice Client - Phase A (2 days)
- [ ] Day 1: Push-to-Talk client
  - [ ] Audio recording (sounddevice)
  - [ ] Keyboard listener (SPACE key)
  - [ ] HTTP client to backend
  - [ ] MQTT audio player
  - [ ] Status display UI
- [ ] Day 2: Testing & Polish
  - [ ] Test recording quality
  - [ ] Test pipeline latency
  - [ ] Error handling
  - [ ] User feedback improvements

### Week 3: Voice Client - Phase B (3-4 days)
- [ ] Day 1: Wake Word Detection
  - [ ] Porcupine integration
  - [ ] Custom wake word training
  - [ ] Detection tuning
- [ ] Day 2: Silence Detection
  - [ ] VAD implementation
  - [ ] Energy threshold tuning
  - [ ] Buffer management
- [ ] Day 3: MQTT Migration
  - [ ] Add MQTT listener to backend
  - [ ] Refactor audio input via MQTT
  - [ ] Test bidirectional MQTT
- [ ] Day 4: State Machine & Polish
  - [ ] Complete state machine
  - [ ] Visual/audio feedback
  - [ ] Performance optimization

### Week 4: Documentation & Demo (2 days)
- [ ] Day 1: Documentation
  - [ ] User guide
  - [ ] Architecture diagrams
  - [ ] ESP32 migration guide
- [ ] Day 2: Demo Preparation
  - [ ] Demo script
  - [ ] Video recording
  - [ ] Presentation slides

---

## 🎯 Success Criteria

### Phase A Success:
- ✅ Press SPACE → record → send → receive response
- ✅ Audio quality acceptable
- ✅ Latency < 3 seconds
- ✅ No crashes after 10 iterations
- ✅ Error messages clear and helpful

### Phase B Success:
- ✅ Wake word detection accuracy > 90%
- ✅ False positive rate < 1 per hour
- ✅ Silence detection works reliably
- ✅ Always listening without crashes
- ✅ Battery/CPU usage acceptable
- ✅ User experience smooth and natural

### ESP32 Migration Success:
- ✅ Hardware wired correctly
- ✅ Audio quality comparable to PC
- ✅ Latency acceptable (< 4s)
- ✅ No backend code changes
- ✅ Works reliably for demo

---

## ⚠️ Common Pitfalls & Solutions

### Pitfall 1: Audio Quality Issues
**Problem:** Noisy, distorted, or clipped audio  
**Solution:**
- Adjust recording volume
- Use noise cancellation
- Test different sample rates (16kHz, 44.1kHz)
- Check microphone positioning

### Pitfall 2: Wake Word False Positives
**Problem:** Wake word triggers randomly  
**Solution:**
- Increase detection threshold
- Add confirmation beep (user knows it triggered)
- Implement cooldown period (5s after detection)
- Test in real environment (background noise)

### Pitfall 3: Silence Detection Too Sensitive
**Problem:** Recording stops mid-sentence  
**Solution:**
- Increase silence threshold duration (3s instead of 2s)
- Lower energy threshold
- Use WebRTC VAD (more robust)

### Pitfall 4: MQTT Connection Lost
**Problem:** Messages not received  
**Solution:**
- Implement reconnection logic
- Use MQTT QoS 1 (at least once)
- Add connection status indicator
- Test with network simulation

### Pitfall 5: High CPU Usage
**Problem:** Computer fans loud, battery drains fast  
**Solution:**
- Use smaller Whisper model (tiny)
- Reduce audio processing frequency
- Optimize wake word detection
- Profile CPU usage (cProfile)

---

## 🔧 Configuration Files

### `voice_client_config.yaml`
```yaml
# Voice Client Configuration

audio:
  sample_rate: 16000
  channels: 1
  chunk_size: 1024
  format: int16

wake_word:
  engine: porcupine  # porcupine, vosk
  keyword: "hey assistant"
  sensitivity: 0.5  # 0.0 - 1.0
  api_key: "YOUR_PORCUPINE_KEY"

silence_detection:
  enabled: true
  threshold_db: -40
  duration_seconds: 2.0

mqtt:
  broker: localhost
  port: 1883
  keepalive: 60
  topic_audio_input: "device/pc_voice_001/audio/input"
  topic_audio_output: "device/pc_voice_001/audio/output"
  qos: 1

backend:
  url: "http://localhost:8000"
  timeout: 30

push_to_talk:
  enabled: true  # Phase A
  key: space

display:
  show_status: true
  show_transcription: true
  colors:
    idle: blue
    listening: green
    recording: yellow
    processing: orange
    speaking: purple
```

---

## 📊 Performance Benchmarks (Target)

| Metric | Phase A | Phase B |
|--------|---------|---------|
| Latency (end-to-end) | 2-3s | 3-4s |
| Wake word accuracy | N/A | >90% |
| False positive rate | N/A | <1/hour |
| CPU usage (idle) | <5% | <10% |
| CPU usage (active) | 20-30% | 30-40% |
| Memory usage | 100MB | 150MB |
| Audio quality | Good | Good |

---

## 🎓 Learning Resources

### Wake Word Detection:
- Porcupine: https://picovoice.ai/docs/porcupine/
- Vosk: https://alphacephei.com/vosk/

### Audio Processing:
- sounddevice: https://python-sounddevice.readthedocs.io/
- WebRTC VAD: https://github.com/wiseman/py-webrtcvad

### MQTT:
- paho-mqtt: https://www.eclipse.org/paho/clients/python/
- MQTT Best Practices: https://www.hivemq.com/mqtt-essentials/

### ESP32:
- ESP32 Arduino: https://docs.espressif.com/projects/arduino-esp32/
- I2S Audio: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/i2s.html

---

## 📝 Next Steps

### Immediate Actions:
1. ✅ Read this document completely
2. ✅ Validate architecture choice (recommend MQTT-based)
3. ✅ Confirm Phase A start
4. ⏳ Install dependencies
5. ⏳ Create `voice_client_pushto_talk.py`
6. ⏳ Test Phase A
7. ⏳ Validate complete pipeline
8. ⏳ Decide on Phase B timeline

### Questions to Answer:
- [ ] HTTP-based or MQTT-based? (Recommend: MQTT)
- [ ] Wake word: Porcupine or Vosk? (Recommend: Porcupine)
- [ ] When to start Phase B? (After Phase A validated)
- [ ] ESP32 hardware budget approved? (~$26)

---

## 🎉 Summary

**Phase A (Push-to-Talk):**
- ✅ Simple, stable, testable
- ✅ 2 hours development
- ✅ Complete pipeline validation
- ✅ Foundation for Phase B

**Phase B (Wake Word):**
- ✅ Advanced, impressive demo
- ✅ 4-6 hours additional work
- ✅ Always listening experience
- ✅ Production-ready feel

**ESP32 Migration:**
- ✅ Easy if architecture clean
- ✅ ~150 lines Arduino code
- ✅ 0 backend changes
- ✅ 2-3 hours migration time

**Your approach is correct:** Start with A, validate, upgrade to B.

**Architecture recommendation:** Use MQTT-based (not HTTP) for easy ESP32 migration.

---

## ✅ Ready to Start?

**Say the word and I'll create:**
1. `voice_client_config.yaml` (configuration)
2. `voice_client_pushto_talk.py` (Phase A implementation)
3. `requirements_voice_client.txt` (dependencies)

**Total development time Phase A:** 2 hours  
**Total lines of code:** ~300  

Let's build this! 🚀
