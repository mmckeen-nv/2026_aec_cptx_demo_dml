
import sys, os
sys.path.insert(0, r"C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\lib\site-packages")
import OpenEXR, numpy as np
from PIL import Image as PILImage

TEMP      = r"C:\Users\swags\Documents\aec_demo_master\renders\ocean_view\v_20260514_2109\depth_raw_temp"
DEPTH_DIR = r"C:\Users\swags\Documents\aec_demo_master\renders\ocean_view\v_20260514_2109\depth"

for f in os.listdir(DEPTH_DIR): os.remove(os.path.join(DEPTH_DIR, f))

files = sorted([f for f in os.listdir(TEMP) if f.endswith('.exr')])
print(f"Re-normalising {len(files)} frames (NO flipud this time)...")

ok = 0
for fname in files:
    frame_num = fname.replace("raw_","").replace(".exr","")
    f   = OpenEXR.File(os.path.join(TEMP, fname))
    px  = list(f.channels().values())[0].pixels    # (H, W, 3) float32
    # NO flipud - Blender EXR via OpenEXR is already top-down
    raw = px[:, :, 0].astype(np.float32)

    valid = raw[raw > 0.01]
    if len(valid) == 0:
        norm = np.zeros_like(raw, dtype=np.uint16)
    else:
        d_min, d_max = float(valid.min()), float(valid.max())
        n = np.clip(1.0 - (raw - d_min) / max(d_max - d_min, 0.001), 0.0, 1.0)
        n[raw <= 0.01] = 0.0
        norm = (n * 65535).astype(np.uint16)

    img = PILImage.fromarray(norm.astype(np.int32), mode='I')
    img.save(os.path.join(DEPTH_DIR, f"depth_{frame_num}.png"))
    ok += 1

print(f"Done: {ok} depth maps saved (right-side up)")
