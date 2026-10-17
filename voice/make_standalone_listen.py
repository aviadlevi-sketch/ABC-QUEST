#!/usr/bin/env python3
"""Create a self-contained HTML audio player for Android file viewers.
Reads the previously generated ElevenLabs MP3 artifact. No provider API calls.
"""
from __future__ import annotations
import base64
import html
import json
import pathlib
import sys
import zipfile

CUES = [
    ("names","A","A"),("names","B","B"),("names","C","C"),
    ("names","M","M"),("names","Z","Z"),
    ("words","apple","Apple"),("words","ball","Ball"),
    ("words","cat","Cat"),("words","dog","Dog"),
    ("words","elephant","Elephant"),("words","fish","Fish"),
    ("words","queen","Queen"),("words","sun","Sun"),
    ("words","water","Water"),("words","zebra","Zebra"),
]

def main():
    folder=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path("voice-preview")
    if not folder.is_dir():
        raise SystemExit("MP3 folder missing; cannot prepare player.")
    rows=[]
    for group,name,label in CUES:
        path=folder/group/(name+".mp3")
        if not path.exists():raise SystemExit(f"Missing recording: {path}")
        data=path.read_bytes()
        if len(data)<1000 or not (data[:3]==b"ID3" or data[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")):
            raise SystemExit(f"Invalid-looking MP3: {path} / {len(data)} bytes")
        b64=base64.b64encode(data).decode("ascii")
        src="data:audio/mpeg;base64,"+b64
        title="שם האות" if group=="names" else "מילה"
        rows.append(f'<article><div class="header"><b>{html.escape(label)}</b><span>{title}</span></div><audio controls preload="metadata" src="{src}">הדפדפן שלך אינו תומך בהשמעת קובץ זה.</audio></article>')
    page = """<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ABC QUEST - Listen on Android</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{font-family:system-ui,Arial,sans-serif;max-width:660px;margin:0 auto;padding:18px;background:#102262;color:white}
h1{font-size:27px}p{line-height:1.5;color:#d6e1ff}article{background:#203b88;padding:13px;margin:11px 0;border-radius:17px}
.header{display:flex;justify-content:space-between;align-items:center;padding:0 5px 10px}.header b{font-size:24px}.header span{color:#d4e1fc}
audio{display:block;width:100%;min-height:54px}footer{margin-top:24px;font-size:12px;color:#c8d5ff}
</style></head><body><h1>🔊 ABC QUEST — בודקים את הקול</h1>
<p>זהו דף עצמאי. כל 15 ההקלטות כבר נמצאות בתוך הקובץ הזה ולכן אפשר לפתוח אותו גם בטלפון אנדרואיד בלי תיקיות MP3 סמוכות ובלי אינטרנט.</p>
"""+"".join(rows)+"""<footer>15 קובצי MP3 של ElevenLabs. שמות האותיות והמילים הם דוגמאות בלבד; הפונטיקה תיבדק בנפרד.</footer></body></html>"""
    target=folder/"LISTEN_ON_PHONE.html"
    target.write_text(page,encoding="utf-8")
    assert page.count("<audio ")==15
    print(f"Created {target}, {target.stat().st_size} bytes, 15 embedded MP3s")
    (folder/"README_PHONE.txt").write_text(
        "ANDROID: Open LISTEN_ON_PHONE.html only. It has all MP3 files embedded.\n"
        "If your phone file viewer does not play the embedded tracks, open names/A.mp3 directly in an audio player.\n"
        "No new audio generated, and no API cost.\n",encoding="utf-8")

if __name__=="__main__":main()
