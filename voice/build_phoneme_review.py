#!/usr/bin/env python3
"""Build an offline Android listener for all 26 existing game phonemes and
15 approved-voice ElevenLabs samples. No ElevenLabs calls or additional charges.
"""
import argparse
import base64
import html
import json
import re
import zipfile
from pathlib import Path

IPA = {
    "A":"æ","B":"b","C":"k","D":"d","E":"ɛ","F":"f","G":"ɡ","H":"h",
    "I":"ɪ","J":"dʒ","K":"k","L":"l","M":"m","N":"n","O":"ɑ","P":"p",
    "Q":"kw","R":"ɹ","S":"s","T":"t","U":"ʌ","V":"v","W":"w","X":"ks",
    "Y":"j","Z":"z",
}
WORDS = ["apple","ball","cat","dog","elephant","fish","queen","sun","water","zebra"]
NAMES = ["A","B","C","M","Z"]

def mp3_uri(data):
    if not data or not (data.startswith(b"ID3") or data[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")):
        raise RuntimeError("Expected an MP3 recording")
    return "data:audio/mpeg;base64,"+base64.b64encode(data).decode("ascii")

def from_archive(archive):
    with zipfile.ZipFile(archive) as zipf:
        names=[x for x in zipf.namelist() if x.endswith("app/src/main/assets/index.html")]
        if len(names)!=1:raise RuntimeError("Cannot uniquely find current ABC QUEST game HTML")
        code=zipf.read(names[0]).decode("utf-8")
    match=re.search(r"const AUDIO\s*=\s*",code)
    if match is None:raise RuntimeError("AUDIO dictionary missing from game")
    catalog,_=json.JSONDecoder().raw_decode(code[match.end():])
    if set(catalog)!=set(IPA):raise RuntimeError("Expected audio entries for A-Z")
    result={}
    for letter in IPA:
        source=catalog[letter].get("sound")
        if not source or not source.startswith("data:audio/mpeg;base64,"):
            raise RuntimeError("Sound for "+letter+" missing/invalid")
        result[letter]=base64.b64decode(source.split(",",1)[1],validate=True)
        mp3_uri(result[letter])
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",required=True,type=Path)
    parser.add_argument("--voice2",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    audio=from_archive(args.archive)
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    (out/"original_game_phonemes").mkdir(exist_ok=True)
    for letter,data in audio.items():
        (out/"original_game_phonemes"/(letter+".mp3")).write_bytes(data)
    clips=[]
    for kind,ids in (("names",NAMES),("words",WORDS)):
        for key in ids:
            fn=args.voice2/kind/(key+".mp3")
            if not fn.is_file():
                raise RuntimeError("Existing chosen-voice recording missing: "+str(fn))
            data=fn.read_bytes()
            mp3_uri(data)
            clips.append((kind,key,data))
    styles="""<style>:root{color-scheme:dark}*{box-sizing:border-box}body{background:#0b2059;color:white;max-width:800px;margin:auto;padding:20px;font:16px system-ui,Arial}header{background:#1e3d87;border-radius:16px;padding:16px;margin:12px 0}h1{font-size:28px}h2{font-size:24px}p{line-height:1.6;color:#d6e4ff}.samples{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.item{background:#244584;border-radius:12px;padding:12px}.item strong{font-size:24px}.item span{font-size:13px;color:#d9e7ff}audio{display:block;width:100%;margin-top:10px;min-width:0}.section{margin-top:30px}.note{background:#553e24;border-radius:12px;padding:12px}</style>"""
    page=['<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',styles,'<title>ABC QUEST · בדיקת קול וצלילים</title><body>']
    page+=['<header><h1>🎙️ ABC QUEST — קול 2 וצלילי האותיות</h1><p>קול 2 נבחר לקריאת שמות אותיות ומילים. חלק זה כולל את 15 הדוגמאות שכבר הפקנו איתו.</p><p>בנפרד מופיעים 26 הצלילים <b>הקיימים כעת במשחק</b>, כדי לבדוק אם יש להחליפם. הם אינם הקלטות חדשות של ElevenLabs.</p></header>']
    for kind,title in (("names","שמות אותיות — קול 2 (ElevenLabs)"),("words","מילים — קול 2 (ElevenLabs)")):
        page += ['<div class="section"><h2>'+title+'</h2><div class="samples">']
        for group,key,data in clips:
            if group!=kind:continue
            label=key.upper() if group=="names" else key.capitalize()
            page+=['<div class="item"><strong dir="ltr">'+html.escape(label)+'</strong><audio controls preload="none" src="'+mp3_uri(data)+'"></audio></div>']
        page+=['</div></div>']
    page+=['<div class="section"><h2>26 צלילי אותיות — הקבצים הקיימים באפליקציה</h2><p>כאן משווים דיוק וטבעיות. אלו צלילים ולא שמות אותיות. אותיות כמו C, G, Q ו־X יכולות להיות בעלות יותר מצליל אחד; ההצעות בסימון IPA הן צלילים נפוצים להוראה ראשונית.</p><div class="samples">']
    for letter,data in audio.items():
        page+=['<div class="item"><strong>'+letter+'</strong><span dir="ltr"> /'+IPA[letter]+'/ </span><audio controls preload="none" src="'+mp3_uri(data)+'"></audio></div>']
    page+=['</div></div><div class="section note"><b>חשוב:</b> בצלילים כמו /b/, /d/, /k/ ו־/p/ אי אפשר לשמר את הצליל לאורך זמן בלי להוסיף תנועה מלאכותית. בבדיקת האיכות יש להעדיף צליל קצר ומדויק על פני הברה כמו “בּוּ”.</div>']
    page+=['<script>document.querySelectorAll("audio").forEach(a=>a.addEventListener("play",()=>document.querySelectorAll("audio").forEach(b=>{if(b!==a&&!b.paused)b.pause()})))</script></body></html>']
    text="".join(page)
    (out/"LISTEN_VOICE2_AND_26_SOUNDS.html").write_text(text,encoding="utf-8")
    count=text.count("<audio controls")
    assert count==41,count
    (out/"README.txt").write_text("Open LISTEN_VOICE2_AND_26_SOUNDS.html in Chrome on Android. Contains 15 chosen ElevenLabs Voice 2 clips plus 26 *existing* phoneme clips from the current game. No new API generation, no API credits. Review educational phonemes before final 208-audio pack.\n",encoding="utf-8")
    print(f"Ready: {count} embedded MP3 samples; 26 original game phonemes; 15 chosen voice recordings. HTML length={len(text)}")

if __name__=="__main__":main()
