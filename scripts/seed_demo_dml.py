"""Seed durable, repository-owned demo knowledge into isolated DML stores."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from daystrom_dml.dml_adapter import DMLAdapter


def seed(
    config: Path,
    storage: Path,
    knowledge: Path,
    *,
    tenant_id: str,
    client_id: str,
    project_id: str,
) -> dict[str, object]:
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
    scope = {"tenant_id": tenant_id, "client_id": client_id, "project_id": project_id}
    prior_hashes = prior.get("files", prior) if isinstance(prior, dict) else {}
    scope_changed = prior.get("scope") != scope if isinstance(prior, dict) else True
    changed = [
        path for path in files
        if scope_changed or prior_hashes.get(str(path.resolve())) != hashes[str(path.resolve())]
    ]
    if not changed:
        return {"files": 0, "current": len(files), "storage": str(storage)}

    adapter = DMLAdapter(
        config_path=str(config),
        config_overrides={"storage_dir": str(storage)},
        start_aging_loop=False,
    )
    try:
        for path in changed:
            adapter.ingest(
                path.read_text(encoding="utf-8"),
                meta={
                    "doc_path": str(path.resolve()),
                    "tenant_id": tenant_id,
                    "client_id": client_id,
                    "project_id": project_id,
                    "kind": "note",
                    "source": "aec-demo-repository-seed",
                    "memory_state": "active",
                    "no_merge": True,
                },
            )
    finally:
        adapter.close()
    marker = {"schema_version": 2, "scope": scope, "files": hashes}
    marker_path.write_text(json.dumps(marker, indent=2, sort_keys=True), encoding="utf-8")
    return {"files": len(changed), "current": len(files) - len(changed), "storage": str(storage)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--tenant-id", default="aec-cptx")
    parser.add_argument("--client-id", default="citizen-snips-aec-demo")
    parser.add_argument("--project-id", required=True)
    args = parser.parse_args()
    print(json.dumps(seed(
        args.config,
        args.storage,
        args.knowledge,
        tenant_id=args.tenant_id,
        client_id=args.client_id,
        project_id=args.project_id,
    ), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
