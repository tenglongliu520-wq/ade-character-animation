"""Refine Ade against recording silhouettes using genuine curved 3D surfaces.
Original generated input is retained unchanged. This is a new, unaccepted
visual iteration; no previous rig or animation is claimed as complete.
"""
from pathlib import Path
import bpy,bmesh,math,json,random,argparse
from mathutils import Vector
from PIL import Image,ImageDraw
from recording_details import EYES, EYE_CROPS, SKIN_RGB, INNER_EAR_RGB
from fit_details import add_hair_tip_shape, hair_lock, recorded_coordinates, smooth_samples
from expression_motion import add_acknowledgment, PEAK
from bamboo_embroidery import add_bamboo
from relaxed_hands import add_relaxed_hand
from facial_expression import add_gaze, lid_meshes, brow_expression, friendly_smile
ROOT=Path(__file__).resolve().parent;PI=math.pi;PARTS=[]
parser=argparse.ArgumentParser();parser.add_argument('--quick',action='store_true');args=parser.parse_args()
def rgba(h):
 a=[int(h[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1,)
def material(name,h,rough=.85,texture=None):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=rgba(h);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.10
 if texture:
  n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(ROOT/texture));n.image.pack();m.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color'])
 return m
def register(o,mat=None):
 if mat:o.data.materials.append(mat)
 for f in o.data.polygons:f.use_smooth=True
 PARTS.append(o);return o
def mesh(name,vs,fs,mat,uv=None):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
 if uv:
  l=d.uv_layers.new(name='SurfaceUV')
  for f in d.polygons:
   for i in f.loop_indices:l.data[i].uv=uv[d.loops[i].vertex_index]
 return register(o,mat)
def sphere(name,loc,size,mat,segments=48,rings=32):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return register(o,mat)
def curve(name,pts,radius,mat,radii=None):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=12;d.bevel_depth=radius;d.bevel_resolution=3;s=d.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
 for p,co in zip(s.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 if radii:
  for point,taper in zip(s.bezier_points,radii):point.radius=taper
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');return register(bpy.context.object,mat)
def project(o):
 for l in list(o.data.uv_layers):o.data.uv_layers.remove(l)
 l=o.data.uv_layers.new(name='RecordingColorProjection')
 for f in o.data.polygons:
  for i in f.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[i].vertex_index].co;l.data[i].uv=((302+p.x*376)/720,1-(915-p.z*376)/950)

def bake_hair_color(obj, recorded, rear):
 """Blend the observed chestnut color into the inferred back across the side."""
 attribute = obj.data.color_attributes.new(name="HairColor",type="FLOAT_COLOR",domain="POINT")
 obj.data.color_attributes.active_color = attribute
 for vertex, color in zip(obj.data.vertices, attribute.data):
  x, y, z = vertex.co
  u = min(1023,max(0,round((302+x*376)/720*1023)))
  v = min(1023,max(0,round((915-z*376)/950*1023)))
  angle = (math.atan2(y,x)/(2*PI)+.5)%1
  height = (1-z*1.3)%1
  front_rgb = recorded.getpixel((u,v))
  rear_rgb = rear.getpixel((int(angle*1023),int(height*1023)))
  mix = min(1,max(0,(y+.125)/.32))
  mix = mix*mix*(3-2*mix)
  color.color_srgb = tuple((a*(1-mix)+b*mix)/255 for a,b in zip(front_rgb,rear_rgb))+(1,)

def bake_fabric(obj, coordinates):
 """Blend observed garment motifs on the front into authored UVs on the back."""
 color_layer = obj.data.color_attributes.new(name="FabricColor",type="FLOAT_COLOR",domain="POINT")
 obj.data.color_attributes.active_color = color_layer
 for vertex, color, (u,v) in zip(obj.data.vertices,color_layer.data,coordinates):
  x,y,z = vertex.co
  pixel = (
   min(719,max(0,round(302+x*376))),
   min(949,max(0,round(915-z*376))),
  )
  red,green,blue,alpha = recorded_fabric.getpixel(pixel)
  base = authored_fabric.getpixel((int((u%1)*2047),int((1-v)%1*2047)))
  facing = min(1,max(0,(-y-.018)/.095))
  weight = facing*facing*(3-2*facing)
  # The center of the visible garment uses the recording palette. Shapes
  # outside the traced cloth panels inherit the authored bamboo material.
  observed = (red,green,blue)
  coverage = alpha/255
  blend = weight * coverage
  color.color_srgb = tuple((a*(1-blend)+b*blend)/255 for a,b in zip(base,observed))+(1,)

def use_vertex_color(mat, name):
 node=mat.node_tree.nodes.new("ShaderNodeVertexColor")
 node.layer_name=name
 shader=mat.node_tree.nodes["Principled BSDF"]
 mat.node_tree.links.new(node.outputs["Color"],shader.inputs["Base Color"])
def thick(o,value=.004):
 mod=o.modifiers.new('Fabric thickness','SOLIDIFY');mod.thickness=value
def interpolate(rows,z):
 for i in range(len(rows)-1):
  if rows[i][0]<=z<=rows[i+1][0]:
   h=rows[i+1][0]-rows[i][0];t=(z-rows[i][0])/h;prev=rows[max(0,i-1)];nxt=rows[min(len(rows)-1,i+2)];out=[]
   for k in range(1,len(rows[i])):
    m0=(rows[i+1][k]-prev[k])/(rows[i+1][0]-prev[0]);m1=(nxt[k]-rows[i][k])/(nxt[0]-rows[i][0]);out.append((2*t**3-3*t*t+1)*rows[i][k]+(t**3-2*t*t+t)*h*m0+(-2*t**3+3*t*t)*rows[i+1][k]+(t**3-t*t)*h*m1)
   return out
 return rows[-1][1:]
def loft(name,rows,mat,open_front=False,pleats=.003):
 vs=[];fs=[];uv=[];n=96;nz=64
 for k in range(nz+1):
  z=rows[0][0]+(rows[-1][0]-rows[0][0])*k/nz;vals=interpolate(rows,z);rx,ry=vals[:2];opening=math.asin(min(.95,vals[2]/rx)) if open_front else 0
  for j in range(n+1):
   theta=-PI/2+opening+(2*PI-2*opening)*j/n;wr=pleats*math.sin(theta*11+z*5)*(1-k/nz)**1.3;x=(rx+wr)*math.cos(theta);y=(ry+wr)*math.sin(theta);zz=z+.006*math.cos(theta*5)*(1-k/nz)**4
   vs.append((x,y,zz));uv.append((j/n*1.8,(z-.25)*1.3))
 for k in range(nz):
  for j in range(n):a=k*(n+1)+j;fs.append((a,a+1,a+n+2,a+n+1))
 o=mesh(name,vs,fs,mat,uv);thick(o,.004)
 if mat==CLOTH:
  bake_fabric(o,uv)
 if not open_front:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.to_mesh(o.data);bm.free()
 if open_front:
  for j in (0,n):curve(name+' thin opening edge '+str(j),[vs[k*(n+1)+j] for k in range(0,nz+1,4)],.0035,TRIM)
 curve(name+' thin hem',vs[:n+1],.0035,TRIM if open_front else INNER_CLOTH)
 return o
def ribbon(name,pts,width,mat,uvscale=1,fold=0,taper=0):
 controls=[Vector(p) for p in pts];sample=[]
 for k in range(len(controls)-1):
  a=controls[max(0,k-1)];b=controls[k];c=controls[k+1];d=controls[min(len(controls)-1,k+2)]
  for step in range(8):
   t=step/8;sample.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)))
 sample.append(tuple(controls[-1]));pts=sample
 vs=[];fs=[];uv=[]
 for i,p in enumerate(pts):
  t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)]);axis=t.cross(Vector((0,1,0))).normalized()*width/2
  progress=i/max(1,len(pts)-1)
  for side in (-1,0,1):
   edge=Vector(p)+axis*side*(1-taper*progress**5)
   edge.y+=fold*(side*(.18+.8*progress)-.50*(1-abs(side)))
   edge.z+=fold*.43*side*progress
   vs.append(tuple(edge));uv.append(((side+1)/2,progress*uvscale))
 for i in range(len(pts)-1):
  for j in range(2):
   a=i*3+j;fs.append((a,a+1,a+4,a+3))
 o=mesh(name,vs,fs,mat,uv);thick(o,.004);return o

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
SKIN=material('Warm ivory skin',''.join(f'{channel:02x}' for channel in SKIN_RGB));FACE=material('Skin and blush only','ffffff',texture='skin-blush.png');EAR=material('Ear soft pink',''.join(f'{channel:02x}' for channel in INNER_EAR_RGB));INNER_CLOTH=material('Celadon mist inner robe','cfdcd8');TRIM=material('Thin pale seam','d9e1cc');CLOTH=material('Dense bamboo sage cloth','ffffff',texture='bamboo-cloth.png');GREEN=material('Dark green sash','1e382c');SASH=material('Bamboo woven hanging sash','ffffff',texture='bamboo-sash.png');BLACK=material('Black cloth shoe','16171c');SOLE=material('Thin ivory sole','e6e0d3');CAP=material('Pale sage hair tie','cad8c0');HAIR=material('Recorded chestnut hair','ffffff',texture='hair-color.png');BROW=material('Chestnut eyebrows','714333');LASH=material('Warm dark upper eyelid','493334');WHITE=material('Eye white','fffaf2',.35);IRIS=material('Brown iris','8d5534',.38);RIM=material('Iris dark rim','4e332e',.4);PUPIL=material('Deep pupil','251e25',.30);LIGHT=material('Eye catchlight','ffffff',.24);LIP=material('Small smile','bd8b86');HEART=material('Red heart badge','e66a54')
for node in list(CLOTH.node_tree.nodes):
 if node.type=="TEX_IMAGE":
  CLOTH.node_tree.nodes.remove(node)
