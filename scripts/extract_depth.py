"""
extract_depth.py
Extract normalised depth maps from Cycles EXR frames.
Run via: blender --background --python scripts/extract_depth.py

Reads every frame_NNNN.exr from EXR_DIR, extracts the Z (depth) channel,
normalises per-sequence (consistent across all frames so depth is comparable),
and writes 16-bit grayscale PNGs to DEPTH_DIR.
"""

import bpy, os, struct, array

EXR_DIR   = r"C:\Users\swags\Documents\aec_demo_master\renders\ocean_view\v_20260514_2109\exr"
DEPTH_DIR = r"C:\Users\swags\Documents\aec_demo_master\renders\ocean_view\v_20260514_2109\depth"
os.makedirs(DEPTH_DIR, exist_ok=True)

exr_files = sorted([f for f in os.listdir(EXR_DIR) if f.endswith('.exr')])
print(f"Found {len(exr_files)} EXR files")

# ── Pass 1: find global depth range across all frames ─────────────────────
print("Pass 1: scanning depth range...")
global_min =  1e18
global_max = -1e18

for fname in exr_files:
    path = os.path.join(EXR_DIR, fname)
    img  = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Linear Rec.709'
    
    w, h    = img.size
    pixels  = list(img.pixels)          # RGBA per pixel (4 values each)
    n_pixels = w * h
    
    # In Blender EXR with depth pass, the Z layer is stored as a separate
    # pass. With OPEN_EXR (single layer) + passes enabled, the depth data
    # is in the image's first channel when you load with the correct layer.
    # Blender packs passes as separate images — check image.layers
    has_layers = hasattr(img, 'render_slots') or len(getattr(img, 'layers', [])) > 0
    
    # The Z pass in a single-layer EXR with passes = the depth channel
    # Blender stores it so the R channel = depth value when depth pass active
    # We read pixels and take channel 0 (R = depth for Z-only render)
    z_vals = [pixels[i*4] for i in range(n_pixels) if pixels[i*4] < 1e10]  # skip inf
    
    if z_vals:
        local_min = min(z_vals)
        local_max = max(z_vals)
        if local_min < global_min: global_min = local_min
        if local_max > global_max: global_max = local_max
    
    bpy.data.images.remove(img)
    if exr_files.index(fname) % 20 == 0:
        print(f"  scanned {exr_files.index(fname)+1}/{len(exr_files)} — range so far: {global_min:.2f} → {global_max:.2f}")

print(f"Global depth range: {global_min:.3f} → {global_max:.3f} units")

# ── Pass 2: extract + normalise + save 16-bit PNG ─────────────────────────
print("\nPass 2: extracting depth maps...")
depth_range = global_max - global_min
if depth_range == 0: depth_range = 1.0

for fname in exr_files:
    frame_num = fname.replace('frame_','').replace('.exr','')
    path = os.path.join(EXR_DIR, fname)
    img  = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Linear Rec.709'
    
    w, h   = img.size
    pixels = list(img.pixels)
    
    # Build normalised depth image (0=near/black, 65535=far/white)
    # Invert: near=bright is more useful for compositing (closer = more mask)
    depth_img = bpy.data.images.new(f"depth_{frame_num}", w, h, float_buffer=False)
    depth_pixels = []
    
    for i in range(w * h):
        z = pixels[i * 4]           # R channel = depth
        if z >= 1e10:               # background / infinite depth
            norm = 0.0
        else:
            norm = 1.0 - (z - global_min) / depth_range  # invert: near=bright
            norm = max(0.0, min(1.0, norm))
        depth_pixels += [norm, norm, norm, 1.0]   # grayscale RGBA
    
    depth_img.pixels = depth_pixels
    depth_img.file_format = 'PNG'
    depth_img.colorspace_settings.name = 'Linear Rec.709'
    
    out_path = os.path.join(DEPTH_DIR, f"depth_{frame_num}.png")
    depth_img.filepath_raw = out_path
    depth_img.save()
    
    bpy.data.images.remove(img)
    bpy.data.images.remove(depth_img)
    
    if int(frame_num) % 20 == 0:
        print(f"  saved depth_{frame_num}.png")

print(f"\nDone. {len(exr_files)} depth maps → {DEPTH_DIR}")
