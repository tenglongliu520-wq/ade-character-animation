"""Extend Ade's rowing choreography with a step turn and hip-hop footwork."""
from bisect import bisect_right
import math

import bpy
from mathutils import Matrix, Vector

from rowing_dance import POSES, STEP_PHRASES, Pose, build_dance, ease, make_curve


# Use the recorded alternating cheek/high-sleeve gestures, weight shifts, and
# crossing gestures as accents in the first phrase. Continue into new footwork.
MINUTE_POSES = tuple(p for p in POSES if p.beat < 28) + (
    Pose(28, (-20,-18), (11,11), rise=.029, nod=-6, spread=75),
    Pose(29, (-31,-22), (49,35), nod=3, spread=5, sweep=(30,-20)),
    Pose(30, (-63,-61), (25,26), rise=.026, nod=-5, spread=31),
    Pose(31, (-22,-20), (12,12), rise=.017, spread=68),
    Pose(32, (-34,-26), (32,48), rise=-.031, nod=6, sweep=(19,-13)),
    # Hip-hop two-step. Lower the weight on the step, then open the chest.
    Pose(33, (-16,-44), (29,54), sway=-.104, rise=-.048, turn=-16, nod=8, spread=14, sweep=(16,-19)),
    Pose(33.55, (-49,-21), (16,38), sway=-.174, rise=-.016, turn=-19, spread=59),
    Pose(34.15, (-19,-54), (49,44), sway=-.157, rise=-.047, turn=-15, nod=9, spread=14, sweep=(38,-28)),
    Pose(35, (-35,-34), (23,26), sway=-.030, rise=.024, nod=-4, spread=48),
    Pose(35.75, (-47,-15), (54,28), sway=.134, rise=-.045, turn=16, nod=8, spread=13, sweep=(21,-17)),
    Pose(36.25, (-19,-50), (37,15), sway=.177, rise=-.011, turn=19, spread=60),
    Pose(37, (-53,-19), (43,49), sway=.114, rise=-.044, turn=12, nod=7, spread=15, sweep=(28,-36)),
    Pose(37.75, (-29,-21), (48,26), sway=-.108, rise=-.033, turn=-13, spread=33, sweep=(27,-12)),
    Pose(38.45, (-9,-64), (27,42), sway=-.169, rise=.023, turn=-18, nod=-6, spread=48),
    Pose(39.2, (-46,-29), (52,50), sway=-.068, rise=-.048, nod=8, spread=6, sweep=(37,-30)),
    Pose(39.93, (-22,-29), (27,49), sway=.128, rise=-.036, turn=13, spread=34, sweep=(15,-26)),
    Pose(40.55, (-63,-10), (41,27), sway=.166, rise=.023, turn=18, nod=-6, spread=48),
    Pose(41.25, (-29,-46), (50,52), sway=.048, rise=-.043, nod=8, spread=5, sweep=(30,-37)),
    Pose(42, (-28,-25), (18,20), rise=.023, nod=-4, spread=70),
    # Pull the sleeves in before turning. Open them as the last foot lands.
    Pose(43.25, (-29,-36), (53,49), sway=.028, rise=-.030, turn=-15, spread=17, sweep=(20,-24)),
    Pose(44.18, (-38,-23), (49,35), sway=-.036, rise=.014, turn=6, spread=15, sweep=(14,-17)),
    Pose(44.98, (-23,-42), (36,49), sway=.035, rise=.020, turn=9, spread=18, sweep=(15,-11)),
    Pose(45.78, (-44,-28), (56,36), sway=-.029, rise=.023, turn=5, spread=14, sweep=(20,-12)),
    Pose(46.58, (-29,-41), (34,47), sway=.031, rise=.017, turn=3, spread=22),
    Pose(47.45, (-23,-21), (13,16), rise=.024, nod=-7, spread=75),
    Pose(48.45, (-21,-41), (52,48), sway=-.035, rise=-.041, nod=8, spread=13, sweep=(34,-21)),
    # Return to broad rowing arcs and a two-sided heel-toe accent.
    Pose(49.4, (-12,-70), (21,39), sway=-.143, rise=.018, turn=-19, nod=-5, spread=50),
    Pose(50.25, (-26,-15), (58,49), sway=-.089, rise=-.035, turn=-11, nod=7, spread=11, sweep=(38,-17)),
    Pose(51.3, (-39,-39), (17,15), rise=.021, spread=68),
    Pose(52.35, (-70,-12), (39,21), sway=.145, rise=.018, turn=19, nod=-5, spread=50),
    Pose(53.18, (-15,-26), (49,58), sway=.093, rise=-.037, turn=11, nod=7, spread=11, sweep=(17,-38)),
    Pose(54, (-46,-46), (36,40), rise=-.024, turn=-6, nod=8, spread=9, sweep=(17,-19)),
    Pose(54.55, (-44,-21), (17,55), sway=-.081, rise=.017, turn=-11, spread=49),
    Pose(55.35, (-17,-48), (50,20), sway=.087, rise=.020, turn=11, spread=49),
    Pose(56, (-27,-28), (17,16), rise=.028, nod=-8, spread=75),
    Pose(57, (-63,-58), (38,30), sway=-.028, rise=.036, turn=-6, nod=-6, spread=27),
    Pose(58, (-22,-21), (61,54), rise=-.037, nod=6, spread=16, sweep=(27,-18)),
    Pose(59, (-44,-42), (12,15), rise=.031, nod=-7, spread=61),
    Pose(60, (-26,-24), (12,13), rise=.023, nod=-5, spread=73),
    Pose(61, (-33,-30), (33,30), nod=4, spread=15, sweep=(22,-19)),
    Pose(62.20, (-10,-10), (12,12), rise=-.049, nod=23, spread=8),
    Pose(63, (-7,-7), (9,9), rise=-.030, nod=17, spread=6),
    Pose(64),
)

