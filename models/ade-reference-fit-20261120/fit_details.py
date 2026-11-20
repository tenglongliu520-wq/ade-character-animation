"""Garment color frame and model surface helpers for the recorded Ade."""
from pathlib import Path

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent

# The interiors stay clear of skin, the ivory lining, the sash and background.
CLOTH_PANELS = (
    [(248,424),(261,437),(238,526),(231,606),(231,638),(204,629),
     (171,627),(149,615),(150,590),(167,541),(208,469)],
    [(349,433),(372,455),(406,523),(432,589),(437,620),(421,638),
     (384,632),(360,644),(351,578),(348,509)],
    [(195,663),(215,655),(227,672),(224,785),(185,775),(171,762)],
    [(364,659),(392,669),(416,704),(427,764),(402,791),(370,798)],
)

def prepare_fabric():
    with Image.open(ROOT / "reference-front.png") as frame:
        rgb = np.asarray(frame.convert("RGB")).astype(float)
    inside = Image.new("L", (720, 950))
    drawing = ImageDraw.Draw(inside)
    for panel in CLOTH_PANELS:
        drawing.polygon(panel, fill=255)
    eligible = (
        (rgb[:,:,1] - rgb[:,:,0] > 2)
        & (rgb[:,:,1] > 98)
        & (rgb[:,:,1] - rgb[:,:,2] > -12)
    )
    weight = np.asarray(inside).astype(float) / 255 * eligible
    weighted = Image.fromarray(np.uint8(rgb[:,:,1] * weight))
    coverage = Image.fromarray(np.uint8(weight * 255))
    local_green = np.asarray(weighted.filter(ImageFilter.GaussianBlur(13))).astype(float)
    local_weight = np.asarray(coverage.filter(ImageFilter.GaussianBlur(13))).astype(float) / 255
    local_green /= np.maximum(local_weight, .15)
    pattern = np.clip(rgb[:,:,1] - local_green, -65, 50)
    base = np.array((181,201,184), dtype=float)
    color = np.clip(base[None,None,:] + pattern[:,:,None] * .91, 0, 255)
    # A feathered flat color field avoids copying the recorded scene lighting.
    alpha = np.asarray(inside.filter(ImageFilter.GaussianBlur(5))).astype(float) / 255
    alpha *= np.asarray(coverage.filter(ImageFilter.GaussianBlur(2))).astype(float) / 255
    rgba = np.dstack((color, alpha * 255))
    Image.fromarray(np.uint8(rgba)).save(ROOT / "recorded-fabric.png")

def recorded_coordinates(px, py):
    return (px - 302) / 376, (915 - py) / 376

def smooth_samples(points, subdivisions=8):
    """Cubic samples with smooth tangents through all of the control points."""
    for i in range(len(points)-1):
        a, b, c, d = (points[index] for index in (
            max(i-1,0), i, i+1, min(i+2,len(points)-1)
        ))
        for j in range(subdivisions):
            t = j / subdivisions
            yield (2*b + (c-a)*t + (2*a-5*b+4*c-d)*t*t + (-a+3*b-3*c+d)*t*t*t) * .5
    yield points[-1]

def hair_lock(controls):
    """Sweep a tapered oval cross section along a reference trace in 3D."""
    from mathutils import Vector

    points = []
    for px, py, depth, width, thickness in controls:
        x, z = recorded_coordinates(px, py)
        points.append(Vector((x,depth,z,width,thickness)))
    samples = list(smooth_samples(points))
    vertices, faces = [], []
    sides = 16
    for i, value in enumerate(samples):
        center = Vector(value[:3])
        direction = Vector(samples[min(i+1,len(samples)-1)][:3]) - Vector(samples[max(i-1,0)][:3])
        width_axis = direction.cross(Vector((0,1,0))).normalized()
        depth_axis = direction.normalized().cross(width_axis)
        for j in range(sides):
            angle = 2*math.pi*j/sides
            distance = max(value[3], .001) * math.cos(angle)
            depth = max(value[4], .001) * math.sin(angle)
            vertices.append(center + width_axis*distance + depth_axis*depth)
        if i:
            for j in range(sides):
                a=(i-1)*sides+j
                b=(i-1)*sides+(j+1)%sides
                faces.append((a,b,b+sides,a+sides))
    faces.extend([tuple(reversed(range(sides))), tuple(range(len(vertices)-sides,len(vertices)))])
    return vertices, faces

if __name__ == "__main__":
    prepare_fabric()
