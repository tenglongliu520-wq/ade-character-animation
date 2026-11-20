"""Refine Ade against recording silhouettes using genuine curved 3D surfaces.
Original generated input is retained unchanged. This is a new, unaccepted
visual iteration; no previous rig or animation is claimed as complete.
"""
from pathlib import Path
import bpy,bmesh,math,json,random,argparse
from mathutils import Vector
from PIL import Image,ImageDraw
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
def curve(name,pts,radius,mat):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=12;d.bevel_depth=radius;d.bevel_resolution=3;s=d.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
 for p,co in zip(s.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');return register(bpy.context.object,mat)
def project(o):
 for l in list(o.data.uv_layers):o.data.uv_layers.remove(l)
 l=o.data.uv_layers.new(name='RecordingColorProjection')
 for f in o.data.polygons:
  for i in f.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[i].vertex_index].co;l.data[i].uv=((302+p.x*376)/720,1-(915-p.z*376)/950)
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
 if not open_front:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.to_mesh(o.data);bm.free()
 if open_front:
  for j in (0,n):curve(name+' thin opening edge '+str(j),[vs[k*(n+1)+j] for k in range(0,nz+1,4)],.0035,TRIM)
 curve(name+' thin hem',vs[:n+1],.0035,TRIM if open_front else IVORY)
 return o
def ribbon(name,pts,width,mat,uvscale=1):
 controls=[Vector(p) for p in pts];sample=[]
 for k in range(len(controls)-1):
  a=controls[max(0,k-1)];b=controls[k];c=controls[k+1];d=controls[min(len(controls)-1,k+2)]
  for step in range(8):
   t=step/8;sample.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)))
 sample.append(tuple(controls[-1]));pts=sample
 vs=[];fs=[];uv=[]
 for i,p in enumerate(pts):
  t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)]);axis=t.cross(Vector((0,1,0))).normalized()*width/2
  for side in (-1,1):vs.append(tuple(Vector(p)+axis*side));uv.append(((side+1)/2,i/max(1,len(pts)-1)*uvscale))
 for i in range(len(pts)-1):a=i*2;fs.append((a,a+1,a+3,a+2))
 o=mesh(name,vs,fs,mat,uv);thick(o,.004);return o

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
SKIN=material('Peach skin','fcd0bb');FACE=material('Skin and blush only','ffffff',texture='skin-blush.png');EAR=material('Ear soft pink','edb09b');IVORY=material('Warm white inner robe','fff0e7');TRIM=material('Thin pale seam','d9e1cc');CLOTH=material('Dense bamboo sage cloth','ffffff',texture='bamboo-cloth.png');GREEN=material('Dark green sash','1e382c');SASH=material('Bamboo woven hanging sash','ffffff',texture='bamboo-sash.png');BLACK=material('Black cloth shoe','16171c');SOLE=material('Thin ivory sole','e6e0d3');CAP=material('Pale sage hair tie','cad8c0');HAIR=material('Recorded chestnut hair','ffffff',texture='hair-color.png');BROW=material('Chestnut eyebrows','714333');LASH=material('Warm dark upper eyelid','493334');WHITE=material('Eye white','fffaf2',.35);IRIS=material('Brown iris','8d5534',.38);RIM=material('Iris dark rim','4e332e',.4);PUPIL=material('Deep pupil','251e25',.30);LIGHT=material('Eye catchlight','ffffff',.24);LIP=material('Small smile','bd806c');HEART=material('Red heart badge','e66a54')

# Layered hair geometry from the actual generated volume, with accessory removed.
REAR=material('Inferred chestnut rear strands','ffffff',texture='inferred-rear-hair.png')
IRIS=material('Brown iris radial color','ffffff',.38,texture='iris-brown.png')
bpy.ops.import_scene.gltf(filepath=str(ROOT/'source-geometry.glb'));raw=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@v.co for o in raw for v in o.data.vertices];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);mid=(hi+lo)/2;scale=2.3/(hi.z-lo.z);ref=Image.open(ROOT/'reference-front.png').convert('RGB')
cap_mask=Image.new('1',(720,950));ImageDraw.Draw(cap_mask).polygon([(311,48),(369,48),(406,67),(424,105),(420,143),(384,137),(358,119),(331,110),(310,94)],fill=1)
for o in raw:
 for v in o.data.vertices:
  p=o.matrix_world@v.co;v.co=((p.x-mid.x)*scale*.91,(p.y-mid.y)*scale,(p.z-lo.z)*scale)
 o.matrix_world.identity();bm=bmesh.new();bm.from_mesh(o.data);remove=[]
 for v in bm.verts:
  x,y,z=v.co;px=max(0,min(719,round(302+x*376)));py=max(0,min(949,round(915-z*376)));r,g,b=ref.getpixel((px,py));hairpixel=45<r<220 and r>g*1.20 and r>b*1.35;mint=g>110 and g>r*.97 and g>b*1.03
  accessory=(x>.30 and y>.015 and z<1.96) or (z>2.05 and cap_mask.getpixel((px,py)))
  if accessory or ((z<1.64 or (z<1.81 and not hairpixel)) if y<.11 else z<1.59):remove.append(v)
 bmesh.ops.delete(bm,geom=remove,context='VERTS');bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=24);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.name='Reference layered hair';o.data.materials.clear();register(o,HAIR);o.data.materials.append(REAR);project(o)
 for f in o.data.polygons:
  if f.center.y>.105:
   f.material_index=1
   for i in f.loop_indices:
    p=o.data.vertices[o.data.loops[i].vertex_index].co;o.data.uv_layers.active.data[i].uv=(math.atan2(p.y,p.x)/(2*PI)+.5,p.z*1.3)
