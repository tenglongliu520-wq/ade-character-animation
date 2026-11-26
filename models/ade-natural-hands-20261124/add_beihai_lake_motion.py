"""Animate the clouds and a single child rowing behind Ade in the Beihai film."""
import argparse
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import bpy
import numpy as np
from PIL import Image, ImageDraw, ImageOps

from render_beihai_dance import FPS, HEIGHT, OVERSCAN, ROOT, WIDTH, render_video


AA = 3
TILE_SIZE = (124, 68)
TILE_ORIGIN = (46, 38)


def range_fade(value, lower, upper):
    ratio = np.clip((value-lower)/(upper-lower),0,1)
    return ratio*ratio*(3-2*ratio)


def lake_sky():
    with Image.open(ROOT/'beihai-lake.png') as image:
        source = ImageOps.fit(
            image.convert('RGB'),(WIDTH+2*OVERSCAN,HEIGHT+2*OVERSCAN),
            Image.Resampling.LANCZOS,
        )
    y,x=np.mgrid[:HEIGHT,:WIDTH].astype(np.float32)
    # Use open sky only, leaving the foreground willow and White Dagoba still.
    top=range_fade(x,178,231)*(1-range_fade(y,63,85))
    left_edge=np.maximum(95,180-(y-74)*1.5)
    below=(
        range_fade(x-left_edge,0,27)*range_fade(y,65,92)*
        (1-range_fade(x,337,372))*(1-range_fade(y,137,167))
    )
    mask=np.uint8(255*np.maximum(top,below))
    return source, Image.fromarray(mask,'L')


def cloud_overlay(source, mask, time):
    pan=6*math.sin(time*.14-.85)
    drift=35*time/60+2.3*math.sin(time*.13)
    north=1.8*math.sin(time*.066)
    clouds=source.transform(
        (WIDTH,HEIGHT),Image.Transform.AFFINE,
        (1,0,OVERSCAN+pan-drift,0,1,OVERSCAN+north),Image.Resampling.BILINEAR,
    )
    clouds.putalpha(mask)
    return clouds


class BoatPaint:
    """Draw the small boat and rower in their own supersampled coordinates."""

    def __init__(self):
        self.image=Image.new('RGBA',tuple(size*AA for size in TILE_SIZE))
        self.draw=ImageDraw.Draw(self.image)

    def point(self, point):
        return tuple(round((axis+origin)*AA) for axis,origin in zip(point,TILE_ORIGIN))

    def path(self, coordinates, fill):
        self.draw.polygon([self.point(point) for point in coordinates],fill)

    def line(self, coordinates, color, width=1):
        self.draw.line([self.point(point) for point in coordinates],color,round(width*AA),joint='curve')

    def ellipse(self, box, fill, outline=None, width=1):
        x0,y0=self.point(box[:2])
        x1,y1=self.point(box[2:])
        self.draw.ellipse((x0,y0,x1,y1),fill,outline,width=round(width*AA))


def draw_oar(boat, lock, reach, far=False):
    x,y=lock
    dx,dy=reach
    hand=(x-dx*.37,y-dy*.37)
    tip=(x+dx,y+dy)
    blade=('#c89762' if far else '#d4ac79')
    boat.line([hand,lock,tip],'#72553f' if far else '#925f38',1.35)
    length=math.hypot(dx,dy)
    ux,uy=dx/length,dy/length
    boat.path([
        (tip[0]-ux*1.5-uy*1.2,tip[1]-uy*1.5+ux*1.2),
        (tip[0]+ux*6-uy*1.8,tip[1]+uy*6+ux*1.8),
        (tip[0]+ux*7.4+uy*1.7,tip[1]+uy*7.4-ux*1.7),
        (tip[0]-ux*1.5+uy*.8,tip[1]-uy*1.5-ux*.8),
    ],blade)
    return hand,tip


