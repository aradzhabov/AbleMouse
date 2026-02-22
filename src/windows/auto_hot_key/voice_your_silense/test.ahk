; Жест для вызова меню - например, поднятие обеих бровей
; (это эмулирует нажатие F24 через программу распознавания жестов)

; Для тестирования - вызывать меню по Ctrl+3
^3::
    Gosub, F24  ; Выполняет тот же код, что и для F24
return

; Основной жест - поднятие обеих бровей (эмулирует F24)
F24::
    ShowCommandMenu()
return


ShowCommandMenu()
{
    ; Создаем плавающее меню
    Menu, MyCommands, Add, Open Notepad, ExecuteCommand
    Menu, MyCommands, Add, ✉️ Открыть Почту, ExecuteCommand
    Menu, MyCommands, Add, 📁 Проводник, ExecuteCommand
    Menu, MyCommands, Add, 🔊 Громкость+, ExecuteCommand
    Menu, MyCommands, Add, 🔉 Громкость-, ExecuteCommand
    Menu, MyCommands, Add, ❌ Закрыть окно, ExecuteCommand
    Menu, MyCommands, Add, 🗂️ Свернуть все, ExecuteCommand

    ; Показываем меню в позиции курсора
    Menu, MyCommands, Show
}

ExecuteCommand:
    ; Определяем какая команда выбрана и проигрываем соответствующий аудио-файл
    if (A_ThisMenuItem = "Open Notepad")
        PlayAudioCommand("open_notepad.mp3")
    else if (A_ThisMenuItem = "✉️ Открыть Почту")
        PlayAudioCommand("open_email.wav")
    else if (A_ThisMenuItem = "📁 Проводник")
        PlayAudioCommand("open_explorer.wav")
    else if (A_ThisMenuItem = "🔊 Громкость+")
        PlayAudioCommand("volume_up.wav")
    else if (A_ThisMenuItem = "🔉 Громкость-")
        PlayAudioCommand("volume_down.wav")
    else if (A_ThisMenuItem = "❌ Закрыть окно")
        PlayAudioCommand("close_window.wav")
    else if (A_ThisMenuItem = "🗂️ Свернуть все")
        PlayAudioCommand("minimize_all.wav")
return

PlayAudioCommand(filename)
{
    ; Временно увеличиваем громкость до максимума
    SoundSet, 100

    ; Проигрываем аудио-команду
    SoundPlay, C:\Users\aradz\PycharmProjects\AbleMouse\src\windows\auto_hot_key\voice_your_silense\%filename%

    ; Ждем окончания воспроизведения
    Sleep, 2000

    ; Возвращаем прежнюю громкость (опционально)
    SoundSet, 70
}