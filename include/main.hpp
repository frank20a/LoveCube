#include <Arduino.h>
// #include <CapacitiveSensor.h>
#include <FastLED.h>
#include <ESP8266WiFi.h>
#include <DNSServer.h>
#include <ESPAsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <LittleFS.h>
#include <Hash.h>

#define SSID_MAX_LEN 32
#define PASS_MAX_LEN 64
#define USER_MAX_LEN 10
#define KEY_LEN 16
#define CONFIG_FILENAME F("/config.dat")
#define DNS_PORT 53


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
    char username[USER_MAX_LEN + 1];
    char key[KEY_LEN + 1];
} Config;


// Variables
Config config;
bool btn_states[2] = {0};
// CapacitiveSensor Btn1 = CapacitiveSensor(CAP_SEND, BTN1);
// CapacitiveSensor Btn2 = CapacitiveSensor(CAP_SEND, BTN2);
CRGB leds[NUM_LEDS];
bool chrg_states[2] = {0};


// Methods
void handle_serial_cmd();
bool load_config();
bool save_config();
void init_config();