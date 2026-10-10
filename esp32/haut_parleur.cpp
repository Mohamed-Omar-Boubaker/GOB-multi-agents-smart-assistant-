#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <HTTPClient.h>
#include <driver/i2s.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>
#include <math.h>

// ===== AUDIO I2S PINS =====
#define I2S_BCLK 25
#define I2S_LRC  26
#define I2S_DOUT 22

// ===== SERVO PINS =====
#define SERVO1_PIN 18
#define SERVO2_PIN 19

// ===== WIFI =====
const char* ssid = "ESP32";
const char* password = "esp32test123";

// ===== MQTT =====
const char* mqtt_server = "10.93.177.189";

const char* mqtt_topic_audio_request = "gob/audio/tts/request";
const char* mqtt_topic_audio_request_alt = "gob/audio/tts";
const char* mqtt_topic_audio_ack = "gob/audio/tts/ack";

const char* mqtt_topic_state = "gob/robot/state";
const char* mqtt_topic_state_ack = "gob/robot/state/ack";

const char* audio_device_id = "esp32_speaker_01";
const char* servo_device_id = "esp32_servo_01";

// ===== AUDIO TUNING =====
#define SAMPLE_RATE     22050
#define DMA_BUF_COUNT   16
#define DMA_BUF_LEN     1024
#define HTTP_BUF_SIZE   4096
#define PREBUFFER_MS    300
#define START_DELAY_MS  3000

// ===== SERVO TUNING =====
#define SERVO_STEP_DEG 2
#define SERVO_UPDATE_INTERVAL_MS 20
#define POWER_LIMITED_MODE true

#define SERVO_PWM_HZ 50
#define SERVO_MIN_US 500
#define SERVO_MAX_US 2400

#define SLEEP_1 10
#define SLEEP_2 170

#define MIN_STATE_CHANGE_INTERVAL_MS 120
#define SLEEP_IDLE_MIN_HOLD_MS 900

#define NEUTRAL_1 20
#define NEUTRAL_2 160

#define LISTENING_AMPLITUDE 12
#define THINKING_AMPLITUDE 12
#define SPEAKING_AMPLITUDE 16
#define HAPPY_AMPLITUDE 20

#define LISTENING_PERIOD_MS 1400
#define THINKING_PERIOD_MS 1500
#define SPEAKING_PERIOD_MS 1100
#define HAPPY_PERIOD_MS 800

#define HAPPY_DURATION_MS 1800
#define ERROR_HOLD_MS 1200

#define TWO_PI_F 6.283185307f

WiFiClient espClient;
PubSubClient client(espClient);
Servo servo1;
Servo servo2;

enum RobotState {
  STATE_IDLE,
  STATE_SLEEP,
  STATE_LISTENING,
  STATE_THINKING,
  STATE_SPEAKING,
  STATE_HAPPY,
  STATE_ERROR
};

RobotState currentState = STATE_IDLE;
unsigned long stateEnteredAt = 0;
unsigned long lastServoUpdate = 0;
unsigned long lastStateChangeAt = 0;

int currentAngle1 = NEUTRAL_1;
int currentAngle2 = NEUTRAL_2;
int targetAngle1 = NEUTRAL_1;
int targetAngle2 = NEUTRAL_2;

String pendingRequestId;
String pendingActionId;
String pendingUrl;
bool playbackPending = false;
bool playbackInProgress = false;

