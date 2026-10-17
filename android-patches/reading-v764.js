/* ABC QUEST 7.6.4: microphone-verified reading, no self-reported success.
 * Recognition uses the Android OS speech service, or Web Speech on HTTPS.
 * Transcripts and voice recordings are never stored in the game save.
 */
(function(){
'use strict';
const olderReadingPage764=gamePage;
const olderReadingScore764=recordReadingSelfCheck;
const olderBeginGame764=beginGame;
const olderNextQuestion764=nextQuestion;
let speechAttempt764=0;
function h764(value){
 return String(value||'').replace(/[&<>"']/g,s=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
}
function active764(){return !!(game&&page==='game'&&game.question?.type==='read');}
function supported764(){
 return !!(window.AndroidBridge&&typeof window.AndroidBridge.startSpeechRecognition==='function')||
   (!!(window.SpeechRecognition||window.webkitSpeechRecognition)&&window.isSecureContext===true);
}
canListen=supported764;
function prompt764(){
 switch(readingStatus){
  case 'listening':return '🔴 המיקרופון פתוח. קראו עכשיו את שמות האותיות בקול.';
  case 'verified':return '🌟 מצוין! המערכת זיהתה את רצף האותיות נכון.';
  case 'retry':return readingTranscript?
   '🎧 שמעתי משהו אחר. הקשיבו לדוגמה ונסו לקרוא שוב.':
   '🎧 לא נקלטו מילים. לחצו שוב על המיקרופון.';
  case 'unsupported':return '⚠️ זיהוי דיבור אינו זמין. ודאו ששירות זיהוי דיבור באנגלית מותקן. ייתכן שנדרש אינטרנט.';
  case 'error':return '⚠️ המיקרופון לא הופעל. בדקו את שירות זיהוי הדיבור ונסו שוב.';
  default:return '1. הקשיבו לדוגמה. 2. קראו את שמות האותיות למיקרופון. 3. המערכת תבדוק.';
 }
}
function verifiedGamePage764(){
 const q=game.question;
 const verified=!!q.answered;
 const heard=readingTranscript&&!verified&&readingStatus==='retry'?
  '<small class="read764-heard">המערכת שמעה: <b dir="ltr">'+h764(readingTranscript)+'</b></small>':'';
 const next=verified?'<div class="feedback"><span>✅ כל הכבוד! בדקתי והקריאה נכונה.</span>'+
  '<button class="btn small teal" data-action="next-question">'+
  (game.at===game.length-1?'סיום 🏆':'לאותיות הבאות ←')+'</button></div>':'';
 return '<div class="game-card game-short read764-scene">'+
  '<div class="game-header"><button data-action="quit-game" class="text-link">→ חזרה</button>'+
  '<strong dir="ltr">'+(game.at+1)+' / '+game.length+' &nbsp; 🏆 '+game.correct+'</strong></div>'+
  '<div class="progress-track" style="margin-top:12px"><div class="progress-fill" style="width:'+
   Math.round((game.at+(verified?1:0))*100/game.length)+'%"></div></div>'+
  '<div class="question"><h2>🎙️ קִרְאוּ בְּקוֹל!</h2>'+
  '<div class="reading-sequence" lang="en" dir="ltr">'+q.sequence.map(h764).join(' ')+'</div>'+
  '<p class="reading-helper read764-helper" aria-live="polite">'+prompt764()+'</p>'+heard+
  '<div class="reading-controls read764-controls">'+
  '<button class="btn outline" data-action="read-sample" '+(readingStatus==='listening'?'disabled':'')+'>🔊 לשמוע דוגמה</button>'+
  '<button class="btn teal" data-action="read-mic" '+
  (verified||readingStatus==='listening'||!supported764()?'disabled':'')+'>'+
  (readingStatus==='listening'?'🔴 מקשיבה...':readingStatus==='retry'?'🎤 לנסות שוב':'🎤 לקרוא למיקרופון')+
  '</button></div>'+
  (supported764()?'':'<p class="read-note">אי אפשר להצליח בשאלת קריאה ללא בדיקת המיקרופון. שירות זיהוי דיבור באנגלית נדרש.</p>')+
  '</div>'+next+'</div>';
}
gamePage=function(){
 return active764()?verifiedGamePage764():olderReadingPage764();
};
// The old read-success/read-practice click actions can no longer award points.
recordReadingSelfCheck=function(success){
 if(!active764()||game.question.answered||success!==true||
    readingStatus!=='verified'||readingMatched!==true)return;
 olderReadingScore764(true);
};
function receiveSpeech764(raw){
 if(!active764()||game.question.answered||readingStatus!=='listening')return;
 const options=(Array.isArray(raw)?raw:[raw])
  .filter(s=>typeof s==='string'&&s.trim()).slice(0,5);
 readingTranscript=options[0]||'';
 readingMatched=options.some(s=>readingMatch(s,game.question.sequence));
 readingStatus=readingMatched?'verified':'retry';
 if(readingMatched){
  recordReadingSelfCheck(true);
 }else{
  render(); // Remain on same question, ready for microphone retry.
 }
}
window.abcNativeSpeechResult=receiveSpeech764;
window.abcNativeSpeechError=function(){
 if(!active764()||game.question.answered||readingStatus!=='listening')return;
 readingStatus='unsupported';readingMatched=false;readingTranscript='';render();
};
startReadingMic=function(){
 if(!active764()||game.question.answered||readingStatus==='listening')return;
 if(!supported764()){readingStatus='unsupported';render();return;}
 // Stop the sample before speech recognition to avoid recognizing its audio.
 window.ABCQuestOfflineAudio?.stop?.();
 stopAudio();
 stopReadingMic();
 const attempt=++speechAttempt764;
 readingStatus='listening';readingTranscript='';readingMatched=false;render();
 if(window.AndroidBridge&&typeof window.AndroidBridge.startSpeechRecognition==='function'){
  try{window.AndroidBridge.startSpeechRecognition();}
  catch(e){readingStatus='error';render();}
  return;
 }
 const API=window.SpeechRecognition||window.webkitSpeechRecognition;
 try{
  const r=new API();recognition=r;
  r.lang='en-US';r.interimResults=false;r.continuous=false;r.maxAlternatives=5;
  r.onresult=function(e){
   if(recognition!==r||attempt!==speechAttempt764)return;
   recognition=null;
   receiveSpeech764(Array.from(e.results?.[0]||[]).map(x=>x.transcript));
  };
  r.onerror=function(e){
   if(recognition!==r||attempt!==speechAttempt764)return;
   recognition=null;readingMatched=false;
   readingStatus=['not-allowed','service-not-allowed','network'].includes(e.error)?'unsupported':'retry';
   render();
  };
  r.onend=function(){
   if(recognition!==r||attempt!==speechAttempt764)return;
   recognition=null;if(readingStatus==='listening'){readingStatus='retry';render();}
  };
  r.start();
 }catch(e){recognition=null;readingStatus='error';render();}
};
function sampleOnNewQuestion764(q){
 if(!q||q.type!=='read')return;
 setTimeout(()=>{
  if(active764()&&game.question===q&&!q.answered&&readingStatus===''){
   try{listenReadSequence();}catch(e){/* Example button remains available. */}
  }
 },280);
}
beginGame=function(...args){
 speechAttempt764++;
 olderBeginGame764(...args);
 if(active764())sampleOnNewQuestion764(game.question);
};
nextQuestion=function(...args){
 if(active764()&&!game.question.answered)return; // No skipping unread words.
 speechAttempt764++;
 const last=game?.question;
 olderNextQuestion764(...args);
 if(active764()&&game.question!==last)sampleOnNewQuestion764(game.question);
};
window.ABCQuestVerifiedReading764={
 version:'7.6.4',
 getState:()=>({status:readingStatus,matched:readingMatched,
  active:active764(),answered:!!game?.question?.answered}),
};
console.info('[ABC QUEST 7.6.4] Recognition-verified reading enabled.');
})();