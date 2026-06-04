"""
comfyui_phase7.py — Phase 7 automation: Blender renders → ComfyUI → enhanced MP4

Connects to ComfyUI on the DGX Spark at 192.168.50.67:8188, queries available
models, uploads frame pairs (beauty + depth), queues depth-conditioned img2img
workflows, downloads results, and encodes ocean_view_ai.mp4.

Usage:
    python comfyui_phase7.py
    python comfyui_phase7.py --denoise 0.4 --strength 0.8 --steps 25
    python comfyui_phase7.py --checkpoint mymodel.safetensors --controlnet depth_v2.safetensors
    python comfyui_phase7.py --frames 0-23          # process a range only
    python comfyui_phase7.py --dry-run              # connect + show models, don't process

Requires: pip install requests pillow tqdm
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE      = Path(r"C:\Users\swags\Documents\aec_demo_master\renders\ocean_view")
PNG_DIR   = BASE / "png"
DEPTH_DIR = BASE / "depth"
OUT_DIR   = BASE / "ai_enhanced"
FFMPEG    = (r"C:\Users\swags\AppData\Local\Microsoft\WinGet\Packages"
             r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
             r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe")

# ─── ComfyUI settings ─────────────────────────────────────────────────────────
COMFYUI_URL        = "http://192.168.50.67:8188"
CHECKPOINT         = None     # None = auto-select first available
CONTROLNET         = None     # None = auto-select first depth model
POSITIVE_PROMPT    = (
    "architectural visualization, modernist hillside house, concrete and glass, "
    "photorealistic render, dramatic natural lighting, golden hour, sharp focus, "
    "professional photography, 8k, ultra detailed"
)
NEGATIVE_PROMPT    = (
    "blurry, distorted, painting, sketch, cartoon, low quality, artifacts, "
    "unrealistic, interior, people, cars, text, watermark"
)
DENOISE            = 0.38
CONTROLNET_STRENGTH = 0.75
STEPS              = 20
CFG                = 7.0
SAMPLER            = "euler"
SCHEDULER          = "normal"
SEED               = 42       # fixed seed = temporal consistency across frames
BATCH_SIZE         = 3        # concurrent frames in flight (tune for VRAM)
POLL_INTERVAL      = 1.5      # seconds between history polls
UPLOAD_TIMEOUT     = 30
QUEUE_TIMEOUT      = 10
DOWNLOAD_TIMEOUT   = 30


# ─── ComfyUI API ──────────────────────────────────────────────────────────────

def api(method, endpoint, **kwargs):
    url = f"{COMFYUI_URL}{endpoint}"
    kwargs.setdefault("timeout", 15)
    r = requests.request(method, url, **kwargs)
    r.raise_for_status()
    return r


def check_server():
    try:
        r = api("GET", "/system_stats")
        d = r.json()
        gpu = d.get("system", {}).get("gpu_utilization", "n/a")
        vram = d.get("system", {}).get("vram_total", "?")
        print(f"  ComfyUI online — GPU util {gpu}%, VRAM {vram} MB")
        return True
    except Exception as e:
        print(f"  ERROR: cannot reach {COMFYUI_URL}  ({e})")
        return False


def get_models():
    """Return dict of available checkpoints and ControlNets."""
    info = api("GET", "/object_info").json()
    checkpoints = (info.get("CheckpointLoaderSimple", {})
                       .get("input", {})
                       .get("required", {})
                       .get("ckpt_name", [None])[0]) or []
    controlnets = (info.get("ControlNetLoader", {})
                       .get("input", {})
                       .get("required", {})
                       .get("control_net_name", [None])[0]) or []
    return checkpoints, controlnets


def pick_depth_controlnet(controlnets):
    """Auto-select the first ControlNet whose name suggests depth."""
    depth_keywords = ["depth", "dep", "d_"]
    for cn in controlnets:
        if any(kw in cn.lower() for kw in depth_keywords):
            return cn
    return controlnets[0] if controlnets else None


def upload_image(local_path, subfolder="phase7"):
    """Upload a PNG/EXR to ComfyUI's input folder. Returns server filename."""
    with open(local_path, "rb") as f:
        r = requests.post(
            f"{COMFYUI_URL}/upload/image",
            files={"image": (Path(local_path).name, f, "image/png")},
            data={"subfolder": subfolder, "type": "input", "overwrite": "true"},
            timeout=UPLOAD_TIMEOUT
        )
    r.raise_for_status()
    resp = r.json()
    # ComfyUI returns {"name": "...", "subfolder": "...", "type": "input"}
    name = resp.get("name", Path(local_path).name)
    sub  = resp.get("subfolder", subfolder)
    return f"{sub}/{name}" if sub else name


