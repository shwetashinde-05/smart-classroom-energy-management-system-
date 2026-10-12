// code for one LED
#include <WiFi.h>
#include <HTTPClient.h>

const char *ssid = "Redmi 10A";
const char *password = "aishwaryapatil";

String serverURL = "http://10.221.205.46:3000/latest";

#define LIGHT_PIN 5

void setup()
{
  Serial.begin(115200);
  pinMode(LIGHT_PIN, OUTPUT);

  digitalWrite(LIGHT_PIN, HIGH); // Active LOW: HIGH = relay OFF = LED OFF at startup

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  // while (WiFi.status() != WL_CONNECTED) {
  //   delay(500);
  //   Serial.print(".");
  // }
  int retry = 0;

  while (WiFi.status() != WL_CONNECTED && retry < 20)
  {
    delay(500);
    Serial.print(".");
    retry++;
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("\nConnected!");
    Serial.println(WiFi.localIP());
  }
  else
  {
    Serial.println("\nWiFi FAILED!");
  }
}

void loop()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    HTTPClient http;
    http.begin(serverURL);
    int code = http.GET();

    if (code == 200)
    {
      String payload = http.getString();
      Serial.println(payload);

      if (payload.indexOf("Occupied") != -1)
      {
        Serial.println("Occupied → LED ON");
        digitalWrite(LIGHT_PIN, LOW); // Active LOW: LOW = relay ON = LED ON
      }
      else
      {
        Serial.println("Unoccupied → LED OFF");
        digitalWrite(LIGHT_PIN, HIGH); // Active LOW: HIGH = relay OFF = LED OFF
      }
    }
    else
    {
      Serial.print("HTTP Error: ");
      Serial.println(http.errorToString(code));
      digitalWrite(LIGHT_PIN, HIGH); // Safety: relay OFF on error
    }

    http.end();
  }
  else
  {
    Serial.println("WiFi Disconnected");
    digitalWrite(LIGHT_PIN, HIGH); // Safety: relay OFF when no WiFi
  }

  delay(5000);
}
