#!/usr/bin/env python3
"""Refine ABC QUEST phonics after user feedback, without any ElevenLabs API use.

For E,I,K,L,N,S,U,V,Y: create two shortened cuts directly from the original
spoken words. For X: extract two later portions of Fox to isolate word-final /ks/,
instead of the vowel-containing earlier segment. Keep previously preferred
short cuts for the remaining 16 letters. Do NOT install unapproved audio.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import shutil
from pathlib import Path

from extract_phonemes_from_words import (
    LETTERS, active_bounds, crop_mp3, samples, valid_mp3
)

# Explicit duration offsets in seconds from detected speech onset.
# The A cut is gentler; B is shorter. They are tests, not certified phonemes.
TUNING = {
    "E": (0.115, 0.155),
    "I": (0.105, 0.145),
    "K": (0.085, 0.115),
    "L": (0.100, 0.135),
    "N": (0.095, 0.130),
    "S": (0.105, 0.145),
    "U": (0.125, 0.165),
    "V": (0.100, 0.140),
    "Y": (0.105, 0.145),
}

def audio_uri(path:Path):
    data=path.read_bytes()
    if not valid_mp3(data):
        raise RuntimeError("Invalid MP3: "+str(path))
    return "data:audio/mpeg;base64,"+base64.b64encode(data).decode("ascii")

def as_player(title,path):
    return ("<div class='player'><small>"+html.escape(title)+"</small>"
        "<audio controls preload='none' src='"+audio_uri(path)+"'></audio></div>")

def render(out:Path,records:list):
    edited=[]
    others=[]
    for letter,word,ipa,kind in LETTERS:
        source=out/"words"/(word+".mp3")
        old=out/"previous_short"/(letter+".mp3")
        blocks=[as_player("מילת המקור: "+word.capitalize(),source),
                as_player("הגרסה הקצרה הקודמת",old)]
        if letter in TUNING or letter=="X":
            blocks.extend([
                as_player("תיקון A — חיתוך עדין",out/"adjusted"/(letter+"_A.mp3")),
                as_player("תיקון B — חיתוך קצר יותר",out/"adjusted"/(letter+"_B.mp3")),
            ])
            group=edited
        else:
            # For unflagged letters use the original short recording as requested.
            blocks=[as_player("הגרסה הקצרה הקודמת",old)]
            group=others
        group.append("<section><div class='title'><b>"+letter+"</b><span dir='ltr'>/"
            +html.escape(ipa)+"/</span><span>"+html.escape(word.capitalize())
            +"</span></div><div class='clips'>"+''.join(blocks)+"</div></section>")
    page='''<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ABC QUEST — תיקון החיתוכים לפי ההערות שלך</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{font:15px system-ui,Arial,sans-serif;background:#0d205b;color:#fff;max-width:950px;margin:0 auto;padding:16px}
h1{font-size:27px}h2{font-size:22px}p{color:#d8e7ff;line-height:1.55}
.notice{background:#32487d;border-radius:12px;padding:12px}
section{background:#1e3d80;border-radius:15px;padding:13px;margin:12px 0}
.title{display:flex;gap:12px;align-items:center}.title b{font-size:29px}
.title span{font-size:16px}
.clips{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:9px;margin-top:10px}
.player{background:#315394;border-radius:10px;padding:10px}
small{display:block;color:#d4e3ff;margin-bottom:8px}
audio{width:100%;min-width:0}
</style><body>
<h1>🔊 ABC QUEST — חיתוכים מתוקנים</h1>
<p>עדכון לפי ההאזנה שלך: תשע אותיות קוצרו מחדש והאות X נחתכה שוב <b>מסוף</b> Fox.
לכל אות מתוקנת מוצגים המקור, הגרסה הקודמת ושני חיתוכים חדשים.</p>
<div class="notice">הצלילים עדיין דורשים אישור בהאזנה. קצר מדי עלול למחוק את העיצור;
ארוך מדי עלול להשאיר תנועה נוספת. בהקלטות של X ייתכן שיידרש מקור נוסף
כדי לבודד את /ks/ בלי שארית התנועה של Fox.</div>
<h2>10 אותיות לתיקון</h2>'''+''.join(edited)+'''
<h2>16 אותיות ללא שינוי — החיתוך הקצר שבחרת</h2>'''+''.join(others)+'''
<p>אין חיוב חדש ואין קריאות ל־ElevenLabs בתהליך הזה. לא שונו קובצי המשחק.</p>
<script>document.querySelectorAll("audio").forEach(a=>a.addEventListener("play",()=>{
document.querySelectorAll("audio").forEach(b=>{if(b!==a&&!b.paused)b.pause()})}))</script></body></html>'''
    output=out/"LISTEN_REFINED_10_LETTERS.html"
    output.write_text(page,encoding="utf-8")
    assert page.count("<audio controls")==10*4+16
    print(f"PLAYER: {output}, {output.stat().st_size} bytes, {10*4+16} audio elements",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    inp,out=args.input,args.output
    for directory in ("words","previous_short","adjusted","recommended"):
        (out/directory).mkdir(parents=True,exist_ok=True)
    report=[]
    for letter,word,ipa,kind in LETTERS:
        src=inp/"words"/(word+".mp3")
        former=inp/"sounds"/(letter+"_short.mp3")
        if not src.is_file() or not former.is_file():
            raise RuntimeError("Prior recording missing: "+letter)
        shutil.copyfile(src,out/"words"/(word+".mp3"))
        shutil.copyfile(former,out/"previous_short"/(letter+".mp3"))
        if not valid_mp3(former.read_bytes()):
            raise RuntimeError("Invalid former short clip "+letter)
        rec={"letter":letter,"word":word,"ipa":ipa,"former":"previous_short/"+letter+".mp3",
             "review_required":letter in TUNING or letter=="X"}
        if letter in TUNING or letter=="X":
            arr=samples(src)
            start,end,peak=active_bounds(arr)
            duration=len(arr)/16000
            if letter=="X":
                # Previous X crop: start~0.155 s, included the vowel of Fox.
                # These windows are anchored to the END of speech and moved later.
                # Ensure they stay in the final 0.19/0.13s, respectively.
                stop=min(duration,end+0.035)
                a=max(start,stop-0.175)
                b=max(start,stop-0.125)
                windows={"A":(a,stop),"B":(b,stop)}
                if a < max(0,start+0.10):
                    raise RuntimeError("X extraction too close to speech onset")
            else:
                a,b=TUNING[letter]
                begin=max(0,start-0.016)
                windows={"A":(begin,min(duration,begin+a)),
                         "B":(begin,min(duration,begin+b))}
            for variant,(s,e) in windows.items():
                target=out/"adjusted"/(letter+"_"+variant+".mp3")
                crop_mp3(src,target,s,e)
                rec["cut_"+variant]={"start_s":round(s,3),"end_s":round(e,3),
                    "seconds":round(e-s,3),"path":f"adjusted/{letter}_{variant}.mp3"}
                print(f"{letter} {variant}: {s:.3f}–{e:.3f} sec, from {word}",flush=True)
            # Recommended draft uses conservative adjusted A; both require user review.
            chosen=out/"adjusted"/(letter+"_A.mp3")
        else:
            chosen=out/"previous_short"/(letter+".mp3")
        shutil.copyfile(chosen,out/"recommended"/(letter+".mp3"))
        rec["recommended_for_review"]="recommended/"+letter+".mp3"
        report.append(rec)
    count=len(list((out/"recommended").glob("*.mp3")))
    if count!=26:raise RuntimeError(f"Expected 26 recommended clips, got {count}")
    render(out,report)
    (out/"REFINEMENT_DETAILS.json").write_text(json.dumps({
        "user_choice":"Previously short crop preferred; E,I,K,L,N,S,U,V,Y too long; X wrong segment",
        "source":"Existing ABC QUEST voice 2 natural-word MP3 recordings",
        "generated_from_elevenlabs":False,
        "caution":"Preview phoneme fragments are not approved for the educational app until listened to",
        "letters":report,
    },indent=2,ensure_ascii=False),encoding="utf-8")
    (out/"README_PHONE.txt").write_text(
        "ANDROID: extract the ZIP and open LISTEN_REFINED_10_LETTERS.html with Chrome.\n"
        "10 letters: E I K L N S U V X Y, each shows old short + two new options.\n"
        "16 other letters keep the previously preferred short clip.\n"
        "52? No. 20 new crop files (2 per corrected letter) + 26 recommended draft files.\n"
        "No ElevenLabs API calls. Not installed in the Android game.\n",encoding="utf-8")
    print("DONE: 10 letters x 2 new clips, 26 draft clips, standalone player. 0 new API credits.",flush=True)

if __name__=="__main__":
    main()
