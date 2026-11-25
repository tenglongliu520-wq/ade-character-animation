"""Build the standalone rowing dance from the approved, symmetrical Ade model."""
from dataclasses import dataclass
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

from expression_motion import adopt, pivot


ROOT = Path(__file__).resolve().parent
CLIP = 'RowingDance'
FPS, BPM, BEATS = 30, 96, 32
FLEX_ANGLES = (22, 44, 66)


@dataclass(frozen=True)
class Pose:
    beat: float
    swing: tuple[int, int] = (0, 0)
    bend: tuple[int, int] = (0, 0)
    sway: float = 0
    rise: float = 0
    turn: float = 0
    nod: float = 0
    spread: float = 0


POSES = (
    Pose(0),
    Pose(1, (-20,-20), (22,22), rise=.009, nod=-4, spread=8),
    Pose(2, (-52,-52), (12,12), rise=.016, nod=-7, spread=12),
    Pose(3, (-21,-21), (58,58), rise=-.013, nod=4, spread=11),
    Pose(4, (7,7), (10,10), rise=.006, spread=6),
    Pose(5, (-32,-18), (20,24), sway=-.035, turn=-7, spread=13),
    Pose(6, (-54,-38), (15,16), sway=-.063, rise=.014, turn=-12, nod=-4, spread=14),
    Pose(7, (-18,-32), (59,42), sway=-.040, rise=-.014, turn=-7, nod=4, spread=11),
    Pose(8, (2,4), (9,12), rise=.005, spread=6),
    Pose(9, (-18,-32), (24,20), sway=.035, turn=7, spread=13),
    Pose(10, (-38,-54), (16,15), sway=.063, rise=.014, turn=12, nod=-4, spread=14),
    Pose(11, (-32,-18), (42,59), sway=.040, rise=-.014, turn=7, nod=4, spread=11),
    Pose(12, (4,2), (12,9), rise=.005, spread=6),
    Pose(13, (-23,-23), (23,23), nod=-4, spread=9),
    Pose(14, (-56,-56), (9,9), rise=.021, nod=-7, spread=13),
    Pose(15, (-21,-21), (62,62), rise=-.016, nod=5, spread=12),
    Pose(16, (-8,-8), (20,20), spread=10),
    Pose(17, (-20,-32), (6,38), sway=-.045, rise=.013, turn=-6, spread=20),
    Pose(18, (-12,-37), (14,48), sway=-.068, rise=.022, turn=-9, nod=-5, spread=25),
    Pose(19, (-28,-18), (43,19), sway=-.025, rise=-.007, turn=-3, spread=18),
    Pose(20, (-12,-12), (18,18), spread=12),
    Pose(21, (-32,-20), (38,6), sway=.045, rise=.013, turn=6, spread=20),
    Pose(22, (-37,-12), (48,14), sway=.068, rise=.022, turn=9, nod=-5, spread=25),
    Pose(23, (-18,-28), (19,43), sway=.025, rise=-.007, turn=3, spread=18),
    Pose(24, (-10,-10), (15,15), spread=10),
    Pose(25, (-27,-27), (19,19), nod=-4, spread=11),
    Pose(26, (-55,-55), (13,13), rise=.015, nod=-6, spread=13),
    Pose(27, (-19,-19), (60,60), rise=-.014, nod=6, spread=10),
    Pose(28, (-10,-10), (31,31), rise=.007, spread=12),
    Pose(29, (2,2), (16,16), nod=-2, spread=8),
    Pose(30.2, (-9,-9), (13,13), rise=-.021, nod=17, spread=5),
    Pose(31.2, nod=2),
    Pose(32),
)


def frame_at(beat):
    return round(1 + beat * FPS * 60 / BPM)


def add_track(owner, name):
    animation = owner.animation_data
    action = animation.action
    action.name = name
    for curve in action.layers[0].strips[0].channelbag(animation.action_slot).fcurves:
        for key in curve.keyframe_points:
            key.handle_left_type = key.handle_right_type = 'AUTO_CLAMPED'
    animation.action = None
    track = animation.nla_tracks.new()
    track.name = CLIP
    track.strips.new(name, 1, action)


def animate_transform(obj, poses):
    rest = obj.location.copy()
    for beat, offset, rotation in poses:
        obj.location = rest + Vector(offset)
        obj.rotation_euler = tuple(math.radians(value) for value in rotation)
        obj.keyframe_insert('location', frame=frame_at(beat))
        obj.keyframe_insert('rotation_euler', frame=frame_at(beat))
    add_track(obj, obj.name + ' dance')


def animate_shapes(obj, values):
    data = obj.data.shape_keys
    for name, keys in values.items():
        key = data.key_blocks[name]
        for beat, value in keys:
            key.value = value
            key.keyframe_insert('value', frame=frame_at(beat))
    add_track(data, obj.name + ' dance')


def add_arm_shapes(obj, elbow, bends):
    world = obj.matrix_world.copy()
    inverse = world.inverted()
    basis = obj.shape_key_add(name='Basis')
    for angle in FLEX_ANGLES:
        target = obj.shape_key_add(name=f'Elbow {angle}')
        for vertex, rest in zip(target.data, basis.data):
            point = world @ rest.co
            t = min(1, max(0, (1.170-point.z)/.163))
            flex = t*t*(3-2*t)
            rotation = Matrix.Rotation(math.radians(-angle*flex), 3, 'X')
            vertex.co = inverse @ (elbow + rotation @ (point-elbow))
    # Neighbouring targets share the same cuff transform, including its hand.
    animate_shapes(obj, {
        f'Elbow {angle}': [(beat, max(0, 1-abs(value-angle)/22)) for beat,value in bends]
        for angle in FLEX_ANGLES
    })


