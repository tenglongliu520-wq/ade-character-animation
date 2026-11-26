"""Add the Detishuo title page to the one-minute Beihai film."""
import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import bpy
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from render_beihai_dance import FPS, HEIGHT, ROOT, WIDTH, render_video


AA = 3
BRAND_FONT = Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyhbd.ttc'
TITLE_FONT = Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/simkai.ttf'
SUBTITLE_FONT = Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyh.ttc'


def title_page(logo, destination):
    center=229
    ink='#243c38'
    title=Image.new('RGBA',(WIDTH*AA,HEIGHT*AA))
    wash=Image.new('L',title.size)
    ImageDraw.Draw(wash).ellipse((49*AA,35*AA,391*AA,183*AA),fill=98)
    paper=Image.new('RGBA',title.size,'#faf6e9')
    paper.putalpha(wash.filter(ImageFilter.GaussianBlur(31*AA)))
    title.alpha_composite(paper)

    draw=ImageDraw.Draw(title)
    brand=ImageFont.truetype(str(BRAND_FONT),21*AA)
    calligraphy=ImageFont.truetype(str(TITLE_FONT),48*AA)
    subtitle=ImageFont.truetype(str(SUBTITLE_FONT),17*AA)
    brand_name='得体说'
    mark_size=34*AA
    brand_center=center*AA+21*AA
    text_left=round(brand_center-draw.textlength(brand_name,font=brand)/2)
    mark_x=text_left-mark_size-7*AA
    mark_y=53*AA
    with Image.open(logo) as image:
        mark=image.convert('RGBA').crop((90,40,340,290))
        mark=mark.resize((mark_size,mark_size),Image.Resampling.LANCZOS)
    alpha=Image.new('L',mark.size)
    ImageDraw.Draw(alpha).ellipse((1,1,mark_size-2,mark_size-2),fill=255)
    mark.putalpha(alpha)
    title.alpha_composite(mark,dest=(mark_x,mark_y))
    draw.text((brand_center,70*AA),brand_name,font=brand,anchor='mm',fill=ink,
              stroke_width=AA,stroke_fill='#f9f7ed')
    draw.text((center*AA,116*AA),'让我们荡起双桨',font=calligraphy,anchor='mm',fill=ink,
              stroke_width=AA,stroke_fill='#fdf9eb')
    draw.text((center*AA,158*AA),'阿德 · 北海公园',font=subtitle,anchor='mm',fill='#315849',
              stroke_width=2,stroke_fill='#f7f4e5')
    title.resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS).save(destination)


def render_opening(base, logo, output, cover, temporary):
    scene=bpy.context.scene
    scene.render.fps=FPS
    scene.frame_start,scene.frame_end=1,60*FPS
    scene.render.resolution_x,scene.render.resolution_y=WIDTH,HEIGHT
    scene.render.resolution_percentage=100
    scene.render.use_sequencer=True
    scene.view_settings.view_transform='Standard'
    strips=scene.sequence_editor_create().strips
    clip=strips.new_movie('Beihai dance',str(base),1,1)
    size=clip.elements[0].orig_width,clip.elements[0].orig_height
    if size!=(WIDTH,HEIGHT) or clip.frame_duration!=scene.frame_end or clip.fps!=FPS:
        raise ValueError('Use the 480 x 576 one-minute Beihai film at 30 fps.')
    strips.new_sound('Existing accompaniment',str(base),3,1)
    title=temporary/'detishuo-title.png'
    title_page(logo,title)
    opening=strips.new_image('Detishuo title page',str(title),2,1)
    opening.frame_final_duration=53
    opening.blend_type='ALPHA_OVER'
    for frame,alpha in ((1,1),(35,1),(53,0)):
        opening.blend_alpha=alpha
        opening.keyframe_insert(data_path='blend_alpha',frame=frame)
    scene.frame_set(1)
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(cover)
    bpy.ops.render.render(write_still=True)
    render_video(scene,output,temporary)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video',type=Path)
    parser.add_argument('--logo',type=Path,default=ROOT/'detishuo-brand.webp')
    parser.add_argument('--output',type=Path,default=ROOT/'ade-rowing-beihai-minute-detishuo.mp4')
    args=parser.parse_args()
    source=args.video.resolve()
    output=args.output.resolve()
    if output.suffix.lower()!='.mp4' or source==output:
        parser.error('Choose a new MP4 output filename.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix='detishuo-opening-',dir=output.parent) as workspace:
        render_opening(source,args.logo.resolve(),output,output.with_suffix('.png'),Path(workspace))


if __name__=='__main__':
    main()
