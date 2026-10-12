#include <WiFi.h>
#include <HTTPClient.h>

// 🔐 WiFi credentials
const char* ssid = "Galaxy";
const char* password = "123456789";

// 🌐 Server URL (your laptop IP)
String serverURL = "http://10.249.97.229:3000/latest";

// 🔌 Relay pins (ACTIVE LOW)
#define LIGHT_PIN 5
#define FAN_PIN   4

void setup() {
  Serial.begin(115200);

  pinMode(LIGHT_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);

  // Default OFF (because relay is ACTIVE LOW)
  digitalWrite(LIGHT_PIN, HIGH);
  digitalWrite(FAN_PIN, HIGH);

  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, password);

  // Wait until connected
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Connected to WiFi");

  // Show ESP32 IP
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {

  if (WiFi.status() == WL_CONNECTED) {

    HTTPClient http;
    http.begin(serverURL);

    int httpCode = http.GET();

    if (httpCode > 0) {
      Serial.print("HTTP Code: ");
      Serial.println(httpCode);

      if (httpCode == 200) {
        String payload = http.getString();
        Serial.print("Response: ");
        Serial.println(payload);

        // 🔍 Check status
        if (payload.indexOf("Occupied") != -1) {
          Serial.println("➡️ Room Occupied → Turning ON");
          digitalWrite(LIGHT_PIN, LOW); // ON
          digitalWrite(FAN_PIN, LOW);   // ON
        } else {
          Serial.println("➡️ Room Empty → Turning OFF");
          digitalWrite(LIGHT_PIN, HIGH); // OFF
          digitalWrite(FAN_PIN, HIGH);   // OFF
        }
      }

    } else {
      // ❌ Error in request
      Serial.print("HTTP Error: ");
      Serial.println(http.errorToString(httpCode));

      // 🔒 Safety: turn OFF devices
      digitalWrite(LIGHT_PIN, HIGH);
      digitalWrite(FAN_PIN, HIGH);
    }

    http.end();

  } else {
    Serial.println("❌ WiFi Disconnected");

    // 🔒 Safety OFF
    digitalWrite(LIGHT_PIN, HIGH);
    digitalWrite(FAN_PIN, HIGH);
  }

  delay(5000); // ⏱️ check every 5 seconds
}