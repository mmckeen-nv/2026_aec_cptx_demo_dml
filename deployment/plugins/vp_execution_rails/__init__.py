"""Narrow VP Studio execution rails.

This plugin does not create geometry or direct design choices. It supplies the
known-good Rhino 8 calling convention and blocks only destructive/external
execution paths. DML and validation remain advisory, matching Cliff House.
"""

from __future__ import annotations

import json
import os
import re
import threading
from typing import Any, Dict, Optional

_LOCK = threading.RLock()
_STATE: Dict[str, Dict[str, Any]] = {}
_MUTATION_TOOLS = {"mcp_rhino_run_python", "mcp_rhino_run_csharp"}
_MUTATION_RE = re.compile(
    r"(?:Objects\s*\.\s*(?:Add|Delete|Replace|Transform)|"
    r"doc\s*\.\s*Objects\s*\.\s*(?:Add|Delete|Replace|Transform)|"
    r"rs\s*\.\s*(?:Add|Delete|Move|Rotate|Scale|Transform)|"
    r"Layers\s*\.\s*Add|SetUserString|CommitChanges)",
    re.IGNORECASE,
)
_EXTERNAL_RHINO_SCRIPT_RE = re.compile(
    r"(?:exec|compile)\s*\([^\r\n]{0,600}(?:open\s*\(|\.(?:py|cs)\b)|"
    r"(?:RunPythonScript|EditPythonScript|RunScript|PythonScript)",
    re.IGNORECASE,
)
_SHELL_LANGUAGE_EXEC_RE = re.compile(
    r"(?:^|[;&|]\s*|\"command\"\s*:\s*\")\s*"
    r"(?:python(?:3|\.exe)?|py(?:\.exe)?|csi(?:\.exe)?|dotnet-script)\b|"
    r"(?:^|[;&|]\s*)\s*&\s*[^\r\n]+\.(?:py|cs)\b",
    re.IGNORECASE,
)
_SHELL_APP_LAUNCH_RE = re.compile(
    r"(?:blender(?:\.exe)?|rhino(?:\.exe)?|comfy(?:\.exe)?|comfyui)\b",
    re.IGNORECASE,
)
_COMFYUI_HELPER_COMMAND_RE = re.compile(
    r"^\s*python3?\s+(?:\./)?skills/comfyui_vp_stylize\.py"
    r"(?:\s+--dry-run|\s+--denoise\s+0\.20)?\s*$",
    re.IGNORECASE,
)
_COMFYUI_IMPROVISATION_RE = re.compile(
    r"(?:127\.0\.0\.1:8188|localhost:8188|/upload/image|/object_info|"
    r"/history/|/prompt\b|vp_studio_workflow\.json|comfy.*workflow.*\.json)",
    re.IGNORECASE,
)
_CAPTURE_RE = re.compile(r"CaptureToBitmap|CaptureToFile", re.IGNORECASE)
_BLENDER_PROHIBITED_HANDOFF_RE = re.compile(
    r"(?:\.obj\b|\.fbx\b|bpy\.ops\.(?:import_scene|wm\.obj_import)|"
    r"io_import_3dm|threemdm|rhino3dm\s+io\s+addon|"
    r"line\.startswith\(\s*['\"](?:v|f|o)['\"]\s*\)|objects_data)",
    re.IGNORECASE,
)
_RHINO_EXECUTION_ERROR_RE = re.compile(
    r"(?:Traceback\s*\(most recent call last\)|"
    r"\b(?:AttributeError|ImportError|IndexError|KeyError|NameError|TypeError|"
    r"ValueError|RuntimeError|SyntaxError)\s*:|"
    r"\bException\s*:)",
    re.IGNORECASE,
)
_BLENDER_CAMERA_LOOP_RE = re.compile(
    r"(?:CAMERA\s+(?:FIX|v\d+)|TrackTo|TRACK_TO|TRACK_NEGATIVE_Z|"
    r"primitive_cube_add|test_cube|test_v\d+\.png|test_recovery)",
    re.IGNORECASE,
)
_BLENDER_DIRECT_CAMERA_RENDER_RE = re.compile(
    r"(?:rotation_euler|rotation_quaternion|constraints\s*\.\s*new|"
    r"to_track_quat|Quaternion\s*\(|TRACK_(?:TO|Z|NEGATIVE_Z)|"
    r"bpy\.ops\.render\.render|render\s*\.\s*filepath|"
    r"/(?:tmp|temp)/|[A-Za-z]:[\\/](?:temp|tmp)[\\/]|"
    r"test[_-].*?\.png)",
    re.IGNORECASE,
)
_BLENDER_APPROVED_CAMERA_RE = re.compile(
    r"blender_vp_production\.py[\s\S]{0,3000}"
    r"(?:setup_(?:manifest_(?:hero_)?|beauty_)camera|render_preview)",
    re.IGNORECASE,
)
_BLENDER_DYNAMIC_ASSET_SCALE_RE = re.compile(
    r"(?:fit_to_proxy\s*\(|resolve_cached_asset\s*\(|"
    r"import_cached_asset\s*\(|dimensions\s*=|scale\s*=)",
    re.IGNORECASE,
)
_BLENDER_APPROVED_ASSET_PLACEMENT_RE = re.compile(
    r"blender_vp_production\.py[\s\S]{0,3000}place_cached_asset\s*\(",
    re.IGNORECASE,
)
_BLENDER_REQUIRED_SET_DRESSING_RE = re.compile(
    r"blender_vp_production\.py[\s\S]{0,3000}apply_required_set_dressing\s*\(",
    re.IGNORECASE,
)
_BLENDER_DIRECT_SCENE_IO_RE = re.compile(
    r"(?:bpy\.ops\.wm\.(?:open_mainfile|save_as_mainfile|save_mainfile)|"
    r"libraries\.load\([^\r\n]*\.blend|\.blend\b)",
    re.IGNORECASE,
)
_BLENDER_CURRENT_HANDOFF_RE = re.compile(
    r"blender_vp_production\.py[\s\S]{0,3000}import_current_handoff\s*\(",
    re.IGNORECASE,
)


