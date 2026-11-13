/* Layered hanfu puppet; same renderer is served by Sites and the local share gateway. */
(()=>{
 const assetBase=new URL('.',document.currentScript.src);
 const parts={head:[30,8,384,372],blink:[442,8,388,372],smile:[846,8,382,372],torso:[55,421,335,423],armL:[526,442,193,333],armR:[945,443,193,333],legL:[111,904,193,299],legR:[539,904,188,299],wave:[891,848,288,353]};
 let parentOrigin=(()=>{try{const o=new URL(document.referrer).origin;return window.parent!==window&&['https://limao-zhoudou-81.hybrid-klvvc-7155.chatgpt.site','http://127.0.0.1:4173','http://127.0.0.1:5188'].includes(o)?o:null;}catch{return null;}})();
 window.addEventListener('message',event=>{if(event.source===window.parent&&['https://limao-zhoudou-81.hybrid-klvvc-7155.chatgpt.site','http://127.0.0.1:4173','http://127.0.0.1:5188'].includes(event.origin)&&event.data?.type==='ade-avatar-connect')parentOrigin=event.origin;});
 window.CompanionAvatar=class{
  constructor(host){
   this.host=host;this.mode='idle';this.paused=false;this.raf=0;this.destroyed=false;this.model=new AdeMotion();this.external=null;this.analyser=null;this.lastFrame=-100;this.lastBroadcast=-100;
   this.canvas=document.createElement('canvas');this.canvas.width=512;this.canvas.height=768;this.canvas.setAttribute('aria-hidden','true');host.append(this.canvas);this.ctx=this.canvas.getContext('2d');
   this.media=matchMedia('(prefers-reduced-motion: reduce)');this.onVisibility=()=>this.start();document.addEventListener('visibilitychange',this.onVisibility);window.addEventListener('pagehide',this.onHide=()=>this.stop());window.addEventListener('pageshow',this.onVisibility);this.media.addEventListener('change',this.onVisibility);
   this.atlas=new Image();this.ready=new Promise(resolve=>{this.atlas.onload=()=>{if(this.destroyed)return resolve(false);this.loaded=true;host.dataset.avatarReady='true';this.start();resolve(true);};this.atlas.onerror=()=>{host.classList.add('avatar-static');this.canvas.hidden=true;resolve(false);};});this.actionsAtlas=new Image();this.actionsReady=new Promise(resolve=>{this.actionsAtlas.onload=()=>{this.actionsLoaded=true;this.alignActionFrames();resolve(true);};this.actionsAtlas.onerror=()=>resolve(false);});this.actionsAtlas.src=new URL('ade-actions-atlas-20261113.png',assetBase).href;this.atlas.src=new URL('ade-puppet-atlas-20261112.png',assetBase).href;
  }
  setState(mode){this.model.setState(mode);this.mode=this.model.mode;this.host.dataset.state=this.mode;}
  setSpeechLevel(level){this.external={level:Number.isFinite(level)?Math.max(0,Math.min(1,level)):0,at:performance.now()};}
  playAction(name){if(this.paused||this.media.matches||!this.actionsLoaded)return false;return this.model.triggerAction(name);}
  greet(){this.model.greet();}
  setPaused(value){this.paused=Boolean(value);this.start();}
  stop(){cancelAnimationFrame(this.raf);this.raf=0;this.model.last=null;}
  start(){this.stop();if(!this.loaded||this.destroyed)return;this.draw(performance.now());if(!document.hidden&&!this.paused&&!this.media.matches)this.raf=requestAnimationFrame(t=>this.tick(t));}
  tick(now){this.raf=0;if(this.destroyed||document.hidden||this.paused||this.media.matches)return;if(now-this.lastFrame>=1000/60){this.lastFrame=now;this.draw(now);}this.raf=requestAnimationFrame(t=>this.tick(t));}
  level(now){if(this.analyser){try{if(this.samples?.length!==this.analyser.fftSize)this.samples=new Uint8Array(this.analyser.fftSize);this.analyser.getByteTimeDomainData(this.samples);let sum=0;for(const s of this.samples)sum+=(s-128)**2;return Math.min(1,Math.sqrt(sum/this.samples.length)/26);}catch{return 0;}}return this.external&&now-this.external.at<260?this.external.level:0;}
  part(name,x,y,w,h,angle=0,ax=0,ay=0,opacity=1){const c=this.ctx;c.save();c.translate(x,y);c.rotate(angle);c.globalAlpha=opacity*(this.baseAlpha??1);c.drawImage(this.atlas,...parts[name],-ax,-ay,w,h);c.restore();}
  actionFrame(frame,p){
   const c=this.ctx,size=this.actionsAtlas.width/3;
   const index=p.actionFrame===8?8:((Math.round(frame)%8)+8)%8;
   const rect=this.actionBounds?.[index]||[(index%3)*size,Math.floor(index/3)*size,size,size];
   const h=660,w=rect[2]*h/rect[3],residual=p.actionFrame===8?0:frame-Math.round(frame);
   c.save();c.globalAlpha=1;c.imageSmoothingEnabled=true;c.imageSmoothingQuality='high';
   c.translate(256,698);c.scale(1+Math.sin(residual*Math.PI)*.075,1);c.drawImage(this.actionsAtlas,...rect,-w/2,-h,w,h);c.restore();
  }
  alignActionFrames(){
   try{const size=this.actionsAtlas.width/3,scratch=document.createElement('canvas');scratch.width=scratch.height=size;const c=scratch.getContext('2d');this.actionBounds=[];
    for(let i=0;i<9;i++){c.clearRect(0,0,size,size);c.drawImage(this.actionsAtlas,(i%3)*size,Math.floor(i/3)*size,size,size,0,0,size,size);const pixels=c.getImageData(0,0,size,size).data;let left=size,top=size,right=0,bottom=0;
     for(let y=0;y<size;y++)for(let x=0;x<size;x++)if(pixels[(y*size+x)*4+3]>128){left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);}
     this.actionBounds.push(right>left?[(i%3)*size+left,Math.floor(i/3)*size+top,right-left+1,bottom-top+1]:[(i%3)*size,Math.floor(i/3)*size,size,size]);}
   }catch{this.actionBounds=null;}
  }
  draw(now){
   if(!this.ctx||!this.loaded)return;const c=this.ctx,level=this.level(now),moving=!this.paused&&!this.media.matches&&!document.hidden,p=this.model.sample(now,level,moving,this.media.matches);this.pose=p;this.host.dataset.motionState=p.action|| (p.running?'run-in':p.waving?'wave':this.mode);
   if(parentOrigin&&now-this.lastBroadcast>=80){this.lastBroadcast=now;window.parent.postMessage({type:'ade-avatar-motion',mode:this.mode,level:this.paused?0:level,paused:this.paused},parentOrigin);}
   c.clearRect(0,0,512,768);c.save();c.translate(256+p.x,712);c.scale(p.scale,p.scale);c.fillStyle='rgba(58,84,63,.08)';c.beginPath();c.ellipse(0,0,p.running?83:93,9,0,0,Math.PI*2);c.fill();c.translate(-256,-712+p.y);
   if(this.actionsLoaded&&p.action){this.actionFrame(p.actionFrame,p);c.restore();return;}
   c.save();const actionMix=0;c.globalAlpha=1-actionMix;this.baseAlpha=1-actionMix;this.part('legL',220,555,82,141,p.legL,41,0);this.part('legR',291,555,82,141,p.legR,41,0);
   c.translate(256,555);c.rotate(p.body);c.translate(-256,-555+p.torsoY);
   this.part('armL',203,293,96,166,p.armL,79,8);this.part('armR',309,293,96,166,p.armR,18,8,1-p.wave);this.part('wave',309,293,160,196,p.handAngle,33,168,p.wave);
   this.part('torso',256,270,242,306,0,121,0);
   c.save();c.translate(256+p.headX,291);c.rotate(p.head);this.part(p.blink?'blink':p.smile?'smile':'head',0,0,268,260,0,134,260);
   c.strokeStyle='#83452e';c.lineWidth=2.2;c.lineCap='round';c.fillStyle='#913b31';c.beginPath();
   if(p.mouth>.04){const h=3+p.mouth*13,w=9+p.mouth*5;c.ellipse(1,-44,w,h,0,0,Math.PI*2);c.fill();c.stroke();c.fillStyle='#ff9a84';c.beginPath();c.ellipse(1,-44+h*.55,w*.62,h*.28,0,0,Math.PI*2);c.fill();c.fillStyle='#fff6e6';c.fillRect(-w*.65+1,-44-h+2,w*1.3,Math.min(3,h*.35));}
   else{c.moveTo(-10,-45);c.quadraticCurveTo(1,p.smile?-32:-36,12,-45);c.stroke();}c.restore();c.restore();this.baseAlpha=1;
   c.restore();
  }
  destroy(){this.destroyed=true;this.stop();document.removeEventListener('visibilitychange',this.onVisibility);window.removeEventListener('pagehide',this.onHide);window.removeEventListener('pageshow',this.onVisibility);this.media.removeEventListener('change',this.onVisibility);this.canvas.remove();}
 };
})();
