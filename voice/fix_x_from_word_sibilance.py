#!/usr/bin/env python3
"""User-approved 25 ABC QUEST phonemes + X rescue with /ks/ from full words.

No new purchase; reuses the approved Round 2 sound files and existing Fox MP3,
then makes three short natural speech samples using the existing ElevenLabs
subscription. Extracts /ks/ by locating the /s/ frication spectrally and
including a short lead-in for /k/. Listen before deciding the final X sound.
"""
from __future__ import annotations
import argparse
import base64
import html
import json
import os
from pathlib import Path
import shutil
import numpy as np

from extract_phonemes_from_words import crop_mp3, samples, active_bounds, valid_mp3
from generate_previews import request_audio

VOICE_ID = "NoOVOzCQFLOvtsMoNcdT"
SOURCE_WORDS = [("fox","Fox (מקור קודם)"),("box","Box"),("six","Six"),("x-ray","X-ray")]
# In ordinary American-English phonics X /ks/ occurs word-final / medial.
# X-ray starts /ɛks/, Xylophone /z/; no regular word-initial /ks/ source.
BASE_SR=16000

def spectrum_s_boundaries(audio:np.ndarray,kind:str):
    """Find the final high-frequency /s/ frication in a spoken word.
    Estimate using log-energy, spectral flatness/3-8kHz power and zero-crossings.
    Time windows returned are approximate, never a pedagogical guarantee.
    """
    a=audio.astype(np.float64)/32768
    frame=320; step=80
    win=np.hanning(frame)
    freqs=np.fft.rfftfreq(frame,d=1/BASE_SR)
    vals=[]
    for i in range(0,len(a)-frame,step):
        wave=a[i:i+frame]
        rms=np.sqrt(np.mean(wave*wave))
        centered=wave-np.mean(wave)
        power=np.abs(np.fft.rfft(centered*win))**2
        hi=power[freqs>=3100].sum()
        total=power[freqs>=450].sum()+1e-12
        hfr=float(hi/total)
        zcr=np.count_nonzero(np.signbit(wave[1:])!=np.signbit(wave[:-1]))/(frame-1)
        vals.append((i/BASE_SR,rms,hfr,zcr))
    if not vals:raise RuntimeError("No time-frequency frames for X")
    peak=max(t[1] for t in vals)
    active=[t for t in vals if t[1]>=max(0.002,peak*0.07)]
    if not active:raise RuntimeError("No active voice")
    first=active[0][0]
    last=active[-1][0]+frame/BASE_SR
    # The /s/ sound should be high in spectral noise at end of fox/box/six
    # or middle of X-ray, preceded by /k/.
    candidates=[]
    for i,(time,rms,hfr,zcr) in enumerate(vals):
        if time<first+0.06 or time>last-0.005:continue
        if rms>=max(0.0012,peak*0.055) and (
            hfr>=0.43 or (hfr>=0.30 and zcr>=0.21)
        ):
            candidates.append((i,time,hfr,zcr))
    # Join neighboring candidate frames when separated by <= 25 ms.
    runs=[]
    for idx,t,_,_ in candidates:
        if not runs or idx-runs[-1][-1][0]>5:
            runs.append([(idx,t)])
        else:runs[-1].append((idx,t))
    qualified=[]
    for group in runs:
        start=group[0][1]
        end=group[-1][1]+frame/BASE_SR
        if end-start>=0.025 and len(group)>=3:
            qualified.append((start,end,len(group)))
    # Prefer the last /s/ interval; for X-ray, avoids the later /r/ vowel.
    # Filter spurious sentence-tail hiss: must be in the spoken range.
    if qualified:
        q=max(qualified,key=lambda x:x[0])
        return {
            "speech_start_s":round(first,3),"speech_end_s":round(last,3),
            "s_start_s":round(q[0],3),"s_end_s":round(q[1],3),
            "s_confidence":"spectral_candidate",
            "other_candidates":qualified,
        }
    # Fallback: likely /s/ in the last 0.14s for fox/box/six; do NOT
    # pretend it is a validated phoneme boundary.
    if kind=="x-ray":
        raise RuntimeError("Cannot automatically find /s/ in X-ray")
    sstart=max(first+0.10,last-0.14)
    return {
        "speech_start_s":round(first,3),"speech_end_s":round(last,3),
        "s_start_s":round(sstart,3),"s_end_s":round(last,3),
        "s_confidence":"fallback_last_140ms","other_candidates":[],
    }

