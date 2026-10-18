/* ABC QUEST 7.6.10: show each hero's world stone type/price in character cards and
   explain what stones buy in existing shared info tooltips. */
const priorHeroCard7610=heroCard;
heroCard=function(h,context='heroes'){
 const html=priorHeroCard7610(h,context),world=worldByHero(h.id);
 const stone=STONES769[world],needed=heroStonePrice769(h.id);
 const creditHtml='<span>🪙 '+formatPrice(heroCreditPrice(h.id))+'</span>';
 const needle=creditHtml+'</span><span class="collectible-price">';
 if(!html.includes(needle)){
  console.warn('[ABC QUEST 7.6.10] Hero economy card location changed: '+h.id);
  return html;
 }
 const stoneHtml='<span class="quest7610-stone-card-price" title="'+stone.name+' — משיגים ב'+stone.world+'">'+stone.icon+' '+fmt768(needed)+' '+stone.name+'</span>';
 return html.replace(needle,creditHtml+stoneHtml+'</span><span class="collectible-price">');
};
stoneHelp769=function(w){
 const info=STONES769[w];if(!info)return;
 document.getElementById('quest769-stone-tip')?.remove();
 const overlay=document.createElement('div');
 overlay.id='quest769-stone-tip';overlay.className='quest769-tip-layer';
 overlay.innerHTML='<div class="quest769-tip quest7610-tip" role="dialog" aria-modal="true" aria-labelledby="quest769-tip-title" dir="rtl">'+
  '<button class="quest769-close" data-action="quest769-close-tip" aria-label="סגירה">✕</button>'+
  '<h2 id="quest769-tip-title">'+info.icon+' '+info.name+'</h2>'+
  '<div class="quest7610-tip-purpose"><h3>🛒 מה קונים עם האבנים האלה?</h3><p>את <strong>הדמויות והסקינים של '+info.world+' (עולם '+(w+1)+')</strong> — ורק שלהם. לכל עולם יש אבנים משלו!</p></div>'+
  '<h3>🎮 איך משיגים אותן?</h3><p>משחקים ב<strong>'+info.world+'</strong> ומנצחים: בארבעת הניצחונות הראשונים בכל יום מקבלים <strong>12 '+info.name+'</strong> בכל ניצחון. מהניצחון החמישי מקבלים <strong>6 '+info.name+'</strong> בכל ניצחון נוסף.</p>'+
  '<h3>💎 כמה אבנים צריך לקנייה?</h3><p>על כל 10 קרדיטים במחיר צריך גם אבן אחת. לדוגמה, פריט שעולה 1,200 קרדיטים דורש גם 120 '+info.name+'.</p>'+
  '<p class="quest7610-tip-footer-note">לקנייה צריך גם קרדיטים, מספיק גביעים והשלמת המשימות. הקרדיטים והאבנים יורדים בקנייה; הגביעים נשארים שלך.</p>'+
  '<button class="btn gold-button" data-action="quest769-close-tip">הבנתי! ⭐</button></div>';
 document.body.appendChild(overlay);
 overlay.querySelector('.quest769-close')?.focus();
};
window.ABCQuestHeroCards7610={version:'7.6.10',price:id=>({credits:heroCreditPrice(id),stones:heroStonePrice769(id),world:worldByHero(id)})};
console.info('[ABC QUEST 7.6.10] World stone tooltip purpose and hero card stone requirements.');