def add_side_step(side, foot):
    phrases = (5, 17) if side < 0 else (9, 21)
    keys = [(0,(0,0,0),(0,0,0))]
    for beat in phrases:
        keys.extend([
            (beat-.65,(0,0,0),(0,0,0)),
            (beat-.15,(side*.032,-.012,.047),(0,0,0)),
            (beat+.55,(side*.076,-.028,.002),(0,0,0)),
            (beat+1.25,(side*.076,-.028,.002),(0,0,0)),
            (beat+2.05,(side*.032,-.012,.043),(0,0,0)),
            (beat+2.78,(0,0,0),(0,0,0)),
        ])
    keys.append((32,(0,0,0),(0,0,0)))
    animate_transform(foot, keys)


def build_dance():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'ade.blend'))
    scene = bpy.context.scene
    scene.frame_set(1)
    for obj in scene.objects:
        obj.animation_data_clear()
        if obj.type == 'MESH' and obj.data.shape_keys:
            obj.data.shape_keys.animation_data_clear()
            for key in list(obj.data.shape_keys.key_blocks)[1:]:
                key.value = 0

    torso = bpy.data.objects['Upper body balance']
    head = bpy.data.objects['Head expression pivot']
    ribbon = bpy.data.objects['Hair ribbon follow through']
    for index,(side,label) in enumerate(((-1,'right'),(1,'left'))):
        shoulder_point = Vector((side*.130,0,1.248))
        elbow_point = Vector((side*.213,0,1.080))
        shoulder = pivot(f'Rowing shoulder {label}', torso.matrix_world.inverted() @ shoulder_point, torso)
        foot = pivot(f'Dance step {label}', (side*.113,-.046,.061))
        bpy.context.view_layer.update()
        bends = [(pose.beat,pose.bend[index]) for pose in POSES]
        arm_names = [f'{part} {side}' for part in ('Soft bell sleeve','Inner cuff facing','Thin cuff seam')]
        arm_names.append(f'Relaxed unified hand {label}')
        for name in arm_names:
            obj = bpy.data.objects[name]
            add_arm_shapes(obj, elbow_point, bends)
            adopt(obj, shoulder)
        for part in ('Loose trouser hem','Thin ivory sole','Black cloth shoe','Shoe fine seam'):
            adopt(bpy.data.objects[f'{part} {side}'],foot)
        animate_transform(shoulder, [
            (p.beat,(0,0,0),(p.swing[index],-side*p.spread,side*abs(p.turn)*.14)) for p in POSES
        ])
        add_side_step(side,foot)

    animate_transform(torso, [
        (p.beat,(p.sway,-p.rise*.34,p.rise),(max(0,p.nod)*.27,p.sway*55,p.turn)) for p in POSES
    ])
    animate_transform(head, [
        (p.beat,(0,0,0),(p.nod,-p.sway*53,-p.turn*.50)) for p in POSES
    ])
    flutter = [(0,(0,0,0),(0,0,0))]
    flutter.extend((p.beat+.20,(0,0,0),(-p.nod*.31,p.sway*44,-p.turn*.35)) for p in POSES[1:-1])
    flutter.append((32,(0,0,0),(0,0,0)))
    animate_transform(ribbon, flutter)
    smile=[(0,0),(1,.50),(6,.82),(10,.66),(16,.92),(22,.75),(27,1),(31,.40),(32,0)]
    blink=[(0,0),(7.55,0),(7.72,1),(7.86,0),(21.73,0),(21.9,1),(22.04,0),(32,0)]
    animate_shapes(bpy.data.objects['Sculpted smile'],{'smile':smile})
    animate_shapes(bpy.data.objects['Soft tapered face'],{'cheekLift':smile})
    for side in ('left','right'):
        for part in ('Upper','Lower'):
            animate_shapes(bpy.data.objects[f'{part} eyelid {side}'],{'blink':blink})

    scene.render.fps = FPS
    scene.frame_end = frame_at(BEATS)
    scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in scene.objects:
        if obj.type in ('MESH','EMPTY'):
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(ROOT/'ade-rowing.glb'), export_format='GLB', use_selection=True,
        export_animations=True, export_animation_mode='NLA_TRACKS', export_skins=False,
        export_current_frame=True, export_morph=True, export_yup=True, export_vertex_color='ACTIVE',
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'ade-rowing.blend'))
    return scene


def render_review(scene):
    camera = scene.camera
    scene.cycles.samples = 16
    scene.render.resolution_x, scene.render.resolution_y = 520, 600
    for name,beat,position in (
        ('reach',2,(2.6,-5,1.62)), ('pull',7,(2.6,-5,1.62)),
        ('step',18,(-1.8,-5,1.43)), ('bow',30.2,(2.3,-5,1.43)),
    ):
        scene.frame_set(frame_at(beat))
        camera.location = position
        camera.rotation_euler = (Vector((0,0,1.17))-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath = str(ROOT/f'rowing-{name}.png')
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    scene = build_dance()
    if '--no-review' not in sys.argv:
        render_review(scene)
