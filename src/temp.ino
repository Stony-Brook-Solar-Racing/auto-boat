#include <AlfredoCRSF.h>
#include <SoftwareSerial.h>
#include <Servo.h>

// ===== Debug UART on UNO pins (for prints you can see) =====
static const uint8_t DBG_RX = 10;   // from adapter TX (optional)
static const uint8_t DBG_TX = 11;   // to adapter RX
SoftwareSerial DebugSerial(DBG_RX, DBG_TX); // RX, TX

AlfredoCRSF crsf;
Servo myServo;

void setup() {
  // Start debug serial first (USB-UART adapter) so we can log status
  myServo.attach(3);
  DebugSerial.begin(115200);
  DebugSerial.println(F("\nUNO CRSF reader using AlfredoCRSF"));
  DebugSerial.println(F("Debug on pins 10(RX)/11(TX) @115200"));
  DebugSerial.println(F("CRSF on hardware Serial RX0 (pin 0)"));

  // IMPORTANT: On UNO, hardware Serial (pins 0/1) is the ONLY UART.
  // Dedicate it to CRSF at CRSF_BAUDRATE (usually 420000).
  Serial.begin(CRSF_BAUDRATE);

  // AlfredoCRSF expects a Stream reference; on UNO pass the global Serial.
  crsf.begin(Serial);

  DebugSerial.println(F("Init done.\n"));
}

void loop() {
  // Must be called frequently so the lib can parse bytes
  crsf.update();

  // Print channels periodically (e.g., ~20 Hz) without blocking too long
  static uint32_t last = 0;
  uint32_t now = millis();
  if (now - last >= 50) {
    last = now;
    printChannels();
  }
  myServo.write((crsf.getChannel(3) - 1000)/1000*180);
  delay(10);
}

// crsf.getChannel(n) returns channel n in microseconds (1000..2000), 1-based index
void printChannels() {
  DebugSerial.print(F("CH: "));
  for (int ch = 1; ch <= 16; ++ch) {
    int us = crsf.getChannel(ch);

    // Also show a 0..1 normalized value using common CRSF raw range 172..1811.
    // If AlfredoCRSF only exposes µs, normalize from 1000..2000 instead.
    float norm01 = 0.0f;
    // Normalize from microseconds (1000..2000) -> (0..1)
    if (us < 1000) us = 1000;
    if (us > 2000) us = 2000;
    norm01 = (us - 1000) / 1000.0f;

    DebugSerial.print(us);
    DebugSerial.print(F(" ("));
    DebugSerial.print(norm01, 3);
    DebugSerial.print(F(")"));

    if (ch < 16) DebugSerial.print(F(", "));
  }
  DebugSerial.println();
}