static uint16_t readLe16(const uint8_t* p) {
  return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static uint32_t readLe32(const uint8_t* p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

int clampAngle(int angle) {
  if (angle < 0) return 0;
  if (angle > 180) return 180;
  return angle;
}

const char* stateToString(RobotState state) {
  switch (state) {
    case STATE_IDLE: return "idle";
    case STATE_SLEEP: return "sleep";
    case STATE_LISTENING: return "listening";
    case STATE_THINKING: return "thinking";
    case STATE_SPEAKING: return "speaking";
    case STATE_HAPPY: return "happy";
    case STATE_ERROR: return "error";
    default: return "idle";
  }
}

bool parseState(const String& raw, RobotState& out) {
  String s = raw;
  s.toLowerCase();

  if (s == "idle") { out = STATE_IDLE; return true; }
  if (s == "sleep") { out = STATE_SLEEP; return true; }
  if (s == "listening") { out = STATE_LISTENING; return true; }
  if (s == "thinking") { out = STATE_THINKING; return true; }
  if (s == "speaking") { out = STATE_SPEAKING; return true; }
  if (s == "happy") { out = STATE_HAPPY; return true; }
  if (s == "error") { out = STATE_ERROR; return true; }

  return false;
}

bool publishAudioAck(const String& requestId,
                    const String& actionId,
                    const String& status,
                    const String& errorMsg = "") {
  JsonDocument doc;
  doc["request_id"] = requestId;
  doc["action_id"] = actionId;
  doc["device_id"] = audio_device_id;
  doc["status"] = status;
  doc["error"] = errorMsg;
  doc["ts"] = (unsigned long)(millis() / 1000);

  String out;
  serializeJson(doc, out);
  return client.publish(mqtt_topic_audio_ack, out.c_str(), true);
}

bool publishServoAck(const String& requestId,
                    const String& userId,
                    const String& status,
                    const String& error,
                    const char* state) {
  JsonDocument doc;
  doc["request_id"] = requestId;
  doc["user_id"] = userId;
  doc["device_id"] = servo_device_id;
  doc["status"] = status;
  doc["error"] = error;
  doc["state"] = state;
  doc["ts"] = (unsigned long)(millis() / 1000);

  String out;
  serializeJson(doc, out);
  return client.publish(mqtt_topic_state_ack, out.c_str(), false);
}

bool applyState(RobotState nextState, bool force = false) {
  unsigned long now = millis();

  if (!force && nextState == currentState) {
    return false;
  }

  if (!force) {
    if (now - lastStateChangeAt < MIN_STATE_CHANGE_INTERVAL_MS) {
      Serial.println("[SERVO] Transition ignored: too fast");
      return false;
    }

    bool sleepIdlePair =
      (currentState == STATE_SLEEP && nextState == STATE_IDLE) ||
      (currentState == STATE_IDLE && nextState == STATE_SLEEP);

    if (sleepIdlePair && (now - stateEnteredAt) < SLEEP_IDLE_MIN_HOLD_MS) {
      Serial.println("[SERVO] Transition ignored: sleep/idle hold guard");
      return false;
    }
  }

  currentState = nextState;
  stateEnteredAt = now;
  lastStateChangeAt = now;
  Serial.print("[SERVO] New state: ");
  Serial.println(stateToString(currentState));
  return true;
}

int approachAngle(int currentValue, int targetValue, int step) {
  if (currentValue < targetValue) {
    currentValue += step;
    if (currentValue > targetValue) currentValue = targetValue;
  } else if (currentValue > targetValue) {
    currentValue -= step;
    if (currentValue < targetValue) currentValue = targetValue;
  }
  return clampAngle(currentValue);
}

float sineWave(unsigned long elapsedMs, unsigned long periodMs) {
  if (periodMs == 0) return 0.0f;
  float phase = (float)(elapsedMs % periodMs) / (float)periodMs;
  return sinf(phase * TWO_PI_F);
}

void computeTargets() {
  unsigned long elapsed = millis() - stateEnteredAt;

  switch (currentState) {
    case STATE_SLEEP:
      targetAngle1 = SLEEP_1;
      targetAngle2 = SLEEP_2;
      break;

    case STATE_IDLE:
      targetAngle1 = NEUTRAL_1;
      targetAngle2 = NEUTRAL_2;
      break;

    case STATE_LISTENING: {
      float wave = sineWave(elapsed, LISTENING_PERIOD_MS);
      targetAngle1 = NEUTRAL_1;
      targetAngle2 = NEUTRAL_2 + (int)roundf(wave * LISTENING_AMPLITUDE);
      break;
    }

    case STATE_THINKING: {
      float wave = sineWave(elapsed, THINKING_PERIOD_MS);
      targetAngle1 = NEUTRAL_1 + (int)roundf(wave * THINKING_AMPLITUDE);
      targetAngle2 = NEUTRAL_2;
      break;
    }

    case STATE_SPEAKING: {
      float wave = sineWave(elapsed, SPEAKING_PERIOD_MS);
      targetAngle1 = NEUTRAL_1 + (int)roundf(wave * SPEAKING_AMPLITUDE);
      if (POWER_LIMITED_MODE) {
        targetAngle2 = NEUTRAL_2;
      } else {
        targetAngle2 = NEUTRAL_2 - (int)roundf(wave * SPEAKING_AMPLITUDE);
      }
      break;
    }

    case STATE_HAPPY: {
      if (elapsed < HAPPY_DURATION_MS) {
        float wave = sineWave(elapsed, HAPPY_PERIOD_MS);
        targetAngle1 = NEUTRAL_1 + (int)roundf(wave * HAPPY_AMPLITUDE);
        if (POWER_LIMITED_MODE) {
          targetAngle2 = NEUTRAL_2;
        } else {
          targetAngle2 = NEUTRAL_2 - (int)roundf(wave * HAPPY_AMPLITUDE);
        }
      } else {
        applyState(STATE_IDLE, true);
      }
      break;
    }

    case STATE_ERROR: {
      if (elapsed < ERROR_HOLD_MS) {
        targetAngle1 = SLEEP_1;
        targetAngle2 = SLEEP_2;
      } else {
        applyState(STATE_IDLE, true);
      }
      break;
    }

    default:
      targetAngle1 = NEUTRAL_1;
      targetAngle2 = NEUTRAL_2;
      break;
  }
}

void updateServos() {
  unsigned long now = millis();
  if (now - lastServoUpdate < SERVO_UPDATE_INTERVAL_MS) {
    return;
  }
  lastServoUpdate = now;

  bool move1 = (currentAngle1 != targetAngle1);
  bool move2 = (currentAngle2 != targetAngle2);

  if (POWER_LIMITED_MODE && move1 && move2) {
    int delta1 = abs(targetAngle1 - currentAngle1);
    int delta2 = abs(targetAngle2 - currentAngle2);
    if (delta1 >= delta2) {
      currentAngle1 = approachAngle(currentAngle1, targetAngle1, SERVO_STEP_DEG);
    } else {
      currentAngle2 = approachAngle(currentAngle2, targetAngle2, SERVO_STEP_DEG);
    }
  } else {
    if (move1) currentAngle1 = approachAngle(currentAngle1, targetAngle1, SERVO_STEP_DEG);
    if (move2) currentAngle2 = approachAngle(currentAngle2, targetAngle2, SERVO_STEP_DEG);
  }

  servo1.write(currentAngle1);
  servo2.write(currentAngle2);
}

void backgroundTick(uint16_t sleepMs = 0) {
  client.loop();
  computeTargets();
  updateServos();
  if (sleepMs > 0) {
    delay(sleepMs);
  }
}

void setupI2S() {
  i2s_config_t config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = DMA_BUF_COUNT,
    .dma_buf_len = DMA_BUF_LEN,
    .use_apll = true
  };

  i2s_pin_config_t pins = {
    .bck_io_num = I2S_BCLK,
    .ws_io_num = I2S_LRC,
    .data_out_num = I2S_DOUT,
    .data_in_num = I2S_PIN_NO_CHANGE
  };

  i2s_driver_install(I2S_NUM_0, &config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pins);
  i2s_zero_dma_buffer(I2S_NUM_0);
}

size_t readExact(WiFiClient* stream, uint8_t* buf, size_t size, uint32_t timeoutMs = 2000) {
  size_t total = 0;
  uint32_t lastProgress = millis();

  while (total < size) {
    if (millis() - lastProgress > timeoutMs) {
      Serial.println("[WARN] readExact timeout");
      break;
    }

    int available = stream->available();
    if (available <= 0) {
      if (!stream->connected()) break;
      backgroundTick(1);
      continue;
    }

    size_t toRead = min((size_t)available, size - total);
    size_t got = stream->readBytes(buf + total, toRead);
    if (got == 0) {
      backgroundTick(1);
      continue;
    }

    total += got;
    lastProgress = millis();
  }

  return total;
}

bool playAudio(const String& url) {
  HTTPClient http;
  http.begin(url);
  http.setTimeout(10000);

  int code = http.GET();
  if (code != HTTP_CODE_OK) {
    Serial.printf("[ERR] HTTP %d\n", code);
    http.end();
    return false;
  }

  int contentLength = http.getSize();
  Serial.printf("[INFO] Content-Length: %d bytes\n", contentLength);

  int expectedAudioBytes = (contentLength > 44) ? (contentLength - 44) : -1;
  size_t sentAudioBytes = 0;
  bool streamTimedOut = false;

  WiFiClient* stream = http.getStreamPtr();

  uint8_t header[44];
  if (readExact(stream, header, 44, 3000) < 44) {
    Serial.println("[ERR] Incomplete WAV header");
    http.end();
    return false;
  }

  if (header[0] != 'R' || header[1] != 'I' || header[2] != 'F' || header[3] != 'F') {
    Serial.println("[WARN] RIFF signature missing");
  }

  uint16_t channels = readLe16(header + 22);
  uint32_t wavSampleRate = readLe32(header + 24);
  uint16_t bitsPerSample = readLe16(header + 34);

  if (bitsPerSample != 16) {
    Serial.printf("[ERR] Unsupported WAV bits: %d\n", bitsPerSample);
    http.end();
    return false;
  }

  if (channels != 1) {
    Serial.printf("[ERR] Unsupported WAV channels (mono required): %d\n", channels);
    http.end();
    return false;
  }

  esp_err_t clkErr = i2s_set_clk(I2S_NUM_0, (int)wavSampleRate, I2S_BITS_PER_SAMPLE_16BIT, I2S_CHANNEL_MONO);
  if (clkErr != ESP_OK) {
    Serial.printf("[ERR] i2s_set_clk: %d\n", clkErr);
    http.end();
    return false;
  }

  Serial.printf("[INFO] WAV format: %d Hz, %d ch, %d bits\n", wavSampleRate, channels, bitsPerSample);

  size_t prebufferBytes = (wavSampleRate * 2 * PREBUFFER_MS) / 1000;
  prebufferBytes = ((prebufferBytes / HTTP_BUF_SIZE) + 1) * HTTP_BUF_SIZE;
  if (expectedAudioBytes > 0 && prebufferBytes > (size_t)expectedAudioBytes) {
    prebufferBytes = (size_t)expectedAudioBytes;
  }

  uint8_t* prebuf = (uint8_t*)malloc(prebufferBytes);
  if (prebuf) {
    Serial.printf("[INFO] Pre-buffering %u bytes...\n", (unsigned int)prebufferBytes);
    size_t filled = readExact(stream, prebuf, prebufferBytes, 3000);
    Serial.printf("[INFO] Pre-buffer filled: %u bytes\n", (unsigned int)filled);

    if (filled > 0) {
      filled &= ~((size_t)1);
      int16_t* samples = (int16_t*)prebuf;
      for (int i = 0; i < (int)(filled / 2); i++) samples[i] /= 2;

      size_t written = 0;
      esp_err_t preErr = i2s_write(I2S_NUM_0, prebuf, filled, &written, pdMS_TO_TICKS(1000));
      if (preErr != ESP_OK) {
        Serial.printf("[ERR] i2s_write prebuffer: %d\n", preErr);
      } else {
        sentAudioBytes += written;
      }
    }

    free(prebuf);
  }

  uint8_t* buffer = (uint8_t*)malloc(HTTP_BUF_SIZE);
  if (!buffer) {
    Serial.println("[ERR] malloc failed");
    http.end();
    return false;
  }

  uint32_t lastDataMs = millis();
  static const uint8_t silenceChunk[512] = {0};

  while (true) {
    if (expectedAudioBytes > 0 && sentAudioBytes >= (size_t)expectedAudioBytes) {
      break;
    }

    int available = stream->available();
    if (available <= 0) {
      backgroundTick(2);

      if (expectedAudioBytes <= 0 && !http.connected() && stream->available() <= 0) {
        break;
      }

      size_t sw = 0;
      i2s_write(I2S_NUM_0, silenceChunk, sizeof(silenceChunk), &sw, pdMS_TO_TICKS(20));

      if (millis() - lastDataMs > 8000) {
        Serial.println("[WARN] Stream idle timeout");
        streamTimedOut = true;
        break;
      }
      continue;
    }

    size_t toRead = min((size_t)available, (size_t)HTTP_BUF_SIZE);
    if (expectedAudioBytes > 0) {
      size_t remaining = (size_t)expectedAudioBytes - sentAudioBytes;
      toRead = min(toRead, remaining);
    }

    size_t got = stream->readBytes(buffer, toRead);
    if (got == 0) {
      backgroundTick(1);
      continue;
    }

    got &= ~((size_t)1);
    if (got == 0) continue;

    lastDataMs = millis();

    int16_t* samples = (int16_t*)buffer;
    for (int i = 0; i < (int)(got / 2); i++) samples[i] /= 2;

    size_t written = 0;
    esp_err_t err = i2s_write(I2S_NUM_0, buffer, got, &written, pdMS_TO_TICKS(1000));
    if (err != ESP_OK) {
      Serial.printf("[ERR] i2s_write: %d\n", err);
      break;
    }

    sentAudioBytes += written;
    backgroundTick();
  }

  free(buffer);

  uint32_t drainMs = ((uint32_t)DMA_BUF_COUNT * DMA_BUF_LEN * 1000) / (wavSampleRate * 2);
  drainMs += streamTimedOut ? 50 : 300;
  Serial.printf("[INFO] Drain DMA: %u ms\n", (unsigned int)drainMs);

  uint32_t drainStart = millis();
  while (millis() - drainStart < drainMs) {
    backgroundTick(2);
  }

  i2s_zero_dma_buffer(I2S_NUM_0);

  if (expectedAudioBytes > 0 && sentAudioBytes < (size_t)expectedAudioBytes) {
    Serial.printf("[WARN] Audio truncated: sent=%u expected=%d\n", (unsigned int)sentAudioBytes, expectedAudioBytes);
  }

  http.end();
  Serial.println("[INFO] Playback done");
  return true;
}

void handleAudioMessage(const String& msg) {
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, msg);
  if (error) {
    Serial.println("[ERR] Audio JSON parse error");
    return;
  }

  String requestId = doc["request_id"] | "";
  String actionId = doc["action_id"] | "";
  String url = doc["url"] | "";

  if (url.length() <= 5) {
    publishAudioAck(requestId, actionId, "error", "missing_url");
    return;
  }

  if (playbackInProgress || playbackPending) {
    publishAudioAck(requestId, actionId, "error", "device_busy");
    return;
  }

  pendingRequestId = requestId;
  pendingActionId = actionId;
  pendingUrl = url;
  playbackPending = true;

  publishAudioAck(requestId, actionId, "started");
}

