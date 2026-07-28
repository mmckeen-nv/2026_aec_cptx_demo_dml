"""Deterministic host dependency checks for the single-frame benchmark."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import subprocess
from typing import Any


RHINO3DM_REQUIREMENT = "rhino3dm==8.17.0"


def _probe_rhino3dm(python_exe: Path) -> dict[str, Any]:
    probe = (
        "import json, rhino3dm; "
        "model=rhino3dm.File3dm(); "
        "assert model is not None; "
        "print(json.dumps({'status':'PASS','version':rhino3dm.__version__,"
        "'python':__import__('sys').executable}))"
    )
    result = subprocess.run(
        [str(python_exe), "-c", probe],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "rhino3dm probe failed")
    return json.loads(result.stdout.strip().splitlines()[-1])


def ensure_rhino3dm(python_exe: Path) -> dict[str, Any]:
    """Verify rhino3dm in Hermes' Python, installing the pinned build if absent."""
    installed = False
    expected_version = RHINO3DM_REQUIREMENT.partition("==")[2]
    try:
        result = _probe_rhino3dm(python_exe)
        if result["version"] != expected_version:
            raise RuntimeError(
                f"rhino3dm version mismatch: expected {expected_version}, got {result['version']}"
            )
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError):
        install = subprocess.run(
            [
                str(python_exe),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                RHINO3DM_REQUIREMENT,
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if install.returncode != 0:
            raise RuntimeError(
                "Unable to install the benchmark rhino3dm dependency: "
                + (install.stderr.strip() or install.stdout.strip())
            )
        installed = True
        result = _probe_rhino3dm(python_exe)

    if result["version"] != expected_version:
        raise RuntimeError(
            f"rhino3dm version mismatch: expected {RHINO3DM_REQUIREMENT}, got {result['version']}"
        )
    result["installed_by_preflight"] = installed
    result["requirement"] = RHINO3DM_REQUIREMENT
    return result


def annotate_preflight(preflight_path: Path, dependency: dict[str, Any]) -> None:
    """Merge dependency evidence into the scene preflight artifact."""
    report: dict[str, Any] = {}
    if preflight_path.exists():
        report = json.loads(preflight_path.read_text(encoding="utf-8"))
    report.setdefault("dependencies", {})["rhino3dm"] = dependency
    report["dependency_verification_timestamp"] = datetime.now().astimezone().isoformat()
    preflight_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
