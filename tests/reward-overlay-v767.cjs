'use strict';
// Regression test for ABC QUEST v7.6.7: fame reward overlay can ALWAYS close,
// including from Android Back, while awards remain claim-once and persisted.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2]||'android-patches/rewards-v766.js','utf8');
const game=fs.readFileSync(process.argv[3]||'android-patches/v76_gameplay.js','utf8');
let activeOverlay=null,priorBackCalls=0,saveCalls=0,keyListener=null;
const env={
 progress:{stars:2500,credits:100,learned:{A:Date.now(),B:Date.now()},worldRecords:{}},
 GLORY:Array.from({length:24},(_,i)=>({name:'תהילה '+(Math.floor(i/3)+1)+' '+['I','II','III'][i%3],min:i*100})),
 app:{addEventListener(){}},
 window:{abcAndroidBack(){priorBackCalls++;return false;}},
 document:{
  querySelector(sel){return sel==='.quest766-reward-overlay'?activeOverlay:null;},
  createElement(tag){
   assert.equal(tag,'div');
   const handlers={};
   return {className:'',innerHTML:'',handlers,setAttribute(){},
    addEventListener(name,handler){handlers[name]=handler;},
    remove(){if(activeOverlay===this)activeOverlay=null;}};
  },
  body:{appendChild(node){activeOverlay=node;}},
  addEventListener(name,fn){if(name==='keydown')keyListener=fn;}
 },
 save(){saveCalls++;},
 today(){return '2026-10-18';},
 render(){},
 showToast(){},
 worldRecords(){return [];},
 homePage(){return '<div><section class="quest76-compass">home</section></div>';},
 progressPage(){return '<div class="quest-progress-worlds"></div>';},
 console:{info(){}}
};
vm.createContext(env);
vm.runInContext(src,env);
const api=env.window.ABCQuestRewards766;
assert.equal(api.claimFame(1),true,'Fame I->II crossing should be claimable');
assert.ok(activeOverlay,'Reward overlay shown');
assert.match(activeOverlay.innerHTML,/ממשיכים במסע!/);
assert.match(activeOverlay.innerHTML,/quest767-reward-x/);
let prevented=false;
const continueButton={closest(sel){return sel==='[data-action="reward766-close"]'?this:null;}};
activeOverlay.handlers.click({target:continueButton,preventDefault(){prevented=true;}});
assert.equal(prevented,true);assert.equal(activeOverlay,null,'Continue must dismiss reward');
assert.equal(api.claimFame(1),false,'Prize not awarded twice after dialog closes');
assert.equal(api.state().credits,1100,'Credits remain after closing');
// Android Back closes reward, does not navigate, does not remove award.
env.progress.stars=4000;
assert.equal(api.claimFame(2),true);
assert.ok(activeOverlay);
assert.equal(env.window.abcAndroidBack(),true,'Android Back handled by overlay');
assert.equal(activeOverlay,null,'Android Back dismissed reward');
assert.equal(priorBackCalls,0,'Back must not navigate when reward shown');
assert.equal(api.state().fameClaims['2'],true);
// Clicking the dark backdrop works too.
env.progress.stars=15000;
assert.equal(api.claimFame(3),true);
assert.ok(activeOverlay);
const backdrop=activeOverlay;
backdrop.handlers.click({target:backdrop,preventDefault(){}});
assert.equal(activeOverlay,null,'Tapping dark backdrop dismisses');
assert.equal(api.state().fameClaims['3'],true);
// Escape and fallback to regular Android Back navigation remain intact.
env.progress.stars=20000;
assert.equal(api.claimFame(4),true);
let escaped=false;
keyListener({key:'Escape',preventDefault(){escaped=true;}});
assert.equal(escaped,true);assert.equal(activeOverlay,null);
assert.equal(env.window.abcAndroidBack(),false);
assert.equal(priorBackCalls,1);
// The in-world guide must reflect the difference between a known letter
// (yellow) and practiced mastery (green), without modifying saved data.
const begin=game.indexOf('const previousStageLegend767=stagePage;');
const end=game.indexOf('window.ABCQuestVersion76={',begin);
assert.ok(begin>0&&end>begin,'Legend patch exists');
const letters=[{up:'A'},{up:'B'},{up:'C'}];
env.stagePage=()=>'<section><div class="letter-grid">letters</div></section>';
env.stageLetters=()=>letters;
env.selectedStage=0;
env.mastery=up=>up==='A';
const oldLearned=JSON.stringify(env.progress.learned);
vm.runInContext(game.slice(begin,end),env);
const world=env.stagePage();
assert.match(world,/מה אומרים צבעי האותיות/);
assert.match(world,/ירוק — שולטים באות \(1\)/);
assert.match(world,/צהוב — הכרנו, ממשיכים לתרגל \(1\)/);
assert.match(world,/לבן — עוד לא הכרנו \(1\)/);
assert.match(world,/80% הצלחה/);
assert.equal(JSON.stringify(env.progress.learned),oldLearned);
console.log('PASS 7.6.7: close button, backdrop, Escape & Android Back work, no duplicate fame awards; green/yellow legend accurate.');
