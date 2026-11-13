/* Shared deterministic choreography. All speech energy comes from actual audio. */
globalThis.AdeMotion=class{
 constructor(){this.clock=0;this.last=null;this.mode='idle';this.modeAt=0;this.energy=0;this.blinkAt=2.9;this.blinkUntil=0;this.greetingAt=-100;}
 setState(mode){if(!['idle','talk','listen','think','wave','hello','breathe','sway','hop','celebrate','sleep'].includes(mode))mode='idle';if(mode===this.mode)return;this.mode=mode;this.modeAt=this.clock;if(mode==='talk'||mode==='listen')this.action=null;if(mode==='wave'||mode==='hello')this.greet();}
 triggerAction(name){if(!['think','turn','spin'].includes(name)||this.action||this.mode==='talk')return false;this.action=name;this.actionAt=this.clock;return true;}
 greet(){this.greetingAt=this.clock;}
 sample(now,level=0,moving=true,reduced=false){
  const dt=this.last===null?0:Math.max(0,Math.min(.1,(now-this.last)/1000));this.last=now;if(reduced)this.clock=Math.max(this.clock,3.5);if(moving)this.clock+=dt;
  const t=this.clock,age=t-this.modeAt,measured=Number.isFinite(level)?Math.max(0,Math.min(1,level)):0;
  const target=moving&&this.mode==='talk'&&measured>.045?measured:0;this.energy+=(target-this.energy)*(1-Math.exp(-dt/(target>this.energy?.045:.075)));if(this.energy<.003||!moving)this.energy=0;
  if(moving&&t>=this.blinkAt){this.blinkUntil=t+.145;this.blinkAt=t+3.1+1.4*(.5+.5*Math.sin(t*7.13));}
  const running=moving&&t<1.6,entering=moving&&t<3.2,progress=Math.min(1,t/1.6),ease=1-(1-progress)**3,gait=running?Math.sin(t*21):0;
  const greetTime=t<3.2&&t>1.65?t-1.65:t-this.greetingAt,waving=moving&&greetTime>=0&&greetTime<1.55,wave=waving?Math.min(1,greetTime/.18,(1.55-greetTime)/.25):0;
  const breath=moving?Math.sin(t*1.7):0,talk=this.mode==='talk'?this.energy:0,listen=moving&&this.mode==='listen',think=moving&&this.mode==='think';
  let action=this.action||null,actionFrame=0,actionMix=0;
  if(reduced){this.action=null;action=null;}
  if(action){const a=t-this.actionAt,d=action==='think'?2.6:action==='turn'?2.8:2.4;
   if(a>=d){this.action=null;action=null;}else{actionMix=Math.max(0,Math.min(1,a/.18,(d-a)/.22));
    const ease=q=>.5-.5*Math.cos(Math.PI*Math.max(0,Math.min(1,q)));
    actionFrame=action==='think'?8:action==='spin'?ease(a/d)*8:a<1?ease(a)*4:a<1.65?4:(1-ease((a-1.65)/1.15))*4;}}
  if(!action&&this.mode==='think'&&!reduced){action='thinking';actionFrame=8;actionMix=Math.min(1,age/.22);}
  return{action,actionFrame,actionMix,clock:t,entering,running,waving,smile:waving||this.mode==='celebrate',scale:t<1.6?.56+.44*ease:1,x:t<1.6?(1-ease)*90:0,
   y:running?-Math.abs(gait)*13:moving&&t>=1.6&&t<1.85?Math.sin((t-1.6)*16)*(1.85-t)*12:breath*1.3,
   body:running?gait*.025:moving?Math.sin(t*.81)*.009+talk*Math.sin(t*2.4)*.014:0,
   head:running?-gait*.025:moving?Math.sin(t*3.7)*talk*.045+(listen?-.055+Math.sin(t*1.8)*.012:think?.045:0)+(this.mode==='idle'?Math.exp(-age*2)*Math.sin(age*5)*.035:0)+Math.sin(t*1.13)*.012:0,
   headX:think?2+Math.sin(t)*1.5:listen?-1.5:0,torsoY:breath*1.2,legL:gait*.3,legR:-gait*.3,
   armL:running?-gait*.23:moving?Math.sin(t*1.1)*.018-talk*(.08+.035*Math.sin(t*3)):0,
   armR:running?gait*.23:moving?-Math.sin(t*1.1)*.018+talk*.045:0,wave,handAngle:waving?Math.sin(greetTime*15)*.14*wave:0,blink:moving&&(t<this.blinkUntil||this.mode==='sleep'),mouth:this.energy};
 }
};
