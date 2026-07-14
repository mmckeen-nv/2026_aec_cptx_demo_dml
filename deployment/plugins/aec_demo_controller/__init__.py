"""Hard runtime guardrails for the AEC demo agents.

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
_FORBIDDEN_COMMAND_RE = re.compile(
    r"(?:^|[_\s-])(?:NewSmall|New|SaveAs|Save|Export)(?:$|[_\s-])", re.IGNORECASE
)


def _active() -> bool:
    return os.environ.get("AEC_DEMO_ID", "").strip().lower() == _DEMO_ID


def _session(kwargs: Dict[str, Any]) -> str:
    return str(kwargs.get("session_id") or kwargs.get("task_id") or "vp-default")


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
    key = "script" if tool == "mcp_rhino_run_python" else "code"
    return str(args.get(key) or "")


def _is_mutation(tool: str, args: Dict[str, Any]) -> bool:
    return tool in _MUTATION_TOOLS and bool(_MUTATION_RE.search(_script(args, tool)))


def on_session_start(**kwargs: Any) -> None:
    if not _active():
        return
    with _LOCK:
        _STATES[_session(kwargs)] = _fresh()
    _log("session_start", kwargs)


def on_session_reset(**kwargs: Any) -> None:
    on_session_start(**kwargs)


def on_pre_llm_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    state = _state(kwargs)
    context = (
        "AEC VP PHASE CONTROLLER (runtime enforced): the model authors bounded Rhino geometry; "
        "no monolithic builder exists. Begin with DML stats -> phase query -> CMA augment. "
        "Use the already-ready Rhino slot, open the datum template at most once, and never spawn "
        "a replacement slot. Build no more than three coherent Rhino groups before list-objects "
        "and viewport inspection. Save only after the final validated Rhino gate. Blender remains "
        "locked until that save succeeds. Current counters: "
        f"mutations={state['mutations']}, since_inspection={state['mutations_since_inspection']}, "
        f"since_memory={state['mutations_since_memory']}, saved={state['saved']}."
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
    if int(state["failures"].get(sig, 0)) >= 2:
        return _block(kwargs, "this identical tool call has already failed twice; query DML and use a materially changed approach")

    if tool in {"run", "mcp_rhino_spawn_slot", "mcp_rhino_close_slot", "mcp_rhino_close_doc"}:
        return _block(kwargs, f"{tool} is prohibited in this workflow; preserve the healthy launcher-owned Rhino slot")

    if tool == "mcp_rhino_run_command":
        command = str(args.get("command") or args.get("macro") or "")
        if _FORBIDDEN_COMMAND_RE.search(command):
            return _block(kwargs, "interactive New/Save/Export commands are prohibited; use the datum template, save_doc, and direct 3DM handoff")

    if tool == "mcp_rhino_open_doc":
        path = str(args.get("path") or args.get("file_path") or "").replace("\\", "/").lower()
        if "vp_studio_01_template.3dm" not in path:
            return _block(kwargs, "only source/vp_studio_01_template.3dm may start a fresh VP run")
        if state["opened"] or state["mutations"]:
            return _block(kwargs, "the datum template may be opened only once and never reopened after modeling begins")

    if tool in _MUTATION_TOOLS:
        required = "script" if tool == "mcp_rhino_run_python" else "code"
        if not str(args.get(required) or "").strip():
            return _block(kwargs, f"{tool} requires a non-empty '{required}' argument")

    if _is_mutation(tool, args):
        if not (state["stats"] and state["query"] and state["augment"]):
            return _block(kwargs, "modeling is locked until successful DML stats, phase-specific DML query, and CMA augment calls occur in that order")
        if state["mutations_since_inspection"] >= 3:
            return _block(kwargs, "three Rhino mutations occurred without inspection; call list_objects and get_viewport_image before more geometry")
        if state["mutations_since_memory"] >= 6:
            return _block(kwargs, "the current subphase budget is exhausted; ingest the attempt evidence, query DML, and call CMA augment before continuing")

    if tool == "mcp_daystrom_dml_query" and state["mutations_since_memory"] >= 6 and not state["ingested_since_memory"]:
        return _block(kwargs, "ingest the just-completed attempt record before querying memory for the next subphase")

    if tool == "mcp_cma_augment" and not state["query"]:
        return _block(kwargs, "CMA augment must follow a successful phase-specific DML query")

    if tool == "mcp_rhino_save_doc":
        if not state["mutations"]:
            return _block(kwargs, "nothing agent-authored has been modeled")
        if state["mutations_since_inspection"] or state["inspections"] < 2 or state["viewports"] < 1:
            return _block(kwargs, "save is a phase gate: require current object inspection plus at least one viewport validation after the last mutation")

    if tool.startswith("mcp_blender_") and not state["saved"]:
        return _block(kwargs, "Blender is locked until the validated Rhino document is saved through mcp_rhino_save_doc")

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
        state["saved"] = False
        if state["mutations_since_memory"] >= 6:
            state["query"] = False
            state["augment"] = False
            state["ingested_since_memory"] = False
    elif tool in _INSPECTION_TOOLS:
        state["inspections"] += 1
        if tool == "mcp_rhino_get_viewport_image":
            state["viewports"] += 1
            state["viewport_since_mutation"] = True
        elif tool == "mcp_rhino_list_objects":
            state["listed_since_mutation"] = True
        # A complete validation pair is required to unlock more mutation.
        if state["listed_since_mutation"] and state["viewport_since_mutation"]:
            state["mutations_since_inspection"] = 0
    elif tool == "mcp_rhino_save_doc":
        state["saved"] = True
    _log("tool_ok", kwargs, tool_name=tool, signature=sig, state=state.copy())


def register(ctx: Any) -> None:
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("on_session_reset", on_session_reset)
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
