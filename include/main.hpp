#define USING_TIM_DIV1      false
#define USING_TIM_DIV16     true
#define USING_TIM_DIV256    false

#include <Arduino.h>
// #include <CapacitiveSensor.h>
#include <FastLED.h>
#include <ESP8266WiFi.h>
#include <DNSServer.h>
#include <ESPAsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ESP8266HTTPClient.h>
#include <LittleFS.h>
#include <Hash.h>
#include <ESP8266TimerInterrupt.h>
#include <ESP8266_ISR_Timer.h>
#include <ArduinoJson.h>


#define SSID_MAX_LEN 32
#define PASS_MAX_LEN 64
#define USER_MAX_LEN 10
#define KEY_LEN 16
#define CONFIG_FILENAME F("/config.dat")
#define DNS_PORT 53
#define HW_TIMER_INTERVAL_MS 5L
#define GET_STATUS_INTERVAL_MS 10000L
#define PUT_STATUS_INTERVAL_MS 120000L
#define LED_ANIMATION_INTERVAL_MS 25L


ESP8266Timer ITimer;
ESP8266_ISR_Timer ISR_Timer;
HTTPClient http;
DNSServer dns_server;
AsyncWebServer web_server(80);
const uint32_t uid = ESP.getChipId();
const String ap_ssid = "LoveCube-" + String(uid, HEX);
const String ap_pass = "password";

// Structures
typedef struct {
    unsigned char cmd;
    unsigned char arg1;
    unsigned char arg2;
    unsigned char hash;
} SER_CMD;
typedef struct {
    unsigned char cmd;
    unsigned char resp;
    unsigned char data[6];
    unsigned char hash;
} SER_RESP;
typedef struct {
    bool configured;
    char ssid[SSID_MAX_LEN + 1];
    char pass[PASS_MAX_LEN + 1];
    char key[KEY_LEN + 1];
    uint8_t brightness;
} Config;

// Variables
Config config;
bool btn_states[2] = {0};
// CapacitiveSensor Btn1 = CapacitiveSensor(CAP_SEND, BTN1);
// CapacitiveSensor Btn2 = CapacitiveSensor(CAP_SEND, BTN2);
CRGB leds[NUM_LEDS];
bool chrg_states[2] = {0};
uint8_t cmd = 0;


// Methods
void handle_serial_cmd();
bool load_config();
bool save_config();
void init_config();
void IRAM_ATTR TimerHandler() { ISR_Timer.run(); }
void get_status();
void put_status();
void led_animation();
void btn_trigger(uint8_t btn_num);
void btn1_handler() { btn_trigger(1); }
void btn2_handler() { btn_trigger(2); }
