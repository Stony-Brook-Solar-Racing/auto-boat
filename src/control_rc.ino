#include <Servo.h>

// Create a servo object
Servo servo;
Servo esc;

void setup() {
  Serial.begin(9600);
  
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

  esc.writeMicroseconds(2000);
  delay(3000);
  esc.writeMicroseconds(1000);
  delay(3000);

  // Initialize at 90 degs
  servo.write(90);
}

void loop() {
  static char buf[96];
  while(Serial.available()) {
    int len = Serial.readBytesUntil('\n', buf, sizeof(buf)-1);
    if (len <= 0) return;
    buf[len] = '\0';

    // channels should range from -1 to 1
    float ch1, ch3;
    if(sscanf(buf, "%f", &ch1, &ch3) == 2) {
      // Convert -1 to 1 to 0 to 180
      int rudder = ((ch1+1)/2)*180
      // Convert -1 to 1 to 1000
      int throttle = ((ch3+2)*1000
      servo.write(rudder);
      esc.writeMicroseconds(throttle);
    } else {
      Serial.print("bad value");
    }
  }
}
