"""Check loadable, embedded real-volume geometry; does not certify likeness."""
import json,struct,hashlib,itertools
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parent
data=(p/'ade.glb').read_bytes()
magic,version,total=struct.unpack_from('<4sII',data)
assert magic==b'glTF' and version==2 and total==len(data)
n,kind=struct.unpack_from('<II',data,12)
assert kind==0x4e4f534a
g=json.loads(data[20:20+n])
assert all('bufferView' in i for i in g.get('images',[]))
points=[]
def visit(index,parent):
 node=g['nodes'][index]
 if 'matrix' in node:m=np.array(node['matrix']).reshape((4,4),order='F')
 else:
  x,y,z,w=node.get('rotation',[0,0,0,1]);m=np.eye(4)
  m[:3,:3]=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]])@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0])
 world=parent@m
 if 'mesh' in node:
  for primitive in g['meshes'][node['mesh']]['primitives']:
   a=g['accessors'][primitive['attributes']['POSITION']]
   for corner in itertools.product(*zip(a['min'],a['max'])):points.append((world@np.array([*corner,1]))[:3])
 for child in node.get('children',[]):visit(child,world)
for index in g['scenes'][g.get('scene',0)]['nodes']:visit(index,np.eye(4))
points=np.asarray(points);dims=(points.max(axis=0)-points.min(axis=0)).tolist()
assert dims[1]>2 and dims[2]/dims[1]>.20,'Thin or undersized model'
names=[n.get('name','') for n in g['nodes'] if 'mesh' in n]
features=['Curved recorded eye left','Curved recorded eye right','Sculpted brow','Small sculpted nose','Sculpted smile']
assert all(any(name.startswith(feature) for name in names) for feature in features),'Separate facial geometry missing'
report={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'dimensions_gltf_y_up':dims,'depth_height_ratio':dims[2]/dims[1],'meshes':len(g['meshes']),'embedded_images':len(g.get('images',[])),'independent_facial_geometry':features,'skins':len(g.get('skins',[])),'animations':len(g.get('animations',[])),'status':'visual refinement; unrigged; likeness not accepted','limits':'Does not certify likeness, watertightness, animations or homepage integration.'}
(p/'candidate-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
