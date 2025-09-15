#Requires AutoHotkey v2.0
#SingleInstance Force
SendMode "Input"
SetWorkingDir A_ScriptDir

; Настройки жеста
gestureTimeWindow := 1000  ; Временное окно жеста в миллисекундах
minDistance := 50          ; Минимальное расстояние движения в пикселях
maxPause := 300            ; Максимальная пауза между движениями
menuTimeout := 3000        ; Таймаут закрытия меню через 3 секунды

; Переменные для отслеживания жеста
lastX := 0
lastY := 0
lastMoveTime := 0
gestureStep := 0           ; 0: ожидание, 1: движение влево, 2: движение вправо

; Запуск мониторинга движений
SetTimer WatchGesture, 50

WatchGesture() {
    global lastX, lastY, lastMoveTime, gestureStep
    global gestureTimeWindow, minDistance, maxPause

    ; Получаем текущую позицию мыши
    MouseGetPos(&currentX, &currentY)
    currentTime := A_TickCount

    ; Проверяем движение только если мышь переместилась
    if (currentX != lastX || currentY != lastY) {
        deltaX := currentX - lastX
        deltaTime := currentTime - lastMoveTime

        ; Определяем направление движения
        if (Abs(deltaX) > Abs(currentY - lastY) * 2) { ; Преобладает горизонтальное движение
            if (deltaX < -minDistance) { ; Движение влево
                if (gestureStep == 0 && deltaTime < maxPause) {
                    gestureStep := 1
                    lastMoveTime := currentTime
                    ShowFeedback("← Движение влево")
                }
            }
            else if (deltaX > minDistance) { ; Движение вправо
                if (gestureStep == 1 && deltaTime < maxPause) {
                    ; Жест завершен!
                    gestureStep := 0
                    ShowQuickPanel()
                    ShowFeedback("✓ Жест распознан!")
                }
            }
        }

        ; Обновляем последнюю позицию и время
        lastX := currentX
        lastY := currentY
        lastMoveTime := currentTime
    }

    ; Сбрасываем жест если время вышло
    if (gestureStep > 0 && (currentTime - lastMoveTime) > gestureTimeWindow) {
        gestureStep := 0
        ShowFeedback("✗ Сброс жеста")
    }
}

ShowFeedback(message) {
    MouseGetPos(&x, &y)
    ToolTip message, x + 20, y + 20
    SetTimer () => ToolTip(), -800
}

ShowQuickPanel() {
    global menuTimeout

    ; Получаем позицию мыши
    MouseGetPos(&x, &y)

    ; Создаем GUI окно
    myGui := Gui("+AlwaysOnTop +ToolWindow -Caption +Border", "QuickPanel")
    myGui.BackColor := "F0F0F0"
    myGui.SetFont("s10")

    ; Проверяем состояние экранной клавиатуры
    isOSKVisible := WinExist("ahk_exe osk.exe")
    oskButtonText := isOSKVisible ? "osk hide" : "osk show"

    ; Добавляем кнопки действий
    myGui.Add("Button", "x10 y10 w100 h30", oskButtonText).OnEvent("Click", (*) => MenuAction("osk_toggle", myGui))
    myGui.Add("Button", "x10 y50 w100 h30", "osk to cursor").OnEvent("Click", (*) => MenuAction("osk_to_cursor", myGui))
    myGui.Add("Button", "x10 y90 w100 h30", "mouse jump").OnEvent("Click", (*) => MenuAction("mouse_jump", myGui))
    myGui.Add("Button", "x10 y130 w100 h30", "crosshair").OnEvent("Click", (*) => MenuAction("crosshair", myGui))
    myGui.Add("Button", "x10 y170 w100 h30", "Отмена").OnEvent("Click", (*) => DestroyMenu(myGui))


    ; Добавляем таймер обратного отсчета
    timeLeft := 3
    timerText := myGui.Add("Text", "x10 y205 w100 h20 Center cGray", "Закроется через " timeLeft "s")

    ; Показываем окно рядом с курсором
    panelX := x - 60
    panelY := y - 85
    myGui.Show("x" panelX " y" panelY " w120 h250")

    ; Запускаем таймер обратного отсчета
    timer := SetTimer(updateTimer, 1000)

    updateTimer() {
        timeLeft--

        if (timeLeft <= 0) {
            DestroyMenu(myGui)
            return
        }

        ; Обновляем текст таймера
        try {
            if (WinExist(myGui.Hwnd)) {
                timerText.Text := "Закроется через " timeLeft "s"

                ; Меняем цвет при малом времени
                if (timeLeft <= 2) {
                    timerText.Opt("cRed")
                } else {
                    timerText.Opt("cGray")
                }
            } else {
                SetTimer timer, 0
            }
        }
    }

    ; Устанавливаем таймер закрытия меню
    SetTimer(() => DestroyMenu(myGui), -menuTimeout)
}

