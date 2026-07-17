"""Execution rails for the Blender-only Cliff House HERO quick lane."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional


_EXTERNAL_SCRIPT = re.compile(r"(?:[.]py|[.]cs)\b|RunPythonScript|EditPythonScript|RunScript", re.I)
_BLENDER_HOST_EXIT = re.compile(
    r"\b(?:raise\s+SystemExit|sys[.]exit\s*\(|quit\s*\(|exit\s*\(|bpy[.]ops[.]wm[.]quit_blender\s*\()",
    re.I,
)
_HERO_MASTER_SAVE = re.compile(
    r"save_(?:as_)?mainfile[\s\S]{0,500}cliff_house_02_HERO[.]blend", re.I
)
_DIRECT_COMFY = re.compile(
    r'^\s*python3?\s+(?:"[^"\r\n]*|\'[^\'\r\n]*\'|[^\s\r\n]+)'
    r'cliff_house[/\\]hero[/\\]skills[/\\]comfyui_cliff_hero[.]py["\']?'
    r'(?:\s+--dry-run)?\s*$', re.I,
)
_RELATIVE_COMFY = re.compile(
    r'^\s*python3?\s+(?:[.]/)?skills[/\\]comfyui_cliff_hero[.]py'
    r'(?:\s+--dry-run)?\s*$', re.I,
)


def _active() -> bool:
    return os.environ.get("AEC_DEMO_ID", "").strip().lower() == "cliff-house-hero-01"


def _block(message: str) -> Dict[str, str]:
    return {"action": "block", "message": "Cliff HERO rails: " + message}


def _terminal_command(args: Dict[str, Any]) -> str:
    for key in ("command", "cmd"):
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _approved_comfy_command(args: Dict[str, Any]) -> Optional[str]:
    command = _terminal_command(args)
    if _DIRECT_COMFY.fullmatch(command) or _RELATIVE_COMFY.fullmatch(command):
        return command
    match = re.fullmatch(r"\s*cd\s+(['\"]?)(.+?)\1\s*&&\s*(.+?)\s*", command)
    if not match:
        return None
    expected = os.path.join(
        os.environ.get("AEC_DEMO_ROOT", ""), "demos", "cliff_house", "hero"
    )
    directory = os.path.normcase(os.path.normpath(match.group(2).replace("/", os.sep)))
    if directory != os.path.normcase(os.path.normpath(expected)):
        return None
    helper = match.group(3).strip()
    return helper if _RELATIVE_COMFY.fullmatch(helper) else None


def on_pre_llm_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    root = os.environ.get("AEC_DEMO_ROOT", "")
    return {"context": (
        "CLIFF HERO HARD RAILS: this quick lane is Blender-to-Comfy only; never call Rhino or browser tools. "
        "The demo root is exactly {0}/demos/cliff_house/hero. Read exactly "
        "{0}/demos/cliff_house/hero/QUICK_DEMO.md; it is not under skills. Do not search for files, "
        "hash the master yourself, or probe ComfyUI because the checked helpers own those validations. "
        "Through Blender MCP, load {0}/demos/cliff_house/hero/skills/"
        "blender_cliff_hero.py, then require CLIFF_HERO_OPEN_PASS and CLIFF_HERO_RENDER_PASS. "
        "For ComfyUI use terminal and only these commands, one per turn: "
        "python \"$AEC_DEMO_ROOT/demos/cliff_house/hero/skills/comfyui_cliff_hero.py\" --dry-run ; "
        "then python \"$AEC_DEMO_ROOT/demos/cliff_house/hero/skills/comfyui_cliff_hero.py\". "
        "Do not invent comfy_stylize.py, change Python executables, or hand-build a workflow. "
        "Require COMFY_OUTPUT_PASS stage=sdxl+flux. DML is advisory."
    ).format(root)}


def on_pre_tool_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    tool = str(kwargs.get("tool_name") or "")
    args = kwargs.get("args") if isinstance(kwargs.get("args"), dict) else {}
    if tool.startswith("mcp_rhino_"):
        return _block("Rhino is prohibited in the Blender-only quick lane")
    if tool.startswith("browser_"):
        return _block("browser automation is prohibited; use the approved terminal wrapper")
    if tool == "mcp_blender_execute_blender_code":
        code = str(args.get("code") or "")
        if _BLENDER_HOST_EXIT.search(code):
            return _block("never terminate the Blender host")
        if _HERO_MASTER_SAVE.search(code):
            return _block("the Cliff HERO master is immutable; save only its working copy")
    if tool in {"run", "terminal", "execute_code"}:
        payload = json.dumps(args, ensure_ascii=False, default=str)
        if tool == "terminal" and _approved_comfy_command(args):
            return None
        if tool in {"run", "terminal", "execute_code"} or _EXTERNAL_SCRIPT.search(payload):
            return _block("only the checked-in Comfy wrapper may run outside Blender MCP")
    return None


def register(ctx: Any) -> None:
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
