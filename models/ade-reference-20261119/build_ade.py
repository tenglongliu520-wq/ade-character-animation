"""Build an authored 3D approximation of Ade from recording reference frames.

Run with Blender 4.5 Python module: python build_ade.py [--render]
The mesh, back and rig are authored here, not recovered from Meshy/video.
"""
from pathlib import Path
import argparse
import json
import math
import random
import struct
import bpy
from mathutils import Vector
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)
random.seed(19)
PI = math.pi
CHARACTER = []
WEIGHTS = {}


def color(value):
    rgb = [int(value[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb) + (1,)


def material(name, value, rough=.45, metallic=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = color(value)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = color(value)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metallic
    return m


def register(obj, mat, bone='spine'):
    if mat:
        obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    CHARACTER.append(obj)
    WEIGHTS[obj.name] = bone
    return obj


def mesh(name, verts, faces, mat, bone='spine', uvs=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    if uvs:
        layer = data.uv_layers.new(name='UVMap')
        for p in data.polygons:
            for i in p.loop_indices:
                layer.data[i].uv = uvs[data.loops[i].vertex_index]
    return register(obj, mat, bone)


def ellipsoid(name, loc, scale, mat, bone='head', segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return register(obj, mat, bone)


def tube(name, pts, radii, mat, bone='head', sides=10):
    verts, faces = [], []
    for i, p in enumerate(pts):
        p = Vector(p)
        tangent = Vector(pts[min(i+1, len(pts)-1)]) - Vector(pts[max(0, i-1)])
        tangent.normalize()
        reference = Vector((0, 1, 0))
        if abs(tangent.dot(reference)) > .92:
            reference = Vector((1, 0, 0))
        a = tangent.cross(reference).normalized()
        b = tangent.cross(a).normalized()
        r = radii[i] if isinstance(radii, list) else radii
        for j in range(sides):
            v = p + r * (a * math.cos(j*2*PI/sides) + b * math.sin(j*2*PI/sides))
            verts.append(tuple(v))
    for i in range(len(pts)-1):
        for j in range(sides):
            k=i*sides+j; n=i*sides+(j+1)%sides
            faces.append((k,n,n+sides,k+sides))
    faces += [tuple(reversed(range(sides))), tuple((len(pts)-1)*sides+j for j in range(sides))]
    return mesh(name, verts, faces, mat, bone)


def curve(name, points, radius, mat, bone='head'):
    # Conversion acts on every selected object. Isolate the curve so a prior
    # eye sphere does not lose its blink shape key during conversion.
    bpy.ops.object.select_all(action='DESELECT')
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2 if radius<.002 else 16
    d.bevel_depth=radius;d.bevel_resolution=1 if radius<.002 else 3
    s=d.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for p,co in zip(s.bezier_points,points):
        p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False)
    return register(o,mat,bone)


def ribbon(name, pts, width, mat, bone='spine'):
    vs=[]
    for i,p in enumerate(pts):
        t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)])
        side=t.cross(Vector((0,1,0))).normalized()*width/2
        vs.extend([tuple(Vector(p)-side),tuple(Vector(p)+side)])
    o=mesh(name,vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)],mat,bone)
    sol=o.modifiers.new('Cloth thickness','SOLIDIFY');sol.thickness=.008
    bevel=o.modifiers.new('Soft cloth edge','BEVEL');bevel.width=.004;bevel.segments=2
    return o


def bamboo_texture():
    im=Image.new('RGB',(1024,1024),(185,206,185));d=ImageDraw.Draw(im)
    rng=random.Random(37)
    for x in range(0,1024,3):
        d.line((x,0,x,1024),fill=(184+rng.randrange(4),204+rng.randrange(4),183+rng.randrange(4)))
    for j in range(14):
        x=rng.randint(40,980);y=rng.randint(60,960)
        angle=rng.uniform(-.5,.5);height=rng.randint(140,260)
        ink=rng.choice([(103,143,113),(122,155,129),(137,170,140)])
        dx=math.sin(angle)*height;dy=-math.cos(angle)*height
        d.line((x,y,x+dx,y+dy),fill=ink,width=3)
        for k in range(1,5):
            bx=x+dx*k/5;by=y+dy*k/5
            d.line((bx-4,by,bx+4,by-1),fill=ink,width=2)
            for side in (-1,1):
                length=rng.uniform(35,65);ex=bx+side*length;ey=by-rng.uniform(21,48)
                midx=(bx+ex)/2;midy=(by+ey)/2
                d.polygon([(bx,by),(midx-7,midy-9),(ex,ey),(midx+7,midy+8)],fill=ink)
    im.save(ROOT/'bamboo-cloth.png')


