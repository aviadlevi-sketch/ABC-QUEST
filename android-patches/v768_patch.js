/* ABC QUEST 7.6.8 — economy and child-friendly progression UI.
   Inject inside the existing adventure_v73.js closure. No save reset. */
const ECONOMY_768={
 heroGates:[[0,2600,8500,14000],[19000,25000,32000,43000],[48000,57000,67000,79000],[84000,95000,108000,125000]],
 skinPrices:[[0,600,1000,1500],[0,900,1300,1800],[0,1200,1600,2100],[0,1500,1900,2400]]
};
for(let w=0;w<4;w++){
 for(let slot=0;slot<4;slot++)HERO_TROPHY_GATES[w][slot]=ECONOMY_768.heroGates[w][slot];
 for(let tier=0;tier<4;tier++)SKIN_CREDIT_PRICES[w][tier]=ECONOMY_768.skinPrices[w][tier];
}
for(const h of HEROES)h.minTrophies=heroTrophyGate(h.id);
const fmt768=n=>Number(n||0).toLocaleString('en-US');
const ok768=(label,done,detail='')=>'<div class="quest768-condition '+(done?'is-done':'is-missing')+'"><span class="quest768-condition-icon" aria-hidden="true">'+(done?'✓':'!')+'</span><span>'+label+(detail?'<small>'+detail+'</small>':'')+'</span></div>';
const counts768=(world)=>{
 const c={matching:0,sound:0,word:0,read:0};
 for(const rec of worldRecords(world)){
  const key=['visual','pair'].includes(rec.mode)?'matching':rec.mode;
  if(Object.prototype.hasOwnProperty.call(c,key))c[key]++;
 }
 return c;
};
const daily768=world=>worldRecords(world).filter(r=>r.date===today()).length;
const nextHeroStep768=(h)=>{
 const w=worldByHero(h.id),slot=slotByHero(h.id),cp=heroCheckpoint(w,slot),st=cp.s,need=cp.need;
 if(!worldOpen(w))return {label:'🗺️ קודם פותחים את העולם הקודם',act:'quest76-world',world:Math.max(w-1,0)};
 if(slot>0&&!progress.questClaimedHeroes?.[WORLD_HEROES[w][slot-1]])return {label:'🎭 קודם פותחים את הדמות שלפניי',act:'quest76-hero',hero:WORLD_HEROES[w][slot-1]};
 if(st.letters<need.letters)return {label:'🔤 בואו ללמוד עוד אותיות',act:'quest76-world',world:w};
 if(slot===3){
  const counts=counts768(w);
  for(const [name,mode] of [['matching','visual'],['sound','sound'],['word','word'],['read','read']]){
   if(counts[name]<2)return {label:'🎮 בואו לשחק במשימה שחסרה',act:'quest76-play',world:w,mode};
  }
 }
 if(st.wins<need.wins||st.modes<need.modes)return {label:'🎮 בואו להתאמן בעולם הזה',act:'quest76-world',world:w};
 if(st.days<need.days)return {label:'📅 נחזור מחר לעוד יום תרגול',act:'quest76-world',world:w};
 if(progress.stars<heroTrophyGate(h.id))return {label:'🏆 נשחק ונצבור עוד גביעים',act:'quest76-world',world:w};
 if(progress.credits<heroCreditPrice(h.id))return {label:'🪙 נשחק ונאסוף קרדיטים',act:'quest76-world',world:w};
 return {label:'🎉 אפשר לרכוש את הדמות!',act:'quest-claim-hero',hero:h.id};
};
const action768=(step,classes='outline')=>{
 const attrs=' data-action="'+step.act+'"'+(step.world!==undefined?' data-world="'+step.world+'"':'')+(step.hero?' data-hero="'+step.hero+'"':'')+(step.mode?' data-mode="'+step.mode+'"':'');
 return '<button class="btn '+classes+' quest768-action"'+attrs+'>'+step.label+'</button>';
};