def build_workflow(beauty_ref, depth_ref, checkpoint, controlnet,
                   seed, denoise, controlnet_strength, steps, cfg,
                   positive_prompt, negative_prompt):
    """
    Build a ComfyUI workflow dict for depth-conditioned img2img.

    Graph:
      [1] CheckpointLoaderSimple  →  model, clip, vae
      [2] CLIPTextEncode (pos)    →  conditioning
      [3] CLIPTextEncode (neg)    →  conditioning
      [4] ControlNetLoader        →  control_net
      [5] LoadImage (beauty)      →  pixels
      [6] LoadImage (depth)       →  depth image
      [7] VAEEncode               →  latent
      [8] ControlNetApply         →  conditioned positive
      [9] KSampler                →  latent out
     [10] VAEDecode               →  image
     [11] SaveImage               →  output
    """
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint}
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive_prompt, "clip": ["1", 1]}
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative_prompt, "clip": ["1", 1]}
        },
        "4": {
            "class_type": "ControlNetLoader",
            "inputs": {"control_net_name": controlnet}
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": beauty_ref}
        },
        "6": {
            "class_type": "LoadImage",
            "inputs": {"image": depth_ref}
        },
        "7": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["5", 0], "vae": ["1", 2]}
        },
        "8": {
            "class_type": "ControlNetApply",
            "inputs": {
                "conditioning":  ["2", 0],
                "control_net":   ["4", 0],
                "image":         ["6", 0],
                "strength":      controlnet_strength
            }
        },
        "9": {
            "class_type": "KSampler",
            "inputs": {
                "model":         ["1", 0],
                "positive":      ["8", 0],
                "negative":      ["3", 0],
                "latent_image":  ["7", 0],
                "seed":          seed,
                "steps":         steps,
                "cfg":           cfg,
                "sampler_name":  SAMPLER,
                "scheduler":     SCHEDULER,
                "denoise":       denoise
            }
        },
        "10": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["9", 0], "vae": ["1", 2]}
        },
        "11": {
            "class_type": "SaveImage",
            "inputs": {"images": ["10", 0], "filename_prefix": "ai_enhanced"}
        }
    }


def queue_prompt(workflow):
    """Submit workflow to ComfyUI. Returns prompt_id."""
    payload = {"prompt": workflow, "client_id": "phase7_script"}
    r = api("POST", "/prompt", json=payload, timeout=QUEUE_TIMEOUT)
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"Workflow error: {data['error']}")
    if data.get("node_errors"):
        raise RuntimeError(f"Node errors: {json.dumps(data['node_errors'], indent=2)}")
    return data["prompt_id"]


def wait_for_result(prompt_id, frame_label):
    """Poll /history until complete. Returns list of output image dicts."""
    while True:
        try:
            r = api("GET", f"/history/{prompt_id}")
            hist = r.json()
        except Exception:
            time.sleep(POLL_INTERVAL)
            continue

        if prompt_id not in hist:
            time.sleep(POLL_INTERVAL)
            continue

        entry = hist[prompt_id]
        status = entry.get("status", {})
        if status.get("status_str") == "error":
            msgs = status.get("messages", [])
            raise RuntimeError(f"Frame {frame_label} failed: {msgs}")

        outputs = entry.get("outputs", {})
        # Find SaveImage node output (node "11")
        for node_id, node_out in outputs.items():
            images = node_out.get("images", [])
            if images:
                return images

        if not status.get("completed", False):
            time.sleep(POLL_INTERVAL)
            continue

        return []  # completed but no images (shouldn't happen)