def robe_shell(name, mat, bone='spine', inner=False):
    vs,fs,uv=[],[],[]; nr=18;nt=64
    for iz in range(nr+1):
        t=iz/nr;z=.36+t*.88
        rx=.37-.15*t+.045*max(0,(t-.65)/.35)
        ry=.19-.045*t
        opening=.30+.30*t
        for j in range(nt+1):
            u=j/nt;theta=-PI/2+opening+u*(2*PI-2*opening)
            pleat=.007*math.sin(theta*12)*(1-t)**2
            vs.append(((rx+pleat)*math.cos(theta),(ry+pleat)*math.sin(theta),z+.012*math.cos(theta*5)*(1-t)))
            uv.append((u*.95,t*.95))
    for iz in range(nr):
        for j in range(nt):
            k=iz*(nt+1)+j;fs.append((k,k+1,k+nt+2,k+nt+1))
    o=mesh(name,vs,fs,mat,bone,uv)
    sol=o.modifiers.new('Woven cloth thickness','SOLIDIFY');sol.thickness=.008
    for side in (0,nt):
        pts=[vs[i*(nt+1)+side] for i in range(nr+1)]
        curve(name+' front seam '+str(side),[(x,y-.005,z) for x,y,z in pts],.008,TRIM,bone)
    curve(name+' hem',vs[:nt+1],.008,TRIM,bone)
    return o


def sleeve(side):
    a=Vector((side*.25,0,1.19));b=Vector((side*.35,-.015,.76))
    axis=(b-a).normalized();u=Vector((0,1,0));v=axis.cross(u).normalized()
    vs=[];uv=[];fs=[];n=12;s=32
    for i in range(n+1):
        t=i/n;center=a.lerp(b,t);r=.105+.025*t
        for j in range(s+1):
            theta=j/s*2*PI
            radius=r*(1+.025*math.sin(theta*7+t))
            p=center+u*math.cos(theta)*radius+v*math.sin(theta)*radius
            vs.append(tuple(p));uv.append((j/s,t))
    for i in range(n):
        for j in range(s):
            k=i*(s+1)+j;fs.append((k,k+1,k+s+2,k+s+1))
    bone='upper_arm.'+('L' if side>0 else 'R')
    o=mesh('Bamboo bell sleeve '+str(side),vs,fs,CLOTH,bone,uv)
    sol=o.modifiers.new('Sleeve thickness','SOLIDIFY');sol.thickness=.008
    curve('Ivory cuff '+str(side),vs[-(s+1):],.012,TRIM,bone)
    return b


