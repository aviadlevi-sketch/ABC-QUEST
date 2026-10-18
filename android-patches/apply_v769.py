#!/usr/bin/env python3
"""Apply ABC QUEST v7.6.9 to the generated 7.6.8 Android project."""
import argparse
from pathlib import Path
import shutil

def swap(s, a, b, label):
    n=s.count(a)
    if n!=1:raise RuntimeError(label+': expected one occurrence, found '+str(n))
    return s.replace(a,b,1)

def main():
    q=argparse.ArgumentParser()
    q.add_argument('--project',required=True,type=Path)
    q.add_argument('--patches',required=True,type=Path)
    a=q.parse_args()
    assets=a.project/'app/src/main/assets'
    file=assets/'adventure_v73.js'
    s=file.read_text(encoding='utf-8')
    s=swap(s,' const unmet=[];\n if(s.letters<need.letters)',
       " const unmet=[];\n const heroId=WORLD_HEROES[i][slot],costStone=Math.round(heroCreditPrice(heroId)/10);\n if(!ownsHero(heroId)&&Number(progress.worldStones769?.[i]||0)<costStone)unmet.push('💎 חסרות אבנים של העולם הזה');\n if(s.letters<need.letters)",'hero stone guard')
    s=swap(s,' return {ready:!problems.length,problems,need,s};',
       " const stoneNeed=Math.round(skinCreditPrice(id,tier)/10),stoneBal=Number(progress.worldStones769?.[i]||0);\n if(tier>0&&!ownsSkin(id,tier)&&stoneBal<stoneNeed)problems.push('💎 חסרות אבנים של העולם הזה');\n return {ready:!problems.length,problems,need,s};",'skin stone guard')
    s=swap(s,' const already=ownsHero(id),price=heroCreditPrice(id);',
       " const already=ownsHero(id),price=heroCreditPrice(id),stoneCost=Math.round(price/10);\n if(!already&&Number(progress.worldStones769?.[i]||0)<stoneCost){showToast('💎 חסרות אבנים של העולם הזה');return;}",'hero affordability')
    s=swap(s,' if(!already)progress.credits-=price;',
       ' if(!already){progress.credits-=price;progress.worldStones769[i]-=stoneCost;}','hero debit')
    s=swap(s,' let starsEarned=0,creditsEarned=0,qualified=false,recorded=false;',
       ' let starsEarned=0,creditsEarned=0,stonesEarned=0,qualified=false,recorded=false;','stones counter')
    s=swap(s,'  progress.stars+=starsEarned;\n  progress.credits+=creditsEarned;',
       "  if(qualified&&typeof scope==='number'&&worldOpen(scope)){\n   stonesEarned=recorded?12:6;\n   progress.worldStones769[scope]=(Number(progress.worldStones769[scope])||0)+stonesEarned;\n  }\n  progress.stars+=starsEarned;\n  progress.credits+=creditsEarned;",'win stone award')
    s=swap(s,'credits:creditsEarned,qualified,recorded,scope,mode,date',
       'credits:creditsEarned,stones:stonesEarned,qualified,recorded,scope,mode,date','win reward detail')
    s=swap(s,'  try{original(el.dataset.hero,tier);}finally{SKIN_LEVELS[tier].price=previous;}',
       "  const id=el.dataset.hero,w=worldByHero(id),cost=Math.round(price/10),ownedBefore=ownsSkin(id,tier);\n  if(!ownedBefore&&Number(progress.worldStones769?.[w]||0)<cost)return showToast('💎 חסרות אבנים של העולם הזה');\n  try{\n   original(id,tier);\n   if(!ownedBefore&&ownsSkin(id,tier)){progress.worldStones769[w]-=cost;save();render();}\n  }finally{SKIN_LEVELS[tier].price=previous;}",'skin debit on success')
    s=swap(s,'big:[7,14,21,28,30].includes(day)',
       'big:[7,14,21,28,29,30].includes(day)','bonus days')
    s=swap(s,"(r.big?'🎁':'🪙')","'🪙'",'credit icon on login tile')
    s=swap(s," return {label:'🎉 אפשר לרכוש את הדמות!'",
       " if((progress.worldStones769?.[w]||0)<Math.round(heroCreditPrice(h.id)/10))return {label:'💎 לשחק בעולם הזה כדי להשיג אבנים',act:'quest76-world',world:w};\n return {label:'🎉 אפשר לרכוש את הדמות!'",'hero next step')
    s=swap(s," return {label:'✨ לרכוש את הסקין'",
       " if((progress.worldStones769?.[world]||0)<Math.round(price/10))return {label:'💎 לשחק בעולם הזה כדי להשיג אבנים',act:'quest76-world',world};\n return {label:'✨ לרכוש את הסקין'",'skin next step')
    patch=(a.patches/'v769_patch.js').read_text(encoding='utf-8').rstrip()
    end='\nrender();\n})();'
    if not s.rstrip().endswith(end):raise RuntimeError('v7.6.8 terminal render not found')
    if 'ABCQuestWorldStones769' in s:raise RuntimeError('already patched')
    s=s.rstrip()[:-len(end)]+'\n'+patch+end+'\n'
    file.write_text(s,encoding='utf-8')
    shutil.copyfile(a.patches/'quest769.css',assets/'quest769.css')
    html=assets/'index.html'
    h=html.read_text(encoding='utf-8')
    h=swap(h,'<link rel="stylesheet" href="quest768.css">','<link rel="stylesheet" href="quest768.css"><link rel="stylesheet" href="quest769.css">','CSS')
    html.write_text(h.replace('גרסה 7.6.8','גרסה 7.6.9'),encoding='utf-8')
    gradle=a.project/'app/build.gradle'
    g=gradle.read_text(encoding='utf-8')
    g=swap(g,'versionCode 21','versionCode 22','Android version code')
    g=swap(g,"versionName '7.6.8-preview'","versionName '7.6.9-preview'",'Android version name')
    gradle.write_text(g,encoding='utf-8')
    print('ABC QUEST 7.6.9 world stone economy applied.')

if __name__=='__main__':
    main()
