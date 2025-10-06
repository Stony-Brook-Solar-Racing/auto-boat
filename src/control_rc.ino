#include <Servo.h>

// Create a servo object
Servo myServo;

void setup() {
  Serial.begin(9600);
  // Attach the servo to pin 3
  myServo.attach(3);
  // Initialize at 90 degs
  myServo.write(90);
}

void loop() {
  static char buf[96];
  while(Serial.available()) {
    int len = Serial.readBytesUntil('\n', buf, sizeof(buf)-1);
    if (len <= 0) return;
    buf[len] = '\0';

    int ch1, ch3, ch4;
    if(sscanf(buf, "%d %d %d", &ch1, &ch3, &ch4) == 3) {
      myServo.write(ch1);
    } else {
      Serial.print("bad value");
    }
  }
}