def lock(name, cps, width, depth, mat):
    pts=[];rs=[]
    for i in range(19):
        t=i/18
        p=sum((Vector(cps[j])*(math.comb(3,j)*(1-t)**(3-j)*t**j) for j in range(4)),Vector())
        pts.append(p)
        rs.append(width*(.38+.85*math.sin(PI*t*.91))*(1-t)**.55+.001)
    # flattened swept locks give hair real thickness and a pointed tip.
    vs=[];fs=[];s=10
    for i,p in enumerate(pts):
        tangent=(pts[min(i+1,18)]-pts[max(0,i-1)]).normalized()
        normal=Vector((p.x,p.y,p.z-1.75)).normalized()
        cross=tangent.cross(normal).normalized()
        normal=cross.cross(tangent).normalized()
        for j in range(s):
            q=p+cross*math.cos(j*2*PI/s)*rs[i]+normal*math.sin(j*2*PI/s)*rs[i]*depth
            vs.append(tuple(q))
    for i in range(18):
        for j in range(s):
            k=i*s+j;next=i*s+(j+1)%s;fs.append((k,next,next+s,k+s))
    fs.extend([tuple(reversed(range(s))),tuple(18*s+j for j in range(s))])
    obj=mesh(name,vs,fs,mat,'head')
    # Fine modeled grooves follow each lock's sweep instead of an image plane.
    for strand,offset in enumerate((-.40,.05,.43)):
        fiber=[]
        for i in range(2,17):
            p=pts[i];tangent=(pts[i+1]-pts[i-1]).normalized()
            normal=Vector((p.x,p.y,p.z-1.75)).normalized()
            cross=tangent.cross(normal).normalized();normal=cross.cross(tangent).normalized()
            fiber.append(tuple(p+cross*rs[i]*offset+normal*rs[i]*depth*math.sqrt(1-offset*offset)))
        curve(name+' fiber '+str(strand),fiber,.0009,HAIR_FIBER,'head')
    return obj


def blink_key(obj, center_z, retract=False):
    obj.shape_key_add(name='Basis')
    key=obj.shape_key_add(name='blink')
    for v in key.data:
        global_z=v.co.z+obj.location.z
        v.co.z=center_z+(global_z-center_z)*.035-obj.location.z
        if retract:v.co.y+=.07


