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
_CONTEXT_LENGTH = max(1, int(os.environ.get("AEC_DEMO_CONTEXT_LENGTH", "262144")))
_MUTATION_TOOLS = {"mcp_rhino_run_python", "mcp_rhino_run_csharp"}
_INSPECTION_TOOLS = {"mcp_rhino_list_objects", "mcp_rhino_get_viewport_image"}
_BLENDER_MUTATION_TOOLS = {"mcp_blender_execute_blender_code", "mcp_blender_execute_code"}
_BLENDER_VIEWPORT_TOOLS = {"mcp_blender_get_viewport_screenshot"}
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
_RHINO_CAPTURE_RE = re.compile(r"CaptureToBitmap|CaptureToFile", re.IGNORECASE)
_LOCAL_PNG_RE = re.compile(r"(?P<path>[A-Za-z]:[\\/][^\"'\r\n]+?\.png)", re.IGNORECASE)
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
        "rhino_handoff_ready": False,
        "active_visual_app": "rhino",
        "rhino_last_viewport_path": "",
        "blender_mutations": 0,
        "blender_viewports": 0,
        "blender_viewport_since_mutation": False,
        "blender_vision_since_viewport": False,
        "failures": {},
        "calls": 0,
        "api_calls": 0,
        "raw_session_id": "",
        "last_input_tokens": 0,
        "peak_input_tokens": 0,
        "compression_rotations": 0,
        "compaction_retained_tokens": 0,
        "compaction_retained_pct": 0.0,
        "compaction_reclaimed_tokens": 0,
        "pending_rollover": None,
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


def _is_rhino_capture(tool: str, args: Dict[str, Any]) -> bool:
    return tool == "mcp_rhino_run_python" and bool(_RHINO_CAPTURE_RE.search(_script(args, tool)))


def _captured_png(args: Dict[str, Any]) -> str:
    match = _LOCAL_PNG_RE.search(_script(args, "mcp_rhino_run_python"))
    return match.group("path") if match else ""


def _vision_passed(kwargs: Dict[str, Any]) -> bool:
    payload = json.dumps(kwargs.get("result"), ensure_ascii=False, default=str)
    return bool(re.search(r"\bPASS\b", payload, re.IGNORECASE)) and not bool(
        re.search(r"\b(?:REVISE|FAIL(?:ED|URE)?)\b", payload, re.IGNORECASE)
    )


def _visual_validation_ready(state: Dict[str, Any]) -> bool:
    return bool(
        state["listed_since_mutation"]
        and state["viewport_since_mutation"]
        and state["vision_since_viewport"]
    )


def _blender_visual_validation_ready(state: Dict[str, Any]) -> bool:
    return bool(
        state["blender_viewport_since_mutation"]
        and state["blender_vision_since_viewport"]
    )


def _ensure_runtime_dirs() -> None:
    root = os.environ.get("AEC_DEMO_ROOT") or os.environ.get("AEC_DEMO_DIR")
    if not root:
        return
    try:
        (Path(root) / "work" / "dml_events").mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def on_session_start(**kwargs: Any) -> None:
    if not _active():
        return
    with _LOCK:
        _STATES.setdefault(_session(kwargs), _fresh())
    _ensure_runtime_dirs()
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
    _ensure_runtime_dirs()
    context = (
        "AEC VP SAFETY SHIM: follow the same agentic phase workflow as Cliff House, using the VP "
        "studio brief as the project-specific design input. Author bounded Rhino geometry and "
        "inspect at meaningful design checkpoints. The launcher owns the ready Rhino slot; do not "
        "spawn, close, or replace it. Use script= for both Rhino Python and C# tools. The safety "
        "shim does not impose mutation quotas, memory quotas, or phase-transition quotas. If an "
        "application MCP cannot connect, report that blocker immediately. Never repair Hermes "
        "configuration from inside the demo and never launch Rhino's Python editor or a script file. "
        "At every major Rhino phase boundary, capture fresh object-list and viewport evidence after "
        "the latest geometry change. Rhino MCP 0.1.5 nests viewport bytes instead of returning a "
        "usable URL: save ActiveView.CaptureToBitmap(System.Drawing.Size(960,540)) to an absolute "
        "PNG under work/ with a read-only mcp_rhino_run_python(script=...) call; the controller "
        "recognizes CaptureToBitmap as viewport evidence, so do not call get_viewport_image again. Then call "
        "vision_analyze on that local path. Never invent a URL or decode base64 with execute_code. "
        "Ask vision only for required visible elements, named defects, and a short PASS/REVISE "
        "verdict; never request a general image description. Use one final object listing per "
        "phase and distill it rather than echoing the raw payload. Model only the physical "
        "building, LED volume, rooms, rigging, cameras, furniture, and production equipment; "
        "electrical/HVAC/data/fire systems are a load note, never geometry. After each validated "
        "phase, ingest one <=1200-character DML state record and begin the next phase with one "
        "targeted DML query plus CMA augmentation. A captured image without completed "
        "vision_analyze is not validation. "
        "The LED wall must be a thin smooth continuous curve, never thick box panels. Finished "
        "architecture cannot be anonymous boxes. After Blender import, replace every visible "
        "required equipment proxy with an approved cached asset and complete actual materials plus "
        "motivated LED/key/fill/rim/practical lighting before any beauty render or ComfyUI work. "
        "Save Rhino exactly once after the final physical-layout audit. CMA success reinforcement "
        "requires the visual pass; Blender handoff additionally requires the final gated save. "
        "Rhino and Blender have independent viewport/vision gates. A JSON or Markdown report is never "
        "visual evidence. After Blender changes, capture with mcp_blender_get_viewport_screenshot and call "
        "vision_analyze on its local image path; do not repeat Rhino validation."
    )
    return {"context": context}


