"""Unified, cuff-fitted relaxed hands with staggered, gently bent fingers."""
import math
import bmesh
import bpy

def add_relaxed_hand(side, skin, mesh):
    vertices, faces = [], []
    # In hand coordinates, the thumb sits towards the center of the body.
    yaw = .12 if side == 1 else .20
    cosine, sine = math.cos(yaw), math.sin(yaw)
    center_x, center_y = side*.296, -.070
    sides = 24

    def rings(sections):
        offset = len(vertices)
        for u, v, z, width, depth in sections:
            for i in range(sides):
                angle = 2*math.pi*i/sides
                x = u + width*math.cos(angle)
                y = v + depth*math.sin(angle)
                vertices.append((center_x + side*(cosine*x-sine*y), center_y+sine*x+cosine*y, z))
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
    # (knuckle x, distal x, tip height, proximal half width).
    digits = [(-.025,-.025,.608,.0112),(-.007,-.008,.598,.0118),
              (.012,.010,.604,.0110),(.028,.025,.622,.0098)]
    for i,(start,tip,end,width) in enumerate(digits):
        top=.668-i*.0013
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
    # Thumb emerges from the side of the palm and curls back inward.
    rings([
        (-.019,-.004,.698,.012,.013),(-.030,-.010,.684,.013,.015),
        (-.039,-.016,.671,.013,.013),(-.043,-.014,.659,.0115,.012),
        (-.042,-.009,.649,.009,.010),(-.037,-.003,.641,.006,.007),
        (-.035,0,.639,.002,.002),
    ])
    hand=mesh("Relaxed unified hand "+("right" if side==1 else "left"),vertices,faces,skin)
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
    seed=next(iter(bm.verts))
    connected={seed}
    queue=[seed]
    while queue:
        for edge in queue.pop().link_edges:
            for vertex in edge.verts:
                if vertex not in connected:
                    connected.add(vertex)
                    queue.append(vertex)
    assert len(connected)==len(bm.verts), hand.name+" has loose parts"
    bm.free()
    return hand