def create_character():
    # Skin and an intentionally large, softly tapered childlike face.
    face=ellipsoid('Continuous face', (0,-.015,1.68),(.405,.335,.385),SKIN,segments=64,rings=40)
    for vertex in face.data.vertices:
        x,y,z=vertex.co
        if y<0:
            # A smoothly projecting lower face replaces overlapping jaw spheres.
            vertex.co.y-=.065*math.exp(-((z+.23)/.105)**2)*math.exp(-(x/.26)**2)*min(1,-y/.08)
    for side in (-1,1):
        ellipsoid('Ear '+str(side),(side*.391,-.005,1.58),(.071,.055,.088),SKIN)
        ellipsoid('Inner ear '+str(side),(side*.411,-.048,1.58),(.031,.015,.047),EAR)
        x=side*.158
        eye=ellipsoid('Eye white '+str(side),(x,-.300,1.665),(.102,.042,.123),WHITE)
        iris=ellipsoid('Warm brown iris '+str(side),(x,-.337,1.660),(.077,.013,.096),IRIS)
        pupil=ellipsoid('Pupil '+str(side),(x,-.348,1.665),(.040,.006,.061),DARK)
        glint=ellipsoid('Eye light '+str(side),(x-.023,-.354,1.698),(.020,.004,.024),GLOSS,segments=20,rings=12)
        small=ellipsoid('Eye small light '+str(side),(x+.024,-.354,1.635),(.009,.004,.011),GLOSS,segments=16,rings=10)
        for o in (eye,iris,pupil,glint,small):blink_key(o,1.665,retract=True)
        eyelid=curve('Upper eyelid '+str(side),[(x-.100,-.316,1.706),(x-.063,-.335,1.771),(x+.020,-.338,1.780),(x+.100,-.316,1.726)],.007,HAIR_DARK)
        blink_key(eyelid,1.665)
        curve('Eyebrow '+str(side),[(x-.10,-.264,1.845),(x,-.296,1.868),(x+.087,-.274,1.85)],.014,HAIR_DARK)
        ellipsoid('Blush '+str(side),(side*.267,-.224,1.503),(.057,.014,.021),BLUSH,segments=24,rings=12)
    ellipsoid('Small nose',(0,-.351,1.548),(.038,.042,.035),SKIN)
    curve('Smile corners',[(-.068,-.347,1.454),(0,-.356,1.434),(.068,-.347,1.454)],.0065,LIP)
    mouth=ellipsoid('Mouth opening',(0,-.354,1.443),(.052,.008,.0055),MOUTH,segments=24,rings=12)
    mouth.shape_key_add(name='Basis');key=mouth.shape_key_add(name='jawOpen')
    for v in key.data:v.co.z*=7
    ellipsoid('Neck',(0,0,1.31),(.085,.079,.12),SKIN,'neck')
    ellipsoid('Ivory inner robe',(0,0,.82),(.254,.157,.46),IVORY,'spine')
    robe_shell('Open bamboo outer robe',CLOTH)
    # Crossed hanfu lapels with warm ivory edging.
    ribbon('Left lapel',[(-.17,-.122,1.24),(-.105,-.179,1.15),(.025,-.174,.993)],.065,TRIM)
    ribbon('Right lapel',[(.17,-.122,1.24),(.11,-.173,1.15),(-.005,-.183,1.02),(-.034,-.178,.94)],.067,IVORY)
    for side in (-1,1):
        cuff=sleeve(side);bone='hand.'+('L' if side>0 else 'R')
        ellipsoid('Hand '+str(side),(side*.375,-.05,.712),(.061,.052,.084),SKIN,bone,segments=24,rings=16)
        for finger in range(4):
            x=side*.375+(finger-1.5)*.022
            tube('Finger '+str(side)+' '+str(finger),[(x,-.081,.708),(x,-.09,.666),(x,-.08,.65+abs(finger-1.5)*.005)],[.013,.013,.009],SKIN,bone,8)
        ellipsoid('Thumb '+str(side),(side*.335,-.092,.704),(.023,.024,.043),SKIN,bone,segments=16,rings=12)
        leg='shin.'+('L' if side>0 else 'R');foot='foot.'+('L' if side>0 else 'R')
        ellipsoid('Loose ivory trousers '+str(side),(side*.14,0,.295),(.105,.108,.245),IVORY,leg)
        for fold in range(3):
            curve('Trouser fold '+str(side)+' '+str(fold),[(side*.14-.075,-.088,.18+fold*.045),(side*.14,-.111,.164+fold*.045),(side*.14+.075,-.088,.18+fold*.045)],.003,TRIM,leg)
        ellipsoid('Ivory shoe sole '+str(side),(side*.14,-.045,.055),(.121,.192,.045),TRIM,foot)
        ellipsoid('Cloth shoe '+str(side),(side*.14,-.055,.093),(.112,.177,.065),SHOE,foot)
        curve('Shoe seam '+str(side),[(side*.14-.09,-.14,.12),(side*.14,-.205,.126),(side*.14+.09,-.14,.12)],.005,IVORY,foot)
    # Belt conforms around waist, rather than a floating front rectangle.
    verts=[];faces=[]
    for z in (.86,.94):
        for j in range(65):
            t=j/64*2*PI;verts.append((.259*math.cos(t),.172*math.sin(t),z))
    for j in range(64):faces.append((j,j+1,66+j,65+j))
    belt=mesh('Deep green waist sash',verts,faces,GREEN,'spine')
    sol=belt.modifiers.new('Sash thickness','SOLIDIFY');sol.thickness=.006
    ribbon('Hanging sash left',[(.035,-.182,.9),(.015,-.204,.64),(-.002,-.208,.45)],.075,GREEN)
    ribbon('Hanging sash right',[(.107,-.18,.9),(.119,-.207,.67),(.165,-.211,.53)],.06,GREEN)
    ellipsoid('Sash clasp',(.075,-.189,.903),(.037,.014,.037),GOLD,'spine',segments=24,rings=12)
    for a in range(6):
        t=a*PI/3
        ellipsoid('Clasp petal '+str(a),(.075+.018*math.sin(t),-.204,.903+.018*math.cos(t)),(.007,.004,.01),TRIM,'spine',segments=12,rings=8)
    # Actual heart silhouette in a small shallow, rounded solid.
    vs=[]
    for y in (-.158,-.171):
        for j in range(48):
            t=j/48*2*PI;x=16*math.sin(t)**3;z=13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)
            vs.append((.197+x*.00155,y,1.144+z*.00155))
    fs=[tuple(reversed(range(48))),tuple(range(48,96))]+[(j,(j+1)%48,(j+1)%48+48,j+48) for j in range(48)]
    heart=mesh('Red heart badge',vs,fs,HEART)
    bevel=heart.modifiers.new('Rounded heart','BEVEL');bevel.width=.003;bevel.segments=3
    # Hair cap with a higher front hairline and lower nape.
    vs=[];fs=[];nt=64;nr=20
    for iz in range(nr+1):
        for j in range(nt+1):
            theta=j/nt*2*PI;end=1.38+.52*(math.sin(theta)+1)/2;phi=.001+iz/nr*end
            vs.append((.435*math.sin(phi)*math.cos(theta),.365*math.sin(phi)*math.sin(theta)+.015,1.76+.40*math.cos(phi)))
    for iz in range(nr):
        for j in range(nt):
            k=iz*(nt+1)+j;fs.append((k,k+nt+1,k+nt+2,k+1))
    mesh('Volumetric hair cap',vs,fs,HAIR_DARK,'head')
    # Flowing crown locks and asymmetric fringe.
    for j in range(25):
        theta=j/25*2*PI+.05*math.sin(j*2.1)
        start=Vector((-.07+.035*math.sin(j),.035+.025*math.cos(j),2.13+.025*math.sin(j*1.8)))
        end=Vector(((.46+.025*math.sin(j*2.7))*math.cos(theta),.39*math.sin(theta)+.015,1.81+.10*math.cos(theta)+.045*math.sin(j*1.7)))
        tangent=Vector((-math.sin(theta)*.11,math.cos(theta)*.11,.05*math.sin(j*2.8)))
        cps=[start,Vector((end.x*.35,end.y*.4,2.23+.035*math.sin(j*1.3))),end+tangent+Vector((0,0,.12)),end+tangent*1.9+Vector((0,0,.025))]
        lock('Crown swept lock %02d'%j,cps,.059+.01*math.sin(j),.49,HAIR[j%3])
    fringes=[
        [(-.02,-.12,2.11),(-.19,-.38,2.10),(-.37,-.39,1.89),(-.41,-.28,1.78)],
        [(.03,-.16,2.13),(-.01,-.39,2.02),(-.15,-.41,1.88),(-.23,-.37,1.82)],
        [(.08,-.16,2.12),(.15,-.39,2.00),(.04,-.43,1.89),(.01,-.393,1.79)],
        [(.15,-.12,2.10),(.33,-.29,2.03),(.34,-.37,1.90),(.43,-.29,1.85)],
        [(.23,-.10,2.06),(.43,-.22,2.04),(.40,-.31,1.83),(.34,-.30,1.76)],
    ]
    for j,cps in enumerate(fringes):
        for part in range(2):
            offset=Vector(((part-.5)*.052,-part*.008,.012*math.sin(j+part)))
            split=[tuple(Vector(p)+offset*(.4+.6*k/3)) for k,p in enumerate(cps)]
            split[-1]=tuple(Vector(split[-1])+Vector(((-1 if part==0 else 1)*.02,0,.025*math.cos(j))))
            lock('Forehead fringe %02d-%d'%(j,part),split,.048 if j!=2 else .038,.45,HAIR[(j+part)%3])
    lock('Raised crown curl',[(-.04,.02,2.14),(-.20,-.01,2.32),(-.33,-.01,2.30),(-.30,-.05,2.24)],.046,.5,HAIR[0])
    for side in (-1,1):
        for j in range(3):
            lock('Side wisp '+str(side)+' '+str(j),[(side*.36,.04-j*.04,1.94-j*.07),(side*.48,.02-j*.05,1.91-j*.06),(side*.48,-.02-j*.06,1.82-j*.07),(side*(.49-.025*j),-.1-j*.04,1.79-j*.07)],.055,.45,HAIR[j%3])
    for j in range(19):
        theta=-.05+j/18*(PI+.1)
        c=math.cos(theta);s=math.sin(theta)
        lower=1.53+.04*math.sin(j*2.3)
        lock('Layered nape lock %02d'%j,[(.29*c,.27*s+.015,2.03),(.45*c,.38*s+.015,1.96),(.46*c,.39*s+.015,1.72),(.41*c,.35*s+.015,lower)],.068,.43,HAIR[j%3])
    # Folded sage cap, knot and cloth tails; rear shape is authored interpretation.
    ellipsoid('Sage hair cap',(.08,.14,2.215),(.135,.12,.095),CAP,'head',segments=28,rings=16)
    curve('Cap stitching',[(-.025,.05,2.25),(.06,.028,2.278),(.16,.05,2.25)],.006,TRIM)
    ellipsoid('Ribbon knot',(.34,.18,1.91),(.07,.043,.06),CAP,'head',segments=24,rings=12)
    ribbon('Rear ribbon tail A',[(.35,.20,1.91),(.45,.23,1.72),(.50,.23,1.46)],.12,CAP,'head')
    ribbon('Rear ribbon tail B',[(.34,.21,1.91),(.32,.26,1.75),(.37,.27,1.54)],.09,CAP,'head')


