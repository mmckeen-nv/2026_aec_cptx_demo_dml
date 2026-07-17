"""Run the VP Studio hero render through local ComfyUI's HTTP API.

This is deliberately a bounded, geometry-preserving two-stage workflow. It
first uses SDXL with depth ControlNet, then refines that accepted image with
FLUX.2 Klein reference conditioning. It does not launch ComfyUI, install
models, or invent a graph at demo time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
from pathlib import Path

import requests
from PIL import Image, ImageStat


DEFAULT_URL = "http://127.0.0.1:8188"
DEFAULT_CHECKPOINT = "sd_xl_base_1.0.safetensors"
DEFAULT_CONTROLNET = "controlnet-depth-sdxl-1.0\\diffusion_pytorch_model.safetensors"
DEFAULT_FLUX_MODEL = "flux-2-klein-base-4b-fp8.safetensors"
DEFAULT_FLUX_CLIP = "qwen_3_4b.safetensors"
DEFAULT_FLUX_VAE = "flux2-vae.safetensors"
SDXL_REQUIRED_NODES = {
    "CheckpointLoaderSimple",
    "CLIPTextEncode",
    "LoadImage",
    "ImageScale",
    "VAEEncode",
    "DepthAnythingV2Preprocessor",
    "ControlNetLoader",
    "ControlNetApplyAdvanced",
    "KSampler",
    "VAEDecode",
    "SaveImage",
}
FLUX_REQUIRED_NODES = {
    "UNETLoader",
    "CLIPLoader",
    "VAELoader",
    "CLIPTextEncode",
    "LoadImage",
    "ImageScale",
    "VAEEncode",
    "ReferenceLatent",
    "EmptyFlux2LatentImage",
    "RandomNoise",
    "Flux2Scheduler",
    "KSamplerSelect",
    "CFGGuider",
    "SamplerCustomAdvanced",
    "VAEDecode",
    "SaveImage",
}

POSITIVE = (
    "photorealistic virtual production studio interior, smooth curved LED volume, "
    "professional cinema cameras, production chairs and workstations, overhead truss, "
    "cinematic architectural visualization, realistic materials, motivated studio lighting, "
    "preserve the exact camera, building, room, equipment, and LED wall layout"
)
NEGATIVE = (
    "changed geometry, changed composition, added or removed objects, duplicate objects, "
    "missing parts, warped forms, altered openings, floating objects, text, watermark, "
    "cartoon, sketch, blurry, low quality"
)


def api(url: str, method: str, endpoint: str, **kwargs):
    kwargs.setdefault("timeout", 30)
    response = requests.request(method, f"{url}{endpoint}", **kwargs)
    response.raise_for_status()
    return response


def inventory(url: str) -> dict:
    api(url, "GET", "/system_stats", timeout=5)
    return api(url, "GET", "/object_info", timeout=30).json()


def choices(info: dict, node: str, field: str) -> list[str]:
    return info.get(node, {}).get("input", {}).get("required", {}).get(field, [[]])[0]


def scaled_size(source: Path, max_dimension: int) -> tuple[int, int]:
    with Image.open(source) as image:
        width, height = image.size
    scale = min(1.0, max_dimension / max(width, height))
    width = max(64, int(width * scale) // 64 * 64)
    height = max(64, int(height * scale) // 64 * 64)
    return width, height


def source_quality(source: Path) -> dict:
    """Reject empty or catastrophically misframed Blender source renders."""
    with Image.open(source) as loaded:
        image = loaded.convert("RGB")
    grayscale = image.convert("L")
    contrast = float(ImageStat.Stat(grayscale).stddev[0])
    pixels = image.load()
    width, height = image.size
    border = []
    for x in range(width):
        border.extend((pixels[x, 0], pixels[x, height - 1]))
    for y in range(height):
        border.extend((pixels[0, y], pixels[width - 1, y]))
    background = tuple(
        sorted(pixel[channel] for pixel in border)[len(border) // 2]
        for channel in range(3)
    )
    foreground = 0
    pixel_data = (
        image.get_flattened_data()
        if hasattr(image, "get_flattened_data")
        else image.getdata()
    )
    for pixel in pixel_data:
        if max(abs(pixel[channel] - background[channel]) for channel in range(3)) > 12:
            foreground += 1
    foreground_fraction = foreground / float(width * height)
    result = {
        "contrast": round(contrast, 3),
        "foreground_fraction": round(foreground_fraction, 5),
    }
    if contrast < 6.0 or foreground_fraction < 0.03:
        raise SystemExit(
            "COMFY_SOURCE_FAIL Blender render failed composition gate "
            "contrast={contrast:.3f} foreground_fraction={foreground_fraction:.5f}".format(
                **result
            )
        )
    return result


def upload(url: str, source: Path) -> str:
    with source.open("rb") as stream:
        response = api(
            url,
            "POST",
            "/upload/image",
            files={"image": (source.name, stream, "image/png")},
            data={"subfolder": "vp_studio", "type": "input", "overwrite": "true"},
            timeout=60,
        ).json()
    subfolder = response.get("subfolder", "")
    return f"{subfolder}/{response['name']}" if subfolder else response["name"]


def workflow(image_ref: str, checkpoint: str, controlnet: str, width: int, height: int,
             seed: int, denoise: float, steps: int, cfg: float,
             positive_prompt: str = POSITIVE, negative_prompt: str = NEGATIVE) -> dict:
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": positive_prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt, "clip": ["1", 1]}},
        "4": {"class_type": "LoadImage", "inputs": {"image": image_ref}},
        "5": {"class_type": "ImageScale", "inputs": {
            "image": ["4", 0], "upscale_method": "lanczos", "width": width,
            "height": height, "crop": "disabled"}},
        "6": {"class_type": "VAEEncode", "inputs": {"pixels": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "DepthAnythingV2Preprocessor", "inputs": {"image": ["5", 0]}},
        "8": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": controlnet}},
        "9": {"class_type": "ControlNetApplyAdvanced", "inputs": {
            "positive": ["2", 0], "negative": ["3", 0], "control_net": ["8", 0],
            "image": ["7", 0], "strength": 0.72, "start_percent": 0.0,
            "end_percent": 0.82}},
        "10": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "positive": ["9", 0], "negative": ["9", 1],
            "latent_image": ["6", 0], "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": denoise}},
        "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["1", 2]}},
        "12": {"class_type": "SaveImage", "inputs": {
            "images": ["11", 0], "filename_prefix": "vp_studio/vp_studio_stylized"}},
    }


def flux_workflow(image_ref: str, model: str, clip: str, vae: str,
                  width: int, height: int, seed: int, steps: int,
                  cfg: float, positive_prompt: str = POSITIVE) -> dict:
    """Build the fixed FLUX.2 Klein image-edit refinement graph."""
    refinement_prompt = (
        positive_prompt.rstrip(" .")
        + ". Refine this exact supplied image with photorealistic materials and lighting. "
        "Keep the camera, primary modeled subject, scene geometry, object count, object "
        "positions, silhouettes, proportions, and clearances unchanged."
    )
    return {
        "101": {"class_type": "UNETLoader", "inputs": {
            "unet_name": model, "weight_dtype": "default"}},
        "102": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": clip, "type": "flux2", "device": "default"}},
        "103": {"class_type": "VAELoader", "inputs": {"vae_name": vae}},
        "104": {"class_type": "CLIPTextEncode", "inputs": {
            "text": refinement_prompt, "clip": ["102", 0]}},
        "105": {"class_type": "CLIPTextEncode", "inputs": {
            "text": "", "clip": ["102", 0]}},
        "106": {"class_type": "LoadImage", "inputs": {"image": image_ref}},
        "107": {"class_type": "ImageScale", "inputs": {
            "image": ["106", 0], "upscale_method": "lanczos", "width": width,
            "height": height, "crop": "disabled"}},
        "108": {"class_type": "VAEEncode", "inputs": {
            "pixels": ["107", 0], "vae": ["103", 0]}},
        "109": {"class_type": "ReferenceLatent", "inputs": {
            "conditioning": ["104", 0], "latent": ["108", 0]}},
        "110": {"class_type": "ReferenceLatent", "inputs": {
            "conditioning": ["105", 0], "latent": ["108", 0]}},
        "111": {"class_type": "EmptyFlux2LatentImage", "inputs": {
            "width": width, "height": height, "batch_size": 1}},
        "112": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "113": {"class_type": "CFGGuider", "inputs": {
            "model": ["101", 0], "positive": ["109", 0],
            "negative": ["110", 0], "cfg": cfg}},
        "114": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "115": {"class_type": "Flux2Scheduler", "inputs": {
            "steps": steps, "width": width, "height": height}},
        "116": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["112", 0], "guider": ["113", 0],
            "sampler": ["114", 0], "sigmas": ["115", 0],
            "latent_image": ["111", 0]}},
        "117": {"class_type": "VAEDecode", "inputs": {
            "samples": ["116", 0], "vae": ["103", 0]}},
        "118": {"class_type": "SaveImage", "inputs": {
            "images": ["117", 0], "filename_prefix": "vp_studio/vp_studio_flux_refined"}},
    }


def wait_for_output(url: str, prompt_id: str, timeout: int) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        history = api(url, "GET", f"/history/{prompt_id}", timeout=15).json()
        entry = history.get(prompt_id)
        if not entry:
            time.sleep(1.5)
            continue
        status = entry.get("status", {})
        if status.get("status_str") == "error":
            raise RuntimeError(json.dumps(status.get("messages", []), indent=2))
        for node_output in entry.get("outputs", {}).values():
            images = node_output.get("images", [])
            if images:
                return images[0]
        if status.get("completed"):
            raise RuntimeError("ComfyUI completed without an image output")
        time.sleep(1.5)
    raise TimeoutError(f"ComfyUI prompt {prompt_id} exceeded {timeout}s")


def download(url: str, image_info: dict, destination: Path) -> None:
    query = urllib.parse.urlencode({
        "filename": image_info["filename"],
        "subfolder": image_info.get("subfolder", ""),
        "type": image_info.get("type", "output"),
    })
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(api(url, "GET", f"/view?{query}", timeout=60).content)


def main() -> int:
    here = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=here / "renders" / "vp_studio_hero_preview.png")
    parser.add_argument("--output", type=Path, default=here / "comfy_enhanced" / "vp_studio_stylized.png")
    parser.add_argument("--intermediate", type=Path, default=here / "comfy_enhanced" / "vp_studio_sdxl.png")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    parser.add_argument("--controlnet", default=DEFAULT_CONTROLNET)
    parser.add_argument("--flux-model", default=DEFAULT_FLUX_MODEL)
    parser.add_argument("--flux-clip", default=DEFAULT_FLUX_CLIP)
    parser.add_argument("--flux-vae", default=DEFAULT_FLUX_VAE)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--denoise", type=float, default=0.28)
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--cfg", type=float, default=6.0)
    parser.add_argument("--flux-steps", type=int, default=20)
    parser.add_argument("--flux-cfg", type=float, default=5.0)
    parser.add_argument("--max-dimension", type=int, default=1216)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument(
        "--prompt-file", type=Path,
        default=here / "user_prompts" / "comfy_style_prompt.txt",
        help="User-editable positive prompt file; used unless --prompt is supplied.",
    )
    parser.add_argument("--prompt", help="Positive prompt override for manual runs.")
    parser.add_argument("--negative-prompt", default=NEGATIVE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--sdxl-only", action="store_true",
        help="Operator recovery path: stop after the depth-controlled SDXL intermediate.",
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    intermediate = args.intermediate.expanduser().resolve()
    prompt_file = args.prompt_file.expanduser().resolve()
    if args.prompt is not None:
        positive_prompt = args.prompt.strip()
        prompt_source = "--prompt"
    elif prompt_file.is_file():
        positive_prompt = prompt_file.read_text(encoding="utf-8").strip()
        prompt_source = str(prompt_file)
    else:
        positive_prompt = POSITIVE
        prompt_source = "built-in default"
    negative_prompt = args.negative_prompt.strip()
    if not positive_prompt:
        raise SystemExit("COMFY_PREFLIGHT_FAIL positive prompt is empty")
    if not negative_prompt:
        raise SystemExit("COMFY_PREFLIGHT_FAIL negative prompt is empty")
    prompt_sha256 = hashlib.sha256(positive_prompt.encode("utf-8")).hexdigest()[:12]
    if not source.is_file() or source.stat().st_size == 0:
        raise SystemExit(f"COMFY_SOURCE_FAIL missing or empty source: {source}")
    quality = source_quality(source)

    try:
        info = inventory(args.url)
    except requests.RequestException as exc:
        raise SystemExit(f"COMFY_PREFLIGHT_FAIL endpoint unavailable: {args.url} ({exc})") from exc
    required_nodes = SDXL_REQUIRED_NODES | (set() if args.sdxl_only else FLUX_REQUIRED_NODES)
    missing = sorted(required_nodes - set(info))
    if missing:
        raise SystemExit(f"COMFY_PREFLIGHT_FAIL missing nodes: {', '.join(missing)}")
    if args.checkpoint not in choices(info, "CheckpointLoaderSimple", "ckpt_name"):
        raise SystemExit(f"COMFY_PREFLIGHT_FAIL checkpoint unavailable: {args.checkpoint}")
    if args.controlnet not in choices(info, "ControlNetLoader", "control_net_name"):
        raise SystemExit(f"COMFY_PREFLIGHT_FAIL ControlNet unavailable: {args.controlnet}")
    if not args.sdxl_only:
        if args.flux_model not in choices(info, "UNETLoader", "unet_name"):
            raise SystemExit(f"COMFY_PREFLIGHT_FAIL FLUX model unavailable: {args.flux_model}")
        if args.flux_clip not in choices(info, "CLIPLoader", "clip_name"):
            raise SystemExit(f"COMFY_PREFLIGHT_FAIL FLUX text encoder unavailable: {args.flux_clip}")
        if args.flux_vae not in choices(info, "VAELoader", "vae_name"):
            raise SystemExit(f"COMFY_PREFLIGHT_FAIL FLUX VAE unavailable: {args.flux_vae}")

    width, height = scaled_size(source, args.max_dimension)
    print(f"COMFY_PREFLIGHT_PASS source={source} size={width}x{height} "
          f"contrast={quality['contrast']} foreground_fraction={quality['foreground_fraction']} "
          f"checkpoint={args.checkpoint} controlnet={args.controlnet} "
          f"flux={'disabled' if args.sdxl_only else args.flux_model} "
          f"prompt_source={prompt_source} prompt_sha256={prompt_sha256}")
    if args.dry_run:
        return 0

    try:
        image_ref = upload(args.url, source)
        graph = workflow(image_ref, args.checkpoint, args.controlnet, width, height,
                         args.seed, args.denoise, args.steps, args.cfg,
                         positive_prompt, negative_prompt)
        queued = api(args.url, "POST", "/prompt", json={"prompt": graph, "client_id": "vp-studio-demo-sdxl"}).json()
    except requests.RequestException as exc:
        raise SystemExit(f"COMFY_QUEUE_FAIL endpoint request failed: {exc}") from exc
    if queued.get("node_errors"):
        raise SystemExit(f"COMFY_QUEUE_FAIL {json.dumps(queued['node_errors'], indent=2)}")
    prompt_id = queued["prompt_id"]
    print(f"COMFY_SDXL_QUEUED prompt_id={prompt_id}")
    try:
        image_info = wait_for_output(args.url, prompt_id, args.timeout)
        download(args.url, image_info, intermediate)
    except (requests.RequestException, RuntimeError, TimeoutError) as exc:
        raise SystemExit(f"COMFY_OUTPUT_FAIL prompt_id={prompt_id} error={exc}") from exc
    print(f"COMFY_SDXL_OUTPUT_PASS prompt_id={prompt_id} output={intermediate} "
          f"bytes={intermediate.stat().st_size} seed={args.seed} denoise={args.denoise}")
    if args.sdxl_only:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(intermediate.read_bytes())
        print(f"COMFY_OUTPUT_PASS stage=sdxl output={output} bytes={output.stat().st_size} "
              f"prompt_sha256={prompt_sha256}")
        return 0

    try:
        flux_image_ref = upload(args.url, intermediate)
        flux_graph = flux_workflow(
            flux_image_ref, args.flux_model, args.flux_clip, args.flux_vae,
            width, height, args.seed, args.flux_steps, args.flux_cfg, positive_prompt,
        )
        flux_queued = api(
            args.url, "POST", "/prompt",
            json={"prompt": flux_graph, "client_id": "vp-studio-demo-flux"},
        ).json()
    except requests.RequestException as exc:
        raise SystemExit(f"COMFY_FLUX_QUEUE_FAIL endpoint request failed: {exc}") from exc
    if flux_queued.get("node_errors"):
        raise SystemExit(f"COMFY_FLUX_QUEUE_FAIL {json.dumps(flux_queued['node_errors'], indent=2)}")
    flux_prompt_id = flux_queued["prompt_id"]
    print(f"COMFY_FLUX_QUEUED prompt_id={flux_prompt_id}")
    try:
        flux_image_info = wait_for_output(args.url, flux_prompt_id, args.timeout)
        download(args.url, flux_image_info, output)
    except (requests.RequestException, RuntimeError, TimeoutError) as exc:
        raise SystemExit(f"COMFY_FLUX_OUTPUT_FAIL prompt_id={flux_prompt_id} error={exc}") from exc
    print(f"COMFY_FLUX_OUTPUT_PASS prompt_id={flux_prompt_id} output={output} "
          f"bytes={output.stat().st_size} model={args.flux_model} steps={args.flux_steps} cfg={args.flux_cfg}")
    print(f"COMFY_OUTPUT_PASS stage=sdxl+flux output={output} bytes={output.stat().st_size} "
          f"seed={args.seed} sdxl_denoise={args.denoise} prompt_sha256={prompt_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
