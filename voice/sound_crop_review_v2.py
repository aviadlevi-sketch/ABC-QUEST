#!/usr/bin/env python3
from pathlib import Path
import argparse, base64, html, json, shutil
from extract_phonemes_from_words import LETTERS, samples, active_bounds, crop_mp3, valid_mp3

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--previous",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--params",type=Path,required=True)
 a=p.parse_args()
 settings=json.loads(a.params.read_text())
 dest=a.out
 for d in ("words","short","alternatives"):
  (dest/d).mkdir(parents=True,exist_ok=True)
 vocab={letter:(word,ipa) for letter,word,ipa,_ in LETTERS}
 for letter,word,ipa,_ in LETTERS:
  shutil.copyfile(a.previous/"words"/(word+".mp3"),dest/"words"/(word+".mp3"))
  shutil.copyfile(a.previous/"sounds"/(letter+"_short.mp3"),dest/"short"/(letter+".mp3"))
 timings={}
 for letter,windows in {**settings["starts"],**settings["tail"]}.items():
  word,ipa=vocab[letter]
  original=dest/"words"/(word+".mp3")
  arr=samples(original)
  initial,final,peak=active_bounds(arr)
  length=len(arr)/16000
  timings[letter]={}
  for version,seconds in zip(("A","B"),windows):
   if letter=="X":
    end=min(length,final+.020)
    start=end-seconds
    assert start > initial + (final-initial)*.43, ("X crop reaches earlier sounds", start, initial, final)
   else:
    start=max(0,initial-.016)
    end=min(length,start+seconds)
   file=dest/"alternatives"/(letter+"_"+version+".mp3")
   crop_mp3(original,file,start,end)
   timings[letter][version]=[round(start,3),round(end,3)]
   print(letter,version,round(start,3),round(end,3),flush=True)
 blocks=[]
 def player(label,file):
  audio=file.read_bytes()
  assert valid_mp3(audio),file
  encoded=base64.b64encode(audio).decode()
  return '<div><small>'+html.escape(label)+'</small><audio controls preload="none" src="data:audio/mpeg;base64,'+encoded+'"></audio></div>'
 for letter in list(settings["starts"])+list(settings["tail"]):
  word,ipa=vocab[letter]
  blocks.append('<section><h2>'+letter+' /'+ipa+'/ — '+word+'</h2><div class="grid">'+
   player("מילה",dest/"words"/(word+".mp3"))+
   player("קצר קודם",dest/"short"/(letter+".mp3"))+
   player("תיקון A",dest/"alternatives"/(letter+"_A.mp3"))+
   player("תיקון B",dest/"alternatives"/(letter+"_B.mp3"))+'</div></section>')
 blocks.append('<h2>16 אותיות ללא שינוי</h2>')
 for letter,word,ipa,_ in LETTERS:
  if letter in timings:continue
  blocks.append('<section><h2>'+letter+' /'+ipa+'/</h2>'+player("החיתוך הקצר הקודם",dest/"short"/(letter+".mp3"))+'</section>')
 page='<html lang="he" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ABC QUEST Sounds</title><style>:root{color-scheme:dark}body{font-family:Arial;background:#122660;color:white;max-width:800px;margin:auto;padding:15px}section{padding:12px;background:#254482;border-radius:12px;margin:12px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}audio{width:100%;display:block;margin:5px 0 12px}small{display:block}</style><h1>ABC QUEST — צלילים מתוקנים</h1><p>10 אותיות לבדיקה, כולל X מסוף Fox. 16 האותיות האחרות ללא שינוי. ההקלטות מוטמעות, ללא אינטרנט. אין הפקת קול חדשה.</p>'+''.join(blocks)+'</html>'
 assert page.count("<audio controls")==56
 (dest/"LISTEN_REFINED_SOUNDS.html").write_text(page,encoding="utf-8")
 (dest/"CUT_TIMINGS.json").write_text(json.dumps(timings,indent=2))
 print("READY 20 revised clips, 26 old clips, no API calls")

if __name__=="__main__":main()
