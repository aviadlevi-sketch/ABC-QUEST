from pathlib import Path
from PIL import Image
from io import BytesIO
import json,base64

a=Path('app/src/main/assets')
htmlfile=a/'index.html'
html=htmlfile.read_text(encoding='utf-8')
begin=html.index('const HERO_IMAGES=')+len('const HERO_IMAGES=')
end=html.index('};',begin)+1
images=json.loads(html[begin:end])
assert len(images)==15
new={}
for hero,variants in images.items():
    assert len(variants)==4
    new[hero]=[]
    dest=a/'images'/hero
    dest.mkdir(parents=True,exist_ok=True)
    for tier,data in enumerate(variants):
        im=Image.open(BytesIO(base64.b64decode(data.partition(',')[2]))).convert('RGB')
        name=str(tier)+'.jpg'
        im.save(dest/name,'JPEG',quality=89,subsampling=0,optimize=True)
        new[hero].append('images/'+hero+'/'+name)
html=html[:begin]+json.dumps(new,separators=(',',':'))+html[end:]
html=html.replace('גרסה 7.3','גרסה 7.4')
html=html.replace('<script src="adventure_v73.js"></script></body>',
 '<script src="adventure_v73.js"></script><link rel="stylesheet" href="balance_v74.css"></body>')
htmlfile.write_text(html,encoding='utf-8')
astra=a/'astra_skins.js'
prefix='window.ABC_QUEST_ASTRA_SKINS='
data=astra.read_text(encoding='utf-8')
assert data.startswith(prefix)
variants=json.loads(data[len(prefix):].rstrip().rstrip(';'))
dest=a/'images'/'astra'
dest.mkdir(parents=True,exist_ok=True)
paths=[]
for tier,img in enumerate(variants):
    im=Image.open(BytesIO(base64.b64decode(img.partition(',')[2]))).convert('RGB')
    name=str(tier)+'.jpg'
    im.save(dest/name,'JPEG',quality=89,subsampling=0,optimize=True)
    paths.append('images/astra/'+name)
astra.write_text(prefix+json.dumps(paths,separators=(',',':'))+';',encoding='utf-8')

p=a/'adventure_v73.js'
s=p.read_text(encoding='utf-8')
def change(before,after,number=1):
    global s
    assert s.count(before)==number, (before[:50],s.count(before))
    s=s.replace(before,after)

change('ABC QUEST v7.3:','ABC QUEST v7.4:')
change('const QUEST_VERSION=4;','const QUEST_VERSION=5;')
change('const WIN_REWARD_TROPHIES=8, WIN_REWARD_CREDITS=12;',
 'const WIN_REWARD_TROPHIES=6, WIN_REWARD_CREDITS=12;\n'+
 'const EXTRA_REWARD_TROPHIES=3, EXTRA_REWARD_CREDITS=6;\n'+
 'const ALL_WORLD_REWARD_TROPHIES=3, ALL_WORLD_REWARD_CREDITS=6;\n'+
 'const ALL_WORLD_EXTRA_TROPHIES=2, ALL_WORLD_EXTRA_CREDITS=3;')
change('const REWARD_TROPHIES_LETTER=8,REWARD_CREDITS_LETTER=6;',
 'const REWARD_TROPHIES_LETTER=4,REWARD_CREDITS_LETTER=6;')
change('if(slot===2)return {letters:Math.ceil(n*.65),wins:4,days:2,modes:2};\n return {letters:n,wins:7,days:2,modes:3};',
 'if(slot===2)return {letters:Math.ceil(n*.65),wins:5,days:2,modes:2};\n return {letters:n,wins:10,days:3,modes:3};')
change('const need={wins:base.wins+[0,2,5,9][tier],days:[0,2,3,4][tier],modes:[0,1,3,4][tier]};',
 'const need={wins:base.wins+[0,2,4,6][tier],days:[0,2,3,4][tier],modes:[0,1,3,4][tier]};')
