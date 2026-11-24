from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
FONT='C:/Windows/Fonts/msyh.ttc';title=ImageFont.truetype(FONT,24);small=ImageFont.truetype(FONT,17)
def panel(path,source=False,size=(400,630)):
 im=Image.open(ROOT/path).convert('RGB');cx=302 if source else 400;h=865;half=h*size[0]/size[1]/2
 return im.crop((round(cx-half),50,round(cx+half),915)).resize(size,Image.Resampling.LANCZOS)
out=Image.new('RGB',(1260,760),'#f6f4ed');d=ImageDraw.Draw(out)
for i,(label,path,src) in enumerate([('录屏原帧','reference-front.png',True),('上一轮','previous-front.png',False),('本轮模型','front.png',False)]):
 d.text((i*420+14,15),label,font=title,fill='#234034');out.paste(panel(path,src),(i*420+10,64))
d.text((18,713),'同一正面投影比例。同一光线与视角，对比暖米灰内搭与青雾灰竹纹。',font=small,fill='#354c40');out.save(ROOT/'comparison.jpg',quality=95)
items=[('录屏正面','reference-front.png',True),('本轮正面','front.png',False),('录屏斜侧','reference-right.png',True),('本轮斜侧','quarter-right.png',False),('录屏另一侧','reference-left.png',True),('本轮另一侧','quarter-left.png',False),('本轮侧面','side.png',False),('本轮背面 · 含推断','back.png',False)]
out=Image.new('RGB',(1440,1230),'#f6f4ed');d=ImageDraw.Draw(out)
for i,(label,path,src) in enumerate(items):
 x=i%4*360;y=i//4*590;d.text((x+12,y+12),label,font=title,fill='#234034');out.paste(panel(path,src,(340,525)),(x+10,y+53))
d.text((15,1190),'录屏人物在动作中；本轮模型为中立站姿。斜侧图用于观察形体，姿态和拍摄角度并非完全一致。',font=small,fill='#354c40');out.save(ROOT/'multi-view-comparison.jpg',quality=94)
print('COMPARISONS_READY')

# Face views for comparing expression without shrinking the head to a thumbnail.
closeups = [
    ('录屏斜侧', 'reference-left.png', (108,130,495,475)),
    ('上一版', 'previous-quarter.png', (195,35,610,455)),
    ('新版青雾灰内搭', 'quarter-left.png', (195,35,610,455)),
    ('偏头轻笑', 'gesture.png', (223,40,644,464)),
]
review = Image.new('RGB', (1360,460), '#f6f4ed')
labels = ImageDraw.Draw(review)
for index,(label,file,box) in enumerate(closeups):
    portrait = Image.open(ROOT/file).convert('RGB').crop(box)
    portrait.thumbnail((320,355), Image.Resampling.LANCZOS)
    x = index*340
    labels.text((x+12,15), label, font=title, fill='#234034')
    review.paste(portrait, (x+(340-portrait.width)//2,62))
labels.text((16,421), '模型截图来自同一 Blender 工程。录屏与渲染的姿势、镜头和灯光存在差异。', font=small, fill='#354c40')
review.save(ROOT/'expression-comparison.jpg',quality=95)
