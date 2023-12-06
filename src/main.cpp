#include "main.hpp"
#include "handlers.hpp"

void setup() {
  // Serial
  Serial.begin(115200);

  // LEDs
  FastLED.addLeds<SK6812, LED, GRB>(leds, NUM_LEDS);

  // Mount LittleFS
  if(!LittleFS.begin()){
    Serial.println("An Error has occurred while mounting LittleFS");
    delay(5000);
    ESP.restart();
  }

  // Configuration File
  if (!load_config()) {
    init_config();
    if (!save_config()) {
      Serial.println("An Error has occurred while saving config");
      delay(5000);
      ESP.restart();
    }
  }

  // Configure WiFi
  if (!config.configured) {   // If not configured, create AP
    // Setup access point
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(IPAddress(192, 168, 1, 1), IPAddress(192, 168, 1, 1), IPAddress(255, 255, 255, 0));
    WiFi.softAP(ap_ssid.c_str(), ap_pass.c_str());

    // Setup DNS for captive portal
    dns_server.setTTL(300);
    dns_server.setErrorReplyCode(DNSReplyCode::NonExistentDomain);
    dns_server.start(DNS_PORT, "setup.lovecube.com", IPAddress(192, 168, 1, 1));
    
    web_server.on("/", HTTP_GET, on_index);
    web_server.on("^\\/styles\\/([a-zA-Z0-9]+).css$", HTTP_GET, on_css);
    web_server.on("/config", HTTP_POST, on_config);
    web_server.on("/restart", HTTP_GET, on_restart);
    web_server.onNotFound(not_found);
    web_server.begin();
  } else {                    // If configured, connect to WiFi
    WiFi.mode(WIFI_STA);
    WiFi.begin(config.ssid, config.pass);
    if (WiFi.waitForConnectResult() != WL_CONNECTED) {
      Serial.println("WiFi connection failed");
      Serial.print("SSID: ");
      Serial.println(config.ssid);
      Serial.print("PASS: ");
      Serial.println(config.pass);

      config.configured = false;
      if (!save_config()) {
        Serial.println("An Error has occurred while saving config");
      }
      
      Serial.println("Accepting debug commands for 1 minute");
      unsigned long long int prevt = millis();
      while(millis() - prevt < 60000) {
        handle_serial_cmd();
        delay(50);
      }
      ESP.restart();
    }
  }

  // Configure Pins
  pinMode(BTN1, INPUT);
  pinMode(BTN2, INPUT);
  pinMode(CAP_SEND, OUTPUT);
  // Btn1.set_CS_AutocaL_Millis(0xFFFFFFFF);
  // Btn2.set_CS_AutocaL_Millis(0xFFFFFFFF);
  pinMode(HW_LED, OUTPUT);
  pinMode(CHRG_PIN, INPUT);
  pinMode(STBY_PIN, INPUT);

  // Turn LEDs off
  for(int i = 0; i < NUM_LEDS; i++) leds[i] = CRGB(0, 0, 0);
  FastLED.show();
}

void loop() {
  // Get charging states
  chrg_states[0] = !digitalRead(CHRG_PIN);
  chrg_states[1] = !digitalRead(STBY_PIN);

  // Timers logic
  blinker_pulse();
  if(config.configured) {
    // put_status();
    get_status();
  }
  led_animation();

  // Serial.println(cmd);

  // Check for serial command
  handle_serial_cmd();
  if (!config.configured) dns_server.processNextRequest();
}

void blinker_pulse() {
  static unsigned long long int prevt_blinker = millis();
  static bool state = true;

  if (millis() - prevt_blinker > BLINKER_PULSE_INTERVAL_MS && !config.configured) {
    prevt_blinker = millis();
    state = !state;
    digitalWrite(HW_LED, !(state && config.configured));
  }
}

void handle_serial_cmd() {
  if (!Serial.available()) return;

  bool restart_flag = false;
  SER_CMD cmd;
  SER_RESP resp = {0};

  // Read command & verify checksum
  Serial.readBytes((char*)&cmd, sizeof(cmd));
  if ((cmd.cmd + cmd.arg1 + cmd.arg2) % 256 != cmd.hash) {
    resp.cmd = 0xFF;  // Error
    resp.resp = 0xFE;  // Checksum Error
    Serial.write((char*)&resp, sizeof(resp));
    return;
  }

  // Handle command
  resp.cmd = cmd.cmd;
  if (cmd.cmd == 0x00) {    // Get status
    resp.resp = 0x01;           // Acknowledge
  } else if (cmd.cmd == 0x01) {     // Reconfigure
      config.configured = false;
      if(!save_config()) {
        resp.resp = 0xFF;       // Error
      } else{
        resp.resp = 0x01;       // Acknowledge
        restart_flag = true;
      }
  } else if (cmd.cmd == 0x02) {     // Get UID
    resp.resp = 0x01;           // Acknowledge
    memcpy(resp.data, &uid, sizeof(uid));
  } else if (cmd.cmd == 0x03) {     // Get charging status
    resp.resp = 0x01;           // Acknowledge
    resp.data[0] = chrg_states[0];
    resp.data[1] = chrg_states[1];
  } else if (cmd.cmd == 0x04) {     // Get Local IP
    resp.resp = 0x01;
    resp.data[0] = WiFi.localIP()[0];
    resp.data[1] = WiFi.localIP()[1];
    resp.data[2] = WiFi.localIP()[2];
    resp.data[3] = WiFi.localIP()[3];
  } else {
    resp.resp = 0xFD;       // Unknown Command
  }

  // Calculate checksum & send response
  resp.hash = resp.cmd + resp.resp;
  for(int i = 0; i < 6; i++) resp.hash += resp.data[i];
  Serial.write((char*)&resp, sizeof(resp));
  Serial.flush();

  if (restart_flag) {
    delay(1000);
    ESP.restart();
  }
}