change('return !!progress.questClaimedHeroes?.[prevLast] && heroCheckpoint(i-1,3).ready;',
 'return !!progress.questClaimedHeroes?.[prevLast]; // keep earned worlds open')
change(' if(!Number.isFinite(progress.legacyGloryFloor))progress.legacyGloryFloor=0;',
 ' if(!Number.isFinite(progress.legacyGloryFloor))progress.legacyGloryFloor=0;\n'+
 ' if(safeInt(progress.questVersion)<QUEST_VERSION)progress.questVersion=QUEST_VERSION;')
change('st.wins/7','st.wins/10')
change('st.days/2','st.days/3')
change(chr(36)+'{st.wins}/7',chr(36)+'{Math.min(st.wins,10)}/10',3)
change('$'+'{st.days}/2','$'+'{Math.min(st.days,3)}/3',2)
change('עד 4 ניצחונות מזכים ביום בכל עולם. משחקים רגילים ממשיכים לפעול ללא הגבלה.',
 '4 ניצחונות ראשונים ביום מקדמים את משימות העולם ומעניקים פרס מלא. מהמשחק החמישי מקבלים חצי גביעים וקרדיטים.')
change('A maximum of 4 qualified rounds per world/day count towards hero quests.',
 'The first four qualified wins count for quests; more wins grant half rewards.')
before='''   if(daily<DAILY_QUEST_WIN_LIMIT){
    records.push({date,mode,score:correct,total:length});
    progress.worldRecords[world].wins=records;
    starsEarned=WIN_REWARD_TROPHIES;
    creditsEarned=WIN_REWARD_CREDITS;
    progress.questXP+=5;
    recorded=true;
   }
  }else if(qualified&&world==='all'){
   const key='all:'+date,n=safeInt(progress.questDailyRewards[key]);
   if(n<2){progress.questDailyRewards[key]=n+1;starsEarned=4;creditsEarned=6;}
  }'''
after='''   if(daily<DAILY_QUEST_WIN_LIMIT){
    records.push({date,mode,score:correct,total:length});
    progress.worldRecords[world].wins=records;
    starsEarned=WIN_REWARD_TROPHIES;
    creditsEarned=WIN_REWARD_CREDITS;
    progress.questXP+=5;
    recorded=true;
   }else{
    starsEarned=EXTRA_REWARD_TROPHIES;
    creditsEarned=EXTRA_REWARD_CREDITS;
   }
  }else if(qualified&&world==='all'){
   const key='all:'+date,n=safeInt(progress.questDailyRewards[key]);
   progress.questDailyRewards[key]=n+1;
   starsEarned=n<2?ALL_WORLD_REWARD_TROPHIES:ALL_WORLD_EXTRA_TROPHIES;
   creditsEarned=n<2?ALL_WORLD_REWARD_CREDITS:ALL_WORLD_EXTRA_CREDITS;
  }'''
change(before,after)
change("won&&world!=='all'?'🎯 הצלחת! ארבעת הניצחונות המזכים להיום כבר נרשמו. אפשר להמשיך לתרגל ללא הגבלה.':",
 "won&&world!=='all'?'🎯 כל הכבוד! אחרי ארבעה ניצחונות מקבלים חצי פרס, ומחר חוזרים לפרס מלא.':")