heroJourneyRow=function(h){
 const w=worldByHero(h.id),slot=slotByHero(h.id),cp=heroCheckpoint(w,slot),s=cp.s,n=cp.need;
 const owned=ownsHero(h.id),price=heroCreditPrice(h.id),gate=heroTrophyGate(h.id);
 if(owned)return '<div class="quest768-status-owned">✅ '+h.name+' כבר באוסף שלך! אפשר לשחק איתה בכל עולם פתוח.</div>';
 let conditions=[];
 conditions.push(ok768('העולם פתוח',worldOpen(w),worldOpen(w)?STAGES[w].name:'קודם מסיימים את העולם הקודם'));
 if(slot>0)conditions.push(ok768('הדמות הקודמת נפתחה',!!progress.questClaimedHeroes?.[WORLD_HEROES[w][slot-1]]));
 if(n.letters)conditions.push(ok768('אותיות בעולם: '+s.letters+' מתוך '+n.letters,s.letters>=n.letters));
 if(n.wins)conditions.push(ok768('ניצחונות בעולם: '+s.wins+' מתוך '+n.wins,s.wins>=n.wins));
 if(n.days)conditions.push(ok768('ימי תרגול: '+s.days+' מתוך '+n.days,s.days>=n.days));
 if(n.modes)conditions.push(ok768('סוגי משחק: '+s.modes+' מתוך '+n.modes,s.modes>=n.modes));
 if(slot===3){
  const counts=counts768(w);
  conditions.push(ok768('4 סוגי המשחק הושלמו',Object.values(counts).every(n=>n>=2),'צריך 2 ניצחונות בהתאמה, בשמיעה, במילים ובקריאה'));
 }
 conditions.push(ok768('גביעים: '+fmt768(progress.stars)+' מתוך '+fmt768(gate),progress.stars>=gate,progress.stars>=gate?'מספיק גביעים':'עוד '+fmt768(gate-progress.stars)+' גביעים'));
 conditions.push(ok768('קרדיטים: '+fmt768(progress.credits)+' מתוך '+fmt768(price),progress.credits>=price,progress.credits>=price?'מספיק קרדיטים':'עוד '+fmt768(price-progress.credits)+' קרדיטים'));
 const done=conditions.filter(t=>t.includes('is-done')).length;
 return '<section class="quest768-guide" aria-label="איך פותחים את '+h.name+'"><div class="quest768-guide-top"><strong>🎯 איך משיגים את '+h.name+'?</strong><small>'+done+' מתוך '+conditions.length+' תנאים הושלמו</small></div><p class="quest768-intro">🟢 ירוק — סיימת! 🔴 אדום — עוד משימה קטנה.</p><div class="quest768-conditions">'+conditions.join('')+'</div></section>';
};
heroActionHtml=function(h){
 const w=worldByHero(h.id),cp=heroCheckpoint(w,slotByHero(h.id));
 if(ownsHero(h.id))return '<button class="btn teal" data-action="equip-hero" data-hero="'+h.id+'" '+(progress.equippedHero===h.id?'disabled':'')+'>'+(progress.equippedHero===h.id?'✓ הדמות שאני משחק איתה':'⭐ לשחק עם '+h.name)+'</button>';
 if(worldOpen(w)&&cp.ready&&progress.credits>=heroCreditPrice(h.id))return '<button class="btn gold-button" data-action="quest-claim-hero" data-hero="'+h.id+'">🎁 לרכוש את '+h.name+' · 🪙 '+fmt768(heroCreditPrice(h.id))+'</button>';
 return action768(nextHeroStep768(h));
};