def b64_audio(path):
    data=path.read_bytes()
    if not valid_mp3(data):raise RuntimeError("Broken audio: "+str(path))
    return "data:audio/mpeg;base64,"+base64.b64encode(data).decode("ascii")

def player(path,label):
    if not path.exists():
        return "<div class='player'><span>"+html.escape(label)+" — לא זמין</span></div>"
    return ("<div class='player'><strong>"+html.escape(label)+"</strong>"
            "<audio controls preload='none' src='"+b64_audio(path)+"'></audio></div>")

def create_page(out,rows):
    cards=[]
    for row in rows:
        word=row["source"]
        cards.append(
            "<section><h2>"+html.escape(row["title"])+"</h2>"
            "<p>שתי גרסאות שמבודדות את /ks/ סביב שריקת ה־/s/, עם אורך שונה של /k/ לפניה.</p>"
            "<div class='grid'>"+
            player(out/"words"/(word+".mp3"),"המילה המלאה")+
            player(out/"candidates"/(word+"_A.mp3"),"אפשרות A — יותר מהעיצור /k/")+
            player(out/"candidates"/(word+"_B.mp3"),"אפשרות B — חיתוך ממוקד יותר")+
            "</div><small>ניתוח: "+html.escape(row.get("detection","not available"))+"</small></section>"
        )
    head='''<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ABC QUEST — מתקנים רק את X</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{font:16px system-ui,Arial,sans-serif;background:#102660;color:#fff;max-width:900px;margin:0 auto;padding:17px}
h1{font-size:30px}h2{font-size:22px}p{color:#dbe5ff;line-height:1.55}
section{background:#213d7e;border-radius:15px;padding:15px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}
.player{background:#315395;padding:10px;border-radius:10px;display:grid;gap:8px}
.player strong{font-size:14px}audio{width:100%;min-width:0}small{color:#d7e7ff}
.notice{background:#434b6e;border-radius:12px;padding:12px}
</style><body><h1>🔊 ABC QUEST — צליל X בלבד</h1>
<div class="notice">שאר <b>25 הצלילים נשמרו כפי שאישרת</b>, כולל חיתוך A לתשע האותיות.
הצליל הרצוי של X הוא /ks/ (כמו סוף Box). X-ray מתחילה /ɛks/ ולא /ks/ טהור,
ולכן אנחנו מנסים גם את ההקלטה הזו ובוחנים חיתוכים שונים.
שום קובץ חדש עדיין לא הוטמע במשחק.</div>
'''
    tail='''<p>לאחר ההאזנה, ציין את שם המילה ואת האפשרות הטובה (A או B).
אם אף אחת לא טובה, נמשיך לעריכה נקודתית נוספת.</p>
<script>document.querySelectorAll("audio").forEach(a=>a.addEventListener("play",()=>document.querySelectorAll("audio").forEach(b=>{if(b!==a&&!b.paused)b.pause()})))</script>
</body></html>'''
    page=head+"".join(cards)+tail
    target=out/"LISTEN_X_FROM_BOX_SIX_FOX_XRAY.html"
    target.write_text(page,encoding="utf-8")
    n=sum(1 for r in rows for p in (
        out/"words"/(r["source"]+".mp3"),
        out/"candidates"/(r["source"]+"_A.mp3"),
        out/"candidates"/(r["source"]+"_B.mp3")) if p.exists())
    assert page.count("<audio controls")==n
    print(f"Generated standalone Android player with {n} audio tracks ({len(page)} chars)",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    for sub in ("words","candidates","approved_25"):
        (args.out/sub).mkdir(parents=True,exist_ok=True)

    # The user approved all 25 other letters in the previous gentle-short-cut.
    # Preserve them byte-for-byte, no speech API or sound recomputation.
    imported=[]
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWYZ":
        original=args.approved/"recommended"/(ch+".mp3")
        data=original.read_bytes()
        if not valid_mp3(data):raise RuntimeError("Invalid approved "+ch)
        shutil.copyfile(original,args.out/"approved_25"/(ch+".mp3"))
        imported.append(ch)
    assert len(imported)==25 and "X" not in imported
    fox=args.approved/"words"/"fox.mp3"
    if not fox.is_file():raise RuntimeError("Previous Fox recording unavailable")
    shutil.copyfile(fox,args.out/"words"/"fox.mp3")

    key=os.environ.get("ELEVENLABS_API_KEY","").strip()
    if not key:raise RuntimeError("Missing existing API secret. Do not post key to chat.")
    rows=[]
    for word,title in SOURCE_WORDS:
        filename=args.out/"words"/(word+".mp3")
        if word!="fox" and not filename.exists():
            # Tiny words; uses credits already in ElevenLabs Starter.
            audio=request_audio(key,VOICE_ID,"X-ray" if word=="x-ray" else word,"eleven_multilingual_v2")
            if not valid_mp3(audio):raise RuntimeError("Non-MP3 ElevenLabs response")
            filename.write_bytes(audio)
            print(f"Recorded source word: {word}",flush=True)
        pcm=np.array(samples(filename))
        detection=spectrum_s_boundaries(pcm,word)
        s_start=detection["s_start_s"]; s_end=detection["s_end_s"]
        # Distinguish /k+s/: include short /k/ closure and release preceding /s/.
        # Avoid extending the previous vowel (the issue with original FOX).
        cut_end=min(len(pcm)/BASE_SR, s_end+0.012)
        cut_a=max(0,s_start-0.082)
        cut_b=max(0,s_start-0.048)
        for tag,cut_start in (("A",cut_a),("B",cut_b)):
            if cut_end-cut_start<0.065:cut_start=cut_end-0.068
            target=args.out/"candidates"/(word+"_"+tag+".mp3")
            crop_mp3(filename,target,max(0,cut_start),cut_end)
            print(f"X via {word} [{tag}]: {cut_start:.3f} to {cut_end:.3f}, /s/ at {s_start:.3f}-{s_end:.3f}, {detection['s_confidence']}",flush=True)
        rows.append({"source":word,"title":title,"detection":detection["s_confidence"],
                     "s_start":s_start,"s_end":s_end})
    assert len(list((args.out/"approved_25").glob("*.mp3")))==25
    assert len(list((args.out/"candidates").glob("*.mp3")))==8
    create_page(args.out,rows)
    (args.out/"ANALYSIS.json").write_text(json.dumps({
        "approved_letters":imported,"provisional_letter":"X","test_sources":rows,
        "warning":"X extractions are candidate approximations and require listening.",
        "method":"Locate /s/ frication using FFT energy and cut a short preceding /k/ lead-in",
    },ensure_ascii=False,indent=2),encoding="utf-8")
    (args.out/"README.txt").write_text(
        "Open LISTEN_X_FROM_BOX_SIX_FOX_XRAY.html in Chrome on Android.\n"
        "All 25 other letter phonemes are copied to approved_25 without changes.\n"
        "Try X from BOX, SIX, FOX and X-RAY. Each has candidate A and B.\n"
        "No new purchase. 3 new short words are generated using the existing ElevenLabs subscription.\n"
        "These X sounds require human pronunciation approval, NOT automatically installed.\n",encoding="utf-8")
    print("DONE — 25 user-approved files preserved, 8 X candidate clips created, one standalone player.",flush=True)

if __name__=="__main__":
    main()
