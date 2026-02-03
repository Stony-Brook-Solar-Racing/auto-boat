#include <ESP32Servo.h> // CHANGE 1: Use the ESP32 specific library

// Create a servo object
Servo servo;
Servo esc;

// CHANGE 2: Define safe pins for ESP32
// Do NOT use pins 6-11 (connected to flash memory) or 1 & 3 (Serial/USB)
const int ESC_PIN = 18;  
const int SERVO_PIN = 19;

void setup() {
  // Allow allocation of all timers
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  Serial.begin(9600); // You might consider increasing this to 115200 for ESP32
  
  // OPTIONAL: set period to 50Hz (Standard for RC servos)
  servo.setPeriodHertz(50);
  esc.setPeriodHertz(50);

  Serial.write("ESP32-READY\n"); // Updated message
  
  // Wait for serial to be available
  while(!Serial.available()) { delay(2000); }
  
  // Block until read signal is sent
  static char buf[96];
  while(Serial.available()) {
    int len = Serial.readBytesUntil('\n', buf, sizeof(buf)-1);
    buf[len] = '\0';
    char ready_check[100];
    
    // Safety check on sscanf result
    if(sscanf(buf, "%s", ready_check) == 1) { // Removed & from array name (optional but cleaner C)
        if(strcmp(ready_check, "PI-READY") == 0) {
          Serial.println("ACK");
          break;
        }
    }
    else { Serial.println("Received Incorrect Signal"); }
  }

  // Attach the esc to the new pin
  // ESP32Servo attach accepts (pin, min, max) just like standard Servo
  esc.attach(ESC_PIN, 1000, 2000);
  
  // Attach the servo to the new pin
  servo.attach(SERVO_PIN, 500, 2500); // Adjusted range, standard servos often need 500-2500 on ESP32Servo lib, but 1000-2000 is safer if unsure.

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
      // Clear the rest of the buffer
      Serial.readStringUntil('\n');

      if(ch1 < -1) ch1 = -1; 
      else if(ch1 > 1) ch1 = 1;
      if(ch3 < -1) ch3 = -1; 
      else if(ch3 > 1) ch3 = 1;
      
      // Convert -1 to 1 -> 45 to 135
      int rudder = (int)lroundf((((ch1 + 1.0f) * 0.5f) * 90.0f) + 45);
      
      // Clamp rudder
      if(rudder < 60) rudder = 60;
      else if(rudder > 120) rudder = 120;
      
      // Convert -1 to 1 -> 1000 to 2000
      int throttle = (int)lroundf(((ch3 + 1.0f) * 0.5f) * 1000.0f + 1000.0f);
      
      // Clamp throttle
      if(throttle < 1000) throttle = 1000;
      else if(throttle > 2000) throttle = 2000;
      
      Serial.println(throttle);
      
      servo.write(rudder);
      esc.writeMicroseconds(throttle);
  }
}
