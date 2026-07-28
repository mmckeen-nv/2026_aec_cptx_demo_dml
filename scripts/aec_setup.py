#!/usr/bin/env python3
"""Portable preflight and guided installer for the AEC CPTX demo.

Examples:
    python scripts/aec_setup.py --check --tier viewer
    python scripts/aec_setup.py --configure
    python scripts/aec_setup.py --install --tier agent
    python scripts/aec_setup.py --check --tier full --json

The installer never installs Rhino, model weights, or private Daystrom source
without an explicit prompt. Use --yes only in an environment where package
manager changes are already approved.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = ROOT / "config" / "demo.env.example"
ENV_FILE = ROOT / "config" / "demo.env"

TIERS = {
    "viewer": ("python", "blender"),
    "agent": ("python", "blender", "git", "uvx", "hermes", "gpu", "ollama", "ollama_models", "dml"),
    "summit": ("python", "git", "uvx", "hermes", "gpu", "ollama", "ollama_embedding", "dml"),
    "enhancement": ("python", "blender", "ffmpeg", "comfyui", "comfy_models"),
    "full": (
        "python", "blender", "ffmpeg", "git", "uvx", "hermes", "gpu",
        "ollama", "ollama_models", "dml", "comfyui", "comfy_models", "obs", "rhino",
    ),
}

DOCS = {
    "blender": "https://docs.blender.org/manual/en/latest/getting_started/installing/index.html",
    "uvx": "https://docs.astral.sh/uv/getting-started/installation/",
    "ollama": "https://docs.ollama.com/quickstart",
    "ollama_models": "Run: ollama pull qwen3-embedding:0.6b && ollama pull llama3:8b",
    "ollama_embedding": "Run: ollama pull qwen3-embedding:0.6b",
    "comfyui": "https://docs.comfy.org/comfy-cli/getting-started",
    "comfy_models": (
        "Install the shared demo SDXL, depth ControlNet, and FLUX.2 Klein model set; "
        "on Windows run scripts\\install_comfy_flux2_models.ps1."
    ),
    "hermes": "https://hermes-agent.nousresearch.com/docs/",
    "rhino": "https://www.rhino3d.com/download/",
}


@dataclass
class Result:
    component: str
    ok: bool
    detail: str
    required: bool = True


def load_env(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def executable(name: str, env_name: str | None = None, candidates: Iterable[Path] = ()) -> str | None:
    configured = os.environ.get(env_name or "") if env_name else None
    if configured and Path(configured).expanduser().exists():
        return str(Path(configured).expanduser())
    found = shutil.which(name)
    if found:
        return found
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def command_version(command: list[str]) -> str:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=15)
        output = (proc.stdout or proc.stderr).strip().splitlines()
        return output[0] if proc.returncode == 0 and output else "available"
    except Exception as exc:
        return f"unusable: {exc}"


def http_ok(url: str) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return 200 <= response.status < 300, f"HTTP {response.status}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, str(exc)


def http_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return {}


def common_windows() -> dict[str, list[Path]]:
    local = Path(os.environ.get("LOCALAPPDATA", "C:/__not_configured__"))
    program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
    return {
        "blender": sorted((program_files / "Blender Foundation").glob("Blender */blender.exe"), reverse=True),
        "rhino": [program_files / "Rhino 8" / "System" / "Rhino.exe"],
        "hermes": [local / "hermes" / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"],
        "obs": [program_files / "obs-studio" / "bin" / "64bit" / "obs64.exe"],
    }


def run_checks(tier: str) -> list[Result]:
    required = set(TIERS[tier])
    win = common_windows() if os.name == "nt" else {"blender": [], "rhino": [], "hermes": []}
    results: list[Result] = []

    def add(component: str, ok: bool, detail: str) -> None:
        results.append(Result(component, ok, detail, component in required))

    add("python", sys.version_info >= (3, 10), platform.python_version())
    for component, command, env_name in (
        ("blender", "blender", "BLENDER_BIN"),
        ("ffmpeg", "ffmpeg", "FFMPEG_BIN"),
        ("git", "git", None),
        ("uvx", "uvx", None),
        ("hermes", "hermes", None),
        ("obs", "obs", None),
        ("rhino", "Rhino", None),
    ):
        found = executable(command, env_name, win.get(component, []))
        version_flag = [found, "--version"] if found else []
        add(component, bool(found), command_version(version_flag) if found else f"not found; {DOCS.get(component, 'configure PATH')}")

    gpu = executable("nvidia-smi")
    add("gpu", bool(gpu), command_version([gpu, "--query-gpu=name", "--format=csv,noheader"]) if gpu else "nvidia-smi not found")

    ollama = executable("ollama")
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    ollama_live, ollama_detail = http_ok(f"{ollama_url}/api/version")
    add("ollama", bool(ollama and ollama_live), f"{ollama or 'CLI missing'}; {ollama_detail}")
    installed_models = ""
    if ollama:
        try:
            installed_models = subprocess.run(
                [ollama, "list"], capture_output=True, text=True, timeout=15
            ).stdout.lower()
        except Exception:
            pass
    required_models = ("qwen3-embedding:0.6b", "llama3:8b")
    missing_models = [model for model in required_models if model not in installed_models]
    add(
        "ollama_models",
        not missing_models,
        "installed" if not missing_models else "missing: " + ", ".join(missing_models),
    )
    embedding_model = "qwen3-embedding:0.6b"
    add(
        "ollama_embedding",
        embedding_model in installed_models,
        "installed" if embedding_model in installed_models else f"missing: {embedding_model}",
    )

    dml_source = Path(os.environ.get("DML_SOURCE_DIR", "")).expanduser()
    dml_ok = bool(str(dml_source) not in ("", ".") and (dml_source / "pyproject.toml").exists())
    add("dml", dml_ok, str(dml_source) if dml_ok else "set DML_SOURCE_DIR to a Daystrom DML checkout")

    comfy_url = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
    comfy_ok, comfy_detail = http_ok(f"{comfy_url}/system_stats")
    add("comfyui", comfy_ok, f"{comfy_url}; {comfy_detail}")
    object_info = http_json(f"{comfy_url}/object_info") if comfy_ok else {}
    checkpoints = (
        object_info.get("CheckpointLoaderSimple", {}).get("input", {})
        .get("required", {}).get("ckpt_name", [[]])[0]
    ) or []
    controlnets = (
        object_info.get("ControlNetLoader", {}).get("input", {})
        .get("required", {}).get("control_net_name", [[]])[0]
    ) or []
    depth_models = [name for name in controlnets if "depth" in str(name).lower()]
    unets = (
        object_info.get("UNETLoader", {}).get("input", {})
        .get("required", {}).get("unet_name", [[]])[0]
    ) or []
    text_encoders = (
        object_info.get("CLIPLoader", {}).get("input", {})
        .get("required", {}).get("clip_name", [[]])[0]
    ) or []
    vaes = (
        object_info.get("VAELoader", {}).get("input", {})
        .get("required", {}).get("vae_name", [[]])[0]
    ) or []
    required_checkpoint = "sd_xl_base_1.0.safetensors"
    required_flux = "flux-2-klein-base-4b-fp8.safetensors"
    required_clip = "qwen_3_4b.safetensors"
    required_vae = "flux2-vae.safetensors"
    comfy_models_ok = bool(
        required_checkpoint in checkpoints
        and depth_models
        and required_flux in unets
        and required_clip in text_encoders
        and required_vae in vaes
    )
    add(
        "comfy_models",
        comfy_models_ok,
        f"sdxl={required_checkpoint in checkpoints}, depth_controlnets={len(depth_models)}, "
        f"flux={required_flux in unets}, flux_clip={required_clip in text_encoders}, "
        f"flux_vae={required_vae in vaes}",
    )
    return results


def install_command(component: str) -> list[str] | None:
    system = platform.system().lower()
    if system == "windows":
        ids = {
            "blender": "BlenderFoundation.Blender",
            "ffmpeg": "Gyan.FFmpeg",
            "obs": "OBSProject.OBSStudio",
            "ollama": "Ollama.Ollama",
            "uvx": "astral-sh.uv",
        }
        return ["winget", "install", "--id", ids[component], "-e"] if component in ids else None
    if system == "darwin":
        formula = {"ffmpeg": "ffmpeg", "uvx": "uv", "ollama": "ollama"}
        casks = {"blender": "blender", "obs": "obs"}
        if component in formula:
            return ["brew", "install", formula[component]]
        if component in casks:
            return ["brew", "install", "--cask", casks[component]]
        return None
    if component == "blender" and shutil.which("snap"):
        return ["sudo", "snap", "install", "blender", "--classic"]
    if component in {"ffmpeg", "obs"} and shutil.which("apt-get"):
        package = "ffmpeg" if component == "ffmpeg" else "obs-studio"
        return ["sudo", "apt-get", "install", "-y", package]
    if component == "uvx":
        return ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]
    if component == "ollama":
        return ["sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"]
    return None


def confirm(prompt: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    return input(f"{prompt} [y/N] ").strip().lower() in {"y", "yes"}


def install_missing(tier: str, assume_yes: bool) -> None:
    missing = [r.component for r in run_checks(tier) if r.required and not r.ok]
    for component in missing:
        if component == "ollama_models" and executable("ollama"):
            for model in ("qwen3-embedding:0.6b", "llama3:8b"):
                if confirm(f"Download required Ollama model {model}?", assume_yes):
                    subprocess.run(["ollama", "pull", model], check=True)
            continue
        if component == "ollama_embedding" and executable("ollama"):
            model = "qwen3-embedding:0.6b"
            if confirm(f"Download required Ollama embedding model {model}?", assume_yes):
                subprocess.run(["ollama", "pull", model], check=True)
            continue
        command = install_command(component)
        if not command:
            print(f"SKIP {component}: manual configuration required. {DOCS.get(component, '')}")
            continue
        if confirm(f"Run: {' '.join(command)}?", assume_yes):
            subprocess.run(command, check=True)

    if "comfyui" in TIERS[tier] and not any(r.ok for r in run_checks(tier) if r.component == "comfyui"):
        if executable("uvx") and confirm("Install comfy-cli and launch its official local setup wizard?", assume_yes):
            subprocess.run(["uv", "tool", "install", "comfy-cli"], check=True)
            subprocess.run(["comfy", "setup", "--where", "local", "--project-dir", str(ROOT / "comfyui")], check=True)


def configure() -> None:
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if ENV_FILE.exists() and not confirm(f"Overwrite {ENV_FILE}?", False):
        return
    values = {}
    for raw in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, default = raw.split("=", 1)
        shown = default or "auto-detect"
        value = input(f"{key} [{shown}]: ").strip() or default
        values[key] = value
    ENV_FILE.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n", encoding="utf-8")
    print(f"Wrote user-local configuration: {ENV_FILE}")


def print_results(results: list[Result], as_json: bool) -> None:
    if as_json:
        print(json.dumps([asdict(item) for item in results], indent=2))
        return
    for item in results:
        status = "PASS" if item.ok else ("FAIL" if item.required else "INFO")
        print(f"{status:4} {item.component:10} {item.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=TIERS, default="viewer")
    parser.add_argument("--check", action="store_true", help="Run preflight checks (default action).")
    parser.add_argument("--install", action="store_true", help="Prompt to install missing supported dependencies.")
    parser.add_argument("--configure", action="store_true", help="Create ignored config/demo.env interactively.")
    parser.add_argument("--yes", action="store_true", help="Approve supported package-manager commands.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable preflight results.")
    args = parser.parse_args()

    load_env()
    if args.configure:
        configure()
        load_env()
    if args.install:
        install_missing(args.tier, args.yes)
    results = run_checks(args.tier)
    print_results(results, args.json)
    return 1 if any(item.required and not item.ok for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
