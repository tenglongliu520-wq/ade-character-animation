"""Assemble generated hair, smooth face and authored clean hanfu body.
Face appearance is projected recording color, not sculpted eye or face controls.
Inputs remain untouched. This candidate has no rig or animations.
"""
from pathlib import Path
import bpy,bmesh,math,json
from mathutils import Vector
from PIL import Image
ROOT=Path(__file__).resolve().parent
def rgba(h):
 a=[int(h[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1,)
def mat(name,h,texture=None):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=rgba(h);p.inputs['Roughness'].default_value=.85;p.inputs['Specular IOR Level'].default_value=.1
 if texture:
  n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(ROOT/texture));n.image.pack();m.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color'])
 return m
def uv_project(o):
 for layer in list(o.data.uv_layers):o.data.uv_layers.remove(layer)
 layer=o.data.uv_layers.new(name='Recorded front projection')
 for f in o.data.polygons:
  for i in f.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[i].vertex_index].co
   layer.data[i].uv=((302+p.x*376)/720,1-(915-p.z*376)/950)
def ellipsoid(name,loc,size,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 for f in o.data.polygons:f.use_smooth=True
 return o
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'source-geometry.glb'))
hair_objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@v.co for o in hair_objects for v in o.data.vertices]
low=Vector(tuple(min(p[i] for p in pts) for i in range(3)));high=Vector(tuple(max(p[i] for p in pts) for i in range(3)));center=(low+high)/2;scale=2.3/(high.z-low.z)
assert (high.y-low.y)/(high.z-low.z)>.15,'Thin scan rejected'
front=mat('Recorded hair color','ffffff','recorded-object-color.png');rear=mat('Inferred rear chestnut','704027');cap=mat('Sage cap and ribbon','cbd8c1');skin=mat('Warm peach skin','fcd0b9');face=mat('Recorded face color','ffffff','recorded-face-color.png')
reference=Image.open(ROOT/'reference-front.png').convert('RGB')
for o in hair_objects:
 for v in o.data.vertices:
  p=o.matrix_world@v.co;v.co=((p.x-center.x)*scale*.91,(p.y-center.y)*scale,(p.z-low.z)*scale)
 o.matrix_world.identity();bm=bmesh.new();bm.from_mesh(o.data);remove=[]
 for v in bm.verts:
  x,y,z=v.co;accessory=(x>.30 and y>.015 and z>1.40)
  px=max(0,min(719,round(302+x*376)));py=max(0,min(949,round(915-z*376)));r,g,b=reference.getpixel((px,py));hair_pixel=r>45 and r<205 and r>g*1.20 and r>b*1.35
  if not accessory and ((z<1.64 or (z<1.81 and not hair_pixel)) if y<.11 else z<1.60):remove.append(v)
 bmesh.ops.delete(bm,geom=remove,context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update();o.name='Generated layered hair and accessory';o.data.materials.clear()
 for m in [front,rear,cap]:o.data.materials.append(m)
 uv_project(o)
 for f in o.data.polygons:
  c=f.center;f.material_index=2 if (c.x>.30 and c.y>.015 and c.z<1.98) or (c.z>2.15 and c.x>.03 and c.y>.05) else (0 if c.y<.12 else 1);f.use_smooth=True
head=ellipsoid('Smooth volumetric face',(0,-.015,1.646),(.305,.265,.308),face);head.data.materials.append(skin);uv_project(head)
for f in head.data.polygons:f.material_index=0 if f.center.y<.04 else 1
# Inferred rounded nape prevents a flat saw-cut termination behind the head.
nape=ellipsoid('Inferred rounded rear hair',(0,.035,1.86),(.329,.292,.365),rear)
bm=bmesh.new();bm.from_mesh(nape.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.y<.075 or v.co.z<-.32+.035*math.cos(v.co.x*24)],context='VERTS');bm.to_mesh(nape.data);bm.free()
for s in (-1,1):ellipsoid('Rounded ear '+str(s),(s*.305,-.015,1.555),(.046,.045,.060),skin)
ellipsoid('Continuous neck',(0,0,1.345),(.070,.072,.105),skin)
head_objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
# A static clean outfit is retained from the authored source. No claim of
# retaining its old rig or morphs is made for this likeness iteration.
bpy.ops.import_scene.gltf(filepath=str(ROOT/'authored-body.glb'))
body=[]
for o in list(bpy.context.scene.objects):
 if o.type!='MESH' or o in head_objects:continue
 used={g.group for v in o.data.vertices for g in v.groups if g.weight>.001}
 groups={g.name for g in o.vertex_groups if g.index in used}
 zmax=max((o.matrix_world@v.co).z for v in o.data.vertices)
 if 'head' in groups or 'neck' in groups or zmax>1.46:bpy.data.objects.remove(o,do_unlink=True);continue
 matrix=o.matrix_world.copy();o.parent=None;o.matrix_world=matrix
 for mod in list(o.modifiers):o.modifiers.remove(mod)
 for v in o.data.vertices:
  p=matrix@v.co;v.co=(p.x,p.y,p.z*1.075)
 o.matrix_world.identity()
 o.vertex_groups.clear();body.append(o)
for o in list(bpy.context.scene.objects):
 if o.type=='ARMATURE':bpy.data.objects.remove(o,do_unlink=True)
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
meshes=head_objects+body
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=head
bpy.ops.export_scene.gltf(filepath=str(ROOT/'ade.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_morph=False,export_yup=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.view_settings.view_transform='Standard';scene.render.resolution_x=800;scene.render.resolution_y=950;scene.render.resolution_percentage=100
w=scene.world;w.use_nodes=True;n=w.node_tree.nodes;l=w.node_tree.links;n['Background'].inputs['Color'].default_value=(1,1,1,1);n['Background'].inputs['Strength'].default_value=.8
bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=rgba('17161b');path=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(path.outputs['Is Camera Ray'],mix.inputs[0]);l.new(n['Background'].outputs[0],mix.inputs[1]);l.new(bg.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n['World Output'].inputs['Surface'])
for name,loc,power in [('Key',(-3,-4,5),90),('Fill',(3,-2,3),30)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Inspection camera');cam=bpy.data.objects.new('Inspection camera',d);scene.collection.objects.link(cam);d.type='ORTHO';d.ortho_scale=2.526;scene.camera=cam
cam.location=(0,-5,1.17);cam.rotation_euler=(Vector((0,0,1.17))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'ade.blend'))
report={'method':'generated layered hair + smooth authored face + clean authored hanfu body','face':'recording projected onto a volumetric face; eyes not separately sculpted','hidden_back':'inferred','status':'visual-only candidate; unrigged; not user-accepted','original_scan_dimensions':list(high-low),'mesh_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes)}
(ROOT/'candidate-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
for name,loc in [('front',(0,-5,1.17)),('quarter',(3,-5,1.5)),('back',(0,5,1.17))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,0,1.17))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('VOLUMETRIC_CANDIDATE_READY',flush=True)
