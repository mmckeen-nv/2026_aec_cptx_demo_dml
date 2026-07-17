"""BAC Teapot house HERO defaults for the tested SDXL -> FLUX helper."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    root = Path(os.environ["AEC_DEMO_ROOT"]).resolve()
    marker = root / "demos" / "teapot" / "work" / "active_render_lane.txt"
    lane = marker.read_text(encoding="utf-8").splitlines()[0].strip() if marker.is_file() else "missing"
    if lane != "bac_hero":
        raise SystemExit(
            "COMFY_SOURCE_FAIL active_lane={} required=bac_hero; render BAC HERO before stylizing it".format(lane)
        )
    helper = root / "demos" / "virtual_production_studio" / "skills" / "comfyui_vp_stylize.py"
    if not helper.is_file():
        raise SystemExit("COMFY_PREFLIGHT_FAIL missing tested helper: " + str(helper))
    hero = root / "demos" / "teapot" / "hero"
    defaults = [
        str(helper),
        "--source", str(hero / "renders" / "bac_teapot_hero_source.png"),
        "--output", str(hero / "comfy_output" / "bac_teapot_hero_stylized.png"),
        "--intermediate", str(hero / "comfy_output" / "bac_teapot_hero_sdxl.png"),
        "--prompt-file", str(hero / "user_prompts" / "comfy_style_prompt.txt"),
    ]
    sys.argv = defaults + sys.argv[1:]
    runpy.run_path(str(helper), run_name="__main__")


if __name__ == "__main__":
    main()