CLOTH.name="Blended recorded bamboo fabric"
use_vertex_color(CLOTH,"FabricColor")
recorded_fabric=Image.open(ROOT/"recorded-fabric.png").convert("RGBA")
authored_fabric=Image.open(ROOT/"bamboo-cloth.png").convert("RGB")

# Layered hair geometry from the actual generated volume, with accessory removed.
REAR=material('Inferred chestnut rear strands','ffffff',texture='inferred-rear-hair.png')
hair_surface=material("Chestnut strands with blended side color","ffffff",.78)
recorded_hair=Image.open(ROOT/'hair-color.png').convert('RGB')
inferred_hair=Image.open(ROOT/'inferred-rear-hair.png').convert('RGB')
bpy.ops.import_scene.gltf(filepath=str(ROOT/'source-geometry.glb'));raw=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@v.co for o in raw for v in o.data.vertices];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);mid=(hi+lo)/2;scale=2.3/(hi.z-lo.z);ref=Image.open(ROOT/'reference-front.png').convert('RGB')
cap_mask=Image.new('1',(720,950));ImageDraw.Draw(cap_mask).polygon([(311,48),(369,48),(406,67),(424,105),(420,143),(384,137),(358,119),(331,110),(310,94)],fill=1)
for o in raw:
 for v in o.data.vertices:
  p=o.matrix_world@v.co;v.co=((p.x-mid.x)*scale*.91,(p.y-mid.y)*scale,(p.z-lo.z)*scale)
 o.matrix_world.identity();bm=bmesh.new();bm.from_mesh(o.data);remove=[]
 for v in bm.verts:
  x,y,z=v.co;px=max(0,min(719,round(302+x*376)));py=max(0,min(949,round(915-z*376)));r,g,b=ref.getpixel((px,py));hairpixel=45<r<220 and r>g*1.20 and r>b*1.35;mint=g>110 and g>r*.97 and g>b*1.03
  accessory=(x>.30 and y>.015 and z<1.96) or (z>2.05 and cap_mask.getpixel((px,py)))
  # Recess the imported central edge behind the newly swept hairline.
  forehead_cut=1.70+.187*math.exp(-(x/.145)**4)
  exposed_fringe=y<-.135 and z<forehead_cut
  if accessory or exposed_fringe or ((z<1.64 or (z<1.81 and not hairpixel)) if y<.11 else z<1.59):remove.append(v)
  elif z>2.21 and x>-.05:
   # Only the narrow former cap attachment needs to be tucked under the fabric.
   v.co.z=2.21+(z-2.21)*.14
 bmesh.ops.delete(bm,geom=remove,context='VERTS');bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=24);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.name='Reference layered hair';o.data.materials.clear();register(o,hair_surface)
 bake_hair_color(o, recorded_hair, inferred_hair)
