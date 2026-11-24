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


def animate_shape(obj, name, keys):
    data = obj.data.shape_keys
    channel = data.key_blocks[name]
    for frame, weight in keys:
        channel.value = weight
        channel.keyframe_insert(data_path="value",frame=frame)
    stash_action(data, obj.name + " stroke")


def add_acknowledgment(parts, head_parts, eye_objects, smile, face):
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
        (1,(0,0,0)), (11,(2,-1,-13)), (26,(-2,2,5)), (37,(-3,3,8)),
        (51,(-4,11,6)), (63,(-3,9,4)), (84,(.5,-1,-5)),
        (99,(.4,0,-.7)), (END,(0,0,0)),
    ])
    animate_pivot(ribbon, [
        (1,(0,0,0)), (20,(2,-2,1)), (36,(-4,3,-3)), (52,(1,-2,1)),
        (63,(4,-3,2)), (83,(-3,2,-2)), (100,(.5,0,.5)), (END,(0,0,0)),
    ])
    for eyes in eye_objects:
        animate_shape(eyes, "blink", [(1,0),(17,0),(19,.96),(21,.70),(24,0),
                     (71,0),(73,.92),(75,.55),(78,0),(END,0)])
    smile_keys = [(1,0),(20,0),(38,.48),(51,.84),(64,.51),(85,.10),(END,0)]
    animate_shape(smile,"smile",smile_keys)
    animate_shape(face,"cheekLift",[(frame,weight*.8) for frame,weight in smile_keys])
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = END
    # Sample the first neutral key, within the strips' evaluated frame range.
    scene.frame_set(1)
    return [torso,head,ribbon]
