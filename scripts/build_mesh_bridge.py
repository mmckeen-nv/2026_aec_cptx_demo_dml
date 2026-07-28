"""Build a deterministic Blender mesh bridge from a Rhino 3DM file."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def load_import_helper(repo_root: Path):
    helper_path = repo_root / "skills" / "import_with_metadata.py"
    spec = importlib.util.spec_from_file_location("aec_import_with_metadata", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load mesh bridge helper: {helper_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-objects", type=int)
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"MESH_BRIDGE_FAIL missing source: {source}")

    repo_root = Path(__file__).resolve().parents[1]
    helper = load_import_helper(repo_root)
    result = helper.build_mesh_bridge(str(source), str(output))
    if args.expect_objects is not None and result["objects"] != args.expect_objects:
        raise SystemExit(
            f"MESH_BRIDGE_FAIL expected={args.expect_objects} actual={result['objects']}"
        )
    if result["skipped"]:
        raise SystemExit(f"MESH_BRIDGE_FAIL skipped={json.dumps(result['skipped'])}")
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit(f"MESH_BRIDGE_FAIL empty output: {output}")

    print(
        "MESH_BRIDGE_PASS "
        + json.dumps(
            {
                "source": str(source),
                "output": str(output),
                "objects": result["objects"],
                "bytes": output.stat().st_size,
                "sha256": result["source"]["sha256"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
