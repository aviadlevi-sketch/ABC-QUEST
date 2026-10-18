/* ABC QUEST 7.6.6 – 30 cumulative login days and claimable rewards.
 * All rewards are local/offline. User-owned reward ledger lives inside the
 * existing progress save and export, with no reset on skipped days.
 *
 * Login rewards: 1..30 cumulative distinct LOCAL calendar days, claimed once.
 * Daily 4/4: FOUR completed, qualifying world quests across ALL worlds today;
 * one 200-credit + 400-trophy reward per calendar date, claimed once.
 * Fame transitions: exactly the seven crossings from III -> next fame I,
 * with rewards 1000/2000 x3, 1500/3000 x3, 2000/4000 x1.
 * Day 30: 2000/4000 and one persistent profile badge; not awarded twice.
 */
(function(){
'use strict';
const VERSION_766='7.6.6';
const LOGIN_CREDITS_766=[
  75,100,125,150,175,200,800,
  100,125,150,175,200,225,1000,
  125,150,175,200,225,250,1200,
  150,175,200,225,250,275,1600,
  500,2000
];
const DAYS_766=30;
const BADGE_766='אלוף מסע 30 הימים';
const value766=v=>Math.max(0,Math.floor(Number(v)||0));
const format766=x=>value766(x).toLocaleString('en-US');
const rewardData766=day=>{
 if(!Number.isInteger(day)||day<1||day>DAYS_766)return null;
 const credits=LOGIN_CREDITS_766[day-1];
 return {
  day,credits,trophies:day===29?2000:credits*2,
  big:[7,14,21,28,30].includes(day),
  badge:day===30?BADGE_766:null
 };
};
const fameReward766=index=>{
 if(!Number.isInteger(index)||index<1||index>7)return null;
 const first=index<=3,second=index<=6;
 return {index,credits:first?1000:second?1500:2000,
   trophies:first?2000:second?3000:4000,
   threshold:GLORY[index*3].min,
   from:GLORY[(index-1)*3]?.name.replace(/\s[IV]+$/,'')||'תהילה',
   to:GLORY[index*3]?.name.replace(/\s[IV]+$/,'')||'תהילה'
 };
};
function ledger766(){
 if(!progress.rewards766||typeof progress.rewards766!=='object'){
  progress.rewards766={loginDates:[],loginClaims:{},dailyClaims:{},
   fameClaims:{},fameGrantedTrophies:0,badges:[],version:766};
 }
 const p=progress.rewards766;
 if(!Array.isArray(p.loginDates))p.loginDates=[];
 if(!p.loginClaims||typeof p.loginClaims!=='object')p.loginClaims={};
 if(!p.dailyClaims||typeof p.dailyClaims!=='object')p.dailyClaims={};
 if(!p.fameClaims||typeof p.fameClaims!=='object')p.fameClaims={};
 if(!Array.isArray(p.badges))p.badges=[];
 p.fameGrantedTrophies=value766(p.fameGrantedTrophies);
 return p;
}
function loginToday766(){
 const p=ledger766(),date=today();
 if(!/^\d{4}-\d{2}-\d{2}$/.test(date))return p;
 if(!p.loginDates.includes(date)){
  p.loginDates.push(date);
  // The actual first 30 DISTINCT login dates form one, non-resetting journey.
  // Never turn "missing yesterday" into loss of past rewards.
  save();
 }
 return p;
}
function countedWinsToday766(date=today()){
 // Each world session is already validated and capped by the core quest logic.
 // Count only its FIRST four qualifying recorded wins for a given world and day.
 let count=0;
 for(let world=0;world<4;world++){
  count+=worldRecords(world).filter(r=>r&&r.date===date).slice(0,4).length;
 }
 return count;
}
function fameEligibleStars766(){
 // Fame milestone rewards must not create a free chain of additional rewards
 // just because the granted TROPHIES cross the next group boundary.
 return Math.max(0,value766(progress.stars)-ledger766().fameGrantedTrophies);
}
function award766(credits,trophies){
 progress.credits=value766(progress.credits)+value766(credits);
 progress.stars=value766(progress.stars)+value766(trophies);
}
function describe766(r){
 return '🪙 +'+format766(r.credits)+' קרדיטים · 🏆 +'+format766(r.trophies)+' גביעים';
}
function showWin766(title,r){
 if(r.big||r.index){
  const old=document.querySelector('.quest766-reward-overlay');
  old?.remove();
  const overlay=document.createElement('div');
  overlay.className='quest766-reward-overlay';
  overlay.setAttribute('role','dialog');
  overlay.setAttribute('aria-modal','true');
  overlay.innerHTML='<div class="quest766-reward-dialog"><div class="quest766-reward-spark">🎉 🎁 ✨</div>'+
    '<h2>'+title+'</h2><p>'+describe766(r)+'</p>'+
    (r.badge?'<p>🌟 תג חדש בפרופיל: '+BADGE_766+'</p>':'')+
    '<button class="quest767-reward-x" type="button" data-action="reward766-close" aria-label="סגירת פרס">✕</button>'+
    '<button class="btn gold-button" data-action="reward766-close">ממשיכים במסע!</button></div>';
  // The reward overlay is outside #app, so #app's delegated click handler
  // CANNOT receive these clicks. Attach its own handler to the actual overlay.
  overlay.addEventListener('click',function(e){
   const close=e.target.closest?.('[data-action="reward766-close"]');
   if(close||e.target===overlay){
    e.preventDefault();
    overlay.remove();
   }
  });
  document.body.appendChild(overlay);
 }else showToast(title+' · '+describe766(r));
}
function claimLogin766(day){
 const p=loginToday766(),r=rewardData766(day);
 if(!r||day>Math.min(DAYS_766,p.loginDates.length)||p.loginClaims[day])return false;
 p.loginClaims[day]=p.loginDates[day-1]; // immutable earned day/date mapping
 if(r.badge&&!p.badges.includes(r.badge))p.badges.push(r.badge);
 award766(r.credits,r.trophies);save();render();
 showWin766(day===30?'🏆 הושלם מסע 30 הימים!':r.big?'🎁 תיבת יום '+day+' נפתחה!':'🎁 פרס יום '+day+' נאסף!',r);
 return true;
}
function claimDaily766(){
 const date=today(),p=loginToday766();
 if(p.dailyClaims[date]||countedWinsToday766(date)<4)return false;
 p.dailyClaims[date]=true;
 const r={credits:200,trophies:400};
 award766(r.credits,r.trophies);save();render();
 showWin766('🌟 השלמת את כל ארבע המשימות!',r);
 return true;
}
function claimFame766(index){
 const p=loginToday766(),r=fameReward766(index);
 if(!r||p.fameClaims[index]||fameEligibleStars766()<r.threshold)return false;
 // Mark claimed and isolate awarded trophies from future transition eligibility.
 p.fameClaims[index]=true;
 p.fameGrantedTrophies+=r.trophies;
 award766(r.credits,r.trophies);save();render();
 showWin766('👑 עלית לתהילה חדשה!',r);
 return true;
}
const percent766=(a,b)=>Math.min(100,Math.round(Math.min(a,b)*100/b));
function bar766(n,max){
 const capped=Math.max(0,Math.min(max,n));
 return '<span class="quest766-track" role="progressbar" aria-valuenow="'+capped+
  '" aria-valuemin="0" aria-valuemax="'+max+'"><i style="width:'+percent766(capped,max)+'%"></i></span>';
}
function loginTiles766(){
 const p=loginToday766(),days=p.loginDates.length;
 const weeks=[
  {name:'שבוע ראשון',start:1,end:7},
  {name:'שבוע שני',start:8,end:14},
  {name:'שבוע שלישי',start:15,end:21},
  {name:'שבוע רביעי',start:22,end:28},
  {name:'סיום המסע',start:29,end:30}
 ];
 return weeks.map(w=>
  '<section class="quest766-week"><div class="quest766-week-head"><h3>'+w.name+'</h3>'+
  '<small>'+w.start+'–'+w.end+' מתוך 30</small></div><div class="quest766-day-grid '+(w.start===29?'ending':'')+'">'+
  Array.from({length:w.end-w.start+1},(_,n)=>{
   const day=w.start+n,r=rewardData766(day),claimed=!!p.loginClaims[day],ready=day<=days&&!claimed;
   return '<button class="quest766-day '+(claimed?'collected':ready?'ready':'locked')+
    (r.big?' major':'')+'" data-action="reward766-claim-login" data-day="'+day+
    '" '+(!ready?'disabled':'')+' aria-label="יום '+day+', '+format766(r.credits)+
    ' קרדיטים, '+format766(r.trophies)+' גביעים">'+
    '<small>יום '+day+'</small><span class="quest766-day-icon">'+(r.big?'🎁':'🪙')+'</span>'+
    '<b>'+format766(r.credits)+'</b><span class="quest766-trophies">🏆 '+format766(r.trophies)+'</span>'+
    '<em>'+(claimed?'✓ נאסף':ready?'לחצו לדרישה':'🔒')+'</em></button>';
  }).join('')+'</div></section>'
 ).join('');
}
function dailyMissionCard766(home=false){
 const date=today(),n=Math.min(4,countedWinsToday766(date)),p=ledger766(),claimed=!!p.dailyClaims[date],ready=n===4&&!claimed;
 return '<section class="quest766-daily '+(home?'home':'')+'"><div class="quest766-head">'+
  '<div><strong>🎯 ארבע המשימות של היום</strong><p>ארבעה ניצחונות מזכים במשחקי העולם, מכל העולמות יחד</p></div>'+
  '<b>'+n+'/4</b></div>'+
  '<div class="quest766-quest-segments">'+
    Array.from({length:4},(_,i)=>'<span class="'+(i<n?'done':'')+'"></span>').join('')+
  '</div><div class="quest766-daily-foot"><span>🎁 200 🪙 + 400 🏆</span>'+
  '<button class="btn '+(ready?'gold-button':'outline')+'" data-action="reward766-claim-daily" '+
    (ready?'':'disabled')+'>'+(claimed?'✓ כבר נאסף היום':ready?'🎁 דרוש את הפרס!':'עוד '+(4-n)+' משימות לפרס')+
  '</button></div></section>';
}
function fameCards766(){
 const earned=fameEligibleStars766(),p=ledger766();
 return '<section class="quest766-fame"><h2>👑 תיבות מעבר בין תהילות</h2>'+
 '<p>תיבה נפתחת רק במעבר מתהילה III לתהילה הבאה I. מעבר בתוך אותה תהילה אינו מעניק תיבה. כל מעבר מזכה פעם אחת בלבד.</p>'+
 '<div class="quest766-fame-grid">'+Array.from({length:7},(_,i)=>{
  const r=fameReward766(i+1),claimed=!!p.fameClaims[r.index],ready=earned>=r.threshold&&!claimed;
  return '<article class="quest766-fame-card '+(ready?'ready':claimed?'collected':'locked')+'">'+
   '<div class="quest766-fame-visual">'+(claimed?'✅':ready?'🎁':'🔒')+'</div>'+
   '<h3>'+r.from+' ← '+r.to+'</h3>'+
   '<p>🪙 '+format766(r.credits)+' · 🏆 '+format766(r.trophies)+'</p>'+
   '<small>'+(earned>=r.threshold?'היעד הושג':'יעד: '+format766(r.threshold)+' גביעים')+'</small>'+
   '<button class="btn '+(ready?'gold-button':'outline')+'" data-action="reward766-claim-fame" data-transition="'+r.index+
   '" '+(!ready?'disabled':'')+'>'+(claimed?'✓ כבר נאסף':ready?'🎁 דרוש פרס תהילה':'עדיין נעול')+'</button>'+
   '</article>';
 }).join('')+'</div></section>';
}
function nextLogin766(){
 const p=loginToday766(),n=Math.min(p.loginDates.length,DAYS_766);
 for(let day=1;day<=n;day++)if(!p.loginClaims[day])return rewardData766(day);
 return rewardData766(Math.min(n+1,DAYS_766));
}
function rewardsHome766(){
 const p=loginToday766(),days=Math.min(p.loginDates.length,DAYS_766);
 const next=nextLogin766(),claimable=next&&next.day<=days&&!p.loginClaims[next.day];
 const claimableFame=Array.from({length:7},(_,i)=>i+1).filter(i=>
  !p.fameClaims[i]&&fameEligibleStars766()>=fameReward766(i).threshold);
 const claimedQuest=!!p.dailyClaims[today()],n=Math.min(4,countedWinsToday766());
 return '<section class="quest766-home"><div class="quest766-home-title">'+
   '<h2>🎁 הפרסים שלי</h2><button class="btn outline" data-action="navigate" data-page="rewards">כל 30 הפרסים ←</button></div>'+
  '<div class="quest766-home-progress"><strong>📅 יום '+days+'/30 בכניסות</strong>'+
  bar766(days,30)+'</div>'+
  '<div class="quest766-next"><span>'+(!next?'סיימת את מסלול הפרסים!':claimable?
    '🎁 פרס יום '+next.day+' מוכן לדרישה!':'הפרס הבא: יום '+next.day)+
    (next?' · 🪙 '+format766(next.credits)+' 🏆 '+format766(next.trophies):'')+'</span>'+
    (claimable?'<button class="btn gold-button" data-action="reward766-claim-login" data-day="'+next.day+'">דרוש פרס היום!</button>':'')+
  '</div>'+dailyMissionCard766(true)+
  (claimableFame.length?'<button class="btn gold-button quest766-fame-alert" data-action="navigate" data-page="rewards">👑 מחכה לך פרס מעבר תהילה!</button>':'')+
  (claimedQuest?'<small>✓ פרס ארבע המשימות כבר נאסף היום</small>':'')+'</section>';
}
function rewardsPage766(){
 const p=loginToday766(),days=Math.min(p.loginDates.length,DAYS_766);
 const claimed=Object.keys(p.loginClaims).filter(day=>value766(day)<=30).length;
 const badge=p.badges.includes(BADGE_766);
 return '<div class="quest766-page"><div class="quest766-page-header">'+
  '<div><span class="game-kicker">🎁 ABC QUEST REWARDS</span><h1>אוצר הפרסים שלי</h1>'+
  '<p>30 כניסות מצטברות — בלי לאבד אף יום כשמפספסים. בכל יום אפשר לדרוש פרס אחד, ובסופי שבוע מחכה תיבה גדולה.</p></div>'+
  '<span class="quest766-count">📅 '+days+'/30 ימים</span></div>'+
  '<div class="quest766-stats"><span>🪙 '+format766(progress.credits)+' קרדיטים</span>'+
  '<span>🏆 '+format766(progress.stars)+' גביעים</span>'+
  '<span>🎁 '+claimed+'/30 תיבות התחברות נאספו</span></div>'+
  bar766(days,30)+
  (badge?'<div class="quest766-badge">🌟 '+BADGE_766+' — התואר כבר שלך!</div>':'')+
  '<h2>📅 פרסי ההתחברות ל־30 יום</h2>'+
  loginTiles766()+
  '<h2>🎯 פרס ארבע המשימות היומיות</h2>'+
  dailyMissionCard766()+
  fameCards766()+
  '<p class="quest766-note">כל הפרסים נצברים ונשמרים מקומית בחשבון המשחק. ימים שהחמצת לא מאפסים את הרצף. '+
  'רק ניצחונות במשחקי עולם נחשבים לארבע המשימות היומיות. פרסי תהילה ניתנים רק במעבר בין קבוצות תהילה.</p>'+
  '</div>';
}
const previousHome766=homePage;
homePage=function(){
 const html=previousHome766(),rewards=rewardsHome766();
 const compass='<section class="quest76-compass">';
 return html.includes(compass)?html.replace(compass,rewards+compass):rewards+html;
};
const previousProgress766=progressPage;
progressPage=function(){
 const html=previousProgress766();
 const tag=ledger766().badges.includes(BADGE_766)?
   '<div class="quest766-badge">🌟 תג מיוחד: '+BADGE_766+'</div>':'';
 const action='<section class="quest766-achievements"><h2>🎁 הפרסים שלי</h2>'+
  tag+'<p>פרסי התחברות, ארבע משימות יומיות ותיבות מעבר תהילה.</p>'+
  '<button class="btn gold-button" data-action="navigate" data-page="rewards">לפתוח את מסך הפרסים ←</button></section>';
 const anchor='<div class="quest-progress-worlds">';
 return html.includes(anchor)?html.replace(anchor,action+anchor):action+html;
};
const previousRender766=render;
render=function(){
 loginToday766(); // idempotent. Also works for migrated/imported/reset saves.
 previousRender766();
};
// Capture claim interactions so legacy generic clicks can never apply credits
// twice; each claim has an independent, persisted ledger gate.
app.addEventListener('click',function(e){
 const el=e.target.closest('[data-action]');if(!el)return;
 const action=el.dataset.action;
 const options=['reward766-claim-login','reward766-claim-daily',
  'reward766-claim-fame','reward766-close'];
 if(!options.includes(action))return;
 e.preventDefault();e.stopImmediatePropagation();
 if(action==='reward766-close'){
  document.querySelector('.quest766-reward-overlay')?.remove();return;
 }
 if(action==='reward766-claim-login')claimLogin766(Number(el.dataset.day));
 if(action==='reward766-claim-daily')claimDaily766();
 if(action==='reward766-claim-fame')claimFame766(Number(el.dataset.transition));
},true);
// The Android hardware Back button must dismiss a prize overlay before
// navigating away from the rewards page. No awarded prize is rolled back.
const previousAndroidBack766=window.abcAndroidBack;
window.abcAndroidBack=function(...args){
 const dialog=document.querySelector('.quest766-reward-overlay');
 if(dialog){dialog.remove();return true;}
 return typeof previousAndroidBack766==='function'?previousAndroidBack766(...args):false;
};
document.addEventListener('keydown',function(e){
 if(e.key==='Escape'){
  const dialog=document.querySelector('.quest766-reward-overlay');
  if(dialog){e.preventDefault();dialog.remove();}
 }
});
loginToday766();
window.ABCQuestRewards766={
 version:'7.6.7',
 page:rewardsPage766,
 state:()=>({
  loginDates:[...ledger766().loginDates],
  loginClaims:{...ledger766().loginClaims},
  dailyClaims:{...ledger766().dailyClaims},
  fameClaims:{...ledger766().fameClaims},
  badges:[...ledger766().badges],
  dailyWins:countedWinsToday766(),
  earnedFameStars:fameEligibleStars766(),
  credits:progress.credits,trophies:progress.stars
 }),
 loginReward:rewardData766,fameReward:fameReward766,
 claimLogin:claimLogin766,claimDaily:claimDaily766,claimFame:claimFame766,
 };
console.info('[ABC QUEST 7.6.7] Claimable rewards with working modal dismiss and Android Back.');
})();