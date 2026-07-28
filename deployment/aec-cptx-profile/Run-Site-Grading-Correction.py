from pathlib import Path
import os
import subprocess


here = Path(__file__).resolve().parent
repo = here.parents[1]
hermes_home = Path(os.environ["LOCALAPPDATA"]) / "hermes"
hermes_exe = hermes_home / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"
prompt = (here / "site-grading-correction.txt").read_text(encoding="utf-8")
log_path = (
    hermes_home
    / "profiles"
    / "aec-cptx"
    / "logs"
    / "site-grading-correction-console.log"
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
    "80",
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

raise SystemExit(result.returncode)
