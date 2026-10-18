#!/usr/bin/env python3
"""Upgrade generated ABC QUEST 7.6.7 Android project to 7.6.8.
Run after android-patches/build_v76_source.py in the existing CI pipeline.
Keeps the package ID, TEST signing key, local save key, audio, and artwork unchanged.
"""
import argparse
from pathlib import Path
import shutil

def replace_once(s: str, old: str, new: str, label: str) -> str:
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one occurrence, found {count}")
    return s.replace(old, new, 1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--patches", type=Path, required=True)
    args = ap.parse_args()
    assets = args.project / "app/src/main/assets"
    js_path = assets / "adventure_v73.js"
    html_path = assets / "index.html"
    gradle_path = args.project / "app/build.gradle"
    js = js_path.read_text(encoding="utf-8")
    js = replace_once(js,
        "const WIN_REWARD_TROPHIES=220, WIN_REWARD_CREDITS=50;",
        "const WIN_REWARD_TROPHIES=220, WIN_REWARD_CREDITS=120;", "full-world reward")
    js = replace_once(js,
        "const EXTRA_REWARD_TROPHIES=110, EXTRA_REWARD_CREDITS=25;",
        "const EXTRA_REWARD_TROPHIES=110, EXTRA_REWARD_CREDITS=60;", "extra-world reward")
    js = replace_once(js,
        "const ALL_WORLD_REWARD_TROPHIES=110,ALL_WORLD_REWARD_CREDITS=25;",
        "const ALL_WORLD_REWARD_TROPHIES=110,ALL_WORLD_REWARD_CREDITS=60;", "all-world reward")
    js = replace_once(js,
        "const ALL_WORLD_EXTRA_TROPHIES=55,ALL_WORLD_EXTRA_CREDITS=12;",
        "const ALL_WORLD_EXTRA_TROPHIES=55,ALL_WORLD_EXTRA_CREDITS=30;", "all-world extra reward")
    patch = (args.patches / "v768_patch.js").read_text(encoding="utf-8").rstrip() + "\n"
    if "ABCQuestEconomy768" in js:
        raise RuntimeError("7.6.8 already injected")
    end = "\nrender();\n})();"
    if not js.rstrip().endswith(end):
        raise RuntimeError("Did not find final render and outer closure")
    js = js.rstrip()[:-len(end)] + "\n" + patch + end + "\n"
    js_path.write_text(js, encoding="utf-8")

    html = html_path.read_text(encoding="utf-8")
    html = replace_once(html, "<title>ABC QUEST | גרסה 7.5</title>",
                        "<title>ABC QUEST | גרסה 7.6.8</title>", "HTML title")
    html = replace_once(html, '<link rel="stylesheet" href="adventure_v73.css"></head>',
                        '<link rel="stylesheet" href="adventure_v73.css"><link rel="stylesheet" href="quest768.css"></head>',
                        "help CSS reference")
    html_path.write_text(html, encoding="utf-8")
    shutil.copyfile(args.patches / "quest768.css", assets / "quest768.css")

    gradle = gradle_path.read_text(encoding="utf-8")
    gradle = replace_once(gradle, "versionCode 20", "versionCode 21", "Android versionCode")
    gradle = replace_once(gradle, "versionName '7.6.7-preview'",
                          "versionName '7.6.8-preview'", "Android versionName")
    gradle_path.write_text(gradle, encoding="utf-8")
    print("ABC QUEST 7.6.8 ready: 120/60 credits, new trophy/skin gates, child's guide.")
    print("Save key and signing assets were not modified.")

if __name__ == "__main__":
    main()