use_vertex_color(hair_surface,"HairColor")

# Width and depth are fitted independently so the tips keep volume from the side.
fringe_controls = {
 "Soft parted hairline": [(274,185,-.226,.026,.029),(294,197,-.265,.040,.033),
  (316,209,-.267,.040,.021),(337,208,-.261,.043,.024),(362,208,-.247,.031,.023)],
 "Central swept fringe": [(234,147,-.198,.020,.023),(252,174,-.251,.040,.035),
  (265,207,-.281,.044,.034),(274,237,-.289,.039,.029),
  (277,259,-.295,.029,.020),(287,279,-.302,.016,.013),(311,285,-.292,.001,.002)],
 "Inner fringe wisp": [(259,192,-.248,.019,.023),(260,224,-.276,.029,.025),
  (249,250,-.290,.023,.015),(253,272,-.294,.012,.008),(276,290,-.289,.001,.002)],
 "Swept left front lock": [(274,153,-.223,.021,.026),(237,169,-.253,.045,.035),
  (218,199,-.274,.050,.036),(202,228,-.267,.036,.025),
  (184,257,-.222,.028,.019),(156,268,-.179,.015,.012),(136,251,-.145,.001,.002)],
 "Swept right front lock": [(310,155,-.188,.018,.024),(334,178,-.226,.046,.035),
  (351,209,-.260,.044,.035),(358,238,-.268,.036,.024),
  (373,268,-.247,.023,.015),(394,293,-.203,.001,.003)],
 "Left temple curl": [(208,196,-.176,.025,.020),(185,225,-.211,.036,.027),
  (163,257,-.181,.035,.026),(147,274,-.136,.023,.017),
  (153,289,-.121,.013,.011),(173,291,-.122,.001,.002)],
 "Right cheek sweep": [(360,175,-.179,.022,.025),(384,206,-.219,.040,.033),
  (403,240,-.217,.039,.028),(424,261,-.182,.028,.020),
  (455,268,-.136,.014,.011),(476,251,-.093,.001,.002)],
 "Right raised temple curl": [(388,166,-.118,.022,.019),(419,190,-.134,.034,.024),
  (444,207,-.128,.028,.021),(464,209,-.100,.012,.012),(481,190,-.071,.001,.002)],
 "Left temple hairline taper": [(174,239,-.171,.023,.020),(170,265,-.169,.032,.026),
  (181,289,-.156,.024,.017),(193,307,-.133,.014,.010),(207,323,-.134,.001,.002)],
 "Right temple hairline taper": [(403,230,-.177,.023,.025),(415,254,-.159,.031,.024),
  (416,279,-.146,.026,.018),(414,297,-.138,.017,.011),(401,320,-.138,.001,.002)],
}
tip_movement = {
 "Central swept fringe": ((.011,-.008,.010),0),
 "Swept left front lock": ((-.014,-.010,.015),1),
 "Swept right front lock": ((.010,-.009,.013),2),
 "Left temple curl": ((-.012,-.006,.013),3),
 "Right raised temple curl": ((.016,-.006,.015),4),
}
moving_hair=[]
for name,controls in fringe_controls.items():
 vertices,faces=hair_lock(controls)
 lock=mesh(name,vertices,faces,hair_surface)
 bake_hair_color(lock,recorded_hair,inferred_hair)
 if name in tip_movement:
  delta,delay=tip_movement[name]
  add_hair_tip_shape(lock,delta)
  moving_hair.append((lock,delay))