def _active() -> bool:
    return os.environ.get("AEC_DEMO_ID", "").strip().lower() == "vp-studio-01"


def _sid(kwargs: Dict[str, Any]) -> str:
    return str(os.environ.get("AEC_DEMO_RUN_ID") or kwargs.get("task_id") or "vp")


def _state(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        return _STATE.setdefault(
            _sid(kwargs),
            {
                "total_mutations": 0,
                "phase_mutations": 0,
                "correction_mutations": 0,
                "review_started": False,
                "document_ready": False,
                "numeric_pass": False,
                "viewport_ready": False,
                "vision_reviewed": False,
                "saved": True,
                "blender_camera_retries": 0,
                "blender_visual_reviews": 0,
                "blender_handoff_ready": False,
                "blender_set_dressing_ready": False,
                "blender_render_ready": False,
                "comfy_preflight_ready": False,
                "workflow_phase": "rhino",
            },
        )


def _block(message: str) -> Dict[str, str]:
    return {"action": "block", "message": "VP execution rails: " + message}


def _script(args: Dict[str, Any]) -> str:
    return str(args.get("script") or "")


def _is_mutation(tool: str, args: Dict[str, Any]) -> bool:
    return tool in _MUTATION_TOOLS and bool(_MUTATION_RE.search(_script(args)))


def _result_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False, default=str)


def _rhino_execution_succeeded(tool: str, result: Any) -> bool:
    """MCP transport success is not the same as Rhino script success.

    rhino-mcp returns HTTP/MCP success while placing Python and C# exceptions in
    stdout.  Such calls must not consume geometry or correction budgets.
    """
    if tool not in _MUTATION_TOOLS:
        return True
    text = _result_text(result)
    if _RHINO_EXECUTION_ERROR_RE.search(text):
        return False
    if isinstance(result, dict):
        error = result.get("error") or result.get("stderr")
        if error and str(error).strip().lower() not in {"none", "null"}:
            return False
    return True


