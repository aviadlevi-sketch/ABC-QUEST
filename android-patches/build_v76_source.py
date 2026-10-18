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

    # Every player starts with Alpha for free. Existing heroes, purchased skins,
    # earned credits and trophies remain intact across in-place upgrades.
    # No other character is gifted or loaned.
    html_page=replace_exact(
        html_page,
        "if(!Array.isArray(progress.ownedHeroes))progress.ownedHeroes=['alpha'];",
        "if(!Array.isArray(progress.ownedHeroes))progress.ownedHeroes=['alpha'];",
        "free starter Alpha for new users",
    )
    html_page=replace_exact(
        html_page,
        "if(!progress.ownedHeroes.includes('alpha'))progress.ownedHeroes.unshift('alpha');",
        "if(!progress.ownedHeroes.includes('alpha'))progress.ownedHeroes.unshift('alpha');"
        "if(!progress.questClaimedHeroes || typeof progress.questClaimedHeroes!=='object')progress.questClaimedHeroes={};"
        "progress.questClaimedHeroes.alpha=true;",
        "mark starter Alpha owned and claimed without cost",
    )

    # Equipped heroes are a global collection, never bound to the current world.
    # Keep previously selected owned characters, or select starter Alpha.
    html_page=replace_exact(
        html_page,
        "if(!progress.equippedHero||!progress.ownedHeroes.includes(progress.equippedHero))progress.equippedHero='alpha';",
        "if(!progress.equippedHero||!progress.ownedHeroes.includes(progress.equippedHero))progress.equippedHero=progress.ownedHeroes[0]||'alpha';",
        "equip a legitimately owned hero, defaulting to free Alpha",
    )
    html_page=replace_exact(
        html_page,
        "function skinImage(id,tier=0){return HERO_IMAGES[id]?.[tier]||HERO_IMAGES.alpha[0];}",
        "function skinImage(id,tier=0){return id==='unassigned'?'branding/no_hero_yet.svg':(HERO_IMAGES[id]?.[tier]||HERO_IMAGES.alpha[0]);}",
        "neutral unowned avatar placeholder",
    )
    html_page=replace_exact(
        html_page,
        "function equippedHero(){return getHero(progress.equippedHero);}",
        "function equippedHero(){return ownsHero(progress.equippedHero)?getHero(progress.equippedHero):{id:'unassigned',name:'עוד אין דמות',subtitle:'שחקו כדי לצבור קרדיטים ולקנות דמות ראשונה'};}",
        "never display unowned Alpha as selected hero",
    )
    html_page=replace_exact(
        html_page,
        "function equippedTier(id){return progress.equippedSkins[id]||0;}",
        "function equippedTier(id){return id==='unassigned'?0:(progress.equippedSkins[id]||0);}",
        "no skin granted to unowned avatar",
    )
    (assets/"branding").mkdir(exist_ok=True)
    (assets/"branding/no_hero_yet.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
        '<defs><linearGradient id="g"><stop stop-color="#2145a8"/>'
        '<stop offset="1" stop-color="#116f92"/></linearGradient></defs>'
        '<rect x="8" y="8" width="184" height="184" rx="44" fill="url(#g)"/>'
        '<circle cx="100" cy="68" r="26" fill="#d2ddff" opacity=".76"/>'
        '<path d="M39 159c2-29 25-51 61-51s59 22 61 51v10H39z" fill="#d2ddff" opacity=".76"/>'
        '<circle cx="164" cy="42" r="17" fill="#ffd96d"/>'
        '<text x="164" y="49" font-size="21" text-anchor="middle" font-weight="bold" fill="#15234f">?</text>'
        '</svg>',
        encoding="utf-8",
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

    # Extend the displayed total practice journey from ten to thirty actual
    # practice days. This DOES NOT inflate per-world win/day gates or lock
    # previously purchased heroes; the 30-day journey is a cumulative target.
    adventure=replace_exact(
        adventure,
        "📅 מסע של כ־10 ימים",
        "📅 יום ${Math.min(fameDays(),30)} מתוך 30 במסע",
        "replace obsolete ten-day journey claim in home ribbon",
    )
    adventure=replace_exact(
        adventure,
        "The 24 levels are tuned for about ten practice days",
        "The 24 levels form a long-term fame ladder, distinct from the 30-day journey",
        "fix obsolete ten-day developer comment",
    )

    gameplay_patch=(args.patches/"v76_gameplay.js").read_text(encoding="utf-8")
    reading_patch=(args.patches/"reading-v764.js").read_text(encoding="utf-8")
    reward_patch=(args.patches/"rewards-v766.js").read_text(encoding="utf-8")
    if "ABCQuestVersion76" not in gameplay_patch:
        raise RuntimeError("Gameplay upgrade patch missing")
    if "ABCQuestVerifiedReading764" not in reading_patch:
        raise RuntimeError("Verified microphone reading patch missing")
    if "ABCQuestRewards766" not in reward_patch:
        raise RuntimeError("30-day reward engine patch missing")
    last=adventure.rfind("})();")
    if last<0 or len(adventure[last:])>15:
        raise RuntimeError("Cannot locate adventure module closing IIFE")
    adventure=adventure[:last]+("\n/* v7.6 progression, home compass and economy */\n"+
            gameplay_patch+"\n/* v7.6.4: microphone-verified reading */\n"+
            reading_patch+"\n/* v7.6.6: cumulative login and claim-once rewards */\n"+
            reward_patch+"\nrender();\n")+adventure[last:]
    js_file.write_text(adventure,encoding="utf-8")

    # Replace the old Android-TTS fallback (all audios bundled) with direct
    # playback and true chained reading practice.
    shutil.copyfile(args.patches/"offline-audio-v76.js",assets/"offline-audio.js")
    shutil.copyfile(args.patches/"economy-v76.css",assets/"economy_v76.css")
    shutil.copyfile(args.patches/"reading-v764.css",assets/"reading_v764.css")
    shutil.copyfile(args.patches/"rewards-v766.css",assets/"rewards_v766.css")
    html_page=replace_exact(
        html_page,'<link rel="stylesheet" href="economy_v75.css">',
        '<link rel="stylesheet" href="economy_v75.css">'+
        '<link rel="stylesheet" href="economy_v76.css">'+
        '<link rel="stylesheet" href="reading_v764.css">'+
        '<link rel="stylesheet" href="rewards_v766.css">',
        "new home quest and rarity badge stylesheet",
    )
    # Register the new prize-screen without replacing the existing navigation.
    # The legacy JS renders pages from a known local screens dictionary.
    html_page=replace_exact(
        html_page,
        "{id:'shop',name:'חנות',icon:'🛒'},{id:'progress',name:'הישגים',icon:'🏆'}",
        "{id:'shop',name:'חנות',icon:'🛒'},{id:'rewards',name:'פרסים',icon:'🎁'},"
        "{id:'progress',name:'הישגים',icon:'🏆'}",
        "add rewards sidebar navigation",
    )
    html_page=replace_exact(
        html_page,
        "shop:shopPage,progress:progressPage",
        "shop:shopPage,rewards:()=>window.ABCQuestRewards766?.page?.()||'<div>טוענים פרסים...</div>',progress:progressPage",
        "register rewards page in main screen router",
    )
    html_page=replace_exact(
        html_page,
        "shop:'החנות',progress:'ההתקדמות שלי'",
        "shop:'החנות',rewards:'אוצר הפרסים',progress:'ההתקדמות שלי'",
        "show meaningful header for reward screen",
    )
    html_page=replace_exact(
        html_page,
        "['home','map','games','heroes','shop'].includes(n.id)",
        "['home','map','games','heroes','shop','rewards'].includes(n.id)",
        "make prize board directly accessible on Android bottom navigation",
    )

    index_file.write_text(html_page,encoding="utf-8")

    # Android recognizer already delegates microphone permissions to the OS.
    # Return up to five speech hypotheses (not just the first) so that the
    # child's correct letter names can be recognized despite ASR ambiguity.
    # No microphone recording or transcript is persisted by our app.
    activity_path=root/"app/src/main/java/com/abcquest/kids/MainActivity.java"
    activity=activity_path.read_text(encoding="utf-8")
    activity=replace_exact(activity,"import org.json.JSONObject;",
        "import org.json.JSONObject;\nimport org.json.JSONArray;",
        "Android Java SpeechRecognizer JSON array dependency")
    activity=replace_exact(activity,"RecognizerIntent.EXTRA_MAX_RESULTS, 4",
        "RecognizerIntent.EXTRA_MAX_RESULTS, 5",
        "request multiple possible speech results")
    activity=replace_exact(activity,
        '"Say the English letter names"',
        '"Read the English letters aloud in order"',
        "speech prompt for a child")
    activity=replace_exact(activity,"notifySpeech(\"\");",
        "notifySpeechUnavailable();","report Android recognizer missing",n=2)
    activity=replace_exact(activity,
        '''    private void notifySpeech(String transcript) {
        if (webView == null) return;
        final String js = "window.abcNativeSpeechResult(" + JSONObject.quote(transcript) + ");";
        webView.post(() -> webView.evaluateJavascript(js, null));
    }''',
        '''    private void notifySpeech(ArrayList<String> transcripts) {
        if (webView == null) return;
        JSONArray alternatives = new JSONArray();
        if (transcripts != null) {
            for (String text : transcripts) {
                if (text != null && !text.trim().isEmpty()) alternatives.put(text);
            }
        }
        final String js = "window.abcNativeSpeechResult(" + alternatives.toString() + ");";
        webView.post(() -> webView.evaluateJavascript(js, null));
    }
    private void notifySpeechUnavailable() {
        if (webView == null) return;
        webView.post(() -> webView.evaluateJavascript(
            "window.abcNativeSpeechError('unavailable');", null));
    }''',
        "send alternatives rather than first-only transcript")
    activity=replace_exact(activity,
        '''        String transcript = "";
        if (resultCode == RESULT_OK && data != null) {
            ArrayList<String> texts = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (texts != null && !texts.isEmpty()) transcript = texts.get(0);
        }
        notifySpeech(transcript);''',
        '''        ArrayList<String> alternatives = new ArrayList<>();
        if (resultCode == RESULT_OK && data != null) {
            ArrayList<String> heard = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (heard != null) alternatives.addAll(heard);
        }
        notifySpeech(alternatives);''',
        "return every OS transcription alternative or an empty canceled result")
    activity_path.write_text(activity,encoding="utf-8")

    gradle=gradle_file.read_text(encoding="utf-8")
    gradle=replace_exact(gradle,"versionName '7.5-preview'","versionName '7.6.7-preview'",
                         "new versionName")
    gradle=replace_exact(gradle,"versionCode 12","versionCode 20",
                         "increment Android versionCode for in-place update")
    gradle_file.write_text(gradle,encoding="utf-8")
    assert (assets/"offline-audio.js").is_file()
    assert "ABCQuestVersion76" in js_file.read_text(encoding="utf-8")
    assert "ABCQuestVerifiedReading764" in js_file.read_text(encoding="utf-8")
    assert "ABCQuestRewards766" in js_file.read_text(encoding="utf-8")
    assert "rewards:'אוצר הפרסים'" in index_file.read_text(encoding="utf-8")
    assert "new JSONArray()" in activity_path.read_text(encoding="utf-8")
    print("v7.6.7 prepared; 208 MP3; 156 word placements / 155 unique spoken words.")
    print("Preserves previous progress; starter Alpha granted at zero cost.")
    print("Android project directory:",root)
    (out/"build_root.txt").write_text(str(root.resolve())+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
