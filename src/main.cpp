#include <main.hpp>

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<SK6812, LED>(leds, NUM_LEDS);

  pinMode(BTN1, INPUT);
  pinMode(BTN2, INPUT);
  pinMode(CAP_SEND, OUTPUT);
  // Btn1.set_CS_AutocaL_Millis(0xFFFFFFFF);
  // Btn2.set_CS_AutocaL_Millis(0xFFFFFFFF);

  pinMode(BUILTIN_LED, OUTPUT);
  pinMode(CHRG_PIN, INPUT);
  pinMode(STBY_PIN, INPUT);

}

void loop() {
  static uint8_t hue = 0;
  for (uint8_t i = 0; i < NUM_LEDS; i++){
    leds[i] = CHSV((hue + 16*i) % 255, 255, 255);
  }
  FastLED.show();
  FastLED.delay(10);
  hue++;

  chrg_states[0] = !digitalRead(CHRG_PIN);
  chrg_states[1] = !digitalRead(STBY_PIN);

  // long touch1 = Btn1.capacitiveSensorRaw(2);
  // long touch2 = Btn2.capacitiveSensorRaw(2);
  
  // Serial.print("Sensor1: "); Serial.println(touch1); 
  // Serial.print("Sensor2: "); Serial.println(touch2);
  // Serial.println();
  Serial.print("Charging: "); Serial.print(chrg_states[0] ? "Yes" : "No");
  Serial.print("\t\tStandby: "); Serial.println(chrg_states[1] ? "Yes" : "No");
  Serial.println();
}