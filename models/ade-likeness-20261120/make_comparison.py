from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
out=Image.new('RGB',(1260,760),'#f6f4ed');draw=ImageDraw.Draw(out)
items=[('录屏目标',ROOT/'reference-front.png',302,50,918),('上一版 · 用户要求调整',ROOT/'reference-v1.png',400,34,870),('本次修订 · 尚未验收',ROOT/'front.png',400,50,913)]
for i,(label,path,cx,top,bottom) in enumerate(items):
 im=Image.open(path).convert('RGB');height=bottom-top;half=height*400/630/2
 crop=im.crop((round(cx-half),top,round(cx+half),bottom));crop=crop.resize((400,630),Image.Resampling.LANCZOS)
 out.paste(crop,(i*420+10,64));draw.text((i*420+15,15),label,font=font,fill='#234034')
draw.text((18,714),'按人物总高度统一展示。当前版本：真实三维网格；五官采用录屏贴图；骨骼和表情尚待制作。',font=small,fill='#354c40')
out.save(ROOT/'comparison.jpg',quality=94)
