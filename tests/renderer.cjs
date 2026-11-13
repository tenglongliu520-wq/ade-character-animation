const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
async function mount({missing=false,reduced=false}={}){
 let now=0,id=0;const jobs=new Map(),listeners={};const context=new Proxy({}, {get:(o,k)=>o[k]||(()=>{})});
 const host={dataset:{},children:[],classList:{add(){}},append(x){this.children.push(x)}};
 const media={matches:reduced,addEventListener(){},removeEventListener(){}};
 const document={hidden:false,currentScript:{src:'http://localhost/companion-avatar.js'},referrer:'',createElement:()=>({setAttribute(){},remove(){},getContext:()=>context}),addEventListener:(n,f)=>listeners[n]=f,removeEventListener(){}};
 const scope={document,window:{parent:{},addEventListener(){},removeEventListener(){}},URL,performance:{now:()=>now},matchMedia:()=>media,requestAnimationFrame:f=>{jobs.set(++id,f);return id},cancelAnimationFrame:i=>jobs.delete(i),Image:class{set src(v){queueMicrotask(()=>missing?this.onerror():this.onload())}}};
 vm.createContext(scope);for(const f of ['ade-motion-model.js','companion-avatar.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../src/web',f),'utf8'),scope);
 const avatar=new scope.window.CompanionAvatar(host);await avatar.ready;
 return {avatar,host,jobs,media,document,listeners,frame(){now+=40;const a=[...jobs.values()];jobs.clear();a.forEach(f=>f(now));}};
}
test('layered renderer owns a single frame loop through repeated starts and state changes',async()=>{const m=await mount();for(let i=0;i<5;i++){m.avatar.start();m.avatar.setState('talk');m.frame();assert.equal(m.jobs.size,1);}m.avatar.destroy();assert.equal(m.jobs.size,0);});
test('pause and background stop rendering; foreground resumes once',async()=>{const m=await mount();m.avatar.setPaused(true);assert.equal(m.jobs.size,0);m.avatar.setPaused(false);assert.equal(m.jobs.size,1);m.document.hidden=true;m.listeners.visibilitychange();assert.equal(m.jobs.size,0);m.document.hidden=false;m.listeners.visibilitychange();assert.equal(m.jobs.size,1);});
test('reduced motion shows settled artwork and missing atlas does not create a loop',async()=>{const m=await mount({reduced:true});assert.equal(m.jobs.size,0);assert.equal(m.avatar.pose.entering,false);const bad=await mount({missing:true});assert.equal(bad.jobs.size,0);assert.equal(bad.avatar.canvas.hidden,true);});
test('external speech levels expire; analyser silence overrides old remote speech',async()=>{const m=await mount();m.avatar.setSpeechLevel(.7);assert.equal(m.avatar.level(100),.7);assert.equal(m.avatar.level(300),0);m.avatar.analyser={fftSize:32,getByteTimeDomainData:s=>s.fill(128)};assert.equal(m.avatar.level(0),0);});

test('turning renders exactly one opaque silhouette, including action entry and exit',async()=>{const m=await mount();const pose=m.avatar.model.sample(5000);m.avatar.actionsLoaded=true;for(const mix of [.05,.5,1]){const draws=[];m.avatar.ctx.drawImage=img=>draws.push({image:img,alpha:m.avatar.ctx.globalAlpha});m.avatar.model.sample=()=>({...pose,action:'spin',actionFrame:1.35,actionMix:mix});m.avatar.draw(5000);assert.equal(draws.length,1,'Never crossfade two poses or layer the idle puppet behind an action');assert.equal(draws[0].image,m.avatar.actionsAtlas);assert.equal(draws[0].alpha,1);}});

