"""Narrow safety and execution rails for the Blender-only BAC Teapot demo."""

from __future__ import annotations

import json
import os
import re
import shlex
from typing import Any, Dict, Optional


_EXTERNAL_SCRIPT = re.compile(r"(?:[.]py|[.]cs)\b|RunPythonScript|EditPythonScript|RunScript", re.I)
_BLENDER_HOST_EXIT = re.compile(r"\b(?:raise\s+SystemExit|sys[.]exit\s*\(|quit\s*\(|exit\s*\(|bpy[.]ops[.]wm[.]quit_blender\s*\()", re.I)
_APPROVED_COMFY_WRAPPER = re.compile(
    r"teapot[/\\]skills[/\\](?:comfyui_teapot|comfyui_bac_hero)[.]py",
    re.I,
)
_HERO_MASTER_SAVE = re.compile(r"save_(?:as_)?mainfile[\s\S]{0,500}BAC_TEAPOT_HERO[.]blend", re.I)


def _active():
    return os.environ.get("AEC_DEMO_ID", "").strip().lower() == "teapot-01"


def _block(message):
    return {"action": "block", "message": "BAC Teapot rails: " + message}


def _terminal_command(args):
    for key in ("command", "cmd"):
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _approved_comfy_command(args):
    """Allow only a checked-in wrapper, optionally after one exact demo-root cd."""
    command = _terminal_command(args)
    root = os.environ.get("AEC_DEMO_ROOT", "")
    env_prefix = re.match(r'^\s*AEC_DEMO_ROOT=(["\']?)(.+?)\1\s+', command, re.I)
    if env_prefix:
        supplied = os.path.normcase(os.path.normpath(env_prefix.group(2).replace("/", os.sep)))
        expected_root = os.path.normcase(os.path.normpath(root))
        if supplied != expected_root:
            return None
        command = command[env_prefix.end():]
    command = re.sub(r'\s+2>&1\s*$', '', command).strip()
    match = re.fullmatch(r"\s*cd\s+(['\"]?)(.+?)\1\s*&&\s*(.+?)\s*", command)
    if match:
        expected = os.path.join(root, "demos", "teapot")
        directory = os.path.normcase(os.path.normpath(match.group(2).replace("/", os.sep)))
        if directory != os.path.normcase(os.path.normpath(expected)):
            return None
        command = match.group(3).strip()
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return None
    if len(tokens) not in (2, 3) or tokens[0].lower() not in {"python", "python3"}:
        return None
    if len(tokens) == 3 and tokens[2] != "--dry-run":
        return None
    script = tokens[1].replace("\\", "/")
    expected_root = root.replace("\\", "/").rstrip("/")
    if re.match(r"^[A-Za-z]:/", expected_root):
        msys_root = "/" + expected_root[0].lower() + expected_root[2:]
    else:
        msys_root = expected_root
    allowed = set()
    for name in ("comfyui_teapot.py", "comfyui_bac_hero.py"):
        suffix = "/demos/teapot/skills/" + name
        allowed.update({
            "skills/" + name,
            "./skills/" + name,
            "$AEC_DEMO_ROOT" + suffix,
            "${AEC_DEMO_ROOT}" + suffix,
            "%AEC_DEMO_ROOT%" + suffix,
            expected_root + suffix,
            msys_root + suffix,
        })
    if script.casefold() not in {item.casefold() for item in allowed}:
        return None
    marker = os.path.join(root, "demos", "teapot", "work", "active_render_lane.txt")
    if os.path.isfile(marker):
        try:
            with open(marker, "r", encoding="utf-8") as stream:
                lane = stream.readline().strip()
        except OSError:
            return None
        selected = os.path.basename(script).casefold()
        expected = "comfyui_bac_hero.py" if lane == "bac_hero" else "comfyui_teapot.py" if lane == "teapot" else ""
        if selected != expected:
            return None
    return command