# The visible side curls turn under the cap toward the nape. The rear ends are
# inferred because the recordings show the ears and temples at oblique angles.
for sign in (-1,1):
 controls=[
  (302+sign*101,227,.195,.045,.027),
  (302+sign*115,260,.208,.041,.024),
  (302+sign*104,291,.218,.032,.020),
  (302+sign*90,317,.191,.020,.013),
  (302+sign*72,316,.167,.002,.003),
 ]
 vertices,faces=hair_lock(controls)
 lock=mesh('Tapered nape lock '+str(sign),vertices,faces,hair_surface)
 bake_hair_color(lock,recorded_hair,inferred_hair)
# Rounded rear mass with recorded brown field; all rear strands remain inferred.
underlay=sphere('Continuous hair underlayer',(0,.04,1.87),(.325,.260,.300),REAR)
bm=bmesh.new();bm.from_mesh(underlay.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v.co.z<-.10 if v.co.y<.08 else v.co.z<-.32)],context='VERTS');bm.to_mesh(underlay.data);bm.free()
FACE_Z=1.646
FACE_HEIGHT_RADIUS=.308

# Face-only silhouette traced on the 401 x 225 close-up, excluding the ears.
# Eye-centre spacing in that frame maps the trace to the existing eye rig.
# Use sparse chin landmarks so the neck junction does not add a kink.
FACE_TRACE=((220,158,191),(209,135,213),(200,123,221),
            (193,116,226),(186,113,229),(179,111,230),(171,111,230),(155,111,229))
FACE_TRACE_SCALE=.00434
FACE_WIDTH_ROWS=[(FACE_Z-FACE_HEIGHT_RADIUS-.001,.59)]
for image_y,left,right in FACE_TRACE:
 z=1.565+(171.5-image_y)*FACE_TRACE_SCALE
 traced_width=(right-left)*FACE_TRACE_SCALE/2
 radial_width=.310*math.sqrt(1-((z-FACE_Z)/FACE_HEIGHT_RADIUS)**2)
 FACE_WIDTH_ROWS.append((z,traced_width/radial_width))
FACE_WIDTH_ROWS.extend([(1.687,.89),(1.772,.97),(FACE_Z+FACE_HEIGHT_RADIUS+.001,1)])

def jaw_width(z):
 return interpolate(FACE_WIDTH_ROWS,z)[0]

def cheek_relief(x,z):
 lower_face=.015*math.exp(-((z-1.472)/.133)**2)
 cheeks=.017*math.exp(-((abs(x)-.167)/.079)**2-((z-1.488)/.072)**2)
 eye_socket=.004*math.exp(-((abs(x)-.146)/.085)**2-((z-1.588)/.055)**2)
 return lower_face+cheeks-eye_socket

