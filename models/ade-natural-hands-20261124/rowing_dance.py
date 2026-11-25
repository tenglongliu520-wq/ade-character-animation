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
    sweep: tuple[int, int] = (0, 0)


# The two arm entries are Ade's right and left. Pose accents use the same
# half-time count that the reference accompaniment uses in the player.
POSES = (
    Pose(0),
    Pose(1, (-31,-30), (24,25), rise=.012, nod=-4, spread=10),
    Pose(2, (-68,-65), (58,60), rise=.015, nod=-5, spread=14, sweep=(9,-9)),
    Pose(3, (-40,-40), (14,16), rise=.030, nod=-2, spread=42),
    Pose(4, (-33,-14), (48,52), rise=-.028, nod=5, spread=2, sweep=(26,-18)),
    Pose(5, (-18,-44), (22,40), sway=-.058, rise=-.036, turn=-11, spread=18),
    Pose(6, (-12,-71), (20,61), sway=-.135, rise=-.052, turn=-24, nod=-6, spread=20, sweep=(0,-9)),
    Pose(7, (-40,-29), (32,19), sway=-.092, rise=.023, turn=-14, nod=2, spread=53),
    Pose(8, (-39,-15), (52,46), sway=-.018, rise=-.022, turn=-4, nod=7, spread=4, sweep=(34,-17)),
    Pose(9, (-44,-18), (40,22), sway=.058, rise=-.036, turn=11, spread=18),
    Pose(10, (-71,-12), (61,20), sway=.135, rise=-.052, turn=24, nod=-6, spread=20, sweep=(9,0)),
    Pose(11, (-29,-40), (19,32), sway=.092, rise=.023, turn=14, nod=2, spread=53),
    Pose(12, (-15,-39), (46,52), sway=.018, rise=-.022, turn=4, nod=7, spread=4, sweep=(17,-34)),
    Pose(13, (-35,-35), (44,44), rise=-.020, nod=5, spread=8, sweep=(17,-17)),
    Pose(14, (-16,-16), (11,11), rise=.035, nod=-8, spread=72),
    Pose(15, (-51,-51), (39,39), rise=-.017, nod=4, spread=16),
    Pose(16, (-24,-15), (47,34), rise=-.008, spread=5, sweep=(17,-12)),
    Pose(17, (-16,-49), (14,50), sway=-.069, rise=-.027, turn=-13, spread=18),
    Pose(18, (1,-73), (11,63), sway=-.145, rise=-.044, turn=-23, nod=-6, spread=25, sweep=(-6,35)),
    Pose(19, (-20,-18), (12,15), sway=-.079, rise=.032, turn=-10, nod=-4, spread=70),
    Pose(20, (-56,-13), (54,48), sway=-.016, rise=-.028, nod=7, spread=1, sweep=(40,-26)),
    Pose(21, (-49,-16), (50,14), sway=.069, rise=-.027, turn=13, spread=18),
    Pose(22, (-73,1), (63,11), sway=.145, rise=-.044, turn=23, nod=-6, spread=25, sweep=(-35,6)),
    Pose(23, (-18,-20), (15,12), sway=.079, rise=.032, turn=10, nod=-4, spread=70),
    Pose(24, (-13,-56), (48,54), sway=.016, rise=-.028, nod=7, spread=1, sweep=(26,-40)),
    Pose(25, (-25,-32), (21,28), sway=-.030, rise=.006, turn=-6, nod=-4, spread=20),
    Pose(26, (-68,-66), (22,23), sway=-.057, rise=.023, turn=-11, nod=-5, spread=18),
    Pose(27, (-16,-18), (64,62), sway=.052, rise=-.034, turn=11, nod=7, spread=19),
    Pose(28, (-18,-18), (10,10), rise=.022, nod=-6, spread=63),
    Pose(29, (-22,-16), (44,31), nod=1, spread=3, sweep=(24,-17)),
    Pose(30.2, (-10,-10), (13,13), rise=-.038, nod=22, spread=5),
    Pose(31.2, nod=2),
    Pose(32),
)

