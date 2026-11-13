const avatar=new CompanionAvatar(document.querySelector('#avatar'));
const audio=document.querySelector('#audio'),status=document.querySelector('#status');
let context,source,objectUrl,paused=false;
avatar.ready.then(ok=>{status.textContent=ok?'人物已就绪，可切换动作或播放音频':'人物素材加载失败，请从预览服务器打开';});
document.querySelector('#modes').addEventListener('click',event=>{const mode=event.target.dataset.mode;if(!mode)return;audio.pause();avatar.setState(mode);if(mode==='wave')avatar.greet();});
document.querySelector('#pause').addEventListener('click',event=>{paused=!paused;avatar.setPaused(paused);event.target.textContent=paused?'恢复动作':'暂停动作';});
function stop(){avatar.setState('idle');avatar.setSpeechLevel(0);}
audio.addEventListener('play',async()=>{try{if(!context){context=new AudioContext();source=context.createMediaElementSource(audio);avatar.analyser=context.createAnalyser();avatar.analyser.fftSize=1024;source.connect(avatar.analyser);avatar.analyser.connect(context.destination);}await context.resume();if(!audio.paused)avatar.setState('talk');}catch(error){audio.pause();stop();status.textContent='音频初始化失败：'+error.message;}});
for(const name of ['pause','ended','emptied'])audio.addEventListener(name,stop);
audio.addEventListener('error',()=>{stop();status.textContent='无法播放音频，请选择本地文件或检查同级语音仓库。';});
function release(){if(objectUrl){URL.revokeObjectURL(objectUrl);objectUrl=null;}}
document.querySelector('#file').addEventListener('change',event=>{const file=event.target.files[0];if(!file)return;audio.pause();release();objectUrl=URL.createObjectURL(file);audio.src=objectUrl;status.textContent='已选择本地音频，点击播放可查看嘴型联动。';});
document.querySelector('#sample').addEventListener('click',async()=>{try{const response=await fetch('/voice-i/manifest.json');if(!response.ok)throw Error('请将 ade-voice 放在本仓库同级目录，或选择本地音频');const data=await response.json();if(data.voice!=='I'||data.voice_id!=='M09')throw Error('声线不匹配');audio.pause();release();audio.src=data.clips[0].src;await audio.play();status.textContent='I / M09：'+data.clips[0].text;}catch(error){stop();status.textContent=error.message;}});
window.addEventListener('pagehide',()=>{audio.pause();release();});
