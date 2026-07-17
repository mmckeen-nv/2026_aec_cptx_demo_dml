"""BAC Teapot style-presets wrapper for the tested SDXL -> FLUX helper."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path


STYLE_PROMPTS = {
    "product": "comfy_style_prompt.txt",
    "neon_noir": "comfy_styles/neon_noir.txt",
    "botanical_porcelain": "comfy_styles/botanical_porcelain.txt",
    "molten_metal": "comfy_styles/molten_metal.txt",
}


def main() -> None:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--style", choices=sorted(STYLE_PROMPTS), default="product")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(os.environ["AEC_DEMO_ROOT"]).resolve()
    marker = root / "demos" / "teapot" / "work" / "active_render_lane.txt"
    lines = marker.read_text(encoding="utf-8").splitlines() if marker.is_file() else []
    lane = lines[0].strip() if lines else "missing"
    if lane != "teapot":
        raise SystemExit(
            "COMFY_SOURCE_FAIL active_lane={} required=teapot; use comfyui_bac_hero.py for BAC HERO".format(lane)
        )
    helper = root / "demos" / "virtual_production_studio" / "skills" / "comfyui_vp_stylize.py"
    if not helper.is_file():
        raise SystemExit("COMFY_PREFLIGHT_FAIL missing tested helper: " + str(helper))
    demo = root / "demos" / "teapot"
    render_root = (demo / "renders").resolve()
    source = Path(lines[1].strip()).resolve() if len(lines) > 1 and lines[1].strip() else None
    if source is None or not source.is_file() or source.suffix.lower() != ".png" or render_root not in source.parents:
        raise SystemExit("COMFY_SOURCE_FAIL marker must name an existing teapot PNG under {}: {}".format(render_root, source))
    source_key = "".join(char if char.isalnum() or char in "-_" else "_" for char in source.stem)
    prompt_file = demo / "user_prompts" / STYLE_PROMPTS[args.style]
    output_key = "{}_{}".format(source_key, args.style)
    print("COMFY_SOURCE_PASS lane=teapot style={} source={}".format(args.style, source))
    generic_args = [
        str(helper),
        "--source", str(source),
        "--output", str(demo / "comfy_output" / (output_key + "_stylized.png")),
        "--intermediate", str(demo / "comfy_output" / (output_key + "_sdxl.png")),
        "--prompt-file", str(prompt_file),
    ]
    if args.dry_run:
        generic_args.append("--dry-run")
    sys.argv = generic_args
    runpy.run_path(str(helper), run_name="__main__")


if __name__ == "__main__":
    main()
