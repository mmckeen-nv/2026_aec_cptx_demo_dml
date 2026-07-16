"""Narrow safety and execution rails for the Blender-only BAC Teapot demo."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional


_EXTERNAL_SCRIPT = re.compile(r"(?:[.]py|[.]cs)\b|RunPythonScript|EditPythonScript|RunScript", re.I)
_BLENDER_HOST_EXIT = re.compile(r"\b(?:raise\s+SystemExit|sys[.]exit\s*\(|quit\s*\(|exit\s*\(|bpy[.]ops[.]wm[.]quit_blender\s*\()", re.I)
_CLIFF_COMFY_WRAPPER = re.compile(r"cliff_house[/\\]hero[/\\]skills[/\\]comfyui_cliff_hero[.]py", re.I)
_HERO_MASTER_SAVE = re.compile(r"save_(?:as_)?mainfile[\s\S]{0,500}cliff_house_02_HERO[.]blend", re.I)


def _active():
    return os.environ.get("AEC_DEMO_ID", "").strip().lower() == "teapot-01"


def _block(message):
    return {"action": "block", "message": "BAC Teapot rails: " + message}


def on_pre_llm_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    root = os.environ.get("AEC_DEMO_ROOT", "")
    return {"context": (
        "BAC TEAPOT HARD RAILS: this demo is Blender-only; never call, inspect, start, or repair Rhino. "
        "START GATE: session startup is idle. Do not mutate Blender until the user explicitly asks to build "
        "or start the Utah teapot; reading prompts is not authorization. Repo root is {0}; demo root is "
        "{0}/demos/teapot. Read startup, manifest, skills, and only the "
        "current phase there. Through mcp_blender_execute_blender_code(code=...), load "
        "skills/blender_teapot_interactions.py and call build_canonical_teapot(root, reset_scene=True). "
        "Require the locked SHA-256, CANONICAL_DATA_PASS, and TEAPOT_BUILD_PASS with four objects, "
        "0.300000 m width, and Z=0 before staging. Never use generic run, terminal scripts, external "
        "Python/C#, primitives, proxies, or legacy 3dm. Then call prepare_product_stage and "
        "render_preview. Material requests are open-ended and do not replay the build. If asked for "
        "the HERO house, use {0}/demos/cliff_house/hero/skills/blender_cliff_hero.py through Blender "
        "MCP; source is {0}/demos/cliff_house/hero/cliff_house_02_HERO.blend. Never look under "
        "virtual_production_studio. DML is advisory."
    ).format(root)}


def on_pre_tool_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    tool = str(kwargs.get("tool_name") or "")
    args = kwargs.get("args") if isinstance(kwargs.get("args"), dict) else {}
    if tool.startswith("mcp_rhino_"):
        return _block("Rhino is prohibited because BAC Teapot is Blender-only")
    if tool == "mcp_blender_execute_blender_code":
        code = str(args.get("code") or "")
        if _BLENDER_HOST_EXIT.search(code):
            return _block("never terminate the Blender host; print or return receipts instead of SystemExit/quit")
        if _HERO_MASTER_SAVE.search(code):
            return _block("the HERO master is immutable; save only the helper-opened working copy")
    if tool in {"run", "terminal", "execute_code"}:
        payload = json.dumps(args, ensure_ascii=False, default=str)
        if tool == "terminal" and _CLIFF_COMFY_WRAPPER.search(payload) and not re.search(r"[;&|]", payload):
            return None
        if tool == "run" or _EXTERNAL_SCRIPT.search(payload):
            return _block("use only the checked-in helper loaded inside Blender MCP")
    return None


def register(ctx: Any) -> None:
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
