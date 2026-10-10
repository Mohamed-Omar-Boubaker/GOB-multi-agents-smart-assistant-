# ESP32 Firmware Module

Embedded firmware for robot state animation and TTS playback over MQTT.

## Maintainers

- Montassar

## Firmware Files

- gob_esp32_final.cpp: main integrated firmware (audio + servos + LEDs)
- haut_parleur.cpp: audio + servo focused variant
- servo_protytpage.cpp: servo prototype and state machine tests
- led_run.cpp: NeoPixel LED animation prototype

## Main Features (gob_esp32_final.cpp)

- Wi-Fi connection to local network
- MQTT subscription to robot/audio topics
- I2S WAV audio playback from HTTP URL
- Dual-servo animation by robot state
- NeoPixel LED effects synchronized with state
- Acknowledgment publishing back to backend/n8n

## Hardware Mapping

### Audio (I2S)

- BCLK: GPIO 25
- LRC/WS: GPIO 26
- DOUT: GPIO 22

### Servos

- Servo 1: GPIO 18
- Servo 2: GPIO 19

### LEDs

- NeoPixel data pin: GPIO 5
- LED count in final firmware: 7

## Network Configuration in Code

Current defaults in firmware:

- Wi-Fi SSID: ESP32
- Wi-Fi password: esp32test123
- MQTT broker: 10.93.177.189

Update these values in source code before production use.

## MQTT Topics

### Incoming topics

- gob/audio/tts/request
- gob/audio/tts (legacy compatibility)
- gob/robot/state

### Outgoing acknowledgment topics

- gob/audio/tts/ack
- gob/robot/state/ack

## Payload Contracts

### Audio request payload

Topic: gob/audio/tts/request

```json
{
  "request_id": "req_001",
  "action_id": "act_001",
  "url": "http://HOST:8005/audio/file.wav"
}
```

### Audio ack payload

Topic: gob/audio/tts/ack

```json
{
  "request_id": "req_001",
  "action_id": "act_001",
  "device_id": "esp32_speaker_01",
  "status": "started",
  "error": "",
  "ts": 1711112000
}
```

Possible status values: started, done, error

### Robot state command payload

Topic: gob/robot/state

```json
{
  "request_id": "req_123",
  "user_id": "web_user_001",
  "state": "listening"
}
```

Allowed states:

- idle
- sleep
- listening
- thinking
- speaking
- happy
- error

### Robot state ack payload

Topic: gob/robot/state/ack

```json
{
  "request_id": "req_123",
  "user_id": "web_user_001",
  "device_id": "esp32_servo_01",
  "status": "applied",
  "error": "",
  "state": "listening",
  "ts": 1711112000
}
```

Possible status values: applied, ignored, error

## State Machine Notes

- Servo transitions include guard intervals to avoid mechanical stress.
- Sleep/idle transitions have a minimum hold time.
- Happy and error states auto-return to idle after a timeout.
- In power-limited mode, servo movement is staggered to reduce current spikes.

## Audio Playback Notes

- WAV only, mono, 16-bit PCM
- Dynamic sample-rate adaptation based on WAV header
- Prebuffer + DMA drain handling for stable playback
- Playback can be rejected with device_busy if a request is already active

## Build and Flash (Arduino IDE)

1. Install Arduino IDE and ESP32 board support.
2. Install required libraries:
   - PubSubClient
   - ArduinoJson
   - ESP32Servo
   - Adafruit NeoPixel
3. Open gob_esp32_final.cpp (or your target variant).
4. Select board and COM port.
5. Upload firmware.
6. Open Serial Monitor at 115200 baud.

## Runtime Checklist

- Wi-Fi connected and IP assigned
- MQTT broker reachable from ESP32
- HTTP audio server reachable for WAV URLs
- Correct topic names configured in backend/n8n
- Stable power supply for ESP32 + servos + LEDs

## Troubleshooting

### No servo movement

- Check GPIO wiring and external power.
- Verify state topic payload uses allowed state names.

### Audio does not play

- Verify WAV format is mono 16-bit PCM.
- Verify URL is reachable from ESP32.
- Check I2S pin wiring.

### Frequent ignored state transitions

- Guard logic is active by design.
- Avoid sending state updates too quickly.
