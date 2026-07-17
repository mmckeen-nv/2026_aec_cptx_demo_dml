"""Cliff HERO defaults for the tested SDXL -> FLUX ComfyUI helper."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main():
    root = Path(os.environ["AEC_DEMO_ROOT"]).resolve()
    helper = root / "demos" / "virtual_production_studio" / "skills" / "comfyui_vp_stylize.py"
    if not helper.is_file():
        raise SystemExit("COMFY_PREFLIGHT_FAIL missing tested helper: " + str(helper))
    hero = root / "demos" / "cliff_house" / "hero"
    defaults = [
        str(helper),
        "--source", str(hero / "renders" / "cliff_house_hero_source.png"),
        "--output", str(hero / "comfy_output" / "cliff_house_stylized.png"),
        "--intermediate", str(hero / "comfy_output" / "cliff_house_sdxl.png"),
        "--prompt-file", str(hero / "user_prompts" / "comfy_style_prompt.txt"),
    ]
    sys.argv = defaults + sys.argv[1:]
    runpy.run_path(str(helper), run_name="__main__")


if __name__ == "__main__":
    main()
