"""
extract_depth_compositor.py
Extract depth maps from all EXR frames using Blender compositor.
Run via: blender --background --python scripts/extract_depth_compositor.py
"""

import bpy, os, time

EXR_DIR   = r"C:\Users\swags\Documents\aec_demo_master\renders\ocean_view\v_20260514_2109\exr"
DEPTH_DIR = r"C:\Users\swags\Documents\aec_demo_master\renders\ocean_view\v_20260514_2109\depth"
os.makedirs(DEPTH_DIR, exist_ok=True)

exr_files = sorted([f for f in os.listdir(EXR_DIR) if f.endswith('.exr')])
print(f"Processing {len(exr_files)} EXR frames → {DEPTH_DIR}")

scene = bpy.context.scene
scene.use_nodes = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode  = 'BW'
scene.render.image_settings.color_depth = '16'

tree = bpy.data.node_groups.new("DepthExtractor", 'CompositorNodeTree')
scene.compositing_node_group = tree
tree.nodes.clear()

# Image input node
img_node = tree.nodes.new("CompositorNodeImage")
img_node.location = (0, 0)

# Normalize depth: Map Range node
# Z values are in world units (metres), need 0-1 range for PNG
map_range = tree.nodes.new("CompositorNodeMapRange")
map_range.location = (300, 0)
# Initial values — will be updated per-frame after scanning
map_range.inputs["From Min"].default_value = 0.0
map_range.inputs["From Max"].default_value = 200.0
map_range.inputs["To Min"].default_value   = 1.0  # near = bright
map_range.inputs["To Max"].default_value   = 0.0  # far  = dark

# Clamp
clamp_node = tree.nodes.new("CompositorNodeClamp")
clamp_node.location = (500, 0)

# Output file node
out_node = tree.nodes.new("CompositorNodeOutputFile")
out_node.location = (700, 0)
out_node.directory = DEPTH_DIR
out_node.format.file_format = 'PNG'
out_node.format.color_mode  = 'BW'
out_node.format.color_depth = '16'
out_node.file_output_items[0].path = "depth_"

# Wire: image.Z → map_range → clamp → output
tree.links.new(img_node.outputs["Z"],           map_range.inputs["Value"])
tree.links.new(map_range.outputs["Value"],       clamp_node.inputs["Value"])
tree.links.new(clamp_node.outputs["Value"],      out_node.inputs[0])

# ── Pass 1: scan depth range across all frames ────────────────────────────
print("Scanning depth range...")
global_min =  1e18
global_max = -1e18

for i, fname in enumerate(exr_files):
    path = os.path.join(EXR_DIR, fname)
    img  = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = 'Linear Rec.709'
    
    w, h   = img.size
    pixels = list(img.pixels)
    
    # Z pass is stored in channel 0 (R) for single-layer EXR depth
    # Blender writes OPEN_EXR with depth as float in RGBA — R=depth
    for j in range(0, len(pixels), 4):
        v = pixels[j]
        if 0 < v < 1e9:
            if v < global_min: global_min = v
            if v > global_max: global_max = v
    
    bpy.data.images.remove(img)
    if i % 30 == 0:
        print(f"  {i+1}/{len(exr_files)}: range {global_min:.1f}–{global_max:.1f}m")

print(f"Depth range: {global_min:.2f} – {global_max:.2f} metres")

# Update map range with actual scene depth
map_range.inputs["From Min"].default_value = global_min
map_range.inputs["From Max"].default_value = global_max

# ── Pass 2: extract and save depth PNGs ──────────────────────────────────
print("\nExtracting depth maps...")
t_start = time.time()

for i, fname in enumerate(exr_files):
    frame_num = int(fname.replace("frame_","").replace(".exr",""))
    path = os.path.join(EXR_DIR, fname)
    
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = 'Linear Rec.709'
    img_node.image = img
    
    # The output filename includes the frame number
    out_node.file_output_items[0].path = f"depth_{frame_num:04d}"
    
    scene.frame_set(frame_num)
    bpy.ops.render.render(write_still=False)
    
    bpy.data.images.remove(img)
    
    if i % 20 == 0:
        elapsed = time.time() - t_start
        rate = (i+1) / elapsed if elapsed > 0 else 0
        remain = (len(exr_files) - i - 1) / rate if rate > 0 else 0
        print(f"  {i+1}/{len(exr_files)} — {remain/60:.1f} min remaining")

print(f"\nDone in {(time.time()-t_start)/60:.1f} min")
print(f"Depth maps: {DEPTH_DIR}")