def create_rig():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.armature_add(location=(0,0,0))
    rig=bpy.context.object;rig.name='Ade_Rig';bpy.ops.object.mode_set(mode='EDIT')
    eb=rig.data.edit_bones;eb.remove(eb[0])
    def add(name,head,tail,parent=None):
        b=eb.new(name);b.head=head;b.tail=tail
        if parent:b.parent=eb[parent]
    add('root',(0,0,0),(0,0,.15))
    add('pelvis',(0,0,.54),(0,0,.84),'root')
    add('spine',(0,0,.84),(0,0,1.22),'pelvis')
    add('neck',(0,0,1.22),(0,0,1.36),'spine')
    add('head',(0,0,1.36),(0,0,1.91),'neck')
    for side,s in [('L',1),('R',-1)]:
        add('upper_arm.'+side,(s*.25,0,1.19),(s*.32,-.01,.90),'spine')
        add('forearm.'+side,(s*.32,-.01,.90),(s*.37,-.03,.74),'upper_arm.'+side)
        add('hand.'+side,(s*.37,-.03,.74),(s*.375,-.06,.66),'forearm.'+side)
        add('thigh.'+side,(s*.14,0,.63),(s*.14,0,.34),'pelvis')
        add('shin.'+side,(s*.14,0,.34),(s*.14,0,.11),'thigh.'+side)
        add('foot.'+side,(s*.14,0,.11),(s*.14,-.16,.06),'shin.'+side)
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in CHARACTER:
        obj.select_set(False)
        obj.parent=rig
        group=obj.vertex_groups.new(name=WEIGHTS[obj.name]);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
        mod=obj.modifiers.new('Ade skeletal deformation','ARMATURE');mod.object=rig
    rig['source']='Authored from recording reference; not original Meshy geometry'
    rig['quality_status']='reference-model-v1-needs-likeness-review'
    return rig


