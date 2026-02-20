

# Kostya_output_watcher.py - настройки
VIDEO_SCALE_FOR_FILE_WATCHER = 0.3 #0.5
# оставлять или нет окошко с аватаром после проигрывания всех новых файлов
CLOSE_AVATAR_IF_NEW_FILES_QUEUE_EMPTY = False
# работает совместно с CLOSE_AVATAR_IF_NEW_FILES_QUEUE_EMPTY
TIME_INTERVAL_TO_DECIDE_THAT_NO_NEW_FILES_ARE_COMING = 5 #sec
WATCH_DIR = r"C:\Users\aradz\PycharmProjects\avatar_fast\output_kostya"
WATCH_FILTER = ".mp4"
WATCH_FILE_READY_CHECK_INTERVAL = 0.1
WATCHER_VLC_INTERVAL_TO_CHECK_IF_PLAYER_STILL_PLAYS = 0.05
WATCHER_VLC_DELAY_TO_START_PLAYING = 0.09
WATCHER_VLC_DELAY_TO_START_PLAYING = 0.09

# Text-to-Speech и генерация аватара
USE_EXISTING_AUDIO = False
USE_GOOGLE_TTS = True
USE_EDGE_TTS = False
USE_RHVOICE_TTS = False
USE_GDL_TTS = False

DEFAULT_LANG = "ru"
RHVOICE_VOICE = "vitaliy"
GDL_VOICE = "MARIYA"

# Edge TTS
EDGE_TTS_VOICE = "ru-RU-SvetlanaNeural" #edge-tts --list-voices
EDGE_TTS_RATE = "+0%"
EDGE_TTS_VOLUME = "+0%"
EDGE_TTS_PITCH = "+0Hz"

AVATAR_API_URL = "http://127.0.0.1:5005/v1/avatar/get-response"
AVATAR_NAME = "avatar_painter_muze_9.mp4"
AVATAR_PADS = [0, 10, 0, 0]

AUDIO_DIR = WATCH_DIR
EXISTING_AUDIO_SOURCE = r"C:\Users\aradz\PycharmProjects\avatar_fast\output_avatar_cow_girl_10.mp4.mp4-audio.ogg"
