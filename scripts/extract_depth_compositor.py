"""
extract_depth_compositor.py
Extract normalized depth maps from single-layer EXR frames with Blender 5.2.
Run via: blender --background --python scripts/extract_depth_compositor.py
"""

import os
import time

import bpy

from path_config import RENDER_ROOT


EXR_DIR = os.environ.get("AEC_EXR_DIR", str(RENDER_ROOT / "exr"))
DEPTH_DIR = os.environ.get("AEC_DEPTH_DIR", str(RENDER_ROOT / "depth"))
os.makedirs(DEPTH_DIR, exist_ok=True)

exr_files = sorted(f for f in os.listdir(EXR_DIR) if f.endswith(".exr"))
print(f"Processing {len(exr_files)} EXR frames -> {DEPTH_DIR}")

scene = bpy.context.scene
scene.use_nodes = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "BW"
scene.render.image_settings.color_depth = "16"

tree = bpy.data.node_groups.get("DepthExtractor")
if tree is None:
    tree = bpy.data.node_groups.new("DepthExtractor", "CompositorNodeTree")
scene.compositing_node_group = tree
tree.nodes.clear()

image_node = tree.nodes.new("CompositorNodeImage")
image_node.location = (0, 0)

# Blender 5.2 removed compositor Map Range, Math, and Clamp nodes. A
# single-layer depth EXR stores depth in its image channels, so normalize the
# Image output per frame and invert it: near = bright, far = dark.
normalize_node = tree.nodes.new("CompositorNodeNormalize")
normalize_node.location = (300, 0)

invert_node = tree.nodes.new("CompositorNodeInvert")
invert_node.location = (500, 0)
invert_node.inputs["Factor"].default_value = 1.0

output_node = tree.nodes.new("CompositorNodeOutputFile")
output_node.location = (700, 0)
output_node.directory = DEPTH_DIR
output_node.format.file_format = "PNG"
output_node.format.color_mode = "BW"
output_node.format.color_depth = "16"
output_node.file_output_items[0].path = "depth_"

tree.links.new(image_node.outputs["Image"], normalize_node.inputs["Value"])
tree.links.new(normalize_node.outputs["Value"], invert_node.inputs["Color"])
tree.links.new(invert_node.outputs["Color"], output_node.inputs[0])

print("Extracting depth maps...")
started = time.time()

for index, filename in enumerate(exr_files):
    frame_number = int(filename.replace("frame_", "").replace(".exr", ""))
    path = os.path.join(EXR_DIR, filename)

    image = bpy.data.images.load(path, check_existing=False)
    image.colorspace_settings.name = "Linear Rec.709"
    image_node.image = image
    output_node.file_output_items[0].path = f"depth_{frame_number:04d}"

    scene.frame_set(frame_number)
    bpy.ops.render.render(write_still=False)
    bpy.data.images.remove(image)

    if index % 20 == 0:
        elapsed = time.time() - started
        rate = (index + 1) / elapsed if elapsed > 0 else 0
        remaining = (len(exr_files) - index - 1) / rate if rate > 0 else 0
        print(f"  {index + 1}/{len(exr_files)} - {remaining / 60:.1f} min remaining")

print(f"Done in {(time.time() - started) / 60:.1f} min")
print(f"Depth maps: {DEPTH_DIR}")
