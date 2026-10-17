#!/usr/bin/env python3
"""Compare four ElevenLabs voices on exactly the same ABC QUEST speech prompts.

Only runs with an existing GitHub Actions API secret. Generates 15 names/words per
voice and one fully self-contained listening page suitable for Android Chrome.
This preview does not modify the installable Android game.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
from pathlib import Path
import re
import sys
import time

from generate_previews import SAMPLES, request_audio, words_from_android_zip

def is_audio(data: bytes) -> bool:
    return len(data) > 1000 and (
        data.startswith(b"ID3") or
        len(data) >= 2 and data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")
    )

def build_page(out: Path, voices: list[dict], samples: list, statuses: list[dict]):
    cards = []
    for section, filename, spoken in samples:
        recordings=[]
        for voice in voices:
            path=out / voice["key"] / section / (filename + ".mp3")
            if not path.exists():
                recordings.append(
                    '<div class="record"><span>קול '+str(voice["number"])+
                    '</span><em>לא זמין</em></div>')
                continue
            data=path.read_bytes()
            if not is_audio(data):
                raise RuntimeError("Invalid MP3 in " + path.as_posix())
            src="data:audio/mpeg;base64,"+base64.b64encode(data).decode("ascii")
            recordings.append(
                '<div class="record"><label>קול '+str(voice["number"])+'</label>'+
                '<audio controls preload="none" src="'+src+'"></audio></div>'
            )
        kind = 'שם אות' if section == 'names' else 'מילה'
        cards.append(
            '<section class="sample"><h2><span dir="ltr">'+html.escape(filename.capitalize() if section=='words' else filename)+
            '</span><small>'+kind+'</small></h2><div class="players">'+''.join(recordings)+'</div></section>'
        )
    legend=''.join(
        '<div class="legenditem"><b>קול '+str(v["number"])+'</b><code>'+html.escape(v["id"])+'</code></div>'
        for v in voices)
    issues=''.join(
        '<p><b>קול '+str(s["number"])+' לא הושלם:</b> '+html.escape(s["error"])+'</p>'
        for s in statuses if s.get("error"))
    page='''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>ABC QUEST | ארבע קרייניות</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{background:#091c50;color:#fff;font:16px system-ui,Arial,sans-serif;max-width:840px;margin:0 auto;padding:18px}
h1{font-size:clamp(24px,6vw,34px);margin-bottom:9px}
p{color:#dce6ff;line-height:1.55}.intro{background:#193677;border-radius:16px;padding:14px}.legends{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:16px 0}
.legenditem{border:1px solid #5473ac;border-radius:10px;padding:10px;display:grid;gap:5px}
.legenditem code{font-size:11px;overflow-wrap:anywhere;color:#d4e2ff}
.sample{background:#16336f;border:1px solid #365799;padding:15px;margin:15px 0;border-radius:18px}
.sample h2{display:flex;align-items:center;gap:12px;margin:0 0 11px;font-size:25px}
.sample h2 small{font-size:13px;font-weight:400;color:#cbdcff}
.players{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
.record{background:#243f7c;border-radius:10px;padding:10px;display:flex;flex-direction:column;gap:5px}
.record label,.record span{font-weight:700}.record em{color:#f9d5ad;font-size:13px}
audio{width:100%;height:44px;min-width:0}
.note{font-size:13px;color:#c9d9ff}.issues{background:#713426;border-radius:12px;padding:10px}
</style></head><body><h1>🎙️ ABC QUEST — משווים ארבעה קולות</h1>
<div class="intro"><p>כל ארבע הקרייניות מקריאות את אותן 5 אותיות ו־10 מילים באנגלית. השמע מוטמע בקובץ הזה, ולכן הוא עובד בלי תיקיות נלוות גם באנדרואיד.</p>
<p>לכל מילה האזן לארבעת הקולות ובחר מי הכי ברורה, נעימה וטבעית לילדים.</p></div>
<div class="legends">'''+legend+'</div>'
    if issues:
        page+='<div class="issues">'+issues+'</div>'
    page+=''.join(cards)
    page+='''<p class="note">בדיקה זו אינה כוללת 26 צלילים פונטיים. יש לבדוק אותם בנפרד לפני ההטמעה במשחק.</p>
<script>document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>{
document.querySelectorAll('audio').forEach(b=>{if(b!==a&&!b.paused)b.pause()})
}));</script></body></html>'''
    output=out/"COMPARE_4_VOICES_ON_PHONE.html"
    output.write_text(page,encoding="utf-8")
    assert page.count('<audio controls') == sum(
        1 for sec,fname,_ in samples for voice in voices
        if (out / voice["key"] / sec / (fname+".mp3")).exists()
    )
    print(f"Created {output} ({output.stat().st_size:,} bytes)",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--request",type=Path,required=True)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--model-id",default="eleven_multilingual_v2")
    opts=p.parse_args()

    key=os.environ.get("ELEVENLABS_API_KEY","").strip()
    if not key:
        sys.exit("Missing ELEVENLABS_API_KEY secret: no external calls made.")
    settings=json.loads(opts.request.read_text(encoding="utf-8"))
    ids=settings["voice_ids"]
    if not isinstance(ids,list) or len(ids)!=4 or len(set(ids))!=4:
        sys.exit("Exactly four unique voice IDs are required.")
    if any(not isinstance(x,str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,90}",x) for x in ids):
        sys.exit("One of the voice IDs has an invalid format.")
    vocab=words_from_android_zip(opts.archive)
    missing=[f for section,f,_ in SAMPLES if section=="words" and f not in vocab]
    if missing:
        sys.exit("Words missing from game: "+str(missing))
    opts.out.mkdir(parents=True,exist_ok=True)
    voices=[{"number":i+1,"key":"voice_"+str(i+1),"id":ident} for i,ident in enumerate(ids)]
    statuses=[]
    for voice in voices:
        completed=0
        error=None
        print("VOICE "+str(voice["number"])+"/4",flush=True)
        for n,(section,filename,spoken) in enumerate(SAMPLES,1):
            target=opts.out/voice["key"]/section/(filename+".mp3")
            target.parent.mkdir(parents=True,exist_ok=True)
            try:
                audio=request_audio(key,voice["id"],spoken,opts.model_id)
                if not is_audio(audio):
                    raise RuntimeError("Voice provider returned invalid MP3 bytes.")
                target.write_bytes(audio)
                completed+=1
                print(f"  {n:02d}/{len(SAMPLES)} {section}/{filename} - OK ({len(audio)} bytes)",flush=True)
            except Exception as exc:
                error=str(exc)
                # Never dump credential-containing request objects.
                print(f"Voice {voice['number']} stopped at {section}/{filename}: {error}",flush=True)
                break
        statuses.append({"number":voice["number"],"clips":completed,"error":error})
        time.sleep(0.3)
    (opts.out/"RESULTS.json").write_text(json.dumps({
        "model":opts.model_id,"voices":voices,"statuses":statuses,
        "samples_per_voice":len(SAMPLES),
        "note":"No phoneme sounds are included in these tests."
    },ensure_ascii=False,indent=2),encoding="utf-8")
    build_page(opts.out,voices,SAMPLES,statuses)
    print("RESULTS "+json.dumps(statuses,ensure_ascii=False),flush=True)
    if not any(v["clips"] for v in statuses):
        sys.exit("No voice audio was produced, see API error above.")

if __name__=="__main__":
    main()