def on_pre_llm_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    root = os.environ.get("AEC_DEMO_ROOT", "")
    return {"context": (
        "BAC TEAPOT HARD RAILS: this demo is Blender-only; never call, inspect, start, or repair Rhino. "
        "START GATE: session startup is idle. Do not mutate Blender until the user explicitly asks to build "
        "or start the Utah teapot; reading prompts is not authorization. Repo root is {0}; demo root is "
        "{0}/demos/teapot. Do not list or guess filenames. Read exactly system_prompts/00_session_startup.md, "
        "skills/INDEX.md, skills/session_state.md, user_prompts/project_prompt.md, "
        "prompts/01_locked_teapot_manifest.md, and only the current phase there. "
        "Every Blender MCP call is isolated: reload the helper module inside every code call; never reuse tp "
        "from a prior call. Through mcp_blender_execute_blender_code(code=...), load "
        "skills/blender_teapot_interactions.py and call build_canonical_teapot(root, reset_scene=True). "
        "Require the locked SHA-256, CANONICAL_DATA_PASS, and TEAPOT_BUILD_PASS with four objects, "
        "0.300000 m width, and Z=0 before staging. Never use generic run, terminal scripts, external "
        "Python/C#, primitives, proxies, or legacy 3dm. Then call prepare_product_stage and "
        "render_preview. Material requests are open-ended and do not replay the build. If asked for "
        "the HERO house, use {0}/demos/teapot/skills/blender_bac_hero.py through Blender "
        "MCP; source is {0}/demos/teapot/hero/BAC_TEAPOT_HERO.blend. Never substitute the "
        "standalone Cliff House or VP Studio HERO. After a valid teapot preview, an explicit user request may run "
        "{0}/demos/teapot/skills/comfyui_teapot.py through terminal. The BAC house uses "
        "{0}/demos/teapot/skills/comfyui_bac_hero.py. Both approved Comfy wrappers "
        "own their own preflight; do not read their internals or search for QUICK_DEMO.md. Run the exact "
        "approved wrapper path with --dry-run, then without it. They own SDXL depth followed by FLUX.2 Klein "
        "and must reach COMFY_OUTPUT_PASS stage=sdxl+flux. "
        "DML is advisory."
    ).format(root)}


def on_pre_tool_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    tool = str(kwargs.get("tool_name") or "")
    args = kwargs.get("args") if isinstance(kwargs.get("args"), dict) else {}
    if tool.startswith("mcp_rhino_"):
        return _block("Rhino is prohibited because BAC Teapot is Blender-only")
    if tool.startswith("browser_"):
        return _block("browser automation is prohibited; run only the approved ComfyUI wrapper through terminal")
    if tool == "mcp_blender_execute_blender_code":
        code = str(args.get("code") or "")
        if _BLENDER_HOST_EXIT.search(code):
            return _block(
                "never terminate the Blender host or run ComfyUI here. After the Blender render receipt, use terminal with "
                "exactly python \"$AEC_DEMO_ROOT/demos/teapot/skills/comfyui_teapot.py\" --dry-run "
                "(or comfyui_bac_hero.py for the HERO lane), then the same command without --dry-run"
            )
        if _HERO_MASTER_SAVE.search(code):
            return _block("the HERO master is immutable; save only the helper-opened working copy")
    if tool in {"run", "terminal", "execute_code"}:
        payload = json.dumps(args, ensure_ascii=False, default=str)
        if tool == "terminal" and _approved_comfy_command(args):
            return None
        if tool in {"terminal", "execute_code"}:
            return _block(
                "outside-Blender execution is limited to the exact terminal command "
                "python \"$AEC_DEMO_ROOT/demos/teapot/skills/comfyui_teapot.py\" --dry-run "
                "or comfyui_bac_hero.py, followed by the same exact command without --dry-run; "
                "never move ComfyUI into Blender MCP or execute_code"
            )
        if tool == "run" or _EXTERNAL_SCRIPT.search(payload):
            return _block("use only the checked-in helper loaded inside Blender MCP")
    return None


def register(ctx: Any) -> None:
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
