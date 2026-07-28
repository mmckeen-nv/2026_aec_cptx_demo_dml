from pathlib import Path
import os
import subprocess

from single_frame_preflight import annotate_preflight, ensure_rhino3dm

here = Path(__file__).resolve().parent
repo = here.parents[1]
hermes_home = Path(os.environ["LOCALAPPDATA"]) / "hermes"
hermes_exe = hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"
hermes_python = hermes_home / "hermes-agent" / "venv" / "Scripts" / "python.exe"
prompt = (here / "single-frame-cleanup.txt").read_text(encoding="utf-8")
log_path = hermes_home / "profiles" / "aec-cptx" / "logs" / "single-frame-cleanup-console.log"
preflight_path = repo / "aa_demo_versions" / "cliff_house_single_frame_01" / "benchmark_preflight.json"

rhino3dm_status = ensure_rhino3dm(hermes_python)

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
    "60",
    "--yolo",
    "--accept-hooks",
]

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

if result.returncode == 0:
    annotate_preflight(preflight_path, rhino3dm_status)

raise SystemExit(result.returncode)
