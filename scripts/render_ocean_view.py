"""
render_ocean_view.py
Full scene setup + versioned render for ocean_view animation.
Run via: blender --background base_model.blend --python scripts/render_ocean_view.py
"""
import bpy, math, mathutils, os, datetime, subprocess, time

scene = bpy.context.scene

# ── Versioned output ──────────────────────────────────────────────────────
stamp   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
BASE    = r"C:\Users\swags\Documents\aec_demo_master\renders\ocean_view"
OUT_DIR = os.path.join(BASE, f"v_{stamp}")
PNG_DIR = os.path.join(OUT_DIR, "png")
os.makedirs(PNG_DIR, exist_ok=True)
print(f"Output: {PNG_DIR}")

# ── Materials ─────────────────────────────────────────────────────────────
def mat(name, color, roughness, metallic=0.0, transmission=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if not b:
        m.node_tree.nodes.clear()
        b = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        o = m.node_tree.nodes.new("ShaderNodeOutputMaterial")
        m.node_tree.links.new(b.outputs["BSDF"], o.inputs["Surface"])
    b.inputs["Base Color"].default_value  = color
    b.inputs["Roughness"].default_value   = roughness
    b.inputs["Metallic"].default_value    = metallic
    if transmission > 0:
        b.inputs["Transmission Weight"].default_value = transmission
        m.blend_method = "BLEND"
    return m

ochre    = mat("M_Wall_Ochre",    (0.42,0.28,0.07,1), 0.78)
roof_m   = mat("M_Roof_Metal",    (0.06,0.08,0.18,1), 0.45, 0.55)
grass_m  = mat("M_Grass",         (0.00375,0.010,0.00375,1), 0.92)
asphalt  = mat("M_Asphalt",       (0.08,0.08,0.08,1), 0.92)
concrete = mat("M_DarkConcrete",  (0.09,0.09,0.09,1), 0.85)
midgray  = mat("M_Slab_LightGray",(0.50,0.50,0.50,1), 0.72)
glass_m  = mat("M_Glass_Tinted_Reflective",(0.12,0.18,0.22,1),0.03,0.0,0.75)
gunmetal = mat("M_Aluminum",      (0.18,0.19,0.20,1), 0.80, 0.40)
wood_m   = mat("M_Wood_Warm",     (0.18,0.10,0.04,1), 0.70)

def assign(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)

for obj in bpy.data.objects:
    if obj.type != 'MESH': continue
    n = obj.name.lower()
    if   "roof"    in n:                                       assign(obj, roof_m)
    elif "wall"    in n or "balcony" in n or "railing" in n:   assign(obj, ochre)
    elif "glass"   in n or "door"    in n:                     assign(obj, glass_m)
    elif "mull"    in n:                                       assign(obj, gunmetal)
    elif "street"  in n or "road"    in n:                     assign(obj, asphalt)
    elif "driveway"in n or "entry_step" in n:                  assign(obj, concrete)
    elif any(x in n for x in ("floor","slab","building_pad","curtain",
                               "retaining","entry_canopy","entry_col",
                               "entry_landing")):              assign(obj, midgray)
    elif "terrain" in n or n == "obj_1":                       assign(obj, grass_m)

# Smooth terrain
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.name == 'obj_1':
        for poly in obj.data.polygons: poly.use_smooth = True
        obj.data.update()

# ── World / HDRI ──────────────────────────────────────────────────────────
HDR = r"C:\Users\swags\Documents\aec_demo_master\assets\RADSKY-007SX.hdr"
world = scene.world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()

out  = nt.nodes.new("ShaderNodeOutputWorld")
bg   = nt.nodes.new("ShaderNodeBackground")
env  = nt.nodes.new("ShaderNodeTexEnvironment")
tc   = nt.nodes.new("ShaderNodeTexCoord")
mpp  = nt.nodes.new("ShaderNodeMapping")
gamma= nt.nodes.new("ShaderNodeGamma")

env.image = bpy.data.images.load(HDR, check_existing=True)
# WSW = 247.5° from north. HDRI rotation to put warm zone at WSW:
mpp.inputs["Rotation"].default_value[2] = math.radians(202.5)
gamma.inputs["Gamma"].default_value = 4.0
bg.inputs["Strength"].default_value = 2.25

nt.links.new(tc.outputs["Generated"],  mpp.inputs["Vector"])
nt.links.new(mpp.outputs["Vector"],    env.inputs["Vector"])
nt.links.new(env.outputs["Color"],     gamma.inputs["Color"])
nt.links.new(gamma.outputs["Color"],   bg.inputs["Color"])
nt.links.new(bg.outputs["Background"],out.inputs["Surface"])

# ── Sun lamp — FROM WEST, aimed east at 5° below horizontal ──────────────
for obj in list(bpy.data.objects):
    if obj.type == 'LIGHT': bpy.data.objects.remove(obj, do_unlink=True)

sun_d = bpy.data.lights.new("SunSet","SUN")
sun_d.energy = 4.0
sun_d.color  = (1.0,0.52,0.16)
sun_d.angle  = math.radians(1.5)
sun_o = bpy.data.objects.new("SunSet", sun_d)
scene.collection.objects.link(sun_o)
# R_y(-90°) makes lamp -Z point +X (east). lamp shines east = sun is in west.
# Z=+22.5° adds 22.5° toward north → sun is WSW (rays go ENE).
# X=-5° adds downward elevation tilt.
sun_o.rotation_euler = mathutils.Euler(
    (math.radians(-5), math.radians(-90), math.radians(22.5)), 'XYZ')

# ── Camera ────────────────────────────────────────────────────────────────
for name in ["ocean_view","cam_target"]:
    obj = bpy.data.objects.get(name)
    if obj: bpy.data.objects.remove(obj, do_unlink=True)

cx, cy = 11.0, 0.0
cam_data = bpy.data.cameras.new("ocean_view")
cam_data.lens = 28.0; cam_data.clip_start=0.5; cam_data.clip_end=500.0
cam_obj = bpy.data.objects.new("ocean_view", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

bpy.ops.object.empty_add(type='SPHERE', radius=0.3, location=(cx,cy,3.0))
tgt = bpy.context.active_object; tgt.name = "cam_target"
tc_cam = cam_obj.constraints.new(type='TRACK_TO')
tc_cam.target=tgt; tc_cam.track_axis='TRACK_NEGATIVE_Z'; tc_cam.up_axis='UP_Y'

scene.frame_start=0; scene.frame_end=143

keyframes=[
    (  0,-18.0,-26.0,6.5,2.5),
    ( 20,-26.0,-10.0,5.5,3.0),
    ( 48,-30.0,  0.0,4.5,3.0),
    ( 70,-26.0, 18.0,5.0,3.5),
    ( 90, -8.0, 38.0,7.0,3.0),
    (110, 28.0, 30.0,5.5,3.0),
    (130, 44.0,  0.0,5.0,2.5),
    (143,-14.0,-28.0,6.0,2.5),
]
for frame,x,y,camZ,targZ in keyframes:
    scene.frame_set(frame)
    cam_obj.location=(x,y,camZ)
    cam_obj.keyframe_insert(data_path="location",frame=frame)
    tgt.location=(cx,cy,targZ)
    tgt.keyframe_insert(data_path="location",frame=frame)

# ── Render settings ───────────────────────────────────────────────────────
scene.render.engine  = 'CYCLES'
scene.cycles.device  = 'GPU'
scene.cycles.samples = 384
scene.cycles.use_denoising = True
try:    scene.cycles.denoiser = 'OPTIX'
except: scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(PNG_DIR, "frame_")

# ── Render verification frame first (frame 0, 64 samples) ────────────────
scene.cycles.samples = 64
scene.frame_set(0)
verify_path = os.path.join(OUT_DIR, "verify_frame0.png")
scene.render.filepath = verify_path
bpy.ops.render.render(write_still=True)
print(f"Verify frame saved: {verify_path}")
print("CHECK highlights/shadows before full render!")

# ── Full sequence ─────────────────────────────────────────────────────────
scene.cycles.samples = 384
scene.render.filepath = os.path.join(PNG_DIR, "frame_")
t = time.time()
bpy.ops.render.render(animation=True)
elapsed = (time.time()-t)/60
print(f"Render complete: {elapsed:.1f} min → {PNG_DIR}")

# ── Encode MP4 ────────────────────────────────────────────────────────────
ffmpeg = (r"C:\Users\swags\AppData\Local\Microsoft\WinGet\Packages"
          r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
          r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe")
mp4 = os.path.join(OUT_DIR, "ocean_view.mp4")
subprocess.run([ffmpeg,"-y","-framerate","24","-start_number","0",
    "-i",os.path.join(PNG_DIR,"frame_%04d.png"),
    "-c:v","libx264","-pix_fmt","yuv420p","-crf","18",mp4],check=True)
print(f"MP4: {mp4}")