def on_pre_llm_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    root = os.environ.get("AEC_DEMO_ROOT", r"C:\Users\test\2026_aec_cptx_demo_dml")
    demo = os.path.join(root, "demos", "virtual_production_studio")
    return {
        "context": (
            f"VP HARD RAILS: repository root is exactly {root}; demo directory is exactly {demo}. "
            "Never resolve project prompts, skills, source, work, or assets under the Hermes profile directory. "
            "Use only the locked manifest and current phase. "
            "Create coherent phase-local assemblies through Rhino MCP; "
            "never one object per turn and never a whole-studio builder. "
            "All Rhino geometry mutations use mcp_rhino_run_csharp with the exact "
            "C# scaffold embedded in the current phase prompt. Python is read-only. "
            "Never use terminal, execute_code, run_command, "
            "editors, desktop file opens, or local script replay. Once mutation "
            "starts, do not patch/write script files. Preferred phase order is numeric "
            "NUMERIC_PASS -> fresh viewport -> local vision -> corrections/revalidate "
            "-> mcp_rhino_save_doc. After compaction re-read state, manifest, and "
            "current phase, then inspect Rhino before mutating. DML is advisory. "
            "C# RULE: copy the phase's tested Func<>/Action<> delegates; set "
            "var rdoc=doc; create Box(Plane.WorldXY, absolute Interval "
            "values), convert with ToBrep(), create ObjectAttributes before add, "
            "and treat every Objects.Add* result as Guid, never an integer index. "
            "Do not probe or substitute APIs. Any exception means zero progress. "
            "BLENDER HANDOFF: bake joined Rhino Mesh companions, save the .3dm, "
            "stay in the launcher-owned generic Blender scene, then load "
            "skills/blender_vp_production.py and call import_current_handoff(root, reset_scene=True). "
            "Never open or reuse a .blend; blender_assets/vp_studio_01.blend is output-only. OBJ, "
            "FBX, add-on probing, import_scene operators, and handwritten parsers "
            "are prohibited. The handoff must contain LED_ACTIVE_WALL at Z=0..288 in "
            "and LED_REAR_SUPPORT at Z=0..312 in. Always run import_3dm with replace_existing=True "
            "and assert_import_matches_source; a populated prior VP_STUDIO_RHINO collection is stale until proven otherwise. "
            "Rhino and Blender both use direct X,Y,Z axes. "
            "BLENDER PRODUCTION: cached payloads fall back to "
            "G:\\AEC-CPTX\\demos\\virtual_production_studio\\assets\\cache. "
            "Use skills/blender_vp_production.py and call apply_required_set_dressing(root) once. "
            "Require VP_SET_DRESSING_PASS categories=6 placements=27 before camera/render. It places three "
            "cameras, eight chairs, six monitors, six road cases, two complete LED soft-panel practicals, and "
            "two server racks. A standalone bare C-stand is prohibited. "
            "For any approved optional placement, call place_cached_asset(root, asset_key, exact_proxy_name). "
            "That helper owns measured fixed XYZ scale, real-world dimensions, and grounding; "
            "never calculate asset scale from proxy bounds and never call fit_to_proxy, resolve_cached_asset, "
            "or import_cached_asset directly. Full floor-standing C-stands and soft panels never replace "
            "overhead STAGE_LIGHT proxies. Then use "
            "setup_beauty_camera, and render_preview. setup_beauty_camera owns the "
            "unobstructed stage-wide presentation preset at (0,-588,144) in aimed at "
            "(-120,120,96) in; never substitute CAM_E, CAM_F, a computed scene-bounds "
            "center, or guessed coordinates. CAM_A is a secondary close-up only. "
            "Call remove_legacy_scene_debris first so vp_studio_01_export and old "
            "camera-test objects cannot overlap the validated handoff. "
            "Never invent camera matrices, Track-To "
            "constraints, test cubes, or iterative CAMERA FIX scripts."
            " PHASE BOUNDARY: after import_current_handoff succeeds, every mcp_rhino_* tool is permanently "
            "out of scope for this run. Blender owns the scene until VP_RENDER_PASS. After that, ComfyUI owns "
            "the final phase; never use Rhino to inspect, launch, or operate ComfyUI. "
            "COMFYUI FINAL: the registered terminal tool is available for the checked-in helper. Load skill "
            "comfyui/comfyui-cookbook, then use terminal "
            "from the demo directory and run exactly one command per turn: "
            "python skills/comfyui_vp_stylize.py --dry-run, followed after PASS by "
            "python skills/comfyui_vp_stylize.py. The checked-in helper owns endpoint "
            "inventory, upload, the fixed SDXL depth graph, queue, history polling, and download. "
            "Never use browser tools, Windows paths, curl, Invoke-RestMethod, handwritten JSON, "
            "or launch/install ComfyUI or models."
        )
    }


