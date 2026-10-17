/* ABC QUEST 7.6: Local MP3 speech only. All 26 names + 26 phonemes
 * + 156 word placements ship in Android assets/audio. No online access/TTS.
 * Original approved metallic X is the single intentionally retained exception.
 */
(function(){
'use strict';
const tracks=window.ABC_QUEST_AUDIO||{names:{},phonemes:{},words:{}};
let currentClip=null;
let batch=0;
function stopClip(){
 batch++;
 if(currentClip){try{currentClip.pause();currentClip.currentTime=0;}catch(e){}currentClip=null;}
 try{stopAudio();}catch(e){}
}
function slug(value){
 return String(value||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
}
function playFile(path,whenDone){
 if(!soundOn){if(typeof showToast==='function')showToast('🔇 הקול כבוי');return;}
 stopClip();
 if(!path){showToast('🔊 קובץ השמע אינו זמין');return;}
 const ticket=batch;
 try{
  const a=new Audio(path);
  currentClip=a;
  a.preload='auto';
  a.volume=1;
  a.onended=()=>{if(batch===ticket){currentClip=null;if(whenDone)whenDone(ticket);}};
  a.onerror=()=>{if(batch===ticket){currentClip=null;showToast('לא ניתן לפתוח את ההקלטה המקומית');}};
  const p=a.play();
  if(p&&p.catch)p.catch(()=>{if(batch===ticket)showToast('לחצו שוב על השמע 🔊');});
 }catch(e){showToast('לא ניתן לנגן את ההקלטה');}
}
playAudio=function(letter,kind){
 const l=String(letter||'').toUpperCase();
 let src;
 if(kind==='name')src=tracks.names?.[l];
 else if(kind==='sound')src=tracks.phonemes?.[l];
 else {
  const word=locate(l)?.word||'';
  src=tracks.words?.[slug(word)];
 }
 playFile(src);
};
playVocabulary=function(letter,index){
 const name=String(WORD_BANK?.[String(letter||'').toUpperCase()]?.[index]?.word||'');
 playFile(tracks.words?.[slug(name)]);
};
speakWord=function(word){playFile(tracks.words?.[slug(word)]);};
listenReadSequence=function(){
 if(!game||page!=='game'||game.question?.type!=='read')return;
 const sequence=(game.question.sequence||[]).slice();
 if(!soundOn){showToast('🔇 הקול כבוי');return;}
 stopClip();
 const token=batch;
 let n=0;
 function next(){
  if(batch!==token||page!=='game'||n>=sequence.length)return;
  const source=tracks.names?.[String(sequence[n++]).toUpperCase()];
  if(!source){showToast('🔊 שם האות חסר');return;}
  try{
   const a=new Audio(source);
   currentClip=a;
   a.preload='auto';
   a.volume=1;
   a.onended=()=>{if(batch===token){currentClip=null;next();}};
   a.onerror=()=>{if(batch===token){currentClip=null;showToast('בעיה בניגון האות');}};
   const p=a.play();
   if(p&&p.catch)p.catch(()=>{if(batch===token)showToast('לא ניתן לנגן את הדוגמה');});
  }catch(e){showToast('שגיאה בהשמעה');}
 }
 next();
};
window.ABCQuestOfflineAudio={
 version:'7.6',
 counts:()=>({names:Object.keys(tracks.names||{}).length,
  phonemes:Object.keys(tracks.phonemes||{}).length,
  words:Object.keys(tracks.words||{}).length}),
 stop:stopClip
};
})();