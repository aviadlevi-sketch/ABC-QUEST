'use strict';
/* Pure local regression tests for ABC QUEST 7.6.6.
 * Run: node tests/rewards-v766.cjs
 */
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2]||'android-patches/rewards-v766.js','utf8');
const thresholds=[0,900,2700,4500,6600,9600,13500,18000,22800,28800,
 34500,40200,46500,52500,58500,66000,73500,81000,91500,102000,
 114000,129000,150000,180000];
const GLORY=Array.from({length:24},(_,i)=>({
 name:'תהילה '+Math.floor(i/3)+' '+['I','II','III'][i%3],min:thresholds[i]}));
let date='2026-10-01',saves=0,renders=0;
const progress={credits:0,stars:0,worldRecords:{0:{wins:[]},1:{wins:[]},2:{wins:[]},3:{wins:[]}}};
const app={addEventListener(){}};
const document={
 querySelector(){return null;},
 createElement(){return {className:'',innerHTML:'',setAttribute(){}};},
 body:{appendChild(){}}
};
const env={
 progress,GLORY,app,document,window:{},today:()=>date,
 save(){saves++;},render(){renders++;},showToast(){},
 worldRecords:i=>progress.worldRecords[i].wins,
 homePage(){return '<div><section class="quest76-compass">demo</section></div>';},
 progressPage(){return '<div class="quest-progress-worlds"></div>';},
 console:{info(){}},
};
vm.createContext(env);vm.runInContext(source,env);
const api=env.window.ABCQuestRewards766;
assert.ok(api);
assert.deepEqual(JSON.parse(JSON.stringify(api.loginReward(30))),{
 day:30,credits:2000,trophies:4000,big:true,badge:'אלוף מסע 30 הימים'});
assert.equal(api.loginReward(31),null);
assert.equal(api.state().loginDates.length,1,'First login records day 1');
assert.equal(api.claimLogin(2),false,'Cannot claim unearned future day');
assert.equal(api.claimLogin(1),true);
assert.equal(api.claimLogin(1),false,'Cannot duplicate login prize');
assert.equal(progress.credits,75);assert.equal(progress.stars,150);
assert.match(api.page(),/30 כניסות מצטברות/);
assert.match(env.homePage(),/הפרסים שלי/);
// Four world wins globally, no reward until 4, and idempotent claim after.
for(let n=0;n<3;n++)progress.worldRecords[0].wins.push({date,mode:'visual'});
assert.equal(api.claimDaily(),false);
progress.worldRecords[1].wins.push({date,mode:'sound'});
assert.equal(api.state().dailyWins,4);
assert.equal(api.claimDaily(),true);
assert.equal(api.claimDaily(),false);
assert.equal(progress.credits,275);
assert.equal(progress.stars,550);
const pre=api.state();
env.render();
assert.equal(api.claimDaily(),false,'Render/relaunch cannot duplicate reward');
assert.equal(api.state().credits,pre.credits);
// Advance across dates without any reset. Count each distinct date only once,
// allow backlog collection and never repeat any existing date.
let creditTotal=75,trophyTotal=150;
for(let d=2;d<=30;d++){
 const dt=new Date(Date.UTC(2026,9,d));
 date=dt.toISOString().slice(0,10);
 env.render();
 env.render(); // repeated app render must not count as another entry
 assert.equal(api.state().loginDates.length,d);
 const prize=api.loginReward(d);
 assert.equal(api.claimLogin(d),true);
 assert.equal(api.claimLogin(d),false);
 creditTotal+=prize.credits;
 trophyTotal+=prize.trophies;
}
assert.equal(creditTotal,11300);
assert.equal(trophyTotal,23600);
assert.equal(progress.credits,11300+200,'One 200-credit daily quest prize on day1');
assert.equal(progress.stars,23600+400,'One 400-trophy daily quest prize on day1');
assert.ok(api.state().badges.includes('אלוף מסע 30 הימים'));
const lastDate=date;date='2026-11-01';env.render();
assert.equal(api.state().loginDates.length,31);
assert.equal(api.claimLogin(30),false);
assert.equal(api.claimLogin(31),false);
date=lastDate;env.render();
assert.equal(api.state().loginDates.length,31,'Returning to previous date must not count again');
// Fame rewards only on group boundaries III->I, never within a group.
// Granted fame trophies do not unlock an unearned later fame reward.
progress.stars=0;
assert.equal(api.claimFame(1),false);
progress.stars=4500;
assert.equal(api.claimFame(1),true);
assert.equal(api.claimFame(1),false);
assert.equal(api.claimFame(2),false);
assert.equal(api.state().earnedFameStars,4500);
for(let i=2;i<=7;i++){
 const needed=api.fameReward(i).threshold;
 progress.stars=needed+progress.rewards766.fameGrantedTrophies;
 assert.equal(api.claimFame(i),true,'Fame transition '+i+' should be claimable once');
 assert.equal(api.claimFame(i),false);
}
assert.equal(Object.keys(api.state().fameClaims).length,7);
assert.equal(progress.rewards766.fameGrantedTrophies,19000);
assert.ok(saves>=38&&renders>=36);
console.log('PASS 7.6.6: 30 cumulative days, 11,300/23,600 login awards, 4/4 daily claim, seven fame chests, persistent idempotence.');
