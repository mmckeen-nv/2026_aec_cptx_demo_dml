"""Minimal application-state safety guardrails for the AEC demo agents.

The controller does not create geometry.  It only constrains tool ordering,
requires inspection and memory checkpoints, and records a durable trajectory.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


_LOCK = threading.RLock()
_STATES: Dict[str, Dict[str, Any]] = {}
_DEMO_ID = "vp-studio-01"
_MUTATION_TOOLS = {"mcp_rhino_run_python", "mcp_rhino_run_csharp"}
_INSPECTION_TOOLS = {"mcp_rhino_list_objects", "mcp_rhino_get_viewport_image"}
_MEMORY_TOOLS = {
    "mcp_daystrom_dml_stats",
    "mcp_daystrom_dml_query",
    "mcp_daystrom_dml_ingest",
    "mcp_cma_augment",
    "mcp_cma_reinforce",
}
_MUTATION_RE = re.compile(
    r"(?:Objects\s*\.\s*(?:Add|Delete|Replace|Transform)|"
    r"doc\s*\.\s*Objects\s*\.\s*(?:Add|Delete|Replace|Transform)|"
    r"rs\s*\.\s*(?:Add|Delete|Move|Rotate|Scale|Transform)|"
    r"SetUserString|SetUserText|CommitChanges|Layers\s*\.\s*Add)",
    re.IGNORECASE,
)
_RHINO_UI_RECOVERY_RE = re.compile(
    r"(?:rhino(?:\.exe)?[^\r\n]*(?:\.py\b|RunPythonScript|EditPythonScript|PythonScript)|"
    r"(?:RunPythonScript|EditPythonScript|PythonScript)[^\r\n]*rhino)",
    re.IGNORECASE,
)
_BLENDER_RECOVERY_RE = re.compile(
    r"(?:blender(?:\.exe)?|blender[_-]?mcp|blendermcp|scripts[\\/]addons|"
    r"bpy\.ops\.preferences\.addon|bpy\.utils\.register_module|"
    r"start_blender|enable_mcp|taskkill[^\r\n]*blender)",
    re.IGNORECASE,
)
_HERMES_CONFIG_MUTATION_RE = re.compile(
    r"(?:hermes\s+config\s+(?:set|remove|unset)|"
    r"(?:AppData[\\/]Local[\\/]hermes|\.hermes)[\\/].*config\.ya?ml)",
    re.IGNORECASE,
)


def _active() -> bool:
    return os.environ.get("AEC_DEMO_ID", "").strip().lower() == _DEMO_ID


def _session(kwargs: Dict[str, Any]) -> str:
    # Hermes may replace session_id during context compression and follow-up
    # turns. task_id is the stable execution identity when it is available.
    return str(
        os.environ.get("AEC_DEMO_RUN_ID")
        or kwargs.get("task_id")
        or kwargs.get("session_id")
        or "vp-default"
    )


def _fresh() -> Dict[str, Any]:
    return {
        "stats": False,
        "query": False,
        "augment": False,
        "opened": 0,
        "mutations": 0,
        "mutations_since_inspection": 0,
        "mutations_since_memory": 0,
        "inspections": 0,
        "viewports": 0,
        "listed_since_mutation": False,
        "viewport_since_mutation": False,
        "vision_since_viewport": False,
        "ingested_since_memory": False,
        "saved": False,
        "failures": {},
        "calls": 0,
    }


def _state(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    sid = _session(kwargs)
    with _LOCK:
        return _STATES.setdefault(sid, _fresh())


def _log(event: str, kwargs: Dict[str, Any], **fields: Any) -> None:
    root = Path(os.environ.get("AEC_DEMO_CONTROLLER_LOG_DIR") or Path.home() / ".hermes" / "logs")
    try:
        root.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "demo_id": _DEMO_ID,
            "session_id": _session(kwargs),
            **fields,
        }
        with (root / "aec_demo_controller.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _signature(tool: str, args: Dict[str, Any]) -> str:
    payload = json.dumps(args, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(f"{tool}\0{payload}".encode("utf-8")).hexdigest()[:16]


def _block(kwargs: Dict[str, Any], message: str) -> Dict[str, str]:
    _log("blocked", kwargs, tool_name=kwargs.get("tool_name"), reason=message)
    return {"action": "block", "message": "AEC phase controller: " + message}


def _script(args: Dict[str, Any], tool: str) -> str:
    return str(args.get("script") or "")


def _is_mutation(tool: str, args: Dict[str, Any]) -> bool:
    return tool in _MUTATION_TOOLS and bool(_MUTATION_RE.search(_script(args, tool)))


def _visual_validation_ready(state: Dict[str, Any]) -> bool:
    return bool(
        state["listed_since_mutation"]
        and state["viewport_since_mutation"]
        and state["vision_since_viewport"]
    )


def on_session_start(**kwargs: Any) -> None:
    if not _active():
        return
    with _LOCK:
        _STATES.setdefault(_session(kwargs), _fresh())
    _log("session_start", kwargs)


def on_session_reset(**kwargs: Any) -> None:
    if not _active():
        return
    with _LOCK:
        _STATES[_session(kwargs)] = _fresh()
    _log("session_reset", kwargs)


def on_pre_llm_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    context = (
        "AEC VP SAFETY SHIM: follow the same agentic phase workflow as Cliff House, using the VP "
        "studio brief as the project-specific design input. Author bounded Rhino geometry and "
        "inspect at meaningful design checkpoints. The launcher owns the ready Rhino slot; do not "
        "spawn, close, or replace it. Use script= for both Rhino Python and C# tools. The safety "
        "shim does not impose mutation quotas, memory quotas, or phase-transition quotas. If an "
        "application MCP cannot connect, report that blocker immediately. Never repair Hermes "
        "configuration from inside the demo and never launch Rhino's Python editor or a script file. "
        "At every major Rhino phase boundary, capture fresh object-list and viewport evidence after "
        "the latest geometry change, then call vision_analyze on the returned image URL to identify "
        "visible defects. A captured image without completed vision_analyze is not validation. "
        "Checkpoint saves, CMA success reinforcement, and Blender handoff require that visual pass."
    )
    return {"context": context}


def on_pre_tool_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    tool = str(kwargs.get("tool_name") or "")
    args = kwargs.get("args") if isinstance(kwargs.get("args"), dict) else {}
    state = _state(kwargs)
    state["calls"] += 1

    sig = _signature(tool, args)

    if tool in {"run", "mcp_rhino_spawn_slot", "mcp_rhino_close_slot", "mcp_rhino_close_doc"}:
        return _block(kwargs, f"{tool} is prohibited in this workflow; preserve the healthy launcher-owned Rhino slot")

    if tool == "mcp_rhino_run_command":
        return _block(kwargs, "Rhino command macros are prohibited because they can wait for interactive input; use dedicated camera/selection tools or direct MCP Python/C#")

    if tool.startswith("browser_"):
        return _block(kwargs, "browser fallback is prohibited during the core Rhino-Blender-ComfyUI run; report the missing application MCP")

    if tool in {"terminal", "execute_code", "patch", "write_file"}:
        payload = json.dumps(args, ensure_ascii=False, default=str)
        if _RHINO_UI_RECOVERY_RE.search(payload):
            return _block(kwargs, "do not launch Rhino or Python scripts through shell/UI recovery; use the registered Rhino MCP or report it unavailable")
        if _HERMES_CONFIG_MUTATION_RE.search(payload):
            return _block(kwargs, "the running demo may not modify Hermes configuration; report the MCP preflight blocker for host-side repair")
        if _BLENDER_RECOVERY_RE.search(payload):
            return _block(kwargs, "do not launch, configure, patch, or repair Blender/add-ons from inside the demo; report the Blender MCP preflight blocker")

    if tool == "mcp_rhino_open_doc":
        path = str(args.get("path") or args.get("file_path") or "").replace("\\", "/").lower()
        if "vp_studio_01_template.3dm" not in path:
            return _block(kwargs, "only source/vp_studio_01_template.3dm may start a fresh VP run")
        if state["opened"] or state["mutations"]:
            return _block(kwargs, "the datum template may be opened only once and never reopened after modeling begins")

    if tool in _MUTATION_TOOLS:
        if not str(args.get("script") or "").strip():
            return _block(kwargs, f"{tool} requires a non-empty 'script' argument")

    if tool == "vision_analyze":
        if not str(args.get("image_url") or "").strip() or not str(args.get("question") or "").strip():
            return _block(kwargs, "vision_analyze requires the captured viewport image_url and a specific defect-review question")
        if not state["viewport_since_mutation"]:
            return _block(kwargs, "capture a fresh Rhino viewport after the latest mutation before vision analysis")

    if tool == "mcp_rhino_save_doc" and state["mutations"] and not _visual_validation_ready(state):
        return _block(kwargs, "a checkpoint or handoff save requires fresh list_objects, viewport capture, and completed vision_analyze after the latest Rhino mutation")

    if tool == "mcp_cma_reinforce" and state["mutations"]:
        if not _visual_validation_ready(state) or not state["saved"]:
            return _block(kwargs, "CMA success reinforcement requires fresh Rhino object/vision validation and a successful gated save")

    if tool in {"mcp_blender_execute_blender_code", "mcp_blender_execute_code"} and state["mutations"]:
        if not _visual_validation_ready(state) or not state["saved"]:
            return _block(kwargs, "Blender mutation/import requires a visually validated and successfully saved Rhino handoff")

    _log("allowed", kwargs, tool_name=tool, signature=sig)
    return None


def on_post_tool_call(**kwargs: Any) -> None:
    if not _active():
        return
    tool = str(kwargs.get("tool_name") or "")
    args = kwargs.get("args") if isinstance(kwargs.get("args"), dict) else {}
    state = _state(kwargs)
    status = str(kwargs.get("status") or "ok").lower()
    success = status == "ok" and not kwargs.get("error_message")
    sig = _signature(tool, args)
    if not success:
        state["failures"][sig] = int(state["failures"].get(sig, 0)) + 1
        _log("tool_error", kwargs, tool_name=tool, signature=sig, error=kwargs.get("error_message"))
        return

    if tool == "mcp_daystrom_dml_stats":
        state["stats"] = True
    elif tool == "mcp_daystrom_dml_query" and state["stats"]:
        state["query"] = True
    elif tool == "mcp_daystrom_dml_ingest":
        state["ingested_since_memory"] = True
    elif tool == "mcp_cma_augment" and state["query"]:
        state["augment"] = True
        state["mutations_since_memory"] = 0
        state["ingested_since_memory"] = False
    elif tool == "mcp_rhino_open_doc":
        state["opened"] += 1
    elif _is_mutation(tool, args):
        state["mutations"] += 1
        state["mutations_since_inspection"] += 1
        state["mutations_since_memory"] += 1
        state["listed_since_mutation"] = False
        state["viewport_since_mutation"] = False
        state["vision_since_viewport"] = False
        state["saved"] = False
    elif tool in _INSPECTION_TOOLS:
        state["inspections"] += 1
        if tool == "mcp_rhino_get_viewport_image":
            state["viewports"] += 1
            state["viewport_since_mutation"] = True
            state["vision_since_viewport"] = False
        elif tool == "mcp_rhino_list_objects":
            state["listed_since_mutation"] = True
        # Object and viewport evidence still require a subsequent vision call.
        if state["listed_since_mutation"] and state["viewport_since_mutation"]:
            state["mutations_since_inspection"] = 0
    elif tool == "vision_analyze" and state["viewport_since_mutation"]:
        state["vision_since_viewport"] = True
    elif tool == "mcp_rhino_save_doc":
        state["saved"] = True
    _log("tool_ok", kwargs, tool_name=tool, signature=sig, state=state.copy())


def register(ctx: Any) -> None:
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("on_session_reset", on_session_reset)
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
