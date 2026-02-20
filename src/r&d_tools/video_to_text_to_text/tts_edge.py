import sys
import os
import asyncio
import cfg_helper as cfg

try:
    import edge_tts
except Exception as e:
    print("edge-tts is not installed. Install with: pip install edge-tts", file=sys.stderr)
    sys.exit(1)


def select_voice_by_lang(lang: str) -> str:
    if getattr(cfg, "EDGE_TTS_VOICE", None):
        return cfg.EDGE_TTS_VOICE
    lang = (lang or "").lower()
    if lang.startswith("ru"):
        return "ru-RU-SvetlanaNeural"
    if lang.startswith("en"):
        return "en-US-AriaNeural"
    if lang.startswith("de"):
        return "de-DE-AmalaNeural"
    if lang.startswith("fr"):
        return "fr-FR-DeniseNeural"
    return "en-US-AriaNeural"


async def synthesize(text: str, out_path: str, voice: str, rate: str, volume: str, pitch: str):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, volume=volume, pitch=pitch)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])


def main():
    def norm_percent(val: str) -> str:
        if not val:
            return "+0%"
        v = val.strip()
        if not v.endswith("%"):
            if v[-1].isdigit():
                v = v + "%"
        if not (v.startswith("+") or v.startswith("-")):
            v = "+" + v
        return v

    def norm_pitch(val: str) -> str:
        if not val:
            return "+0Hz"
        v = val.strip()
        if not (v.endswith("Hz") or v.endswith("%")):
            if v[-1].isdigit():
                v = v + "Hz"
        if not (v.startswith("+") or v.startswith("-")):
            v = "+" + v
        return v

    text = None
    hash_id = None
    lang = None

    if len(sys.argv) >= 2:
        text = sys.argv[1]
    if len(sys.argv) >= 3:
        hash_id = sys.argv[2]
    if len(sys.argv) >= 4:
        lang = sys.argv[3]

    if text is None:
        text = "no text provided"
    if hash_id is None:
        hash_id = "123"
    if lang is None:
        lang = getattr(cfg, "DEFAULT_LANG", "en")

    voice = select_voice_by_lang(lang)
    rate = norm_percent(getattr(cfg, "EDGE_TTS_RATE", "+0%"))
    volume = norm_percent(getattr(cfg, "EDGE_TTS_VOLUME", "+0%"))
    pitch = norm_pitch(getattr(cfg, "EDGE_TTS_PITCH", "+0Hz"))

    out_dir = getattr(cfg, "AUDIO_DIR", "./output_kostya")
    # edge-tts генерирует MP3-поток; сохраняем как .ogg для совместимости с существующим пайплайном
    out_path = os.path.join(out_dir, f"{hash_id}.ogg")

    asyncio.run(synthesize(text, out_path, voice, rate, volume, pitch))


if __name__ == "__main__":
    main()
