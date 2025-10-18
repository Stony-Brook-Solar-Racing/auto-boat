#include <Servo.h>

// Create a servo object
Servo servo;
Servo esc;

void setup() {
  Serial.begin(9600);
  Serial.write("ACK");
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
  esc.attach(9,1000,2000);
  // Attach the servo to pin 3
  servo.attach(3);

  // ESC arming
  esc.writeMicroseconds(2000);
  delay(3000);
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
      // Convert -1 to 1 to 0 to 180
      int rudder = (int)lroundf(((ch1 + 1.0f) * 0.5f) * 180.0f);
      if(rudder < 0) rudder = 0;
      else if(rudder > 180) rudder = 180;
      // Convert -1 to 1 to 1000 to 2000
      int throttle = (int)lroundf(((ch3 + 1.0f) * 0.5f) * 1000.0f + 1000.0f);
      if(throttle < 1000) throttle = 1000;
      else if(throttle > 2000) rudder = 2000;
      Serial.write(throttle);
      servo.write(rudder);
      esc.writeMicroseconds(throttle);
  }
}
