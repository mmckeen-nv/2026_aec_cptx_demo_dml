"""BAC Teapot house HERO defaults for the tested SDXL -> FLUX helper."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    root = Path(os.environ["AEC_DEMO_ROOT"]).resolve()
    marker = root / "demos" / "teapot" / "work" / "active_render_lane.txt"
    marker_lines = marker.read_text(encoding="utf-8").splitlines() if marker.is_file() else []
    lane = marker_lines[0].strip() if marker_lines else "missing"
    if lane != "bac_hero":
        raise SystemExit(
            "COMFY_SOURCE_FAIL active_lane={} required=bac_hero; render BAC HERO before stylizing it".format(lane)
        )
    helper = root / "demos" / "virtual_production_studio" / "skills" / "comfyui_vp_stylize.py"
    if not helper.is_file():
        raise SystemExit("COMFY_PREFLIGHT_FAIL missing tested helper: " + str(helper))
    hero = root / "demos" / "teapot" / "hero"
    render_root = (hero / "renders").resolve()
    source = Path(marker_lines[1].strip()).resolve() if len(marker_lines) > 1 and marker_lines[1].strip() else None
    if source is None or not source.is_file() or source.suffix.lower() != ".png" or render_root not in source.parents:
        raise SystemExit(
            "COMFY_SOURCE_FAIL marker must name an existing PNG under {}: {}".format(render_root, source)
        )
    stage = marker_lines[2].strip() if len(marker_lines) > 2 else "missing"
    stage_files = {
        "base": ("comfy_style_prompt_base.txt", "bac_teapot_hero_base_sdxl.png", "bac_teapot_hero_base_stylized.png", "126"),
        # Seed 314 is visually locked for this exact source/prompt: seed 126
        # changed the circular ring into a second flamingo during FLUX refine.
        "floaties": ("comfy_style_prompt_floaties.txt", "bac_teapot_hero_floaties_sdxl.png", "bac_teapot_hero_floaties_stylized.png", "314"),
        "complete": ("comfy_style_prompt.txt", "bac_teapot_hero_complete_sdxl.png", "bac_teapot_hero_complete_stylized.png", "126"),
    }
    if stage not in stage_files:
        raise SystemExit("COMFY_SOURCE_FAIL unknown BAC HERO stage={!r}; render a validated base/floaties/complete scene".format(stage))
    prompt_name, intermediate_name, output_name, seed = stage_files[stage]
    print("COMFY_SOURCE_PASS lane=bac_hero stage={} source={}".format(stage, source))
    defaults = [
        str(helper),
        "--source", str(source),
        "--output", str(hero / "comfy_output" / output_name),
        "--intermediate", str(hero / "comfy_output" / intermediate_name),
        "--prompt-file", str(hero / "user_prompts" / prompt_name),
        "--seed", seed,
        "--denoise", "0.18",
        "--steps", "28",
        "--flux-steps", "24",
        "--flux-cfg", "3.5",
    ]
    sys.argv = defaults + sys.argv[1:]
    runpy.run_path(str(helper), run_name="__main__")


if __name__ == "__main__":
    main()
