"""Deterministic texture construction from recording colors and authored cloth."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,random,math
ROOT=Path(__file__).resolve().parent
raw=np.asarray(Image.open(ROOT/'reference-front.png').convert('RGB')).copy();a=raw.astype(float)
y,x=np.indices(a.shape[:2]);valid=(y<310)&(y>60)&(x>125)&(x<485)&(a[:,:,0]>55)&(a[:,:,0]<220)&(a[:,:,0]>a[:,:,1]*1.22)&(a[:,:,0]>a[:,:,2]*1.4)
seen=valid.copy();q=deque(zip(*np.where(valid)))
while q:
 yy,xx=q.popleft()
 for ny,nx in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
  if 0<=ny<950 and 0<=nx<720 and not seen[ny,nx]:raw[ny,nx]=raw[yy,xx];seen[ny,nx]=True;q.append((ny,nx))
Image.fromarray(raw).resize((1024,1024),Image.Resampling.LANCZOS).save(ROOT/'hair-color.png')
yy,xx=np.indices((1024,1024));u=xx/1024;v=yy/1024;flow=u+.035*np.sin(v*6+u*9);broad=.5+.5*np.sin(flow*math.pi*28+v*2);fine=.5+.5*np.sin(flow*math.pi*240+np.sin(v*13)*2);shine=np.clip(broad,0,1)**2*.27+fine*.035
ar=np.zeros((1024,1024,3),float)
for k,(low,high) in enumerate(zip((78,39,24),(148,80,44))):ar[:,:,k]=low+(high-low)*shine*2
Image.fromarray(np.uint8(ar)).save(ROOT/'inferred-rear-hair.png')
yy,xx=np.indices((512,512));nx=(xx-256)/256;nz=(256-yy)/256;rad=np.sqrt(nx*nx+nz*nz);angle=np.arctan2(nz,nx);f=np.clip(.35-.27*nz+.08*np.sin(angle*43+rad*9)*rad,0,1);ar=np.zeros((512,512,3),float)
for k,(low,high) in enumerate(zip((61,38,35),(174,111,62))):ar[:,:,k]=low+(high-low)*f
Image.fromarray(np.uint8(ar)).save(ROOT/'iris-brown.png')
# A continuous skin field with blush only. Eyes, eyebrows and smile are geometry.
yy,xx=np.indices((950,720));arr=np.zeros((950,720,3),float);arr[:]=(252,208,187)
for cx,cy in ((226,356),(370,360)):
 g=np.exp(-((xx-cx)/36)**2-((yy-cy)/22)**2)*.52
 arr=arr*(1-g[:,:,None])+np.array((251,137,119))*g[:,:,None]
Image.fromarray(np.uint8(arr)).resize((1024,1024),Image.Resampling.LANCZOS).save(ROOT/'skin-blush.png')
W=1536;rng=random.Random(1120);im=Image.new('RGB',(W,W),(177,197,174));d=ImageDraw.Draw(im)
for xx in range(0,W,3):d.line((xx,0,xx,W),fill=(177+rng.randint(-2,2),197+rng.randint(-2,2),174+rng.randint(-2,2)))
for k in range(22):
 cx=rng.uniform(-90,W+90);cy=rng.uniform(30,W+350);length=rng.uniform(250,465);tilt=rng.uniform(-.65,.65);dx=math.sin(tilt)*length;dy=-math.cos(tilt)*length;ink=rng.choice([(104,139,112),(127,154,127),(154,180,150),(208,218,193)])
 d.line((cx,cy,cx+dx,cy+dy),fill=ink,width=3)
 for t in (.25,.43,.61,.79):
  bx=cx+dx*t;by=cy+dy*t
  d.line((bx-4,by,bx+4,by-2),fill=ink,width=2)
  for side in (-1,1):
   for leaf in range(rng.choice((2,3))):
    ll=rng.uniform(85,160);angle=-math.pi/2+side*rng.uniform(.40,1.35)+leaf*.18;ex=bx+math.cos(angle)*ll;ey=by+math.sin(angle)*ll;nx=-(ey-by)/ll;ny=(ex-bx)/ll;width=rng.uniform(8,16)
    d.polygon([(bx,by),((bx+ex)*.5+nx*width,(by+ey)*.5+ny*width),(ex,ey),((bx+ex)*.5-nx*width*.35,(by+ey)*.5-ny*width*.35)],fill=ink)
im.resize((2048,2048),Image.Resampling.LANCZOS).save(ROOT/'bamboo-cloth.png')
ar=np.asarray(im.crop((300,200,650,1350)).resize((256,1024),Image.Resampling.LANCZOS)).astype(float);luminance=ar.mean(axis=2);ink=(luminance<165)
dark=np.zeros_like(ar);dark[:]=(29,54,42);dark[ink]=(153,181,143)
Image.fromarray(dark.astype('uint8')).save(ROOT/'bamboo-sash.png')
print('TEXTURES_READY')