def optimize_geometry():
    """Merge rigid, same-material parts and omit unused UVs before binding."""
    groups={}
    for o in list(CHARACTER):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active=o;o.select_set(True)
        for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
        if o.data.materials[0]!=CLOTH:
            for layer in list(o.data.uv_layers):o.data.uv_layers.remove(layer)
        if not o.data.shape_keys:
            groups.setdefault((WEIGHTS[o.name],o.data.materials[0].name),[]).append(o)
    for (bone,mat),objects in groups.items():
        if len(objects)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        active=objects[0];bpy.context.view_layer.objects.active=active
        for o in objects:CHARACTER.remove(o)
        bpy.ops.object.join()
        active.name='Ade '+bone+' '+mat
        CHARACTER.append(active);WEIGHTS[active.name]=bone
    bpy.ops.object.select_all(action='DESELECT')


def animate(rig):
    def action(name,frames,fn):
        rig.animation_data_clear()
        for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.scale=(1,1,1)
        for frame in frames:
            fn(frame)
            for b in rig.pose.bones:
                b.keyframe_insert('rotation_euler',frame=frame,group=b.name)
                b.keyframe_insert('scale',frame=frame,group=b.name)
        a=rig.animation_data.action;a.name=name;a.use_fake_user=True
        return a
    def idle(f):
        t=(f-1)/72*2*PI
        rig.pose.bones['spine'].rotation_euler=(.009*math.sin(t),0,.009*math.sin(t))
        rig.pose.bones['head'].rotation_euler=(0,.016*math.sin(t),-.012*math.sin(t))
        rig.pose.bones['spine'].scale=(1+.006*math.sin(t),1+.006*math.sin(t),1+.004*math.sin(t))
    def wave(f):
        age=(f-1)/72;mix=math.sin(min(1,age/.22)*PI/2)*math.sin(min(1,(1-age)/.22)*PI/2)
        rig.pose.bones['upper_arm.R'].rotation_euler=(.18*mix,0,1.95*mix)
        rig.pose.bones['forearm.R'].rotation_euler=(.15*mix,.12*math.sin(age*6*PI)*mix,.20*mix)
        rig.pose.bones['hand.R'].rotation_euler=(.20*math.sin(age*6*PI)*mix,0,0)
        rig.pose.bones['head'].rotation_euler=(0,-.06*mix,.05*mix)
    def think(f):
        t=(f-1)/72;mix=math.sin(PI*t)**.7
        rig.pose.bones['head'].rotation_euler=(.035*mix,-.11*mix,.045*mix)
        rig.pose.bones['upper_arm.L'].rotation_euler=(.08*mix,0,-.05*mix)
        rig.pose.bones['forearm.L'].rotation_euler=(.06*mix,0,-.06*mix)
    idle_action=action('idle',range(1,74,6),idle)
    action('wave',range(1,74,3),wave)
    action('think',range(1,74,3),think)
    rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=idle_action
    bpy.context.scene.frame_set(1)


