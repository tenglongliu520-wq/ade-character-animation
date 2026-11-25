"""Deform the recorded eye color without moving its silhouette.

Skin-colored lids pass in front of the eye during a blink. This preserves the
iris proportions as the aperture decreases.
"""
import math


def add_gaze(eye, radii, face_depth):
    eye.shape_key_add(name="Basis")
    neutral = eye.data.shape_keys.key_blocks["Basis"].data
    for name, direction in (("glanceLeft", -1), ("glanceRight", 1)):
        target = eye.shape_key_add(name=name)
        for vertex, rest, radius in zip(target.data, neutral, radii):
            weight = (1 - radius**3)**1.5
            x, y, z = rest.co
            new_x=x+direction*.0135*weight
            new_z=z+(.0015 if direction<0 else .003)*weight
            vertex.co=(new_x,y+face_depth(new_x,new_z)-face_depth(x,z),new_z)


def aperture_columns(outline):
    left = min(point[0] for point in outline) + 0.15
    right = max(point[0] for point in outline) - 0.15
    for column in range(49):
        x = left + (right-left)*column/48
        heights = []
        for a, b in zip(outline, outline[1:]+outline[:1]):
            if min(a[0],b[0]) <= x < max(a[0],b[0]):
                heights.append(a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]))
        if len(heights)<2:
            raise ValueError("Eye outline must have an upper and lower contour")
        upper, lower = (915-min(heights))/376, (915-max(heights))/376
        closing = upper*.38 + lower*.62
        yield (x-302)/376, upper, lower, closing


def lid_meshes(name, outline, mesh, face_depth, skin, lash_color):
    columns = list(aperture_columns(outline))
    lids = []
    rows = 7
    for upper in (True, False):
        vertices, closed, smile, uvs = [], [], [], []
        for x, top, bottom, meeting in columns:
            edge = top if upper else bottom
            direction = 1 if upper else -1
            for row in range(rows):
                t = row/(rows-1)
                outer = edge + direction*.009
                rest = outer+(edge+direction*.001-outer)*t
                z = outer+(meeting-direction*.0008-outer)*t
                depth = -.0012+.013*(1-(1-t)**3)
                vertices.append((x,face_depth(x,rest)+.0015,rest))
                closed.append((x,face_depth(x,z)-depth,z))
                narrowed = rest + (0 if upper else (meeting-bottom)*.28*t)
                smile.append((x,face_depth(x,narrowed)-depth,narrowed))
                uvs.append(((302+x*376)/720,(35+rest*376)/950))
        faces = []
        for i in range(len(columns)-1):
            for j in range(rows-1):
                start = i*rows+j
                face = (start,start+rows,start+rows+1,start+1)
                faces.append(tuple(reversed(face)) if upper else face)
        lid = mesh(f"{'Upper' if upper else 'Lower'} eyelid {name}",vertices,faces,skin,uvs)
        lid.shape_key_add(name="Basis")
        for vertex, co in zip(lid.shape_key_add(name="blink").data,closed):
            vertex.co=co
        if not upper:
            for vertex, co in zip(lid.shape_key_add(name="smileSquint").data,smile):
                vertex.co=co
        lids.append(lid)
    vertices, visible, faces = [], [], []
    for i,(x,top,bottom,meeting) in enumerate(columns):
        size=.0024*math.sin(math.pi*i/(len(columns)-1))**.55+.00020
        for z in (meeting-size,meeting+size):
            vertices.append((x,face_depth(x,z)+.016,z))
            visible.append((x,face_depth(x,z)-.013,z))
        if i:
            start=2*(i-1)
            faces.append((start,start+2,start+3,start+1))
    lash = mesh(f"Closed lash {name}",vertices,faces,lash_color)
    lash.shape_key_add(name="Basis")
    for vertex, co in zip(lash.shape_key_add(name="closeLash").data,visible):
        vertex.co=co
    return lids,lash


def brow_expression(brow, face_depth):
    brow.shape_key_add(name="Basis")
    raised=brow.shape_key_add(name="curiousLift")
    for vertex in raised.data:
        x,y,z=vertex.co
        lift=.0125+.003*math.cos((abs(x)-.13)*23)
        vertex.co=(x,y+face_depth(x,z+lift)-face_depth(x,z),z+lift)


def friendly_smile(mesh, face_depth, lip_color, mouth_color):
    """Fit a tapered smile and expanding opening to one continuous curve."""
    from mathutils import Vector
    def profile(u, smile):
        x=-.004 + (.056 + .006*smile)*u
        # Soft corners with a small asymmetry keep the resting smile gentle.
        lift=.010+.0045*smile
        z=1.439 + lift*u*u*(2-u*u) + .0017*u + .0015*smile
        return x,z

    def lip_rows(smile):
        vertices=[]
        for i in range(49):
            u=2*i/48-1
            x,z=profile(u,smile)
            width=.00075+.00115*max(0,1-u*u)**.68
            vertices.extend((x,face_depth(x,z+offset)-.002,z+offset) for offset in (-width,width))
        return vertices

    def mouth_rows(smile, mouth_open):
        vertices=[]
        for i in range(49):
            u=2*i/48-1
            x,z=profile(u,smile)
            z-=.0009
            gap=.00032+.0115*mouth_open*max(0,1-u*u)**.88
            lift=.007-.00945*mouth_open
            vertices.extend((x,face_depth(x,height)+lift,height) for height in (z-gap,z))
        return vertices

    faces=[(i,i+2,i+3,i+1) for i in range(0,96,2)]
    lip=mesh("Sculpted smile",lip_rows(0),faces,lip_color)
    lip.shape_key_add(name="Basis")
    for vertex, co in zip(lip.shape_key_add(name="smile").data,lip_rows(1)):
        vertex.co=co

    rest=mouth_rows(0,0)
    smiling=mouth_rows(1,0)
    opening=mouth_rows(1,1)
    mouth=mesh("Soft open smile",rest,faces,mouth_color)
    mouth.shape_key_add(name="Basis")
    for vertex, co in zip(mouth.shape_key_add(name="smile").data,smiling):
        vertex.co=co
    for vertex, base, closed, open_ in zip(mouth.shape_key_add(name="smileOpen").data,rest,smiling,opening):
        vertex.co=Vector(base)+Vector(open_)-Vector(closed)
    return lip,mouth
