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
assert 2.25<dims[1]<2.36 and dims[2]/dims[1]>.20,'Incorrect neutral pose height'
names=[n.get('name','') for n in g['nodes'] if 'mesh' in n]
features=['Curved recorded eye left','Curved recorded eye right','Sculpted brow','Small sculpted nose','Sculpted smile']
assert all(any(name.startswith(feature) for name in names) for feature in features),'Separate facial geometry missing'
moving_hair = {
    'Central swept fringe', 'Swept left front lock', 'Swept right front lock',
    'Left temple curl', 'Right raised temple curl',
}
colored_surfaces = [
    'Flowing open bamboo coat', 'Soft bell sleeve -1', 'Soft bell sleeve 1',
    *sorted(moving_hair), 'Soft parted hairline',
    'Soft ear -1', 'Soft ear 1',
]
for name in colored_surfaces:
    node = next(node for node in g['nodes'] if node.get('name') == name)
    primitives = g['meshes'][node['mesh']]['primitives']
    assert all('COLOR_0' in primitive['attributes'] for primitive in primitives), name
head = next(node for node in g['nodes'] if node.get('name') == 'Head expression pivot')
head_children = {g['nodes'][i].get('name') for i in head['children']}
assert {'Soft ear -1', 'Soft ear 1', 'Soft parted hairline'} | moving_hair <= head_children
for node in (node for node in g['nodes'] if node.get('name') in moving_hair):
    for primitive in g['meshes'][node['mesh']]['primitives']:
        target, = primitive['targets']
        delta = g['accessors'][target['POSITION']]
        assert all(max(abs(low), abs(high)) > .004 for low, high in zip(delta['min'], delta['max'])), node['name']
assert not any(name.startswith('Inner ear ') for name in names)
assert 'Single folded pale sage cap' in names
clip, = g['animations']
assert clip['name']=='LookTiltReturn'
expected = {
    ('Upper body balance','translation'), ('Upper body balance','rotation'),
    ('Head expression pivot','rotation'), ('Hair ribbon follow through','rotation'),
    ('Curved recorded eye left','weights'), ('Curved recorded eye right','weights'),
    ('Sculpted smile','weights'), ('Soft tapered face','weights'),
    ('Upper eyelid left','weights'), ('Upper eyelid right','weights'),
    ('Lower eyelid left','weights'), ('Lower eyelid right','weights'),
    ('Closed lash left','weights'), ('Closed lash right','weights'),
    ('Sculpted brow -1','weights'), ('Sculpted brow 1','weights'),
    ('Soft open smile','weights'),
}
expected.update((name, 'weights') for name in moving_hair)
torso = next(node for node in g['nodes'] if node.get('name') == 'Upper body balance')
assert np.allclose(torso['translation'], [0,1.02,0], atol=1e-4), 'Incorrect neutral hierarchy'
torso_children = {g['nodes'][i].get('name') for i in torso['children']}
assert {'Neck', 'Small inner collar left', 'Small inner collar right'} <= torso_children
heart_index, = (i for i,node in enumerate(g['nodes']) if node.get('name') == 'Small red heart')
assert heart_index in torso['children'] and 'mesh' in g['nodes'][heart_index], 'Heart pin must follow the coat'
hands = {node['name']: node for i in torso['children']
         if (node := g['nodes'][i]).get('name', '').startswith('Relaxed unified hand ')}
assert set(hands) == {'Relaxed unified hand left', 'Relaxed unified hand right'}
for side, label in ((1, 'left'), (-1, 'right')):
    hand = hands['Relaxed unified hand ' + label]
    accessors = [g['accessors'][p['attributes']['POSITION']]
                 for p in g['meshes'][hand['mesh']]['primitives']]
    assert all(side * (a[bound][0] + hand.get('translation', [0, 0, 0])[0]) > 0
               for a in accessors for bound in ('min', 'max')), label
observed = set()
duration = 0
binary = memoryview(data)[28+n:]
for channel in clip['channels']:
    target = channel['target']
    observed.add((g['nodes'][target['node']]['name'], target['path']))
    sampler = clip['samplers'][channel['sampler']]
    times = g['accessors'][sampler['input']]
    values = g['accessors'][sampler['output']]
    duration = max(duration, times['max'][0]-times['min'][0])
    assert values['componentType']==5126 and sampler['interpolation']=='LINEAR'
    width = {'SCALAR':1,'VEC3':3,'VEC4':4}[values['type']]
    view = g['bufferViews'][values['bufferView']]
    offset = view.get('byteOffset',0)+values.get('byteOffset',0)
    samples = np.ndarray((values['count'],width),dtype='<f4',buffer=binary,offset=offset,
                         strides=(view.get('byteStride',width*4),4))
    assert np.isfinite(samples).all() and np.ptp(samples,axis=0).max()>.005
    assert np.allclose(samples[0],samples[-1],atol=1e-4), 'Motion does not return to neutral'
assert expected==observed and abs(duration-3.6)<.04
report={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'dimensions_gltf_y_up':dims,'depth_height_ratio':dims[2]/dims[1],'meshes':len(g['meshes']),'embedded_images':len(g.get('images',[])),'independent_facial_geometry':features,'skins':len(g.get('skins',[])),'animations':[{'name':clip['name'],'seconds':duration,'tracks':sorted(observed)}],'status':'exported short gesture; appearance subject to review'}
report['verified_vertex_color_surfaces'] = colored_surfaces
(p/'candidate-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
