"""A short, authored head acknowledgment with body lead and delayed ribbons."""
import math

import bpy

CLIP = "LookTiltReturn"
FPS = 30
END = 109
PEAK = 51


def pivot(name, position, parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.empty_display_size = .095
    obj.parent = parent
    obj.location = position
    return obj


def adopt(obj, parent):
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def stash_action(owner, name):
    animation = owner.animation_data
    action = animation.action
    action.name = name
    animation.action = None
    track = animation.nla_tracks.new()
    track.name = CLIP
    start = int(action.frame_range[0])
    strip = track.strips.new(name, start, action)
    strip.extrapolation = 'HOLD'


def animate_pivot(obj, rotation_keys, position_keys=()):
    reference = obj.location.copy()
    for frame, angles in rotation_keys:
        obj.rotation_euler = tuple(math.radians(angle) for angle in angles)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    for frame, delta in position_keys:
        obj.location = tuple(base+step for base,step in zip(reference,delta))
        obj.keyframe_insert(data_path="location", frame=frame)
    stash_action(obj, obj.name + " stroke")


def animate_shapes(obj, tracks):
    data = obj.data.shape_keys
    for name, keys in tracks.items():
        channel = data.key_blocks[name]
        for frame, weight in keys:
            channel.value = weight
            channel.keyframe_insert(data_path="value",frame=frame)
    stash_action(data, obj.name + " stroke")


def add_acknowledgment(parts, head_parts, eye_groups, brows, smile, mouth, face):
    # Head attaches above the collar. Lower legs remain planted in this gesture.
    torso = pivot("Upper body balance", (0,0,1.02))
    head = pivot("Head expression pivot", (0,0,.335), torso)
    ribbon = pivot("Hair ribbon follow through", (.32,.15,.46), head)
    bpy.context.view_layer.update()
    for obj in parts:
        if obj.name.startswith(("Loose trouser","Black cloth shoe","Thin ivory sole","Shoe fine seam")):
            continue
        parent = torso
        if obj in head_parts:
            parent = ribbon if obj.name.startswith(("Long sage ribbon","Short sage ribbon")) else head
        adopt(obj,parent)

    # Body moves first and by a smaller amount than the head. The ribbon
    # catches up after the head has reached its deepest tilt.
    animate_pivot(torso, [
        (1,(0,0,0)), (13,(.5,-.7,-1.5)), (28,(-1,1.6,3.3)),
        (50,(-1,1.7,3.5)), (75,(.5,-.3,-.5)), (91,(0,.2,.3)), (END,(0,0,0)),
    ], [
        (1,(0,0,0)), (13,(-.008,0,-.006)), (30,(.018,-.012,.009)),
        (51,(.016,-.010,.007)), (76,(-.004,0,-.002)), (END,(0,0,0)),
    ])
    animate_pivot(head, [
        (1,(0,0,0)), (11,(1,-.5,-7)), (19,(2,-2,-11)), (28,(-3,3,6)),
        (39,(-4,8,9)), (51,(-4,13,8)), (63,(-2,10,5)), (84,(.5,-1,-4)),
        (99,(.4,0,-.7)), (END,(0,0,0)),
    ])
    animate_pivot(ribbon, [
        (1,(0,0,0)), (20,(2,-2,1)), (36,(-4,3,-3)), (52,(1,-2,1)),
        (63,(4,-3,2)), (83,(-3,2,-2)), (100,(.5,0,.5)), (END,(0,0,0)),
    ])
    blink = [(1,0),(16,0),(17,.12),(19,1),(20,.94),(23,0),
             (71,0),(72,.14),(74,.97),(77,0),(END,0)]
    lash = [(1,0),(18,0),(19,1),(20,.82),(21,0),
            (73,0),(74,1),(75,.2),(76,0),(END,0)]
    smile_keys = [(1,0),(24,0),(33,.37),(45,.86),(51,.96),
                  (59,.90),(67,.48),(71,.14),(83,0),(END,0)]
    for eye,lids,closed_lash in eye_groups:
        animate_shapes(eye,{
            "glanceLeft":[(1,0),(6,0),(9,.91),(14,.83),(18,.34),(21,0),(END,0)],
            "glanceRight":[(1,0),(22,0),(25,.91),(32,.58),(38,.27),(52,.18),
                           (66,.12),(72,0),(80,.33),(84,.25),(93,0),(END,0)],
        })
        animate_shapes(lids[0],{"blink":blink})
        animate_shapes(lids[1],{"blink":blink,"smileSquint":smile_keys})
        animate_shapes(closed_lash,{"closeLash":lash})
    lift = [(1,0),(8,.25),(13,.63),(20,.12),(25,.83),(30,.95),
            (43,.45),(60,.36),(72,.05),(90,0),(END,0)]
    for brow in brows:
        animate_shapes(brow,{"curiousLift":lift})
    animate_shapes(smile,{"smile":smile_keys})
    animate_shapes(mouth,{"smile":smile_keys,"smileOpen":[(1,0),(35,0),(43,.61),(51,1),(59,.89),
                                     (65,.33),(69,0),(END,0)]})
    animate_shapes(face,{"cheekLift":smile_keys})
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = END
    # Sample the first neutral key, within the strips' evaluated frame range.
    scene.frame_set(1)
    return [torso,head,ribbon]