def face_y(x,z):
 width=.310*jaw_width(z)
 profile=((z-FACE_Z)/FACE_HEIGHT_RADIUS)**2
 depth=.265*math.sqrt(max(.001,1-(x/width)**2-profile))
 fade=min(1,depth/.12)
 return -.015-depth-cheek_relief(x,z)*fade*fade*(3-2*fade)

head=sphere('Soft tapered face',(0,-.015,FACE_Z),(.310,.265,FACE_HEIGHT_RADIUS),FACE,96,96)
for v in head.data.vertices:
 z=v.co.z+FACE_Z
 v.co.x*=jaw_width(z)
 if v.co.y<0:
  weight=min(1,-v.co.y/.12)
  v.co.y-=cheek_relief(v.co.x,z)*weight*weight*(3-2*weight)
project(head)
for f in head.data.polygons:
 if f.center.y>0:
  for i in f.loop_indices:head.data.uv_layers.active.data[i].uv=(.01,.01)
head.shape_key_add(name="Basis")
cheek_lift=head.shape_key_add(name="cheekLift")
for vertex in cheek_lift.data:
 x,y,z=vertex.co
 if y>=0:
  continue
 strength=math.exp(-((abs(x)-.165)/.077)**2-((z+FACE_Z-1.486)/.049)**2)*min(1,-y/.18)
 vertex.co.y-=.005*strength
 vertex.co.z+=.013*strength
def recorded_eye(name, contour, crop):
 """Trace the observed eye and wrap its recorded color over a curved surface."""
 corners = [Vector(p) for p in contour]
 center = sum(corners, Vector((0, 0))) / len(corners)
 boundary = []
 for index, point in enumerate(corners):
  prev, end, after = [corners[i % len(corners)] for i in (index-1,index+1,index+2)]
  for step in range(5):
   t = step / 5
   boundary.append(.5 * (2*point + (end-prev)*t + (2*prev-5*point+4*end-after)*t*t + (-prev+3*point-3*end+after)*t**3))
 vertices, faces, uv, radii = [], [], [], []
 def add_pixel(point, radius):
  px, py = point
  x, z = (px-302)/376, (915-py)/376
  y = face_y(x,z) - .0018 - .0048*(1-radius*radius)
  vertices.append((x,y,z))
  radii.append(radius)
  u,v,w,h = crop
  uv.append(((px-u)/(w-u),1-(py-v)/(h-v)))
 add_pixel(center, 0)
 count = len(boundary)
 rings = 18
 for ring in range(1, rings+1):
  for point in boundary:
   add_pixel(center.lerp(point,ring/rings), ring/rings)
 for j in range(count):
  faces.append((0,1+(j+1)%count,1+j))
 for ring in range(rings-1):
  for j in range(count):
   a=1+ring*count+j
   b=1+ring*count+(j+1)%count
   faces.append((a,b,b+count,a+count))
 mat=material(f"Recorded {name} iris and lash color","ffffff",.72,texture=f"eye-{name}.png")
 eye=mesh(f"Curved recorded eye {name}",vertices,faces,mat,uv)
 add_gaze(eye,radii,name,face_y)
 lids,lash=lid_meshes(name,boundary,mesh,face_y,FACE,LASH)
 return eye,lids,lash

def sculpt_ear(side):
 """Fit a continuous outer rim, shallow bowl, and tapered earlobe."""
 width,depth,height=.062,.052,.060
 ear=sphere('Soft ear '+str(side),(side*.285,-.013,1.529),(width,depth,height),EAR,64,48)
 colors=ear.data.color_attributes.new(name='EarColor',type='FLOAT_COLOR',domain='POINT')
 ear.data.color_attributes.active_color=colors
 cosine,sine=math.cos(.24),math.sin(.24)
 for vertex,color in zip(ear.data.vertices,colors.data):
  x,y,z=vertex.co
  outward=side*x/width
  vertical=z/height
  radius=math.hypot((outward-.49+.10*vertical)/.36,(vertical-.09)/.57)
  front=max(0,min(1,-y/.036))
  front=front*front*(3-2*front)
  bowl=front*math.exp(-radius*radius)
  rim=front*math.exp(-((radius-1.12)/.29)**2)
  # Angle the ear to show the rim and bowl in the three-quarter view.
  local_x=side*x+.008*vertical-.007*vertical*vertical
  local_y=y+.017*bowl-.0035*rim
  vertex.co.x=side*(cosine*local_x-sine*local_y)
  vertex.co.y=sine*local_x+cosine*local_y
  tint=.84*bowl
  color.color_srgb=tuple((base*(1-tint)+inner*tint)/255 for base,inner in zip(SKIN_RGB,INNER_EAR_RGB))+(1,)
 return ear

