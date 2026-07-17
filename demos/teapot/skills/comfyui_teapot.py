"""BAC Teapot defaults for the tested SDXL -> FLUX ComfyUI helper."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    root = Path(os.environ["AEC_DEMO_ROOT"]).resolve()
    marker = root / "demos" / "teapot" / "work" / "active_render_lane.txt"
    lane = marker.read_text(encoding="utf-8").splitlines()[0].strip() if marker.is_file() else "missing"
    if lane != "teapot":
        raise SystemExit(
            "COMFY_SOURCE_FAIL active_lane={} required=teapot; use comfyui_bac_hero.py for BAC HERO".format(lane)
        )
    helper = root / "demos" / "virtual_production_studio" / "skills" / "comfyui_vp_stylize.py"
    if not helper.is_file():
        raise SystemExit("COMFY_PREFLIGHT_FAIL missing tested helper: " + str(helper))
    demo = root / "demos" / "teapot"
    defaults = [
        str(helper),
        "--source", str(demo / "renders" / "teapot_preview.png"),
        "--output", str(demo / "comfy_output" / "teapot_stylized.png"),
        "--intermediate", str(demo / "comfy_output" / "teapot_sdxl.png"),
        "--prompt-file", str(demo / "user_prompts" / "comfy_style_prompt.txt"),
    ]
    sys.argv = defaults + sys.argv[1:]
    runpy.run_path(str(helper), run_name="__main__")


if __name__ == "__main__":
    main()