def setup_scene():
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
    scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=950;scene.render.resolution_percentage=100
    scene.world.color=(.22,.22,.22)
    scene.view_settings.view_transform='AgX'
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    floor=material('Studio warm background','f6f4ec',.8)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.005));bpy.context.object.name='Studio floor';bpy.context.object.data.materials.append(floor)
    def area(name,loc,power,size):
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
        o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc
        o.rotation_euler=(Vector((0,0,1.1))-o.location).to_track_quat('-Z','Y').to_euler()
    area('Softbox key',(-3,-4,5),450,4)
    area('Softbox fill',(3,-2,3),240,3)
    area('Hair rim',(1,3,4),400,3)
    camd=bpy.data.cameras.new('Portrait camera');cam=bpy.data.objects.new('Portrait camera',camd);bpy.context.collection.objects.link(cam)
    camd.type='ORTHO';camd.ortho_scale=2.65;scene.camera=cam
    cam.location=(0,-5,2.05)
    cam.rotation_euler=(Vector((0,0,1.09))-cam.location).to_track_quat('-Z','Y').to_euler()
    return cam


def export(rig):
    # Apply actual garment thickness and badge bevel before glTF export. Keep
    # armature and shape keys live; export_apply would otherwise drop morphs.
    bpy.ops.object.select_all(action='DESELECT')
    for o in CHARACTER:
        bpy.context.view_layer.objects.active=o;o.select_set(True)
        for mod in list(o.modifiers):
            if mod.type!='ARMATURE':bpy.ops.object.modifier_apply(modifier=mod.name)
        o.select_set(False)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    for o in CHARACTER:o.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'ade.glb'),export_format='GLB',use_selection=True,
        export_animations=True,export_animation_mode='ACTIONS',export_skins=True,export_morph=True,
        export_apply=False,export_yup=True,export_force_sampling=True,export_frame_range=False)
    normalize_skin_roots(ROOT/'ade.glb')
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'ade.blend'))
    report={'blender_version':bpy.app.version_string,'model':'ade.glb','source':'build_ade.py',
        'method':'authored volumetric approximation from video-derived reference; not original model recovery',
        'objects':len(CHARACTER),'vertices_before_modifiers':sum(len(o.data.vertices) for o in CHARACTER),
        'bones':len(rig.data.bones),'actions':[a.name for a in bpy.data.actions],
        'limitations':['back and hidden anatomy authored','rigid part weights; not production organic skinning','no cloth simulation','likeness needs visual review','audio level mouth control is not phoneme lip sync']}
    (ROOT/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


def normalize_skin_roots(path):
    """Remove an identity export grouping parent above skinned meshes.

    glTF requires skins to carry their own transforms. The Blender armature
    grouping is identity here, so making mesh nodes scene roots preserves
    geometry and joints while avoiding ignored parent-transform semantics.
    """
    data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0]
    g=json.loads(data[20:20+n]);nodes=g['nodes']
    parents={child:i for i,node in enumerate(nodes) for child in node.get('children',[])}
    for i,node in enumerate(nodes):
        if 'skin' not in node or i not in parents:continue
        parent=nodes[parents[i]]
        assert parent['name']=='Ade_Rig' and not any(k in parent for k in ('matrix','translation','rotation','scale'))
        assert not any(c['target']['node']==parents[i] for a in g.get('animations',[]) for c in a['channels'])
        parent['children'].remove(i)
        for scene in g['scenes']:
            if parents[i] in scene['nodes']:scene['nodes'].append(i)
    raw=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode('utf8')
    raw+=b' '*((-len(raw))%4)
    remainder=data[20+n:]
    path.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(raw)+len(remainder))+struct.pack('<II',len(raw),0x4E4F534A)+raw+remainder)