bool load_config() {
  File f = LittleFS.open(CONFIG_FILENAME, "r");
  if(!f || FORCE_CONFIG_RESET) return false;
  else f.read((uint8_t*)&config, sizeof(config));
  f.close();
  return true;
}

bool save_config() {
    File f = LittleFS.open(CONFIG_FILENAME, "w");
    if(!f) return false;
    f.write((char*)&config, sizeof(config));
    f.close();
    return true;
}

void init_config() {
  config.configured = false;
  strcpy(config.ssid, "SSID_HERE");
  strcpy(config.pass, "PASS_HERE");
  strcpy(config.key, "0123456789ABCDEF");
  config.brightness = 128;
}

void get_status() {
  static unsigned long long int prevt_status = millis();

  if (millis() - prevt_status < GET_STATUS_INTERVAL_MS) return;
  prevt_status = millis();

  WiFiClient client;
  String host = String(API_HOST) + "api/v1/get-cmd/" + String(config.key) + "/" + String(uid, HEX);

  http.begin(client, host);
  StaticJsonDocument<256> resp;

  int http_code = http.GET();
  if (http_code == HTTP_CODE_OK) {
    if (!deserializeJson(resp, http.getString())) {
      if (resp["error"] == 0) {
        cmd = resp["cmd"];
      } else {
        Serial.print("Error getting status: ");
        Serial.println(String(resp["error_msg"]));
      }
    } else {
      Serial.println("Error parsing JSON");
    }
  } else {
    Serial.print("Error getting status from ");
    Serial.print(host);
    Serial.print(": ");
    Serial.print(String(http_code));
    Serial.print(" - ");
    Serial.println(http.errorToString(http_code));
    Serial.println(http.getString());
    Serial.println();
  }

  http.end();
}

void put_status() {
  static unsigned long long int prevt_status = millis();

  if (millis() - prevt_status < PUT_STATUS_INTERVAL_MS) return;
  prevt_status = millis();

  WiFiClient client;
  String host = String(API_HOST) + "api/v1/state/" + String(config.key) + "/" + String(uid, HEX);

  http.begin(client, host);
  StaticJsonDocument<256> buff;
  String json;

  buff['chrg_flag'] = chrg_states[0];
  buff['stby_flag'] = chrg_states[1];
  serializeJson(buff, json);

  http.addHeader("Content-Type", "application/json");
  int http_code = http.PUT(json);
  if (http_code == HTTP_CODE_OK) {
    if (!deserializeJson(buff, http.getString())) {
      if (buff["error"] == 0) {
        cmd = buff["cmd"];
      } else {
        Serial.print("Error getting status: ");
        Serial.println(String(buff["error_msg"]));
      }
    } else {
      Serial.println("Error parsing JSON");
    }
  } else {
    Serial.print("Error getting status: ");
    Serial.println(http.errorToString(http_code));
  }

  http.end();
}

void btn_trigger(uint8_t btn_num) {
  WiFiClient client;

  http.begin(client, String(API_HOST) + "api/v1/trigger/" + String(config.key) + "/" + uid + "/" + String(btn_num));
  StaticJsonDocument<256> resp;

  int http_code = http.GET();
  if (http_code == HTTP_CODE_OK) {
    if (!deserializeJson(resp, http.getString())) {
      if (resp["error"] != 0) {
        Serial.print("Error getting status: ");
        Serial.println(String(resp["error_msg"]));
      }
    } else {
      Serial.println("Error parsing JSON");
    }
  } else {
    Serial.print("Error getting status: ");
    Serial.println(http.errorToString(http_code));
  }

  http.end();
}

void led_animation() {
  static unsigned long long int prevt_led = millis();
  static uint8_t hue = 0;
  static uint8_t brightness = config.brightness;
  static bool dir = true;

  if (millis() - prevt_led < LED_ANIMATION_INTERVAL_MS) return;
  prevt_led = millis();

  if (cmd == 0 or cmd > 8) {
    for(int i = 0; i < NUM_LEDS; i++) {
      leds[i] = CRGB(0, 0, 0);
    }
  } else if (cmd == 1) {
    for(int i = 0; i < NUM_LEDS; i++) {
      leds[i] = CHSV((hue + 5*i) % 256, 255, config.brightness);
    }
  } else if (cmd < 8) {
    for(int i = 0; i < NUM_LEDS; i++) {
      Serial.println(cmd);
      switch (cmd){
        case 2:
          leds[i] = CRGB(brightness, 0, 0);
          break;
        case 3:
          leds[i] = CRGB(0, brightness, 0);
          break;
        case 4:
          leds[i] = CRGB(0, 0, brightness);
          break;
        case 5:
          leds[i] = CRGB(brightness, brightness, 0);
          break;
        case 6:
          leds[i] = CRGB(0, brightness, brightness);
          break;
        case 7:
          leds[i] = CRGB(brightness, 0, brightness);
          break;
      }
    }
  } else if (cmd == 8){
    for(int i = 0; i < NUM_LEDS; i++) {
      leds[i] = CHSV(0, 0, brightness);
    }
  }

  hue++;
  if (brightness <= 10 ) dir = true;
  else if (brightness >= config.brightness) dir = false;
  brightness += dir ? 3 : -3;
  FastLED.show();
}
