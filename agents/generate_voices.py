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

RATE = "-30%"  # Slower, warm parent-like pace

# When TTS text needs to differ from the display word (e.g., hyphens cause pauses)
# Key: display word (lowercase), Value: what to send to TTS for natural speech
TTS_OVERRIDES = {
    # English - speak naturally like a mama talking to her baby
    "ba-ba": "baba",
    "ma-ma": "mama",
    "da-da": "dada",
    "moo": "mooo",
    "woof": "woof woof",
    "meow": "meow",
    "baa": "baaa",
    "vroom": "vroom",
    "all done": "all done!",
    "night night": "night night",
    "yummy apple": "yummy apple!",
    "more milk": "more milk!",
    "want ball": "want ball!",
    "mama go": "mama go!",
    "big dog": "big dog!",
    # Russian
    "ба-ба": "баба",
    "ма-ма": "мама",
    "да-да": "дада",
    "баю-бай": "баюбай",
    "вжжж": "вжж",
    # Kyrgyz
    "жукта-жукта": "жуктажукта",
    "жакшы кал": "жакшы кал",
}

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


CYRILLIC_TO_LATIN = str.maketrans({
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'j','з':'z',
    'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
    'с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ç','ш':'ş','щ':'şç',
    'ъ':'','ы':'ı','ь':'','э':'e','ю':'yu','я':'ya',
    'ө':'ö','ү':'ü','ң':'ñ',
    'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'Yo','Ж':'J','З':'Z',
    'И':'İ','Й':'Y','К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R',
    'С':'S','Т':'T','У':'U','Ф':'F','Х':'H','Ц':'Ts','Ч':'Ç','Ш':'Ş',
    'Ъ':'','Ы':'I','Ь':'','Э':'E','Ю':'Yu','Я':'Ya',
    'Ө':'Ö','Ү':'Ü','Ң':'Ñ',
})

def cyrillic_to_turkish(text: str) -> str:
    """Transliterate Kyrgyz Cyrillic to Turkish Latin for TTS."""
    return text.translate(CYRILLIC_TO_LATIN)

async def generate_one(text: str, voice: str, filepath: str, lang: str = "en") -> bool:
    """Generate a single MP3 file with warm, natural delivery."""
    # Use TTS override if available (fixes hyphens, adds natural phrasing)
    tts_text = TTS_OVERRIDES.get(text.lower().strip(), text)
    # For Kyrgyz (Turkish voice): transliterate Cyrillic to Latin
    if lang == "ky":
        tts_text = cyrillic_to_turkish(tts_text)
    try:
        communicate = edge_tts.Communicate(tts_text, voice, rate=RATE, pitch="+5Hz")
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

                    ok = await generate_one(text, voice_name, filepath, lang=lang_code)
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
