#include <BleMouse.h>

/*
 * ESP32 Touch-Controlled BLE Mouse
 *
 * Features:
 * - Touch-based mouse movement (up, down, left, right)
 * - Left and right mouse clicks
 * - Speed control via touch:
 *   • Short press: increase speed by +5
 *   • Long press (1s): decrease speed by -5 (min 1)
 * - Speed changes limited to once per second
 *
 * Pin mapping:
 * D4  - Move left
 * D15 - Move right
 * D33 - Move up
 * D27 - Move down
 * D13 - Left click
 * D32 - Right click
 * D14 - Speed control
 */

 /*
 * ALGORITHM DESCRIPTION / ОПИСАНИЕ АЛГОРИТМА
 *
 * (en):
 *
 * Speed Control Algorithm Logic:
 *
 * Overview:
 * The algorithm implements a touch-based speed control system with short press for speed increase
 * and long press for speed decrease functionality.
 *
 * Key Components:
 * 1. Touch Sensing: Uses filtered touch readings from pin D14 for reliable detection
 * 2. State Machine: Tracks button press/release states and press duration
 * 3. Speed Management: Controls movement speed with cooldown periods
 *
 * Algorithm Flow:
 *
 * 1. Touch Detection:
 *    - Reads touch sensor value from pin D14
 *    - Applies moving average filter (5 samples) for stability
 *    - Compares filtered value against threshold (20) to determine touch state
 *
 * 2. State Tracking:
 *    - speedButtonPressed: Tracks if button is currently pressed
 *    - longPressActive: Flags when long press is detected
 *    - shortPressHandled: Prevents duplicate short press handling
 *
 * 3. Press Detection:
 *    - Button Press: When touch detected and not previously pressed
 *      - Records press start time
 *      - Resets state flags
 *    - Button Release: When touch ends and was previously pressed
 *      - Handles short press (if not already handled)
 *      - Resets all states
 *
 * 4. Long Press Handling:
 *    - After 1000ms of continuous press, activates long press mode
 *    - Decreases speed by 5 every 1000ms while pressed
 *    - Minimum speed limited to 1
 *    - Sets shortPressHandled to prevent short press on release
 *
 * 5. Short Press Handling:
 *    - On release before 1000ms, increases speed by 5
 *    - Respects 1000ms cooldown between changes
 *    - Only executed if long press wasn't activated
 *
 * 6. Cooldown Management:
 *    - lastSpeedChangeTime ensures minimum 1 second between speed changes
 *    - Prevents rapid consecutive adjustments
 *
 * (ru):
 *
 * Логика алгоритма контроля скорости:
 *
 * Обзор:
 * Алгоритм реализует сенсорную систему контроля скорости с коротким нажатием для увеличения скорости
 * и длинным нажатием для уменьшения.
 *
 * Ключевые компоненты:
 * 1. Сенсорное управление: Использует фильтрованные показания с пина D14 для надежного определения
 * 2. Конечный автомат: Отслеживает состояния нажатия/отпускания и длительность нажатия
 * 3. Управление скоростью: Контролирует скорость перемещения с периодами задержки
 *
 * Логика работы:
 *
 * 1. Обнаружение касания:
 *    - Чтение значения сенсора с пина D14
 *    - Применение скользящего среднего (5 samples) для стабильности
 *    - Сравнение отфильтрованного значения с порогом (20)
 *
 * 2. Отслеживание состояний:
 *    - speedButtonPressed: Отслеживает текущее состояние нажатия
 *    - longPressActive: Флаг длинного нажатия
 *    - shortPressHandled: Предотвращает повторную обработку короткого нажатия
 *
 * 3. Обнаружение нажатий:
 *    - Нажатие кнопки: При обнаружении касания
 *      - Запись времени начала нажатия
 *      - Сброс флагов состояний
 *    - Отпускание кнопки: При окончании касания
 *      - Обработка короткого нажатия (если не обработано)
 *      - Сброс всех состояний
 *
 * 4. Обработка длинного нажатия:
 *    - После 1000ms непрерывного нажатия активирует режим длинного нажатия
 *    - Уменьшает скорость на 5 каждые 1000ms пока нажато
 *    - Минимальная скорость ограничена значением 1
 *    - Устанавливает shortPressHandled для предотвращения короткого нажатия
 *
 * 5. Обработка короткого нажатия:
 *    - При отпускании до 1000ms увеличивает скорость на 5
 *    - Соблюдает задержку 1000ms между изменениями
 *    - Выполняется только если не было длинного нажатия
 *
 * 6. Управление задержками:
 *    - lastSpeedChangeTime обеспечивает минимум 1 секунду между изменениями скорости
 *    - Предотвращает быстрое последовательное изменение скорости
 *
 * Преимущества алгоритма:
 * - Устойчивость к "дребезгу" сенсора благодаря фильтрации
 * - Четкое разделение коротких и длинных нажатий
 * - Защита от случайных multiple-triggers
 * - Плавное и предсказуемое управление скоростью
 */