# Rounded rear mass with recorded brown field; all rear strands remain inferred.
underlay=sphere('Continuous hair underlayer',(0,.04,1.87),(.325,.260,.300),REAR)
bm=bmesh.new();bm.from_mesh(underlay.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v.co.z<-.10 if v.co.y<.08 else v.co.z<-.32)],context='VERTS');bm.to_mesh(underlay.data);bm.free()
head=sphere('Soft tapered face',(0,-.015,1.646),(.310,.265,.308),FACE,64,48)
for v in head.data.vertices:
 if v.co.y<0:
  weight=min(1,-v.co.y/.12);weight=weight*weight*(3-2*weight);v.co.y-=.027*math.exp(-((v.co.z+.18)/.13)**2)*weight
project(head)
for f in head.data.polygons:
 if f.center.y>0:
  for i in f.loop_indices:head.data.uv_layers.active.data[i].uv=(.01,.01)
def face_y(x,z):return -.015-.265*math.sqrt(max(.02,1-(x/.310)**2-((z-1.646)/.308)**2))-.027*math.exp(-((z-1.466)/.13)**2)
def eye_patch(name,cx,cz,rx,rz,offset,mat):
 vs=[(cx,face_y(cx,cz)-offset-.004,cz)];fs=[];uv=[(.5,.5)];nt=64;nr=16
 for k in range(1,nr+1):
  r=k/nr
  for j in range(nt):
   a=j/nt*2*PI;x=cx+rx*r*math.cos(a);z=cz+rz*r*math.sin(a);vs.append((x,face_y(x,z)-offset-.004*(1-r*r),z));uv.append((.5+r*math.cos(a)*.5,.5+r*math.sin(a)*.5))
 for j in range(nt):fs.append((0,1+j,1+(j+1)%nt))
 for k in range(nr-1):
  for j in range(nt):a=1+k*nt+j;b=1+k*nt+(j+1)%nt;fs.append((a,b,b+nt,a+nt))
 return mesh(name,vs,fs,mat,uv if mat==IRIS else None)
for side in (-1,1):
 sphere('Soft ear '+str(side),(side*.317,-.005,1.548),(.048,.046,.062),SKIN)
 sphere('Inner ear '+str(side),(side*.326,-.043,1.548),(.025,.012,.037),EAR)
 cx=side*.132;ez=1.562
 eye_patch('Separate sclera '+str(side),cx,ez,.083,.080,.003,WHITE)
 eye_patch('Iris rim '+str(side),cx+.004,ez-.005,.059,.065,.006,RIM)
 eye_patch('Brown iris '+str(side),cx+.004,ez-.006,.055,.061,.0075,IRIS)
 eye_patch('Pupil '+str(side),cx+.004,ez+.005,.031,.043,.009,PUPIL)
 eye_patch('Large eye catchlight '+str(side),cx-.018,ez+.029,.016,.018,.011,LIGHT)
 eye_patch('Small eye catchlight '+str(side),cx+.026,ez-.025,.007,.008,.011,LIGHT)
 points=[(cx-.081,ez+.008),(cx-.050,ez+.065),(cx+.012,ez+.079),(cx+.078,ez+.032)]
 curve('Sculpted upper eyelid '+str(side),[(x,face_y(x,z)-.007,z) for x,z in points],.0055,LASH)
 brow=[(cx-.072,1.696),(cx-.014,1.713),(cx+.055,1.696)]
 curve('Sculpted brow '+str(side),[(x,face_y(x,z)-.006,z) for x,z in brow],.010,BROW)
