"""Unified, cuff-fitted relaxed hands with staggered, gently bent fingers."""
import math
import bmesh
import bpy

# Local coordinates run from the thumb edge toward the little finger.
# Each row gives the base, tip, height at both ends, and half-width.
FINGERS = (
    ("index", -.025, -.026, .668, .610, .0108),
    ("middle", -.007, -.007, .668, .598, .0114),
    ("ring", .012, .013, .666, .604, .0106),
    ("little", .029, .031, .662, .621, .0094),
)
THUMB_TIP = (-.049, .007, .638)


def hand_point(side, u, v, z):
    # Reflect the same forward-facing palm pose across the body centerline.
    # Both thumbs sit on the outer edges when Ade faces the viewer.
    yaw = 2.72
    cosine, sine = math.cos(yaw), math.sin(yaw)
    return (side*(.296 + cosine*u - sine*v), -.070 + sine*u + cosine*v, z)


def add_relaxed_hand(side, skin, mesh):
    vertices, faces = [], []
    # Ade faces -Y, so positive X is his left.
    hand_side = "left" if side == 1 else "right"
    sides = 24

    def rings(sections):
        offset = len(vertices)
        for u, v, z, width, depth in sections:
            for i in range(sides):
                angle = 2*math.pi*i/sides
                x = u + width*math.cos(angle)
                y = v + depth*math.sin(angle)
                vertices.append(hand_point(side, x, y, z))
        faces.append(tuple(range(offset,offset+sides)))
        for section in range(len(sections)-1):
            start=offset+sides*section
            for i in range(sides):
                a,b=start+i,start+(i+1)%sides
                faces.append((a,a+sides,b+sides,b))
        start=offset+(len(sections)-1)*sides
        faces.append(tuple(reversed(range(start,start+sides))))

    # Rounded trapezoid palm, with a narrow wrist and a flat knuckle arc.
    rings([
        (-.002,.007,.758,.016,.016),(-.001,.006,.734,.020,.020),
        (0,.003,.713,.025,.023),(.001,-.003,.695,.033,.025),
        (.002,-.004,.679,.038,.025),(.002,-.006,.663,.039,.022),
        (.002,-.004,.652,.032,.019),(.002,-.002,.645,.020,.014),
    ])
    # These four digits share the knuckle arc and curl toward the palm.
    for _, start, tip, top, end, width in FINGERS:
        length=top-end
        rings([
            (start,-.006,top,width,width*.96),
            (start,-.010,top-.20*length,width*1.02,width*.96),
            (start*.77+tip*.23,-.008,top-.43*length,width*.82,width*.91),
            (start*.4+tip*.6,-.003,top-.67*length,width*.77,width*.83),
            (tip,.003,top-.85*length,width*.71,width*.73),
            (tip,.005,end+.003,width*.43,width*.45),
            (tip,.006,end,width*.12,width*.13),
        ])
    # Start above the index knuckle and leave an opening at the thumb tip.
    rings([
        (-.019,.002,.698,.012,.013),(-.030,.001,.684,.013,.015),
        (-.041,-.002,.671,.0125,.013),(-.049,0,.659,.0105,.011),
        (-.052,.003,.649,.0085,.010),(-.051,.006,.641,.0055,.0065),
        (*THUMB_TIP,.002,.002),
    ])
    hand=mesh("Relaxed unified hand "+hand_side,vertices,faces,skin)
    bm=bmesh.new()
    bm.from_mesh(hand.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(hand.data)
    bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    hand.select_set(True)
    bpy.context.view_layer.objects.active=hand
    hand.data.remesh_voxel_size=.0017
    bpy.ops.object.voxel_remesh()
    hand.data.materials.clear()
    hand.data.materials.append(skin)
    smooth=hand.modifiers.new("Soften palm and finger junctions",'SMOOTH')
    smooth.factor=.65
    smooth.iterations=4
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    for face in hand.data.polygons:
        face.use_smooth=True

    bm=bmesh.new()
    bm.from_mesh(hand.data)
    assert all(edge.is_manifold for edge in bm.edges), hand.name+" has an open edge"
    remaining = set(bm.verts)
    components = []
    while remaining:
        seed = remaining.pop()
        connected = [seed]
        for vertex in connected:
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    connected.append(other)
        components.append(connected)
    # Voxelizing near-touching surfaces can leave isolated slivers. Reject
    # substantial detached geometry before discarding these small artifacts.
    main = max(components, key=len)
    debris = [v for component in components if component is not main for v in component]
    assert len(debris) <= len(main) / 1000, f"{hand.name} has disconnected geometry"
    if debris:
        bmesh.ops.delete(bm, geom=debris, context='VERTS')
        bm.to_mesh(hand.data)
    bm.free()
    return hand