def render_views(cam,rig):
    scene=bpy.context.scene
    for label,position in [('front',(0,-5,2.05)),('three-quarter',(3,-5,2.1)),('side',(5,-.1,1.8)),('back',(0,5,1.9))]:
        cam.location=position;cam.rotation_euler=(Vector((0,0,1.09))-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(ROOT/(label+'.png'));bpy.ops.render.render(write_still=True)
    rig.animation_data.action=bpy.data.actions['wave'];scene.frame_set(34)
    cam.location=(0,-5,2.05);cam.rotation_euler=(Vector((0,0,1.09))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(ROOT/'wave.png');bpy.ops.render.render(write_still=True)
    rig.animation_data.action=bpy.data.actions['idle'];scene.frame_set(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');args=parser.parse_args()
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    SKIN=material('Warm porcelain skin','ffd2ad',.55)
    EAR=material('Warm ear recess','e9a78e',.65)
    WHITE=material('Eye porcelain white','fffdf5',.24)
    IRIS=material('Chestnut iris','704230',.2)
    DARK=material('Dark pupil','241a19',.16)
    GLOSS=material('Eye catchlight','ffffff',.1)
    BLUSH=material('Peach cheeks','f3ad98',.7)
    LIP=material('Smile','a76a59',.5);MOUTH=material('Mouth inside','6e3532',.6)
    IVORY=material('Ivory fabric','f0e8d5',.85);TRIM=material('Warm ivory borders','e2d8bd',.8)
    GREEN=material('Deep sage sash','385a47',.65);GOLD=material('Antique brass clasp','a68e53',.45,.25)
    SHOE=material('Charcoal cloth shoes','343633',.8);HEART=material('Coral heart','df6d55',.4)
    CAP=material('Sage hair accessory','a8bba4',.8)
    HAIR_DARK=material('Hair dark chestnut','4c2b20',.46)
    HAIR_FIBER=material('Subtle hair fibers','86583a',.64)
    HAIR=[material('Chestnut hair '+str(i),c,.54) for i,c in enumerate(['603a25','70432c','593322'])]
    bamboo_texture();CLOTH=material('Sage bamboo silk','b9ceb9',.82)
    node=CLOTH.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(ROOT/'bamboo-cloth.png'));node.image.pack()
    CLOTH.node_tree.links.new(node.outputs['Color'],CLOTH.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    create_character();optimize_geometry();rig=create_rig();animate(rig);cam=setup_scene();export(rig)
    if args.render:render_views(cam,rig)
    print('ADE_BUILD_OK',str(ROOT/'ade.glb'),flush=True)
