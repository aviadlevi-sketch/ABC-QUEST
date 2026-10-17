#!/usr/bin/env python3
"""Generate the COMPLETE ABC QUEST English word-bank with approved ElevenLabs Voice 2.

Sources:
 - Word bank is parsed directly from current Android v7.5 game's index.html ZIP
 - Existing natural-word recordings from prior X phoneme extraction artifact
 - Zebra MUST be approved US "ZEE-bruh" (never synthesized as "zebra")
 - Any missing words are generated once with the user's existing ElevenLabs
   account secret, without exposing credentials and without modifying the APK.

Artifacts include a complete 156-MP3 set, normalized manifest for installation,
and a standalone Android-friendly HTML audio listener.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
from collections import OrderedDict
from pathlib import Path
import re
import shutil
import sys
import time
import zipfile

from generate_previews import request_audio

VOICE_ID = "NoOVOzCQFLOvtsMoNcdT"
MODEL_ID = "eleven_multilingual_v2"

def word_bank(archive: Path):
    with zipfile.ZipFile(archive) as z:
        matches=[x for x in z.namelist() if x.endswith("app/src/main/assets/index.html")]
        if len(matches)!=1:
            raise RuntimeError("Cannot locate exactly one ABC QUEST Android HTML in ZIP")
        page=z.read(matches[0]).decode("utf-8")
    match=re.search(r"\bconst\s+WORD_BANK\s*=\s*",page)
    if not match:
        raise RuntimeError("Cannot find the app WORD_BANK constant")
    categories,_=json.JSONDecoder().raw_decode(page[match.end():])
    if not isinstance(categories,dict) or len(categories)!=26:
        raise RuntimeError("Expected exactly 26 word bank letter categories")
    catalog=[]
    counts={}
    known_paths=set()
    for letter,rows in categories.items():
        if not isinstance(letter,str) or not re.fullmatch("[A-Z]",letter):
            raise RuntimeError("Unexpected word bank letter: "+repr(letter))
        if not isinstance(rows,list) or len(rows)!=6:
            raise RuntimeError(f"Expected exactly six words for letter {letter}")
        counts[letter]=len(rows)
        for row in rows:
            if not isinstance(row,dict) or not isinstance(row.get("word"),str):
                raise RuntimeError("Word bank row has no word field")
            display=row["word"].strip()
            key=display.lower()
            if not re.fullmatch(r"[a-z]+(?:[-'][a-z]+)*",key):
                raise RuntimeError(f"Unsafe word for filename: {display}")
            rel=f"words/{letter}/{key}.mp3"
            if rel in known_paths:
                raise RuntimeError("Duplicate within one letter: "+rel)
            known_paths.add(rel)
            catalog.append({"key":key,"word":display,"letter":letter,"file":rel})
    if len(catalog)!=156 or set(counts)!={chr(i) for i in range(65,91)}:
        raise RuntimeError(f"Expected 156 word placements across A-Z; found {len(catalog)}")
    print(f"Validated source list: 156 placements, {len({x['key'] for x in catalog})} unique spoken words",flush=True)
    return catalog

def read_mp3(path: Path):
    if not path.is_file():
        raise RuntimeError(f"Missing MP3 recording: {path}")
    data=path.read_bytes()
    if len(data)<1000 or not (
        data[:3]==b"ID3" or data[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")
    ):
        raise RuntimeError(f"Recording does not look like valid MP3: {path}")
    return data

def embed(path: Path):
    return "data:audio/mpeg;base64,"+base64.b64encode(read_mp3(path)).decode("ascii")

def make_mobile_listener(out: Path, records: list):
    sections=[]
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        all_for_letter=[r for r in records if r["letter"]==letter]
        if len(all_for_letter)!=6:
            raise RuntimeError(f"Wrong number of words in {letter}")
        cards=[]
        for record in all_for_letter:
            name=record["key"]
            label=record["word"]
            src=embed(out/record["file"])
            marker="הגייה שאושרה" if name=="zebra" else ("הקלטה קיימת" if record["source"]=="reused" else "הקלטה חדשה")
            cards.append(
                '<article><div class="w"><strong dir="ltr">'+html.escape(label)+
                '</strong><span>'+marker+'</span></div>'+
                '<audio preload="none" controls src="'+src+'"></audio></article>')
        sections.append(
            '<section><h2>'+letter+'</h2><div class="grid">'+''.join(cards)+'</div></section>')
    page='''<!doctype html><html lang="he" dir="rtl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ABC QUEST — 156 English words, Voice 2</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{font:15px system-ui,Arial,sans-serif;max-width:1000px;margin:0 auto;padding:16px;background:#10245e;color:white}
h1{font-size:27px}p{color:#d5e5ff;line-height:1.6}
section{background:#213d80;margin:15px 0;padding:12px;border-radius:15px}
h2{font-size:24px;margin:0 0 9px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
article{background:#305095;border-radius:11px;padding:11px;min-width:0}
.w{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px}
.w strong{font-size:21px}.w span{font-size:11px;color:#d8e4ff}
audio{display:block;width:100%;min-width:0}
.header{background:#1b3674;border-radius:14px;padding:12px}
</style></head><body>
<div class="header"><h1>🎙️ ABC QUEST — כל 156 המילים</h1>
<p>קול 2 הנבחר של ElevenLabs. שישה מילים לכל אות מ־A עד Z.
המילה Zebra משתמשת בהגייה האמריקאית ZEE-bruh שכבר אושרה.</p>
<p>כל ההקלטות נמצאות בתוך דף זה, ולכן אפשר להאזין בטלפון Android גם ללא אינטרנט.</p></div>
'''+''.join(sections)+'''
<script>
document.querySelectorAll('audio').forEach(player => player.addEventListener('play', () => {
 document.querySelectorAll('audio').forEach(other => {
  if (other !== player && !other.paused) other.pause();
 });
}));
</script></body></html>'''
    if page.count("<audio preload")!=156:
        raise RuntimeError("Wrong number of audio players in mobile HTML")
    page_file=out/"LISTEN_ALL_156_WORDS_ON_PHONE.html"
    page_file.write_text(page,encoding="utf-8")
    print(f"Created standalone offline listening HTML with 156 embedded MP3 files ({page_file.stat().st_size:,} bytes)",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--existing",type=Path,required=True)
    p.add_argument("--approved-zebra",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    opts=p.parse_args()
    words=word_bank(opts.archive)
    out=opts.out
    (out/"words").mkdir(parents=True,exist_ok=True)
    key=os.environ.get("ELEVENLABS_API_KEY","").strip()
    if not key:
        raise SystemExit("Missing GitHub secret ELEVENLABS_API_KEY; no new ElevenLabs calls.")
    approved=read_mp3(opts.approved_zebra/"zebra"/"zee-bruh.mp3")
    existing_dir=opts.existing/"words"
    manifest=[]
    generated=0
    reused=0
    repeat_copies=0
    unique_audio_cache={}
    for n,metadata in enumerate(words,1):
        name=metadata["key"]
        target=out/metadata["file"]
        target.parent.mkdir(parents=True,exist_ok=True)
        if name=="zebra":
            target.write_bytes(approved)
            origin="approved_zebra"
            print(f"{n:03d}/156 APPROVED Zebra — ZEE-bruh, no API call",flush=True)
        elif name in unique_audio_cache:
            target.write_bytes(unique_audio_cache[name])
            origin="repeated_word_copy"
            repeat_copies+=1
            print(f"{n:03d}/156 REPEATED {name}, same audio as earlier category",flush=True)
        elif target.exists() and target.stat().st_size>1000:
            read_mp3(target)
            origin="resumed"
            reused+=1
            print(f"{n:03d}/156 KEEP {name} from previous generation",flush=True)
        else:
            source=existing_dir/(name+".mp3")
            if source.is_file():
                target.write_bytes(read_mp3(source))
                origin="reused"
                reused+=1
                print(f"{n:03d}/156 REUSED {name}, no API call",flush=True)
            else:
                audio=request_audio(key,VOICE_ID,metadata["word"],MODEL_ID)
                target.write_bytes(audio)
                read_mp3(target)
                origin="generated"
                generated+=1
                print(f"{n:03d}/156 GENERATED {name}, {len(audio)} bytes",flush=True)
                time.sleep(0.15)
        data=read_mp3(target)
        unique_audio_cache[name]=data
        manifest.append({"letter":metadata["letter"],"key":name,"word":metadata["word"],
                         "file":metadata["file"],"source":origin,"bytes":len(data)})
    files=list((out/"words").rglob("*.mp3"))
    if len(files)!=156 or len(manifest)!=156:
        raise RuntimeError(f"Word bank/audio inventory mismatch: {len(files)} files, {len(manifest)} records")
    for record in manifest:
        read_mp3(out/record["file"])
    (out/"WORD_AUDIO_MANIFEST.json").write_text(json.dumps({
        "game":"ABC QUEST","voice_id":VOICE_ID,"model_id":MODEL_ID,
        "expected_word_count":156,"actual_word_count":len(manifest),
        "word_count_per_letter":6,"approved_zebra":"ZEE-bruh",
        "generated_new":generated,"reused_existing":reused,
        "repeated_word_copies":repeat_copies,"distinct_spoken_words":len(unique_audio_cache),
        "records":manifest,
    },ensure_ascii=False,indent=2),encoding="utf-8")
    make_mobile_listener(out,manifest)
    (out/"README.txt").write_text(
        "ABC QUEST — all 156 words (26 letters x six words) with selected ElevenLabs Voice 2\n"+
        "Voice ID: "+VOICE_ID+"\n"+
        "Open LISTEN_ALL_156_WORDS_ON_PHONE.html on your Android Chrome browser.\n"+
        "All MP3 files are inside the words/ folder for later offline Android APK integration.\n"+
        "Zebra uses APPROVED US ZEE-bruh audio. No new phonics or letter name clips generated.\n"+
        "Source: exact word bank read from Android v7.5 ZIP.\n"+
        f"Reused existing audio: {reused}, newly generated audio: {generated}, repeated words copied: {repeat_copies}, zebra separately reused.\n"+
        "This workflow produces assets only and does not alter the Android app or APK.\n",encoding="utf-8")
    print(f"SUCCESS: 156/156 word placement MP3s, {len(unique_audio_cache)} unique terms, {reused} reused, {generated} generated, {repeat_copies} repeated-word copies, Zebra approved.",flush=True)

if __name__=="__main__":
    main()
