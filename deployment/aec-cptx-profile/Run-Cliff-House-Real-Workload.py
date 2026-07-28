from pathlib import Path
import os
import subprocess

here = Path(__file__).resolve().parent
hermes_home = Path(os.environ["LOCALAPPDATA"]) / "hermes"
hermes_exe = hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"
prompt = (here / "cliff-house-real-workload.txt").read_text(encoding="utf-8")
log_path = hermes_home / "profiles" / "aec-cptx" / "logs" / "cliff-house-real-workload-console.log"
hermes_python = hermes_home / "hermes-agent" / "venv" / "Scripts" / "python.exe"

subprocess.run(
    [str(hermes_python), str(repo_root / "scripts" / "validate_cliff_house_geometry_contract.py")],
    cwd=repo_root,
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

with log_path.open("w", encoding="utf-8", buffering=1) as log:
    log.write("Starting real Cliff House workload.\n")
    result = subprocess.run(
        command,
        cwd=here.parents[1],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log.write(f"\nHermes exited with code {result.returncode}.\n")

raise SystemExit(result.returncode)