MenuAction(action, myGui) {
    switch action {
        case "osk_toggle":
            Send "#^o" ; Windows+Ctrl+O - переключает видимость OSK
        case "osk_to_cursor":
            OskToCursor()
        case "mouse_jump":
            Send "#+d" ; Windows+Shift+D
        case "crosshair":
            Send "#!p" ; Windows+Alt+P
    }

    DestroyMenu(myGui)
}

; Функция для показа OSK и перемещения курсора
OskToCursor() {
    ; Проверяем, видна ли уже экранная клавиатура
    isOSKVisible := WinExist("ahk_exe osk.exe")

    if !isOSKVisible {
        ; Если OSK не видна - показываем её
        Send "#^o"
    }

    ; Ждем появления/активации OSK и перемещаем курсор
    SetTimer MoveCursorToOSK, -1000
}

; Функция для перемещения курсора в центр экранной клавиатуры
MoveCursorToOSK() {
    ; Ждем появления экранной клавиатуры
    WinWait "ahk_exe osk.exe",, 3

    if WinExist("ahk_exe osk.exe") {
        ; Получаем позицию и размеры экранной клавиатуры
        WinGetPos(&oskX, &oskY, &oskWidth, &oskHeight, "ahk_exe osk.exe")

        ; Вычисляем центр окна
        centerX := oskX + oskWidth // 2
        centerY := oskY + oskHeight // 2

        ; Перемещаем курсор в центр экранной клавиатуры
        MouseMove centerX, centerY, 0

        ; Визуальная обратная связь
        ToolTip "Курсор перемещен в центр клавиатуры", centerX, centerY + 30
        SetTimer () => ToolTip(), -1500
    } else {
        ToolTip "Экранная клавиатура не найдена"
        SetTimer () => ToolTip(), -1500
    }
}

DestroyMenu(myGui) {
    try {
        if (WinExist(myGui.Hwnd)) {
            myGui.Destroy()
        }
    }
    ToolTip()
}

; Функция для закрытия активного GUI
DestroyActiveGui() {
    if (activeGui := GuiFromHwnd(WinExist("A"))) {
        activeGui.Destroy()
    }
    ToolTip()
}

; Обработка закрытия GUI через Escape
#HotIf WinActive("ahk_class AutoHotkeyGUI")
Escape:: {
    if (activeGui := GuiFromHwnd(WinExist("A"))) {
        activeGui.Destroy()
    }
}
#HotIf

; Пауза/возобновление отслеживания жестов
Pause:: {
    static isPaused := false
    isPaused := !isPaused

    if (isPaused) {
        SetTimer WatchGesture, 0
        ToolTip "Отслеживание жестов ПАУЗА", A_ScreenWidth // 2, 50
    } else {
        SetTimer WatchGesture, 50
        ToolTip "Отслеживание жестов ВКЛ", A_ScreenWidth // 2, 50
    }
    SetTimer () => ToolTip(), -1500
}

; Информационная панель
^!i:: {
    MsgBox "Жест активации: ВЛЕВО → ВПРАВО`n`n" .
           "Как использовать:`n" .
           "1. Сделайте движение мышью ВЛЕВО (> " minDistance "px)`n" .
           "2. Затем сразу движение ВПРАВО (> " minDistance "px)`n" .
           "3. Весь жест должен занять < " gestureTimeWindow "ms`n" .
           "4. Меню закроется автоматически через " (menuTimeout//1000) " секунды`n`n" .
           "Нажмите Pause для паузы отслеживания",
           "Информация о жесте", "Info"
}

; Инициализация
ToolTip "Жест активации: ВЛЕВО → ВПРАВО", A_ScreenWidth // 2, 50
SetTimer () => ToolTip(), -2000