def on_pre_api_request(**kwargs: Any) -> None:
    """Measure context pressure and detect compression-driven session rotation."""
    if not _active():
        return
    state = _state(kwargs)
    raw_session = str(kwargs.get("session_id") or "")
    approx_tokens = max(0, int(kwargs.get("approx_input_tokens") or 0))
    prior_session = str(state.get("raw_session_id") or "")
    if prior_session and raw_session and raw_session != prior_session:
        before_tokens = max(
            int(state.get("last_input_tokens") or 0),
            int(state.get("peak_input_tokens") or 0),
        )
        state["compression_rotations"] += 1
        state["pending_rollover"] = {
            "from_session": prior_session,
            "to_session": raw_session,
            "before_tokens": before_tokens,
        }
        state["peak_input_tokens"] = 0
    if raw_session:
        state["raw_session_id"] = raw_session
    state["api_calls"] += 1
    state["peak_input_tokens"] = max(int(state["peak_input_tokens"]), approx_tokens)
    _log(
        "context_pre_api",
        kwargs,
        raw_session_id=raw_session,
        api_call_count=kwargs.get("api_call_count"),
        approx_input_tokens=approx_tokens,
        context_length=_CONTEXT_LENGTH,
        context_pct=round(100.0 * approx_tokens / _CONTEXT_LENGTH, 2),
        message_count=kwargs.get("message_count"),
    )