EAR.name='Ear skin with soft inner tint'
use_vertex_color(EAR,'EarColor')
eye_groups=[recorded_eye(name,contour,EYE_CROPS[name]) for name,contour in EYES.items()]
brow_meshes=[]
brow_traces=[[(216,290),(229,286),(241,286),(252,290)],
             [(329,292),(340,288),(351,287),(363,292)]]
for side in (-1,1):
 sculpt_ear(side)
 coordinates=[recorded_coordinates(px,py) for px,py in brow_traces[int(side>0)]]
 taper=(.14,.69,1,.58) if side<0 else (.61,1,.76,.14)
 brow=curve('Sculpted brow '+str(side),[(x,face_y(x,z)-.002,z) for x,z in coordinates],.0105,BROW,taper)
 brow_expression(brow,side,face_y)
 brow_meshes.append(brow)
sphere('Small sculpted nose',(0,face_y(0,1.486)+.005,1.486),(.016,.013,.012),SKIN)
smile,smile_open=friendly_smile(mesh,face_y,LIP,material('Soft rose mouth interior','a87573'))
HEAD_PARTS=set(PARTS)
sphere('Neck',(0,0,1.323),(.063,.067,.105),SKIN)

# Continuous sloping shoulders and curved open coat replace the old cylinders.
inner_robe=loft('Inner garment',[(.222,.195,.125),(.42,.205,.133),(.98,.198,.137),(1.20,.18,.115),(1.319,.074,.072)],INNER_CLOTH,pleats=.0035)
add_bamboo(inner_robe,material,mesh,curve)
outer_coat=loft('Flowing open bamboo coat',[(.30,.363,.178,.192),(.48,.309,.147,.170),(.68,.268,.159,.155),(.85,.244,.146,.131),(1.03,.213,.142,.126),(1.17,.205,.125,.096),(1.28,.138,.098,.070),(1.32,.078,.073,.044)],CLOTH,True,.012)
for side in (-1,1):
 vs=[];fs=[];uv=[];nr=72;nt=96
 rows=[(0,.130,1.25,.048,.063),(.18,.178,1.185,.079,.091),(.48,.252,1.035,.098,.115),(.78,.278,.873,.118,.133),(1,.285,.737,.122,.128)]
 for k in range(nr+1):
  t=k/nr;cx,z,rx,ry=interpolate(rows,t);axis=Vector((side*.24,0,-.97));u=Vector((0,1,0));v=axis.cross(u).normalized()
  for j in range(nt+1):
   a=j/nt*2*PI
   fold=.075*math.sin(a*4+t*2)+.014*math.sin(a*7-t*4)
   wr=1+fold*t**1.6
   p=Vector((side*cx,-.023*t,z))+u*math.cos(a)*ry*wr+v*math.sin(a)*rx*wr
   p.z+=(.038*math.cos(a)+.013*math.sin(a*3+.4*side))*t**3
   vs.append(tuple(p));uv.append((j/nt*.84+(side+1)*.16,t*.75))
 for k in range(nr):
  for j in range(nt):a=k*(nt+1)+j;fs.append((a,a+1,a+nt+2,a+nt+1))
 o=mesh('Soft bell sleeve '+str(side),vs,fs,CLOTH,uv);thick(o,.004)
 bake_fabric(o,uv)
 edge=vs[-nt-1:];facing=[]
 for x,y,z in edge:
  facing.extend([(x,y,z),(.285*side+(x-.285*side)*.83,-.023+(y+.023)*.83,z-.026)])
 mesh('Inner cuff facing '+str(side),facing,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(nt)],INNER_CLOTH)
 curve('Thin cuff seam '+str(side),edge,.004,TRIM)
 add_relaxed_hand(side,SKIN,mesh)
 # Only short soft trouser hems remain visible below the long inner garment.
 leg=loft('Loose trouser hem '+str(side),[(.096,.065,.072),(.15,.080,.086),(.23,.095,.103),(.36,.096,.100)],INNER_CLOTH,pleats=.004)
 for v in leg.data.vertices:v.co.x+=side*.107
 # The hem curve was built at the origin; remove that helper before exporting.
 helper=next(o for o in PARTS if o.name=='Loose trouser hem '+str(side)+' thin hem');PARTS.remove(helper);bpy.data.objects.remove(helper,do_unlink=True)
 sphere('Thin ivory sole '+str(side),(side*.113,-.046,.019),(.109,.162,.013),SOLE,48,24)
 sphere('Black cloth shoe '+str(side),(side*.113,-.049,.067),(.102,.153,.049),BLACK,48,28)
 # A fine seam follows the upper without a broad white platform.
 curve('Shoe fine seam '+str(side),[(side*.113-.082,-.138,.080),(side*.113,-.190,.083),(side*.113+.082,-.138,.080)],.002,BLACK)