begin=s.index('/* Prestige progression —')
end=s.index('\nconst baseHomePage=homePage;',begin)
fame=r'''
/* Trophy-only glory, 24 attainable levels. */
const TROPHY_FAME_THRESHOLDS=Array.from({length:GLORY.length},(_,i)=>
 Math.round(520*Math.pow(i/(GLORY.length-1),1.35)));
for(let i=0;i<GLORY.length;i++)GLORY[i].min=TROPHY_FAME_THRESHOLDS[i];
currentGlory=function(){return [...GLORY].reverse().find(g=>safeInt(progress.stars)>=g.min)||GLORY[0];};
fameTrackHtml=function(){
 const cur=currentGlory(),next=GLORY.find(g=>g.min>safeInt(progress.stars));
 let cards='';
 for(let i=0;i<8;i++){
  const levels=GLORY.slice(i*3,i*3+3),g=levels[0];
  cards+='<div class="fame-tile '+(progress.stars>=g.min?'fame-open':'fame-locked')+'">'+
   '<div class="fame-icon">'+g.icon+'</div><strong>'+g.name.replace(/\s[IV]+$/,'')+
   '</strong><small>'+levels.map(v=>progress.stars>=v.min?'●':'○').join(' ')+
   '</small><span>'+g.min+' 🏆</span></div>';
 }
 return '<section class="fame-road"><div class="fame-head"><div><span class="game-kicker">👑 מסלול התהילה</span>'+
  '<h2>'+cur.icon+' '+cur.name+'</h2></div><span>'+
  (next?(next.min-progress.stars)+' 🏆 לדרגה הבאה':'🏆 הגעת לתהילת השיא!')+
  '</span></div><div class="quest-prestige-info"><span>🏆 '+progress.stars+
  ' גביעים</span><span>'+(next?'הדרגה הבאה ב־'+next.min+' גביעים':'כל הדרגות הושלמו')+
  '</span><span>📅 '+fameDays()+' ימי תרגול</span></div><div class="fame-tiles">'+cards+
  '</div><p>תהילה נקבעת לפי גביעים: 6 לכל ניצחון מלא, 3 לניצחונות נוספים ו־4 ללימוד אות חדשה.</p></section>';
};
'''
s=s[:begin]+fame+s[end:]
change("version:'7.3'","version:'7.4'")
change("prestige:()=>({rank:GLORY.indexOf(currentGlory()),xp:progress.questXP,days:fameDays()}),",
 "prestige:()=>({rank:GLORY.indexOf(currentGlory()),trophies:progress.stars,next:GLORY.find(g=>g.min>progress.stars)?.min??null}),\n fameThresholds:()=>GLORY.map(g=>g.min),")
change('📅 אתגר של כמה ימים','📅 מסע של כ־10 ימים')
p.write_text(s,encoding='utf-8')

(a/'balance_v74.css').write_text('''
.hero.hero-compact{align-items:start}
.hero .home-character{
 align-self:start;justify-self:stretch;height:auto!important;min-height:0!important;
 max-height:none!important;overflow:hidden;border-radius:20px;
 border:2px solid rgba(255,231,150,.75);
 background:linear-gradient(150deg,#2f6cdb,#7031d2);
 box-shadow:0 8px 0 #101c74,0 17px 28px rgba(8,15,60,.34)}
.hero .home-character-img{
 width:100%!important;height:auto!important;max-height:none!important;
 aspect-ratio:1/1.12;object-fit:cover!important;
 object-position:center 14%!important;display:block}
.hero .home-character-name{
 font-size:clamp(13px,3.5vw,20px);line-height:1.2;
 padding:9px 5px 11px;white-space:normal}
@media(max-width:640px){
 .hero.hero-compact{grid-template-columns:minmax(0,1fr) 132px!important;gap:10px;padding:12px;align-items:start}
}
@media(max-width:355px){
 .hero.hero-compact{grid-template-columns:minmax(0,1fr) 112px!important;gap:8px}
 .home-character-name{padding:7px 3px;font-size:13px}
}
''',encoding='utf-8')
gradle=Path('app/build.gradle')
v=gradle.read_text(encoding='utf-8')
assert "versionCode 10" in v and "versionName '7.3-preview'" in v
gradle.write_text(v.replace('versionCode 10','versionCode 11').replace("versionName '7.3-preview'","versionName '7.4-preview'"),encoding='utf-8')
assert len(list((a/'images').rglob('*.jpg')))==64
print('ABC QUEST 7.4 ready: economy, 24 trophy glory levels and 64 JPEG heroes.')