STEP_PHRASES = ((-1,5,.165,-.025), (1,9,.165,-.025),
                (-1,17,.185,-.066), (1,21,.185,-.066))
MAX_STEP = max(stride for _,_,stride,_ in STEP_PHRASES)


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
    for name in ('swing','bend','sweep'):
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
    def step(beat):
        for foot_side,start,stride,depth in STEP_PHRASES:
            if side!=foot_side:
                continue
            at = beat-start
            if -.52<=at<.71:
                phase=(at+.52)/1.23
                progress=ease(phase)
            elif .71<=at<1.42:
                return (side*stride,depth,0),(0,0,side*11)
            elif 1.42<=at<2.72:
                phase=(at-1.42)/1.30
                progress=1-ease(phase)
            else:
                continue
            lift=math.sin(math.pi*phase)**2
            toe=15*lift*(1-2*phase)
            return (side*stride*progress,depth*progress,.071*lift),(toe,0,side*11*progress)
        return (0,0,0),(0,0,0)

    keys=[(beat,*step(beat)) for beat in beats]
    animate_transform(foot,keys)
    return [(beat,abs(offset[0])/MAX_STEP) for beat,offset,_ in keys]


def add_trouser_follow(trouser, side, step_amount):
    """Keep the upper trouser inside the robe while the cuff follows the foot."""
    world=trouser.matrix_world.copy()
    inverse=world.inverted()
    basis=trouser.shape_key_add(name='Basis')
    tuck=trouser.shape_key_add(name='Step tuck')
    for vertex,rest in zip(tuck.data,basis.data):
        point=world @ rest.co
        bound=ease((point.z-.135)/.223)
        center_x=side*.113
        point.x=center_x+(point.x-center_x)*(1-.48*bound)-side*MAX_STEP*.76*bound
        point.y=point.y*(1-.39*bound)+.094*bound
        vertex.co=inverse @ point
    animate_shapes(trouser,{'Step tuck':step_amount},baked=True)


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
            drift = Vector((direction*(.087 if sash else .048),direction*.015,direction*.003))*amount
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
                curves['sweep',index](phased(beat,.06+index*.03))+side*curves['turn'](phased(beat,.09))*.10,
            )) for beat in beats
        ])
        step_amount=add_side_step(side,foot,beats)
        add_trouser_follow(bpy.data.objects[f'Loose trouser hem {side}'],side,step_amount)

    torso_keys,head_keys,ribbon_keys,waves,tip_follow=[],[],[],[],[]
    for beat in beats:
        body_beat=phased(beat,-.16)
        head_beat=phased(beat,.085)
        cloth_beat=phased(beat,.25)
        counterweight=0
        for side,start,_,_ in STEP_PHRASES:
            landing=(beat-start+.52)/1.23
            if 0<landing<1:
                counterweight-=side*.041*math.sin(math.pi*landing)**2
        sway=curves['sway'](body_beat)+counterweight
        rise=curves['rise'](body_beat)
        turn=curves['turn'](body_beat)
        torso_keys.append((beat,(sway,-rise*.34,rise),(curves['nod'](body_beat)*.25,sway*68,turn)))
        head_keys.append((beat,(0,0,0),(curves['nod'](head_beat),-curves['sway'](head_beat)*49,-curves['turn'](head_beat)*.48)))
        ribbon_keys.append((beat,(0,0,0),(-curves['nod'](cloth_beat)*.32,curves['sway'](cloth_beat)*62,-curves['turn'](cloth_beat)*.50)))
        follow=curves['sway'](cloth_beat)/.151
        waves.append((beat,-follow*.63-curves['turn'](cloth_beat)*.012))
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
        ('reach',2,(.8,-5,1.49)), ('pull',27.2,(1.7,-5,1.50)),
        ('step',18.2,(-.65,-5,1.40)), ('open',19.1,(.6,-5,1.40)),
        ('cross',20.1,(.8,-5,1.45)), ('bow',30.2,(1.3,-5,1.43)),
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
