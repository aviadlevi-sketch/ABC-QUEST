#!/usr/bin/env python3
"""ABC QUEST: complete 26 English LETTER NAMES using approved contextual method B.
Reuse six approved letter clips and approved US pronunciation of zebra.
Does NOT generate or replace any phonics sounds.
"""
from __future__ import annotations
import argparse
import base64
import html
import json
import os
from pathlib import Path
import shutil
import string
import tempfile

from repair_pronunciation_pilot import tts, crop_last_letter

VOICE_ID = "NoOVOzCQFLOvtsMoNcdT"
APPROVED = "ABCMWZ"

def check_mp3(p:Path):
    data=p.read_bytes()
    if len(data)<1000 or not (data[:3]==b"ID3" or data[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")):
        raise RuntimeError(f"File not valid MP3: {p}")
    return data

def build_player(folder:Path):
    blocks=[]
    for letter in string.ascii_uppercase:
        uri="data:audio/mpeg;base64,"+base64.b64encode(check_mp3(folder/"names"/(letter+".mp3"))).decode("ascii")
        approved="<span>אושר בניסוי הקודם</span>" if letter in APPROVED else "<span>חדש — לבדיקה</span>"
        blocks.append(f'<div class="item"><b>{letter}</b>{approved}<audio controls preload="none" src="{uri}"></audio></div>')
    uri="data:audio/mpeg;base64,"+base64.b64encode(check_mp3(folder/"words"/"zebra.mp3")).decode("ascii")
    header='''<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ABC QUEST — 26 שמות אותיות/Zebra</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{background:#10235e;color:#fff;font:16px system-ui,Arial,sans-serif;max-width:920px;margin:auto;padding:18px}
h1{font-size:29px}p{color:#d7e2ff;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:11px}
.item{background:#234184;border-radius:12px;padding:12px;display:grid;gap:6px}
b{font-size:28px}.item span{color:#cbdcff;font-size:12px}
audio{width:100%;min-width:0}
aside{background:#394777;border-radius:12px;padding:14px;margin:16px 0}
</style>
<body><h1>🎙️ ABC QUEST — 26 שמות אותיות</h1>
<p>אלו שמות האותיות (Letter Names), לא הצלילים הפונטיים. כולם בקול 2 של ElevenLabs בשיטה B:
הפקה מתוך משפט טבעי והפרדת שם האות.</p>
<aside>אותיות A, B, C, M, W, Z הן בדיוק ההקלטות שכבר אישרת. שאר 20 האותיות חדשות ודורשות האזנה ואישור.
המילה Zebra מופיעה בתחתית בהגיית ZEE-bruh (שיטה A) שאישרת.</aside>
<div class="grid">'''
    last=f'''</div><h2>Zebra — הגרסה שאושרה</h2>
<div class="grid"><div class="item"><b>Zebra</b><span>ZEE-bruh · שיטה A</span>
<audio controls preload="none" src="{uri}"></audio></div></div>
<p>26 הצלילים הפונטיים יופקו ממקור הקלטות נפרד; אין כאן צלילים מסונתזים שאינם מדויקים.</p>
<script>document.querySelectorAll("audio").forEach(a=>a.addEventListener("play",()=>document.querySelectorAll("audio").forEach(b=>{if(b!==a&&!b.paused)b.pause()})))</script>
</body></html>'''
    page=header+"".join(blocks)+last
    assert page.count("<audio controls")==27
    (folder/"LISTEN_26_LETTER_NAMES_AND_ZEBRA.html").write_text(page,encoding="utf-8")
    (folder/"PRODUCTION_NOTES.txt").write_text(
        "VOICE ID: "+VOICE_ID+"\n"
        "APPROVED letter name method B: Extract target letter from 'The letter is X.' with ElevenLabs alignment + ffmpeg.\n"
        "Reused approved letter recordings: "+", ".join(APPROVED)+"\n"
        "Zebra is reused from approved method A (spoken prompt 'ZEE-bruh.').\n"
        "No phonics sounds are included. No Android app changes made.\n"
        "Review all 20 additional letter names before installing in the APK.\n", encoding="utf-8"
    )
    print(f"Offline listening page prepared: 27 embedded clips / {len(page):,} chars",flush=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--approved",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    key=os.environ.get("ELEVENLABS_API_KEY","").strip()
    if not key:
        raise SystemExit("Missing ElevenLabs API key in GitHub secret. No requests made.")
    dest=args.out
    (dest/"names").mkdir(parents=True,exist_ok=True)
    (dest/"words").mkdir(parents=True,exist_ok=True)
    for letter in APPROVED:
        old=args.approved/"names"/letter/"context_cropped.mp3"
        check_mp3(old)
        shutil.copyfile(old,dest/"names"/(letter+".mp3"))
        print(f"Reusing approved name {letter} (0 new API credits)",flush=True)
    old_zebra=args.approved/"zebra"/"zee-bruh.mp3"
    check_mp3(old_zebra)
    shutil.copyfile(old_zebra,dest/"words"/"zebra.mp3")
    print("Reusing approved US zebra (0 new API credits)",flush=True)
    for letter in string.ascii_uppercase:
        path=dest/"names"/(letter+".mp3")
        if path.exists():
            check_mp3(path)
            continue
        print(f"Producing name {letter} from sentence alignment.",flush=True)
        with tempfile.TemporaryDirectory(prefix="abcquest-clip-") as temporary:
            raw,alignment=tts(key,f"The letter is {letter}.","eleven_multilingual_v2",True)
            clip,meta=crop_last_letter(raw,alignment,letter,Path(temporary))
        path.write_bytes(clip)
        check_mp3(path)
        print(f"  Saved {letter}: {len(clip)} bytes (align {meta['start']:.2f}s–{meta['end']:.2f}s)",flush=True)
    assert len(list((dest/"names").glob("*.mp3")))==26
    build_player(dest)
    print("READY: 26 alphabet names + US zebra, with 20 newly generated names.",flush=True)

if __name__=="__main__":
    main()
