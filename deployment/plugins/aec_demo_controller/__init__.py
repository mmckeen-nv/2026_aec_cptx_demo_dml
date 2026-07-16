"""Minimal application-state safety guardrails for the AEC demo agents.

The controller does not create geometry and does not impose mutation quotas or
memory/vision ceremony. It blocks only unsafe lifecycle/UI paths and records a
durable trajectory for diagnosis.
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
_CLIFF_ID = "cliff-house-01"
_CONTEXT_LENGTH = max(1, int(os.environ.get("AEC_DEMO_CONTEXT_LENGTH", "262144")))
_MUTATION_TOOLS = {"mcp_rhino_run_python", "mcp_rhino_run_csharp"}
_INSPECTION_TOOLS = {"mcp_rhino_list_objects"}
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
_COMFY_EXECUTION_RE = re.compile(r"(?:127\.0\.0\.1:8188|localhost:8188|/prompt\b|ComfyUI)", re.IGNORECASE)
_EXTERNAL_SCRIPT_RE = re.compile(
    r"(?:exec|compile)\s*\([^\r\n]{0,500}(?:open\s*\(|\.py\b)|"
    r"open\s*\([^\r\n]{0,500}\.py\b[^\r\n]{0,500}(?:exec|compile)",
    re.IGNORECASE,
)
_RHINO_CAPTURE_SCRIPT = "capture_rhino_viewport.py"
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
    return os.environ.get("AEC_DEMO_ID", "").strip().lower() in {_DEMO_ID, _CLIFF_ID}


def _is_vp() -> bool:
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
    script = _script(args, tool)
    return tool in _MUTATION_TOOLS and bool(
        _MUTATION_RE.search(script) or _EXTERNAL_SCRIPT_RE.search(script)
    )


def _is_rhino_capture(tool: str, args: Dict[str, Any]) -> bool:
    script = _script(args, tool)
    return tool == "mcp_rhino_run_python" and bool(
        _RHINO_CAPTURE_RE.search(script) or _RHINO_CAPTURE_SCRIPT.lower() in script.lower()
    )


def _captured_png(args: Dict[str, Any]) -> str:
    match = _LOCAL_PNG_RE.search(_script(args, "mcp_rhino_run_python"))
    return match.group("path") if match else ""


def _capture_call() -> str:
    return (
        "mcp_rhino_run_python(script=\"import os; p=os.path.join(os.environ['AEC_DEMO_ROOT'],"
        "'demos','virtual_production_studio','scripts','capture_rhino_viewport.py'); "
        "exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))\")"
    )


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
    if not _is_vp():
        return {"context": (
            "AEC CLIFF GUARDRAILS: follow the original Cliff House phase rhythm. Use coherent bounded "
            "Rhino MCP Python/C# scripts, inspect at meaningful checkpoints, and save useful artifacts. "
            "DML active-read is automatic; query/ingest at meaningful boundaries, not between every call. "
            "Never use Rhino command macros, spawn/close slots, open a script editor, or repair apps/config."
        )}
    context = (
        "AEC VP GUARDRAILS: work like the original Cliff House demo. Read the VP brief and only the "
        "current phase prompt; design the geometry yourself through bounded Rhino MCP Python/C# scripts. "
        "A substantial coherent phase script is allowed. Inspect after meaningful design groups and save "
        "useful checkpoints. DML active-read is automatic: query it when prior experience is useful and "
        "ingest one compact record after a meaningful success or failure, not between ordinary tool calls. "
        "At phase review, capture a local PNG with scripts/capture_rhino_viewport.py and use vision once; "
        "revise visible defects, but report unavailable vision instead of looping. The launcher owns Rhino: "
        "never spawn/close slots, use command macros, open a Python editor, or repair applications/config. "
        "Model the physical studio only; electrical is an estimated-load note. The LED face must be a smooth "
        "continuous curve. Use direct .3dm handoff, then cached assets/materials/lighting in Blender."
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

    if _is_vp() and tool == "mcp_rhino_get_viewport_image":
        return _block(
            kwargs,
            "the Rhino 0.1.5 viewport tool is prohibited because it injects nested base64 into context. Execute this exact local-PNG capture instead: " + _capture_call(),
        )

    if tool in {"terminal", "execute_code", "patch", "write_file"}:
        payload = json.dumps(args, ensure_ascii=False, default=str)
        if tool in {"terminal", "execute_code"} and _RHINO_UI_RECOVERY_RE.search(payload):
            return _block(kwargs, "do not launch Rhino or Python scripts through shell/UI recovery; use the registered Rhino MCP or report it unavailable")
        if _HERMES_CONFIG_MUTATION_RE.search(payload):
            return _block(kwargs, "the running demo may not modify Hermes configuration; report the MCP preflight blocker for host-side repair")
        if tool in {"terminal", "execute_code"} and _BLENDER_RECOVERY_RE.search(payload):
            return _block(kwargs, "do not launch, configure, patch, or repair Blender/add-ons from inside the demo; report the Blender MCP preflight blocker")

    if _is_vp() and tool == "mcp_rhino_open_doc":
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
        if _is_vp() and app == "rhino" and re.match(r"^https?://", image_source, re.IGNORECASE):
            return _block(
                kwargs,
                "Rhino MCP 0.1.5 does not return a usable remote viewport URL; save the active view to work/*.png with ActiveView.CaptureToBitmap in a read-only Rhino Python call, then pass that absolute local path",
            )

    if _is_vp() and tool in _BLENDER_MUTATION_TOOLS and state["mutations"]:
        if not state["saved"]:
            return _block(
                kwargs,
                "Blender import requires a successfully saved Rhino .3dm handoff first.",
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
    elif tool == "mcp_daystrom_dml_query":
        state["query"] = True
    elif tool == "mcp_daystrom_dml_ingest":
        state["ingested_since_memory"] = True
    elif tool == "mcp_cma_augment" and state["query"]:
        state["augment"] = True
        state["mutations_since_memory"] = 0
        state["ingested_since_memory"] = False
    elif tool == "mcp_rhino_open_doc":
        state["opened"] += 1
    elif _is_rhino_capture(tool, args):
        state["inspections"] += 1
        state["viewports"] += 1
        state["viewport_since_mutation"] = True
        state["vision_since_viewport"] = False
        state["active_visual_app"] = "rhino"
        state["rhino_last_viewport_path"] = _captured_png(args) or str(
            Path(os.environ.get("AEC_DEMO_ROOT", ""))
            / "demos" / "virtual_production_studio" / "work" / "rhino_phase_view.png"
        )
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
        state["rhino_handoff_ready"] = True
    _log("tool_ok", kwargs, tool_name=tool, signature=sig, state=state.copy())


def register(ctx: Any) -> None:
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("on_session_reset", on_session_reset)
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("pre_api_request", on_pre_api_request)
    ctx.register_hook("post_api_request", on_post_api_request)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