ribbon('Small inner collar left',[(-.055,-.079,1.307),(-.025,-.114,1.27),(.010,-.130,1.237)],.019,INNER_CLOTH)
ribbon('Small inner collar right',[(.055,-.079,1.307),(.025,-.115,1.27),(-.010,-.132,1.237)],.020,INNER_CLOTH)
loft('Slim waist band',[(.987,.213,.153),(1.052,.210,.151)],GREEN,pleats=0)
helper=next(o for o in PARTS if o.name=='Slim waist band thin hem');PARTS.remove(helper);bpy.data.objects.remove(helper,do_unlink=True)
ribbon('Woven sash left',[(.058,-.167,1.017),(.049,-.178,.86),(.027,-.186,.68),(.018,-.192,.578)],.071,SASH,1,fold=.010,taper=.12)
ribbon('Woven sash right',[(.105,-.160,1.015),(.112,-.171,.83),(.116,-.184,.64),(.122,-.184,.439)],.063,SASH,1,fold=-.012,taper=.22)
for a in range(7):
 t=a/7*2*PI;sphere('Cream flower clasp petal '+str(a),(.062+.013*math.sin(t),-.169,1.019+.013*math.cos(t)),(.0055,.004,.008),TRIM,20,12)
sphere('Sage clasp centre',(.062,-.175,1.019),(.007,.004,.007),CAP,20,12)
def fit_heart_pin(coat):
 """Project the heart onto the left front panel and round its visible edge."""
 bpy.context.view_layer.update()
 depsgraph=bpy.context.evaluated_depsgraph_get()
 surface=coat.evaluated_get(depsgraph)
 sleeve=bpy.data.objects['Soft bell sleeve 1'].evaluated_get(depsgraph)
 center_x,center_z=.118,1.183
 direction=Vector((0,1,0))

 def cloth_point(x,z,raise_by):
  origin=Vector((x,-.55,z))
  hit,point,normal,_=surface.ray_cast(origin,direction,distance=.53)
  assert hit and normal.y<-.22, 'Heart pin must stay on the front panel'
  if raise_by>0:
   covered,sleeve_point,_,_=sleeve.ray_cast(origin,direction,distance=.53)
   assert not covered or sleeve_point.y>point.y-raise_by+.001, 'Sleeve covers the heart pin'
  return (x,point.y-raise_by,z)

 vertices,faces=[],[]
 sides=64
 layers=((.94,-.0008),(1,.0026),(.88,.0052),(.46,.0065))
 for size,raise_by in layers:
  for index in range(sides):
   angle=index*2*PI/sides
   x=center_x+.00136*size*16*math.sin(angle)**3
   z=center_z+.00136*size*(13*math.cos(angle)-5*math.cos(2*angle)-2*math.cos(3*angle)-math.cos(4*angle))
   vertices.append(cloth_point(x,z,raise_by))
 faces.append(tuple(reversed(range(sides))))
 for ring in range(len(layers)-1):
  for index in range(sides):
   a=ring*sides+index
   b=ring*sides+(index+1)%sides
   faces.append((a,b,b+sides,a+sides))
 face_center=len(vertices)
 vertices.append(cloth_point(center_x,center_z,.007))
 start=(len(layers)-1)*sides
 for index in range(sides):
  faces.append((start+index,start+(index+1)%sides,face_center))
 heart=mesh('Small red heart',vertices,faces,HEART)
 bm=bmesh.new()
 bm.from_mesh(heart.data)
 assert all(edge.is_manifold for edge in bm.edges), 'Heart pin mesh has an open edge'
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 bm.to_mesh(heart.data)
 bm.free()

fit_heart_pin(outer_coat)
# The temple side of the cap is lower and flares into the folded lower edge.
accessory_start=len(PARTS)
# Ring bounds are measured on the front. Their depth is inferred.
cap_rows=[
 (.00,377,141,.002,.004),(.12,385,134,.063,.043),
 (.27,380,120,.095,.053),(.41,369,105,.109,.052),
 (.58,361,89,.126,.064),(.76,355,69,.107,.063),
 (.90,346,54,.074,.046),(1.00,343,50,.002,.003),
]
positions, cap_faces=[],[]
ring_size=48
for row in range(49):
 t=row/48
 px, py, width, depth=interpolate(cap_rows,t)
 x,z=recorded_coordinates(px,py)
 for index in range(ring_size):
  angle=2*PI*index/ring_size
  fold=math.sin(3*angle+.7)*math.sin(PI*t)*.007
  positions.append((x+width*math.cos(angle),.080+depth*math.sin(angle),z+fold))
  if row:
   left=(row-1)*ring_size+index
   right=(row-1)*ring_size+(index+1)%ring_size
   cap_faces.append((left,right,right+ring_size,left+ring_size))
