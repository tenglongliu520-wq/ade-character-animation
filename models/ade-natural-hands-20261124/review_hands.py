"""Check and render the exported neutral hand shapes from both sides."""
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from PIL import Image, ImageDraw, ImageFont

from relaxed_hands import FINGERS, THUMB_TIP, hand_point


root = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root / "ade.blend"))
scene = bpy.context.scene
scene.frame_set(1)
scene.cycles.samples = 20
scene.render.resolution_x = scene.render.resolution_y = 440
scene.render.resolution_percentage = 100
camera = scene.camera
camera.data.ortho_scale = .192

assert tuple(name for name, *_ in FINGERS) == ("index", "middle", "ring", "little")
tip_heights = {name: end for name, _, _, _, end, _ in FINGERS}
assert tip_heights["middle"] < tip_heights["ring"] < tip_heights["index"] < tip_heights["little"] < THUMB_TIP[2]

font = ImageFont.load_default(size=17)
number_font = ImageFont.load_default(size=18)
sheet = Image.new("RGB", (904, 962), "#f6f4ec")
draw = ImageDraw.Draw(sheet)
all_meshes = [obj for obj in scene.objects if obj.type == "MESH"]

for column, (side, name) in enumerate(((-1, "right"), (1, "left"))):
    hand = bpy.data.objects["Relaxed unified hand " + name]
    vertices = [hand.matrix_world @ vertex.co for vertex in hand.data.vertices]
    assert all(side * vertex.x > 0 for vertex in vertices), f"Incorrect {name} hand placement"
    surface = BVHTree.FromPolygons(vertices, [face.vertices for face in hand.data.polygons])
    tips = [THUMB_TIP, *((tip, .006, end) for _, _, tip, _, end, _ in FINGERS)]
    positions = [Vector(hand_point(side, *tip)) for tip in tips]
    # Facing Ade, screen x follows world x. On both hands the thumb
    # starts at the outer edge and the remaining digits lead inward.
    assert all(side*a.x > side*b.x for a, b in zip(positions, positions[1:])), name
    for tip in positions:
        assert surface.find_nearest(tip, .005)[0] is not None, (name, tip)

    lateral, depth, notch_height = -.039, .002, .645
    first = Vector(hand_point(side, lateral, depth-.09, notch_height))
    last = Vector(hand_point(side, lateral, depth+.09, notch_height))
    assert surface.ray_cast(first, last-first, .18)[0] is None, f"{name} thumb-index gap is closed"

    for row in range(2):
        for obj in all_meshes:
            obj.hide_render = row == 1 and obj != hand
        target = Vector(hand_point(side, -.009, 0, .671))
        offset = Vector((0, -2, 0)) if row == 0 else Vector((side*.27, -2, .02))
        camera.location = target + offset
        camera.rotation_euler = (target-camera.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = str(root / f"hand-{name}-{row}.png")
        bpy.ops.render.render(write_still=True)
        tile = Image.open(scene.render.filepath).convert("RGB")
        x, y = 8 + column*448, 32 + row*469
        sheet.paste(tile, (x, y))
        Path(scene.render.filepath).unlink()
        view = "front with sleeve" if row == 0 else "palm side"
        draw.text((x, y-23), f"Ade's {name} hand | {view}", fill="#244638", font=font)
        if row == 0:
            continue
        for number, tip in enumerate(positions, 1):
            projected = world_to_camera_view(scene, camera, tip)
            px, py = x+projected.x*440, y+(1-projected.y)*440
            label_y = y+395 if number > 1 else py+32
            label_x = px + side*25 if number == 1 else px
            draw.line(((px, py), (label_x, label_y)), fill="#f7ebcf", width=2)
            draw.ellipse((px-3, py-3, px+3, py+3), fill="#f7ebcf")
            draw.ellipse((label_x-12, label_y-12, label_x+12, label_y+12), fill="#f7ebcf")
            draw.text((label_x, label_y), str(number), fill="#263e34", font=number_font, anchor="mm")

sheet.save(root / "hand-order.jpg", quality=93)
print("Verified ten digit tips, both thumb-index gaps, and both thumbs at the outer edges.")
