#!/usr/bin/env python3
"""Finalize ABC QUEST 26 reviewed phonics clips, keeping original Android X.

A-Z selection:
 - 9 revised letters E I K L N S U V Y: variant A (the gentle shorter crop)
 - remaining 16 letters except X: previous short cut, approved by user
 - X: original metallic phoneme from installed ABC QUEST 7.5 app archive

Makes MP3 directory and standalone Android listening page. No TTS/API calls.
Does NOT overwrite Android app. This is the approved sound pack for integration.
"""
from __future__ import annotations
import argparse
import base64
import html
import json
import shutil
import string
from pathlib import Path
from build_phoneme_review import from_archive, IPA, mp3_uri

REVISED = set("EIKLNSUVY")
ALL = string.ascii_uppercase

def validate(path):
    content=path.read_bytes()
    if len(content)<800 or not (
        content[:3]==b"ID3" or content[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")
    ):
        raise RuntimeError("MP3 is missing or invalid: "+str(path))
    return content

def make_page(out, records):
    tiles=[]
    for letter in ALL:
        content=validate(out/"phonemes"/(letter+".mp3"))
        label="הצליל המקורי מהאפליקציה" if letter=="X" else (
            "גרסת A המקוצרת שאושרה" if letter in REVISED
            else "הגרסה הקצרה שאושרה"
        )
        tiles.append('<article><div class="heading"><strong>'+letter+
          '</strong><span dir="ltr">/'+html.escape(IPA[letter])+'/</span></div>'+
          '<div class="note">'+label+'</div>'+
          '<audio controls preload="none" src="'+mp3_uri(content)+'"></audio></article>')
    page='''<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ABC QUEST — כל 26 הצלילים שאושרו</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}
body{font:15px system-ui,Arial,sans-serif;background:#0d205a;color:#fff;max-width:850px;margin:0 auto;padding:18px}
h1{font-size:28px}p{color:#d9e6ff;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
article{background:#234184;border-radius:13px;padding:12px}.heading{display:flex;align-items:center;gap:15px}
.heading strong{font-size:29px}.heading span{font-size:17px}
.note{font-size:12px;color:#d0e0ff;margin:6px 0 10px}audio{width:100%;min-width:0}
</style><body><h1>🔊 ABC QUEST — 26 צלילי אותיות</h1>
<p>25 צלילים מהחיתוכים הקצרים שאישרת. האות X משתמשת בצליל המקורי מהמשחק,
בהתאם לבחירתך. הקבצים נמצאים גם בתיקיית phonemes, ללא צורך באינטרנט.</p>
<div class="grid">'''+''.join(tiles)+'''</div>
<script>document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>
document.querySelectorAll('audio').forEach(b=>{if(b!==a&&!b.paused)b.pause()})))</script></body></html>'''
    page_path=out/"LISTEN_FINAL_26_PHONEMES.html"
    page_path.write_text(page,encoding="utf-8")
    assert page.count("<audio controls")==26
    print(f"Listening page: {len(page)} chars, 26 phonemes",flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-zip",type=Path,required=True)
    ap.add_argument("--round2",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    original=from_archive(args.original_zip)
    out=args.out
    (out/"phonemes").mkdir(parents=True,exist_ok=True)
    records=[]
    for letter in ALL:
        if letter=="X":
            data=original["X"]
            source="original_v75_game_X"
        elif letter in REVISED:
            src=args.round2/"adjusted"/(letter+"_A.mp3")
            data=validate(src)
            source="revised_gentle_A"
        else:
            src=args.round2/"previous_short"/(letter+".mp3")
            data=validate(src)
            source="previous_short"
        target=out/"phonemes"/(letter+".mp3")
        target.write_bytes(data)
        validate(target)
        records.append({"letter":letter,"phoneme_ipa":IPA[letter],
                        "selection":source,"relative_file":"phonemes/"+letter+".mp3",
                        "size_bytes":len(data)})
        print(f"{letter}: {source}, {len(data)} bytes",flush=True)
    assert len(records)==26
    assert [r["letter"] for r in records if r["selection"]=="original_v75_game_X"]==["X"]
    assert sum(r["selection"]=="revised_gentle_A" for r in records)==9
    assert sum(r["selection"]=="previous_short" for r in records)==16
    make_page(out,records)
    (out/"SELECTION_MANIFEST.json").write_text(json.dumps({
        "purpose":"approved ABC QUEST phonics sound assets",
        "voice":"ElevenLabs NoOVOzCQFLOvtsMoNcdT for 25 clips; original game sound for X",
        "uses_new_api_credits":False,
        "counts":{"original_X":1,"gentle_variant_A":9,"previous_short":16},
        "records":records,
    },ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"README.txt").write_text(
        "Open LISTEN_FINAL_26_PHONEMES.html in Chrome on Android.\n"
        "The phonemes directory has one MP3 for each A-Z. X is the original ABC QUEST 7.5 sound.\n"
        "E I K L N S U V Y use reviewed gentle variant A; other letters use previous short clips.\n"
        "No ElevenLabs API calls. The game APK is not modified by this packaging step.\n",
        encoding="utf-8")
    print("SUCCESS: 26 letter sounds finalized, X original. No ElevenLabs calls.",flush=True)

if __name__=="__main__":
    main()
