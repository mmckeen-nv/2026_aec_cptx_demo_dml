from datetime import datetime
import json
from pathlib import Path
import os
import subprocess

from single_frame_preflight import annotate_preflight, ensure_rhino3dm

here = Path(__file__).resolve().parent
repo = here.parents[1]
project = repo / "aa_demo_versions" / "cliff_house_single_frame_01"
project.mkdir(parents=True, exist_ok=True)
timeline = project / "benchmark_timeline.jsonl"
preflight_path = project / "benchmark_preflight.json"

hermes_home = Path(os.environ["LOCALAPPDATA"]) / "hermes"
hermes_exe = hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"
hermes_python = hermes_home / "hermes-agent" / "venv" / "Scripts" / "python.exe"
prompt = (here / "single-frame-benchmark.txt").read_text(encoding="utf-8")
log_path = hermes_home / "profiles" / "aec-cptx" / "logs" / "single-frame-benchmark-console.log"

rhino3dm_status = ensure_rhino3dm(hermes_python)
annotate_preflight(preflight_path, rhino3dm_status)
subprocess.run(
    [str(hermes_python), str(repo / "scripts" / "validate_cliff_house_geometry_contract.py")],
    cwd=repo,
    check=True,
)

env = os.environ.copy()
env["HERMES_HOME"] = str(hermes_home)
env["HERMES_PROFILE"] = "aec-cptx"

command = [
    str(hermes_exe),
    "-p",
    "aec-cptx",
    "chat",
    "-q",
    prompt,
    "--max-turns",
    "120",
    "--yolo",
    "--accept-hooks",
]

with timeline.open("a", encoding="utf-8") as timing:
    timing.write(json.dumps({"event": "process_start", "timestamp": datetime.now().astimezone().isoformat()}) + "\n")

with log_path.open("w", encoding="utf-8", buffering=1) as log:
    result = subprocess.run(
        command,
        cwd=repo,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log.write(f"\nHermes exited with code {result.returncode}.\n")

with timeline.open("a", encoding="utf-8") as timing:
    timing.write(
        json.dumps(
            {
                "event": "process_end",
                "timestamp": datetime.now().astimezone().isoformat(),
                "exit_code": result.returncode,
            }
        )
        + "\n"
    )

raise SystemExit(result.returncode)
