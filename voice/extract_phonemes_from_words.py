#!/usr/bin/env python3
"""ABC QUEST — recover introductory phonics sounds from natural word recordings.

Use GOOD spoken words in selected ElevenLabs Voice 2.  For 10 letters reuse
existing MP3s; for 16 missing source words use the *existing* ElevenLabs API
subscription (not a new purchase). Isolate word-onset consonants/vowels and
word-final /ks/ for X with two crop durations per letter.
This is a PREVIEW ONLY. Such automatic trimming is not a verified phoneme
transcription: plosive consonants and glides require human review.
"""
from __future__ import annotations

import argparse
from array import array
import base64
import html
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

import imageio_ffmpeg

from generate_previews import request_audio, words_from_android_zip

VOICE_ID = "NoOVOzCQFLOvtsMoNcdT"
# The first common phonics sound associated with each letter.
# The source words below are ALL in the actual ABC QUEST 7.5 word bank.
# The X /ks/ example is at the end of FOX rather than word-initial.
LETTERS = [
    ("A","apple","æ","vowel"),
    ("B","ball","b","stop"),
    ("C","cat","k","stop"),
    ("D","dog","d","stop"),
    ("E","elephant","ɛ","vowel"),
    ("F","fish","f","fricative"),
    ("G","goat","ɡ","stop"),
    ("H","hat","h","fricative"),
    ("I","insect","ɪ","vowel"),
    ("J","juice","dʒ","affricate"),
    ("K","kite","k","stop"),
    ("L","lion","l","liquid"),
    ("M","moon","m","nasal"),
    ("N","nest","n","nasal"),
    ("O","octopus","ɑ","vowel"),
    ("P","pig","p","stop"),
    ("Q","queen","kw","cluster"),
    ("R","rabbit","ɹ","liquid"),
    ("S","sun","s","fricative"),
    ("T","tiger","t","stop"),
    ("U","umbrella","ʌ","vowel"),
    ("V","van","v","fricative"),
    ("W","water","w","liquid"),
    ("X","fox","ks","final"),
    ("Y","yellow","j","liquid"),
    ("Z","zebra","z","fricative"),
]
# Ear-review choices, not promised precise IPA isolations.
WINDOWS = {
    "stop":(0.13,0.25),
    "fricative":(0.19,0.34),
    "vowel":(0.21,0.36),
    "affricate":(0.17,0.30),
    "nasal":(0.18,0.34),
    "liquid":(0.16,0.30),
    "cluster":(0.21,0.38),
    "final":(0.23,0.38),
}
def valid_mp3(data):
    return len(data)>1000 and (
        data.startswith(b"ID3") or data[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")
    )

def ffmpeg_binary():
    return imageio_ffmpeg.get_ffmpeg_exe()

def ffmpeg(arguments,stdin=None):
    call=[ffmpeg_binary(),"-hide_banner","-loglevel","error",*arguments]
    proc=subprocess.run(call,input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=35)
    if proc.returncode:
        raise RuntimeError("Audio processing failed: "+proc.stderr.decode("utf-8","replace")[:250])
    return proc.stdout

def samples(mp3_path):
    raw=ffmpeg(["-i",str(mp3_path),"-ac","1","-ar","16000","-f","s16le","pipe:1"])
    ints=array("h")
    ints.frombytes(raw)
    if sys.byteorder!="little":
        ints.byteswap()
    if len(ints)<1600:
        raise RuntimeError("Too little decoded audio")
    return ints

def active_bounds(ints):
    # Detect silence by short-time RMS at 10 ms. Adapt to each voice recording.
    rate=16000
    span=160
    rms=[]
    for n in range(0,len(ints)-span,span):
        seg=ints[n:n+span]
        rms.append(math.sqrt(sum(int(v)*int(v) for v in seg)/len(seg)))
    peak=max(rms)
    threshold=max(140,peak*0.085)
    active=[i for i,v in enumerate(rms) if v>threshold]
    if not active: raise RuntimeError("Sound activity not detected")
    start=max(0,(active[0]-3)*0.01)
    end=min(len(ints)/rate,(active[-1]+4)*0.01)
    if end-start<0.12:raise RuntimeError("Source word unexpectedly short")
    return start,end,peak

def crop_mp3(source,output,start,end,boost=0):
    if end-start<=0.065: raise RuntimeError("Too short a phoneme fragment")
    total=end-start
    # Tiny fades reduce clicks without erasing the consonant attack.
    fade_end=max(0,total-0.025)
    filters=f"afade=t=in:st=0:d=0.006,afade=t=out:st={fade_end:.3f}:d=0.024"
    ffmpeg([
        "-ss",f"{start:.4f}","-to",f"{end:.4f}",
        "-i",str(source),"-af",filters,
        "-codec:a","libmp3lame","-q:a","3","-y",str(output)
    ])
    if not valid_mp3(output.read_bytes()):
        raise RuntimeError(f"Clip is not an MP3: {output}")

def embed(path):
    data=path.read_bytes()
    if not valid_mp3(data): raise RuntimeError("Bad MP3: "+str(path))
    return "data:audio/mpeg;base64,"+base64.b64encode(data).decode("ascii")

def html_page(dest,rows):
    blocks=[]
    for item in rows:
        letter=item["letter"]
        word=item["word"]
        ipa=item["ipa"]
        rows_html=[]
        for label,filename in (
            ("מקור: "+word,"words/"+word+".mp3"),
            ("חיתוך קצר","sounds/"+letter+"_short.mp3"),
            ("חיתוך ארוך","sounds/"+letter+"_long.mp3")
        ):
            rows_html.append(
                "<div class='player'><small>"+html.escape(label)+"</small>"+
                "<audio controls preload='none' src='"+embed(dest/filename)+"'></audio></div>"
            )
        blocks.append(
            "<section><div class='head'><b>"+html.escape(letter)+"</b><span dir='ltr'>/"
            +html.escape(ipa)+"/</span><span>"+html.escape(word.capitalize())+
            "</span></div><div class='clips'>"+''.join(rows_html)+"</div></section>"
        )
    page='''<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ABC QUEST — חילוץ צלילי אותיות מתוך מילים</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{font:15px system-ui,Arial,sans-serif;background:#112460;color:#fff;max-width:930px;margin:0 auto;padding:16px}
h1{font-size:29px}p{line-height:1.5;color:#d8e6ff}
.notice{background:#435073;border-radius:13px;padding:13px}
section{background:#213e82;border-radius:16px;padding:14px;margin:13px 0}
.head{display:flex;gap:16px;align-items:center}.head b{font-size:29px}.head span{font-size:18px}
.clips{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:9px;margin-top:10px}
.player{background:#315295;border-radius:11px;padding:9px}.player small{display:block;color:#d3e4ff;margin-bottom:7px}
audio{width:100%;min-width:0}
</style><body><h1>🔊 ABC QUEST — צלילים מתוך מילים</h1>
<p>26 אותיות · לכל אות מילה מקורית ושתי אפשרויות חיתוך, קצרה וארוכה.
כל המילים מוקראות בקול 2 שכבר אישרת.</p>
<div class="notice"><strong>ניסוי לימודי בלבד:</strong> זו הפרדה אוטומטית לפי תחילת המילה, ולא זיהוי פונטי מדויק.
אם צליל נשמע כמו הברה עם תנועת עזר, או שההתחלה שלו קטועה, אין להשתמש בו ללימוד.
במיוחד B, C, D, G, J, K, P, Q, T ו־X ידרשו ביקורת. באות X הצליל נחתך מסוף Fox.</div>
'''+"".join(blocks)+'''
<p>כדי לבחור, הקשב קודם למילת המקור, ואז לחץ על החיתוך הקצר והארוך.
אפשר לדווח לי אילו אותיות טובות ואילו דורשות חיתוך ידני משופר.</p>
<script>document.querySelectorAll("audio").forEach(a=>a.addEventListener("play",()=>document.querySelectorAll("audio").forEach(b=>{if(b!==a&&!b.paused)b.pause()})))</script></body></html>'''
    fn=dest/"LISTEN_26_EXTRACTED_PHONEMES.html"
    fn.write_text(page,encoding="utf-8")
    assert page.count("<audio controls")==26*3
    print("Built HTML audio player:",fn,fn.stat().st_size,"bytes",flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--archive",type=Path,required=True)
    ap.add_argument("--existing",type=Path,required=True)
    ap.add_argument("--approved",type=Path,required=True)
    ap.add_argument("--dest",type=Path,required=True)
    ap.add_argument("--model",default="eleven_multilingual_v2")
    args=ap.parse_args()
    vocabulary=words_from_android_zip(args.archive)
    missing=[word for _,word,_,_ in LETTERS if word not in vocabulary]
    if missing: raise RuntimeError("Not in actual game word bank: "+str(missing))
    dest=args.dest
    for name in ("words","sounds"):
        (dest/name).mkdir(parents=True,exist_ok=True)
    api_key=os.environ.get("ELEVENLABS_API_KEY","").strip()
    reusable=0
    generated=0
    words_needed={}
    for letter,word,ipa,kind in LETTERS:
        words_needed.setdefault(word,[]).append(letter)
        target=dest/"words"/(word+".mp3")
        if target.exists() and valid_mp3(target.read_bytes()):
            continue
        if word=="zebra":
            source=args.approved/"zebra"/"zee-bruh.mp3"
        else:
            source=args.existing/"voice_2"/"words"/(word+".mp3")
        if source.exists():
            data=source.read_bytes()
            if not valid_mp3(data): raise RuntimeError(f"Bad original audio {source}")
            target.write_bytes(data)
            print(f"REUSED {word} (no API call)",flush=True)
            reusable+=1
        else:
            if not api_key: raise RuntimeError(f"API secret required to record missing word {word}")
            data=request_audio(api_key,VOICE_ID,word,args.model)
            if not valid_mp3(data): raise RuntimeError(f"Unexpected audio for {word}")
            target.write_bytes(data)
            generated+=1
            print(f"RECORDED {word} using current subscription",flush=True)
            time.sleep(0.2)
    records=[]
    for letter,word,ipa,kind in LETTERS:
        source=dest/"words"/(word+".mp3")
        samples_arr=samples(source)
        first,last,peak=active_bounds(samples_arr)
        full_duration=len(samples_arr)/16000
        short,long=WINDOWS[kind]
        for label,window in (("short",short),("long",long)):
            if kind=="final":
                # Take only the terminal /ks/ sequence of FOX, never its initial F.
                end=min(full_duration,last+0.035)
                start=max(first,end-window)
            else:
                start=max(0,first-0.016)
                end=min(full_duration,last+0.025,start+window)
            if end-start<0.07:raise RuntimeError(f"{letter}: cannot make {label} clip")
            target=dest/"sounds"/(letter+"_"+label+".mp3")
            crop_mp3(source,target,start,end)
            print(f"CROP {letter} {label}: {start:.3f}s–{end:.3f}s from {word}",flush=True)
        records.append({"letter":letter,"word":word,"ipa":ipa,"kind":kind,
                        "duration_s":round(full_duration,3),"source_start_s":round(first,3),
                        "source_end_s":round(last,3)})
    html_page(dest,records)
    (dest/"CUT_DETAILS.json").write_text(json.dumps({
        "voice_id":VOICE_ID,
        "reused_existing_word_mp3_count":reusable,
        "new_word_mp3_count":generated,
        "phoneme_approximations":records,
        "warning":"Automatically extracted fragments. Human review required."
    },indent=2,ensure_ascii=False),encoding="utf-8")
    (dest/"README.txt").write_text(
        "Open LISTEN_26_EXTRACTED_PHONEMES.html in Chrome on Android.\n"+
        "All 26 word recordings and 52 phoneme approximations are embedded in one file.\n"+
        "Each sound has 2 cuts, short and long. THESE ARE UNREVIEWED and NOT installed in ABC QUEST.\n"+
        "Letter X /ks/ is extracted from the end of FOX.\n"+
        "Generated words may consume existing ElevenLabs subscription credits; no new purchases were made.\n",encoding="utf-8")
    print(f"FINISHED: 26 letters; {reusable} reused words; {generated} generated words; 52 crops.",flush=True)

if __name__=="__main__":
    main()
