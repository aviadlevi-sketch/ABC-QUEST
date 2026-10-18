/* ABC QUEST 7.6.9: World-specific stones in addition to credits and trophies. */
const STONES769=[
 {name:'אבני ירח',short:'ירח',icon:'🌙',world:'יער האותיות',color:'#6ec9f2'},
 {name:'אבני מאדים',short:'מאדים',icon:'🔴',world:'עמק הצלילים',color:'#f08665'},
 {name:'אבני שמש',short:'שמש',icon:'☀️',world:'אי האוצרות',color:'#ffca51'},
 {name:'אבני גלקסיה',short:'גלקסיה',icon:'🌌',world:'טירת האלפבית',color:'#b795ff'}
];
const BONUSES769={7:{world:0,count:250},14:{world:1,count:450},21:{world:2,count:700},28:{world:3,count:1000},29:{choice:true,count:700},30:{choice:true,count:900}};
function stonesState769(){
 if(!Array.isArray(progress.worldStones769))progress.worldStones769=[0,0,0,0];
 progress.worldStones769=Array.from({length:4},(_,w)=>safeInt(progress.worldStones769[w]));
 if(!progress.stoneBonusClaims769||typeof progress.stoneBonusClaims769!=='object')progress.stoneBonusClaims769={};
 return progress.worldStones769;
}
stonesState769();save();
const stonePrice769=credits=>Math.round(credits/10);
const heroStonePrice769=id=>stonePrice769(heroCreditPrice(id));
const skinStonePrice769=(id,tier)=>stonePrice769(skinCreditPrice(id,tier));
const stoneBalance769=w=>stonesState769()[w]||0;
function stoneInfo769(w){
 const info=STONES769[w];
 return '<button type="button" class="quest769-info" data-action="quest769-stone-help" data-world="'+w+'" aria-label="מהן '+info.name+' ואיפה משיגים אותן?" title="איפה משיגים '+info.name+'?">ⓘ</button>';
}
function stoneLabel769(w,have,need){return STONES769[w].icon+' '+STONES769[w].name+': '+fmt768(have)+' / '+fmt768(need)+' '+stoneInfo769(w);}
function stoneHelp769(w){
 const info=STONES769[w];document.getElementById('quest769-stone-tip')?.remove();
 const wrap=document.createElement('div');wrap.id='quest769-stone-tip';wrap.className='quest769-tip-layer';
 wrap.innerHTML='<div class="quest769-tip" role="dialog" aria-modal="true" aria-labelledby="quest769-tip-title" dir="rtl">'+
 '<button class="quest769-close" data-action="quest769-close-tip" aria-label="סגירה">✕</button>'+
 '<h2 id="quest769-tip-title">'+info.icon+' '+info.name+'</h2><p>כדי להשיג '+info.name+' משחקים ב<strong>'+info.world+'</strong>.</p>'+
 '<p>בארבעת הניצחונות הראשונים ביום מקבלים <strong>12 אבנים</strong> בכל ניצחון. אחר כך ממשיכים לקבל <strong>6 אבנים</strong> על כל ניצחון!</p>'+
 '<p>אבנים של עולם אחד לא יכולות לקנות דמויות וסקינים בעולם אחר. הגביעים נשארים שלך, הקרדיטים והאבנים משמשים לקנייה.</p>'+
 '<button class="btn gold-button" data-action="quest769-close-tip">הבנתי!</button></div>';
 document.body.appendChild(wrap);wrap.querySelector('.quest769-close').focus();
}
const originalHeroJourney769=heroJourneyRow;
heroJourneyRow=function(h){
 const old=originalHeroJourney769(h),w=worldByHero(h.id),cost=heroStonePrice769(h.id);
 if(ownsHero(h.id)||!cost)return old;
 const have=stoneBalance769(w);
 const stoneCheck=ok768(stoneLabel769(w,have,cost),have>=cost,have>=cost?'מספיק אבנים':'צריך עוד '+fmt768(cost-have)+' אבנים בעולם הזה');
 return old.replace('</div></section>',stoneCheck+'</div></section>');
};
const oldHeroAction769=heroActionHtml;
heroActionHtml=function(h){
 const w=worldByHero(h.id),cost=heroStonePrice769(h.id),have=stoneBalance769(w);
 if(!ownsHero(h.id)&&cost>have&&worldOpen(w)){
  const cp=heroCheckpoint(w,slotByHero(h.id));
  if(cp.ready&&progress.credits>=heroCreditPrice(h.id))return '<button class="btn outline quest768-action" data-action="quest76-world" data-world="'+w+'">'+STONES769[w].icon+' חסרות '+fmt768(cost-have)+' אבנים — לשחק בעולם '+(w+1)+'</button>';
 }
 const html=oldHeroAction769(h);
 if(!ownsHero(h.id)&&cost&&have>=cost)return html.replace('· 🪙 '+fmt768(heroCreditPrice(h.id)),'· 🪙 '+fmt768(heroCreditPrice(h.id))+' + '+STONES769[w].icon+' '+fmt768(cost));
 return html;
};
const oldSkinCard769=skinCard;
skinCard=function(h,tier){
 const old=oldSkinCard769(h,tier);if(tier.id===0)return old;
 const w=worldByHero(h.id),cost=skinStonePrice769(h.id,tier.id),have=stoneBalance769(w),req=skinRequirements(h.id,tier.id);
 const test=ok768(stoneLabel769(w,have,cost),have>=cost,have>=cost?'מספיק אבנים':'צריך עוד '+fmt768(cost-have)+' אבנים בעולם הזה');
 let html=old.replace('<div class="quest768-skin-action">',test+'<div class="quest768-skin-action">');
 if(!ownsSkin(h.id,tier.id)&&cost>have&&req.problems.every(p=>!p.includes('אבני'))){
  if(req.problems.length===0&&progress.credits>=skinCreditPrice(h.id,tier.id))html=html.replace(/<button class="btn gold-button" data-action="buy-skin"[^>]*>[^<]*<\/button>/,'<button class="btn outline quest768-action" data-action="quest76-world" data-world="'+w+'">'+STONES769[w].icon+' לשחק בעולם '+(w+1)+' ולהשיג אבנים</button>');
 }
 if(!ownsSkin(h.id,tier.id)&&cost<=have)html=html.replace('· לקנות את הסקין',' + '+STONES769[w].icon+' '+cost+' · לקנות');
 return html;
};
const previousFinish769=finishPage;
finishPage=function(){
 let html=previousFinish769(),r=progress.lastQuestReward||{};
 if(r.stones>0&&typeof r.scope==='number'){
  const tag='<span class="quest769-earned">'+STONES769[r.scope].icon+' +'+fmt768(r.stones)+' '+STONES769[r.scope].name+'</span>';
  html=html.replace('</div>\n <div class="quest-finish-message">',tag+'</div>\n <div class="quest-finish-message">');
 }
 return html;
};
const oldHome769=homePage;
homePage=function(){
 let html=oldHome769();
 const stones='<section class="quest769-wallet" aria-label="האבנים שלי"><h2>💎 אבני העולם שלי</h2><p>כדי להשיג אבנים, משחקים בעולם המתאים. אפשר לחזור לכל עולם פתוח!</p><div class="quest769-wallet-grid">'+
 STONES769.map((s,w)=>'<div class="quest769-wallet-item"><span>'+s.icon+' '+s.name+' '+stoneInfo769(w)+'</span><strong>'+fmt768(stoneBalance769(w))+'</strong></div>').join('')+'</div></section>';
 html=html.replace('<section class="quest768-today">',stones+'<section class="quest768-today">');
 html=html.replace('מעניקים פרס מלא; אחר כך ממשיכים לתרגל ולקבל חצי פרס.', 'מעניקים פרס מלא ו־12 אבני עולם לכל ניצחון; אחר כך ממשיכים לתרגל, לקבל חצי פרס ו־6 אבנים לכל ניצחון.');
 return html;
};
helpSections768.splice(5,0,
 ['💎 מהן אבני העולם?','לכל עולם יש אבנים משלו: 🌙 ירח בעולם 1, 🔴 מאדים בעולם 2, ☀️ שמש בעולם 3 ו־🌌 גלקסיה בעולם 4. ארבעת הניצחונות הראשונים ביום מעניקים 12 אבנים בכל ניצחון, וכל ניצחון נוסף מעניק 6. האבנים מתקבלות רק במשחקים של אותו עולם.'],
 ['🎭 מה קונים עם אבנים?','לכל דמות ולכל סקין צריך גם קרדיטים וגם אבנים של העולם שלהם, ובנוסף מספיק גביעים והשלמת משימות. מחיר האבנים הוא עשירית ממחיר הקרדיטים. למשל, אסטרה עולה 5,200 קרדיטים ו־520 אבני גלקסיה. אבנים מתבזבזות ברכישה, גביעים לא.'],
 ['🌟 מתי מקבלים מתנות אבנים?','ביום התחברות 7 מקבלים 250 אבני ירח, ביום 14 מקבלים 450 אבני מאדים, ביום 21 מקבלים 700 אבני שמש וביום 28 מקבלים 1,000 אבני גלקסיה. ביום 29 בוחרים 700 אבנים וביום 30 בוחרים 900 אבנים מכל סוג שאוהבים. אלה מתנות נוספות לקרדיטים ולגביעים!']);
