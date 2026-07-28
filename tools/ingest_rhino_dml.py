"""Ingest the curated Rhino 8 MCP corpus into a Daystrom DML store."""

from __future__ import annotations

import argparse
from pathlib import Path

from dml_mcp.dml_mcp_server import _build_adapter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--storage", type=Path, required=True)
    args = parser.parse_args()

    files = sorted(args.corpus.glob("*.md"))
    if not files:
        parser.error(f"no Markdown files found in {args.corpus}")

    adapter = _build_adapter(args.config, args.storage)
    ingested = 0
    try:
        for path in files:
            adapter.ingest(
                path.read_text(encoding="utf-8"),
                meta={
                    "source": "rhino8-official-and-validated",
                    "doc_path": str(path),
                    "domain": "rhino8-mcp",
                    "validation": "success-validated",
                    "kind": "note",
                },
            )
            ingested += 1
            print(f"ingested {path.name}")
    finally:
        adapter.close(persist=False)

    print(f"ingested_files={ingested}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
