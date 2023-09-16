#include <Arduino.h>
// #include <CapacitiveSensor.h>
#include <FastLED.h>

#define BTN1 14
#define BTN2 12
#define CAP_SEND 13
#define BUILTIN_LED 2
#define LED 0
#define NUM_LEDS 7
#define CHRG_PIN 5
#define STBY_PIN 4
 
#define TOUCH_THRESH 800


bool btn_states[2] = {0};
// CapacitiveSensor Btn1 = CapacitiveSensor(CAP_SEND, BTN1);
// CapacitiveSensor Btn2 = CapacitiveSensor(CAP_SEND, BTN2);

CRGB leds[NUM_LEDS];

bool chrg_states[2] = {0};