"""Verify the actual GLB's geometry, skeleton, animation, and facial controls.

Only Python standard library is required. This does not certify appearance.
"""
from pathlib import Path
import struct,json,math,hashlib

ROOT=Path(__file__).resolve().parent
data=(ROOT/'ade.glb').read_bytes()
magic,version,length=struct.unpack_from('<4sII',data)
assert magic==b'glTF' and version==2 and length==len(data),'Invalid GLB header'
js_len,js_type=struct.unpack_from('<II',data,12)
assert js_type==0x4E4F534A
g=json.loads(data[20:20+js_len])
bin_start=20+js_len
bin_len,bin_type=struct.unpack_from('<II',data,bin_start)
assert bin_type==0x004E4942
blob=memoryview(data)[bin_start+8:bin_start+8+bin_len]
assert not any('uri' in b for b in g.get('buffers',[])),'Model must be self-contained'
assert not any('uri' in i for i in g.get('images',[])),'Textures must be embedded'

def accessor(index):
    a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
    types={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}
    widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    fmt='<'+types[a['componentType']]*widths[a['type']]
    offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',struct.calcsize(fmt))
    return [struct.unpack_from(fmt,blob,offset+i*stride) for i in range(a['count'])]

triangles=vertices=skin_primitives=morph_primitives=0;depth=0
for m in g.get('meshes',[]):
    for p in m['primitives']:
        assert p.get('mode',4)==4,'Expected triangle geometry'
        positions=accessor(p['attributes']['POSITION']);vertices+=len(positions)
        assert all(math.isfinite(c) for v in positions for c in v),'Invalid geometry values'
        depth=max(depth,max(v[2] for v in positions)-min(v[2] for v in positions))
        triangles+=len(accessor(p['indices']))//3
        if 'JOINTS_0' in p['attributes']:
            skin_primitives+=1
            for row in accessor(p['attributes']['WEIGHTS_0']):
                assert abs(sum(row)-1)<.0001,'Invalid skin weight sum'
        if p.get('targets'):morph_primitives+=1
assert vertices>1000 and triangles>1000 and depth>.15,'Insufficient volumetric geometry'
assert skin_primitives and len(g.get('skins',[]))==1
joint_count=len(g['skins'][0]['joints']);assert joint_count>=17
animations={a['name']:a for a in g.get('animations',[])}
assert {'idle','wave','think'}<=animations.keys(),'Missing required clips'
animated_nodes={}
for name,a in animations.items():
    varying=set();duration=0
    for c in a['channels']:
        sampler=a['samplers'][c['sampler']]
        times=accessor(sampler['input']);values=accessor(sampler['output'])
        assert times[0][0]>=0,'Invalid animation time'
        duration=max(duration,times[-1][0])
        assert all(math.isfinite(x) for v in values for x in v)
        if any(any(abs(x-y)>.00001 for x,y in zip(v,values[0])) for v in values[1:]):varying.add(c['target']['node'])
    assert duration>1,'Invalid animation duration'
    assert len(varying)>=2,f'{name} has no coordinated skeletal motion'
    animated_nodes[name]=len(varying)
target_names={name for m in g['meshes'] for name in m.get('extras',{}).get('targetNames',[])}
assert {'blink','jawOpen'}<=target_names,'Missing facial controls'
assert morph_primitives>=13,'Some eye parts lost their blink shape keys'
assert g.get('images') and g.get('materials'),'Missing embedded appearance'
result={'status':'pass','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'meshes':len(g['meshes']),
    'vertices':vertices,'triangles':triangles,'skeleton_joints':joint_count,'animated_nodes':animated_nodes,
    'morph_primitives':morph_primitives,'face_targets':sorted(target_names),'embedded_images':len(g['images']),
    'limits':'Structure only; does not certify likeness, all-frame cloth quality, device FPS or phoneme lip sync.'}
(ROOT/'model-check.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