def on_pre_tool_call(**kwargs: Any) -> Optional[Dict[str, str]]:
    if not _active():
        return None
    tool = str(kwargs.get("tool_name") or "")
    args = kwargs.get("args") if isinstance(kwargs.get("args"), dict) else {}
    state = _state(kwargs)

    if state["workflow_phase"] != "rhino" and tool.startswith("mcp_rhino_"):
        return _block(
            "Rhino phase is permanently closed after the validated Blender handoff; "
            "continue with Blender MCP, or with the checked-in ComfyUI helper after VP_RENDER_PASS"
        )

    if tool.startswith("browser_"):
        return _block(
            "browser automation is prohibited for VP Studio; ComfyUI runs through the exact "
            "skills/comfyui_vp_stylize.py cookbook helper"
        )

    if tool in {
        "run",
        "mcp_rhino_run_command",
        "mcp_rhino_spawn_slot",
        "mcp_rhino_close_slot",
        "mcp_rhino_close_doc",
    }:
        return _block(f"{tool} is prohibited; preserve launcher-owned Rhino and use direct MCP APIs")

    if tool in {"mcp_cma_get_prompt", "mcp_daystrom_dml_get_prompt"}:
        return _block(
            "memory prompt lookup is not part of this demo; use mcp_cma_augment or mcp_daystrom_dml_query for advisory retrieval"
        )

    if tool in {"terminal", "execute_code"}:
        payload = json.dumps(args, ensure_ascii=False, default=str)
        command = str(args.get("command") or args.get("code") or "")
        if _COMFYUI_HELPER_COMMAND_RE.fullmatch(command):
            if not state["blender_render_ready"]:
                return _block(
                    "ComfyUI requires a composition-gated VP_RENDER_PASS from Blender; "
                    "repair materials, lighting, and the stage-wide camera in Blender first"
                )
            is_dry_run = "--dry-run" in command
            if not is_dry_run and not state["comfy_preflight_ready"]:
                return _block(
                    "run python skills/comfyui_vp_stylize.py --dry-run first and require COMFY_PREFLIGHT_PASS"
                )
            return None
        if _COMFYUI_IMPROVISATION_RE.search(payload):
            return _block(
                "handwritten ComfyUI REST calls and workflow JSON are prohibited; from the demo "
                "directory run exactly: python skills/comfyui_vp_stylize.py --dry-run, then "
                "python skills/comfyui_vp_stylize.py"
            )
        if _SHELL_APP_LAUNCH_RE.search(payload):
            return _block(
                "launching or opening Blender, Rhino, or ComfyUI from inside the demo is prohibited; "
                "use the launcher-owned MCP application and report a missing bridge as a blocker"
            )
        if _SHELL_LANGUAGE_EXEC_RE.search(payload) or "RunPythonScript" in payload:
            return _block("Python/C# execution outside Rhino MCP is prohibited")

    if tool == "mcp_blender_execute_blender_code":
        code = str(args.get("code") or "")
        if "grip_c_stand_kilianpohl" in code.lower():
            return _block(
                "a standalone bare C-stand is prohibited; use the required complete "
                "light_led_soft_panel_roy practical-light assemblies"
            )
        if _BLENDER_DIRECT_SCENE_IO_RE.search(code):
            return _block(
                "direct .blend open/save/link operations are prohibited; begin from the launcher-owned generic scene, "
                "call import_current_handoff, and save only with save_production_checkpoint"
            )
        if _BLENDER_PROHIBITED_HANDOFF_RE.search(code):
            return _block(
                "OBJ/FBX, Blender import add-ons, and handwritten mesh parsers are prohibited; "
                "follow prompts/07_phase_export_blender.md and execute skills/import_with_metadata.py"
            )
        if _BLENDER_DYNAMIC_ASSET_SCALE_RE.search(code) and not _BLENDER_APPROVED_ASSET_PLACEMENT_RE.search(code):
            return _block(
                "dynamic asset import or scaling is prohibited; load skills/blender_vp_production.py "
                "and call place_cached_asset(root, asset_key, exact_proxy_name)"
            )
        if _BLENDER_DIRECT_CAMERA_RENDER_RE.search(code) and not _BLENDER_APPROVED_CAMERA_RE.search(code):
            return _block(
                "direct camera transforms, constraints, temporary renders, and custom camera math are prohibited; "
                "load skills/blender_vp_production.py and call a manifest camera preset plus render_preview"
            )
        if _BLENDER_APPROVED_CAMERA_RE.search(code):
            if not state["blender_set_dressing_ready"] and not _BLENDER_REQUIRED_SET_DRESSING_RE.search(code):
                return _block(
                    "camera/render requires apply_required_set_dressing(root) and VP_SET_DRESSING_PASS first; "
                    "the beauty must contain the locked cameras, furniture, road cases, complete practical lights, and racks"
                )
            state["blender_camera_retries"] += 1
            if state["blender_camera_retries"] > 2:
                return _block(
                    "the manifest hero preview and one targeted correction are already spent; "
                    "accept the last validated render or report the remaining blocker"
                )
        if _BLENDER_CAMERA_LOOP_RE.search(code):
            return _block(
                "camera/render diagnostic scripts are prohibited; use a manifest camera preset once and permit one correction"
            )

    if tool in {"mcp_blender_get_viewport_screenshot", "vision_analyze"}:
        state["blender_visual_reviews"] += 1
        if state["blender_visual_reviews"] > 3:
            return _block(
                "Blender visual-review budget exhausted (handoff review, hero review, one correction); "
                "do not recapture an unchanged scene"
            )

    if tool in {"patch", "write_file"}:
        path = str(args.get("path") or args.get("file_path") or args.get("filename") or "")
        normalized_path = path.replace("\\", "/").lower()
        if normalized_path.endswith(".json") and (
            "comfy" in normalized_path or "workflow" in normalized_path
        ):
            return _block(
                "writing ComfyUI workflow JSON during the demo is prohibited; use the checked-in "
                "skills/comfyui_vp_stylize.py cookbook helper"
            )
        if normalized_path.endswith((
            "skills/import_with_metadata.py",
            "skills/blender_vp_production.py",
        )):
            return _block(
                "the checked-in Rhino-to-Blender importer is immutable during a demo; "
                "execute it exactly as specified in prompts/07_phase_export_blender.md"
            )
        if normalized_path.endswith((".py", ".cs", ".csx")):
            return _block(
                "writing Python or C# files is prohibited for VP Studio; keep bounded Rhino code inline in "
                "mcp_rhino_run_csharp and use only checked-in Blender helpers"
            )

    if tool in _MUTATION_TOOLS:
        script = _script(args)
        if not script.strip():
            return _block(f"{tool} requires a non-empty script argument")
        if _is_mutation(tool, args) and not state["document_ready"]:
            return _block("open source/vp_studio_01_template.3dm before any geometry mutation")
        if tool == "mcp_rhino_run_python" and _is_mutation(tool, args):
            return _block("Rhino geometry mutations must use the current phase's embedded C# scaffold via mcp_rhino_run_csharp")
        if _EXTERNAL_RHINO_SCRIPT_RE.search(script):
            return _block("external script replay/editor macros are prohibited; send bounded code inline through Rhino MCP")
        # Do not police turns, mutation counts, inspection cadence, or saving.
        # The original Cliff House succeeds by letting the agent recover. These
        # state values are telemetry only and must never trap that recovery.

    return None


