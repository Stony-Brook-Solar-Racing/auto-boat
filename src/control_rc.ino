#include <Servo.h>

// Create a servo object
Servo servo;
Servo esc;

void setup() {
  Serial.begin(9600);
  Serial.write("ARDUINO-READY\n");
  // Wait for serial to be available
  while(!Serial.available()) { delay(2000); }
  // Block until read signal is sent
  static char buf[96];
  while(Serial.available()) {
    int len = Serial.readBytesUntil('\n', buf, sizeof(buf)-1);
    buf[len] = '\0';
    char ready_check[100];
    if(sscanf(buf, "%s", &ready_check) == 1) {
        if(strcmp(ready_check, "PI-READY") == 0) {
          Serial.println("ACK");
          break;
        }
    }
    else { Serial.println("Received Incorrect Signal"); }
  }
  // Attach the esc to pin 9
  esc.attach(9, 1000, 2000);
  // Attach the servo to pin 3
  servo.attach(3);

  /*
  esc.writeMicroseconds(2000);
  delay(3000);
  */
  esc.writeMicroseconds(1000);
  delay(3000);

  // Initialize at 90 degs
  servo.write(90);
}

void loop() {
  while(Serial.available()) {
    // channels should range from -1 to 1
    float ch1, ch3;
      ch1 = Serial.parseFloat();
      ch3 = Serial.parseFloat();
      Serial.readStringUntil('\n');

      if(ch1 < -1) ch1 = -1; 
      else if(ch1 > 1) ch1 = 1;
      if(ch3 < -1) ch3 = -1; 
      else if(ch3 > 1) ch3 = 1;
      // Convert -1 to 1 to 45 to 135
      int rudder = (int)lroundf((((ch1 + 1.0f) * 0.5f) * 90.0f) + 45);
      if(rudder < 60) rudder = 60;
      else if(rudder > 120) rudder = 120;
      // Convert -1 to 1 to 1000 to 2000
      int throttle = (int)lroundf(((ch3 + 1.0f) * 0.5f) * 1000.0f + 1000.0f);
      if(throttle < 1000) throttle = 1000;
      else if(throttle > 2000) throttle = 2000;
      Serial.println(throttle);
      servo.write(rudder);
      esc.writeMicroseconds(throttle);
  }
}
