const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function model(){const scope={};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../src/web/ade-motion-model.js'),'utf8'),scope);return new scope.AdeMotion();}
function advance(m,end,level=0,moving=true){let p;for(let t=m.last===null?0:m.last+20;t<=end;t+=20)p=m.sample(t,level,moving);return p;}
test('entrance has alternating legs, then settles and does not replay on talk',()=>{const m=model();const a=advance(m,400),b=m.sample(480,0,true);assert.ok(Math.abs(a.legL)>.1);assert.ok(a.legL*a.legR<0);assert.notEqual(a.legL,b.legL);const end=advance(m,3800);assert.equal(end.entering,false);m.setState('talk');assert.equal(m.sample(3820,.5,true).entering,false);});
test('silence closes mouth while audio drives independent head and body gestures',()=>{const m=model();advance(m,4000);m.setState('talk');let p=advance(m,4700,.8);assert.ok(p.mouth>.4);assert.ok(Math.abs(p.head)>0);assert.notEqual(p.head,p.body);p=advance(m,5500,0);assert.ok(p.mouth<.01);});
test('pause freezes pose; reduced motion starts settled with a closed mouth',()=>{const m=model();const a=advance(m,700),b=m.sample(2000,.8,false);assert.equal(a.clock,b.clock);assert.equal(b.mouth,0);const reduced=model();const p=reduced.sample(0,.8,false,true);assert.equal(p.entering,false);assert.equal(p.legL,0);assert.equal(p.head,0);});
test('repeated states keep clock and noisy or invalid audio cannot poison transforms',()=>{const m=model();advance(m,4000);m.setState('talk');const a=m.sample(4020,.6,true);m.setState('talk');const b=m.sample(4040,NaN,true);assert.ok(b.clock>a.clock);for(const v of Object.values(b))if(typeof v==='number')assert.ok(Number.isFinite(v));});
