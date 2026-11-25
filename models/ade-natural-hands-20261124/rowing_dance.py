"""Build the standalone rowing dance from the approved, symmetrical Ade model."""
from dataclasses import dataclass
from bisect import bisect_right
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
    Pose(17, (-17,-38), (9,40), sway=-.030, rise=.009, turn=-5, spread=15),
    Pose(18, (-6,-55), (14,62), sway=-.068, rise=.016, turn=-11, nod=-7, spread=19),
    Pose(19.2, (-25,-25), (16,18), sway=-.039, rise=-.006, turn=-4, spread=43),
    Pose(20, (-12,-12), (18,18), spread=12),
    Pose(21, (-38,-17), (40,9), sway=.030, rise=.009, turn=5, spread=15),
    Pose(22, (-55,-6), (62,14), sway=.068, rise=.016, turn=11, nod=-7, spread=19),
    Pose(23.2, (-25,-25), (18,16), sway=.039, rise=-.006, turn=4, spread=43),
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


def ease(value):
    t = min(1, max(0, value))
    return t*t*t*(10 + t*(-15 + 6*t))


def make_curve(keys):
    """Interpolate with continuous velocity and bounded motion at a reversal."""
    beats, values = zip(*keys)
    slopes = [(b-a)/(beats[i+1]-beats[i]) for i,(a,b) in enumerate(zip(values,values[1:]))]
    tangents = [0]
    for a,b in zip(slopes,slopes[1:]):
        tangents.append(2*a*b/(a+b) if a*b>0 else 0)
    tangents.append(0)

    def value_at(beat):
        if beat <= beats[0]:
            return values[0]
        if beat >= beats[-1]:
            return values[-1]
        i = bisect_right(beats,beat)-1
        length = beats[i+1]-beats[i]
        t = (beat-beats[i])/length
        blend = t*t*(3-2*t)
        return (values[i]*(1-blend) + values[i+1]*blend +
                length*t*(1-t)*(tangents[i]*(1-t)-tangents[i+1]*t))

    return value_at


def sample_motion():
    curves = {name:make_curve([(p.beat,getattr(p,name)) for p in POSES])
              for name in ('sway','rise','turn','nod','spread')}
    for name in ('swing','bend'):
        for i in range(2):
            curves[name,i]=make_curve([(p.beat,getattr(p,name)[i]) for p in POSES])
    return curves, [(frame-1)*BPM/(60*FPS) for frame in range(1,frame_at(BEATS)+1)]


def phased(beat, delay):
    fade = ease(beat/.75)*ease((BEATS-beat)/.85)
    return beat-delay*fade


def add_track(owner, name, baked=False):
    animation = owner.animation_data
    action = animation.action
    action.name = name
    for curve in action.layers[0].strips[0].channelbag(animation.action_slot).fcurves:
        for key in curve.keyframe_points:
            if baked:
                key.interpolation = 'LINEAR'
            else:
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
    add_track(obj, obj.name + ' dance', baked=True)


def animate_shapes(obj, values, baked=False):
    data = obj.data.shape_keys
    for name, keys in values.items():
        key = data.key_blocks[name]
        for beat, value in keys:
            key.value = value
            key.keyframe_insert('value', frame=frame_at(beat))
    add_track(data, obj.name + ' dance', baked=baked)


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
    # Use one continuous blend for sleeve, cuff and hand, even as flex
    # crosses the original pose boundaries.
    ratios = [(beat,min(1,max(0,value/66))) for beat,value in bends]
    animate_shapes(obj, {
        'Elbow 22': [(b,3*t*(1-t)**2) for b,t in ratios],
        'Elbow 44': [(b,3*t*t*(1-t)) for b,t in ratios],
        'Elbow 66': [(b,t**3) for b,t in ratios],
    }, baked=True)


def add_side_step(side, foot, beats):
    phrases = (5,17) if side<0 else (9,21)

    def step(beat):
        for start in phrases:
            at = beat-start
            if -.48<=at<.72:
                phase=(at+.48)/1.20
                progress=ease(phase)
            elif .72<=at<1.35:
                return (side*.086,-.028,0),(0,0,0)
            elif 1.35<=at<2.70:
                phase=(at-1.35)/1.35
                progress=1-ease(phase)
            else:
                continue
            lift=math.sin(math.pi*phase)**2
            toe=12*lift*(1-2*phase)
            return (side*.086*progress,-.028*progress,.056*lift),(toe,0,0)
        return (0,0,0),(0,0,0)

    animate_transform(foot,[(beat,*step(beat)) for beat in beats])