BleMouse bleMouse("ESP32-Touch-Mouse");

int threshold = 10; // Increased threshold for better stability
int moveSpeed = 5; // Base movement speed

// Touch detection flags
bool touchLeftDetected = false;    // D4 - left
bool touchRightDetected = false;   // D15 - right
bool touchUpDetected = false;      // D33 - up
bool touchDownDetected = false;    // D27 - down
bool touchLeftClickDetected = false;  // D13 - left click
bool touchRightClickDetected = false; // D32 - right click

// Speed control variables
unsigned long lastSpeedChangeTime = 0;
const unsigned long speedChangeCooldown = 1000; // Cooldown between speed changes
bool speedButtonPressed = false;
unsigned long speedButtonPressTime = 0;
const unsigned long longPressDuration = 1000; // Long press duration
bool longPressActive = false;
bool shortPressHandled = false;

// Touch value filtering
const int FILTER_SAMPLES = 5;
int touchReadings[FILTER_SAMPLES];
int readIndex = 0;
int touchTotal = 0;
int touchAverage = 0;

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

  // Initialize touch filter
  for (int i = 0; i < FILTER_SAMPLES; i++) {
    touchReadings[i] = touchRead(14);
    touchTotal += touchReadings[i];
  }
  touchAverage = touchTotal / FILTER_SAMPLES;

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

int getFilteredTouchValue() {
  // Remove the oldest reading
  touchTotal -= touchReadings[readIndex];

  // Read new value
  touchReadings[readIndex] = touchRead(14);

  // Add new value to total
  touchTotal += touchReadings[readIndex];

  // Update index
  readIndex = (readIndex + 1) % FILTER_SAMPLES;

  // Return average
  return touchTotal / FILTER_SAMPLES;
}

void handleSpeedControl() {
  unsigned long currentTime = millis();

  // Get filtered touch value
  int filteredTouch = getFilteredTouchValue();
  bool isTouched = (filteredTouch < threshold);

  if (isTouched && !speedButtonPressed) {
    // Button just pressed
    speedButtonPressed = true;
    speedButtonPressTime = currentTime;
    longPressActive = false;
    shortPressHandled = false;
    Serial.print("Speed button pressed, value: ");
    Serial.println(filteredTouch);
  }
  else if (!isTouched && speedButtonPressed) {
    // Button released
    if (!longPressActive && !shortPressHandled) {
      // Short press - increase speed
      if (currentTime - lastSpeedChangeTime >= speedChangeCooldown) {
        moveSpeed += 5;
        lastSpeedChangeTime = currentTime;
        shortPressHandled = true;
        Serial.print("Speed increased: ");
        Serial.println(moveSpeed);
      }
    }
    speedButtonPressed = false;
    longPressActive = false;
    Serial.println("Speed button released");
  }
  else if (isTouched && speedButtonPressed) {
    // Button still pressed
    unsigned long pressDuration = currentTime - speedButtonPressTime;

    if (!longPressActive && pressDuration >= longPressDuration) {
      // Long press detected
      longPressActive = true;
      shortPressHandled = true; // Prevent short press handling
      Serial.println("Long press detected");
    }

    // Continuous speed decrease during long press
    if (longPressActive && (currentTime - lastSpeedChangeTime >= speedChangeCooldown)) {
      moveSpeed = max(1, moveSpeed - 5);
      lastSpeedChangeTime = currentTime;
      Serial.print("Speed decreased: ");
      Serial.println(moveSpeed);
    }
  }
}

void loop() {
  // Handle speed control
  handleSpeedControl();

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

  delay(50); // Slightly longer delay for stability
}