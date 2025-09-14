// ESP32 Touch Test
// Just test touch pin - D4.
 
void setup() {
  Serial.begin(115200);
  delay(1000); // give me time to bring up serial monitor
  Serial.println("ESP32 Touch Test");
}
 
void loop() {
  Serial.print("Touch: ");
  Serial.println(touchRead(4));  // get touch value on GPIO 4
  delay(1000);
}