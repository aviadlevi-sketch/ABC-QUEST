#!/usr/bin/env python3
"""Build ABC QUEST 7.6 source from official 7.5 Android ZIP and approved audio.

All assets are offline and paid voice provider credentials are NOT embedded.
The script requires three already-downloaded GitHub Actions artifacts:
  - 26 contextual letter names
  - 26 approved phonemes (X is the legacy source recording)
  - 156 game word placements in selected Voice 2 (approved US Zebra)
Patches the Android game, supports existing localStorage saves and increases
versionCode so that v7.6 installs over v7.5 without losing progress.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import string
import zipfile

ABC = string.ascii_uppercase

def replace_exact(content: str, old: str, new: str, label: str, n: int = 1) -> str:
    seen=content.count(old)
    if seen!=n:
        raise RuntimeError(f"Cannot safely patch {label}: expected {n} matches, got {seen}")
    return content.replace(old,new)

def word_bank_from_html(page: str):
    match=re.search(r"\bconst\s+WORD_BANK\s*=\s*",page)
    if not match: raise RuntimeError("Word bank missing")
    data,_=json.JSONDecoder().raw_decode(page[match.end():])
    if len(data)!=26 or set(data)!=set(ABC):
        raise RuntimeError("Word bank must have 26 A-Z categories")
    for letter in ABC:
        if len(data[letter])!=6: raise RuntimeError(f"Expected 6 words in {letter}")
    return data

def read_audio(path: Path) -> bytes:
    b=path.read_bytes()
    if len(b)<1000 or not (b[:3]==b"ID3" or b[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")):
        raise RuntimeError(f"Missing or invalid MP3: {path}")
    return b

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-zip",required=True,type=Path)
    parser.add_argument("--project-output",required=True,type=Path)
    parser.add_argument("--patches",required=True,type=Path)
    parser.add_argument("--names",required=True,type=Path)
    parser.add_argument("--phonemes",required=True,type=Path)
    parser.add_argument("--words",required=True,type=Path)
    args=parser.parse_args()

    out=args.project_output
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.source_zip) as src:
        # GitHub-supplied ZIP only; ensure safe paths.
        for entry in src.namelist():
            normalized=Path(entry)
            if normalized.is_absolute() or ".." in normalized.parts:
                raise RuntimeError("Unsafe path found in source ZIP")
        src.extractall(out)
    projects=list(out.rglob("settings.gradle"))
    if len(projects)!=1:raise RuntimeError("Expected one Android project in source")
    root=projects[0].parent
    assets=root/"app/src/main/assets"
    index_file=assets/"index.html"
    js_file=assets/"adventure_v73.js"
    gradle_file=root/"app/build.gradle"
    html_page=index_file.read_text(encoding="utf-8")
    adventure=js_file.read_text(encoding="utf-8")
    bank=word_bank_from_html(html_page)
    audio=assets/"audio"
    audio.mkdir(exist_ok=True)

    names={};sounds={};words={}
    all_records=[]

    for letter in ABC:
        source=args.names/"names"/(letter+".mp3")
        data=read_audio(source)
        relative="audio/names/"+letter+".mp3"
        target=assets/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        names[letter]=relative
        source=args.phonemes/"phonemes"/(letter+".mp3")
        data=read_audio(source)
        relative="audio/phonemes/"+letter+".mp3"
        target=assets/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        sounds[letter]=relative

    for letter in ABC:
        for row in bank[letter]:
            label=row["word"]
            key=label.lower()
            # Word bank includes the same word "fox" in F and X.
            source=args.words/"words"/letter/(key+".mp3")
            data=read_audio(source)
            relative="audio/words/"+letter+"/"+key+".mp3"
            target=assets/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            if key not in words:
                words[key]=relative
            all_records.append({"letter":letter,"word":label,"audio":relative})
    if len(all_records)!=156 or len(words)!=155:
        raise RuntimeError(f"Wrong word-bank inventory: {len(all_records)} placements, {len(words)} distinct")

    # Strict end-to-end checks: names, phonemes, 156 word files.
    clips=list(audio.rglob("*.mp3"))
    if len(clips)!=208:
        raise RuntimeError(f"Expected 208 local MP3 files, got {len(clips)}")
    for item in clips:read_audio(item)
    manifest={
        "names":names,"phonemes":sounds,"words":words,
    }
    (audio/"manifest.js").write_text(
        "window.ABC_QUEST_AUDIO="+json.dumps(manifest,ensure_ascii=False,separators=(",",":"))+";\n",
        encoding="utf-8",
    )
    (audio/"validation.json").write_text(json.dumps({
        "game":"ABC QUEST 7.6","voice":"NoOVOzCQFLOvtsMoNcdT",
        "count_local_mp3":len(clips),"names":26,"phonemes":26,"word_placements":156,
        "unique_spoken_words":len(words),
        "special_cases":{"zebra":"approved US ZEE-bruh","X_phoneme":"original v7.5 recording"},
        "words":all_records,
    },indent=2,ensure_ascii=False),encoding="utf-8")

    # A newly-installed app starts without a purchased character. Alpha can be
    # displayed as a borrowed starter avatar until the first paid unlock.
    # Old players keep already owned Alpha and all previously earned heroes.
    html_page=replace_exact(
        html_page,
        "if(!Array.isArray(progress.ownedHeroes))progress.ownedHeroes=['alpha'];",
        "if(!Array.isArray(progress.ownedHeroes))progress.ownedHeroes=[];",
        "don't give Alpha ownership to fresh installs",
    )
    html_page=replace_exact(
        html_page,
        "if(!progress.ownedHeroes.includes('alpha'))progress.ownedHeroes.unshift('alpha');",
        "/* v7.6: starter Alpha is a trial avatar, not a free owned character. */",
        "avoid regranting Alpha",
    )

    # Disable the v7.5 automatic world-first hero gifting (including on
    # page re-renders). v7.6 requires achievements AND credits for these heroes.
    gift_pattern=r"function maybeAutoOpenWorldHero\(\)\{[\s\S]*?\n\}\nfunction initQuest\(\)"
    if len(re.findall(gift_pattern,adventure))!=1:
        raise RuntimeError("Cannot safely disable previous free-world-hero mechanism")
    adventure=re.sub(
        gift_pattern,
        "function maybeAutoOpenWorldHero(){return false;}\nfunction initQuest()",
        adventure,count=1,
    )
    adventure=replace_exact(adventure,"const QUEST_VERSION=6;","const QUEST_VERSION=76;",
                            "quest version")
    # Existing version 75/76 saves must never be scaled by 30x/4x again.
    adventure=replace_exact(
        adventure,"if(progress.economyVersion!==75){",
        "if(progress.economyVersion!==75 && progress.economyVersion!==76){",
        "don't multiply saved credits and trophies on reinstall",
    )
    # Phonics/reading MUST be able to qualify as world victories when >75%.
    adventure=replace_exact(
        adventure,"qualified=correct>=Math.ceil(length*.75) && mode!=='read';",
        "qualified=correct>=Math.ceil(length*.75);",
        "reading games count toward world victories",
    )
    adventure=replace_exact(
        adventure,"const won=!game.diagnostic&&pct>=75&&game.mode!=='read'",
        "const won=!game.diagnostic&&pct>=75",
        "reading win screen status",
    )
    # Skins require 2.5x more EXTRA trophy milestones on top of their now
    # 4x-priced hero gate, so the skin threshold cannot undercut its hero.
    adventure=replace_exact(
        adventure,"heroTrophyGate(id)+[0,600,1500,3200][tier]",
        "heroTrophyGate(id)+[0,1500,3750,8000][tier]",
        "scale skin trophies by 2.5 over hero baseline",
    )

    gameplay_patch=(args.patches/"v76_gameplay.js").read_text(encoding="utf-8")
    if "ABCQuestVersion76" not in gameplay_patch:
        raise RuntimeError("Gameplay upgrade patch missing")
    last=adventure.rfind("})();")
    if last<0 or len(adventure[last:])>15:
        raise RuntimeError("Cannot locate adventure module closing IIFE")
    adventure=adventure[:last]+("\n/* v7.6 progression, home compass and economy */\n"+
            gameplay_patch+"\nrender();\n")+adventure[last:]
    js_file.write_text(adventure,encoding="utf-8")

    # Replace the old Android-TTS fallback (all audios bundled) with direct
    # playback and true chained reading practice.
    shutil.copyfile(args.patches/"offline-audio-v76.js",assets/"offline-audio.js")
    shutil.copyfile(args.patches/"economy-v76.css",assets/"economy_v76.css")
    html_page=replace_exact(
        html_page,'<link rel="stylesheet" href="economy_v75.css">',
        '<link rel="stylesheet" href="economy_v75.css">'+
        '<link rel="stylesheet" href="economy_v76.css">',
        "new home quest and rarity badge stylesheet",
    )
    index_file.write_text(html_page,encoding="utf-8")

    gradle=gradle_file.read_text(encoding="utf-8")
    gradle=replace_exact(gradle,"versionName '7.5-preview'","versionName '7.6-preview'",
                         "new versionName")
    gradle=replace_exact(gradle,"versionCode 12","versionCode 13",
                         "increment Android versionCode for in-place update")
    gradle_file.write_text(gradle,encoding="utf-8")
    assert (assets/"offline-audio.js").is_file()
    assert "ABCQuestVersion76" in js_file.read_text(encoding="utf-8")
    print("v7.6 prepared; 208 MP3; 156 word placements / 155 unique spoken words.")
    print("Preserves previous progress and removes new-account free hero grant.")
    print("Android project directory:",root)
    (out/"build_root.txt").write_text(str(root.resolve())+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
