/* ABC QUEST 7.2 - Android fixes */
(function () {
  "use strict";
  var debug = !!window.ABC_QUEST_DEBUG;
  function trace() { if (debug) console.debug.apply(console,arguments); }
  stagePercent = function (stage) {
    var letters = stageLetters(Number(stage));
    if (!letters.length) return 0;
    var known = letters.filter(function(l){return Boolean(progress.learned && progress.learned[l.up]);}).length;
    return Math.max(0,Math.min(100,Math.round(known / letters.length * 100)));
  };
  overallPercent = function () {return Math.max(0,Math.min(100,Math.round(learnedTotal() / 26 * 100)));};
  mapPage = function () {
    var cards = STAGES.map(function (stage,i) {
      var letters=stageLetters(i), known=letters.filter(function(l){return !!progress.learned[l.up];}).length;
      var pct=stagePercent(i);
      return '<article class="world-card" style="--shade:'+stage.shade+'"><div class="world-head"><div class="world-icon">'+stage.emoji+'</div><div><span class="tag">עולם '+(i+1)+' מתוך '+STAGES.length+'</span><h3>'+stage.name+'</h3></div></div><div class="letters" dir="ltr">'+letters.map(function(l){return l.up;}).join(' · ')+'</div><div class="progress-track" role="progressbar" aria-label="התקדמות ב'+stage.name+'" aria-valuemin="0" aria-valuemax="100" aria-valuenow="'+pct+'"><div class="progress-fill" style="width:'+pct+'%"></div></div><div class="abc-world-progress"><span>🔤 נלמדו <b dir="ltr">'+known+'/'+letters.length+'</b> אותיות</span><span>התקדמות: <b dir="ltr">'+pct+'%</b></span></div><button class="btn small" data-action="open-stage" data-stage="'+i+'">נכנסים ←</button></article>';
    }).join('');
    return '<div class="screen-back"><button class="btn ghost" data-action="navigate" data-page="home">→ 🏠 לבית</button></div><h1 class="screen-title">🗺️ מפת ההרפתקה</h1><div class="world-list">'+cards+'</div>';
  };
  var ledger=progress.claimedLetterRewards && typeof progress.claimedLetterRewards==='object' ? progress.claimedLetterRewards : {};
  LETTERS.forEach(function (l) {if(progress.learned && progress.learned[l.up]) ledger[l.up]=true;});
  progress.claimedLetterRewards=ledger;
  save();
  markLearned = function (up) {
    var l=locate(String(up||'').toUpperCase()); if(!l) return;
    var k=l.up;
    if(ledger[k] || progress.learned[k]) {
      ledger[k]=true;
      if(!progress.learned[k])progress.learned[k]=Date.now();
      save(); return;
    }
    ledger[k]=true; progress.learned[k]=Date.now();
    progress.stars=Math.max(0,Number(progress.stars)||0)+15;
    progress.credits=Math.max(0,Number(progress.credits)||0)+10;
    save();
  };
  var run=0,clip=null,pause=null,stopOriginal=stopAudio;
  function cancelSequence() {
    run++;
    if(pause){clearTimeout(pause);pause=null;}
    if(clip){clip.onended=null;clip.onerror=null;try{clip.pause();clip.currentTime=0;}catch(e){}clip=null;}
  }
  stopAudio=function(){cancelSequence();stopOriginal();};
  listenReadSequence=function(){
    if(!game || page!=='game' || !game.question || game.question.type!=='read')return;
    var seq=(game.question.sequence||[]).slice();
    if(!seq.length)return;
    if(!soundOn){showToast('🔇 הפעילו קול כדי לשמוע');return;}
    stopAudio();
    var session=++run,index=0;
    function next(){
      if(session!==run || index>=seq.length){clip=null;return;}
      var letter=String(seq[index++]).toUpperCase();
      var source=(window.ABC_QUEST_AUDIO && window.ABC_QUEST_AUDIO.names && window.ABC_QUEST_AUDIO.names[letter])||(AUDIO[letter]&&AUDIO[letter].name);
      if(!source){pause=setTimeout(next,170);return;}
      var finished=false;
      function advance(){
        if(finished || run!==session)return;
        finished=true; clip=null; pause=setTimeout(next,170);
      }
      try{
        var player=new Audio(source); clip=player; player.volume=1;
        player.onended=advance;player.onerror=advance;
        var promise=player.play(); if(promise && promise.catch)promise.catch(advance);
      }catch(e){advance();}
    }
    trace('reading',seq.join(' '));next();
  };
  function unlockReveal(kind,id,tier){
    var hero=getHero(id); if(!hero)return;
    var old=document.querySelector('.abc-reveal-overlay');if(old)old.remove();
    var name=kind==='hero'?hero.name:(HERO_SKIN_NAMES[id]&&HERO_SKIN_NAMES[id][tier]||hero.name);
    var title=kind==='hero'?'דמות חדשה נפתחה!':'סקין חדש נפתח!';
    var badge=kind==='hero'?'גיבור חדש!':(['מקורי','נדיר','אפי','אגדי'][tier]||'נדיר');
    var overlay=document.createElement('div');
    overlay.className='abc-reveal-overlay';
    overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label',title);
    overlay.innerHTML='<div class="abc-reveal-rays"></div><div class="abc-reveal-box"><b>✨ ABC QUEST ✨</b><h2>'+title+'</h2><div class="abc-reveal-rarity">🏆 '+badge+'</div><div class="abc-reveal-portrait"><img src="'+skinImage(id,tier)+'" alt="'+name+'"></div><h3>'+name+'</h3><p>איזה יופי! הפרס שלך 🎉</p><button type="button" class="abc-reveal-close">ממשיכים להרפתקה ←</button></div>'+Array.from({length:18},function(_,i){return '<i class="abc-confetti" style="--i:'+i+';--d:'+(i%7*.14)+'s"></i>';}).join('');
    document.body.appendChild(overlay);
    overlay.querySelector('.abc-reveal-close').addEventListener('click',function(){overlay.remove();},{once:true});
    overlay.addEventListener('click',function(e){if(e.target===overlay)overlay.remove();});
    try{overlay.querySelector('.abc-reveal-close').focus({preventScroll:true});}catch(e){}
    try{if(navigator.vibrate)navigator.vibrate([65,45,90]);}catch(e){}
  }
  var originalHero=buyHero,originalSkin=buySkin;
  buyHero=function(id){var had=ownsHero(id);originalHero(id);if(!had&&ownsHero(id))unlockReveal('hero',id,0);};
  buySkin=function(id,tier){tier=Number(tier);var had=ownsSkin(id,tier);originalSkin(id,tier);if(!had&&ownsSkin(id,tier))unlockReveal('skin',id,tier);};
  var beforeRender=render,frame=0;
  function fit(){
    var main=document.querySelector('.main');if(!main)return;
    var modal=document.querySelector('.modal-backdrop .modal');
    if(modal){modal.style.zoom='1';var mh=modal.getBoundingClientRect().height;if(mh>innerHeight-18)modal.style.zoom=Math.max(.78,(innerHeight-18)/mh).toFixed(3);}
    var card=page==='lesson'?main.querySelector('.lesson-card'):page==='game'?main.querySelector('.game-card'):null;
    main.classList.toggle('abc-compact-page',!!card);
    if(!card)return;
    card.style.zoom='1';
    var nav=document.querySelector('.mobile-nav');
    var bottom=nav&&getComputedStyle(nav).display!=='none'?nav.getBoundingClientRect().top:innerHeight;
    var available=bottom-card.getBoundingClientRect().top-12;
    var height=card.getBoundingClientRect().height;
    if(height>available&&available>0)card.style.zoom=Math.max(.78,Math.min(1,available/height)).toFixed(3);
  }
  render=function(){
    var previous=document.querySelector('.main')&&document.querySelector('.main').dataset.abcScreen;
    beforeRender();
    var main=document.querySelector('.main');
    if(main){main.dataset.abcScreen=page;if(previous!==page)main.scrollTop=0;}
    cancelAnimationFrame(frame);
    frame=requestAnimationFrame(fit);
  };
  window.addEventListener('resize',function(){requestAnimationFrame(fit);});
  fit();
  window.ABCQuestV72={version:'7.2',getStagePercent:function(i){return stagePercent(i);},currentProgress:function(){return {stars:progress.stars,credits:progress.credits,claimed:Object.assign({},ledger)};}};
})();