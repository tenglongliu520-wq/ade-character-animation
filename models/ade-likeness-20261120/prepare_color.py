from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw,ImageFilter
import numpy as np
ROOT=Path(__file__).resolve().parent
raw=np.asarray(Image.open(ROOT/'reference-front.png').convert('RGB')).copy()
outline=[(313,50),(367,50),(405,70),(421,106),(418,139),(469,160),(480,187),(460,208),(485,241),(469,267),(486,283),(452,315),(459,329),(483,362),(486,394),(465,420),(418,412),(382,388),(356,399),(350,420),(374,445),(405,505),(430,569),(447,619),(443,651),(427,676),(423,733),(426,789),(400,814),(370,825),(368,849),(385,872),(382,897),(345,910),(320,901),(306,891),(287,908),(249,918),(209,909),(203,887),(215,861),(230,846),(221,813),(187,809),(163,786),(159,760),(168,713),(161,683),(148,658),(139,626),(146,579),(168,518),(202,459),(252,413),(271,400),(236,390),(203,375),(176,360),(171,337),(150,317),(141,294),(140,272),(122,253),(143,247),(126,225),(139,215),(133,195),(132,166),(174,123),(228,95),(280,73),(313,82)]
mask=Image.new('1',(720,950));ImageDraw.Draw(mask).polygon(outline,fill=1)
a=raw.astype(float)
valid=np.asarray(mask)&((a.max(axis=2)>75)|((a[:,:,0]>a[:,:,1]*1.20)&(a[:,:,0]>50))|((a[:,:,1]>a[:,:,0]*1.15)&(a[:,:,1]>a[:,:,2]*1.08)&(a[:,:,1]>35)))
seen=valid.copy();q=deque(zip(*np.where(valid)))
while q:
 y,x=q.popleft()
 for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
  if 0<=ny<950 and 0<=nx<720 and not seen[ny,nx]:
   raw[ny,nx]=raw[y,x];seen[ny,nx]=True;q.append((ny,nx))
Image.fromarray(raw).resize((1024,1024),Image.Resampling.LANCZOS).save(ROOT/'recorded-object-color.png')
original=np.asarray(Image.open(ROOT/'reference-front.png').convert('RGB'))
face=Image.new('1',(720,950));ImageDraw.Draw(face).polygon([(207,291),(227,268),(264,271),(289,291),(314,295),(301,229),(334,230),(344,264),(368,291),(397,292),(407,320),(436,327),(439,351),(419,375),(379,391),(340,404),(300,412),(262,403),(222,387),(194,371),(173,357),(174,337),(189,320),(204,325)],fill=1)
face_mask=np.asarray(face);a=original.astype(float)
skin=face_mask&(a[:,:,0]>185)&(a[:,:,1]>140)&(a[:,:,2]>100)&(a[:,:,0]<a[:,:,1]*1.55)&(a[:,:,0]>a[:,:,1]*1.08)&(a[:,:,1]>a[:,:,2]*1.02)
result=original.copy();seen=skin.copy();q=deque(zip(*np.where(skin)))
while q:
 y,x=q.popleft()
 for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
  if 0<=ny<950 and 0<=nx<720 and not seen[ny,nx]:
   result[ny,nx]=result[y,x];seen[ny,nx]=True;q.append((ny,nx))
features=Image.new('1',(720,950));draw=ImageDraw.Draw(features)
for box in [(213,291,280,356),(322,291,390,356),(220,268,277,289),(326,268,385,289),(280,363,324,385),(290,350,314,372)]:draw.rectangle(box,fill=1)
# Extrapolating nearest pixels across a forehead/cheek creates streaks. Use a
# continuous skin field and retain only observed facial features with feathered
# boundaries; the recorded pixels remain the identity source.
field=Image.new('RGB',(720,950),(252,204,182))
feature_mask=Image.new('L',(720,950));draw=ImageDraw.Draw(feature_mask)
for box in [(213,291,281,357),(322,291,391,357),(215,265,280,291),(322,265,389,291),(277,361,330,386),(291,349,316,370),(208,352,271,382),(337,352,401,382)]:draw.ellipse(box,fill=255)
field=Image.composite(Image.fromarray(original),field,feature_mask.filter(ImageFilter.GaussianBlur(2)))
field.resize((1024,1024),Image.Resampling.LANCZOS).save(ROOT/'recorded-face-color.png')
cloth_mask=Image.new('1',(720,950));draw=ImageDraw.Draw(cloth_mask)
for polygon in [[(252,408),(269,428),(250,505),(225,633),(228,802),(170,785),(160,764),(171,690),(145,645),(140,613),(155,545),(206,455)],[(341,408),(371,450),(406,510),(432,578),(447,625),(432,653),(421,747),(422,790),(365,811),(344,790),(342,638),(341,509)]]:draw.polygon(polygon,fill=1)
cloth_mask.save(ROOT/'observed-cloth-mask.png')
print('RECORDED_OBJECT_COLOR_READY')
