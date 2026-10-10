// ============================================================
//  GOB Agent — ESP32 Firmware Final
//  Fusionne : haut-parleur I2S (WAV over HTTP) + servos animés
//  Un seul ESP32, un seul callback MQTT, loop non-bloquant.
// ============================================================

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>
#include <driver/i2s.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>
#include <math.h>

//////////////////////////

// ─── PINS ────────────────────────────────────────────────────────────────────

#define I2S_BCLK  25
#define I2S_LRC   26
#define I2S_DOUT  22

#define SERVO1_PIN 18
#define SERVO2_PIN 19

#define LED_PIN   5
#define LED_COUNT 7

// ─── WIFI / MQTT ──────────────────────────────────────────────────────────────

const char* ssid     = "ESP32";
const char* password = "esp32test123";

const char* mqtt_server = "10.93.177.189";

// Audio topics
const char* mqtt_topic_tts_request     = "gob/audio/tts/request";
const char* mqtt_topic_tts_request_alt = "gob/audio/tts";   // compat anciens publishers
const char* mqtt_topic_tts_ack         = "gob/audio/tts/ack";

// Servo topics
const char* mqtt_topic_robot_state = "gob/robot/state";
const char* mqtt_topic_robot_ack   = "gob/robot/state/ack";

const char* audio_device_id = "esp32_speaker_01";
const char* servo_device_id = "esp32_servo_01";

WiFiClient   espClient;
PubSubClient client(espClient);
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

// ─── AUDIO CONFIG ─────────────────────────────────────────────────────────────

#define SAMPLE_RATE      22050
#define DMA_BUF_COUNT    16
#define DMA_BUF_LEN      1024
#define HTTP_BUF_SIZE    4096
#define PREBUFFER_MS     300
#define START_DELAY_MS   3000   // délai avant lecture (laisse le servo réagir)

String pendingRequestId;
String pendingActionId;
String pendingUrl;
bool   playbackPending    = false;
bool   playbackInProgress = false;

float ledPhase = 0.0f;
unsigned long lastLedUpdate = 0;
#define LED_UPDATE_INTERVAL 20

// ─── SERVO CONFIG ─────────────────────────────────────────────────────────────

#define SERVO_STEP_DEG              1
#define SERVO_UPDATE_INTERVAL_MS    30
#define POWER_LIMITED_MODE          true

#define SERVO_PWM_HZ   50
#define SERVO_MIN_US  500
#define SERVO_MAX_US 2400

// Angles extrêmes (sleep = yeux fermés / baissés)
#define SLEEP_1   10
#define SLEEP_2  90

// Angles neutres (position repos)
#define NEUTRAL_1  20
#define NEUTRAL_2 90

// Amplitudes oscillation par état
#define LISTENING_AMPLITUDE  12
#define THINKING_AMPLITUDE   12
#define SPEAKING_AMPLITUDE   14
#define HAPPY_AMPLITUDE      20

// Périodes oscillation par état (ms)
#define LISTENING_PERIOD_MS 1400
#define THINKING_PERIOD_MS  1500
#define SPEAKING_PERIOD_MS  1100
#define HAPPY_PERIOD_MS      800

// Durées états auto-retour
#define HAPPY_DURATION_MS 1800
#define ERROR_HOLD_MS     1200

// ── Guards de transition (sécurité servo) ─────────────────────────────────────
// Empêche les transitions trop rapides qui stressent les servos / créent des
// pics de courant.  Le pair sleep↔idle a sa propre garde de durée minimale.
#define MIN_STATE_CHANGE_INTERVAL_MS  120
#define SLEEP_IDLE_MIN_HOLD_MS        900

#define TWO_PI_F 6.283185307f

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

RobotState   currentState      = STATE_IDLE;
unsigned long stateEnteredAt   = 0;
unsigned long lastServoUpdate  = 0;
unsigned long lastStateChangeAt = 0;

int currentAngle1 = NEUTRAL_1;
int currentAngle2 = NEUTRAL_2;
int targetAngle1  = NEUTRAL_1;
int targetAngle2  = NEUTRAL_2;

// ─── UTILS ───────────────────────────────────────────────────────────────────

static uint16_t readLe16(const uint8_t* p) {
  return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}
static uint32_t readLe32(const uint8_t* p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8)
       | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

