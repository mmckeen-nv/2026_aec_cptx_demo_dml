"""
extract_passes.py — Extract render passes from multilayer EXR files
                    produced by the aec_demo_master Phase 5 render.

Usage (run with Blender's Python or any Python with OpenEXR + Pillow):
    python extract_passes.py
    python extract_passes.py --skip-crypto

Requires:
    pip install openexr pillow numpy

Passes extracted:
    Depth.V      → depth/depth_####.png   (16-bit grayscale, globally normalised)
                   Near = white (65535), Far = black (0)
                   Direct input for ComfyUI ControlNet depth preprocessor.

    CryptoObject00  → masks/crypto_obj_####.png   (RGBA 8-bit, if present)
    CryptoMaterial00 → masks/crypto_mat_####.png  (RGBA 8-bit, if present)

To re-run from command line:
    & "C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe" extract_passes.py
"""

import os, glob, argparse
import numpy as np
from PIL import Image

try:
    import OpenEXR, Imath
except ImportError:
    raise SystemExit("OpenEXR not installed. Run: pip install openexr")

# ---------- default paths ----------
BASE    = r"C:\Users\swags\Documents\aec_demo_master\renders\ocean_view"
EXR_DIR = os.path.join(BASE, "exr")
DEP_DIR = os.path.join(BASE, "depth")
MSK_DIR = os.path.join(BASE, "masks")


def exr_dimensions(exr_file):
    f = OpenEXR.InputFile(exr_file)
    dw = f.header()['dataWindow']
    f.close()
    return dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1


def read_channel(exr_file, channel_name, W, H):
    """Read a single FLOAT channel from an EXR file."""
    f = OpenEXR.InputFile(exr_file)
    data = np.frombuffer(
        f.channel(channel_name, Imath.PixelType(Imath.PixelType.FLOAT)),
        dtype=np.float32
    ).reshape(H, W)
    f.close()
    return data


def extract_depth(exr_files, out_dir):
    """
    Extract depth maps as 16-bit grayscale PNGs.
    Uses global min/max across all frames for temporal consistency.
    Near = white (65535), Far = black (0).
    """
    os.makedirs(out_dir, exist_ok=True)
    W, H = exr_dimensions(exr_files[0])

    # Pass 1: scan global depth range
    print(f"[Depth] Scanning {len(exr_files)} frames for global range...")
    g_min, g_max = float('inf'), float('-inf')
    for path in exr_files:
        raw = read_channel(path, 'Depth.V', W, H)
        valid = raw[np.isfinite(raw) & (raw < 1e10)]
        if len(valid):
            g_min = min(g_min, float(valid.min()))
            g_max = max(g_max, float(valid.max()))
    print(f"[Depth] Global range: {g_min:.2f}m → {g_max:.2f}m")

    # Pass 2: normalise and save
    for path in exr_files:
        frame_num = os.path.basename(path).replace("frame_", "").replace(".exr", "")
        raw = read_channel(path, 'Depth.V', W, H)
        valid_mask = np.isfinite(raw) & (raw < 1e10)
        norm = np.zeros_like(raw)
        norm[valid_mask] = 1.0 - (raw[valid_mask] - g_min) / (g_max - g_min + 1e-10)
        norm = np.clip(norm, 0.0, 1.0)
        depth_16 = (norm * 65535).astype(np.uint16)
        Image.fromarray(depth_16, mode='I;16').save(
            os.path.join(out_dir, f"depth_{frame_num}.png"))

    print(f"[Depth] {len(exr_files)} PNGs → {out_dir}")


def extract_rgba_layer(exr_files, layer_name, out_dir, out_prefix):
    """
    Extract a 4-channel (RGBA) cryptomatte layer as 8-bit RGBA PNGs.
    """
    os.makedirs(out_dir, exist_ok=True)
    W, H = exr_dimensions(exr_files[0])

    # Check layer exists
    f = OpenEXR.InputFile(exr_files[0])
    available = list(f.header()['channels'].keys())
    f.close()
    if f"{layer_name}.R" not in available:
        print(f"[{layer_name}] Not found in EXR (available: {available}) — skipping")
        return

    print(f"[{layer_name}] Extracting {len(exr_files)} frames...")
    for path in exr_files:
        frame_num = os.path.basename(path).replace("frame_", "").replace(".exr", "")
        f = OpenEXR.InputFile(path)
        channels_rgba = []
        for comp in ('R', 'G', 'B', 'A'):
            ch = f"{layer_name}.{comp}"
            if ch in available:
                arr = np.frombuffer(
                    f.channel(ch, Imath.PixelType(Imath.PixelType.FLOAT)),
                    dtype=np.float32
                ).reshape(H, W)
            else:
                arr = np.zeros((H, W), dtype=np.float32)
            channels_rgba.append(arr)
        f.close()
        rgba = np.stack(channels_rgba, axis=-1)
        img8 = (np.clip(rgba, 0, 1) * 255).astype(np.uint8)
        Image.fromarray(img8, mode='RGBA').save(
            os.path.join(out_dir, f"{out_prefix}_{frame_num}.png"))

    print(f"[{layer_name}] {len(exr_files)} PNGs → {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Extract render passes from EXR sequence")
    parser.add_argument('--exr-dir',    default=EXR_DIR,  help="Folder containing frame_####.exr files")
    parser.add_argument('--depth-dir',  default=DEP_DIR,  help="Output folder for depth PNGs")
    parser.add_argument('--masks-dir',  default=MSK_DIR,  help="Output folder for cryptomatte PNGs")
    parser.add_argument('--skip-crypto', action='store_true', help="Skip cryptomatte extraction")
    args = parser.parse_args()

    exr_files = sorted(glob.glob(os.path.join(args.exr_dir, "frame_????.exr")))
    if not exr_files:
        raise SystemExit(f"No EXR files found in {args.exr_dir}")
    print(f"Found {len(exr_files)} EXR files in {args.exr_dir}\n")

    extract_depth(exr_files, args.depth_dir)

    if not args.skip_crypto:
        extract_rgba_layer(exr_files, "CryptoObject00",   args.masks_dir, "crypto_obj")
        extract_rgba_layer(exr_files, "CryptoMaterial00", args.masks_dir, "crypto_mat")

    print("\n========== Done ==========")
    print(f"Depth maps:      {args.depth_dir}")
    print(f"Segmentation:    {args.masks_dir}")
    print()
    print("ComfyUI usage:")
    print("  1. LoadImage → depth_####.png")
    print("  2. Connect to ControlNetApply (use a depth ControlNet model)")
    print("  3. depth_####.png is 16-bit grayscale: near=white, far=black")
    print()
    print("To re-run:")
    blender_py = r"C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe"
    script = r"C:\Users\swags\Documents\aec_demo_master\scripts\extract_passes.py"
    print(f'  & "{blender_py}" "{script}"')


if __name__ == "__main__":
    main()
