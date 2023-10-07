#include "main.hpp"
#include "handlers.hpp"

void setup() {
  // Serial
  Serial.begin(115200);

  // LEDs
  FastLED.addLeds<SK6812, LED>(leds, NUM_LEDS);

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
      Serial.println("WiFi connection failed! Rebooting...");
      delay(5000);
      ESP.restart();
    }
  }

  // Start timers
  if (!ITimer.attachInterruptInterval(HW_TIMER_INTERVAL_MS * 1000, TimerHandler)) {
    Serial.println("Error attaching interrupt");
    delay(5000);
    ESP.restart();
  }
  ISR_Timer.setInterval(GET_STATUS_INTERVAL_MS, get_status);
  ISR_Timer.setInterval(PUT_STATUS_INTERVAL_MS, put_status);
  ISR_Timer.setInterval(LED_ANIMATION_INTERVAL_MS, led_animation);

  // Configure Pins
  pinMode(BTN1, INPUT);
  pinMode(BTN2, INPUT);
  pinMode(CAP_SEND, OUTPUT);
  // Btn1.set_CS_AutocaL_Millis(0xFFFFFFFF);
  // Btn2.set_CS_AutocaL_Millis(0xFFFFFFFF);
  pinMode(HW_LED, OUTPUT);
  pinMode(CHRG_PIN, INPUT);
  pinMode(STBY_PIN, INPUT);
}

void loop() {
  // Blinker variables
  static bool state = true;
  static uint64_t last_time = millis();
  static int hue = 0;

  // for(int i = 0; i < NUM_LEDS; i++) {
  //   leds[i] = CHSV((hue + 5*i) % 256, 255, 255);
  // }
  // hue += 1;

  // Get charging states
  chrg_states[0] = !digitalRead(CHRG_PIN);
  chrg_states[1] = !digitalRead(STBY_PIN);

  // Blinker logic
  if (millis() - last_time > 1000) {
    last_time = millis();
    state = !state;
    digitalWrite(HW_LED, !(state && config.configured));
  }

  // Check for serial command
  handle_serial_cmd();
  if (!config.configured) dns_server.processNextRequest();
  // FastLED.delay(25);
  // FastLED.show();
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
  http.begin("http://lovecube.com/api/v1/get-cmd/" + String(config.key) + "/" + uid);
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
    Serial.print("Error getting status: ");
    Serial.println(http.errorToString(http_code));
  }

  http.end();
}

void put_status() {
  http.begin("http://lovecube.com/api/v1/state/" + String(config.key) + "/" + uid);
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
  http.begin("http://lovecube.com/api/v1/trigger/" + String(config.key) + "/" + uid + "/" + String(btn_num));
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
  static int hue = 0;
  for(int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV((hue + 5*i) % 256, 255, config.brightness);
  }
  hue += 1;
  FastLED.show();
}