def on_post_tool_call(**kwargs: Any) -> None:
    if not _active():
        return
    status = str(kwargs.get("status") or "ok").lower()
    if status != "ok" or kwargs.get("error_message"):
        return
    tool = str(kwargs.get("tool_name") or "")
    args = kwargs.get("args") if isinstance(kwargs.get("args"), dict) else {}
    state = _state(kwargs)
    raw_result = kwargs.get("result")
    result = _result_text(raw_result)

    # The router reports a completed MCP call even when Rhino printed a Python
    # or C# exception. Do not let a transport-level success advance rail state.
    if not _rhino_execution_succeeded(tool, raw_result):
        return

    if tool == "mcp_rhino_open_doc":
        state.update(
            total_mutations=0,
            phase_mutations=0,
            correction_mutations=0,
            review_started=False,
            numeric_pass=False,
            viewport_ready=False,
            vision_reviewed=False,
            saved=True,
            document_ready=True,
            blender_handoff_ready=False,
            blender_set_dressing_ready=False,
            blender_render_ready=False,
            comfy_preflight_ready=False,
            workflow_phase="rhino",
        )
    elif _is_mutation(tool, args):
        state["total_mutations"] += 1
        if state["review_started"]:
            state["correction_mutations"] += 1
        else:
            state["phase_mutations"] += 1
        state["numeric_pass"] = False
        state["viewport_ready"] = False
        state["saved"] = False
        state["blender_handoff_ready"] = False
    elif tool in _MUTATION_TOOLS and "NUMERIC_PASS" in result and "NUMERIC_FAIL" not in result:
        state["numeric_pass"] = True
        state["review_started"] = True
    elif tool == "mcp_rhino_get_viewport_image":
        state["viewport_ready"] = True
        # Hermes routes MCP ImageContent through the configured vision model
        # automatically; there may be no separate vision_analyze tool event.
        state["vision_reviewed"] = True
    elif tool == "mcp_rhino_run_python" and _CAPTURE_RE.search(_script(args)):
        state["viewport_ready"] = True
    elif tool == "vision_analyze":
        state["vision_reviewed"] = True
    elif tool == "mcp_rhino_save_doc":
        state["phase_mutations"] = 0
        state["correction_mutations"] = 0
        state["review_started"] = False
        state["numeric_pass"] = False
        state["viewport_ready"] = False
        state["vision_reviewed"] = False
        state["saved"] = True
    elif tool == "mcp_blender_execute_blender_code":
        code = str(args.get("code") or "")
        if "VP_HANDOFF_PASS" in result or (
            _BLENDER_CURRENT_HANDOFF_RE.search(code) and "VP_HANDOFF_READY" in result
        ):
            state["blender_handoff_ready"] = True
            state["blender_set_dressing_ready"] = False
            state["blender_camera_retries"] = 0
            state["blender_visual_reviews"] = 0
            state["blender_render_ready"] = False
            state["comfy_preflight_ready"] = False
            state["workflow_phase"] = "blender"
        if "VP_SET_DRESSING_PASS" in result:
            state["blender_set_dressing_ready"] = True
        if (
            "VP_RENDER_PASS" in result
            and "VP_RENDER_REJECT" not in result
            and state["blender_set_dressing_ready"]
        ):
            state["blender_render_ready"] = True
    elif tool in {"terminal", "execute_code"}:
        command = str(args.get("command") or args.get("code") or "")
        if _COMFYUI_HELPER_COMMAND_RE.fullmatch(command):
            if "COMFY_PREFLIGHT_PASS" in result:
                state["comfy_preflight_ready"] = True
                state["workflow_phase"] = "comfy"
            if "COMFY_OUTPUT_PASS" in result:
                state["workflow_phase"] = "complete"


def register(ctx: Any) -> None:
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
