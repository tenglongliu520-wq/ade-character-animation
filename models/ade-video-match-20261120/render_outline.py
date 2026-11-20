"""Independent reference outline overlay. Manual trace is approximate, no score."""
from pathlib import Path
import bpy
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT / "ade.blend"))
scene=bpy.context.scene;scene.render.film_transparent=True;scene.cycles.samples=4;scene.cycles.use_denoising=False;scene.render.filepath=str(ROOT/'model-alpha.png');bpy.ops.render.render(write_still=True)
outline=[(313,50),(367,50),(405,70),(421,106),(418,139),(469,160),(480,187),(460,208),(485,241),(469,267),(486,283),(452,315),(459,329),(483,362),(486,394),(465,420),(418,412),(382,388),(356,399),(350,420),(374,445),(405,505),(430,569),(447,619),(443,651),(427,676),(423,733),(426,789),(400,814),(370,825),(368,849),(385,872),(382,897),(345,910),(320,901),(306,891),(287,908),(249,918),(209,909),(203,887),(215,861),(230,846),(221,813),(187,809),(163,786),(159,760),(168,713),(161,683),(148,658),(139,626),(146,579),(168,518),(202,459),(252,413),(271,400),(236,390),(203,375),(176,360),(171,337),(150,317),(141,294),(140,272),(122,253),(143,247),(126,225),(139,215),(133,195),(132,166),(174,123),(228,95),(280,73),(313,82)]
refmask=Image.new('L',(800,950));ImageDraw.Draw(refmask).polygon([(x+98,y) for x,y in outline],fill=255)
modelmask=Image.open(ROOT/'model-alpha.png').getchannel('A').point(lambda a:255 if a>127 else 0)
base=Image.new('RGB',(800,950),'#17161b');base.paste(Image.open(ROOT/'reference-front.png').convert('RGB'),(98,0));base=Image.blend(base,Image.new('RGB',base.size,'#17161b'),.38)
for mask,color in [(refmask,'#42d4d9'),(modelmask,'#ffd25a')]:
 edge=mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3));base.paste(Image.new('RGB',base.size,color),mask=edge)
out=Image.new('RGB',(1040,1020),'#f6f4ed');out.paste(base,(0,55));d=ImageDraw.Draw(out);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
d.text((15,13),'同一投影比例 · 录屏与本轮模型轮廓',font=font,fill='#234034');d.text((812,90),'青色：录屏人工描边',font=small,fill='#007c82');d.text((812,125),'黄色：模型实际轮廓',font=small,fill='#8b6300');d.text((812,190),'录屏处于动作中',font=small,fill='#354c40');d.text((812,220),'描边含人工误差',font=small,fill='#354c40');d.text((812,250),'不作为相似度分数',font=small,fill='#354c40');out.save(ROOT/'outline-comparison.jpg',quality=94)
print('OUTLINE_COMPARISON_READY')
