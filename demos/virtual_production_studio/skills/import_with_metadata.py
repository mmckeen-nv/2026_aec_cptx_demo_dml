"""Compatibility entry point for the shared, tested Rhino handoff importer.

Some Hermes sessions resolve skills relative to the demo directory. Keep this
file deliberately logic-free so both paths execute the same implementation.
"""
import importlib.util
import os
from pathlib import Path


def _shared_module():
    repo_root = Path(os.environ.get("AEC_DEMO_ROOT", Path(__file__).resolve().parents[3]))
    shared = repo_root / "skills" / "import_with_metadata.py"
    if not shared.is_file():
        raise RuntimeError("missing shared importer: " + str(shared))
    spec = importlib.util.spec_from_file_location("aec_shared_import_with_metadata", shared)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_impl = _shared_module()
ensure_rhino3dm = _impl.ensure_rhino3dm
inspect_3dm = _impl.inspect_3dm
import_3dm = _impl.import_3dm
assert_import_matches_source = _impl.assert_import_matches_source

__all__ = ["ensure_rhino3dm", "inspect_3dm", "import_3dm", "assert_import_matches_source"]