sphere('Small sculpted nose',(0,face_y(0,1.486)-.003,1.486),(.017,.012,.013),SKIN)
curve('Sculpted smile',[(-.043,face_y(-.043,1.443)-.004,1.443),(0,face_y(0,1.433)-.004,1.433),(.043,face_y(.043,1.443)-.004,1.443)],.0032,LIP)
sphere('Neck',(0,0,1.323),(.063,.067,.105),SKIN)

# Continuous sloping shoulders and curved open coat replace the old cylinders.
loft('Ivory inner garment',[(.235,.195,.125),(.42,.205,.133),(.98,.198,.137),(1.20,.18,.115),(1.305,.074,.072)],IVORY,pleats=.002)
loft('Flowing open bamboo coat',[(.30,.313,.160,.192),(.51,.283,.153,.172),(.82,.232,.143,.151),(1.03,.211,.139,.132),(1.17,.216,.125,.100),(1.28,.145,.098,.072),(1.32,.078,.073,.044)],CLOTH,True,.004)
for side in (-1,1):
 vs=[];fs=[];uv=[];nr=40;nt=64
 rows=[(0,.150,1.24,.045,.060),(.18,.215,1.17,.080,.093),(.48,.275,1.025,.105,.118),(.78,.309,.86,.124,.133),(1,.290,.745,.113,.123)]
 for k in range(nr+1):
  t=k/nr;cx,z,rx,ry=interpolate(rows,t);axis=Vector((side*.24,0,-.97));u=Vector((0,1,0));v=axis.cross(u).normalized()
  for j in range(nt+1):
   a=j/nt*2*PI;wr=1+.018*math.sin(a*6+t*5)*t;p=Vector((side*cx,-.012*t,z))+u*math.cos(a)*ry*wr+v*math.sin(a)*rx*wr;vs.append(tuple(p));uv.append((j/nt*1.4,t*.82))
 for k in range(nr):
  for j in range(nt):a=k*(nt+1)+j;fs.append((a,a+1,a+nt+2,a+nt+1))
 o=mesh('Soft bell sleeve '+str(side),vs,fs,CLOTH,uv);thick(o,.004);curve('Thin cuff seam '+str(side),vs[-nt-1:],.0045,TRIM)
 x=side*.294;sphere('Wrist '+str(side),(x,-.019,.716),(.033,.033,.068),SKIN,32,24);sphere('Palm '+str(side),(x,-.026,.658),(.040,.032,.056),SKIN,32,24)
 for finger in range(4):sphere('Finger '+str(side)+' '+str(finger),(x+(finger-1.5)*.017,-.038,.616+abs(finger-1.5)*.008),(.010,.014,.032),SKIN,24,16)
 sphere('Thumb '+str(side),(x-side*.034,-.050,.660),(.016,.020,.032),SKIN,24,16)
 # Only short soft trouser hems remain visible below the long inner garment.
 leg=loft('Loose trouser hem '+str(side),[(.096,.065,.072),(.15,.080,.086),(.23,.095,.103),(.36,.096,.100)],IVORY,pleats=.004)
 for v in leg.data.vertices:v.co.x+=side*.107
 # The hem curve was built at the origin; remove that helper before exporting.
 helper=next(o for o in PARTS if o.name=='Loose trouser hem '+str(side)+' thin hem');PARTS.remove(helper);bpy.data.objects.remove(helper,do_unlink=True)
 sphere('Thin ivory sole '+str(side),(side*.113,-.046,.019),(.109,.162,.013),SOLE,48,24)
 sphere('Black cloth shoe '+str(side),(side*.113,-.049,.067),(.102,.153,.049),BLACK,48,28)
 # A fine seam follows the upper without a broad white platform.
 curve('Shoe fine seam '+str(side),[(side*.113-.082,-.138,.080),(side*.113,-.190,.083),(side*.113+.082,-.138,.080)],.002,BLACK)

ribbon('Small inner collar left',[(-.055,-.079,1.307),(-.025,-.114,1.27),(.010,-.130,1.237)],.019,IVORY)
ribbon('Small inner collar right',[(.055,-.079,1.307),(.025,-.115,1.27),(-.010,-.132,1.237)],.020,IVORY)
loft('Slim waist band',[(.987,.213,.153),(1.052,.210,.151)],GREEN,pleats=0)
helper=next(o for o in PARTS if o.name=='Slim waist band thin hem');PARTS.remove(helper);bpy.data.objects.remove(helper,do_unlink=True)
ribbon('Woven sash left',[(.048,-.159,1.02),(.042,-.175,.86),(.026,-.185,.68),(.018,-.191,.565)],.074,SASH,1)
ribbon('Woven sash right',[(.112,-.159,1.02),(.116,-.177,.83),(.116,-.188,.64),(.128,-.194,.485)],.063,SASH,1)
for a in range(7):
 t=a/7*2*PI;sphere('Cream flower clasp petal '+str(a),(.062+.013*math.sin(t),-.169,1.019+.013*math.cos(t)),(.0055,.004,.008),TRIM,20,12)
