#include <BleMouse.h>

/*
 * ESP32 Touch-Controlled BLE Mouse
 *
 * Features:
 * - Touch-based mouse movement (up, down, left, right)
 * - Left and right mouse clicks
 *
 * Pin mapping:
 * D4  - Move left
 * D15 - Move right
 * D33 - Move up
 * D27 - Move down
 * D13 - Left click
 * D32 - Right click
 */

BleMouse bleMouse("ESP32-Touch-Mouse");

int threshold = 10;
int moveSpeed = 5; // Base movement speed

// Touch detection flags
bool touchLeftDetected = false;    // D4 - left
bool touchRightDetected = false;   // D15 - right
bool touchUpDetected = false;      // D33 - up
bool touchDownDetected = false;    // D27 - down
bool touchLeftClickDetected = false;  // D13 - left click
bool touchRightClickDetected = false; // D32 - right click


void handleTouchLeft() {
  touchLeftDetected = true;
}

void handleTouchDown() {
  touchDownDetected = true;
}

void handleTouchRight() {
  touchRightDetected = true;
}

void handleTouchLeftClick() {
  touchLeftClickDetected = true;
}

void handleTouchUp() {
  touchUpDetected = true;
}

void handleTouchRightClick() {
  touchRightClickDetected = true;
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("ESP32 Touch Mouse Started");
  Serial.print("Initial move speed: ");
  Serial.println(moveSpeed);

  // Assign touch interrupt handlers
  touchAttachInterrupt(4, handleTouchLeft, threshold);        // LEFT
  touchAttachInterrupt(27, handleTouchDown, threshold);       // DOWN
  touchAttachInterrupt(15, handleTouchRight, threshold);      // RIGHT
  touchAttachInterrupt(13, handleTouchLeftClick, threshold);  // LEFT CLICK
  touchAttachInterrupt(33, handleTouchUp, threshold);         // UP
  touchAttachInterrupt(32, handleTouchRightClick, threshold); // RIGHT CLICK

  bleMouse.begin();
  Serial.println("BLE Mouse started");
}

void loop() {

  // Handle movement
  if (touchLeftDetected) {
    bleMouse.move(-moveSpeed, 0);
    Serial.print("Moving LEFT, speed: ");
    Serial.println(moveSpeed);
  }

  if (touchRightDetected) {
    bleMouse.move(moveSpeed, 0);
    Serial.print("Moving RIGHT, speed: ");
    Serial.println(moveSpeed);
  }

  if (touchUpDetected) {
    bleMouse.move(0, -moveSpeed);
    Serial.print("Moving UP, speed: ");
    Serial.println(moveSpeed);
  }

  if (touchDownDetected) {
    bleMouse.move(0, moveSpeed);
    Serial.print("Moving DOWN, speed: ");
    Serial.println(moveSpeed);
  }

  if (touchLeftClickDetected) {
    bleMouse.click(MOUSE_LEFT);
    Serial.println("Single left click");
  }

  if (touchRightClickDetected) {
    bleMouse.click(MOUSE_RIGHT);
    Serial.println("Single right click");
    delay(100);
  }

  // Reset touch flags
  touchLeftDetected = false;
  touchRightDetected = false;
  touchDownDetected = false;
  touchLeftClickDetected = false;
  touchUpDetected = false;
  touchRightClickDetected = false;

  delay(10);
}