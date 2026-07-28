from pathlib import Path
import os
import subprocess

here = Path(__file__).resolve().parent
repo_root = here.parents[1]
hermes_home = Path(os.environ["LOCALAPPDATA"]) / "hermes"
hermes_exe = hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"
prompt = (here / "cliff-house-continue-workload.txt").read_text(encoding="utf-8")
log_path = hermes_home / "profiles" / "aec-cptx" / "logs" / "cliff-house-continuation-console.log"

env = os.environ.copy()
env["HERMES_HOME"] = str(hermes_home)
env["HERMES_PROFILE"] = "aec-cptx"

command = [
    str(hermes_exe),
    "-p",
    "aec-cptx",
    "chat",
    "--resume",
    "20260726_160512_e0b2e6",
    "-q",
    prompt,
    "--max-turns",
    "120",
    "--yolo",
    "--accept-hooks",
]

with log_path.open("w", encoding="utf-8", buffering=1) as log:
    log.write("Resuming real Cliff House workload from the 41-object checkpoint.\n")
    result = subprocess.run(
        command,
        cwd=repo_root,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log.write(f"\nHermes continuation exited with code {result.returncode}.\n")

raise SystemExit(result.returncode)