void handleRobotStateMessage(const String& msg) {
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, msg);
  if (err) {
    Serial.println("[ERR] State JSON parse error");
    publishServoAck("", "", "error", "invalid_json", stateToString(currentState));
    return;
  }

  String requestId = doc["request_id"] | "";
  String userId = doc["user_id"] | "";
  String stateRaw = doc["state"] | "";

  RobotState nextState;
  if (!parseState(stateRaw, nextState)) {
    Serial.print("[ERR] Invalid state: ");
    Serial.println(stateRaw);
    publishServoAck(requestId, userId, "error", "invalid_state", stateToString(currentState));
    return;
  }

  bool changed = applyState(nextState);
  if (changed) {
    publishServoAck(requestId, userId, "applied", "", stateToString(currentState));
  } else {
    publishServoAck(requestId, userId, "ignored", "transition_guard", stateToString(currentState));
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  msg.reserve(length + 1);
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  Serial.println("---- MQTT ----");
  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Payload: ");
  Serial.println(msg);

  if (strcmp(topic, mqtt_topic_state) == 0) {
    handleRobotStateMessage(msg);
    return;
  }

  if (strcmp(topic, mqtt_topic_audio_request) == 0 || strcmp(topic, mqtt_topic_audio_request_alt) == 0) {
    handleAudioMessage(msg);
    return;
  }

  Serial.println("[WARN] Unknown topic ignored");
}

