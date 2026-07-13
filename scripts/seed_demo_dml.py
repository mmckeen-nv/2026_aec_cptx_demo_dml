"""Seed durable, repository-owned demo knowledge into isolated DML stores."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from daystrom_dml.dml_adapter import DMLAdapter


def seed(config: Path, storage: Path, knowledge: Path) -> dict[str, object]:
    files = sorted(knowledge.glob("*.md")) if knowledge.is_dir() else []
    storage.mkdir(parents=True, exist_ok=True)
    marker_path = storage / ".aec-demo-seed.json"
    prior = {}
    if marker_path.exists():
        try:
            prior = json.loads(marker_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            prior = {}
    hashes = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    changed = [path for path in files if prior.get(str(path.resolve())) != hashes[str(path.resolve())]]
    if not changed:
        return {"files": 0, "current": len(files), "storage": str(storage)}

    adapter = DMLAdapter(
        config_path=str(config),
        config_overrides={"storage_dir": str(storage)},
        start_aging_loop=False,
    )
    try:
        for path in changed:
            adapter.ingest(path.read_text(encoding="utf-8"), meta={"doc_path": str(path.resolve())})
    finally:
        adapter.close()
    marker_path.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")
    return {"files": len(changed), "current": len(files) - len(changed), "storage": str(storage)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(seed(args.config, args.storage, args.knowledge), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
