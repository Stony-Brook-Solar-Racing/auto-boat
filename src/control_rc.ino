#include <Servo.h>

// Create a servo object
Servo servo;
Servo esc;

void setup() {
  Serial.begin(9600);
  // Attach the servo to pin 3
  //myServo.attach(3);
  delay(10000);
  esc.attach(9,1000,2000);
  // Initialize at 90 degs
  //myServo.write(2000);
  esc.writeMicroseconds(2000);
  delay(3000);
  esc.writeMicroseconds(1000);
  delay(3000);
  //esc.writeMicroseconds(1500);
}

void loop() {
  static char buf[96];
  esc.writeMicroseconds(1200);
  delay(3000);
  esc.writeMicroseconds(1000);
  delay(3000);
  ;
  /*
  while(Serial.available()) {
    int len = Serial.readBytesUntil('\n', buf, sizeof(buf)-1);
    if (len <= 0) return;
    buf[len] = '\0';

    int ch1, ch3, ch4;
    if(sscanf(buf, "%d %d %d", &ch1, &ch3, &ch4) == 3) {
      //myServo.write(ch1);
      esc.writeMicroseconds(ch1);
    } else {
      Serial.print("bad value");
    }
  }
  */
}