void setupWifi() {
  delay(10);
  Serial.println("[WIFI] Connecting...");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("[WIFI] Connected");
  Serial.print("[WIFI] IP: ");
  Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("[MQTT] Connecting...");

    if (client.connect("ESP32_AUDIO_SERVO")) {
      Serial.println("OK");
      client.subscribe(mqtt_topic_audio_request);
      client.subscribe(mqtt_topic_audio_request_alt);
      client.subscribe(mqtt_topic_state);

      Serial.print("[MQTT] Subscribed: ");
      Serial.println(mqtt_topic_audio_request);
      Serial.print("[MQTT] Subscribed: ");
      Serial.println(mqtt_topic_audio_request_alt);
      Serial.print("[MQTT] Subscribed: ");
      Serial.println(mqtt_topic_state);
    } else {
      Serial.print("[MQTT] Failed rc=");
      Serial.print(client.state());
      Serial.println(" retry in 1s");
      delay(1000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(800);

  servo1.setPeriodHertz(SERVO_PWM_HZ);
  servo2.setPeriodHertz(SERVO_PWM_HZ);
  servo1.attach(SERVO1_PIN, SERVO_MIN_US, SERVO_MAX_US);
  servo2.attach(SERVO2_PIN, SERVO_MIN_US, SERVO_MAX_US);

  servo1.write(currentAngle1);
  servo2.write(currentAngle2);
  applyState(STATE_IDLE, true);

  setupWifi();
  setupI2S();

  client.setServer(mqtt_server, 1883);
  client.setBufferSize(1024);
  client.setCallback(callback);

  reconnectMQTT();
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }

  client.loop();

  if (playbackPending && !playbackInProgress) {
    playbackInProgress = true;
    playbackPending = false;

    String requestId = pendingRequestId;
    String actionId = pendingActionId;
    String url = pendingUrl;

    if (START_DELAY_MS > 0) {
      Serial.printf("[INFO] Start delay: %d ms\n", START_DELAY_MS);
      uint32_t waitStart = millis();
      while (millis() - waitStart < START_DELAY_MS) {
        backgroundTick(10);
      }
    }

    bool ok = playAudio(url);
    publishAudioAck(requestId, actionId, ok ? "done" : "error", ok ? "" : "playback_failed");

    playbackInProgress = false;
  }

  computeTargets();
  updateServos();
}