cap_faces.extend([tuple(reversed(range(ring_size))),tuple(range(len(positions)-ring_size,len(positions)))])
mesh('Single folded pale sage cap',positions,cap_faces,CAP)
sphere('Ribbon knot',(.321,.156,1.81),(.045,.033,.043),CAP,32,20)
ribbon('Long sage ribbon',[(.330,.155,1.81),(.350,.179,1.69),(.397,.204,1.50),(.379,.199,1.32)],.145,CAP,fold=.045,taper=.63)
ribbon('Short sage ribbon',[(.320,.173,1.81),(.338,.216,1.68),(.427,.221,1.487)],.112,CAP,fold=-.032,taper=.68)
HEAD_PARTS.update(PARTS[accessory_start:])

for o in PARTS:
 bpy.context.view_layer.objects.active=o
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 if not any(m and m.use_nodes and any(n.type=='TEX_IMAGE' for n in m.node_tree.nodes) for m in o.data.materials):
  for layer in list(o.data.uv_layers):o.data.uv_layers.remove(layer)
controls=add_acknowledgment(PARTS,HEAD_PARTS,eye_groups,brow_meshes,smile,smile_open,head,moving_hair)
assert abs(controls[0].matrix_world.translation.z-1.02)<.001, "Torso lost its neutral transform"
bpy.ops.object.select_all(action='DESELECT')
for o in PARTS+controls:o.select_set(True)
bpy.context.view_layer.objects.active=head
bpy.ops.export_scene.gltf(filepath=str(ROOT/'ade.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_current_frame=True,export_skins=False,export_morph=True,export_yup=True,export_vertex_color='ACTIVE')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_settings.view_transform='Standard';scene.render.resolution_x=800;scene.render.resolution_y=950;scene.render.resolution_percentage=100
w=scene.world;w.use_nodes=True;n=w.node_tree.nodes;l=w.node_tree.links;n['Background'].inputs['Color'].default_value=(1,1,1,1);n['Background'].inputs['Strength'].default_value=.80;bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=rgba('17161b');path=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(path.outputs['Is Camera Ray'],mix.inputs[0]);l.new(n['Background'].outputs[0],mix.inputs[1]);l.new(bg.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n['World Output'].inputs['Surface'])
for name,loc,power,size,color in [('Warm key',(-2.8,-3.1,4.4),115,3.0,(1,.88,.78)),('Face fill',(2.5,-3,2.9),42,4.2,(.94,.96,1)),('Hair rim',(1.5,2.0,3.8),85,2.5,(1,.87,.69))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;d.color=color;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.55))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Inspection camera');cam=bpy.data.objects.new('Inspection camera',d);scene.collection.objects.link(cam);d.type='ORTHO';d.ortho_scale=2.526;scene.camera=cam;cam.location=(0,-5,1.17);cam.rotation_euler=(Vector((0,0,1.17))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'ade.blend'))
report={'method':'Recorded eye color with local gaze deformation, eyelid occlusion, unequal brow lifts, cheek squint and soft open smile.','parts':len(PARTS),'vertices':sum(len(o.data.vertices) for o in PARTS),'textures':['recorded eye crops','authored blush','recorded fabric motifs blended with authored cloth'],'skin_palette':{'base_srgb':SKIN_RGB,'inner_ear_srgb':INNER_EAR_RGB,'blush_srgb':(251,151,141)},'inner_cloth_srgb':'cfdcd8','decoration':'fitted bamboo embroidery','hands':'two closed connected hand meshes with curled fingers','status':'relaxed hand sculpt','hidden_back':'inferred'}
(ROOT/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
views=[('front',(0,-5,1.17)),('quarter-right',(-3,-5,1.4)),('quarter-left',(3,-5,1.4)),('side',(5,0,1.17)),('back',(0,5,1.17))]
if args.quick:views=[views[0],views[2]];scene.cycles.samples=24
for name,loc in views:
 scene.frame_set(1)
 cam.location=loc;cam.rotation_euler=(Vector((0,0,1.17))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
scene.frame_set(PEAK)
cam.location=(2.5,-5,1.40);cam.rotation_euler=(Vector((0,0,1.17))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(ROOT/'gesture.png');bpy.ops.render.render(write_still=True)
scene.frame_set(19)
scene.render.filepath=str(ROOT/'blink.png');bpy.ops.render.render(write_still=True)
scene.frame_set(13)
scene.render.filepath=str(ROOT/'glance.png');bpy.ops.render.render(write_still=True)
print('REFINED_MODEL_READY',flush=True)

