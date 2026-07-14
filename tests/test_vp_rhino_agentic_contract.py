from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demos" / "virtual_production_studio"
CONTRACT = DEMO / "prompts" / "02_rhino_modeling_contract.md"


class VpRhinoAgenticContractTests(unittest.TestCase):
    def test_no_checked_in_geometry_builder_exists(self):
        scripts = DEMO / "scripts"
        geometry_scripts = list(scripts.glob("*rhino*.py")) if scripts.exists() else []
        self.assertEqual([], geometry_scripts)
        self.assertFalse((scripts / "build_rhino_massing.py").exists())

    def test_contract_requires_agent_authored_bounded_mcp_geometry(self):
        text = CONTRACT.read_text(encoding="utf-8")
        for required in (
            "Hermes designs and models the studio in Rhino",
            "Author the Python or C#",
            "one coherent element group",
            "no more than 20 objects",
            "objects tagged `project=vp-studio-01`",
            "Do not use `exec(open(...))`",
            "no fixed count is a",
            "call `mcp_rhino_save_doc` exactly once",
        ):
            self.assertIn(required, text)

    def test_cliff_house_style_phase_prompts_exist(self):
        expected = (
            "02a_phase_site_shell.md",
            "02b_phase_stage_led.md",
            "02c_phase_rooms_access.md",
            "02d_phase_rigging_cameras.md",
            "02e_phase_electrical_mechanical.md",
            "02f_phase_life_safety_data.md",
        )
        for filename in expected:
            text = (DEMO / "prompts" / filename).read_text(encoding="utf-8")
            for heading in ("## Purpose", "## Inputs", "## Execution steps", "## Post-phase checklist", "## Review gate"):
                self.assertIn(heading, text)
            self.assertIn("MCP", text)

    def test_current_dml_policy_supersedes_builder_recipe(self):
        policy = (DEMO / "knowledge" / "dml" / "rhino_agent_authored_workflow_current_20260713.md").read_text(encoding="utf-8")
        self.assertIn("status: CURRENT_POLICY", policy)
        self.assertIn("supersedes: build_rhino_massing.py", policy)
        self.assertIn("target 98 objects", policy)

    def test_blender_handoff_policy_names_real_tool_and_paths(self):
        policy = (DEMO / "knowledge" / "dml" / "blender_handoff_tool_contract_current_20260713.md").read_text(encoding="utf-8")
        self.assertIn("status: CURRENT_POLICY", policy)
        self.assertIn("mcp_blender_execute_blender_code", policy)
        self.assertIn("../../skills/import_with_metadata.py", policy)
        self.assertIn("no generic `run` tool", policy)

    def test_handoff_memory_rejects_first_mesh_part_and_count_only_gate(self):
        policy = (DEMO / "knowledge" / "dml" / "rhino_mesh_first_part_failure_20260713.md").read_text(encoding="utf-8")
        self.assertIn("status: CURRENT_POLICY", policy)
        self.assertIn("retained only the first face mesh", policy)
        self.assertIn("bounding-box parity", policy)
        self.assertIn("count equality alone never passes", policy)


if __name__ == "__main__":
    unittest.main()
