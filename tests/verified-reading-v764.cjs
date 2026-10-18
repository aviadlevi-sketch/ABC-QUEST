'use strict';
// Regression tests for microphone-verified ABC QUEST reading.
// Run: node tests/verified-reading-v764.cjs
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const code=fs.readFileSync(process.argv[2]||'android-patches/reading-v764.js','utf8');
let starts=0,awards=0,samples=0;
const game={question:{type:'read',sequence:['A','B','C'],answered:false},at:0,length:8,correct:0};
const env={
 game,page:'game',readingStatus:'',readingMatched:false,readingTranscript:'',recognition:null,
 window:{AndroidBridge:{startSpeechRecognition(){starts++}},ABCQuestOfflineAudio:{stop(){}},isSecureContext:false},
 gamePage(){return 'original-ui';},
 recordReadingSelfCheck(success){awards++;if(success){game.question.answered=true;game.correct++;}},
 beginGame(){game.question={type:'read',sequence:['A','B','C'],answered:false};env.readingStatus='';},
 nextQuestion(){game.at++;game.question={type:'read',sequence:['D','E','F'],answered:false};env.readingStatus='';env.readingMatched=false;},
 stopAudio(){},stopReadingMic(){},render(){},listenReadSequence(){samples++;},setTimeout(fn){fn();},
 readingMatch(input,letters){return String(input).toLowerCase().replace(/[^a-z]/g,'')===letters.join('').toLowerCase();},
 console:{info(){}},
};
vm.createContext(env);vm.runInContext(code,env);
assert.match(env.gamePage(),/read-mic/);
assert.match(env.gamePage(),/read-sample/);
assert.equal(samples,0,'A new question must never auto-play a sample');
env.beginGame('read',0);
assert.equal(samples,0,'Starting reading must never auto-play');
assert.match(env.gamePage(),/read-sample/);
assert.doesNotMatch(env.gamePage(),/read-success|read-practice|הצלחתי|אתרגל שוב/);
env.recordReadingSelfCheck(true);
assert.equal(game.question.answered,false,'Cannot self-approve');
env.nextQuestion();
assert.equal(game.at,0,'Cannot skip unverified reading');
env.startReadingMic();
assert.equal(starts,1);
assert.equal(env.readingStatus,'listening');
env.window.abcNativeSpeechResult(['A B F']);
assert.equal(env.readingStatus,'retry');
assert.equal(game.question.answered,false);
assert.equal(awards,0);
env.startReadingMic();
env.window.abcNativeSpeechResult(['wrong','A B C']);
assert.equal(game.question.answered,true,'Correct alternative verifies');
assert.equal(game.correct,1);
assert.equal(awards,1);
assert.match(env.gamePage(),/next-question/);
assert.match(env.gamePage(),/data-action="read-mic" disabled/);
env.nextQuestion();
assert.equal(game.at,1);
assert.equal(game.question.answered,false);
assert.equal(samples,0,'Next reading question must never auto-play');
env.startReadingMic();
env.window.abcNativeSpeechError();
assert.equal(env.readingStatus,'unsupported');
assert.equal(game.question.answered,false);
game.question={type:'word',target:'A'};
assert.equal(env.gamePage(),'original-ui','Other game modes intact');
console.log('PASS: reading is microphone-verified, never auto-plays examples or skips questions.');