helpSections768[2][1]='משחק של 8 שאלות. לפחות 6 נכונות? ניצחון! ארבעת הניצחונות הראשונים בכל עולם ביום מעניקים כל אחד 120 קרדיטים, 220 גביעים ו־12 אבני אותו עולם.';
helpSections768[3][1]='הניצחון החמישי והלאה באותו עולם עדיין מעניק 60 קרדיטים, 110 גביעים ו־6 אבני אותו עולם! אפשר להמשיך לתרגל כמה שרוצים.';
const originalsRewardPage769=window.ABCQuestRewards766.page;
function bonusAlready769(day){return !!progress.stoneBonusClaims769?.[day]}
function bonusReady769(day){return Boolean(BONUSES769[day]&&progress.rewards766?.loginDates?.length>=day&&!bonusAlready769(day));}
window.ABCQuestRewards766.page=function(){
 let html=originalsRewardPage769();
 html=html.replace(/(<button class="quest766-day [\s\S]*?data-day="(\d+)"[\s\S]*?<\/button>)/g, (tile,all,number)=>{
  const day=Number(number),info=BONUSES769[day];if(!info)return tile;
  const ready=bonusReady769(day),already=bonusAlready769(day),reward='<span class="quest769-bonus-label">'+(info.choice?'💎 '+info.count+' אבנים לבחירה':STONES769[info.world].icon+' '+fmt768(info.count)+' '+STONES769[info.world].name)+'</span>';
  let changed=tile.replace('</button>',reward+'</button>').replace('🎁','🪙');
  if(ready){changed=changed.replace(' disabled','').replace('🔒','💎 לאסוף אבנים').replace('✓ נאסף','💎 לאסוף אבנים');}
  if(already&&progress.rewards766?.loginClaims?.[day])changed=changed.replace('✓ נאסף','✓ כולל אבנים');
  return changed;
 });
 return html;
};
function bonusSelect769(day){
 document.getElementById('quest769-choice')?.remove();
 const reward=BONUSES769[day];if(!reward||!bonusReady769(day))return;
 const spent=w=>WORLD_HEROES[w].reduce((sum,id)=>sum+(!ownsHero(id)?heroStonePrice769(id):0)+[1,2,3].reduce((acc,t)=>acc+(!ownsSkin(id,t)?skinStonePrice769(id,t):0),0),0);
 const recommendations=STONES769.map((s,w)=>Math.max(0,spent(w)-stoneBalance769(w)));
 const recommended=recommendations.indexOf(Math.max(...recommendations));
 const el=document.createElement('div');el.id='quest769-choice';el.className='quest769-tip-layer';
 el.innerHTML='<div class="quest769-tip quest769-choice" dir="rtl" role="dialog" aria-modal="true"><button class="quest769-close" data-action="quest769-close-choice">✕</button><h2>💎 מתנת יום '+day+'!</h2><p>בחרו סוג אחד של אבנים. תקבלו <strong>'+fmt768(reward.count)+'</strong> אבנים מהסוג הזה.</p><div class="quest769-choices">'+STONES769.map((s,w)=>'<button class="quest769-choice-item" data-action="quest769-select-bonus" data-day="'+day+'" data-world="'+w+'"><strong>'+s.icon+' '+s.name+'</strong><small>יש לי '+fmt768(stoneBalance769(w))+(w===recommended?' · כדאי לי לבחור!':'')+'</small></button>').join('')+'</div><p>אפשר לבחור גם אבנים של עולם שעדיין לא פתחת. הן יישמרו עבורך.</p></div>';
 document.body.appendChild(el);el.querySelector('.quest769-close').focus();
}
function bonusGrant769(day,chosen){
 stonesState769();const b=BONUSES769[day];
 if(!b||bonusAlready769(day)||progress.rewards766?.loginDates?.length<day)return false;
 const w=b.choice?chosen:b.world;
 if(!Number.isInteger(w)||w<0||w>3)return false;
 if(!progress.rewards766?.loginClaims?.[day]){if(!window.ABCQuestRewards766.claimLogin(day))return false;}
 progress.worldStones769[w]+=b.count;
 progress.stoneBonusClaims769[day]={world:w,amount:b.count,claimedAt:Date.now()};
 save();document.getElementById('quest769-choice')?.remove();render();
 const overlay=document.querySelector('.quest766-reward-overlay .quest766-reward-dialog');
 if(overlay){const old=overlay.querySelector('.quest769-earned-bonus');old?.remove();const p=document.createElement('p');p.className='quest769-earned-bonus';p.textContent=STONES769[w].icon+' +'+b.count+' '+STONES769[w].name;overlay.insertBefore(p,overlay.querySelector('button'));}
 else showToast('✨ קיבלת '+b.count+' '+STONES769[w].name+'!');
 return true;
}
const oldAndroidBack769=window.abcAndroidBack;
window.abcAndroidBack=function(...args){
 if(document.getElementById('quest769-choice')){document.getElementById('quest769-choice').remove();return true;}
 if(document.getElementById('quest769-stone-tip')){document.getElementById('quest769-stone-tip').remove();return true;}
 return typeof oldAndroidBack769==='function'?oldAndroidBack769(...args):false;
};
document.addEventListener('click',e=>{
 const el=e.target.closest?.('[data-action]');
 if(e.target.id==='quest769-stone-tip'||el?.dataset.action==='quest769-close-tip'){e.preventDefault();e.stopPropagation();document.getElementById('quest769-stone-tip')?.remove();return;}
 if(e.target.id==='quest769-choice'||el?.dataset.action==='quest769-close-choice'){e.preventDefault();e.stopPropagation();document.getElementById('quest769-choice')?.remove();return;}
 if(!el)return;
 const action=el.dataset.action;
 if(action==='quest769-stone-help'){e.preventDefault();e.stopPropagation();stoneHelp769(Number(el.dataset.world));return;}
 if(action==='quest769-select-bonus'){e.preventDefault();e.stopPropagation();bonusGrant769(Number(el.dataset.day),Number(el.dataset.world));return;}
 if(action==='reward766-claim-login'&&BONUSES769[Number(el.dataset.day)]){
  e.preventDefault();e.stopPropagation();const day=Number(el.dataset.day);
  if(!bonusReady769(day))return;
  if(BONUSES769[day].choice)bonusSelect769(day);else bonusGrant769(day,BONUSES769[day].world);
 }
},true);
document.addEventListener('keydown',e=>{
 if(e.key!=='Escape')return;
 const dialog=document.getElementById('quest769-choice')||document.getElementById('quest769-stone-tip');
 if(dialog){e.preventDefault();e.stopImmediatePropagation();dialog.remove();}
},true);
window.ABCQuestWorldStones769={version:'7.6.9',prices:{hero:heroStonePrice769,skin:skinStonePrice769},balances:()=>[...stonesState769()],reward:day=>BONUSES769[day]||null,isClaimed:bonusAlready769,claim:bonusGrant769,openChoice:bonusSelect769,help:stoneHelp769};
console.info('[ABC QUEST 7.6.9] 4 world gems, 12/6 per win, 10:1 prices, 4000 gem day bonuses.');