// ─── SERVO HELPERS ────────────────────────────────────────────────────────────

int clampAngle(int a) {
  if (a < 0)   return 0;
  if (a > 180) return 180;
  return a;
}

const char* stateToString(RobotState s) {
  switch (s) {
    case STATE_IDLE:      return "idle";
    case STATE_SLEEP:     return "sleep";
    case STATE_LISTENING: return "listening";
    case STATE_THINKING:  return "thinking";
    case STATE_SPEAKING:  return "speaking";
    case STATE_HAPPY:     return "happy";
    case STATE_ERROR:     return "error";
    default:              return "idle";
  }
}

bool parseState(const String& raw, RobotState& out) {
  String s = raw;
  s.toLowerCase();
  if (s == "idle")      { out = STATE_IDLE;      return true; }
  if (s == "sleep")     { out = STATE_SLEEP;     return true; }
  if (s == "listening") { out = STATE_LISTENING; return true; }
  if (s == "thinking")  { out = STATE_THINKING;  return true; }
  if (s == "speaking")  { out = STATE_SPEAKING;  return true; }
  if (s == "happy")     { out = STATE_HAPPY;     return true; }
  if (s == "error")     { out = STATE_ERROR;     return true; }
  return false;
}

// ─── applyState ───────────────────────────────────────────────────────────────
// force=true : bypasse tous les guards (usage interne uniquement)
// force=false : applique les guards de sécurité servo

bool applyState(RobotState nextState, bool force = false) {
  unsigned long now = millis();

  if (!force && nextState == currentState) return false;

  if (!force) {
    // Guard 1 : transitions trop rapides
    if (now - lastStateChangeAt < MIN_STATE_CHANGE_INTERVAL_MS) {
      Serial.println("[SERVO] Transition ignorée: trop rapide");
      return false;
    }
    // Guard 2 : paire sleep↔idle doit rester en place assez longtemps
    bool sleepIdlePair =
      (currentState == STATE_SLEEP && nextState == STATE_IDLE) ||
      (currentState == STATE_IDLE  && nextState == STATE_SLEEP);
    if (sleepIdlePair && (now - stateEnteredAt) < SLEEP_IDLE_MIN_HOLD_MS) {
      Serial.println("[SERVO] Transition ignorée: sleep/idle hold guard");
      return false;
    }
  }

  currentState      = nextState;
  stateEnteredAt    = now;
  lastStateChangeAt = now;
  Serial.print("[SERVO] Nouvel état: ");
  Serial.println(stateToString(currentState));
  return true;
}

int approachAngle(int cur, int tgt, int step) {
  if (cur < tgt) { cur += step; if (cur > tgt) cur = tgt; }
  else if (cur > tgt) { cur -= step; if (cur < tgt) cur = tgt; }
  return clampAngle(cur);
}

float sineWave(unsigned long elapsedMs, unsigned long periodMs) {
  if (periodMs == 0) return 0.0f;
  float phase = (float)(elapsedMs % periodMs) / (float)periodMs;
  return sinf(phase * TWO_PI_F);
}

// ─── computeTargets ───────────────────────────────────────────────────────────

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
      float w = sineWave(elapsed, LISTENING_PERIOD_MS);
      targetAngle1 = NEUTRAL_1;
      targetAngle2 = NEUTRAL_2 + (int)roundf(w * LISTENING_AMPLITUDE);
      break;
    }

    case STATE_THINKING: {
      float w = sineWave(elapsed, THINKING_PERIOD_MS);
      targetAngle1 = NEUTRAL_1 + (int)roundf(w * THINKING_AMPLITUDE);
      targetAngle2 = NEUTRAL_2;
      break;
    }

    case STATE_SPEAKING: {
      float w = sineWave(elapsed, SPEAKING_PERIOD_MS);
      targetAngle1 = NEUTRAL_1 + (int)roundf(w * SPEAKING_AMPLITUDE);
      targetAngle2 = POWER_LIMITED_MODE
                   ? NEUTRAL_2
                   : NEUTRAL_2 - (int)roundf(w * SPEAKING_AMPLITUDE);
      break;
    }

    case STATE_HAPPY: {
      if (elapsed < HAPPY_DURATION_MS) {
        float w = sineWave(elapsed, HAPPY_PERIOD_MS);
        targetAngle1 = NEUTRAL_1 + (int)roundf(w * HAPPY_AMPLITUDE);
        targetAngle2 = POWER_LIMITED_MODE
                     ? NEUTRAL_2
                     : NEUTRAL_2 - (int)roundf(w * HAPPY_AMPLITUDE);
      } else {
        applyState(STATE_IDLE, true);  // retour auto idle après HAPPY_DURATION_MS
      }
      break;
    }

    case STATE_ERROR: {
      if (elapsed < ERROR_HOLD_MS) {
        targetAngle1 = SLEEP_1;
        targetAngle2 = SLEEP_2;
      } else {
        applyState(STATE_IDLE, true);  // retour auto idle après ERROR_HOLD_MS
      }
      break;
    }

    default:
      targetAngle1 = NEUTRAL_1;
      targetAngle2 = NEUTRAL_2;
      break;
  }
}

