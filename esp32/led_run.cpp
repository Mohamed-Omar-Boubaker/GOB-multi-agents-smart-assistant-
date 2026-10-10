#include <Adafruit_NeoPixel.h>

#define PIN        23
#define NUM_LEDS   10

Adafruit_NeoPixel strip(NUM_LEDS, PIN, NEO_GRB + NEO_KHZ800);

// Fonction pour définir une couleur globale
void setColor(int r, int g, int b) {
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}

void setup() {
  strip.begin();
  strip.setBrightness(60); // IMPORTANT pour éviter surcharge
  strip.show(); // tout éteint
}

void loop() {

  // 🔴 Rouge
  setColor(255, 0, 0);
  delay(1000);

  // 🟢 Vert
  setColor(0, 255, 0);
  delay(1000);

  // 🔵 Bleu
  setColor(0, 0, 255);
  delay(1000);

  // 🌈 Effet dégradé simple
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(i * 20, 0, 255 - i * 20));
  }
  strip.show();
  delay(1000);

  // ✨ Effet chenille (animation)
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.clear();
    strip.setPixelColor(i, strip.Color(255, 255, 0));
    strip.show();
    delay(100);
  }
}