def on_post_api_request(**kwargs: Any) -> None:
    """Record actual provider usage and quantify compaction effectiveness."""
    if not _active():
        return
    state = _state(kwargs)
    usage = kwargs.get("usage") if isinstance(kwargs.get("usage"), dict) else {}
    input_tokens = max(
        0,
        int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0),
    )
    if input_tokens:
        state["last_input_tokens"] = input_tokens
        state["peak_input_tokens"] = max(int(state["peak_input_tokens"]), input_tokens)
    pending = state.get("pending_rollover")
    if isinstance(pending, dict) and input_tokens:
        before = max(0, int(pending.get("before_tokens") or 0))
        reclaimed = max(0, before - input_tokens)
        savings_pct = round(100.0 * reclaimed / before, 2) if before else 0.0
        retained_pct = round(100.0 * input_tokens / _CONTEXT_LENGTH, 2)
        state["compaction_retained_tokens"] = input_tokens
        state["compaction_retained_pct"] = retained_pct
        state["compaction_reclaimed_tokens"] = reclaimed
        state["pending_rollover"] = None
        _log(
            "context_rollover",
            kwargs,
            from_session=pending.get("from_session"),
            to_session=pending.get("to_session"),
            before_tokens=before,
            retained_tokens=input_tokens,
            reclaimed_tokens=reclaimed,
            savings_pct=savings_pct,
            retained_pct_of_window=retained_pct,
            ineffective=bool(before and (input_tokens >= before * 0.8 or retained_pct >= 50.0)),
            compression_rotations=state["compression_rotations"],
        )
    _log(
        "context_usage",
        kwargs,
        raw_session_id=kwargs.get("session_id"),
        input_tokens=input_tokens,
        output_tokens=usage.get("output_tokens") or usage.get("completion_tokens") or 0,
        context_length=_CONTEXT_LENGTH,
        context_pct=round(100.0 * input_tokens / _CONTEXT_LENGTH, 2),
        compression_rotations=state["compression_rotations"],
    )


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
        image_source = str(args.get("image_url") or "").strip()
        if not image_source or not str(args.get("question") or "").strip():
            return _block(kwargs, "vision_analyze requires the captured viewport image_url and a specific defect-review question")
        app = str(state.get("active_visual_app") or "rhino")
        viewport_ready = (
            state["blender_viewport_since_mutation"]
            if app == "blender"
            else state["viewport_since_mutation"]
        )
        if not viewport_ready:
            capture_tool = "mcp_blender_get_viewport_screenshot" if app == "blender" else "a CaptureToBitmap Rhino Python call"
            return _block(kwargs, f"capture a fresh {app.title()} viewport with {capture_tool} after the latest mutation before vision analysis")
        if app == "rhino" and re.match(r"^https?://", image_source, re.IGNORECASE):
            return _block(
                kwargs,
                "Rhino MCP 0.1.5 does not return a usable remote viewport URL; save the active view to work/*.png with ActiveView.CaptureToBitmap in a read-only Rhino Python call, then pass that absolute local path",
            )

    if tool == "mcp_rhino_save_doc" and state["mutations"] and not _visual_validation_ready(state):
        return _block(kwargs, "a checkpoint or handoff save requires fresh list_objects, viewport capture, and completed vision_analyze after the latest Rhino mutation")

    if tool == "mcp_cma_reinforce" and state["mutations"]:
        if not _visual_validation_ready(state):
            return _block(kwargs, "CMA success reinforcement requires fresh Rhino object/vision validation after the latest mutation")

    if tool in _BLENDER_MUTATION_TOOLS and state["mutations"]:
        if not state["rhino_handoff_ready"]:
            return _block(
                kwargs,
                "Blender import requires a successfully saved Rhino handoff. Do exactly this once in Rhino: list_objects, save one local PNG with CaptureToBitmap, vision_analyze that PNG to a PASS verdict, then mcp_rhino_save_doc. Do not create validation JSON and do not repeat completed steps.",
            )

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
        state["rhino_handoff_ready"] = False
        state["active_visual_app"] = "rhino"
    elif _is_rhino_capture(tool, args):
        state["inspections"] += 1
        state["viewports"] += 1
        state["viewport_since_mutation"] = True
        state["vision_since_viewport"] = False
        state["active_visual_app"] = "rhino"
        state["rhino_last_viewport_path"] = _captured_png(args)
    elif tool in _INSPECTION_TOOLS:
        state["inspections"] += 1
        if tool == "mcp_rhino_get_viewport_image":
            state["viewports"] += 1
            state["viewport_since_mutation"] = True
            state["vision_since_viewport"] = False
            state["active_visual_app"] = "rhino"
        elif tool == "mcp_rhino_list_objects":
            state["listed_since_mutation"] = True
        # Object and viewport evidence still require a subsequent vision call.
        if state["listed_since_mutation"] and state["viewport_since_mutation"]:
            state["mutations_since_inspection"] = 0
    elif tool in _BLENDER_MUTATION_TOOLS:
        state["blender_mutations"] += 1
        state["blender_viewport_since_mutation"] = False
        state["blender_vision_since_viewport"] = False
        state["active_visual_app"] = "blender"
    elif tool in _BLENDER_VIEWPORT_TOOLS:
        state["blender_viewports"] += 1
        state["blender_viewport_since_mutation"] = True
        state["blender_vision_since_viewport"] = False
        state["active_visual_app"] = "blender"
    elif tool == "vision_analyze":
        passed = _vision_passed(kwargs)
        if state.get("active_visual_app") == "blender" and state["blender_viewport_since_mutation"]:
            state["blender_vision_since_viewport"] = passed
        elif state["viewport_since_mutation"]:
            state["vision_since_viewport"] = passed
        _log("vision_verdict", kwargs, application=state.get("active_visual_app"), passed=passed)
    elif tool == "mcp_rhino_save_doc":
        state["saved"] = True
        state["rhino_handoff_ready"] = _visual_validation_ready(state)
    _log("tool_ok", kwargs, tool_name=tool, signature=sig, state=state.copy())


def register(ctx: Any) -> None:
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("on_session_reset", on_session_reset)
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("pre_api_request", on_pre_api_request)
    ctx.register_hook("post_api_request", on_post_api_request)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