// ─── updateServos ─────────────────────────────────────────────────────────────

void updateServos() {
  unsigned long now = millis();
  if (now - lastServoUpdate < SERVO_UPDATE_INTERVAL_MS) return;
  lastServoUpdate = now;

  bool move1 = (currentAngle1 != targetAngle1);
  bool move2 = (currentAngle2 != targetAngle2);

  if (POWER_LIMITED_MODE && move1 && move2) {
    // Un seul servo à la fois pour éviter les pics de courant
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

void updateLEDs() {
  unsigned long now = millis();
  if (now - lastLedUpdate < LED_UPDATE_INTERVAL) return;
  lastLedUpdate = now;

  ledPhase += 0.05f;
  if (ledPhase > TWO_PI_F) ledPhase -= TWO_PI_F;

  for (int i = 0; i < LED_COUNT; i++) {
    float wave = sinf(ledPhase + i * 0.5f);
    float intensity = (wave + 1.0f) / 2.0f;

    uint8_t r = 0;
    uint8_t g = 0;
    uint8_t b = 0;

    switch (currentState) {
      case STATE_IDLE:
        b = 10 + (uint8_t)(20 * intensity);
        break;

      case STATE_LISTENING:
        b = (uint8_t)(80 * intensity);
        break;

      case STATE_THINKING:
        r = (uint8_t)(60 * intensity);
        g = (uint8_t)(60 * intensity);
        break;

      case STATE_SPEAKING:
        g = (uint8_t)(100 * intensity);
        break;

      case STATE_HAPPY:
        r = (uint8_t)(80 * intensity);
        b = (uint8_t)(80 * (1.0f - intensity));
        break;

      case STATE_ERROR:
        if ((now / 200) % 2 == 0) {
          r = 100;
        }
        break;

      default:
        break;
    }

    strip.setPixelColor(i, strip.Color(r, g, b));
  }

  strip.show();
}

// ─── pumpServos ───────────────────────────────────────────────────────────────
// À appeler dans toute boucle bloquante pour garder les servos vivants.

void pumpServos() {
  computeTargets();
  updateServos();
  updateLEDs();
}

// ─── I2S ─────────────────────────────────────────────────────────────────────

void setupI2S() {
  i2s_config_t config = {
    .mode                 = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate          = SAMPLE_RATE,
    .bits_per_sample      = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format       = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags     = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count        = DMA_BUF_COUNT,
    .dma_buf_len          = DMA_BUF_LEN,
    .use_apll             = true
  };
  i2s_pin_config_t pins = {
    .bck_io_num   = I2S_BCLK,
    .ws_io_num    = I2S_LRC,
    .data_out_num = I2S_DOUT,
    .data_in_num  = I2S_PIN_NO_CHANGE
  };
  i2s_driver_install(I2S_NUM_0, &config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pins);
  i2s_zero_dma_buffer(I2S_NUM_0);
}

// ─── readExact ────────────────────────────────────────────────────────────────

size_t readExact(WiFiClient* stream, uint8_t* buf, size_t size, uint32_t timeoutMs = 2000) {
  size_t   total        = 0;
  uint32_t lastProgress = millis();

  while (total < size) {
    if (millis() - lastProgress > timeoutMs) {
      Serial.println("[WARN] readExact timeout");
      break;
    }
    int available = stream->available();
    if (available <= 0) {
      if (!stream->connected()) break;
      pumpServos();   // servos vivants pendant attente réseau
      delay(1);
      continue;
    }
    size_t toRead = min((size_t)available, size - total);
    size_t got    = stream->readBytes(buf + total, toRead);
    if (got == 0) { delay(1); continue; }
    total        += got;
    lastProgress  = millis();
  }
  return total;
}

// ─── ACK Audio ────────────────────────────────────────────────────────────────

bool publishAudioAck(const String& requestId, const String& actionId,
                     const String& status, const String& errorMsg = "") {
  JsonDocument doc;
  doc["request_id"] = requestId;
  doc["action_id"]  = actionId;
  doc["device_id"]  = audio_device_id;
  doc["status"]     = status;
  doc["error"]      = errorMsg;
  doc["ts"]         = (unsigned long)(millis() / 1000);
  String out;
  serializeJson(doc, out);
  return client.publish(mqtt_topic_tts_ack, out.c_str(), true);
}

// ─── ACK Servo ────────────────────────────────────────────────────────────────

bool publishServoAck(const String& requestId, const String& userId,
                     const String& status,    const String& error,
                     const char* state) {
  JsonDocument doc;
  doc["request_id"] = requestId;
  doc["user_id"]    = userId;
  doc["device_id"]  = servo_device_id;
  doc["status"]     = status;
  doc["error"]      = error;
  doc["state"]      = state;
  doc["ts"]         = (unsigned long)(millis() / 1000);
  String out;
  serializeJson(doc, out);
  return client.publish(mqtt_topic_robot_ack, out.c_str(), false);
}

// ─── playAudio ────────────────────────────────────────────────────────────────

bool playAudio(String url) {
  HTTPClient http;
  http.begin(url);
  http.setTimeout(10000);

  int code = http.GET();
  if (code != HTTP_CODE_OK) {
    Serial.printf("[ERR] HTTP %d\n", code);
    http.end();
    return false;
  }

  int contentLength    = http.getSize();
  int expectedAudio    = (contentLength > 44) ? (contentLength - 44) : -1;
  size_t sentAudio     = 0;
  bool   streamTimedOut = false;

  Serial.printf("[AUDIO] Content-Length: %d bytes\n", contentLength);

  WiFiClient* stream = http.getStreamPtr();

  // ── Lecture header WAV ────────────────────────────────────────────────────
  uint8_t header[44];
  if (readExact(stream, header, 44, 3000) < 44) {
    Serial.println("[ERR] WAV header incomplet");
    http.end();
    return false;
  }
  if (header[0] != 'R' || header[1] != 'I' || header[2] != 'F' || header[3] != 'F') {
    Serial.println("[WARN] Signature RIFF absente");
  }

  uint16_t channels      = readLe16(header + 22);
  uint32_t wavSampleRate = readLe32(header + 24);
  uint16_t bitsPerSample = readLe16(header + 34);

  if (bitsPerSample != 16) {
    Serial.printf("[ERR] WAV non supporté: %d bits\n", bitsPerSample);
    http.end();
    return false;
  }
  if (channels != 1) {
    Serial.printf("[ERR] WAV doit être mono: %d channels\n", channels);
    http.end();
    return false;
  }

  esp_err_t clkErr = i2s_set_clk(I2S_NUM_0, (int)wavSampleRate,
                                  I2S_BITS_PER_SAMPLE_16BIT, I2S_CHANNEL_MONO);
  if (clkErr != ESP_OK) {
    Serial.printf("[ERR] i2s_set_clk: %d\n", clkErr);
    http.end();
    return false;
  }
  Serial.printf("[AUDIO] WAV: %d Hz, %d ch, %d bits\n",
                wavSampleRate, channels, bitsPerSample);

  // ── Pre-buffer ────────────────────────────────────────────────────────────
  size_t prebufBytes = (wavSampleRate * 2 * PREBUFFER_MS) / 1000;
  prebufBytes = ((prebufBytes / HTTP_BUF_SIZE) + 1) * HTTP_BUF_SIZE;
  if (expectedAudio > 0 && prebufBytes > (size_t)expectedAudio)
    prebufBytes = (size_t)expectedAudio;

  uint8_t* prebuf = (uint8_t*)malloc(prebufBytes);
  if (prebuf) {
    Serial.printf("[AUDIO] Pre-buffer: %d bytes...\n", prebufBytes);
    size_t filled = readExact(stream, prebuf, prebufBytes, 3000);
    Serial.printf("[AUDIO] Pre-buffer rempli: %d bytes\n", filled);

    if (filled > 0) {
      filled &= ~((size_t)1);                          // aligne 16-bit
      int16_t* s = (int16_t*)prebuf;
      for (int i = 0; i < (int)(filled / 2); i++) s[i] /= 2;

      size_t written;
      esp_err_t e = i2s_write(I2S_NUM_0, prebuf, filled, &written, pdMS_TO_TICKS(1000));
      if (e != ESP_OK) Serial.printf("[ERR] i2s_write prebuf: %d\n", e);
      else             sentAudio += written;
    }
    free(prebuf);
  }

  // ── Stream du reste ───────────────────────────────────────────────────────
  uint8_t* buffer = (uint8_t*)malloc(HTTP_BUF_SIZE);
  if (!buffer) {
    Serial.println("[ERR] malloc échoué");
    http.end();
    return false;
  }

  static const uint8_t silenceChunk[512] = {0};
  uint32_t lastDataMs = millis();

  while (true) {
    // Sortie propre si on a tout envoyé
    if (expectedAudio > 0 && sentAudio >= (size_t)expectedAudio) break;

    int available = stream->available();
    if (available <= 0) {
      client.loop();
      pumpServos();   // ← servos vivants pendant stall réseau
      delay(2);

      if (expectedAudio <= 0 && !http.connected() && stream->available() <= 0) break;

      // Silence pour éviter que le DAC répète le dernier sample
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
    if (expectedAudio > 0) {
      size_t remaining = (size_t)expectedAudio - sentAudio;
      toRead = min(toRead, remaining);
    }

    size_t got = stream->readBytes(buffer, toRead);
    if (got == 0) continue;
    got &= ~((size_t)1);   // aligne 16-bit
    if (got == 0) continue;

    lastDataMs = millis();

    int16_t* s = (int16_t*)buffer;
    for (int i = 0; i < (int)(got / 2); i++) s[i] /= 2;

    size_t written;
    esp_err_t err = i2s_write(I2S_NUM_0, buffer, got, &written, pdMS_TO_TICKS(1000));
    if (err != ESP_OK) {
      Serial.printf("[ERR] i2s_write: %d\n", err);
      break;
    }
    sentAudio += written;

    client.loop();
    pumpServos();   // ← servos vivants pendant lecture
  }

  free(buffer);

  // ── Drain DMA — pompe les servos pendant l'attente ────────────────────────
  uint32_t drain_ms = ((uint32_t)DMA_BUF_COUNT * DMA_BUF_LEN * 1000) / (wavSampleRate * 2);
  drain_ms += streamTimedOut ? 50 : 300;
  Serial.printf("[AUDIO] Drain DMA: %d ms\n", drain_ms);

  uint32_t drainStart = millis();
  while (millis() - drainStart < drain_ms) {
    pumpServos();
    client.loop();
    delay(5);
  }

  i2s_zero_dma_buffer(I2S_NUM_0);

  if (expectedAudio > 0 && sentAudio < (size_t)expectedAudio) {
    Serial.printf("[WARN] Audio tronqué: sent=%u expected=%d\n",
                  (unsigned int)sentAudio, expectedAudio);
  }

  http.end();
  Serial.println("[AUDIO] Playback terminé");
  return true;
}

// ─── MQTT Callback (routeur unique) ──────────────────────────────────────────

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  msg.reserve(length);
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.print("[MQTT] Topic: ");  Serial.println(topic);
  Serial.print("[MQTT] Payload: "); Serial.println(msg);

  String topicStr(topic);

  // ── Route → Audio ─────────────────────────────────────────────────────────
  if (topicStr == mqtt_topic_tts_request || topicStr == mqtt_topic_tts_request_alt) {
    JsonDocument doc;
    if (deserializeJson(doc, msg)) {
      Serial.println("[ERR] JSON audio invalide");
      return;
    }
    String requestId = doc["request_id"] | "";
    String actionId  = doc["action_id"]  | "";
    String url       = doc["url"]        | "";

    if (url.length() <= 5) {
      publishAudioAck(requestId, actionId, "error", "missing_url");
      return;
    }
    if (playbackInProgress || playbackPending) {
      publishAudioAck(requestId, actionId, "error", "device_busy");
      return;
    }
    pendingRequestId  = requestId;
    pendingActionId   = actionId;
    pendingUrl        = url;
    playbackPending   = true;
    publishAudioAck(requestId, actionId, "started");
    return;
  }

  // ── Route → Servo ─────────────────────────────────────────────────────────
  if (topicStr == mqtt_topic_robot_state) {
    JsonDocument doc;
    if (deserializeJson(doc, msg)) {
      Serial.println("[ERR] JSON servo invalide");
      publishServoAck("", "", "error", "invalid_json", stateToString(currentState));
      return;
    }
    String requestId = doc["request_id"] | "";
    String userId    = doc["user_id"]    | "";
    String stateRaw  = doc["state"]      | "";

    RobotState nextState;
    if (!parseState(stateRaw, nextState)) {
      Serial.print("[ERR] État inconnu: "); Serial.println(stateRaw);
      publishServoAck(requestId, userId, "error", "invalid_state", stateToString(currentState));
      return;
    }

    bool changed = applyState(nextState);
    if (changed) {
      publishServoAck(requestId, userId, "applied", "", stateToString(currentState));
    } else {
      publishServoAck(requestId, userId, "ignored", "transition_guard", stateToString(currentState));
    }
    return;
  }

  Serial.println("[WARN] Topic non géré");
}

// ─── MQTT Reconnect ───────────────────────────────────────────────────────────

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.println("[MQTT] Connexion...");
    if (client.connect("ESP32_GOB_AGENT")) {
      Serial.println("[MQTT] Connecté");
      client.subscribe(mqtt_topic_tts_request);
      client.subscribe(mqtt_topic_tts_request_alt);
      client.subscribe(mqtt_topic_robot_state);
    } else {
      Serial.printf("[MQTT] Échec rc=%d, retry 1s\n", client.state());
      delay(1000);
    }
  }
}

