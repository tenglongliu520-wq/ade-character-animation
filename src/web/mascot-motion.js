(()=>{
 const home=document.querySelector('#welcomeView'),host=home?.querySelector('.welcome-character'),fallback=host?.querySelector('img');if(!host||!fallback||!window.CompanionAvatar)return;
 const button=document.createElement('button');button.type='button';button.className='mascot-touch';button.setAttribute('aria-label','和阿德打招呼');fallback.before(button);button.append(fallback);
 const avatar=new CompanionAvatar(button);host.adeAvatar=avatar;host.dataset.motionState='loading';
 const tools=document.createElement('div');tools.className='mascot-tools';const hint=document.createElement('span');hint.className='mascot-hint';hint.textContent='点点我，打个招呼';
 const toggle=document.createElement('button');toggle.type='button';toggle.className='mascot-toggle';toggle.textContent='暂停动作';toggle.setAttribute('aria-pressed','false');
 const status=document.createElement('span');status.className='mascot-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');tools.append(hint,toggle);host.append(tools,status);
 let paused=false,sayTimer;try{paused=localStorage.getItem('politeMascotMotionPaused')==='true';}catch{}
 function sync(){const splash=document.querySelector('#brandSplash'),covered=home.hidden||(splash&&!splash.classList.contains('hidden'))||Boolean(document.querySelector('dialog[open]'));avatar.setPaused(paused||covered);toggle.textContent=avatar.media.matches?'已减少动态':paused?'开启动作':'暂停动作';toggle.disabled=avatar.media.matches;toggle.setAttribute('aria-pressed',String(paused));}
 avatar.ready.then(ok=>{fallback.hidden=ok;host.dataset.motionState=ok?'ready':'static';sync();});
 button.onclick=()=>{avatar.greet();status.textContent='你好呀，慢慢说，我在听。';clearTimeout(sayTimer);sayTimer=setTimeout(()=>status.textContent='',3200);};
 toggle.onclick=()=>{paused=!paused;try{localStorage.setItem('politeMascotMotionPaused',String(paused));}catch{}sync();};
 const observer=new MutationObserver(sync);observer.observe(home,{attributes:true,attributeFilter:['hidden']});const splash=document.querySelector('#brandSplash');if(splash)observer.observe(splash,{attributes:true,attributeFilter:['class']});document.querySelectorAll('dialog').forEach(d=>observer.observe(d,{attributes:true,attributeFilter:['open']}));avatar.media.addEventListener('change',sync);document.addEventListener('polite:reading-complete',()=>avatar.greet());sync();
})();
