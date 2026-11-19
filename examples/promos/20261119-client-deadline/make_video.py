from pathlib import Path
import sys,shutil,asyncio,subprocess,wave,math,json
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'vendor'))
from PIL import Image,ImageDraw,ImageFont,ImageOps
import numpy as np
import imageio_ffmpeg,edge_tts
A=R/'assets';A.mkdir(exist_ok=True)
# Supply authorized local assets/client.jpg, worker.jpg, product.jpg before rendering.
I={n:Image.open(A/(n+'.jpg')).convert('RGB') for n in ['client','worker','product']}
W,H,F=720,1280,30
G='#214c3d';C='#f7f7ed';K='#122b24';RED='#f26450'
fonts={}
def ft(s,b=False):
 key=(s,b)
 if key not in fonts:fonts[key]=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc' if b else 'C:/Windows/Fonts/msyh.ttc',s)
 return fonts[key]
def tx(im,xy,s,z=40,c=G,b=False):ImageDraw.Draw(im).multiline_text(xy,s,font=ft(z,b),fill=c,spacing=16)
def ct(im,y,s,z=40,c=G,b=False):
 d=ImageDraw.Draw(im);tx(im,((720-d.textlength(s,font=ft(z,b)))/2,y),s,z,c,b)
def bx(im,rect,c,r=24):ImageDraw.Draw(im).rounded_rectangle(rect,r,fill=c)
def tag(im,x,y,s,c=G,z=24):
 width=ImageDraw.Draw(im).textlength(s,font=ft(z,True))+34;bx(im,(x,y,x+width,y+48),c,24);tx(im,(x+17,y+5),s,z,'white',True)
def pic(im,n,rect,zoom=1):
 x,y,w,h=rect;p=ImageOps.fit(I[n],(round(w*zoom),round(h*zoom)),centering=(.5,.37));dx=(p.width-w)//2;dy=(p.height-h)//2;p=p.crop((dx,dy,dx+w,dy+h));mask=Image.new('L',(w,h));ImageDraw.Draw(mask).rounded_rectangle((0,0,w,h),24,fill=255);im.paste(p,(x,y),mask)
def frame(t):
 dark=t<4.6;im=Image.new('RGB',(W,H),K if dark else C)
 if t<2.8:
  tag(im,44,63,'客户临时催方案',RED);tx(im,(44,145),'今天，必须给！',64,'white',True);tx(im,(46,237),'一句话，压力拉满。',28,'#bdcbbf');pic(im,'client',(44,310,632,620),1+.025*t);tag(im,64,330,'客户');bx(im,(44,970,676,1152),'#2c453a');tx(im,(72,990),'“方案今天必须给，\n  来得及吧？”',42,'white',True)
 elif t<4.6:
  tag(im,44,63,'脑内弹幕 · 尚未发送',RED);tx(im,(44,146),'你当我会分身啊？',56,'#ffb4a2',True);pic(im,'worker',(44,278,632,698),1.02+.025*(t-2.8));bx(im,(44,1005,676,1150),RED);tx(im,(76,1024),'想怼回去？\n先按住发送键。',39,K,True)
 elif t<6.5:
  tag(im,44,63,'换个说法，稳住场面');tx(im,(44,148),'先别急着回。',62,G,True);tx(im,(44,242),'打开 得体说',42,G,True);pic(im,'product',(44,342,632,509),1+.015*(t-4.6));bx(im,(44,892,676,1010),'#e4ebdd');tx(im,(66,916),'客户今天催方案，怎么回？',32,G,True);tx(im,(46,1050),'先理清，再开口。',46,G,True);tx(im,(46,1135),'真实产品截图 · 情景演示',21,'#748274')
 elif t<11.5:
  tag(im,44,63,'同一个问题，换一种回应');tx(im,(44,148),'把火气，',66,G,True);tx(im,(44,246),'换成底气。',66,G,True);pic(im,'worker',(44,372,244,468),1+.008*(t-6.5));bx(im,(307,372,676,866),G);tx(im,(332,404),'“我先确认\n关键部分，\n今天给您\n准确时间。”',39,'white',True);tag(im,44,915,'先确认',G,30);tag(im,242,915,'再承诺',G,30);tx(im,(44,1016),'得体说 · 陪你练习开口',35,G,True);tx(im,(45,1092),'回应示例，结合实际进度调整',23,'#71816e')
 else:
  tag(im,44,63,'有些话，可以先说给阿德听');ct(im,174,'得体说',94,G,True);ct(im,308,'陪你把话说好',42,G,True);p=I['product'].crop((35,350,465,703));p=ImageOps.fit(p,(516,424));im.paste(p,(102,410));ct(im,900,'理清心事 · 练习开口 · 陪你聊聊',28);bx(im,(83,997,637,1096),G,48);ct(im,1018,'先和阿德聊一聊 →',35,'white',True);ct(im,1137,'客户沟通｜先确认，再承诺',25,'#71816e')
 d=ImageDraw.Draw(im);d.rectangle((44,1215,676,1218),fill='#60766a' if dark else '#dce2d6');d.rectangle((44,1215,44+632*t/15,1218),fill=RED if dark else G);tx(im,(44,1232),'得体说 / 客户沟通',18,'#aec0b4' if dark else '#748274');tx(im,(576,1232),'15秒短片',18,'#aec0b4' if dark else '#748274')
 for cut in [2.8,4.6,6.5,11.5]:
  if 0<=t-cut<.1:im=Image.blend(im,Image.new('RGB',(W,H),C),.3*(1-(t-cut)/.1))
 return im