STEPS = STEP_PHRASES + (
    (-1,32.83,.217,-.034), (1,35.43,.222,-.038),
    (-1,37.55,.209,.042), (1,39.66,.219,.042),
    (-1,48.88,.217,-.052), (1,51.73,.218,-.051),
)

TURN = make_curve((
    (0,0),(43.47,0),(44.18,58),(44.98,137),(45.78,222),
    (46.58,303),(47.35,360),(64,360),
))
SPOT = make_curve((
    (0,0),(43.46,0),(44.11,-34),(44.85,-24),
    (45.32,18),(46.1,25),(47.35,0),(64,0),
))

# Each landing holds its world-space position until the next swing.
SWING = {
    -1: ((43.47,44.18),(44.98,45.78),(46.58,47.35)),
     1: ((44.18,44.98),(45.78,46.58),(47.35,47.95)),
}


def spinning_step(beat, side):
    if not 43.47 <= beat <= 47.95:
        return None
    rest = Vector((side*.113,-.046,0))
    local_to_world = lambda angle: Matrix.Rotation(math.radians(angle),3,'Z')
    direction = 0
    lift = toe = arc = 0
    for index, (start, end) in enumerate(SWING[side]):
        if beat < start:
            break
        goal_direction = TURN(end)
        if beat < end:
            progress = (beat-start)/(end-start)
            direction += (goal_direction-direction)*ease(progress)
            arc = math.sin(math.pi*progress)**2
            lift = (.076 if index<2 else .055)*arc
            toe = 14*arc*(1-2*progress)
            break
        direction = goal_direction
    yaw = TURN(beat)
    center = Vector((0,-.046,0))
    anchor = center + local_to_world(direction) @ ((rest-center)*(1+.23*arc))
    offset = local_to_world(-yaw) @ anchor - rest
    return (offset.x,offset.y,lift), (toe,0,(direction-yaw)*.65)


def footwork(beat, side):
    turn = spinning_step(beat,side)
    if turn is not None:
        return turn
    # Alternate who touches the heel down and who bears the weight.
    center = 54.48 if side == -1 else 55.38
    phase = (beat-center+.26)/.73
    if 0 < phase < 1:
        pulse = math.sin(math.pi*phase)**2
        return (side*.057*pulse,-.102*pulse,.036*pulse),(-17*pulse,0,-side*13*pulse)
    return None


def main():
    expression=[(0,0),(2,.7),(10,.83),(16,.92),(26,.95),(32,.64),
                (38,.88),(43,.64),(47.45,1),(54,.84),(59,1),(62,.7),(64,.44)]
    blinking=[(0,0),(7.55,0),(7.72,1),(7.86,0),(21.73,0),(21.9,1),
              (22.04,0),(34.8,0),(34.94,1),(35.09,0),(51.5,0),(51.65,1),
              (51.8,0),(62.12,0),(62.36,1),(62.62,0),(64,0)]
    return build_dance(
        MINUTE_POSES,STEPS,output='ade-rowing-minute',floor_turn=TURN,
        extra_step=footwork,spotting=SPOT,smile=expression,blink=blinking,
    )


if __name__ == '__main__':
    main()
