/* ABC QUEST 7.6: economy, guided progression and audio-driven learning.
   Injected INSIDE adventure_v73.js IIFE after v7.5 code; no live purchases. */
(function(){
'use strict';
const ECONOMY_76 = 76;
const format76 = x=>Number(x||0).toLocaleString('en-US');
const baseHeroCredits = HERO_CREDIT_PRICES.map(a=>a.slice());
const baseHeroTrophies = HERO_TROPHY_GATES.map(a=>a.slice());
const baseSkinCredits = SKIN_CREDIT_PRICES.map(a=>a.slice());
for(let i=0;i<4;i++){
 for(let j=1;j<4;j++){
  HERO_CREDIT_PRICES[i][j]=baseHeroCredits[i][j]*10;
  HERO_TROPHY_GATES[i][j]=baseHeroTrophies[i][j]*4;
 }
 for(let j=1;j<4;j++)SKIN_CREDIT_PRICES[i][j]=baseSkinCredits[i][j]*5;
}
// Third and fourth worlds (0-based indices 2 and 3): epic (tier 2) and
// legendary (tier 3) skins cost HALF their v7.6 credit price.
// Other skin tiers, other worlds, and ALL trophy gates are unchanged.
for(const world of [2,3]){
 for(const tier of [2,3]){
  SKIN_CREDIT_PRICES[world][tier]=Math.round(SKIN_CREDIT_PRICES[world][tier]/2);
 }
}
// The first hero is no longer given away. Average the previous hero and next
// hero; the first ever hero has no predecessor, so use half the next hero.
for(let i=0;i<4;i++){
 const previousC=i===0?0:HERO_CREDIT_PRICES[i-1][3];
 const previousT=i===0?0:HERO_TROPHY_GATES[i-1][3];
 HERO_CREDIT_PRICES[i][0]=Math.round((previousC+HERO_CREDIT_PRICES[i][1])/2);
 HERO_TROPHY_GATES[i][0]=Math.round((previousT+HERO_TROPHY_GATES[i][1])/2);
}
// v7.6.2 price corrections are in CREDITS (trophy gates remain unchanged).
// Apply AFTER the original 10x scaling and first-world-hero averages so that
// all six user-specified amounts stay EXACT and unrelated heroes keep their prices.
const EXACT_HERO_PRICES_762={luna:2200,rex:2600,nova:2800,mix:3300,kitty:3400,orion:4200};
for(const [id,amount] of Object.entries(EXACT_HERO_PRICES_762)){
 const world=worldByHero(id),slot=slotByHero(id);
 if(!WORLD_HEROES[world]||WORLD_HEROES[world][slot]!==id)throw Error('Unknown hero ID: '+id);
 HERO_CREDIT_PRICES[world][slot]=amount;
}
// Alpha is FREE for every new player; there is no credit or trophy purchase gate.
HERO_CREDIT_PRICES[0][0]=0;
HERO_TROPHY_GATES[0][0]=0;
// Keep legacy/base-store prices synchronized with the quest store and UI.
for(const h of HEROES){
 h.price=heroCreditPrice(h.id);
 h.minTrophies=heroTrophyGate(h.id);
}
FAME_TROPHIES.forEach((val,i)=>{FAME_TROPHIES[i]=val*3;GLORY[i].min=FAME_TROPHIES[i];});
progress.questVersion=ECONOMY_76;
progress.economyVersion=ECONOMY_76;
save();

const MODE_TARGETS=[
 {key:'matching',name:'התאמת אותיות',icon:'🔡',required:2,play:'visual'},
 {key:'sound',name:'זיהוי אות בשמיעה',icon:'🎧',required:2,play:'sound'},
 {key:'word',name:'שמיעת מילים',icon:'🖼️',required:2,play:'word'},
 {key:'read',name:'קריאה בקול',icon:'🎙️',required:2,play:'read'},
];
function modeCounts76(world){
 const modes={matching:0,sound:0,word:0,read:0,mixed:0};
 for(const row of worldRecords(world)){
  if(row.mode==='visual'||row.mode==='pair')modes.matching++;
  else if(Object.prototype.hasOwnProperty.call(modes,row.mode))modes[row.mode]++;
 }
 return modes;
}
const priorWorldStats76=worldStats;
worldStats=function(world){
 const result=priorWorldStats76(world);
 result.modeCounts=modeCounts76(world);
 return result;
};
const priorHeroCheckpoint76=heroCheckpoint;
heroCheckpoint=function(world,slot){
 const info=priorHeroCheckpoint76(world,slot);
 if(slot===3){
  const modes=modeCounts76(world);
  for(const spec of MODE_TARGETS){
   if(modes[spec.key]<spec.required){
    info.unmet.push(spec.icon+' עוד '+(spec.required-modes[spec.key])+' במשחק '+spec.name);
   }
  }
  info.ready=info.unmet.length===0;
 }
 return info;
};
function currentWorld76(){
 for(let i=0;i<4;i++){
  if(!worldOpen(i))return Math.max(0,i-1);
  if(WORLD_HEROES[i].some(id=>!progress.questClaimedHeroes[id]))return i;
 }
 return 3;
}
function recommendedMode76(world){
 const counts=modeCounts76(world);
 for(const type of ['sound','word','read','matching']){
  const goal=MODE_TARGETS.find(x=>x.key===type);
  if(counts[type]<goal.required)return goal;
 }
 return {key:'mixed',name:'מסלול ההפתעות',icon:'🚀',required:2,play:'mixed'};
}
function modeProgress76(world){
 const st=worldStats(world),counts=st.modeCounts;
 const group=MODE_TARGETS.map(m=>{
  const n=counts[m.key],pct=Math.min(100,Math.round(n/m.required*100));
  return '<button class="quest76-mode" data-action="quest76-play" data-world="'+world+
    '" data-mode="'+m.play+'" aria-label="'+m.name+': '+n+' מתוך '+m.required+' משחקים">'+
    '<div class="quest76-mode-title"><b>'+m.icon+' '+m.name+'</b><strong>'+n+'/'+m.required+'</strong></div>'+
    '<span class="quest76-meter"><i style="width:'+pct+'%"></i></span>'+
    '<small>'+(n>=m.required?'✓ הושלם':'עוד '+(m.required-n)+' משחקים להשלמה')+'</small></button>';
 }).join('');
 return '<section class="quest76-mode-dashboard"><div class="quest76-title"><h2>🎯 המשימות שלי בעולם הזה</h2>'+
 '<span>🎮 '+st.wins+'/10 ניצחונות · 📅 '+st.days+'/3 ימים</span></div>'+
 '<p>כדי לעבור עולם: לפחות 2 משחקים מוצלחים מכל סוג, ועוד 2 משחקים לבחירה. בכל משחק צריך לפחות 6 מ־8.</p>'+
 '<div class="quest76-mode-grid">'+group+'</div>'+
 '<div class="quest76-total"><span>סה״כ ניצחונות בעולם</span><span class="quest76-meter"><i style="width:'+Math.min(100,st.wins*10)+'%"></i></span><b>'+st.wins+'/10</b></div></section>';
}
function nextUnclaimedHero76(world){
 return WORLD_HEROES[world].find(id=>!progress.questClaimedHeroes[id])||null;
}
function nextAvailableSkin76(){
 for(const h of HEROES){
  if(!ownsHero(h.id))continue;
  for(let tier=1;tier<=3;tier++){
   if(ownsSkin(h.id,tier))continue;
   const req=skinRequirements(h.id,tier);
   if(req.ready&&progress.credits>=skinCreditPrice(h.id,tier)){
    return {id:h.id,tier,name:HERO_SKIN_NAMES[h.id][tier]};
   }
  }
 }
 return null;
}
function guidance76(){
 const world=currentWorld76(),st=worldStats(world),hId=nextUnclaimedHero76(world);
 const hero=hId?getHero(hId):null;
 const cp=hero?heroCheckpoint(world,slotByHero(hId)):null;
 const skin=nextAvailableSkin76();
 const mode=recommendedMode76(world);
 let message='',primary='',action='quest76-play',modeTarget=mode.play,heroTarget=hId;
 if(hero&&cp.ready&&progress.credits>=heroCreditPrice(hId)){
  message='🎉 '+hero.name+' מוכנ'+(hero.name.endsWith('ה')?'ה':'ה')+' לרכישה! השלמת את כל התנאים.';
  primary='🎭 לראות את '+hero.name+' ולקנות';
  action='quest76-hero';
 }else if(skin){
  message='✨ נפתח סקין חדש: '+skin.name+'! אפשר להיכנס לחנות ולרכוש אותו.';
  primary='🛒 לסקין החדש';
  action='quest76-skin';
  heroTarget=skin.id;
 }else if(hero&&cp.ready){
  const need=Math.max(0,heroCreditPrice(hId)-progress.credits);
  message='המשימות של '+hero.name+' הושלמו! חסרים עוד '+format76(need)+' קרדיטים לרכישה.';
  primary='🎮 ממשיכים לצבור קרדיטים';
 }else if(hero){
  const gaps=cp.unmet.filter(x=>!x.includes('קודם פותחים')).slice(0,2);
  const creditGap=Math.max(0,heroCreditPrice(hId)-progress.credits);
  message='הדמות הבאה: '+hero.name+'. '+(gaps.join(' · ')||'נמשיך במשימות העולם')+
   (creditGap?' · חסרים '+format76(creditGap)+' קרדיטים':'');
  primary=mode.icon+' לשחק: '+mode.name;
 }else{
  message='כל הדמויות נפתחו! אפשר לאסוף סקינים, לתרגל ולעלות בדרגות התהילה.';
  primary=mode.icon+' משחק נוסף';
 }
 const modeDone=MODE_TARGETS.filter(m=>st.modeCounts[m.key]>=m.required).length;
 const trophies=hero?heroTrophyGate(hId):0;
 const credits=hero?heroCreditPrice(hId):0;
 return '<section class="quest76-compass"><div class="quest76-compass-head"><span>🧭 המשימה הבאה שלי</span>'+
  '<strong>'+STAGES[world].emoji+' '+STAGES[world].name+'</strong></div>'+
  '<h2>'+message+'</h2>'+
  '<div class="quest76-task-stats"><span>✅ '+modeDone+'/4 סוגי משחק הושלמו</span>'+
  '<span>🎮 '+st.wins+'/10 ניצחונות</span><span>📅 '+st.days+'/3 ימים</span>'+
  (hero?'<span>🏆 '+format76(progress.stars)+'/'+format76(trophies)+'</span>'+
    '<span>🪙 '+format76(progress.credits)+'/'+format76(credits)+'</span>':'')+'</div>'+
  '<div class="quest76-home-actions"><button class="btn gold-button" data-action="'+action+
  '" data-world="'+world+'" data-mode="'+modeTarget+'" data-hero="'+(heroTarget||'')+'">'+primary+'</button>'+
  '<button class="btn outline" data-action="quest76-world" data-world="'+world+'">📊 לראות את כל המשימות</button></div></section>';
}
const originalHome76=homePage;
homePage=function(){
 let out=originalHome76();
 const h=equippedHero(),tier=equippedTier(h.id);
 const selectedIsOwned=ownsHero(h.id);
 const status=selectedIsOwned?'הדמות שלי · אפשר לשחק איתה בכל עולם':'טרם נרכשה דמות';
 const badge='<span class="quest76-hero-badge">'+
  (selectedIsOwned?rarityLabel(tier):'<span class="quest76-no-hero-tag">🎯 משחקים כדי להשיג דמות</span>')+
  '<small>'+status+'</small></span>';
 out=out.replace('<span class="home-character-name">'+h.name+' ⭐</span>',
  '<span class="home-character-name">'+h.name+'</span>'+badge);
 out=out.replace('<section class="home-actions">',guidance76()+'<section class="home-actions">');
 out=out.replace('data-action="start-smart">🎮 משחק מהיר',
  'data-action="quest76-next-game">🎯 המשימה הבאה');
 return out;
};
const originalStage76=stagePage;
stagePage=function(){
 let out=originalStage76();
 if(!worldOpen(selectedStage))return out;
 out=out.replace('<div class="quest-rule-hint">',modeProgress76(selectedStage)+'<div class="quest-rule-hint">');
 out=out.replace(/(🎮\s*\d+)\/7\b/g,'$1/10');
 out=out.replace(/(📅\s*\d+)\/2\b/g,'$1/3');
 return out;
};
const originalGames76=gamesPage;
gamesPage=function(){
 let out=originalGames76();
 if(typeof gameWorldChoice!=='number')return out;
 const counts=modeCounts76(gameWorldChoice);
 return out.replace(/(<button class="game-mode"[^>]*data-mode="([^"]+)"[^>]*>)([\s\S]*?)(<\/button>)/g,
  function(full,opening,mode,inner,end){
   const key=(mode==='visual'||mode==='pair')?'matching':mode;
   const spec=MODE_TARGETS.find(x=>x.key===key);
   if(!spec)return full;
   const n=counts[key],pct=Math.min(100,Math.round(n/spec.required*100));
   return opening+inner+'<span class="quest76-game-need">'+
    (n>=spec.required?'✅ המשימה הושלמה':'🎯 '+n+'/'+spec.required+' להשלמת העולם')+
    '</span><span class="quest76-meter"><i style="width:'+pct+'%"></i></span>'+end;
  });
};
const originalHeroJourney76=heroJourneyRow;
heroJourneyRow=function(h){
 const base=originalHeroJourney76(h);
 const cp=heroCheckpoint(worldByHero(h.id),slotByHero(h.id));
 const c=Math.max(0,heroCreditPrice(h.id)-progress.credits);
 const t=Math.max(0,heroTrophyGate(h.id)-progress.stars);
 const note=ownsHero(h.id)?'✅ הדמות כבר שלך':
  cp.ready?(c?'🔓 המשימות הושלמו · חסרים '+format76(c)+' קרדיטים לרכישה':
   '🎉 המשימות והמחיר הושלמו! אפשר לרכוש את הדמות.'):
  '🔒 כדי לרכוש את הדמות יש להשלים את המשימות, את הגביעים ואת הקרדיטים.';
 return base+'<p class="quest76-purchase-help">'+note+
  (t?' · חסרים '+format76(t)+' גביעים':'')+'</p>';
};
heroActionHtml=function(h){
 if(ownsHero(h.id))return '<button class="btn teal" data-action="equip-hero" data-hero="'+h.id+'" '+
  (progress.equippedHero===h.id?'disabled':'')+'>'+
  (progress.equippedHero===h.id?'✓ הדמות שלי':'⭐ בחירת דמות')+'</button>';
 const world=worldByHero(h.id),cp=heroCheckpoint(world,slotByHero(h.id));
 const creditGap=Math.max(0,heroCreditPrice(h.id)-progress.credits);
 if(!worldOpen(world)||!cp.ready){
  return '<button class="btn outline" data-action="quest76-world" data-world="'+world+'">🔒 מה חסר לפתיחת '+h.name+'?</button>';
 }
 if(creditGap){
  return '<button class="btn outline" disabled>🪙 חסרים '+format76(creditGap)+' קרדיטים</button>';
 }
 return '<button class="btn gold-button" data-action="quest-claim-hero" data-hero="'+h.id+
  '">🪙 '+format76(heroCreditPrice(h.id))+' · לרכוש את '+h.name+'</button>';
};
const originalCheckpoint76=checkpointCard;
checkpointCard=function(i,id,slot){
 let out=originalCheckpoint76(i,id,slot);
 if(slot===0){
  out=out.replace('פתיחה בכניסה לעולם',
    i===0?'אלפא · מתנה חינמית לכל שחקן':'דמות ראשונה בעולם · דורשת רכישה');
  if(i===0)out=out.replace('דמות ראשונה · אינה בחינם','אלפא · דמות חינמית');
 }
 const cp=heroCheckpoint(i,slot),gap=Math.max(0,heroCreditPrice(id)-progress.credits);
 if(cp.ready&&!ownsHero(id)&&gap){
  out=out.replace('מוכן לקבלה!','המשימות הושלמו · חסרים '+format76(gap)+' קרדיטים');
 }
 return out;
};
const originalFame76=fameTrackHtml;
fameTrackHtml=function(){
 return originalFame76().replace('תהילת השיא ב־60,000 גביעים','תהילת השיא ב־180,000 גביעים');
};
const originalProgress76=progressPage;
progressPage=function(){
 let out=originalProgress76();
 out=out.replace(/(🎮\s*\d+)\/7\b/g,'$1/10');
 out=out.replace(/(📅\s*\d+)\/2\b/g,'$1/3');
 return out;
};
const originalFinish76=finishPage;
finishPage=function(){
 let out=originalFinish76();
 if(game?.mode==='read'){
  out=out.replace('🎙️ יופי של קריאה! זהו תרגול עצמי, ולכן אינו מעניק ניצחון רשמי במסע.',
   '🎙️ יופי של קריאה! ארבעת הניצחונות הראשונים ביום מקדמים גם את מסע העולם.');
 }
 return out;
};
app.addEventListener('click',function(e){
 const target=e.target.closest('[data-action]');
 if(!target)return;
 const act=target.dataset.action;
 if(!['quest76-next-game','quest76-play','quest76-world','quest76-hero','quest76-skin'].includes(act))return;
 e.stopImmediatePropagation();e.preventDefault();
 const world=Number(target.dataset.world);
 const fallback=currentWorld76();
 const w=Number.isInteger(world)&&world>=0&&world<4?world:fallback;
 if(act==='quest76-next-game'||act==='quest76-play'){
  const mode=act==='quest76-next-game'?recommendedMode76(fallback).play:target.dataset.mode;
  if(!worldOpen(w))return showToast('🔒 העולם הזה עדיין נעול');
  gameWorldChoice=w;
  beginGame(mode||'mixed',w);
 }else if(act==='quest76-world'){
  selectedStage=w;page='stage';render();
 }else if(act==='quest76-hero'){
  browsedHeroId=target.dataset.hero;page='heroes';render();
 }else if(act==='quest76-skin'){
  shopHeroId=target.dataset.hero;shopTab='skins';page='shop';render();
 }
},true);

// All purchased heroes and their purchased skins are available in EVERY world.
// World origin governs how rewards are earned, never which avatar can be equipped.
function crossWorldCharacterChooser76(){
 const owned=HEROES.filter(h=>ownsHero(h.id));
 if(!owned.length){
  return '<section class="quest76-roster">'+
   '<h2>🎭 הדמות שלי</h2>'+
   '<div class="quest76-roster-empty">עוד אין לך דמות. אפשר לשחק ולצבור קרדיטים וגביעים עד לרכישת הדמות הראשונה. אין דמויות בהשאלה.</div>'+
   '<button class="btn teal" data-action="navigate" data-page="heroes">לראות את הדמויות שאפשר להשיג</button></section>';
 }
 // Repairs an old save if its selected hero was sold/removed, without
 // granting ownership. Usually already normalized on app startup.
 if(!ownsHero(progress.equippedHero)){
  progress.equippedHero=owned[0].id;
  save();
 }
 const current=equippedHero();
 let roster='<div class="quest76-owned-heroes">';
 for(const h of owned){
  const selected=current.id===h.id;
  roster+='<button class="quest76-owned-hero'+(selected?' chosen':'')+
    '" data-action="equip-hero" data-hero="'+h.id+'" aria-label="בחר את '+h.name+
    ' לשחק בעולם הזה">'+artHtml(h.id,equippedTier(h.id),'quest76-owned-pic')+
    '<span>'+h.name+'</span><small>'+(selected?'✓ הדמות הפעילה':'בחר דמות')+'</small></button>';
 }
 roster+='</div>';
 const tiers=(progress.ownedSkins[current.id]||[0]).filter((x,i,a)=>Number.isInteger(Number(x))&&
   Number(x)>=0&&Number(x)<=3&&a.indexOf(x)===i).map(Number).sort();
 let skins='<div class="quest76-owned-skins">';
 for(const tier of tiers){
  skins+='<button class="quest76-owned-skin'+(equippedTier(current.id)===tier?' chosen':'')+
    '" data-action="equip-skin" data-hero="'+current.id+'" data-tier="'+tier+
    '" '+(equippedTier(current.id)===tier?'disabled':'')+'>'+
    rarityLabel(tier)+' '+(HERO_SKIN_NAMES[current.id]?.[tier]||'סקין')+
    (equippedTier(current.id)===tier?' ✓':'')+'</button>';
 }
 skins+='</div>';
 return '<section class="quest76-roster"><h2>🎭 הדמות שאיתה משחקים</h2>'+
   '<p>אפשר לבחור כאן כל דמות שכבר קנית, מכל עולם קודם, ולהחליף לסקינים שרכשת. הדמות שנבחרה תלווה אותך בכל משחק.</p>'+
   roster+'<h3>✨ הסקינים שכבר רכשתי עבור '+current.name+'</h3>'+skins+'</section>';
}
const earlierStageGlobal76=stagePage;
stagePage=function(){
 const output=earlierStageGlobal76();
 // This is a player-wide locker, not tied to selectedStage or WORLD_HEROES.
 if(!worldOpen(selectedStage))return output;
 return crossWorldCharacterChooser76()+output;
};
const earlierCollectiblePanelGlobal76=collectiblePanel;
collectiblePanel=function(){
 if(ownsHero(progress.equippedHero))return earlierCollectiblePanelGlobal76();
 return '<div class="active-hero-panel quest76-no-hero">'+
  '<div class="active-hero-visual">'+artHtml('unassigned',0,'active-hero-img')+'</div>'+
  '<div class="active-hero-copy"><span class="game-kicker">🎯 עוד אין דמות בבעלותי</span>'+
  '<h2>ממשיכים לצבור קרדיטים</h2>'+
  '<p>אחרי שתרכוש דמות, היא וכל הסקינים שקנית לה יוכלו לשחק בכל העולמות. אין דמויות בהשאלה.</p>'+
  '<button class="btn teal" data-action="navigate" data-page="heroes">🎭 לדמויות שאפשר לרכוש</button>'+
  '</div></div>';
};
// The sidebar must not display the 'common/basic skin' badge for a nonexistent
// hero. Replace it with a neutral progress hint, never a loaned character.
const originalGlobalRender76=render;
render=function(){
 originalGlobalRender76();
 if(!ownsHero(progress.equippedHero)){
  const sidebar=app.querySelector('.sidebar-hero');
  if(sidebar){
   const fakeRarity=sidebar.querySelector('.rarity');
   if(fakeRarity){
    const hint=document.createElement('small');
    hint.className='quest76-no-hero-tag';
    hint.textContent='עוד אין דמות בבעלותי';
    fakeRarity.replaceWith(hint);
   }
  }
 }
};
window.ABCQuestCrossWorldHeroes={
 isAvailableInWorld:function(heroId,worldIndex){
  return Number.isInteger(worldIndex)&&worldIndex>=0&&worldIndex<4&&ownsHero(heroId);
 },
 purchasedHeroes:()=>HEROES.filter(h=>ownsHero(h.id)).map(h=>h.id),
 purchasedSkins:id=>ownsHero(id)?[...(progress.ownedSkins[id]||[0])]:[],
 equipped:()=>ownsHero(progress.equippedHero)?progress.equippedHero:null,
};

window.ABCQuestVersion76={
 version:'7.6.2',
 economy:()=>({heroes:HERO_CREDIT_PRICES.map(x=>x.slice()),trophies:HERO_TROPHY_GATES.map(x=>x.slice()),
  skins:SKIN_CREDIT_PRICES.map(x=>x.slice()),fameMax:GLORY[GLORY.length-1].min}),
 modeGoals:()=>MODE_TARGETS.map(x=>({key:x.key,needed:x.required})),
 modeStatus:world=>modeCounts76(world),
};
console.info('[ABC QUEST 7.6.2] Free Alpha, six exact hero credit prices and all-world purchases.');
})();