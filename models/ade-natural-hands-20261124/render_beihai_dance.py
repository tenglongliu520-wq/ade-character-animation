"""Composite the rowing dance over an animated Beihai Park landscape."""
import argparse
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import bpy
from mathutils import Vector
import numpy as np
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 480, 576
FPS, ORIGINAL_TEMPO, BEATS = 30, 96, 32
OVERSCAN = 12


def make_plates(directory, frames):
    with Image.open(ROOT / 'beihai-lake.png') as image:
        source = ImageOps.fit(
            image.convert('RGB'), (WIDTH + 2*OVERSCAN, HEIGHT + 2*OVERSCAN),
            Image.Resampling.LANCZOS,
        )
    colors = np.asarray(source)
    # Blend displacement in below the far shore and out before the stone quay.
    top, bottom = round(HEIGHT*.492), round(HEIGHT*.875)
    y, x = np.mgrid[top:bottom, :WIDTH].astype(np.float32)
    depth = (y-top)/(bottom-top)
    envelope = np.clip(depth*13, 0, 1)*np.clip((1-depth)*18, 0, 1)
    swell = 2.4*np.pi*(np.sqrt(depth+.055)-.23)*8
    across = x/WIDTH*2*np.pi

    for frame in frames:
        time = (frame-1)/FPS
        pan = 6*np.sin(time*.14-.85)
        plate = source.transform(
            (WIDTH, HEIGHT), Image.Transform.AFFINE, (1, 0, OVERSCAN+pan, 0, 1, OVERSCAN),
            Image.Resampling.BILINEAR,
        )
        phase = swell + .7*np.sin(across*1.9) - time*3.1
        reflected = swell*.61 + across*.8 - time*1.83
        sample_x = x + OVERSCAN + pan + (1.3*np.sin(reflected)+1.9*np.cos(phase))*envelope
        sample_y = y + OVERSCAN + (.48+1.25*depth)*np.sin(phase)*envelope
        ix, iy = sample_x.astype(np.intp), sample_y.astype(np.intp)
        dx, dy = (sample_x-ix)[..., None], (sample_y-iy)[..., None]
        near = colors[iy, ix]*(1-dx)+colors[iy, ix+1]*dx
        far = colors[iy+1, ix]*(1-dx)+colors[iy+1, ix+1]*dx
        sparkle = np.maximum(0, np.cos(phase))**8
        sparkle *= (1+np.cos(3*across+reflected))*.5*envelope
        water = near*(1-dy)+far*dy+sparkle[..., None]*np.array([6, 5, 3])
        plate.paste(Image.fromarray(np.uint8(np.clip(water, 0, 255))), (0, top))
        plate.save(directory / f'lake-{frame:04d}.jpg', quality=94, subsampling=0)


def configure_scene(tempo, audio, plates):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'ade-rowing.blend'))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.frame_start = 1
    scene.frame_end = round(BEATS*60/tempo*FPS)
    scene.render.fps = FPS
    scene.render.fps_base = 1
    for obj in scene.objects:
        owners = [obj]
        if obj.type == 'MESH' and obj.data.shape_keys:
            owners.append(obj.data.shape_keys)
        for owner in owners:
            if owner.animation_data:
                for track in owner.animation_data.nla_tracks:
                    for strip in track.strips:
                        strip.scale *= ORIGINAL_TEMPO/tempo

    camera = scene.camera
    camera.data.ortho_scale = 3.76
    camera.location = (.75, -5, 1.89)
    camera.rotation_euler = (Vector((0, 0, 1.62))-camera.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, -.018))
    bpy.context.object.name = 'Beihai quay contact shadows'
    bpy.context.object.is_shadow_catcher = True
    scene.render.film_transparent = True
    scene.cycles.samples = 6
    scene.cycles.use_denoising = True
    scene.cycles.denoising_input_passes = 'RGB_ALBEDO'
    scene.cycles.denoising_prefilter = 'FAST'
    scene.cycles.denoising_quality = 'FAST'
    scene.cycles.max_bounces = 3
    scene.cycles.diffuse_bounces = 1
    scene.render.use_persistent_data = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = min(12, os.cpu_count() or 1)
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    # Only this region contains the model and its shadow. The plate fills the frame.
    scene.render.use_border = True
    scene.render.use_crop_to_border = False
    scene.render.border_min_x, scene.render.border_max_x = .14, .86
    scene.render.border_min_y, scene.render.border_max_y = .02, .80

    scene.use_nodes = True
    scene.render.use_compositing = True
    tree = scene.node_tree
    tree.nodes.clear()
    lake = tree.nodes.new('CompositorNodeImage')
    lake.image = bpy.data.images.load(str(plates / 'lake-0001.jpg'))
    lake.image.source = 'SEQUENCE'
    lake.frame_start = 1
    lake.frame_duration = scene.frame_end
    lake.use_auto_refresh = True
    actor = tree.nodes.new('CompositorNodeRLayers')
    composite = tree.nodes.new('CompositorNodeAlphaOver')
    output = tree.nodes.new('CompositorNodeComposite')
    tree.links.new(lake.outputs['Image'], composite.inputs[1])
    tree.links.new(actor.outputs['Image'], composite.inputs[2])
    tree.links.new(composite.outputs['Image'], output.inputs['Image'])

    if scene.sequence_editor:
        scene.sequence_editor_clear()
    scene.sequence_editor_create().strips.new_sound('Dance accompaniment', str(audio), 1, 1)
    scene.render.use_sequencer = True
    return scene


def render_video(scene, output, temporary):
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    scene.render.ffmpeg.audio_codec = 'AAC'
    scene.render.ffmpeg.audio_bitrate = 192
    scene.render.filepath = str(temporary / 'beihai-')
    bpy.ops.render.render(animation=True)
    rendered = temporary / f'beihai-{scene.frame_start:04d}-{scene.frame_end:04d}.mp4'
    rendered.replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', default=ROOT / 'rowing-beat.wav', type=Path)
    parser.add_argument('--tempo', type=float, default=ORIGINAL_TEMPO)
    parser.add_argument('--output', default=ROOT / 'ade-rowing-beihai.mp4', type=Path)
    parser.add_argument('--stills', nargs='+', type=int, help='Render selected frames as PNG previews.')
    arguments = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    if not 45 <= arguments.tempo <= 180:
        parser.error('--tempo must be between 45 and 180 BPM')
    if not arguments.audio.is_file():
        parser.error(f'Audio file missing: {arguments.audio}')
    count = round(BEATS*60/arguments.tempo*FPS)
    if arguments.stills and any(frame < 1 or frame > count for frame in arguments.stills):
        parser.error(f'Preview frames must be between 1 and {count}')
    output = arguments.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='ade-beihai-', dir=output.parent) as workspace:
        plates = Path(workspace)
        frames = sorted({1, *arguments.stills}) if arguments.stills else range(1, count+1)
        make_plates(plates, frames)
        scene = configure_scene(arguments.tempo, arguments.audio.resolve(), plates)
        if arguments.stills:
            scene.render.image_settings.file_format = 'PNG'
            for frame in arguments.stills:
                scene.frame_set(frame)
                scene.render.filepath = str(output.with_name(f'{output.stem}-{frame:04d}.png'))
                bpy.ops.render.render(write_still=True)
        else:
            render_video(scene, output, plates)


if __name__ == '__main__':
    main()