def rowing_boat(time):
    phase=(time/2.45+.14)%1
    swing=(1-math.cos(2*math.pi*phase))*.5
    drive=math.sin(2*math.pi*phase)
    lean=2.1-4*swing
    paint=BoatPaint()

    for line in range(3):
        points=[(26+i,7+line*2.35+math.sin(i*.19-time*2+line)*.8+i*.08) for i in range(0,25-line*4,2)]
        paint.line(points,(231,244,238,105-line*23),.75)
    paint.ellipse((-34,6,34,15),(42,70,66,45))
    paint.line([(-28,11),(-10,12),(9,12),(28,9)],(222,194,154,79),1)

    far_hand,_=draw_oar(paint,(0,-7),(-18+35*swing,-10+drive*2),far=True)
    paint.path([(-34,-3),(-23,-8),(9,-10),(24,-8),(34,-5),(29,-1),(-18,2)],'#b38258')
    paint.path([(-27,-3),(-13,-6),(16,-7),(28,-5),(14,-2),(-15,0)],'#70513d')
    paint.line([(3,-6),(11,-2)],'#be986d',2)

    skin='#dfac81'
    shoulder=(3+lean,-19)
    paint.line([shoulder,(9+lean,-12),far_hand],'#adc4b9',3)
    paint.path([
        (-2+lean,-20),(5+lean,-21),(9+lean,-12),
        (7,-5),(-2,-5),(-4+lean,-11),
    ],'#d49a57')
    paint.line([(-1+lean,-17),(-1,-7),(5,-7)],'#98693f',1.1)
    paint.ellipse((-.5+lean,-29,10.5+lean,-18),skin)
    paint.path([
        (-1+lean,-22),(-1+lean,-27),(2+lean,-31),(7+lean,-31),
        (11+lean,-27),(10+lean,-24),(6+lean,-26),(2+lean,-24),(1+lean,-21),
    ],'#514035')
    paint.ellipse((8.2+lean,-24.8,9.55+lean,-23.4),'#685145')
    paint.ellipse((9.4+lean,-23.6,11.25+lean,-21.4),skin)

    paint.path([
        (-35,-4),(-26,-2),(-17,-1),(6,-1),(23,-3),(35,-6),
        (31,1),(25,5),(15,8),(-14,8),(-25,5),(-31,1),
    ],'#80563a')
    paint.path([
        (-33,-3),(-21,1),(-4,2),(17,1),(31,-3),
        (27,2),(19,5),(-16,6),(-26,3),
    ],'#a3734c')
    paint.line([(-35,-4),(-25,-1),(-14,1),(6,1),(23,-1),(34,-5)],'#ddaf79',1.05)
    paint.line([(-25,4),(-13,6),(16,6),(26,3)],'#614632',.72)

    hand,tip=draw_oar(paint,(-1,-3),(-24+42*swing,11+drive*2.8))
    elbow=(9+lean*.7,-11+drive*.9)
    paint.line([shoulder,elbow],'#88a9a3',3.55)
    paint.line([elbow,hand],'#bcc8b7',2.6)
    paint.ellipse((hand[0]-1.65,hand[1]-1.25,hand[0]+1.5,hand[1]+1.25),skin)
    if drive>0:
        x,y=tip
        paint.ellipse((x-4,y+1,x+9,y+5),None,(231,245,236,round(drive*124)),.75)
    return paint.image.resize(TILE_SIZE,Image.Resampling.LANCZOS)


def lake_overlay(source, mask, frame):
    time=(frame-1)/FPS
    overlay=cloud_overlay(source,mask,time)
    boat=rowing_boat(time)
    bow_x=.873*WIDTH-49*time/60+1.8*math.sin(time*.5)
    waterline=.664*HEIGHT+1.1*math.sin(time*math.tau/2.95)
    position=(round(bow_x)-TILE_ORIGIN[0],round(waterline)-TILE_ORIGIN[1])
    overlay.alpha_composite(boat,dest=position)
    return overlay


def composite_movie(base, output, temporary):
    scene=bpy.context.scene
    scene.render.fps=FPS
    scene.render.resolution_x=WIDTH
    scene.render.resolution_y=HEIGHT
    scene.render.resolution_percentage=100
    scene.render.use_sequencer=True
    scene.view_settings.view_transform='Standard'
    strips=scene.sequence_editor_create().strips
    movie=strips.new_movie('Original 60-second Ade dance',str(base),1,1)
    size=(movie.elements[0].orig_width,movie.elements[0].orig_height)
    if movie.fps!=FPS or movie.frame_duration!=60*FPS or size!=(WIDTH,HEIGHT):
        raise ValueError('Use the original 480 x 576 one-minute Beihai edit at 30 fps.')
    strips.new_sound('Keep the original soundtrack',str(base),3,1)
    scene.frame_start,scene.frame_end=1,movie.frame_duration
    source,mask=lake_sky()
    first=temporary/'lake-motion-0001.png'
    for frame in range(1,scene.frame_end+1):
        lake_overlay(source,mask,frame).save(temporary/f'lake-motion-{frame:04d}.png',compress_level=1)
    layer=strips.new_image('Animated clouds and rower',str(first),2,1)
    for frame in range(2,scene.frame_end+1):
        layer.elements.append(f'lake-motion-{frame:04d}.png')
    layer.frame_final_duration=scene.frame_end
    layer.blend_type='ALPHA_OVER'
    render_video(scene,output,temporary)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'ade-rowing-beihai-minute-lake.mp4')
    args=parser.parse_args()
    output=args.output.resolve()
    if args.video.resolve()==output:
        parser.error('Use a different filename for the updated film.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix='ade-lake-motion-',dir=output.parent) as temporary:
        composite_movie(args.video.resolve(),output,Path(temporary))


if __name__=='__main__':
    main()
