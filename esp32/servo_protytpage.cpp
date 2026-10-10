#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>
#include <math.h>

// ===== SERVO PINS =====
#define SERVO1_PIN 18
#define SERVO2_PIN 19

// ===== WIFI =====
const char* ssid = "ESP32";
const char* password = "esp32test123";

// ===== MQTT =====
const char* mqtt_server = "10.93.177.189";
const char* mqtt_topic_state = "gob/robot/state";
const char* mqtt_topic_ack = "gob/robot/state/ack";
const char* device_id = "esp32_servo_01";

// ===== TUNING =====
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

bool publishAck(const String& requestId,
                const String& userId,
                const String& status,
                const String& error,
                const char* state) {
  JsonDocument doc;
  doc["request_id"] = requestId;
  doc["user_id"] = userId;
  doc["device_id"] = device_id;
  doc["status"] = status;
  doc["error"] = error;
  doc["state"] = state;
  doc["ts"] = (unsigned long)(millis() / 1000);

  String out;
  serializeJson(doc, out);
  return client.publish(mqtt_topic_ack, out.c_str(), false);
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
    // Reduce current spikes: move one servo at a time when both are pending.
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

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.println("---- MQTT ----");
  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Payload: ");
  Serial.println(message);

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, message);
  if (err) {
    Serial.println("[ERR] invalid JSON");
    publishAck("", "", "error", "invalid_json", stateToString(currentState));
    return;
  }

  String requestId = doc["request_id"] | "";
  String userId = doc["user_id"] | "";
  String stateRaw = doc["state"] | "";

  RobotState nextState;
  if (!parseState(stateRaw, nextState)) {
    Serial.print("[ERR] invalid state: ");
    Serial.println(stateRaw);
    publishAck(requestId, userId, "error", "invalid_state", stateToString(currentState));
    return;
  }

  bool changed = applyState(nextState);
  if (changed) {
    publishAck(requestId, userId, "applied", "", stateToString(currentState));
  } else {
    publishAck(requestId, userId, "ignored", "transition_guard", stateToString(currentState));
  }
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

void reconnectMqtt() {
  while (!client.connected()) {
    Serial.print("[MQTT] Connecting...");

    if (client.connect("ESP32_SERVO_ROBOT")) {
      Serial.println("OK");
      client.subscribe(mqtt_topic_state);
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

  setupWifi();

  client.setServer(mqtt_server, 1883);
  client.setBufferSize(1024);
  client.setCallback(callback);

  applyState(STATE_IDLE, true);
}

void loop() {
  if (!client.connected()) {
    reconnectMqtt();
  }

  client.loop();
  computeTargets();
  updateServos();
}