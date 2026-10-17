#!/usr/bin/env python3
"""ABC QUEST: pilot corrected alphabet names, actual phonemes and US zee-bra.

No change to Android app. Uses ElevenLabs TTS only with GitHub Actions secret.
A/B tests 6 letter names and 6 independent speech sounds, plus two US zebra
pronunciation versions, embedded in one local-player HTML file for Android.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import subprocess
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

VOICE_ID = "NoOVOzCQFLOvtsMoNcdT"
# American-English letter names (CMU ARPABET), matched to familiar spelling.
NAME_TESTS = [
    ("A", "EY1"), ("B", "B IY1"), ("C", "S IY1"),
    ("M", "EH1 M"), ("W", "D AH1 B AH0 L Y UW1"), ("Z", "Z IY1"),
]
# First phonics sound normally introduced for each letter (not letter names).
# Stops (/b/, /k/) are transient and should not be extended with a vowel.
SOUND_TESTS = [
    ("A", "æ", "AE1"), ("B", "b", "B"), ("C", "k", "K"),
    ("F", "f", "F"), ("S", "s", "S"), ("Z", "z", "Z"),
]

def tts(api_key: str, spoken: str, model: str, timestamps: bool = False):
    endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    if timestamps: endpoint += "/with-timestamps"
    endpoint += "?output_format=mp3_44100_128"
    payload=json.dumps({
        "text":spoken, "model_id":model,
        "voice_settings":{
            "stability":0.70, "similarity_boost":0.80,
            "style":0.0, "use_speaker_boost":True,
        }
    }).encode()
    req=urllib.request.Request(endpoint,data=payload,method="POST",headers={
        "xi-api-key":api_key,"Content-Type":"application/json",
        "Accept":"application/json" if timestamps else "audio/mpeg",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=100) as response:
                data=response.read()
                if timestamps:
                    record=json.loads(data.decode("utf-8"))
                    content=base64.b64decode(record["audio_base64"])
                    if not content:raise RuntimeError("Missing audio from timestamp response")
                    return content,record.get("alignment") or record.get("normalized_alignment")
                if len(data)<800:raise RuntimeError("Returned audio is too short")
                return data,None
        except urllib.error.HTTPError as exc:
            body=exc.read(500).decode("utf-8",errors="replace")
            if exc.code in (429,500,502,503) and attempt<2:
                print(f"Temporary ElevenLabs HTTP {exc.code}, retrying",flush=True)
                time.sleep((attempt+1)*3)
                continue
            raise RuntimeError(f"ElevenLabs HTTP {exc.code}: {body}") from None
    raise RuntimeError("Unexpected API retry failure")

def crop_last_letter(raw:bytes,alignment:dict,letter:str,folder:Path):
    if not alignment:raise ValueError("Alignment not available")
    ch=alignment.get("characters",[])
    starts=alignment.get("character_start_times_seconds",[])
    ends=alignment.get("character_end_times_seconds",[])
    if not (len(ch)==len(starts)==len(ends)):
        raise ValueError("Alignment arrays differ in length")
    # The final *visible letter* from "The letter is B." is the target.
    idxs=[idx for idx,c in enumerate(ch) if c.upper()==letter]
    if not idxs:raise ValueError("Requested letter absent from alignment")
    i=idxs[-1]
    start=max(0.0,float(starts[i])-0.10)
    end=float(ends[i])+0.28
    if end-start<0.09:raise ValueError("Invalid letter alignment")
    folder.mkdir(exist_ok=True,parents=True)
    original=folder/"context_uncropped.mp3"
    original.write_bytes(raw)
    output=folder/"context_cropped.mp3"
    binary=shutil.which("ffmpeg")
    if not binary:
        import imageio_ffmpeg
        binary=imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([
        binary,"-y","-hide_banner","-loglevel","error",
        "-ss",f"{start:.3f}","-to",f"{end:.3f}",
        "-i",str(original),"-af","afade=t=in:st=0:d=0.018",
        "-codec:a","libmp3lame","-q:a","3",str(output),
    ],check=True,timeout=25)
    data=output.read_bytes()
    if len(data)<700:raise ValueError("Letter crop is unexpectedly short")
    return data,{"start":start,"end":end,"alignment_char":ch[i]}

def embed_mp3(p:Path):
    if not p.is_file() or p.stat().st_size<700:
        raise ValueError(f"Missing/invalid audio: {p}")
    b=p.read_bytes()
    if not (b.startswith(b"ID3") or b[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")):
        raise ValueError(f"Not an MP3: {p}")
    return "data:audio/mpeg;base64,"+base64.b64encode(b).decode("ascii")

def make_page(out,results):
    groups=[
        ("שמות אותיות — השוואת שתי שיטות",
         "שיטה א׳: הגייה מוגדרת ב־CMU. שיטה ב׳: הקרנת האות מתוך משפט טבעי; שתי השיטות ניסיוניות.",
         [(f"{letter} • A",f"names/{letter}/phonetic_cmu.mp3","הגייה מוגדרת")
          for letter,_ in NAME_TESTS]+
         [(f"{letter} • B",f"names/{letter}/context_cropped.mp3","מתוך משפט")
          for letter,_ in NAME_TESTS]),
        ("צלילים פונטיים — לא שמות אותיות",
         "דוגמאות בסימון IPA וב־CMU. במיוחד עבור B ו־C יש לבדוק שלא נשמעת תנועת עזר כמו 'בְּה' או 'קוּ'.",
         [(f"{letter} /{ipa}/ • IPA",f"sounds/{letter}/ipa.mp3","IPA")
          for letter,ipa,_ in SOUND_TESTS]+
         [(f"{letter} /{ipa}/ • CMU",f"sounds/{letter}/cmu.mp3","CMU")
          for letter,ipa,_ in SOUND_TESTS]),
        ("Zebra — הגייה אמריקאית זִי־בְּרָה",
         "שתי הצעות לתיקון ההגייה. המטרה: ZEE-bruh ולא ZEB-ruh.",
         [("Zebra • A","zebra/zee-bruh.mp3","כתיב פונטי"),
          ("Zebra • B","zebra/cmu.mp3","CMU מבוקר")]),
    ]
    blocks=[]
    for title,description,items in groups:
        blocks.append("<section><h2>"+html.escape(title)+"</h2><p>"+html.escape(description)+"</p><div class='grid'>")
        for label,file,note in items:
            path=out/file
            if not path.exists():
                blocks.append("<article><b>"+html.escape(label)+"</b><small>לא הופק בהצלחה</small></article>")
                continue
            blocks.append("<article><b>"+html.escape(label)+"</b><small>"+html.escape(note)+
                "</small><audio controls preload='none' src='"+embed_mp3(path)+"'></audio></article>")
        blocks.append("</div></section>")
    page='''<!DOCTYPE html><html dir="rtl" lang="he"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ABC QUEST — תיקון אותיות וצלילים</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}
body{background:#10235a;color:#fff;font:16px system-ui,Arial,sans-serif;max-width:950px;margin:0 auto;padding:16px}
h1{font-size:28px}h2{font-size:22px}p{line-height:1.55;color:#d8e6ff}
section{margin-top:22px;background:#1b3776;padding:15px;border-radius:17px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:11px}
article{padding:12px;background:#284988;border-radius:12px;display:grid;gap:8px}
b{font-size:19px}small{color:#d0e0ff}audio{width:100%;min-width:0}
.info{background:#384477;border-radius:14px;padding:12px}
</style></head><body><h1>🔊 ABC QUEST — מתקנים את ההגייה</h1>
<p class="info">נגן עצמאי לאנדרואיד: כל ההקלטות מוטמעות בקובץ HTML אחד. אלה ניסויים חדשים בקול 2; עדיין לא החלפנו קבצים באפליקציה.
כדי לאשר איכות, הקשב במיוחד להבחנה בין שם האות B לבין הצליל /b/.</p>
'''+"".join(blocks)+'''<p>בשלב הבא, לאחר האישור, ניצור את כל 26 שמות האותיות ו־26 הצלילים. קבצי המילים שאושרו לא דורשים הפקה חוזרת מלבד Zebra.</p>
<script>document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a&&!b.paused)b.pause()})))</script></body></html>'''
    (out/"LISTEN_FIXED_LETTERS_AND_ZEBRA.html").write_text(page,encoding="utf-8")
    expected=sum(1 for _,_,items in groups for _,f,_ in items if (out/f).exists())
    assert page.count("<audio controls")==expected
    (out/"RESULTS.json").write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding="utf-8")
    (out/"README.txt").write_text(
        "Open LISTEN_FIXED_LETTERS_AND_ZEBRA.html in Chrome on Android. All clips embedded.\n"+
        "Tests phonetic CMU vs contextual letter names, IPA vs CMU sounds, and American zee-bruh. "+
        "These are listening experiments; not the final game audio.\n",encoding="utf-8")
    print(f"Player created: {expected} MP3 recordings; file size={len(page)}",flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    key=os.environ.get("ELEVENLABS_API_KEY","").strip()
    if not key:raise SystemExit("Missing ElevenLabs API secret; no requests made.")
    args.out.mkdir(parents=True,exist_ok=True)
    report=[]
    def generate(name,spoken,model,timestamp=False, letter=None):
        target=args.out/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.stat().st_size>=800:
            report.append({"file":name,"state":"reused","model":model,"prompt":spoken})
            print(f"REUSED {name} (no new API request)",flush=True)
            return
        try:
            audio,alignment=tts(key,spoken,model,timestamp)
            if timestamp and letter:
                audio,meta=crop_last_letter(audio,alignment,letter,target.parent)
            else:meta={}
            target.write_bytes(audio)
            report.append({"file":name,"state":"ok","model":model,"prompt":spoken,**meta})
            print(f"OK {name} ({len(audio)} bytes)",flush=True)
        except Exception as exc:
            report.append({"file":name,"state":"failed","error":str(exc)})
            print(f"Failed {name}: {exc}",flush=True)

    for letter,cmu in NAME_TESTS:
        spoken=f'<phoneme alphabet="cmu-arpabet" ph="{cmu}">{letter}</phoneme>'
        generate(f"names/{letter}/phonetic_cmu.mp3",spoken,"eleven_flash_v2")
        generate(f"names/{letter}/context_cropped.mp3",f"The letter is {letter}.","eleven_multilingual_v2",True,letter)
    for letter,ipa,cmu in SOUND_TESTS:
        generate(f"sounds/{letter}/ipa.mp3",f'<phoneme alphabet="ipa" ph="{ipa}">{letter.lower()}</phoneme>',"eleven_flash_v2")
        generate(f"sounds/{letter}/cmu.mp3",f'<phoneme alphabet="cmu-arpabet" ph="{cmu}">{letter.lower()}</phoneme>',"eleven_flash_v2")
    generate("zebra/zee-bruh.mp3","ZEE-bruh.","eleven_multilingual_v2")
    generate("zebra/cmu.mp3",'<phoneme alphabet="cmu-arpabet" ph="Z IY1 B R AH0">zebra</phoneme>',"eleven_flash_v2")
    make_page(args.out,report)
    n=sum(x["state"] in ("ok","reused") for x in report)
    print(f"Completed {n}/{len(report)} trials; review pronunciation before further generation.",flush=True)
    if n==0:raise SystemExit("No audio produced")

if __name__=="__main__":main()
