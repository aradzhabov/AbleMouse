#Requires AutoHotkey v2.0
#SingleInstance Force
SendMode "Input"
SetWorkingDir A_ScriptDir

; Gesture settings
gestureTimeWindow := 1000  ; Gesture time window in milliseconds
minDistance := 50          ; Minimum movement distance in pixels
maxPause := 300            ; Maximum pause between movements
menuTimeout := 3000        ; Menu close timeout after 3 seconds

; Hotkey settings
oskToggleHotkey := "#^o"   ; Windows+Ctrl+O - toggles OSK visibility
mouseJumpHotkey := "#+d"   ; Windows+Shift+D
crosshairHotkey := "#!p"   ; Windows+Alt+P

; Variables for gesture tracking
lastX := 0
lastY := 0
lastMoveTime := 0
gestureStep := 0           ; 0: waiting, 1: left movement, 2: right movement

; Start monitoring movements
SetTimer WatchGesture, 50

WatchGesture() {
    global lastX, lastY, lastMoveTime, gestureStep
    global gestureTimeWindow, minDistance, maxPause

    ; Get current mouse position
    MouseGetPos(&currentX, &currentY)
    currentTime := A_TickCount

    ; Check movement only if mouse has moved
    if (currentX != lastX || currentY != lastY) {
        deltaX := currentX - lastX
        deltaTime := currentTime - lastMoveTime

        ; Determine movement direction
        if (Abs(deltaX) > Abs(currentY - lastY) * 2) { ; Horizontal movement predominates
            if (deltaX < -minDistance) { ; Left movement
                if (gestureStep == 0 && deltaTime < maxPause) {
                    gestureStep := 1
                    lastMoveTime := currentTime
                    ShowFeedback("← Left movement")
                }
            }
            else if (deltaX > minDistance) { ; Right movement
                if (gestureStep == 1 && deltaTime < maxPause) {
                    ; Gesture completed!
                    gestureStep := 0
                    ShowQuickPanel()
                    ShowFeedback("✓ Gesture recognized!")
                }
            }
        }

        ; Update last position and time
        lastX := currentX
        lastY := currentY
        lastMoveTime := currentTime
    }

    ; Reset gesture if time has expired
    if (gestureStep > 0 && (currentTime - lastMoveTime) > gestureTimeWindow) {
        gestureStep := 0
        ShowFeedback("✗ Gesture reset")
    }
}

ShowFeedback(message) {
    MouseGetPos(&x, &y)
    ToolTip message, x + 20, y + 20
    SetTimer () => ToolTip(), -800
}