sphere('Sage clasp centre',(.062,-.175,1.019),(.007,.004,.007),CAP,20,12)
vs=[]
for y in (-.112,-.120):
 for j in range(48):
  t=j/48*2*PI;vs.append((.154+16*math.sin(t)**3*.0010,y,1.254+(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))*.0010))
fs=[tuple(reversed(range(48))),tuple(range(48,96))]+[(j,(j+1)%48,(j+1)%48+48,j+48) for j in range(48)];heart=mesh('Small red heart',vs,fs,HEART);bevel=heart.modifiers.new('Soft heart edge','BEVEL');bevel.width=.002;bevel.segments=3
# Rounded pale cap and two folded fabric ribbons, replacing split scan material.
cap=sphere('Folded pale sage cap',(.12,.115,2.204),(.126,.045,.095),CAP,48,32)
for v in cap.data.vertices:
 v.co.x=math.copysign((abs(v.co.x)/.126)**.80*.126,v.co.x);v.co.z=math.copysign((abs(v.co.z)/.095)**.80*.095,v.co.z);v.co.z+=.006*math.cos(v.co.x*35)*math.exp(-((v.co.z+.02)/.07)**2)
curve('Cap folded band',[(.005,.074,2.19),(.07,.064,2.175),(.16,.067,2.165),(.235,.089,2.18)],.005,CAP)
sphere('Ribbon knot',(.321,.156,1.81),(.045,.033,.043),CAP,32,20)
ribbon('Long sage ribbon',[(.331,.165,1.82),(.365,.197,1.70),(.392,.221,1.54),(.434,.230,1.365)],.127,CAP)
ribbon('Short sage ribbon',[(.319,.182,1.81),(.292,.231,1.69),(.328,.252,1.49)],.093,CAP)

for o in PARTS:
 bpy.context.view_layer.objects.active=o
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 if not any(m and m.use_nodes and any(n.type=='TEX_IMAGE' for n in m.node_tree.nodes) for m in o.data.materials):
  for layer in list(o.data.uv_layers):o.data.uv_layers.remove(layer)
bpy.ops.object.select_all(action='DESELECT')
for o in PARTS:o.select_set(True)
bpy.context.view_layer.objects.active=head
bpy.ops.export_scene.gltf(filepath=str(ROOT/'ade.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_morph=False,export_yup=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_settings.view_transform='Standard';scene.render.resolution_x=800;scene.render.resolution_y=950;scene.render.resolution_percentage=100
w=scene.world;w.use_nodes=True;n=w.node_tree.nodes;l=w.node_tree.links;n['Background'].inputs['Color'].default_value=(1,1,1,1);n['Background'].inputs['Strength'].default_value=.80;bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=rgba('17161b');path=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(path.outputs['Is Camera Ray'],mix.inputs[0]);l.new(n['Background'].outputs[0],mix.inputs[1]);l.new(bg.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n['World Output'].inputs['Surface'])
for name,loc,power in [('Key',(-3,-4,5),90),('Fill',(3,-2,3),30)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Inspection camera');cam=bpy.data.objects.new('Inspection camera',d);scene.collection.objects.link(cam);d.type='ORTHO';d.ortho_scale=2.526;scene.camera=cam;cam.location=(0,-5,1.17);cam.rotation_euler=(Vector((0,0,1.17))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'ade.blend'))
report={'iteration':'user rejected previous version; continuing recorded-shape refinement','method':'recording-shaped authored body and independent 3D eyes/eyelids/nose/smile; generated layered hair retained','parts':len(PARTS),'vertices':sum(len(o.data.vertices) for o in PARTS),'actual_3d_features':['sclera','iris','pupil','catchlights','eyelids','brows','nose','smile'],'textures':['hair color field from recording','authored blush','authored dense bamboo cloth'],'status':'visual iteration; not accepted; no rig/actions','hidden_back':'inferred'}
(ROOT/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
views=[('front',(0,-5,1.17)),('quarter-right',(-3,-5,1.4)),('quarter-left',(3,-5,1.4)),('side',(5,0,1.17)),('back',(0,5,1.17))]
if args.quick:views=[views[0],views[2]];scene.cycles.samples=24
for name,loc in views:
 cam.location=loc;cam.rotation_euler=(Vector((0,0,1.17))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('REFINED_MODEL_READY',flush=True)
