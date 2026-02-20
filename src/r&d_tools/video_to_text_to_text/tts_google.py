# ToDo-1 text 2 spech хороший обзор разных сервисов https://vc.ru/future/756954-poproboval-6-servisov-i-python-bibliotek-text-to-speech-tts-delyus-rezultatami
# !! Установить mpg123 / 321 и  см: https://pypi.org/project/mpyg321/
from gtts import gTTS
import os
import sys
import cfg_helper as cfg

text = None
hash = None
lang = None

if len(sys.argv) >= 2:
    text = sys.argv[1]
if len(sys.argv) >= 3:
    hash = sys.argv[2]
if len(sys.argv) >= 4:
    lang = sys.argv[3]

if text is None:
    text = "no text provided"
if hash is None:
    hash = "123"
if lang is None:
    lang = getattr(cfg, "DEFAULT_LANG", "en")

tts = gTTS(text=text, lang=lang)
out_dir = getattr(cfg, "AUDIO_DIR", "./output_kostya")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, f"{hash}.ogg")
tts.save(out_path)

