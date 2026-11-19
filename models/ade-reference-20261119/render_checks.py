"""Render authored action/morph evidence from the saved Blender source."""
from pathlib import Path
import bpy

root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'ade.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Ade_Rig'];scene.cycles.samples=24
for name,action,frame,blink,mouth in [('think','think',37,0,0),('blink','idle',1,1,0),('mouth','idle',1,0,1)]:
    rig.animation_data.action=bpy.data.actions[action];scene.frame_set(frame)
    for obj in bpy.data.objects:
        if obj.type!='MESH' or not obj.data.shape_keys:continue
        for target,value in [('blink',blink),('jawOpen',mouth)]:
            key=obj.data.shape_keys.key_blocks.get(target)
            if key:key.value=value
    scene.render.filepath=str(root/(name+'.png'));bpy.ops.render.render(write_still=True)
