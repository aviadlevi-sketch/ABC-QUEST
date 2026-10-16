#!/usr/bin/env python3
"""Produce a small, human-reviewable ElevenLabs speech preview for ABC QUEST.
Run only from GitHub Actions with the API key in a protected secret.
No API key or user information is embedded into the app or preview files.
"""
import argparse
import html as html_lib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

SAMPLES = [
    ("names", "A", "ay"),
    ("names", "B", "bee"),
    ("names", "C", "see"),
    ("names", "M", "em"),
    ("names", "Z", "zee"),
    ("words", "apple", "apple"),
    ("words", "ball", "ball"),
    ("words", "cat", "cat"),
    ("words", "dog", "dog"),
    ("words", "elephant", "elephant"),
    ("words", "fish", "fish"),
    ("words", "queen", "queen"),
    ("words", "sun", "sun"),
    ("words", "water", "water"),
    ("words", "zebra", "zebra"),
]

def words_from_android_zip(archive):
    with zipfile.ZipFile(archive) as z:
        found = [n for n in z.namelist() if n.endswith("/app/src/main/assets/index.html")]
        if len(found) != 1:
            raise RuntimeError("Expected one app/src/main/assets/index.html in Android archive")
        document = z.read(found[0]).decode("utf-8")
    label = "const WORD_BANK="
    start = document.find(label)
    if start < 0:
        raise RuntimeError("WORD_BANK missing from ABC QUEST")
    result, _ = json.JSONDecoder().raw_decode(document[start + len(label):])
    assert len(result) == 26 and sum(map(len, result.values())) == 156
    return {str(row["word"]).lower() for entries in result.values() for row in entries}

def request_audio(key, voice_id, phrase, model_id):
    url = "https://api.elevenlabs.io/v1/text-to-speech/" + urllib.parse.quote(voice_id, safe="")
    url += "?output_format=mp3_44100_128"
    body = json.dumps({
        "text": phrase,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.68,
            "similarity_boost": 0.78,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                audio = response.read()
                if not audio or len(audio) < 1000:
                    raise RuntimeError("Empty or invalid audio from voice provider")
                return audio
        except urllib.error.HTTPError as exc:
            # Never dump headers or requests, as those include credentials.
            info = exc.read(300).decode("utf-8", errors="replace")
            if exc.code in (429, 500, 502, 503) and attempt < 2:
                print(f"Temporary provider failure HTTP {exc.code}; retrying.", flush=True)
                time.sleep((attempt + 1) * 4)
                continue
            raise RuntimeError(f"ElevenLabs returned HTTP {exc.code}: {info}") from None
    raise RuntimeError("Unable to generate after three attempts")

def create_listening_page(output):
    blocks = []
    for category, file_id, spoken in SAMPLES:
        rel = f"{category}/{file_id}.mp3"
        label = "שם האות" if category == "names" else "מילה"
        blocks.append(
            f'<section><strong>{html_lib.escape(file_id)}</strong>'
            f'<span>{label} · prompt: {html_lib.escape(spoken)}</span>'
            f'<audio controls preload="none" src="{rel}"></audio></section>'
        )
    page = """<!doctype html><html lang="he" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ABC QUEST — ElevenLabs voice test</title><style>
body{font-family:Arial,sans-serif;background:#112362;color:white;max-width:720px;margin:auto;padding:25px}
section{display:grid;grid-template-columns:80px 1fr;gap:12px;align-items:center;
background:#243d86;border-radius:12px;padding:12px;margin:10px 0}
audio{grid-column:1/-1;width:100%}span{font-size:13px;color:#d4e0ff}
</style></head><body><h1>🔊 ABC QUEST — מבחן קריינות נשית</h1>
<p>האזן להקלטות. שמות האותיות A, B, C, M ו-Z דורשים בדיקת הגייה קפדנית.
הצלילים הפונטיים (כמו /b/) אינם חלק מחבילת הניסוי הזאת ויטופלו בנפרד.</p>
""" + "\n".join(blocks) + "</body></html>"
    (output / "LISTEN_FIRST.html").write_text(page, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--voice-id", required=True)
    parser.add_argument("--model-id", default="eleven_multilingual_v2")
    args = parser.parse_args()
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        sys.exit("Missing GitHub Actions secret ELEVENLABS_API_KEY; no requests sent.")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,90}", args.voice_id):
        sys.exit("Invalid voice ID; no requests sent.")
    available = words_from_android_zip(args.archive)
    absent = [name for category, name, _ in SAMPLES if category == "words" and name not in available]
    if absent:
        sys.exit("Preview words not in current game: " + ", ".join(absent))
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"names": {}, "phonemes": {}, "words": {}}
    for i, (category, ident, text) in enumerate(SAMPLES, start=1):
        target = output / category / (ident + ".mp3")
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f"{i:02d}/{len(SAMPLES)}: {category}/{ident}.mp3", flush=True)
        target.write_bytes(request_audio(api_key, args.voice_id, text, args.model_id))
        manifest[category][ident] = f"audio/{category}/{ident}.mp3"
    (output / "manifest.js").write_text(
        "window.ABC_QUEST_AUDIO=" + json.dumps(manifest, ensure_ascii=False) + ";",
        encoding="utf-8",
    )
    create_listening_page(output)
    (output / "README.txt").write_text(
        "ABC QUEST — ElevenLabs voice pilot\n"
        "Open LISTEN_FIRST.html to listen to all 15 samples.\n"
        "Names use pronunciation prompt spellings, which MUST be reviewed.\n"
        "No phonemes produced. Do not publish this preview as a complete voice pack.\n"
        f"Model: {args.model_id}\nVoice ID: {args.voice_id}\n",
        encoding="utf-8",
    )
    print("Success: 15 MP3 previews saved. No full pack generated.", flush=True)

if __name__ == "__main__":
    main()
