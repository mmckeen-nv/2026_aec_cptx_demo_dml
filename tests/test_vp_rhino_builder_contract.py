from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demos" / "virtual_production_studio"
BUILDER = DEMO / "scripts" / "build_rhino_massing.py"
CONTRACT = DEMO / "prompts" / "02_rhino_modeling_contract.md"


class VpRhinoBuilderContractTests(unittest.TestCase):
    def test_builder_is_valid_self_contained_python(self):
        source = BUILDER.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("VP_STUDIO_BUILD_RESULT=", source)
        self.assertIn('"passed": passed', source)
        self.assertIn("Rhino.Geometry.Brep.CreateFromBox", source)

    def test_builder_cannot_trigger_a_save_dialog(self):
        source = BUILDER.read_text(encoding="utf-8")
        forbidden = (
            "RhinoApp.RunScript",
            "mcp_rhino_save_doc",
            "WriteFile",
            "SaveAs",
            "_Save",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_contract_requires_one_gated_noninteractive_save(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("pass its exact contents, unchanged", text)
        self.assertIn("call `mcp_rhino_save_doc` exactly once", text)
        self.assertIn("the massing builder never saves", text.lower())


if __name__ == "__main__":
    unittest.main()
