#!/usr/bin/env python3
"""Apply UI-only 7.6.10 patch to an existing 7.6.9 Android source folder."""
import argparse
from pathlib import Path
import shutil

p=argparse.ArgumentParser()
p.add_argument('--project',type=Path,required=True)
p.add_argument('--patches',type=Path,required=True)
a=p.parse_args()
assets=a.project/'app/src/main/assets'
js=assets/'adventure_v73.js'
source=js.read_text(encoding='utf-8')
ending='\nrender();\n})();'
assert source.rstrip().endswith(ending), 'Unexpected game footer'
assert 'ABCQuestHeroCards7610' not in source, 'Already updated'
source=source.rstrip()[:-len(ending)]+'\n'+(a.patches/'v7610_patch.js').read_text(encoding='utf-8')+ending+'\n'
js.write_text(source,encoding='utf-8')
shutil.copyfile(a.patches/'quest7610.css',assets/'quest7610.css')
html=assets/'index.html'
text=html.read_text(encoding='utf-8')
needle='<link rel="stylesheet" href="quest769.css">'
assert text.count(needle)==1, 'Missing stylesheet'
text=text.replace(needle,needle+'<link rel="stylesheet" href="quest7610.css">',1)
text=text.replace('גרסה 7.6.9','גרסה 7.6.10')
html.write_text(text,encoding='utf-8')
build=a.project/'app/build.gradle'
text=build.read_text(encoding='utf-8')
assert text.count('versionCode 22')==1
assert text.count("versionName '7.6.9-preview'")==1
text=text.replace('versionCode 22','versionCode 23').replace("versionName '7.6.9-preview'","versionName '7.6.10-preview'")
build.write_text(text,encoding='utf-8')
print('ABC QUEST v7.6.10 patched successfully.')