// ─── Setup ────────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(800);
  Serial.println("[GOB] START");

  strip.begin();
  strip.show();

  // Servos
  servo1.setPeriodHertz(SERVO_PWM_HZ);
  servo2.setPeriodHertz(SERVO_PWM_HZ);
  servo1.attach(SERVO1_PIN, SERVO_MIN_US, SERVO_MAX_US);
  servo2.attach(SERVO2_PIN, SERVO_MIN_US, SERVO_MAX_US);
  servo1.write(currentAngle1);
  servo2.write(currentAngle2);
  applyState(STATE_IDLE, true);
  updateLEDs();

  // WiFi
  WiFi.begin(ssid, password);
  Serial.print("[WIFI] Connexion");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\n[WIFI] IP: " + WiFi.localIP().toString());

  // Test HTTP server
  WiFiClient test;
  Serial.println(test.connect("10.93.177.189", 8005)
    ? "[HTTP] Serveur joignable"
    : "[HTTP] Serveur NON joignable");

  // I2S
  setupI2S();

  // MQTT
  client.setServer(mqtt_server, 1883);
  client.setBufferSize(1024);
  client.setCallback(callback);
  reconnectMQTT();

  Serial.println("[GOB] Prêt");
}

// ─── Loop ─────────────────────────────────────────────────────────────────────

void loop() {
  if (!client.connected()) reconnectMQTT();
  client.loop();

  // Servos : toujours animés, même hors playback
  computeTargets();
  updateServos();
  updateLEDs();

  // Playback audio en attente
  if (playbackPending && !playbackInProgress) {
    playbackInProgress = true;
    playbackPending    = false;

    String requestId = pendingRequestId;
    String actionId  = pendingActionId;
    String url       = pendingUrl;

    // Délai de démarrage — servos + MQTT restent actifs
    if (START_DELAY_MS > 0) {
      Serial.printf("[AUDIO] Délai démarrage: %d ms\n", START_DELAY_MS);
      uint32_t waitStart = millis();
      while (millis() - waitStart < START_DELAY_MS) {
        client.loop();
        computeTargets();
        updateServos();
        updateLEDs();
        delay(10);
      }
    }

    bool ok = playAudio(url);
    publishAudioAck(requestId, actionId, ok ? "done" : "error",
                                         ok ? ""     : "playback_failed");
    playbackInProgress = false;
  }
}
