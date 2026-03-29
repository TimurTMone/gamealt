#!/usr/bin/env python3
"""
🔊 Edge TTS Voice Generator for BabyPath Speech Buddy
======================================================
Pre-generates MP3 files for all words in all languages using Microsoft Edge TTS.
Run once, then bundle the output with the Capacitor app.

Usage:
    python3 generate_voices.py           # Generate all voices
    python3 generate_voices.py --test    # Generate 3 test files only
"""

import asyncio
import os
import sys
import json
import edge_tts

# ── VOICE CONFIG ──
VOICES = {
    "en": {"female": "en-US-AriaNeural", "male": "en-US-ChristopherNeural"},
    "ru": {"female": "ru-RU-SvetlanaNeural", "male": "ru-RU-DmitryNeural"},
    "ky": {"female": "tr-TR-EmelNeural", "male": "tr-TR-AhmetNeural"},  # Turkish fallback
}

RATE = "-20%"  # Slower, parent-like pace

# ── OUTPUT DIR ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(BASE_DIR, "assets", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# ── WORD DATABASE (must match speech-buddy.html STAGES) ──
WORDS = {
    "s1": [  # Sounds & Babbling
        {"en": "ba-ba", "ru": "ба-ба", "ky": "ба-ба"},
        {"en": "ma-ma", "ru": "ма-ма", "ky": "ма-ма"},
        {"en": "da-da", "ru": "да-да", "ky": "да-да"},
        {"en": "moo", "ru": "му", "ky": "муу"},
        {"en": "woof", "ru": "гав", "ky": "ав"},
        {"en": "meow", "ru": "мяу", "ky": "мяу"},
        {"en": "baa", "ru": "бее", "ky": "маа"},
        {"en": "vroom", "ru": "вжжж", "ky": "вжжж"},
    ],
    "s2": [  # First Core Words
        {"en": "More", "ru": "Ещё", "ky": "Дагы"},
        {"en": "All done", "ru": "Всё", "ky": "Бүттү"},
        {"en": "Up", "ru": "Вверх", "ky": "Жогору"},
        {"en": "Open", "ru": "Открой", "ky": "Ач"},
        {"en": "Go", "ru": "Иди", "ky": "Бар"},
        {"en": "Stop", "ru": "Стоп", "ky": "Токто"},
        {"en": "Help", "ru": "Помоги", "ky": "Жардам"},
        {"en": "Hi", "ru": "Привет", "ky": "Салам"},
        {"en": "Bye", "ru": "Пока", "ky": "Жакшы кал"},
        {"en": "Want", "ru": "Хочу", "ky": "Керек"},
        {"en": "Yes", "ru": "Да", "ky": "Ооба"},
        {"en": "No", "ru": "Нет", "ky": "Жок"},
    ],
    "s3": [  # First Nouns & Verbs
        {"en": "Mama", "ru": "Мама", "ky": "Апа"},
        {"en": "Papa", "ru": "Папа", "ky": "Ата"},
        {"en": "Milk", "ru": "Молоко", "ky": "Сүт"},
        {"en": "Water", "ru": "Вода", "ky": "Суу"},
        {"en": "Banana", "ru": "Банан", "ky": "Банан"},
        {"en": "Ball", "ru": "Мяч", "ky": "Топ"},
        {"en": "Dog", "ru": "Собака", "ky": "Ит"},
        {"en": "Cat", "ru": "Кошка", "ky": "Мышык"},
        {"en": "Eat", "ru": "Кушать", "ky": "Же"},
        {"en": "Sleep", "ru": "Спать", "ky": "Укта"},
        {"en": "Eye", "ru": "Глаз", "ky": "Көз"},
        {"en": "Nose", "ru": "Нос", "ky": "Мурун"},
    ],
    "s4": [  # Word Combinations
        {"en": "More milk", "ru": "Ещё молоко", "ky": "Дагы сүт"},
        {"en": "Want ball", "ru": "Хочу мяч", "ky": "Топ керек"},
        {"en": "Mama go", "ru": "Мама иди", "ky": "Апа бар"},
        {"en": "Big dog", "ru": "Большая собака", "ky": "Чоң ит"},
        {"en": "Night night", "ru": "Баю-бай", "ky": "Жукта-жукта"},
        {"en": "Yummy apple", "ru": "Вкусное яблоко", "ky": "Даамдуу алма"},
    ],
}


def get_filename(lang: str, gender: str, word: str) -> str:
    """Generate a safe filename for a word."""
    safe = word.lower().strip().replace(" ", "_").replace("-", "_")
    # transliterate common chars for filename safety
    for old, new in [("ё", "yo"), ("ü", "u"), ("ө", "o"), ("ң", "n")]:
        safe = safe.replace(old, new)
    return f"{lang}_{gender}_{safe}.mp3"


async def generate_one(text: str, voice: str, filepath: str) -> bool:
    """Generate a single MP3 file."""
    try:
        communicate = edge_tts.Communicate(text, voice, rate=RATE)
        await communicate.save(filepath)
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


async def generate_all(test_mode: bool = False):
    """Generate all voice files."""
    total = 0
    success = 0
    failed = 0
    skipped = 0

    # Count total
    for stage_words in WORDS.values():
        total += len(stage_words) * 3 * 2  # 3 langs × 2 genders

    if test_mode:
        total = 6  # 1 word × 3 langs × 2 genders

    print(f"\n🔊 EDGE TTS VOICE GENERATOR")
    print(f"   Target: {total} MP3 files")
    print(f"   Output: {AUDIO_DIR}\n")

    manifest = {}  # {filename: {lang, gender, word, stage}}

    for stage_id, stage_words in WORDS.items():
        words_to_process = stage_words[:1] if test_mode else stage_words

        for word_data in words_to_process:
            for lang_code, voice_config in VOICES.items():
                text = word_data.get(lang_code, word_data["en"])

                for gender, voice_name in voice_config.items():
                    filename = get_filename(lang_code, gender, text)
                    filepath = os.path.join(AUDIO_DIR, filename)

                    # Skip if already generated
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 500:
                        skipped += 1
                        manifest[filename] = {
                            "lang": lang_code, "gender": gender,
                            "word": text, "stage": stage_id
                        }
                        continue

                    print(f"  [{success + failed + skipped + 1}/{total}] {voice_name}: \"{text}\" → {filename}")

                    ok = await generate_one(text, voice_name, filepath)
                    if ok:
                        success += 1
                        manifest[filename] = {
                            "lang": lang_code, "gender": gender,
                            "word": text, "stage": stage_id
                        }
                        print(f"  ✓ OK ({os.path.getsize(filepath) // 1024}KB)")
                    else:
                        failed += 1

        if test_mode:
            break

    # Save manifest
    manifest_path = os.path.join(AUDIO_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Summary
    total_size = sum(
        os.path.getsize(os.path.join(AUDIO_DIR, f))
        for f in os.listdir(AUDIO_DIR)
        if f.endswith(".mp3")
    )

    print(f"\n{'='*50}")
    print(f"  ✓ Generated: {success}")
    print(f"  ⏭ Skipped (already exist): {skipped}")
    print(f"  ✗ Failed: {failed}")
    print(f"  📁 Output: {AUDIO_DIR}")
    print(f"  📦 Total size: {total_size / (1024*1024):.1f} MB")
    print(f"  📋 Manifest: {manifest_path}")
    print()


if __name__ == "__main__":
    test = "--test" in sys.argv
    asyncio.run(generate_all(test_mode=test))