ShowQuickPanel() {
    global menuTimeout

    ; Get mouse position
    MouseGetPos(&x, &y)

    ; Create GUI window
    myGui := Gui("+AlwaysOnTop +ToolWindow -Caption +Border", "QuickPanel")
    myGui.BackColor := "F0F0F0"
    myGui.SetFont("s10")

    ; Check on-screen keyboard state
    isOSKVisible := WinExist("ahk_exe osk.exe")
    oskButtonText := isOSKVisible ? "⌨️ osk hide" : "⌨️ osk show"

    ; Add action buttons
    myGui.Add("Button", "x10 y10 w100 h30", oskButtonText).OnEvent("Click", (*) => MenuAction("osk_toggle", myGui))
    myGui.Add("Button", "x10 y50 w100 h30", " ️➤ to ⌨️osk").OnEvent("Click", (*) => MenuAction("osk_to_cursor", myGui))
    myGui.Add("Button", "x10 y90 w100 h30", "🖥️ mouse jump").OnEvent("Click", (*) => MenuAction("mouse_jump", myGui))
    myGui.Add("Button", "x10 y130 w100 h30", "🎯 crosshair").OnEvent("Click", (*) => MenuAction("crosshair", myGui))
    myGui.Add("Button", "x10 y170 w100 h30", "❌ сancel").OnEvent("Click", (*) => DestroyMenu(myGui))


    ; Add countdown timer
    countdownTime := menuTimeout // 1000  ; Convert milliseconds to seconds
    timeLeft := countdownTime
    timerText := myGui.Add("Text", "x10 y205 w100 h20 Center cGray", "Closes in " timeLeft "s")

    ; Show window near cursor
    panelX := x - 60
    panelY := y - 85
    myGui.Show("x" panelX " y" panelY " w120 h250")

    ; Start countdown timer
    timer := SetTimer(updateTimer, 1000)

    updateTimer() {
        timeLeft--

        if (timeLeft <= 0) {
            DestroyMenu(myGui)
            return
        }

        ; Update timer text
        try {
            if (WinExist(myGui.Hwnd)) {
                timerText.Text := "Closes in " timeLeft "s"

                ; Change color when time is low
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

    ; Set menu close timer
    SetTimer(() => DestroyMenu(myGui), -menuTimeout)
}

MenuAction(action, myGui) {
    global oskToggleHotkey, mouseJumpHotkey, crosshairHotkey

    switch action {
        case "osk_toggle":
            Send oskToggleHotkey
        case "osk_to_cursor":
            OskToCursor()
        case "mouse_jump":
            Send mouseJumpHotkey
        case "crosshair":
            Send crosshairHotkey
    }

    DestroyMenu(myGui)
}

; Function to show OSK and move cursor
OskToCursor() {
    global oskToggleHotkey

    ; Check if on-screen keyboard is already visible
    isOSKVisible := WinExist("ahk_exe osk.exe")

    if !isOSKVisible {
        ; If OSK is not visible - show it
        Send oskToggleHotkey
    }

    ; Wait for OSK to appear/activate and move cursor
    SetTimer MoveCursorToOSK, -1000
}

; Function to move cursor to center of on-screen keyboard
MoveCursorToOSK() {
    ; Wait for on-screen keyboard to appear
    WinWait "ahk_exe osk.exe",, 3

    if WinExist("ahk_exe osk.exe") {
        ; Get position and dimensions of on-screen keyboard
        WinGetPos(&oskX, &oskY, &oskWidth, &oskHeight, "ahk_exe osk.exe")

        ; Calculate window center
        centerX := oskX + oskWidth // 2
        centerY := oskY + oskHeight // 2

        ; Move cursor to center of on-screen keyboard
        MouseMove centerX, centerY, 0

        ; Visual feedback
        ToolTip "Cursor moved to keyboard center", centerX, centerY + 30
        SetTimer () => ToolTip(), -1500
    } else {
        ToolTip "On-screen keyboard not found"
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

; Function to close active GUI
DestroyActiveGui() {
    if (activeGui := GuiFromHwnd(WinExist("A"))) {
        activeGui.Destroy()
    }
    ToolTip()
}

; Handle GUI close via Escape
#HotIf WinActive("ahk_class AutoHotkeyGUI")
Escape:: {
    if (activeGui := GuiFromHwnd(WinExist("A"))) {
        activeGui.Destroy()
    }
}
#HotIf

; Pause/resume gesture tracking
Pause:: {
    static isPaused := false
    isPaused := !isPaused

    if (isPaused) {
        SetTimer WatchGesture, 0
        ToolTip "Gesture tracking PAUSED", A_ScreenWidth // 2, 50
    } else {
        SetTimer WatchGesture, 50
        ToolTip "Gesture tracking ON", A_ScreenWidth // 2, 50
    }
    SetTimer () => ToolTip(), -1500
}


; Information panel Ctrl+Alt+I
^!i:: {
    global minDistance, gestureTimeWindow, menuTimeout
    global oskToggleHotkey, mouseJumpHotkey, crosshairHotkey

    MsgBox(
        "Activation gesture: LEFT → RIGHT`n`n" .
        "How to use:`n" .
        "1. Make a LEFT mouse movement (> " minDistance "px)`n" .
        "2. Then immediately a RIGHT movement (> " minDistance "px)`n" .
        "3. The entire gesture must take < " gestureTimeWindow "ms`n" .
        "4. Menu will close automatically after " (menuTimeout//1000) " seconds`n`n"
    )
}

; Initialization
ToolTip "Activation gesture: LEFT → RIGHT", A_ScreenWidth // 2, 50
SetTimer () => ToolTip(), -2000