def add_cloth_follow(obj, waves):
    """Keep the collar and belt fixed while the loose cloth carries the turn."""
    world = obj.matrix_world.copy()
    inverse = world.inverted()
    basis = obj.shape_key_add(name='Basis')
    sash = obj.name.startswith('Woven sash')
    for direction,name in ((-1,'Follow left'),(1,'Follow right')):
        target = obj.shape_key_add(name=name)
        for vertex,rest in zip(target.data,basis.data):
            point = world @ rest.co
            amount = ease((1.00-point.z)/(.51 if sash else .70))
            drift = Vector((direction*(.062 if sash else .032),direction*.010,direction*.003))*amount
            vertex.co = inverse @ (point+drift)
    animate_shapes(obj, {
        name:[(beat,max(0,direction*value)) for beat,value in waves]
        for direction,name in ((-1,'Follow left'),(1,'Follow right'))
    }, baked=True)


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
    curves, beats = sample_motion()
    for index,(side,label) in enumerate(((-1,'right'),(1,'left'))):
        shoulder_point = Vector((side*.130,0,1.248))
        elbow_point = Vector((side*.213,0,1.080))
        shoulder = pivot(f'Rowing shoulder {label}', torso.matrix_world.inverted() @ shoulder_point, torso)
        foot = pivot(f'Dance step {label}', (side*.113,-.046,.061))
        bpy.context.view_layer.update()
        delay = .14+index*.075
        bends = [(beat,curves['bend',index](phased(beat,delay))) for beat in beats]
        arm_names = [f'{part} {side}' for part in ('Soft bell sleeve','Inner cuff facing','Thin cuff seam')]
        arm_names.append(f'Relaxed unified hand {label}')
        for name in arm_names:
            obj = bpy.data.objects[name]
            add_arm_shapes(obj, elbow_point, bends)
            adopt(obj, shoulder)
        for part in ('Loose trouser hem','Thin ivory sole','Black cloth shoe','Shoe fine seam'):
            adopt(bpy.data.objects[f'{part} {side}'],foot)
        animate_transform(shoulder, [
            (beat,(0,0,0),(
                curves['swing',index](phased(beat,index*.045)),
                -side*curves['spread'](phased(beat,.04+index*.04)),
                side*curves['turn'](phased(beat,.09))*.16,
            )) for beat in beats
        ])
        add_side_step(side,foot,beats)

    torso_keys,head_keys,ribbon_keys,waves,tip_follow=[],[],[],[],[]
    step_phrases=((-1,5),(1,9),(-1,17),(1,21))
    for beat in beats:
        body_beat=phased(beat,-.16)
        head_beat=phased(beat,.085)
        cloth_beat=phased(beat,.25)
        counterweight=0
        for side,start in step_phrases:
            landing=(beat-start+.48)/1.20
            if 0<landing<1:
                counterweight-=side*.022*math.sin(math.pi*landing)**2
        sway=curves['sway'](body_beat)+counterweight
        rise=curves['rise'](body_beat)
        turn=curves['turn'](body_beat)
        torso_keys.append((beat,(sway,-rise*.34,rise),(max(0,curves['nod'](body_beat))*.25,sway*57,turn)))
        head_keys.append((beat,(0,0,0),(curves['nod'](head_beat),-curves['sway'](head_beat)*56,-curves['turn'](head_beat)*.52)))
        ribbon_keys.append((beat,(0,0,0),(-curves['nod'](cloth_beat)*.32,curves['sway'](cloth_beat)*65,-curves['turn'](cloth_beat)*.50)))
        follow=curves['sway'](cloth_beat)/.075
        waves.append((beat,-follow*.69-curves['turn'](cloth_beat)*.018))
        turn_change=curves['turn'](cloth_beat)-curves['turn'](phased(beat,.40))
        tip_follow.append((beat,min(.72,abs(turn_change)*.12+abs(curves['nod'](cloth_beat))*.020)))
    animate_transform(torso,torso_keys)
    animate_transform(head,head_keys)
    animate_transform(ribbon,ribbon_keys)
    for obj in scene.objects:
        if obj.name.startswith(('Flowing open bamboo coat','Woven sash')):
            add_cloth_follow(obj,waves)
        if obj.type=='MESH' and obj.data.shape_keys and 'tipFollow' in obj.data.shape_keys.key_blocks:
            animate_shapes(obj,{'tipFollow':tip_follow},baked=True)
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
        ('step',18,(-1.8,-5,1.43)), ('open',19.2,(1.9,-5,1.43)), ('bow',30.2,(2.3,-5,1.43)),
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