def download_image(image_info, out_path):
    """Download an output image from ComfyUI to local disk."""
    params = {
        "filename": image_info["filename"],
        "subfolder": image_info.get("subfolder", ""),
        "type": image_info.get("type", "output")
    }
    url = f"{COMFYUI_URL}/view?" + urllib.parse.urlencode(params)
    r = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)


def process_frame(frame_num, beauty_path, depth_path, checkpoint, controlnet,
                  denoise, controlnet_strength, steps, cfg, seed):
    """Full pipeline for one frame: upload → queue → wait → download → return path."""
    label = f"{frame_num:04d}"
    out_path = OUT_DIR / f"frame_{label}.png"

    if out_path.exists():
        return label, str(out_path), "skipped"

    # Upload both images
    beauty_ref = upload_image(beauty_path)
    depth_ref  = upload_image(depth_path)

    # Build and queue workflow
    wf = build_workflow(
        beauty_ref, depth_ref, checkpoint, controlnet,
        seed, denoise, controlnet_strength, steps, cfg,
        POSITIVE_PROMPT, NEGATIVE_PROMPT
    )
    prompt_id = queue_prompt(wf)

    # Wait for completion
    images = wait_for_result(prompt_id, label)
    if not images:
        raise RuntimeError(f"No output images returned for frame {label}")

    # Download first output image
    download_image(images[0], out_path)
    return label, str(out_path), "done"