const skinStep768=(h,tier,req,price)=>{
 const world=worldByHero(h.id);
 if(!worldOpen(world))return {label:'🗺️ קודם לפתוח את העולם',act:'quest76-world',world:Math.max(0,world-1)};
 if(!ownsHero(h.id))return {label:'🎭 קודם להשיג את '+h.name,act:'quest76-hero',hero:h.id};
 if(req.s.days<req.need.days&&daily768(world)>=4)return {label:'📅 ממשיכים מחר בעולם הזה',act:'quest76-world',world};
 if(req.s.wins<req.need.wins||req.s.modes<req.need.modes||req.s.days<req.need.days)return {label:'🎮 בואו למשימות בעולם הזה',act:'quest76-world',world};
 if(progress.stars<req.need.trophies)return {label:'🏆 צוברים עוד גביעים',act:'quest76-world',world};
 if(progress.credits<price)return {label:'🪙 צוברים עוד קרדיטים',act:'quest76-world',world};
 return {label:'✨ לרכוש את הסקין',act:'buy-skin',hero:h.id,tier:tier.id};
};
skinCard=function(h,tier){
 const own=ownsSkin(h.id,tier.id),equipped=ownsHero(h.id)&&equippedTier(h.id)===tier.id;
 const req=skinRequirements(h.id,tier.id),price=skinCreditPrice(h.id,tier.id),w=worldByHero(h.id);
 const canBuy=!own&&req.ready&&progress.credits>=price;
 if(tier.id===0)return '<article class="skin-card skin-base quest768-skin"><div class="skin-card-art">'+artHtml(h.id,0)+'<span class="skin-card-badge">מראה מקורי</span></div><div class="skin-card-info"><h3>'+HERO_SKIN_NAMES[h.id][0]+'</h3><p>🎁 מקבלים יחד עם הדמות, בלי תשלום נוסף.</p></div></article>';
 const stages=[
  ok768('קודם משיגים את '+h.name,ownsHero(h.id)),
  ok768('ניצחונות: '+req.s.wins+'/'+req.need.wins,req.s.wins>=req.need.wins),
  ok768('ימים שונים: '+req.s.days+'/'+req.need.days,req.s.days>=req.need.days),
  ok768('סוגי משחק: '+req.s.modes+'/'+req.need.modes,req.s.modes>=req.need.modes),
  ok768('גביעים: '+fmt768(progress.stars)+'/'+fmt768(req.need.trophies),progress.stars>=req.need.trophies),
  ok768('קרדיטים: '+fmt768(progress.credits)+'/'+fmt768(price),progress.credits>=price)
 ];
 const step=skinStep768(h,tier,req,price);
 const button=own?'<button class="btn teal" data-action="equip-skin" data-hero="'+h.id+'" data-tier="'+tier.id+'" '+(equipped?'disabled':'')+'>'+(equipped?'✓ הסקין שלי':'✨ ללבוש את הסקין')+'</button>':
  canBuy?'<button class="btn gold-button" data-action="buy-skin" data-hero="'+h.id+'" data-tier="'+tier.id+'">🪙 '+fmt768(price)+' · לקנות את הסקין</button>':action768(step);
 return '<article class="skin-card skin-'+tier.rarity+' quest768-skin"><div class="skin-card-art">'+artHtml(h.id,tier.id)+'<span class="skin-card-badge">'+rarityLabel(tier.id)+'</span></div><div class="skin-card-info"><h3>'+HERO_SKIN_NAMES[h.id][tier.id]+'</h3><p class="quest768-intro">'+(own?'✅ כבר שלך!':('שחקו ב'+STAGES[w].name+' כדי לפתוח את הסקין. ההתקדמות משותפת לכל הדמויות בעולם.'))+'</p><div class="quest768-conditions">'+stages.join('')+'</div><div class="quest768-skin-action">'+button+'</div></div></article>';
};
const previousHome768=homePage;
homePage=function(){
 let out=previousHome768();
 const active=[0,1,2,3].filter(w=>worldOpen(w));
 const chips=active.map(w=>{
  const wins=Math.min(4,daily768(w));
  return '<div class="quest768-today-item"><span>'+STAGES[w].emoji+' '+STAGES[w].name+'</span><strong>'+wins+'/4</strong>'+action768({label:wins<4?'🎮 לשחק':'✓ אפשר להמשיך לתרגל',act:'quest76-world',world:w},wins>=4?'teal':'outline')+'</div>';
 }).join('');
 const todayPanel='<section class="quest768-today"><div class="quest768-today-title"><h2>🎯 מה עושים היום?</h2><small>כל ניצחון = לפחות 6 תשובות נכונות מתוך 8</small></div><p>משחקים בכל עולם פתוח. ארבעת הניצחונות הראשונים בכל עולם מקדמים משימות ומעניקים פרס מלא; אחר כך ממשיכים לתרגל ולקבל חצי פרס.</p><div class="quest768-today-grid">'+chips+'</div><button class="quest768-help-link" data-action="quest768-help">❔ לא בטוחים מה לעשות? מדריך קצר</button></section>';
 out=out.replace('<section class="hero hero-compact">',todayPanel+'<section class="hero hero-compact">');
 out=out.replace('<div class="abc-brand-copy"><strong>ABC QUEST</strong>', '<div class="abc-brand-copy"><div class="quest768-brand-name"><strong>ABC QUEST</strong><button class="quest768-help-icon" type="button" data-action="quest768-help" aria-label="מה עושים במשחק? מדריך ABC QUEST" title="איך משחקים?">i</button></div>');
 return out;
};
const helpSections768=[
 ['🎯 מה המטרה?','ללמוד את 26 האותיות באנגלית, לנצח במשחקים, להשיג 16 דמויות ו־48 סקינים, ולגלות ארבעה עולמות.'],
 ['📅 מה כדאי לעשות כל יום?','נכנסים לעולם הפתוח, לומדים אותיות ומשחקים. בכל עולם, ארבעת הניצחונות הראשונים ביום נותנים פרס מלא ומקדמים את משימות הדמויות. אפשר לחזור גם לעולמות ישנים.'],
 ['🎮 מה זה ניצחון?','משחק של 8 שאלות. עניתם נכון על לפחות 6? זה ניצחון! ארבעת הראשונים בכל עולם ביום מעניקים 120 קרדיטים ו־220 גביעים כל אחד.'],
 ['🔁 ומה עם משחקים נוספים?','הניצחון החמישי ואילך באותו עולם לא מוסיף ניצחונות למשימות הדמויות והסקינים באותו יום, אבל עדיין מעניק 60 קרדיטים ו־110 גביעים. תמשיכו להתאמן!'],
 ['🏆 מה הם גביעים?','הגביעים מראים כמה התקדמתם. הם פותחים דמויות, סקינים ודרגות תהילה. הגביעים שלכם לא נעלמים בקניות.'],
 ['🪙 מה הם קרדיטים?','זה כסף המשחק. אוספים קרדיטים מניצחונות ומפרסים, ומשלמים איתם על דמויות ועל סקינים. אין קניות בכסף אמיתי.'],
 ['👑 מה זו תהילה?','ככל שצוברים יותר גביעים, עולים בדרגות תהילה. כשעולים לקבוצת תהילה חדשה, מחכה לכם גם פרס שאפשר לאסוף במסך הפרסים.'],
 ['🎁 איפה מקבלים פרסים?','במסך ״פרסים״: מתנות על התחברות, מתנה על ארבעה ניצחונות ביום (פעם אחת ביום בסך הכול), ומתנות על עלייה בתהילה. צריך ללחוץ כדי לאסוף אותן!'],
 ['🎭 איך פותחים דמויות?','בוחרים דמות ורואים מה הושלם בירוק ומה חסר באדום: אותיות, ניצחונות, ימים שונים, סוגי משחק, גביעים וקרדיטים. רוכשים את הדמות האחרונה בעולם כדי לפתוח את העולם הבא.'],
 ['✨ איך משיגים סקינים?','קודם רוכשים את הדמות. אחר כך מתרגלים בעולם שאליו היא שייכת, גם בימים שונים ובסוגי משחק שונים. המשימות שסיימתם בעולם נחשבות לכל הסקינים באותו עולם. כשהכול ירוק — אפשר לקנות!'],
 ['🎧 למה צריך משחקים שונים?','כדי להכיר אותיות מכל הכיוונים: התאמה, שמיעה, מילים וקריאה בקול. לדמות האחרונה בכל עולם צריך שני ניצחונות מכל סוג.'],
 ['🌐 ומה קורה במשחק ״כל העולמות״?','זה תרגול חופשי נחמד. מקבלים בו פחות גביעים וקרדיטים, אבל הוא לא מחליף משימות של עולם מסוים.']
];
function help768(){
 document.getElementById('quest768-help')?.remove();
 const el=document.createElement('div');el.id='quest768-help';el.className='quest768-modal';
 el.setAttribute('role','dialog');el.setAttribute('aria-modal','true');el.setAttribute('aria-labelledby','quest768-help-title');
 el.innerHTML='<div class="quest768-help-card" dir="rtl"><div class="quest768-help-header"><div><small>🗺️ מדריך להרפתקה</small><h2 id="quest768-help-title">איך משחקים ב־ABC QUEST?</h2><p>הנה כל מה שצריך לדעת כדי להצליח בכל יום!</p></div><button type="button" class="quest768-close" data-action="quest768-close" aria-label="סגירת ההסבר">✕</button></div><div class="quest768-help-body">'+helpSections768.map(([title,txt],i)=>'<section><h3>'+title+'</h3><p>'+txt+'</p></section>').join('')+'</div><div class="quest768-help-footer"><button type="button" class="btn gold-button" data-action="quest768-close">הבנתי! בואו לשחק 🎮</button></div></div>';
 document.body.appendChild(el);
 el.querySelector('.quest768-close')?.focus();
}
function closeHelp768(){document.getElementById('quest768-help')?.remove();}
app.addEventListener('click',e=>{
 const button=e.target.closest('[data-action="quest768-help"]');if(!button)return;
 e.preventDefault();e.stopImmediatePropagation();help768();
},true);
document.addEventListener('click',e=>{
 const modal=document.getElementById('quest768-help');if(!modal)return;
 if(e.target===modal||e.target.closest?.('[data-action="quest768-close"]')){e.preventDefault();closeHelp768();}
},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.getElementById('quest768-help')){e.preventDefault();e.stopImmediatePropagation();closeHelp768();}},true);
const oldAndroidBack768=window.abcAndroidBack;
window.abcAndroidBack=function(...args){
 if(document.getElementById('quest768-help')){closeHelp768();return true;}
 return typeof oldAndroidBack768==='function'?oldAndroidBack768(...args):false;
};
window.ABCQuestEconomy768={version:'7.6.8',data:()=>({heroGates:HERO_TROPHY_GATES.map(x=>[...x]),skinPrices:SKIN_CREDIT_PRICES.map(x=>[...x]),full:WIN_REWARD_CREDITS,extra:EXTRA_REWARD_CREDITS}),modeCounts:counts768,help:help768};
console.info('[ABC QUEST 7.6.8] Economy 120/60; character gates; reduced skin prices; child-friendly help and requirements.');
