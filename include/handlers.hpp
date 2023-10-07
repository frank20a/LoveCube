#include <ESP8266WiFi.h>
#include <ESPAsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <LittleFS.h>


void not_found(AsyncWebServerRequest *request) {
  request->send(404, "text/plain", "Not found");
}

void on_index(AsyncWebServerRequest *request) {
    // Process file template
    request->send(
        LittleFS,
        "/pages/index.html",
        "text/html", 
        false,
        [](const String& var ) -> String {
            if(var == "ssid")
                return config.ssid;
            if(var == "pass")
                return config.pass;
            if(var == "key")
                return String(config.key);
            if(var == "uid")
                return String(uid, HEX);
            if(var == "max_ssid")
                return String(SSID_MAX_LEN);
            if(var == "max_pass")
                return String(PASS_MAX_LEN);
            if(var == "max_user")
                return String(USER_MAX_LEN);
            if(var == "max_key")
                return String(KEY_LEN) + 4;
            return String();
        }
    );
}

void on_css(AsyncWebServerRequest *request) {
    // Open file
    File f = LittleFS.open("/styles/" + request->pathArg(0) + ".css", "r");

    // Check if file exists
    if(!f) {
        request->send(500, "text/plain", "CSS:500 (Server Error)\nCould not open file.");
        return;
    }

    // Send file
    request->send(f, "text/css");
    f.close();
}

void on_config(AsyncWebServerRequest *request){
    if(
        !request->hasParam("ssid", true) ||
        !request->hasParam("password", true) ||
        !request->hasParam("key", true)
    ) {
        request->send(400, "text/plain", "Config:400 (Bad Request)\nMissing parameters.");
        return;
    }

    // Get parameters
    config.configured = true;
    strcpy(config.ssid, request->getParam("ssid", true)->value().c_str());
    strcpy(config.pass, request->getParam("password", true)->value().c_str());
    strcpy(config.key, request->getParam("key", true)->value().c_str());
    save_config();

    // Restart device
    request->send(LittleFS, "/pages/restart.html", "text/html", false);
}

void on_restart(AsyncWebServerRequest *request) {
    request->send(200, "text/plain", "Restarting...");
    ESP.restart();
}

