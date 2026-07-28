"""Run one Blender beauty frame directly through FLUX.2 reference conditioning."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from PIL import Image, PngImagePlugin


DEFAULT_URL = "http://127.0.0.1:8188"
DEFAULT_MODEL = "flux-2-klein-base-4b-fp8.safetensors"
DEFAULT_CLIP = "qwen_3_4b.safetensors"
DEFAULT_VAE = "flux2-vae.safetensors"
ARCHITECTURE_GEOMETRY_LOCK = (
    "Geometry lock: 'Cliff House' is only the project name. Keep the supplied image "
    "pixel-registered: identical camera, framing, house massing, roof plates, balconies, "
    "curtain-wall openings, railings, patio, rectangular infinity pool, object positions, "
    "architectural silhouettes, proportions, and clearances. The complete rectangular pool "
    "water surface and perimeter remain visible. The absent/neutral Blender background and "
    "removed SITE_TERRAIN are an intentional environment mask: replace only that unmodeled "
    "environment with a photorealistic rugged coastal cliff, native scrub, ocean, distant "
    "horizon, and sky. Never move, resize, occlude, or redesign the house, patio, or pool."
)
DEFAULT_PROMPT = (
    "Photorealistic architecture-magazine visualization of the exact supplied "
    "modernist three-level coastal house. Preserve the supplied camera and all "
    "modeled geometry, positions, proportions, and clearances. Refine materials "
    "only: warm white ashlar stone with subtle joints, smooth exposed-concrete "
    "slabs and soffits, bronze-framed lightly tinted glazing, slender dark steel "
    "cable railings, a near-black infinity pool with a thin bronze overflow edge, "
    "a light-grey patio and neutral late-afternoon ocean-view lighting. Replace the unmodeled "
    "surroundings with a rugged coastal cliff descending to the ocean, sparse native "
    "vegetation, distant water, and a clear horizon. No people, cars, text, or watermark. "
    + ARCHITECTURE_GEOMETRY_LOCK
)


def load_flux_helper(repo_root: Path):
    helper_path = (
        repo_root
        / "demos"
        / "virtual_production_studio"
        / "skills"
        / "comfyui_vp_stylize.py"
    )
    spec = importlib.util.spec_from_file_location("aec_flux2_helper", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load FLUX.2 helper: {helper_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--clip", default=DEFAULT_CLIP)
    parser.add_argument("--vae", default=DEFAULT_VAE)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--cfg", type=float, default=5.0)
    parser.add_argument(
        "--metadata-output",
        type=Path,
        help="JSON provenance sidecar; defaults beside the output PNG.",
    )
    parser.add_argument(
        "--max-generation-dimension",
        type=int,
        default=1536,
        help="Generate at or below this size, then upscale to the source dimensions.",
    )
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    metadata_output = (
        args.metadata_output.expanduser().resolve()
        if args.metadata_output is not None
        else output.with_suffix(".comfy.json")
    )
    if not source.is_file() or source.stat().st_size == 0:
        raise SystemExit(f"COMFY_SOURCE_FAIL missing or empty source: {source}")

    prompt = args.prompt.strip()
    prompt_source = "built-in"
    prompt_file_sha256 = None
    if args.prompt_file is not None:
        prompt_path = args.prompt_file.expanduser().resolve()
        if not prompt_path.is_file():
            raise SystemExit(f"COMFY_PREFLIGHT_FAIL prompt file missing: {prompt_path}")
        prompt_bytes = prompt_path.read_bytes()
        prompt_file_sha256 = hashlib.sha256(prompt_bytes).hexdigest()
        prompt = prompt_bytes.decode("utf-8").strip()
        prompt_source = str(prompt_path)
    if not prompt:
        raise SystemExit("COMFY_PREFLIGHT_FAIL prompt is empty")
    source_prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if ARCHITECTURE_GEOMETRY_LOCK not in prompt:
        prompt = prompt.rstrip(" .") + ". " + ARCHITECTURE_GEOMETRY_LOCK

    helper = load_flux_helper(repo_root)
    try:
        info = helper.inventory(args.url)
    except Exception as exc:
        raise SystemExit(f"COMFY_PREFLIGHT_FAIL endpoint unavailable: {exc}") from exc

    missing_nodes = sorted(helper.FLUX_REQUIRED_NODES - set(info))
    if missing_nodes:
        raise SystemExit(f"COMFY_PREFLIGHT_FAIL missing nodes: {missing_nodes}")
    if args.model not in helper.choices(info, "UNETLoader", "unet_name"):
        raise SystemExit(f"COMFY_PREFLIGHT_FAIL FLUX model unavailable: {args.model}")
    if args.clip not in helper.choices(info, "CLIPLoader", "clip_name"):
        raise SystemExit(f"COMFY_PREFLIGHT_FAIL FLUX text encoder unavailable: {args.clip}")
    if args.vae not in helper.choices(info, "VAELoader", "vae_name"):
        raise SystemExit(f"COMFY_PREFLIGHT_FAIL FLUX VAE unavailable: {args.vae}")

    quality = helper.source_quality(source)
    with Image.open(source) as loaded:
        width, height = loaded.size
    generation_width, generation_height = helper.scaled_size(
        source, args.max_generation_dimension
    )
    prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
    preflight = {
        "source": str(source),
        "dimensions": [width, height],
        "generation_dimensions": [generation_width, generation_height],
        "quality": quality,
        "model": args.model,
        "clip": args.clip,
        "vae": args.vae,
        "steps": args.steps,
        "cfg": args.cfg,
        "seed": args.seed,
        "prompt_sha256": prompt_sha256,
        "prompt_source": prompt_source,
        "prompt_file_sha256": prompt_file_sha256,
        "source_prompt_sha256": source_prompt_sha256,
        "architecture_geometry_lock": True,
        "generative_environment": "coastal_cliff_ocean",
    }
    print("COMFY_FLUX2_PREFLIGHT_PASS " + json.dumps(preflight))
    if args.dry_run:
        return 0

    image_ref = helper.upload(args.url, source)
    workflow = helper.flux_workflow(
        image_ref,
        args.model,
        args.clip,
        args.vae,
        generation_width,
        generation_height,
        args.seed,
        args.steps,
        args.cfg,
        prompt,
    )
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    started = time.monotonic()
    try:
        queued = helper.api(
            args.url,
            "POST",
            "/prompt",
            json={"prompt": workflow, "client_id": "aec-flux2-direct"},
            timeout=30,
        ).json()
    except Exception as exc:
        raise SystemExit(f"COMFY_FLUX2_QUEUE_FAIL endpoint request failed: {exc}") from exc
    if queued.get("error") or queued.get("node_errors"):
        raise SystemExit("COMFY_FLUX2_QUEUE_FAIL " + json.dumps(queued, indent=2))

    prompt_id = queued["prompt_id"]
    try:
        image_info = helper.wait_for_output(args.url, prompt_id, args.timeout)
    except Exception as exc:
        raise SystemExit(f"COMFY_FLUX2_OUTPUT_FAIL prompt_id={prompt_id}: {exc}") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    helper.download(args.url, image_info, output)
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit(f"COMFY_FLUX2_OUTPUT_FAIL missing output: {output}")
    with Image.open(output) as loaded:
        generated_size = loaded.size
        final_image = loaded.convert("RGB")
        if generated_size != (width, height):
            final_image = final_image.resize(
                (width, height), Image.Resampling.LANCZOS
            )
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("Software", "ComfyUI FLUX.2 direct")
        pnginfo.add_text("Model", args.model)
        pnginfo.add_text("TextEncoder", args.clip)
        pnginfo.add_text("VAE", args.vae)
        pnginfo.add_text("PromptSource", prompt_source)
        if prompt_file_sha256 is not None:
            pnginfo.add_text("PromptFileSHA256", prompt_file_sha256)
        pnginfo.add_text("SourcePromptSHA256", source_prompt_sha256)
        pnginfo.add_text("PromptSHA256", prompt_sha256)
        pnginfo.add_text("PromptID", prompt_id)
        pnginfo.add_text("Seed", str(args.seed))
        pnginfo.add_text("Steps", str(args.steps))
        pnginfo.add_text("CFG", str(args.cfg))
        final_image.save(output, pnginfo=pnginfo)
    with Image.open(output) as loaded:
        output_size = loaded.size
    if output_size != (width, height):
        raise SystemExit(
            f"COMFY_FLUX2_OUTPUT_FAIL expected={width}x{height} actual={output_size}"
        )

    output_sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    provenance = {
        "stage": "flux2-direct",
        "prompt_id": prompt_id,
        "source": str(source),
        "source_sha256": source_sha256,
        "output": str(output),
        "output_sha256": output_sha256,
        "dimensions": list(output_size),
        "generation_dimensions": list(generated_size),
        "model": args.model,
        "clip": args.clip,
        "vae": args.vae,
        "seed": args.seed,
        "steps": args.steps,
        "cfg": args.cfg,
        "prompt_source": prompt_source,
        "prompt_file_sha256": prompt_file_sha256,
        "source_prompt_sha256": source_prompt_sha256,
        "prompt_sha256": prompt_sha256,
        "prompt": prompt,
        "effective_prompt": workflow["104"]["inputs"]["text"],
        "comfy_output": image_info,
    }
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(
        "COMFY_OUTPUT_PASS stage=flux2-direct "
        + json.dumps(
            {
                "prompt_id": prompt_id,
                "output": str(output),
                "bytes": output.stat().st_size,
                "dimensions": list(output_size),
                "generation_dimensions": list(generated_size),
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "prompt_sha256": prompt_sha256,
                "prompt_source": prompt_source,
                "prompt_file_sha256": prompt_file_sha256,
                "source_prompt_sha256": source_prompt_sha256,
                "metadata": str(metadata_output),
                "output_sha256": output_sha256,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
