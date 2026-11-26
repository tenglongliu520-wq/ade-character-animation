(()=>{
 const home=document.querySelector('#welcomeView'),host=home?.querySelector('.welcome-character'),fallback=host?.querySelector('img');if(!host||!fallback)return;
 const button=document.createElement('button');button.type='button';button.className='mascot-touch';button.setAttribute('aria-label','和阿德打招呼');fallback.before(button);button.append(fallback);
 let renderer,mode='idle',suspended=true,speech=0,speechAt=0;
 const avatar={
  media:matchMedia('(prefers-reduced-motion: reduce)'),
  get mode(){return renderer?.mode??mode;},
  setState(value){mode=value;renderer?.setState(value);},
  setSpeechLevel(value){speech=value;speechAt=performance.now();renderer?.setSpeechLevel(value);},
  setPaused(value){suspended=value;renderer?.setPaused(value);},
  greet(){return renderer?.greet()??false;},
  playAction(name){return renderer?.playAction(name)??false;}
 };
 host.adeAvatar=avatar;host.dataset.motionState='loading';
 const ready=import('/ade-home-3d/home-avatar.js').then(async({HomeAdeAvatar})=>{
  const next=new HomeAdeAvatar(button,avatar.media);
  try{await next.ready;}catch(error){next.destroy();throw error;}
  renderer=next;
  next.setState(mode);
  if(performance.now()-speechAt<240)next.setSpeechLevel(speech);
  next.setPaused(suspended);
  return true;
 }).catch(error=>{console.warn('阿德三维形象加载失败',error);return false;});
 const tools=document.createElement('div');tools.className='mascot-tools';const hint=document.createElement('span');hint.className='mascot-hint';hint.textContent='点点我，打个招呼';
 const toggle=document.createElement('button');toggle.type='button';toggle.className='mascot-toggle';toggle.textContent='暂停动作';toggle.setAttribute('aria-pressed','false');
 const status=document.createElement('span');status.className='mascot-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');tools.append(hint,toggle);host.append(tools,status);
 const actions=document.createElement('div');actions.className='mascot-actions';actions.setAttribute('role','group');actions.setAttribute('aria-label','阿德小动作');
 for(const [name,label]of [['think','想一想'],['turn','转个身'],['spin','转一圈']]){const b=document.createElement('button');b.type='button';b.textContent=label;b.onclick=()=>{status.textContent=avatar.playAction(name)?label+'，陪你放松一下':paused?'请先开启动作':avatar.media.matches?'已跟随系统减少动态':avatar.mode==='talk'?'阿德说完就能做小动作啦':'动作正在准备或进行中';};actions.append(b);}host.append(actions);
 let paused=false,sayTimer,available=null;try{paused=localStorage.getItem('politeMascotMotionPaused')==='true';}catch{}
 function sync(){const splash=document.querySelector('#brandSplash'),covered=home.hidden||(splash&&!splash.classList.contains('hidden'))||Boolean(document.querySelector('dialog[open]'));avatar.setPaused(paused||covered);toggle.textContent=available===false?'静态形象':avatar.media.matches?'已减少动态':paused?'开启动作':'暂停动作';toggle.disabled=available!==true||avatar.media.matches;toggle.setAttribute('aria-pressed',String(paused));for(const b of actions.querySelectorAll('button'))b.disabled=available!==true;}
 ready.then(ok=>{available=ok;fallback.hidden=ok;host.dataset.motionState=ok?'ready':'static';sync();});
 button.onclick=()=>{avatar.greet();status.textContent='你好呀，慢慢说，我在听。';clearTimeout(sayTimer);sayTimer=setTimeout(()=>status.textContent='',3200);};
 toggle.onclick=()=>{paused=!paused;try{localStorage.setItem('politeMascotMotionPaused',String(paused));}catch{}sync();};
 const observer=new MutationObserver(sync);observer.observe(home,{attributes:true,attributeFilter:['hidden']});const splash=document.querySelector('#brandSplash');if(splash)observer.observe(splash,{attributes:true,attributeFilter:['class']});document.querySelectorAll('dialog').forEach(d=>observer.observe(d,{attributes:true,attributeFilter:['open']}));avatar.media.addEventListener('change',sync);document.addEventListener('polite:reading-complete',()=>avatar.greet());sync();
})();
