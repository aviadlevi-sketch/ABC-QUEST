/* Offline audio-pack support. If no recorded file is provided, the existing
   audio engine is used. Real licensed recordings can be placed in:
   audio/names/A.mp3, audio/phonemes/B.mp3, audio/words/apple.mp3, etc.
   The build workflow creates audio/manifest.js from any available files.
 */
(function(){
  "use strict";
  const manifest = window.ABC_QUEST_AUDIO || {names:{},phonemes:{},words:{}};
  const existingLetter = playAudio;
  const existingVocab = playVocabulary;
  const existingSound = playLetterPhoneme;
  let recorded = null;
  let operation = 0;

  function safelyStop() {
    if(recorded) { recorded.pause(); recorded.currentTime = 0; recorded = null; }
    try { stopAudio(); } catch(e) { /* keep working */ }
  }
  function tryRecorded(url, fallback) {
    if(!url) { fallback(); return; }
    if(typeof soundOn !== "undefined" && !soundOn) { fallback(); return; }
    const myOperation = ++operation;
    safelyStop();
    const p = new Audio(url);
    recorded = p;
    let failed = false;
    function fail() {
      if(failed || operation !== myOperation) return;
      failed = true;
      if(recorded === p) recorded = null;
      fallback();
    }
    p.addEventListener("error", fail, {once:true});
    const promise = p.play();
    if(promise && typeof promise.catch === "function") promise.catch(fail);
    p.addEventListener("ended",()=>{ if(recorded === p) recorded=null; },{once:true});
  }
  function wordKey(word) {
    return String(word||"").toLowerCase().trim()
      .replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
  }
  playAudio = function(up,kind) {
    const letter=String(up||"").toUpperCase();
    let path="";
    if(kind === "name") path=manifest.names?.[letter];
    if(kind === "sound") path=manifest.phonemes?.[letter];
    tryRecorded(path,()=>existingLetter(up,kind));
  };
  playLetterPhoneme = function(up) {
    const letter=String(up||"").toUpperCase();
    tryRecorded(manifest.phonemes?.[letter],()=>existingSound(up));
  };
  playVocabulary = function(up,index) {
    const word=WORD_BANK?.[up]?.[index]?.word;
    const key=wordKey(word);
    tryRecorded(manifest.words?.[key],()=>existingVocab(up,index));
  };
  const oldSay = sayEnglish;
  sayEnglish = function(word, fallbackUp, fallbackKind, fallbackIndex) {
    const key=wordKey(word);
    if(fallbackKind === "name" && /^[A-Z]$/.test(String(word||""))) {
      return tryRecorded(manifest.names?.[word],()=>oldSay(word,fallbackUp,fallbackKind,fallbackIndex));
    }
    const path=manifest.words?.[key];
    tryRecorded(path,()=>oldSay(word,fallbackUp,fallbackKind,fallbackIndex));
  };
  window.ABCQuestVoicePack = {available: Object.values(manifest.names).length +
      Object.values(manifest.phonemes).length + Object.values(manifest.words).length};
})();