L=[(.15,2.5,'方案今天必须给，来得及吧？','zh-CN-YunjianNeural'),(2.9,1.55,'你当我会分身啊？','zh-CN-XiaoxiaoNeural'),(4.8,1.55,'先问问得体说。','zh-CN-XiaoxiaoNeural'),(6.65,4.65,'我先确认关键部分，今天给您准确时间。','zh-CN-XiaoxiaoNeural'),(11.65,3.05,'得体说，陪你把话说好。','zh-CN-XiaoxiaoNeural')]
FF=imageio_ffmpeg.get_ffmpeg_exe()
async def voices():
 for i,(_,_,words,voice) in enumerate(L):
  p=R/f'voice-{i}.mp3'
  if not p.exists():await edge_tts.Communicate(words,voice,rate='+12%',connect_timeout=15,receive_timeout=30).save(str(p))
  print('VOICE',i,flush=True)
def render():
 sr=48000;mix=np.zeros(sr*15,dtype=np.float32);durations=[]
 for i,(start,dur,words,voice) in enumerate(L):
  p=R/f'voice-{i}.mp3';b=subprocess.check_output([FF,'-v','error','-i',str(p),'-f','f32le','-ac','1','-ar',str(sr),'-']);a=np.frombuffer(b,np.float32);orig=len(a)/sr;durations.append(orig)
  if orig>dur:
   b=subprocess.check_output([FF,'-v','error','-i',str(p),'-af',f'atempo={orig/dur:.4f}','-f','f32le','-ac','1','-ar',str(sr),'-']);a=np.frombuffer(b,np.float32)
  pos=round(start*sr);n=min(len(a),len(mix)-pos);mix[pos:pos+n]+=a[:n]*.92
 for at,freq in [(.02,900),(.58,900),(1.15,900),(1.73,900),(2.3,900),(2.8,160),(4.6,523),(4.72,659),(4.84,784),(11.5,523),(11.65,659),(11.8,784)]:
  n=int(sr*.4);x=np.arange(n)/sr;p=np.sin(2*np.pi*freq*x)*np.exp(-x*18)*.085;pos=int(at*sr);mix[pos:pos+n]+=p
 with wave.open(str(R/'mix.wav'),'wb') as wav:wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(sr);wav.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())
 out=R/'得体说_客户催方案_15秒竖屏.mp4';p=subprocess.Popen([FF,'-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-','-i',str(R/'mix.wav'),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','15','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for i in range(450):
  p.stdin.write(frame(i/30).tobytes())
  if i%90==0:print('FRAME',i,flush=True)
 p.stdin.close()
 if p.wait():raise RuntimeError('encoding failed')
 sheet=Image.new('RGB',(720,768),C)
 for j,t in enumerate([1.3,3.5,5.7,8.7,12.8,14.5]):sheet.paste(frame(t).resize((240,384)),((j%3)*240,(j//3)*384))
 sheet.save(R/'分镜核验.jpg',quality=95);frame(1.3).save(R/'封面.jpg',quality=95)
 check=subprocess.run([FF,'-i',str(out),'-f','null','-'],capture_output=True)
 (R/'encoding-check.txt').write_text(check.stderr.decode(errors='replace'),encoding='utf8')
 (R/'audio-durations.json').write_text(json.dumps(durations))
 print('DONE',str(out),flush=True)
if __name__=='__main__':
 if '--render-only' not in sys.argv:asyncio.run(voices())
 render()
