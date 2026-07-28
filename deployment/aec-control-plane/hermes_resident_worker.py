"""Resident Hermes runner for the local AEC control plane.

The worker keeps the last Hermes session resumable and accepts JSON jobs from a
loopback-only filesystem queue. Preflight belongs to the parent launcher and is
therefore paid once per worker lifetime, not once per user instruction.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Any
import uuid


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SESSION_RE = re.compile(r"^\s*Session:\s*(\S+)", re.MULTILINE)
WORKER_VERSION = "warm-agent-v5"
ATOMIC_JSON_LOCK = threading.Lock()
AUTOMATIC_PROMPT_REQUIRED_SNIPPETS = (
    "`L1_east`: `(5,3,0.25)` to `(17,14,4)`",
    "`L3_roof_slab`: `(-1,-13.5,11.5)` to `(15,4.5,12.3)`",
    "MeshingParameters.QualityRenderMesh",
    "Do not access",
    "FindByLayer(layerName)",
    "Do not call any Rhino viewport-image or camera tool",
)


def register_resident_aec_controller() -> None:
    """Register repo-owned automatic rails without changing manual Hermes."""
    from hermes_cli.plugins import PluginContext, PluginManifest, get_plugin_manager

    manager = get_plugin_manager()
    if getattr(manager, "_resident_aec_controller_registered", False):
        return
    repo_root = Path(
        os.environ.get("AEC_DEMO_ROOT") or os.getcwd()
    ).resolve()
    module_path = (
        repo_root
        / "deployment"
        / "plugins"
        / "aec_demo_controller"
        / "__init__.py"
    )
    if not module_path.is_file():
        raise RuntimeError(f"AEC controller plugin source missing: {module_path}")
    spec = importlib.util.spec_from_file_location(
        "_resident_aec_demo_controller",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load AEC controller plugin: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = PluginManifest(
        name="aec_demo_controller",
        version="resident",
        description="Resident-only AEC automatic execution rails",
        key="aec_demo_controller",
        source="project",
        path=str(module_path.parent),
    )
    module.register(PluginContext(manifest, manager))
    setattr(manager, "_resident_aec_controller_registered", True)


class WarmHermesRuntime:
    """One in-process AIAgent with MCP connections reused across jobs."""

    def __init__(self) -> None:
        os.environ["HERMES_YOLO_MODE"] = "1"
        os.environ["HERMES_ACCEPT_HOOKS"] = "1"
        os.environ["HERMES_SESSION_SOURCE"] = "tool"
        # Child processes inherit this marker. Legacy one-shot launchers use it
        # to refuse accidental Hermes-within-Hermes execution while preserving
        # their normal desktop/manual behavior.
        os.environ["AEC_RESIDENT_HERMES"] = "1"

        from gateway.session_context import declare_stateless_channel
        from hermes_cli.config import load_config
        from hermes_cli.fallback_config import get_fallback_chain
        from hermes_cli.plugins import discover_plugins
        from hermes_cli.runtime_provider import resolve_runtime_provider
        from hermes_cli.tools_config import _get_platform_tools
        from hermes_logging import setup_logging
        from hermes_state import SessionDB
        from run_agent import AIAgent
        from tools.mcp_tool import discover_mcp_tools

        setup_logging(mode="cli")
        declare_stateless_channel()
        # The normal `hermes` CLI performs both of these steps before it
        # constructs AIAgent.  The resident embeds AIAgent directly, so
        # skipping them silently produced a warm agent with only built-in CLI
        # tools: the profile listed Rhino and Blender, but neither server had
        # registered its actual tool definitions.
        discover_plugins()
        register_resident_aec_controller()
        discovered_mcp_tools = set(discover_mcp_tools())
        cfg = load_config()
        model_cfg = cfg.get("model") or {}
        model = (
            (model_cfg.get("default") or model_cfg.get("model") or "")
            if isinstance(model_cfg, dict)
            else str(model_cfg)
        )
        provider = (
            str(model_cfg.get("provider") or "").strip()
            if isinstance(model_cfg, dict)
            else ""
        )
        runtime = resolve_runtime_provider(
            requested=provider or None,
            target_model=model or None,
        )
        self.session_db = SessionDB()
        enabled_toolsets = sorted(_get_platform_tools(cfg, "cli"))
        required_mcp_tools = {
            "mcp__rhino__run_csharp",
            "mcp__blender__execute_blender_code",
        }
        missing_mcp_tools = sorted(required_mcp_tools - discovered_mcp_tools)
        if missing_mcp_tools:
            raise RuntimeError(
                "Resident Hermes MCP registration incomplete; missing "
                + ", ".join(missing_mcp_tools)
            )
        self.discovered_mcp_tools = sorted(discovered_mcp_tools)
        self.agent = AIAgent(
            api_key=runtime.get("api_key"),
            base_url=runtime.get("base_url"),
            provider=runtime.get("provider"),
            api_mode=runtime.get("api_mode"),
            model=model,
            enabled_toolsets=enabled_toolsets,
            quiet_mode=True,
            platform="cli",
            session_db=self.session_db,
            credential_pool=runtime.get("credential_pool"),
            fallback_model=get_fallback_chain(cfg) or None,
            max_iterations=120,
            clarify_callback=lambda _question, _choices=None: (
                "Use the safest reasonable default and continue."
            ),
        )
        self.agent.suppress_status_output = True
        self.agent.stream_delta_callback = None
        self.agent.tool_gen_callback = None
        self.history: list[dict[str, Any]] = []

    @property
    def session_id(self) -> str:
        return str(self.agent.session_id)

    def rotate_session(self) -> None:
        """Clear model history without rebuilding plugins or MCP clients."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_session_id = f"{timestamp}_{uuid.uuid4().hex[:6]}"
        try:
            self.session_db.end_session(self.agent.session_id, "new_session")
        except Exception:
            pass
        self.agent.session_id = new_session_id
        self.agent.session_start = datetime.now()
        self.agent.reset_session_state()
        if hasattr(self.agent, "_last_flushed_db_idx"):
            self.agent._last_flushed_db_idx = 0
        if hasattr(self.agent, "_invalidate_system_prompt"):
            self.agent._invalidate_system_prompt()
        try:
            self.agent._session_db_created = False
            self.session_db.create_session(
                session_id=new_session_id,
                source="tool",
                model=self.agent.model,
                model_config={"max_iterations": 120},
            )
            self.agent._session_db_created = True
        except Exception:
            pass
        try:
            manager = getattr(self.agent, "_memory_manager", None)
            if manager is not None:
                manager.on_session_switch(new_session_id, reset=True)
        except Exception:
            pass
        os.environ["HERMES_SESSION_ID"] = new_session_id
        self.history = []

    @staticmethod
    def _called_tool_names(messages: Any) -> list[str]:
        names: list[str] = []
        if not isinstance(messages, list):
            return names
        for message in messages:
            if not isinstance(message, dict):
                continue
            tool_name = message.get("tool_name")
            if tool_name:
                names.append(str(tool_name))
            tool_calls = message.get("tool_calls")
            if not isinstance(tool_calls, list):
                continue
            for call in tool_calls:
                if not isinstance(call, dict):
                    continue
                function = call.get("function")
                if isinstance(function, dict) and function.get("name"):
                    names.append(str(function["name"]))
                elif call.get("name"):
                    names.append(str(call["name"]))
        return names

    def run(
        self,
        prompt: str,
        *,
        fresh: bool,
        require_rhino_start: bool = False,
    ) -> tuple[int, str, list[str]]:
        if fresh and self.history:
            self.rotate_session()
        result = self.agent.run_conversation(
            prompt,
            conversation_history=[] if fresh else self.history,
        )
        messages = result.get("messages")
        if isinstance(messages, list):
            self.history = messages
        called_tools = self._called_tool_names(messages)
        response = str(result.get("final_response") or "")
        if response:
            print(response, flush=True)
        completed = bool(result.get("completed", True)) and not result.get("failed")
        rhino_run_csharp_names = {
            "mcp__rhino__run_csharp",  # Hermes-native MCP projection
            "mcp.rhino.run_csharp",    # Codex app-server MCP projection
        }
        if require_rhino_start and not rhino_run_csharp_names.intersection(called_tools):
            completed = False
            response = (
                "Automatic run failed before Rhino construction: no "
                "mcp__rhino__run_csharp call was executed. "
                + response
            ).strip()
        return (0 if completed else 1, response, called_tools)

    def close(self) -> None:
        try:
            self.agent.shutdown_memory_provider(self.history)
        except Exception:
            pass
        try:
            self.agent.close()
        finally:
            self.session_db.close()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    # Heartbeat and job-completion paths may publish state concurrently. A
    # shared `.tmp` filename lets one writer replace/delete the other writer's
    # staging file, which can terminate an otherwise healthy resident after a
    # completed run. Give every write its own staging path while retaining the
    # atomic replace contract for readers.
    temporary = path.with_name(
        f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False),
            encoding="utf-8",
        )
        # Windows can briefly deny concurrent replacement of the same target,
        # even when each writer owns a unique staging file. Serialize resident
        # threads and tolerate a short collision with an external controller.
        with ATOMIC_JSON_LOCK:
            for attempt in range(20):
                try:
                    os.replace(temporary, path)
                    break
                except PermissionError:
                    if attempt == 19:
                        raise
                    time.sleep(0.01 * (attempt + 1))
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def validate_automatic_prompt(prompt: str) -> None:
    missing = [
        snippet for snippet in AUTOMATIC_PROMPT_REQUIRED_SNIPPETS
        if snippet not in prompt
    ]
    if missing:
        raise ValueError(
            "Automatic-run prompt contract is incomplete; missing: "
            + ", ".join(missing)
        )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser()
    parser.add_argument("--hermes-exe", required=True)
    parser.add_argument("--profile", default="aec-cptx")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--queue-dir", required=True)
    parser.add_argument("--initial-prompt-file")
    parser.add_argument("--start-idle", action="store_true")
    args = parser.parse_args()

    # `hermes -p <name>` switches HERMES_HOME to the named profile before
    # loading configuration. The resident worker runs Hermes in-process, so it
    # must perform that profile switch itself or load the global fallback model.
    hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).resolve()
    profile_home = hermes_home
    if hermes_home.name.lower() != args.profile.lower():
        candidate = hermes_home / "profiles" / args.profile
        if candidate.is_dir():
            profile_home = candidate
    os.environ["HERMES_HOME"] = str(profile_home)
    os.environ["HERMES_PROFILE"] = args.profile
    os.environ.setdefault("AEC_DEMO_ROOT", str(Path(args.repo).resolve()))
    os.environ.setdefault("AEC_DEMO_ID", "cliff-house-01")
    os.environ.setdefault(
        "AEC_DEMO_CONTROLLER_LOG_DIR",
        str(profile_home / "logs"),
    )

    queue_dir = Path(args.queue_dir).resolve()
    queue_dir.mkdir(parents=True, exist_ok=True)
    state_path = queue_dir / "resident-agent.json"
    lock_path = queue_dir / "resident-agent.lock"
    stop_path = queue_dir / "resident-agent.stop"

    if state_path.exists():
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8-sig"))
            if process_alive(int(previous.get("pid", 0))):
                print(f"Resident Hermes worker already active as PID {previous['pid']}.", flush=True)
                return 23
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            lock_path.unlink()
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError:
            print("Unable to acquire the resident Hermes worker lock.", file=sys.stderr, flush=True)
            return 24
    os.write(lock_fd, str(os.getpid()).encode("ascii"))
    os.close(lock_fd)

    stopping = False
    session_id: str | None = None
    current_job_id: str | None = None
    current_job_started_at: float | None = None
    last_job_id: str | None = None
    last_job_started_at: float | None = None
    last_job_completed_at: float | None = None

    def write_state(status: str, **extra: Any) -> None:
        atomic_json(
            state_path,
            {
                "pid": os.getpid(),
                "status": status,
                "session_id": session_id,
                "updated_at": time.time(),
                "job_id": current_job_id,
                "job_started_at": current_job_started_at,
                "last_job_id": last_job_id,
                "last_job_started_at": last_job_started_at,
                "last_job_completed_at": last_job_completed_at,
                "worker_version": WORKER_VERSION,
                **extra,
            },
        )

    def request_stop(_signum: int, _frame: Any) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    runtime: WarmHermesRuntime | None = None

    resting_status = "idle"

    def run_turn(prompt: str, job_id: str, action: str = "query") -> int:
        nonlocal runtime
        nonlocal session_id, current_job_id, current_job_started_at
        nonlocal last_job_id, last_job_started_at, last_job_completed_at
        nonlocal resting_status
        if action == "automatic":
            validate_automatic_prompt(prompt)
        prior_action = os.environ.get("AEC_DEMO_ACTION")
        os.environ["AEC_DEMO_ACTION"] = action
        if runtime is None:
            runtime = WarmHermesRuntime()
            session_id = runtime.session_id
        current_job_id = job_id
        current_job_started_at = time.time()
        write_state("running", prompt_preview=prompt[:180])
        try:
            code, response, called_tools = runtime.run(
                prompt,
                fresh=action in {"automatic", "reset"},
                require_rhino_start=action == "automatic",
            )
        finally:
            if prior_action is None:
                os.environ.pop("AEC_DEMO_ACTION", None)
            else:
                os.environ["AEC_DEMO_ACTION"] = prior_action
        session_id = runtime.session_id
        last_job_id = current_job_id
        last_job_started_at = current_job_started_at
        last_job_completed_at = time.time()
        current_job_id = None
        current_job_started_at = None
        resting_status = "idle" if code == 0 else "error"
        write_state(
            resting_status,
            last_exit_code=code,
            last_error=response[-1200:] if code else None,
            last_tool_calls=called_tools[-20:],
            mcp_tool_count=len(runtime.discovered_mcp_tools),
        )
        return code

    try:
        if args.start_idle:
            write_state("idle", preflight_complete=True)
        else:
            if not args.initial_prompt_file:
                raise ValueError("--initial-prompt-file is required unless --start-idle is used.")
            initial_path = Path(args.initial_prompt_file)
            initial_prompt = initial_path.read_text(encoding="utf-8-sig").strip()
            if not initial_prompt:
                raise ValueError("Initial resident Hermes prompt is empty.")
            run_turn(initial_prompt, "initial", "automatic")
        last_heartbeat = 0.0
        while not stopping and not stop_path.exists():
            jobs = sorted(queue_dir.glob("job-*.json"), key=lambda item: item.stat().st_mtime_ns)
            if jobs:
                job_path = jobs[0]
                processing = job_path.with_suffix(".processing")
                try:
                    os.replace(job_path, processing)
                    payload = json.loads(processing.read_text(encoding="utf-8-sig"))
                    prompt = str(payload.get("prompt", "")).strip()
                    job_id = str(payload.get("id", processing.stem))
                    action = str(payload.get("action", "query")).strip().lower()
                    if prompt:
                        run_turn(prompt, job_id, action)
                    processing.unlink(missing_ok=True)
                except Exception as error:  # keep the resident worker recoverable
                    print(f"Resident job failed: {error}", file=sys.stderr, flush=True)
                    write_state("error", error=str(error))
                    processing.unlink(missing_ok=True)
                continue
            now = time.time()
            if now - last_heartbeat >= 5:
                write_state(resting_status)
                last_heartbeat = now
            time.sleep(0.4)
    finally:
        if runtime is not None:
            runtime.close()
        write_state("stopped")
        lock_path.unlink(missing_ok=True)
        stop_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