def encode_mp4(frame_dir, out_mp4, fps=24):
    """Encode PNG sequence to MP4 using ffmpeg."""
    pattern = str(frame_dir / "frame_%04d.png")
    cmd = [
        FFMPEG, "-y",
        "-framerate", str(fps),
        "-i", pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        str(out_mp4)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-500:]}")
    size_kb = out_mp4.stat().st_size // 1024
    print(f"  Encoded {out_mp4.name} ({size_kb} KB)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Phase 7 — ComfyUI post-processing")
    parser.add_argument("--url",        default=COMFYUI_URL)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--controlnet", default=None)
    parser.add_argument("--denoise",    type=float, default=DENOISE)
    parser.add_argument("--strength",   type=float, default=CONTROLNET_STRENGTH)
    parser.add_argument("--steps",      type=int,   default=STEPS)
    parser.add_argument("--cfg",        type=float, default=CFG)
    parser.add_argument("--seed",       type=int,   default=SEED)
    parser.add_argument("--batch",      type=int,   default=BATCH_SIZE)
    parser.add_argument("--frames",     default=None, help="Range, e.g. 0-23 or comma list 0,1,2")
    parser.add_argument("--dry-run",    action="store_true", help="Connect and show models only")
    args = parser.parse_args()

    global COMFYUI_URL
    COMFYUI_URL = args.url

    print("=" * 60)
    print("Phase 7 — ComfyUI Post-Processing")
    print(f"  Host       : {COMFYUI_URL}")
    print(f"  Denoise    : {args.denoise}")
    print(f"  CN Strength: {args.strength}")
    print(f"  Steps / CFG: {args.steps} / {args.cfg}")
    print(f"  Seed       : {args.seed}  (fixed for temporal consistency)")
    print("=" * 60)

    # 1. Verify ComfyUI is running
    print("\n[1] Checking ComfyUI...")
    if not check_server():
        sys.exit(1)

    # 2. Query available models
    print("\n[2] Querying available models...")
    try:
        checkpoints, controlnets = get_models()
    except Exception as e:
        sys.exit(f"  ERROR fetching model list: {e}")

    print(f"  Checkpoints ({len(checkpoints)}):")
    for c in checkpoints[:10]:
        print(f"    {c}")
    if len(checkpoints) > 10:
        print(f"    ... and {len(checkpoints)-10} more")

    print(f"  ControlNets ({len(controlnets)}):")
    for c in controlnets:
        print(f"    {c}")

    # 3. Select checkpoint and ControlNet
    checkpoint = args.checkpoint or (checkpoints[0] if checkpoints else None)
    controlnet = args.controlnet or pick_depth_controlnet(controlnets)

    if not checkpoint:
        sys.exit("  ERROR: No checkpoints found on ComfyUI.")
    if not controlnet:
        sys.exit("  ERROR: No ControlNets found. Install a depth ControlNet model.")

    print(f"\n[3] Model selection:")
    print(f"  Checkpoint : {checkpoint}")
    print(f"  ControlNet : {controlnet}")

    if args.dry_run:
        print("\n  --dry-run set. Exiting without processing.")
        return

    # 4. Build frame list
    beauty_files = sorted(PNG_DIR.glob("frame_????.png"))
    depth_files  = sorted(DEPTH_DIR.glob("depth_????.png"))

    # Map frame numbers
    beauty_map = {int(p.stem.split("_")[1]): p for p in beauty_files}
    depth_map  = {int(p.stem.split("_")[1]): p for p in depth_files}
    all_frames = sorted(set(beauty_map) & set(depth_map))

    # Apply --frames filter
    if args.frames:
        if "-" in args.frames:
            lo, hi = args.frames.split("-")
            all_frames = [f for f in all_frames if int(lo) <= f <= int(hi)]
        else:
            wanted = set(int(x) for x in args.frames.split(","))
            all_frames = [f for f in all_frames if f in wanted]

    print(f"\n[4] Frames to process: {len(all_frames)}")
    if not all_frames:
        sys.exit("  No frames matched. Check png/ and depth/ directories.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 5. Process frames in parallel batches
    print(f"\n[5] Processing {len(all_frames)} frames (batch={args.batch})...")
    done = skipped = errors = 0
    failed_frames = []

    def submit(frame_num):
        return process_frame(
            frame_num,
            str(beauty_map[frame_num]),
            str(depth_map[frame_num]),
            checkpoint, controlnet,
            args.denoise, args.strength,
            args.steps, args.cfg, args.seed
        )

    iter_frames = tqdm(all_frames, unit="frame") if HAS_TQDM else all_frames

    with ThreadPoolExecutor(max_workers=args.batch) as pool:
        futures = {pool.submit(submit, fn): fn for fn in all_frames}
        for future in as_completed(futures):
            fn = futures[future]
            try:
                label, path, status = future.result()
                if status == "skipped":
                    skipped += 1
                else:
                    done += 1
                if not HAS_TQDM:
                    print(f"  [{status}] frame_{label}.png")
                elif HAS_TQDM:
                    iter_frames.update(1)
                    iter_frames.set_postfix(done=done, skip=skipped, err=errors)
            except Exception as e:
                errors += 1
                failed_frames.append(fn)
                print(f"\n  ERROR frame {fn:04d}: {e}")

    if HAS_TQDM:
        iter_frames.close()

    print(f"\n  Results: done={done}  skipped={skipped}  errors={errors}")
    if failed_frames:
        print(f"  Failed frames: {failed_frames}")

    # 6. Verify output completeness
    out_files = sorted(OUT_DIR.glob("frame_????.png"))
    print(f"\n[6] Output check: {len(out_files)} / {len(all_frames)} frames in {OUT_DIR}")
    if len(out_files) < len(all_frames):
        missing = sorted(set(all_frames) - {int(p.stem.split("_")[1]) for p in out_files})
        print(f"  WARNING: missing frames: {missing[:20]}{'...' if len(missing)>20 else ''}")

    # 7. Encode MP4
    print("\n[7] Encoding ocean_view_ai.mp4...")
    out_mp4 = BASE / "ocean_view_ai.mp4"
    try:
        encode_mp4(OUT_DIR, out_mp4)
        print(f"  Done: {out_mp4}")
    except Exception as e:
        print(f"  WARNING: ffmpeg encode failed: {e}")
        print(f"  Enhanced frames are in {OUT_DIR}")

    print("\n" + "=" * 60)
    print("Phase 7 complete.")
    print(f"  Enhanced frames : {OUT_DIR}")
    print(f"  Final video     : {out_mp4}")
    print("=" * 60)


if __name__ == "__main__":
    main()
