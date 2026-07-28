from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "deployment"
    / "aec-control-plane"
    / "hermes_resident_worker.py"
)
SPEC = importlib.util.spec_from_file_location("hermes_resident_worker_test", MODULE_PATH)
worker = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(worker)


class HermesResidentWorkerTests(unittest.TestCase):
    def test_checked_in_automatic_prompt_satisfies_contract(self):
        prompt = (
            ROOT
            / "deployment"
            / "aec-cptx-profile"
            / "cliff-house-automatic-run.txt"
        ).read_text(encoding="utf-8-sig")
        worker.validate_automatic_prompt(prompt)

    def test_incomplete_automatic_prompt_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "contract is incomplete"):
            worker.validate_automatic_prompt("build a house")


if __name__ == "__main__":
    unittest.main()
